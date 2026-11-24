#!/usr/bin/env python3
"""
Seed verified WaveWeaver publications onto Gno.land `onyx-1` Testnet via `gnomcp` once GPAO enables the Realm.
Usage:
  GNOMCP_BIN=/path/to/gnomcp python3 scripts/seed_gno_onyx.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import gno_provenance as gp  # noqa: E402


def main() -> int:
    gnomcp_bin = os.environ.get("GNOMCP_BIN") or shutil.which("gnomcp")
    if not gnomcp_bin:
        print("Set GNOMCP_BIN=/path/to/gnomcp or install gnomcp on PATH.", file=sys.stderr)
        return 1

    proc = subprocess.Popen(
        [gnomcp_bin],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.stdin and proc.stdout

    def rpc(msg: dict) -> dict:
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()
        return json.loads(proc.stdout.readline())

    rpc({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "ww-seed", "version": "1.0"}},
    })
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    proc.stdin.flush()

    realm = gp.GNO_ONYX_CONFIG["realm_path"]
    chk = rpc({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "gno_render", "arguments": {"profile": "testnet", "realm": realm}},
    })
    if chk.get("result", {}).get("isError"):
        print(f"Realm {realm} is still parked awaiting GPAO clearance:\n{json.dumps(chk, indent=2)}")
        proc.terminate()
        return 2

    for idx, pub in enumerate(gp.SEEDED_REALM_PUBLICATIONS, start=10):
        res = rpc({
            "jsonrpc": "2.0",
            "id": idx,
            "method": "tools/call",
            "params": {
                "name": "gno_call",
                "arguments": {
                    "profile": "testnet",
                    "realm": realm,
                    "func": "AnchorPublication",
                    "args": [
                        pub["id"],
                        pub["channel"],
                        pub["title"],
                        pub["sha256"],
                        str(pub["qa_score_permille"]),
                        str(pub["slop_removed"]),
                        str(pub["citations"]),
                        pub["formats"],
                        f"Audited by WaveWeaver Stage 6 QA ({pub['qa_score']}/100) with {pub['citations']} primary citations.",
                    ],
                },
            },
        })
        print(f"[{pub['id']}] -> {json.dumps(res)}")

    proc.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
