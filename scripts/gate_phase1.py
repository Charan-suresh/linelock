"""Phase 1 exit gate. Packet 1 must release, and the model log must show the mapping call."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "data" / "packets" / "P01"
FILES = [
    "po.pdf",
    "drawing.pdf",
    "drawing.json",
    "delivery_note.pdf",
    "material_cert.pdf",
    "supplier_report.pdf",
    "cmm_report.pdf",
    "calibration.json",
]


def main() -> None:
    base = os.environ.get("GATEWAY_URL", "http://127.0.0.1:8080")
    llm = os.environ.get("LLM_BASE_URL", "http://127.0.0.1:8001/v1")
    files = [
        ("files", (name, (PACKET / name).read_bytes(), "application/octet-stream"))
        for name in FILES
    ]
    health = httpx.get(f"{base}/health", timeout=10)
    health.raise_for_status()
    llm_health = httpx.get(llm.replace("/v1", "") + "/health", timeout=10)
    llm_health.raise_for_status()
    response = httpx.post(f"{base}/packets", files=files, timeout=60)
    response.raise_for_status()
    body = response.json()
    disposition = body["record"]["conformance"]["disposition"]
    mapped = {row["supplier_feature"]: row["characteristic_id"] for row in body["record"]["mapping"]}
    print(f"case={body['id']} disposition={disposition}")
    print(f"mapping={mapped}")
    if disposition != "release":
        sys.exit(f"gate failed: expected release, got {disposition}")
    if mapped.get("Bohrung A") != "C4":
        sys.exit(f"gate failed: Bohrung A was not mapped to C4 ({mapped})")
    print("phase 1 gate passed")


if __name__ == "__main__":
    main()
