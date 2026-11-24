#!/usr/bin/env python3
"""
Unit & invariant tests for WaveWeaver × Gno.land (`onyx-1`) On-Chain Content Provenance (`gno_provenance.py`).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gno_provenance as gp
from server import handle_api_request


def test_provenance_gate_accepts_high_qa_calibrated_draft() -> None:
    digest = gp.compute_draft_sha256(
        title="576-Token Wick-Stripped Washout Empirical Breakdown",
        channel_slug="ch-ai-quant",
        body="Verified K-line study stripping 1s opening wicks.",
    )
    res = gp.evaluate_provenance_gate(
        pub_id="WW-GNO-001",
        channel_slug="ch-ai-quant",
        title="576-Token Wick-Stripped Washout Empirical Breakdown",
        sha256_digest=digest,
        qa_score_permille=942,
        slop_removed_count=4,
        citation_count=3,
    )
    assert res["ok"] is True
    assert res["verdict"] == "ANCHORED_READY"
    assert res["publication"]["qa_score"] == "94.2"
    assert res["gnomcp_call"]["tool"] == "gno_call"
    assert res["gnomcp_call"]["arguments"]["func"] == "AnchorPublication"


def test_provenance_gate_fails_closed_below_85_anti_slop_threshold() -> None:
    digest = "0x" + "a" * 64
    res = gp.evaluate_provenance_gate(
        pub_id="WW-SLOP-001",
        channel_slug="ch-ai-quant",
        title="Generic AI Slop Post",
        sha256_digest=digest,
        qa_score_permille=790,
        slop_removed_count=0,
        citation_count=2,
    )
    assert res["ok"] is False
    assert res["verdict"] == "FAIL_CLOSED_SLOP_GATE"


def test_provenance_gate_fails_closed_on_zero_citations_or_bad_hash() -> None:
    digest = "0x" + "b" * 64
    no_cite = gp.evaluate_provenance_gate(
        pub_id="WW-NOCITE-001",
        channel_slug="ch-seasonal-terroir",
        title="Uncited Claim",
        sha256_digest=digest,
        qa_score_permille=910,
        citation_count=0,
    )
    assert no_cite["ok"] is False
    assert no_cite["verdict"] == "FAIL_CLOSED_ZERO_CITATIONS"

    bad_hash = gp.evaluate_provenance_gate(
        pub_id="WW-BADHASH-001",
        channel_slug="ch-seasonal-terroir",
        title="Malformed Digest",
        sha256_digest="0x1234",
        qa_score_permille=910,
        citation_count=2,
    )
    assert bad_hash["ok"] is False
    assert bad_hash["verdict"] == "REJECTED_INVALID_SHA256"


def test_server_gno_endpoints_and_digest_verification() -> None:
    seeded_hash = gp.SEEDED_REALM_PUBLICATIONS[0]["sha256"]
    v = handle_api_request("POST", "/api/gno/verify", {"sha256_digest": seeded_hash})
    assert v["ok"] is True
    assert v["verification"]["verified"] is True

    gate_ok = handle_api_request(
        "POST",
        "/api/gno/evaluate-anchor",
        {
            "id": "WW-API-009",
            "channel_slug": "ch-ai-quant",
            "title": "Calibrated Release Note",
            "sha256_digest": "0x" + "c" * 64,
            "qa_score_permille": 925,
            "slop_removed_count": 4,
            "citation_count": 3,
        },
    )
    assert gate_ok["ok"] is True
    assert gate_ok["evaluation"]["verdict"] == "ANCHORED_READY"
