#!/usr/bin/env python3
"""Focused tests for the live Twitch poll, hype, SSE, and approval layer."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from live_twitch import LiveTwitchState  # noqa: E402
from register_eventsub import create_subscriptions, subscription_payloads  # noqa: E402


class Clock:
    def __init__(self, value: float = 1_000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


def notification(sub_type: str, event: Dict[str, Any], message_id: str) -> Dict[str, Any]:
    return {"subscription": {"type": sub_type}, "event": event, "message_id": message_id}


def drain(subscriber_queue: Any) -> List[bytes]:
    frames: List[bytes] = []
    while True:
        try:
            frames.append(subscriber_queue.get_nowait())
        except Exception:
            return frames


def test_poll_commands_are_case_insensitive_and_one_vote_per_chatter() -> None:
    clock = Clock()
    state = LiveTwitchState(clock=clock)
    started = state.start_poll({"question": "Choose", "options": ["Red", "Blue"], "duration_seconds": 30})
    assert started["ok"] is True

    first = state.ingest_notification(
        notification(
            "channel.chat.message",
            {"chatter_user_id": "u-1", "message": {"message_id": "chat-1", "text": "!VoTe blue"}},
            "delivery-1",
        ),
        message_id="delivery-1",
    )
    second = state.ingest_notification(
        notification(
            "channel.chat.message",
            {"chatter_user_id": "u-1", "message": {"message_id": "chat-2", "text": "!vote Red"}},
            "delivery-2",
        ),
        message_id="delivery-2",
    )
    assert first["command"]["accepted"] is True
    assert second["command"] == {"command": "vote", "accepted": False, "reason": "already_voted"}
    assert state.snapshot()["poll"]["votes"] == {"Red": 0, "Blue": 1}


def test_hype_command_cheer_raid_and_expiry_update_meter() -> None:
    clock = Clock()
    state = LiveTwitchState(clock=clock)
    state.ingest_notification(
        notification("channel.chat.message", {"chatter_user_id": "u", "message": {"text": "!hype"}}, "d1"),
        message_id="d1",
    )
    state.ingest_notification(notification("channel.cheer", {"bits": 100}, "d2"), message_id="d2")
    state.ingest_notification(notification("channel.raid", {"viewers": 20}, "d3"), message_id="d3")
    assert state.snapshot()["hype"]["score"] == 30.0

    state.start_poll({"question": "Soon", "options": ["Yes", "No"], "duration_seconds": 5})
    clock.value += 6
    assert state.snapshot()["poll"]["active"] is False
    clock.value += 300
    assert state.snapshot()["hype"]["score"] == 0.0


def test_sse_filters_pending_alerts_until_streamer_approval() -> None:
    state = LiveTwitchState(clock=Clock())
    control_id, control_queue = state.subscribe("control")
    overlay_id, overlay_queue = state.subscribe("overlay")
    drain(control_queue)
    drain(overlay_queue)
    highlight = {
        "highlight_id": "HL-1",
        "peak_score": 120,
        "overlay": {
            "source": "fallback",
            "spec": {
                "headline": "HYPE",
                "subline": "Approved by streamer",
                "accent_hex": "#9146FF",
                "animation": "pulse",
                "duration_ms": 3000,
            },
        },
    }
    state.queue_alert(highlight)
    control_frames = b"".join(drain(control_queue))
    overlay_frames = b"".join(drain(overlay_queue))
    assert b"alert.pending" in control_frames
    assert b"alert.pending" not in overlay_frames

    approved = state.approve_alert("HL-1")
    assert approved["ok"] is True
    approved_frames = b"".join(drain(overlay_queue))
    assert b"alert.approved" in approved_frames
    assert state.snapshot("overlay")["approved_alert"]["alert_id"] == "HL-1"
    state.unsubscribe(control_id)
    state.unsubscribe(overlay_id)


def test_control_token_uses_constant_time_comparison() -> None:
    state = LiveTwitchState(control_token="secret-token", clock=Clock())
    assert state.is_authorized({"X-Control-Token": "secret-token"}) is True
    assert state.is_authorized({"Authorization": "Bearer secret-token"}) is True
    assert state.is_authorized({"X-Control-Token": "wrong"}) is False


def test_subscription_payloads_use_expected_eventsub_conditions() -> None:
    payloads = list(
        subscription_payloads(
            broadcaster_id="42",
            chat_user_id="99",
            callback_url="https://example.test/eventsub",
            secret="a" * 20,
        )
    )
    assert [item["type"] for item in payloads] == ["channel.chat.message", "channel.cheer", "channel.raid"]
    assert payloads[0]["condition"] == {"broadcaster_user_id": "42", "user_id": "99"}
    assert payloads[1]["condition"] == {"broadcaster_user_id": "42"}
    assert payloads[2]["condition"] == {"to_broadcaster_user_id": "42"}
    assert all(item["transport"]["callback"].endswith("/eventsub") for item in payloads)


def test_create_subscriptions_posts_three_helix_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    requests: List[Dict[str, Any]] = []

    class Response:
        status = 202

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *args: Any) -> bool:
            return False

        def read(self) -> bytes:
            return json.dumps({"data": [{"id": "sub-1", "status": "enabled"}]}).encode()

    def fake_urlopen(request: Any, timeout: float = 0) -> Response:
        requests.append({"url": request.full_url, "body": json.loads(request.data.decode()), "timeout": timeout})
        return Response()

    import register_eventsub

    monkeypatch.setattr(register_eventsub.urllib.request, "urlopen", fake_urlopen)
    result = create_subscriptions(
        client_id="client",
        token="token",
        broadcaster_id="42",
        callback_url="https://example.test/eventsub",
        secret="a" * 20,
    )
    assert len(result) == len(requests) == 3
    assert {request["body"]["type"] for request in requests} == {"channel.chat.message", "channel.cheer", "channel.raid"}
    assert all(request["url"].endswith("/helix/eventsub/subscriptions") for request in requests)

