#!/usr/bin/env python3
"""
WaveWeaver — Twitch EventSub highlight detector + OpenAI Codex overlay spec generator.

Zero third-party dependencies (Python 3.10+ stdlib only).

What this module really does (and nothing more):
1. Verifies Twitch EventSub webhook requests (HMAC-SHA256 over
   message_id + timestamp + raw_body, 10-minute replay window, message-id dedupe)
   and answers `webhook_callback_verification` challenges.
2. Scores incoming EventSub notifications (`channel.chat.message`, `channel.cheer`,
   `channel.raid`, `channel.subscribe`, `channel.hype_train.*`) with a deterministic
   sliding-window "hype score" and opens a highlight marker when it crosses a threshold.
3. Optionally creates a real Twitch clip via Helix `POST /helix/clips`
   (needs TWITCH_CLIENT_ID + TWITCH_USER_TOKEN with `clips:edit`). Without credentials
   it returns a clearly-labelled sandbox record.
4. Asks an OpenAI Codex model (Responses API, model from OPENAI_CODEX_MODEL) for a small
   JSON overlay *spec*. The spec is validated against a strict whitelist and rendered by a
   fixed local HTML template — model output is never injected as raw HTML/JS.
   Without OPENAI_API_KEY (or on any validation failure) a deterministic fallback spec is used.
"""

from __future__ import annotations

import collections
import hashlib
import hmac
import html
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 1. EventSub webhook verification
# ---------------------------------------------------------------------------

HDR_ID = "twitch-eventsub-message-id"
HDR_TS = "twitch-eventsub-message-timestamp"
HDR_SIG = "twitch-eventsub-message-signature"
HDR_TYPE = "twitch-eventsub-message-type"
MAX_MESSAGE_AGE_SECONDS = 10 * 60


def _lower_headers(headers: Dict[str, str]) -> Dict[str, str]:
    return {str(k).lower(): str(v) for k, v in headers.items()}


def compute_eventsub_signature(secret: str, message_id: str, timestamp: str, raw_body: bytes) -> str:
    mac = hmac.new(secret.encode("utf-8"), message_id.encode("utf-8") + timestamp.encode("utf-8") + raw_body, hashlib.sha256)
    return "sha256=" + mac.hexdigest()


def _parse_rfc3339(ts: str) -> Optional[float]:
    # Twitch sends e.g. 2026-11-01T12:34:56.123456789Z (nanoseconds) — trim to seconds.
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})", ts or "")
    if not m:
        return None
    import calendar

    y, mo, d, h, mi, s = (int(x) for x in m.groups())
    return float(calendar.timegm((y, mo, d, h, mi, s, 0, 0, 0)))


class EventSubVerifier:
    """Stateful verifier (keeps a bounded set of seen message ids for replay protection)."""

    def __init__(self, secret: str, max_seen: int = 5000) -> None:
        if not secret or len(secret) < 10:
            raise ValueError("EventSub secret must be 10-100 characters (Twitch requirement).")
        self.secret = secret
        self._seen: "collections.OrderedDict[str, None]" = collections.OrderedDict()
        self._max_seen = max_seen

    def verify(self, headers: Dict[str, str], raw_body: bytes, now: Optional[float] = None) -> Tuple[bool, str]:
        h = _lower_headers(headers)
        msg_id, ts, sig = h.get(HDR_ID, ""), h.get(HDR_TS, ""), h.get(HDR_SIG, "")
        if not (msg_id and ts and sig):
            return False, "missing_eventsub_headers"
        expected = compute_eventsub_signature(self.secret, msg_id, ts, raw_body)
        if not hmac.compare_digest(expected, sig):
            return False, "bad_signature"
        sent_at = _parse_rfc3339(ts)
        now = time.time() if now is None else now
        if sent_at is None or abs(now - sent_at) > MAX_MESSAGE_AGE_SECONDS:
            return False, "stale_or_invalid_timestamp"
        if msg_id in self._seen:
            return False, "duplicate_message_id"
        self._seen[msg_id] = None
        while len(self._seen) > self._max_seen:
            self._seen.popitem(last=False)
        return True, "ok"


# ---------------------------------------------------------------------------
# 2. Deterministic hype scoring (zero LLM involvement)
# ---------------------------------------------------------------------------

@dataclass
class HypeConfig:
    window_seconds: float = 30.0
    threshold: float = 100.0
    cooldown_seconds: float = 90.0
    chat_message_weight: float = 1.0
    cheer_per_100_bits: float = 10.0
    raid_per_viewer: float = 0.5
    raid_cap: float = 150.0
    subscribe_weight: float = 15.0
    hype_train_level_weight: float = 25.0


