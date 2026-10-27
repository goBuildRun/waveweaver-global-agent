#!/usr/bin/env python3
"""Tests for the Twitch EventSub + Codex overlay module (no network required)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import twitch_codex as tc  # noqa: E402

SECRET = "test-secret-0123456789"


@pytest.fixture(autouse=True)
def _no_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("OPENAI_API_KEY", "OPENAI_CODEX_MODEL", "TWITCH_CLIENT_ID", "TWITCH_USER_TOKEN"):
        monkeypatch.delenv(var, raising=False)


def _signed_headers(body: bytes, msg_id: str = "m-1", ts: str = "2026-11-01T12:00:00.123456789Z", msg_type: str = "notification") -> dict:
    return {
        "Twitch-Eventsub-Message-Id": msg_id,
        "Twitch-Eventsub-Message-Timestamp": ts,
        "Twitch-Eventsub-Message-Signature": tc.compute_eventsub_signature(SECRET, msg_id, ts, body),
        "Twitch-Eventsub-Message-Type": msg_type,
    }


NOW = tc._parse_rfc3339("2026-11-01T12:00:30Z")


def test_signature_accepts_valid_and_rejects_tampered() -> None:
    v = tc.EventSubVerifier(SECRET)
    body = b'{"subscription":{"type":"channel.cheer"},"event":{"bits":100}}'
    h = _signed_headers(body)
    assert v.verify(h, body, now=NOW) == (True, "ok")
    assert v.verify(_signed_headers(body, msg_id="m-2"), body + b" ", now=NOW) == (False, "bad_signature")


def test_replay_protection_dup_id_and_stale_timestamp() -> None:
    v = tc.EventSubVerifier(SECRET)
    body = b"{}"
    h = _signed_headers(body, msg_id="dup")
    assert v.verify(h, body, now=NOW)[0] is True
    assert v.verify(h, body, now=NOW) == (False, "duplicate_message_id")
    stale = _signed_headers(body, msg_id="old", ts="2026-11-01T11:00:00Z")
    assert v.verify(stale, body, now=NOW) == (False, "stale_or_invalid_timestamp")


def test_webhook_challenge_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    pipe = tc.TwitchCodexPipeline(verifier=tc.EventSubVerifier(SECRET))
    monkeypatch.setattr(tc.time, "time", lambda: NOW)
    body = json.dumps({"challenge": "pogchamp-123", "subscription": {"type": "channel.raid"}}).encode()
    status, ctype, text = pipe.handle_webhook(_signed_headers(body, msg_type="webhook_callback_verification"), body)
    assert (status, ctype, text) == (200, "text/plain", "pogchamp-123")


def test_hype_detector_fires_once_then_cools_down() -> None:
    fixture = json.loads((ROOT / "fixtures" / "eventsub_replay.json").read_text())["events"]
    pipe = tc.TwitchCodexPipeline()
    highlights = tc.replay_fixture(pipe, fixture, start=0.0)
    assert len(highlights) == 1
    hl = highlights[0]
    assert hl["peak_score"] >= 100
    assert hl["trigger_breakdown"]["raid"] == 90.0
    assert hl["clip"]["mode"] == "sandbox"
    assert hl["overlay"]["source"] == "fallback"
    assert hl["overlay"]["spec"]["headline"] == "RAID INCOMING!"


@pytest.mark.parametrize(
    "spec,ok",
    [
        ({"headline": "RAID!", "subline": "x", "accent_hex": "#9146FF", "animation": "pulse", "duration_ms": 3000}, True),
        ({"headline": "<script>alert(1)</script>", "subline": "x", "accent_hex": "#9146FF", "animation": "pulse", "duration_ms": 3000}, False),
        ({"headline": "ok", "subline": "x", "accent_hex": "red", "animation": "pulse", "duration_ms": 3000}, False),
        ({"headline": "ok", "subline": "x", "accent_hex": "#000000", "animation": "explode", "duration_ms": 3000}, False),
        ({"headline": "ok", "subline": "x", "accent_hex": "#000000", "animation": "none", "duration_ms": 3000, "css": "x"}, False),
    ],
)
def test_overlay_spec_whitelist(spec: dict, ok: bool) -> None:
    assert tc.validate_overlay_spec(spec)[0] is ok


def test_rendered_overlay_escapes_text_and_respects_reduced_motion() -> None:
    spec = {"headline": "Tom & Jerry", "subline": "50% hype", "accent_hex": "#00FF00", "animation": "shake", "duration_ms": 2000}
    out = tc.render_overlay_html(spec)
    assert "Tom &amp; Jerry" in out
    assert "prefers-reduced-motion" in out
    with pytest.raises(ValueError):
        tc.render_overlay_html({**spec, "headline": "<b>x</b>"})


def test_codex_output_rejected_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_CODEX_MODEL", "test-model")

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            bad = {"headline": "<img src=x>", "subline": "x", "accent_hex": "#123456", "animation": "pulse", "duration_ms": 3000}
            return json.dumps({"output": [{"content": [{"type": "output_text", "text": json.dumps(bad)}]}]}).encode()

    monkeypatch.setattr(tc.urllib.request, "urlopen", lambda req, timeout=0: _Resp())
    hl = tc.Highlight("HL-x", "1", "demo", 0.0, 120.0, {"cheer": 120.0})
    res = tc.generate_overlay_spec(hl)
    assert res["source"] == "fallback"
    assert "unsafe_headline" in res["errors"]
