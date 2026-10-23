#!/usr/bin/env python3
"""
WaveWeaver — Hackathon Interactive Demo & API Server.
Zero external dependencies required; runs out-of-the-box on Python 3.10+ (`python3 server.py --port 8767`).
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict

from integrations import (
    CHANNELS_REGISTRY,
    EIGHT_STAGE_PIPELINE_SPEC,
    MPT_VIDEO_PIPELINE_STEPS,
    WaveWeaverHackathonEngine,
)

ENGINE = WaveWeaverHackathonEngine()
STATIC_DIR = Path(__file__).resolve().parent / "static"


def handle_api_request(method: str, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
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

    return {"ok": False, "error": f"Unknown endpoint {method} {path}"}


class WaveWeaverRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: Dict[str, Any], status: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        clean_path = self.path.split("?", 1)[0]
        if clean_path.startswith("/api/"):
            res = handle_api_request("GET", clean_path, {})
            self._send_json(res, 200 if res.get("ok") else 404)
            return

        index_file = STATIC_DIR / "index.html"
        content = index_file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:  # noqa: N802
        clean_path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            body = json.loads(raw_body) if raw_body else {}
        except json.JSONDecodeError:
            body = {}
        res = handle_api_request("POST", clean_path, body)
        self._send_json(res, 200 if res.get("ok") else 400)

    def log_message(self, fmt: str, *args: Any) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="WaveWeaver Hackathon Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8767, help="Bind port (default: 8767)")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), WaveWeaverRequestHandler)
    print(f"🌊 WaveWeaver Workbench running at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