@dataclass
class Highlight:
    highlight_id: str
    broadcaster_user_id: str
    broadcaster_user_login: str
    opened_at: float
    peak_score: float
    trigger_breakdown: Dict[str, float]
    clip: Optional[Dict[str, Any]] = None
    overlay: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "highlight_id": self.highlight_id,
            "broadcaster_user_id": self.broadcaster_user_id,
            "broadcaster_user_login": self.broadcaster_user_login,
            "opened_at": self.opened_at,
            "peak_score": round(self.peak_score, 2),
            "trigger_breakdown": {k: round(v, 2) for k, v in self.trigger_breakdown.items()},
            "clip": self.clip,
            "overlay": self.overlay,
        }


def score_notification(sub_type: str, event: Dict[str, Any], cfg: HypeConfig) -> Tuple[str, float]:
    """Map one EventSub notification to (bucket, points). Unknown types score 0."""
    if sub_type == "channel.chat.message":
        return "chat", cfg.chat_message_weight
    if sub_type == "channel.cheer":
        bits = float(event.get("bits") or 0)
        return "cheer", bits / 100.0 * cfg.cheer_per_100_bits
    if sub_type == "channel.raid":
        viewers = float(event.get("viewers") or 0)
        return "raid", min(viewers * cfg.raid_per_viewer, cfg.raid_cap)
    if sub_type in ("channel.subscribe", "channel.subscription.message", "channel.subscription.gift"):
        total = float(event.get("total") or 1)
        return "subs", cfg.subscribe_weight * max(total, 1.0)
    if sub_type.startswith("channel.hype_train."):
        level = float(event.get("level") or 1)
        return "hype_train", cfg.hype_train_level_weight * level
    return "ignored", 0.0


class HypeDetector:
    def __init__(self, cfg: Optional[HypeConfig] = None) -> None:
        self.cfg = cfg or HypeConfig()
        self._events: Deque[Tuple[float, str, float]] = collections.deque()
        self._last_highlight_at: float = -1e18
        self.highlights: List[Highlight] = []

    def _trim(self, now: float) -> None:
        while self._events and now - self._events[0][0] > self.cfg.window_seconds:
            self._events.popleft()

    def current_breakdown(self, now: float) -> Dict[str, float]:
        self._trim(now)
        out: Dict[str, float] = collections.defaultdict(float)
        for _, bucket, pts in self._events:
            out[bucket] += pts
        return dict(out)

    def ingest(self, sub_type: str, event: Dict[str, Any], now: Optional[float] = None) -> Optional[Highlight]:
        now = time.time() if now is None else now
        bucket, pts = score_notification(sub_type, event, self.cfg)
        if pts <= 0:
            return None
        self._events.append((now, bucket, pts))
        breakdown = self.current_breakdown(now)
        score = sum(breakdown.values())
        if score < self.cfg.threshold or now - self._last_highlight_at < self.cfg.cooldown_seconds:
            # Update the peak of the most recent open highlight if still within cooldown.
            if self.highlights and now - self._last_highlight_at < self.cfg.cooldown_seconds:
                self.highlights[-1].peak_score = max(self.highlights[-1].peak_score, score)
            return None
        self._last_highlight_at = now
        hl = Highlight(
            highlight_id="HL-" + hashlib.sha256(f"{event.get('broadcaster_user_id')}:{now}".encode()).hexdigest()[:12],
            broadcaster_user_id=str(event.get("broadcaster_user_id") or event.get("to_broadcaster_user_id") or ""),
            broadcaster_user_login=str(event.get("broadcaster_user_login") or event.get("to_broadcaster_user_login") or ""),
            opened_at=now,
            peak_score=score,
            trigger_breakdown=breakdown,
        )
        self.highlights.append(hl)
        return hl


# ---------------------------------------------------------------------------
# 3. Twitch Helix clip creation (real API when credentials exist)
# ---------------------------------------------------------------------------

