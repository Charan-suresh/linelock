"""Compare live gateway results with the packet labels."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
PACKETS = ROOT / "data" / "packets"
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
    timeout = float(os.environ.get("EVAL_TIMEOUT", "180"))
    names = sys.argv[1:] or sorted(path.name for path in PACKETS.iterdir() if path.is_dir())
    failed = 0
    for name in names:
        folder = PACKETS / name
        expected = __import__("json").loads((folder / "expected.json").read_text())
        files = [("files", (item, (folder / item).read_bytes(), "application/octet-stream")) for item in FILES]
        body = httpx.post(f"{base}/packets", files=files, timeout=timeout).json()
        record = body["record"]
        problems = []
        if record["conformance"]["disposition"] != expected["disposition"]:
            problems.append(f"disposition {record['conformance']['disposition']} != {expected['disposition']}")
        for reason in expected.get("reasons_contain", []):
            if reason not in record["conformance"]["reasons"]:
                problems.append(f"missing reason {reason}")
        decision = record.get("decision") or {}
        if "responsibility" in expected and decision.get("responsibility") != expected["responsibility"]:
            problems.append(f"responsibility {decision.get('responsibility')} != {expected['responsibility']}")
        if "clause_id" in expected and (decision.get("cited_clause") or {}).get("clause_id") != expected["clause_id"]:
            problems.append("clause mismatch")
        if "amount" in expected and record.get("amount") != expected["amount"]:
            problems.append(f"amount {record.get('amount')} != {expected['amount']}")
        mapping = expected.get("mapping") or {}
        actual = {row["supplier_feature"]: row["characteristic_id"] for row in record["mapping"]}
        for feature, cid in mapping.items():
            if actual.get(feature) != cid:
                problems.append(f"mapping {feature}")
        if problems:
            failed += 1
            print(f"{name} FAIL " + "; ".join(problems))
        else:
            print(f"{name} ok {record['conformance']['disposition']}")
    if failed:
        sys.exit(f"{failed} packet(s) failed")
    print(f"eval passed ({len(names)} packets)")


if __name__ == "__main__":
    main()
