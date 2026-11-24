#!/usr/bin/env python3
"""
WaveWeaver — Hackathon Interactive Demo & API Server.
Zero external dependencies required; runs out-of-the-box on Python 3.10+ (`python3 server.py --port 8767`).
"""

from __future__ import annotations

import argparse
import json
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlsplit

from integrations import (
    CHANNELS_REGISTRY,
    EIGHT_STAGE_PIPELINE_SPEC,
    MPT_VIDEO_PIPELINE_STEPS,
    WaveWeaverHackathonEngine,
)

from twitch_codex import TwitchCodexPipeline, render_overlay_html, replay_fixture
from live_twitch import LiveTwitchState
import gno_provenance as gp

ENGINE = WaveWeaverHackathonEngine()
TWITCH = TwitchCodexPipeline.from_env()
LIVE = LiveTwitchState()
TWITCH_LOCK = threading.RLock()
STATIC_DIR = Path(__file__).resolve().parent / "static"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "eventsub_replay.json"


def handle_api_request(
    method: str,
    path: str,
    body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    headers = headers or {}
    if method == "GET" and path == "/api/state":
        return {
            "ok": True,
            "active_channel_key": ENGINE.active_channel_key,
            "active_channel": CHANNELS_REGISTRY[ENGINE.active_channel_key],
            "channels": CHANNELS_REGISTRY,
            "eight_stages": EIGHT_STAGE_PIPELINE_SPEC,
            "intel_cards": ENGINE.intel_cards,
            "calibration_state": ENGINE.calibration_state,
            "mpt_steps": MPT_VIDEO_PIPELINE_STEPS,
            "five_format_artifacts": ENGINE.five_format_artifacts,
            "provenance_attestations": ENGINE.provenance_attestations,
            "seven_day_review_loop": ENGINE.seven_day_review_loop,
            "telemetry_logs": ENGINE.telemetry_logs,
            "twitch_live": LIVE.snapshot("control"),
        }

    if method == "POST" and path == "/api/switch-channel":
        channel_key = str(body.get("channel_key") or "ch-ai-quant")
        ch = ENGINE.switch_channel(channel_key)
        return {
            "ok": True,
            "active_channel_key": ENGINE.active_channel_key,
            "active_channel": ch,
            "telemetry_logs": ENGINE.telemetry_logs,
        }

    if method == "POST" and path == "/api/ingest-intel":
        prompt = str(body.get("prompt") or "Ingest BNB Chain Tokenized Tech Stocks (4STOCK) & AI Agent washout metrics")
        card = ENGINE.ingest_live_intelligence(prompt)
        return {
            "ok": True,
            "card": card,
            "intel_cards": ENGINE.intel_cards,
            "telemetry_logs": ENGINE.telemetry_logs,
        }

    if method == "POST" and path == "/api/calibrate":
        cal = ENGINE.run_humanized_calibration_and_preflight()
        return {
            "ok": True,
            "calibration_state": cal,
            "telemetry_logs": ENGINE.telemetry_logs,
        }

    if method == "POST" and path == "/api/produce-mpt":
        res = ENGINE.run_mpt_five_format_production()
        return {
            "ok": True,
            "mpt_steps": res["mpt_steps"],
            "five_format_artifacts": res["artifacts"],
            "telemetry_logs": ENGINE.telemetry_logs,
        }

    if method == "POST" and path == "/api/attest-provenance":
        title = str(body.get("title") or "576-Token Golden Washout Study: Multi-Format Campaign Master")
        record = ENGINE.mint_content_provenance(title=title)
        return {
            "ok": True,
            "attestation": record,
            "provenance_attestations": ENGINE.provenance_attestations,
            "telemetry_logs": ENGINE.telemetry_logs,
        }

    if method == "GET" and path == "/api/gno/status":
        return {"ok": True, "gno_status": gp.query_gno_realm_status()}

    if method == "POST" and path == "/api/gno/verify":
        sha256_digest = str(body.get("sha256_digest") or "")
        return {"ok": True, "verification": gp.verify_digest_on_gno(sha256_digest)}

    if method == "POST" and path == "/api/gno/evaluate-anchor":
        eval_res = gp.evaluate_provenance_gate(
            pub_id=str(body.get("id") or "WW-GNO-001"),
            channel_slug=str(body.get("channel_slug") or ENGINE.active_channel_key),
            title=str(body.get("title") or "Calibrated Release Master"),
            sha256_digest=str(body.get("sha256_digest") or ""),
            qa_score_permille=int(body.get("qa_score_permille") if body.get("qa_score_permille") is not None else 942),
            slop_removed_count=int(body.get("slop_removed_count") if body.get("slop_removed_count") is not None else 4),
            citation_count=int(body.get("citation_count") if body.get("citation_count") is not None else 3),
        )
        return {"ok": eval_res["ok"], "evaluation": eval_res}

    if method == "POST" and path == "/api/twitch/replay":
        # Replays the synthetic EventSub fixture through the real detector/clip/Codex pipeline.
        global TWITCH
        with TWITCH_LOCK:
            TWITCH = TwitchCodexPipeline.from_env()
            events = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["events"]
            highlights = replay_fixture(TWITCH, events, start=1_000_000.0)
        LIVE.clear_alerts()
        for highlight in highlights:
            LIVE.queue_alert(highlight)
        return {"ok": True, "highlights": highlights, "log": TWITCH.log}

    if method == "GET" and path == "/api/twitch/highlights":
        with TWITCH_LOCK:
            highlights = [h.to_dict() for h in TWITCH.detector.highlights]
            log = list(TWITCH.log)
        return {"ok": True, "highlights": highlights, "log": log}

    if method == "GET" and path in ("/api/twitch/live/state", "/api/live/state"):
        return {"ok": True, **LIVE.snapshot("control")}

    if method == "POST" and path in (
        "/api/twitch/poll/start",
        "/api/live/poll/start",
    ):
        if not LIVE.is_authorized(headers):
            return {"ok": False, "error": "unauthorized"}
        return LIVE.start_poll(body)

    if method == "POST" and path in (
        "/api/twitch/poll/stop",
        "/api/live/poll/stop",
    ):
        if not LIVE.is_authorized(headers):
            return {"ok": False, "error": "unauthorized"}
        return LIVE.stop_poll()

    if method == "POST" and path in (
        "/api/twitch/alert/approve",
        "/api/live/alerts/approve",
    ):
        if not LIVE.is_authorized(headers):
            return {"ok": False, "error": "unauthorized"}
        return LIVE.approve_alert(str(body.get("alert_id") or ""))

    if method == "POST" and path in (
        "/api/twitch/alert/reject",
        "/api/live/alerts/reject",
    ):
        if not LIVE.is_authorized(headers):
            return {"ok": False, "error": "unauthorized"}
        return LIVE.reject_alert(str(body.get("alert_id") or ""))

    return {"ok": False, "error": f"Unknown endpoint {method} {path}"}


class WaveWeaverRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send_json(self, data: Dict[str, Any], status: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def _send_static_file(self, filename: str) -> None:
        content = (STATIC_DIR / filename).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _stream_sse(self, role: str) -> None:
        try:
            subscriber_id, subscriber_queue = LIVE.subscribe(role)
        except ValueError:
            self._send_json({"ok": False, "error": "invalid_sse_role"}, 400)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        try:
            while True:
                try:
                    frame = subscriber_queue.get(timeout=15.0)
                except queue.Empty:
                    frame = b": keepalive\n\n"
                self.wfile.write(frame)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            LIVE.unsubscribe(subscriber_id)

    def do_GET(self) -> None:  # noqa: N802
        clean_path = urlsplit(self.path).path
        if clean_path in ("/api/twitch/events", "/events"):
            role = (parse_qs(urlsplit(self.path).query).get("role") or ["overlay"])[0]
            self._stream_sse(role)
            return
        if clean_path in ("/twitch/overlay", "/obs/overlay", "/overlay"):
            self._send_static_file("twitch-overlay.html")
            return
        if clean_path in ("/twitch/control", "/twitch/streamer", "/control"):
            self._send_static_file("twitch-control.html")
            return
        if clean_path == "/overlay/latest":
            alert = LIVE.snapshot("overlay").get("approved_alert")
            if not alert:
                self.send_response(204)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            content = render_overlay_html(alert["overlay"]["spec"]).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        if clean_path.startswith("/api/"):
            res = handle_api_request("GET", clean_path, {})
            self._send_json(res, 200 if res.get("ok") else 404)
            return

        self._send_static_file("index.html")

    def do_POST(self) -> None:  # noqa: N802
        clean_path = urlsplit(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        if clean_path == "/eventsub":
            if length > 1_048_576:
                self.send_error(413, "EventSub body too large")
                return
            raw = self.rfile.read(length) if length > 0 else b""
            headers = dict(self.headers.items())
            with TWITCH_LOCK:
                before = len(TWITCH.detector.highlights)
                try:
                    status, ctype, text = TWITCH.handle_webhook(headers, raw)
                except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
                    status, ctype, text = 400, "text/plain", "invalid_eventsub_payload"
                after = len(TWITCH.detector.highlights)
                new_highlight = TWITCH.detector.highlights[-1].to_dict() if after > before else None
            message_type = {str(key).lower(): str(value) for key, value in headers.items()}.get("twitch-eventsub-message-type", "")
            if status == 204 and message_type == "notification":
                try:
                    payload = json.loads(raw.decode("utf-8") or "{}")
                except (UnicodeDecodeError, json.JSONDecodeError):
                    payload = {}
                message_id = {str(key).lower(): str(value) for key, value in headers.items()}.get("twitch-eventsub-message-id", "")
                LIVE.ingest_notification(payload, message_id=message_id, highlight=new_highlight)
            out = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)
            return
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            body = json.loads(raw_body) if raw_body else {}
        except json.JSONDecodeError:
            body = {}
        res = handle_api_request("POST", clean_path, body, dict(self.headers.items()))
        if res.get("ok"):
            status = 200
        elif res.get("error") == "unauthorized":
            status = 401
        elif res.get("error") in ("alert_not_found", "no_active_poll"):
            status = 404
        else:
            status = 400
        self._send_json(res, status)

    def log_message(self, fmt: str, *args: Any) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="WaveWeaver Hackathon Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8767, help="Bind port (default: 8767)")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), WaveWeaverRequestHandler)
    server.daemon_threads = True
    print(f"🌊 WaveWeaver Workbench running at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
