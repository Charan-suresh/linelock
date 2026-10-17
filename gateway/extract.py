"""Packet extractor. Local PDF text, or the Evolus ask-file path when configured."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from pdftext import read_pdf_lines

FIELD_PATTERNS = {
    "po_no": re.compile(r"^Purchase order (\S+)"),
    "supplier": re.compile(r"^Supplier (.+)$"),
    "part_no": re.compile(r"^Part (\S+)"),
    "drawing_no": re.compile(r"^Drawing (DRW-\S+)"),
    "drawing_revision": re.compile(r"^(?:Drawing revision|Inspected to drawing revision) (\w+)"),
    "quantity": re.compile(r"^Quantity (\d+)"),
    "unit_price": re.compile(r"^Unit price EUR ([0-9.]+)"),
    "lot": re.compile(r"^Lot (\S+)"),
    "heat_no": re.compile(r"^Heat (\S+)"),
    "material": re.compile(r"^Material grade (\S+)"),
    "gauge_id": re.compile(r"^Gauge (\S+)"),
    "measured_on": re.compile(r"^Measured on (\S+)"),
    "language": re.compile(r"^Language (\w+)"),
}


def _fields_from_lines(lines: list[str]) -> dict:
    fields: dict[str, dict] = {}
    features: list[dict] = []
    for line in lines:
        matched = False
        for name, pattern in FIELD_PATTERNS.items():
            found = pattern.match(line)
            if found:
                fields[name] = {"value": found.group(1), "confidence": 0.95}
                matched = True
                break
        if matched:
            continue
        feature = re.match(r"^Feature (.+) ([0-9.]+) mm$", line)
        if feature:
            features.append({"name": feature.group(1), "value": float(feature.group(2)), "unit": "mm"})
            continue
        characteristic = re.match(r"^Characteristic (C\d) ([0-9.]+) mm$", line)
        if characteristic:
            features.append(
                {"name": characteristic.group(1), "value": float(characteristic.group(2)), "unit": "mm", "already_id": True}
            )
            continue
        low = re.match(r"^Low confidence (\w+) ([0-9.]+)$", line)
        if low and low.group(1) in fields:
            fields[low.group(1)]["confidence"] = float(low.group(2))
            continue
        if line.startswith("Defect "):
            fields["defect"] = {"value": line.removeprefix("Defect "), "confidence": 0.95}
    if features:
        fields["features"] = {"value": features, "confidence": 0.95}
    return fields


def extract_packet(folder: Path) -> list[dict]:
    if os.environ.get("EXTRACTOR") == "evolus":
        import evolus_client

        return evolus_client.extract_documents(folder)
    return _extract_local(folder)


def _extract_local(folder: Path) -> list[dict]:
    documents = [
        "po",
        "delivery_note",
        "material_cert",
        "supplier_report",
        "cmm_report",
        "drawing",
    ]
    extractions = []
    for name in documents:
        lines = read_pdf_lines((folder / f"{name}.pdf").read_bytes())
        extractions.append({"document": name, "fields": _fields_from_lines(lines)})
    calibration = json.loads((folder / "calibration.json").read_text())
    extractions.append(
        {
            "document": "calibration",
            "fields": {
                "gauge_id": {"value": calibration["gauge_id"], "confidence": 1},
                "valid_until": {"value": calibration["valid_until"], "confidence": 1},
            },
        }
    )
    return extractions
