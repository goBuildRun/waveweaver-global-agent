#!/usr/bin/env python3
"""Live Twitch interaction state for the WaveWeaver OBS overlay.

This module deliberately wraps :mod:`twitch_codex` instead of changing it.  The
existing module remains responsible for EventSub verification, hype detection,
and Codex overlay-spec generation.  This module owns the live product state:
polls, the small hype meter, SSE subscribers, and the streamer approval gate.
"""

from __future__ import annotations

import collections
import hmac
import os
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from twitch_codex import HypeConfig, score_notification, validate_overlay_spec


MAX_SSE_QUEUE = 64
MAX_SEEN_MESSAGES = 5000
HYPE_MAX = 100.0
HYPE_COMMAND_POINTS = 10.0


@dataclass
class Poll:
    poll_id: str
    question: str
    options: List[str]
    started_at: float
    duration_seconds: int
    votes: Dict[str, int] = field(default_factory=dict)
    voters: Dict[str, str] = field(default_factory=dict)
    active: bool = True

    @property
    def ends_at(self) -> float:
        return self.started_at + self.duration_seconds

    def to_dict(self, now: float) -> Dict[str, Any]:
        active = self.active and now < self.ends_at
        remaining = max(0, int(self.ends_at - now)) if active else 0
        return {
            "poll_id": self.poll_id,
            "question": self.question,
            "options": list(self.options),
            "votes": dict(self.votes),
            "total_votes": sum(self.votes.values()),
            "started_at": self.started_at,
            "ends_at": self.ends_at,
            "remaining_seconds": remaining,
            "duration_seconds": self.duration_seconds,
            "active": active,
        }


