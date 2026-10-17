"""Deterministic checks. The language model does not release a batch."""

from __future__ import annotations

import json
from datetime import date

CONFIDENCE_FLOOR = 0.8


def _value(extractions: list[dict], document: str, field: str):
    for item in extractions:
        if item["document"] == document:
            found = item["fields"].get(field)
            return None if found is None else found["value"]
    return None


def _confidence(extractions: list[dict], document: str, field: str) -> float:
    for item in extractions:
        if item["document"] == document:
            found = item["fields"].get(field)
            return 0.0 if found is None else float(found["confidence"])
    return 0.0


def evaluate(drawing: dict, extractions: list[dict], mapping: list[dict]) -> dict:
    ordered_revision = str(_value(extractions, "po", "drawing_revision"))
    revision = drawing["revisions"][ordered_revision]
    characteristics = {item["id"]: item for item in revision["characteristics"]}

    low_confidence = []
    for item in extractions:
        for field, payload in item["fields"].items():
            if float(payload["confidence"]) < CONFIDENCE_FLOOR:
                low_confidence.append(f"{item['document']}.{field}")

    mapped_rows = []
    reasons: list[str] = []
    seen: set[tuple[str, str]] = set()
    for row in mapping:
        cid = row["characteristic_id"]
        spec = characteristics.get(cid)
        source = row["source_document"]
        if spec is None or row.get("unit") != spec["unit"] or (source, cid) in seen:
            reasons.append("mapping_invalid")
            continue
        seen.add((source, cid))
        measured = float(row["measured_value"])
        passed = spec["lower"] <= measured <= spec["upper"]
        mapped_rows.append(
            {
                "id": cid,
                "measured": measured,
                "lower": spec["lower"],
                "upper": spec["upper"],
                "pass": passed,
                "source_document": source,
                "supplier_feature": row["supplier_feature"],
            }
        )
    covered = {item["id"] for item in mapped_rows if item["source_document"] == "cmm_report"}
    if set(characteristics) - covered:
        reasons.append("mapping_invalid")

    identities = []
    for field, sources in (
        ("part_no", ("po", "delivery_note", "material_cert")),
        ("lot", ("delivery_note", "supplier_report", "cmm_report")),
        ("heat_no", ("delivery_note", "material_cert", "supplier_report")),
        ("drawing_revision", ("po", "supplier_report", "cmm_report")),
    ):
        values = {source: _value(extractions, source, field) for source in sources}
        match = len({value for value in values.values() if value is not None}) <= 1
        identities.append({"field": field, "values_by_document": values, "match": match})
        if not match and field == "heat_no":
            reasons.append("heat_conflict")
        if not match and field == "drawing_revision":
            reasons.append("revision_conflict")
        if not match and field in {"part_no", "lot"}:
            reasons.append("identity_mismatch")

    measured_on = _value(extractions, "cmm_report", "measured_on")
    valid_until = _value(extractions, "calibration", "valid_until")
    gauge_valid = True
    if measured_on and valid_until:
        gauge_valid = date.fromisoformat(measured_on) <= date.fromisoformat(valid_until)
    if not gauge_valid:
        reasons.append("gauge_invalid")

    cmm_rows = [row for row in mapped_rows if row["source_document"] == "cmm_report"]
    if any(not row["pass"] for row in cmm_rows):
        reasons.append("out_of_tolerance")

    drawing_material = drawing.get("material")
    cert_material = _value(extractions, "material_cert", "material")
    if drawing_material and cert_material and drawing_material != cert_material:
        reasons.append("material_mismatch")

    defect = _value(extractions, "supplier_report", "defect") or ""
    if "non-functional" in defect:
        reasons.append("cosmetic_excluded")

    if low_confidence:
        reasons.append("low_confidence")

    ordered_reasons = list(dict.fromkeys(reasons))
    if any(reason in ordered_reasons for reason in ("low_confidence", "gauge_invalid", "heat_conflict", "mapping_invalid")):
        disposition = "hold"
    elif ordered_reasons:
        disposition = "quarantine"
    else:
        disposition = "release"

    return {
        "ordered_revision": ordered_revision,
        "characteristics": [
            {key: row[key] for key in ("id", "measured", "lower", "upper", "pass")}
            for row in cmm_rows
        ],
        "identities": identities,
        "gauge_valid": gauge_valid,
        "low_confidence_fields": low_confidence,
        "disposition": disposition,
        "reasons": ordered_reasons,
    }


def load_drawing(path) -> dict:
    return json.loads(path.read_text())