def create_twitch_clip(broadcaster_id: str, timeout: float = 8.0) -> Dict[str, Any]:
    client_id = os.environ.get("TWITCH_CLIENT_ID", "").strip()
    token = os.environ.get("TWITCH_USER_TOKEN", "").strip()
    if not (client_id and token and broadcaster_id):
        return {"mode": "sandbox", "reason": "TWITCH_CLIENT_ID / TWITCH_USER_TOKEN not set", "clip_id": None, "edit_url": None}
    req = urllib.request.Request(
        "https://api.twitch.tv/helix/clips?broadcaster_id=" + urllib.request.quote(broadcaster_id),
        method="POST",
        headers={"Client-Id": client_id, "Authorization": "Bearer " + token},
        data=b"",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        item = (payload.get("data") or [{}])[0]
        return {"mode": "live", "clip_id": item.get("id"), "edit_url": item.get("edit_url")}
    except urllib.error.HTTPError as e:
        return {"mode": "error", "http_status": e.code, "detail": e.read().decode("utf-8", "replace")[:300]}
    except Exception as e:  # network errors
        return {"mode": "error", "detail": str(e)[:300]}


# ---------------------------------------------------------------------------
# 4. Codex overlay spec: generate -> validate -> render with fixed template
# ---------------------------------------------------------------------------

ALLOWED_ANIMATIONS = ("pulse", "slide", "shake", "none")
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

OVERLAY_INSTRUCTIONS = (
    "You generate a Twitch stream alert overlay SPEC as strict JSON, no prose, no markdown. "
    'Schema: {"headline": string <= 48 chars, "subline": string <= 80 chars, '
    '"accent_hex": "#RRGGBB", "animation": one of ["pulse","slide","shake","none"], '
    '"duration_ms": integer 1500-8000}. Do not output HTML, CSS, JavaScript or URLs.'
)


def validate_overlay_spec(spec: Any) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not isinstance(spec, dict):
        return False, ["spec_not_object"]
    extra = set(spec) - {"headline", "subline", "accent_hex", "animation", "duration_ms"}
    if extra:
        errors.append("unexpected_keys:" + ",".join(sorted(extra)))
    for key, limit in (("headline", 48), ("subline", 80)):
        val = spec.get(key)
        if not isinstance(val, str) or not val.strip() or len(val) > limit:
            errors.append(f"bad_{key}")
        elif re.search(r"[<>]|https?://|javascript:", val, re.I):
            errors.append(f"unsafe_{key}")
    if not isinstance(spec.get("accent_hex"), str) or not _HEX.match(spec["accent_hex"]):
        errors.append("bad_accent_hex")
    if spec.get("animation") not in ALLOWED_ANIMATIONS:
        errors.append("bad_animation")
    dur = spec.get("duration_ms")
    if not isinstance(dur, int) or isinstance(dur, bool) or not (1500 <= dur <= 8000):
        errors.append("bad_duration_ms")
    return (not errors), errors


def fallback_overlay_spec(highlight: Highlight) -> Dict[str, Any]:
    top = max(highlight.trigger_breakdown.items(), key=lambda kv: kv[1])[0] if highlight.trigger_breakdown else "chat"
    headlines = {
        "raid": "RAID INCOMING!",
        "cheer": "BITS STORM!",
        "subs": "SUB TRAIN!",
        "hype_train": "HYPE TRAIN!",
        "chat": "CHAT IS ON FIRE!",
    }
    return {
        "headline": headlines.get(top, "HYPE MOMENT!"),
        "subline": f"Hype score {highlight.peak_score:.0f} in the last 30s",
        "accent_hex": "#9146FF",
        "animation": "pulse",
        "duration_ms": 4000,
    }


def _extract_response_text(payload: Dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    chunks: List[str] = []
    for item in payload.get("output") or []:
        for part in item.get("content") or []:
            if part.get("type") in ("output_text", "text") and isinstance(part.get("text"), str):
                chunks.append(part["text"])
    return "".join(chunks)


def generate_overlay_spec(highlight: Highlight, timeout: float = 20.0) -> Dict[str, Any]:
    """Returns {"source": "codex"|"fallback", "spec": {...}, "errors": [...]}."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("OPENAI_CODEX_MODEL", "").strip()
    if not (api_key and model):
        return {"source": "fallback", "reason": "OPENAI_API_KEY / OPENAI_CODEX_MODEL not set", "spec": fallback_overlay_spec(highlight), "errors": []}
    context = json.dumps({"breakdown": highlight.trigger_breakdown, "peak_score": round(highlight.peak_score, 1), "channel": highlight.broadcaster_user_login})
    body = json.dumps({"model": model, "instructions": OVERLAY_INSTRUCTIONS, "input": "Stream moment: " + context}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        method="POST",
        data=body,
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = _extract_response_text(json.loads(resp.read().decode("utf-8")))
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        spec = json.loads(text)
    except Exception as e:
        return {"source": "fallback", "reason": f"codex_call_failed: {str(e)[:200]}", "spec": fallback_overlay_spec(highlight), "errors": []}
    ok, errors = validate_overlay_spec(spec)
    if not ok:
        return {"source": "fallback", "reason": "codex_spec_rejected", "spec": fallback_overlay_spec(highlight), "errors": errors}
    return {"source": "codex", "model": model, "spec": spec, "errors": []}


def render_overlay_html(spec: Dict[str, Any]) -> str:
    """Fixed template for an OBS browser source. Only escaped, validated values are interpolated."""
    ok, errors = validate_overlay_spec(spec)
    if not ok:
        raise ValueError("refusing to render invalid spec: " + ",".join(errors))
    keyframes = {
        "pulse": "@keyframes ww{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}",
        "slide": "@keyframes ww{0%{transform:translateX(-120%)}15%,85%{transform:translateX(0)}100%{transform:translateX(120%)}}",
        "shake": "@keyframes ww{0%,100%{transform:translateX(0)}25%{transform:translateX(-6px)}75%{transform:translateX(6px)}}",
        "none": "@keyframes ww{}",
    }[spec["animation"]]
    dur = spec["duration_ms"]
    return (
        "<!doctype html><html><head><meta charset='utf-8'><style>"
        "html,body{margin:0;background:transparent;font-family:system-ui,sans-serif}"
        f"{keyframes}"
        f".card{{display:inline-block;margin:24px;padding:16px 24px;border-radius:12px;background:#0e0e10;color:#fff;"
        f"border-left:8px solid {spec['accent_hex']};animation:ww {min(dur, 1200)}ms ease-in-out infinite}}"
        ".h{font-size:40px;font-weight:800;letter-spacing:.5px}.s{font-size:20px;opacity:.9;margin-top:4px}"
        "@media (prefers-reduced-motion:reduce){.card{animation:none}}"
        "</style></head><body>"
        f"<div class='card' role='status' aria-live='polite'><div class='h'>{html.escape(spec['headline'])}</div>"
        f"<div class='s'>{html.escape(spec['subline'])}</div></div>"
        f"<script>setTimeout(function(){{document.body.innerHTML=''}},{int(dur)});</script>"
        "</body></html>"
    )


# ---------------------------------------------------------------------------
# 5. Orchestrator used by server.py
# ---------------------------------------------------------------------------

@dataclass
class TwitchCodexPipeline:
    detector: HypeDetector = field(default_factory=HypeDetector)
    verifier: Optional[EventSubVerifier] = None
    log: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "TwitchCodexPipeline":
        secret = os.environ.get("TWITCH_EVENTSUB_SECRET", "").strip()
        return cls(verifier=EventSubVerifier(secret) if secret else None)

    def handle_webhook(self, headers: Dict[str, str], raw_body: bytes) -> Tuple[int, str, str]:
        """Returns (status, content_type, body) exactly as Twitch expects."""
        if self.verifier is None:
            return 503, "text/plain", "TWITCH_EVENTSUB_SECRET not configured"
        ok, reason = self.verifier.verify(headers, raw_body)
        if not ok:
            # Duplicates must still be acknowledged with 2xx so Twitch stops retrying.
            return (204, "text/plain", "") if reason == "duplicate_message_id" else (403, "text/plain", reason)
        payload = json.loads(raw_body.decode("utf-8") or "{}")
        msg_type = _lower_headers(headers).get(HDR_TYPE, "")
        if msg_type == "webhook_callback_verification":
            return 200, "text/plain", str(payload.get("challenge", ""))
        if msg_type == "revocation":
            self.log.append({"type": "revocation", "subscription": payload.get("subscription", {})})
            return 204, "text/plain", ""
        sub_type = str((payload.get("subscription") or {}).get("type", ""))
        self.process_event(sub_type, payload.get("event") or {})
        return 204, "text/plain", ""

    def process_event(self, sub_type: str, event: Dict[str, Any], now: Optional[float] = None) -> Optional[Dict[str, Any]]:
        hl = self.detector.ingest(sub_type, event, now=now)
        if hl is None:
            return None
        hl.clip = create_twitch_clip(hl.broadcaster_user_id)
        hl.overlay = generate_overlay_spec(hl)
        self.log.append({"type": "highlight", "highlight_id": hl.highlight_id, "clip_mode": hl.clip.get("mode"), "overlay_source": hl.overlay["source"]})
        return hl.to_dict()


def replay_fixture(pipeline: TwitchCodexPipeline, events: List[Dict[str, Any]], start: float = 0.0) -> List[Dict[str, Any]]:
    """Replay a list of {"t": seconds_offset, "type": sub_type, "event": {...}} without network/clock."""
    out: List[Dict[str, Any]] = []
    for ev in events:
        res = pipeline.process_event(ev["type"], ev.get("event", {}), now=start + float(ev["t"]))
        if res:
            out.append(res)
    return out