class LiveTwitchState:
    """Thread-safe state store and SSE fan-out for one local streamer.

    ``clock`` is injectable so command, expiry, and decay behavior can be
    tested without sleeping.  Subscriber queues contain already formatted SSE
    frames, which keeps the HTTP handler simple and makes disconnects cheap.
    """

    def __init__(
        self,
        *,
        control_token: Optional[str] = None,
        clock: Callable[[], float] = time.time,
        hype_config: Optional[HypeConfig] = None,
    ) -> None:
        self.control_token = os.environ.get("TWITCH_CONTROL_TOKEN", "").strip() if control_token is None else control_token.strip()
        self.clock = clock
        self.hype_config = hype_config or HypeConfig()
        self.lock = threading.RLock()
        self.poll: Optional[Poll] = None
        self.hype_points = 0.0
        self._hype_updated_at = self.clock()
        self.pending_alerts: "collections.OrderedDict[str, Dict[str, Any]]" = collections.OrderedDict()
        self.approved_alert: Optional[Dict[str, Any]] = None
        self._seen_messages: "collections.OrderedDict[str, None]" = collections.OrderedDict()
        self._subscribers: Dict[int, Tuple[str, "queue.Queue[bytes]"]] = {}
        self._next_subscriber_id = 0
        self._next_event_id = 0

    # ------------------------------------------------------------------
    # SSE transport
    # ------------------------------------------------------------------

    @staticmethod
    def _frame(event: str, payload: Dict[str, Any], event_id: int) -> bytes:
        import json

        body = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
        return f"id: {event_id}\nevent: {event}\ndata: {body}\n\n".encode("utf-8")

    def _emit_locked(self, event: str, payload: Dict[str, Any], roles: Tuple[str, ...] = ("overlay", "control")) -> None:
        self._next_event_id += 1
        frame = self._frame(event, payload, self._next_event_id)
        for subscriber_id, (role, subscriber_queue) in list(self._subscribers.items()):
            if role not in roles:
                continue
            try:
                subscriber_queue.put_nowait(frame)
            except queue.Full:
                # A stale browser tab must not block Twitch webhook intake.
                try:
                    subscriber_queue.get_nowait()
                except queue.Empty:
                    pass
                try:
                    subscriber_queue.put_nowait(frame)
                except queue.Full:
                    self._subscribers.pop(subscriber_id, None)

    def subscribe(self, role: str = "overlay") -> Tuple[int, "queue.Queue[bytes]"]:
        if role not in ("overlay", "control"):
            raise ValueError("role must be overlay or control")
        with self.lock:
            self._next_subscriber_id += 1
            subscriber_id = self._next_subscriber_id
            subscriber_queue: "queue.Queue[bytes]" = queue.Queue(maxsize=MAX_SSE_QUEUE)
            self._subscribers[subscriber_id] = (role, subscriber_queue)
            self._emit_locked("state", self._snapshot_locked(role), (role,))
            return subscriber_id, subscriber_queue

    def unsubscribe(self, subscriber_id: int) -> None:
        with self.lock:
            self._subscribers.pop(subscriber_id, None)

    # ------------------------------------------------------------------
    # State snapshots and helpers
    # ------------------------------------------------------------------

    def _decay_hype_locked(self, now: float) -> None:
        elapsed = max(0.0, now - self._hype_updated_at)
        # A full meter fades over roughly five minutes when chat goes quiet.
        self.hype_points = max(0.0, self.hype_points - elapsed * (HYPE_MAX / 300.0))
        self._hype_updated_at = now

    def _expire_poll_locked(self, now: float) -> None:
        if self.poll and self.poll.active and now >= self.poll.ends_at:
            self.poll.active = False

    def _snapshot_locked(self, role: str, now: Optional[float] = None) -> Dict[str, Any]:
        current = self.clock() if now is None else now
        self._decay_hype_locked(current)
        self._expire_poll_locked(current)
        snapshot: Dict[str, Any] = {
            "poll": self.poll.to_dict(current) if self.poll else None,
            "hype": {"score": round(self.hype_points, 1), "max": HYPE_MAX},
            "approved_alert": self.approved_alert,
        }
        if role == "control":
            snapshot["pending_alerts"] = list(self.pending_alerts.values())
        # Pending Codex output is intentionally never sent to OBS; the latest
        # approved alert is safe for both the control page and reconnecting OBS.
        return snapshot

    def snapshot(self, role: str = "control", now: Optional[float] = None) -> Dict[str, Any]:
        if role not in ("overlay", "control"):
            raise ValueError("role must be overlay or control")
        with self.lock:
            return self._snapshot_locked(role, now)

    def _publish_state_locked(self) -> None:
        self._emit_locked("state", self._snapshot_locked("overlay"), ("overlay",))
        self._emit_locked("state", self._snapshot_locked("control"), ("control",))

    def _mark_message_locked(self, message_id: str) -> bool:
        if not message_id:
            return True
        if message_id in self._seen_messages:
            return False
        self._seen_messages[message_id] = None
        while len(self._seen_messages) > MAX_SEEN_MESSAGES:
            self._seen_messages.popitem(last=False)
        return True

    def _add_hype_locked(self, points: float, source: str, now: float) -> None:
        self._decay_hype_locked(now)
        self.hype_points = min(HYPE_MAX, max(0.0, self.hype_points + max(0.0, points)))
        self._hype_updated_at = now
        self._emit_locked("hype.updated", {"source": source, "hype": {"score": round(self.hype_points, 1), "max": HYPE_MAX}})

    # ------------------------------------------------------------------
    # Streamer controls
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_poll_input(body: Dict[str, Any]) -> Tuple[Optional[str], Optional[List[str]], Optional[int], Optional[str]]:
        question = body.get("question")
        raw_options = body.get("options")
        duration = body.get("duration_seconds", 300)
        if not isinstance(question, str) or not question.strip() or len(question.strip()) > 120:
            return None, None, None, "question must be 1-120 characters"
        if not isinstance(raw_options, list) or not 2 <= len(raw_options) <= 8:
            return None, None, None, "options must contain 2-8 items"
        options: List[str] = []
        seen = set()
        for option in raw_options:
            if not isinstance(option, str):
                return None, None, None, "options must be strings"
            clean = option.strip()
            key = clean.casefold()
            if not clean or len(clean) > 40 or key in seen:
                return None, None, None, "options must be unique, non-empty, and <= 40 characters"
            seen.add(key)
            options.append(clean)
        if isinstance(duration, bool) or not isinstance(duration, int) or not 5 <= duration <= 3600:
            return None, None, None, "duration_seconds must be between 5 and 3600"
        return question.strip(), options, duration, None

    def start_poll(self, body: Dict[str, Any]) -> Dict[str, Any]:
        question, options, duration, error = self._validate_poll_input(body)
        if error:
            return {"ok": False, "error": error}
        assert question is not None and options is not None and duration is not None
        with self.lock:
            now = self.clock()
            self._expire_poll_locked(now)
            if self.poll and self.poll.active:
                return {"ok": False, "error": "poll_already_active"}
            poll_id = "poll-" + uuid.uuid4().hex[:12]
            self.poll = Poll(
                poll_id=poll_id,
                question=question,
                options=options,
                started_at=now,
                duration_seconds=duration,
                votes={option: 0 for option in options},
            )
            self._emit_locked("poll.started", {"poll": self.poll.to_dict(now)})
            self._publish_state_locked()
            return {"ok": True, "poll": self.poll.to_dict(now)}

    def stop_poll(self) -> Dict[str, Any]:
        with self.lock:
            now = self.clock()
            self._expire_poll_locked(now)
            if not self.poll or not self.poll.active:
                return {"ok": False, "error": "no_active_poll"}
            self.poll.active = False
            result = self.poll.to_dict(now)
            self._emit_locked("poll.stopped", {"poll": result})
            self._publish_state_locked()
            return {"ok": True, "poll": result}

    def approve_alert(self, alert_id: str) -> Dict[str, Any]:
        with self.lock:
            alert = self.pending_alerts.pop(str(alert_id), None)
            if alert is None:
                return {"ok": False, "error": "alert_not_found"}
            alert = dict(alert)
            alert["approved_at"] = self.clock()
            self.approved_alert = alert
            self._emit_locked("alert.approved", alert)
            self._publish_state_locked()
            return {"ok": True, "alert": alert}

    def reject_alert(self, alert_id: str) -> Dict[str, Any]:
        with self.lock:
            alert = self.pending_alerts.pop(str(alert_id), None)
            if alert is None:
                return {"ok": False, "error": "alert_not_found"}
            self._emit_locked("alert.rejected", {"alert_id": str(alert_id)}, ("control",))
            self._publish_state_locked()
            return {"ok": True, "alert_id": str(alert_id)}

    def clear_alerts(self) -> None:
        with self.lock:
            self.pending_alerts.clear()
            self.approved_alert = None
            self._publish_state_locked()

    def queue_alert(self, highlight: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        overlay = highlight.get("overlay") if isinstance(highlight, dict) else None
        spec = overlay.get("spec") if isinstance(overlay, dict) else None
        valid, _ = validate_overlay_spec(spec)
        if not valid:
            return None
        alert_id = str(highlight.get("highlight_id") or "alert-" + uuid.uuid4().hex[:12])
        alert = {
            "alert_id": alert_id,
            "highlight": highlight,
            "overlay": overlay,
            "created_at": self.clock(),
        }
        with self.lock:
            self.pending_alerts[alert_id] = alert
            while len(self.pending_alerts) > 20:
                self.pending_alerts.popitem(last=False)
            self._emit_locked("alert.pending", alert, ("control",))
            self._publish_state_locked()
        return alert

    # ------------------------------------------------------------------
    # EventSub command intake
    # ------------------------------------------------------------------

    def _cast_vote_locked(self, event: Dict[str, Any], option_text: str, now: float) -> Dict[str, Any]:
        self._expire_poll_locked(now)
        if not self.poll or not self.poll.active:
            return {"command": "vote", "accepted": False, "reason": "no_active_poll"}
        option_key = option_text.strip().casefold()
        option_map = {option.casefold(): option for option in self.poll.options}
        option = option_map.get(option_key)
        if option is None:
            return {"command": "vote", "accepted": False, "reason": "unknown_option"}
        user_id = str(event.get("chatter_user_id") or event.get("chatter_user_login") or event.get("message_id") or "anonymous")
        if user_id in self.poll.voters:
            return {"command": "vote", "accepted": False, "reason": "already_voted"}
        self.poll.voters[user_id] = option
        self.poll.votes[option] += 1
        self._emit_locked("poll.updated", {"poll": self.poll.to_dict(now), "vote": {"user": user_id, "option": option}})
        return {"command": "vote", "accepted": True, "option": option, "poll": self.poll.to_dict(now)}

    def _handle_chat_locked(self, event: Dict[str, Any], now: float) -> Optional[Dict[str, Any]]:
        message = event.get("message") if isinstance(event.get("message"), dict) else {}
        text = str(message.get("text") or "").strip()
        parts = text.split(maxsplit=1)
        if not parts:
            return None
        command = parts[0].casefold()
        if command == "!vote":
            if len(parts) != 2 or not parts[1].strip():
                return {"command": "vote", "accepted": False, "reason": "missing_option"}
            return self._cast_vote_locked({**event, "message_id": message.get("message_id")}, parts[1], now)
        if command == "!hype":
            self._add_hype_locked(HYPE_COMMAND_POINTS, "chat", now)
            return {"command": "hype", "accepted": True, "points": HYPE_COMMAND_POINTS}
        return None

    def ingest_notification(
        self,
        payload: Dict[str, Any],
        *,
        message_id: str = "",
        highlight: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Apply an already verified EventSub notification.

        ``highlight`` is the return value observed from the existing
        ``TwitchCodexPipeline``.  Passing it in avoids running detector or
        network work twice while still allowing this state layer to gate the
        generated alert.
        """

        with self.lock:
            if not self._mark_message_locked(message_id):
                return {"ok": True, "duplicate": True}
            now = self.clock()
            sub_type = str((payload.get("subscription") or {}).get("type") or "")
            event = payload.get("event") if isinstance(payload.get("event"), dict) else {}
            command = self._handle_chat_locked(event, now) if sub_type == "channel.chat.message" else None
            if sub_type in ("channel.cheer", "channel.raid"):
                _, points = score_notification(sub_type, event, self.hype_config)
                self._add_hype_locked(points, sub_type.rsplit(".", 1)[-1], now)
            alert = self.queue_alert(highlight) if highlight else None
            if command or sub_type in ("channel.cheer", "channel.raid"):
                self._publish_state_locked()
            return {"ok": True, "command": command, "alert": alert}

    # ------------------------------------------------------------------
    # Control authentication
    # ------------------------------------------------------------------

    def is_authorized(self, headers: Dict[str, str]) -> bool:
        if not self.control_token:
            return True
        normalized = {str(key).lower(): str(value) for key, value in headers.items()}
        supplied = normalized.get("x-control-token", "")
        authorization = normalized.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            supplied = authorization[7:].strip()
        return bool(supplied) and hmac.compare_digest(supplied, self.control_token)

