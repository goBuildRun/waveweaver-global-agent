#!/usr/bin/env python3
"""
Automated verification suite for the WaveWeaver (织浪 AI) Hackathon Adapter.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from integrations import CHANNELS_REGISTRY, EIGHT_STAGE_PIPELINE_SPEC, MPT_VIDEO_PIPELINE_STEPS
from server import handle_api_request


def test_three_tier_channel_context_isolation() -> None:
    state = handle_api_request("GET", "/api/state", {})
    assert state["ok"] is True
    assert len(state["eight_stages"]) == len(EIGHT_STAGE_PIPELINE_SPEC) == 8
    assert len(state["mpt_steps"]) == len(MPT_VIDEO_PIPELINE_STEPS) == 8

    sw = handle_api_request("POST", "/api/switch-channel", {"channel_key": "ch-seasonal-terroir"})
    assert sw["ok"] is True
    assert sw["active_channel"]["channel_id"] == CHANNELS_REGISTRY["ch-seasonal-terroir"]["channel_id"]


def test_intel_ingestion_and_anti_ai_slop_calibration() -> None:
    intel = handle_api_request("POST", "/api/ingest-intel", {"prompt": "Test BNB Chain AI Agent Intel"})
    assert intel["ok"] is True
    assert "AI-Curated" in intel["card"]["source_badge"]

    cal = handle_api_request("POST", "/api/calibrate", {})
    assert cal["ok"] is True
    assert len(cal["calibration_state"]["slop_phrases_removed"]) >= 3


def test_mpt_five_formats_and_sha256_provenance() -> None:
    mpt = handle_api_request("POST", "/api/produce-mpt", {})
    assert mpt["ok"] is True
    assert len(mpt["five_format_artifacts"]) == 5

    prov = handle_api_request("POST", "/api/attest-provenance", {"title": "WaveWeaver Test Master"})
    assert prov["ok"] is True
    assert prov["attestation"]["sha256_content_digest"].startswith("0x")
