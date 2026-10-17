import json
from pathlib import Path

import extract
import rules

PACKETS = Path(__file__).resolve().parents[1] / "data" / "packets"


def _case(name: str) -> dict:
    folder = PACKETS / name
    drawing = json.loads((folder / "drawing.json").read_text())
    extractions = extract.extract_packet(folder)
    ordered = next(
        item["fields"]["drawing_revision"]["value"]
        for item in extractions
        if item["document"] == "po"
    )
    # The unit test feeds a correct mapping. The live gate asks the model.
    mapping = []
    for item in extractions:
        features = item["fields"].get("features")
        if not features:
            continue
        aliases = {
            "bohrung a": "C4",
            "foro principale": "C4",
            "laenge": "C1",
            "lunghezza": "C1",
            "breite": "C2",
            "larghezza": "C2",
            "dicke": "C3",
            "spessore": "C3",
            "c1": "C1",
            "c2": "C2",
            "c3": "C3",
            "c4": "C4",
        }
        for feature in features["value"]:
            mapping.append(
                {
                    "supplier_feature": feature["name"],
                    "characteristic_id": aliases[feature["name"].lower()],
                    "unit": feature["unit"],
                    "measured_value": feature["value"],
                    "source_document": item["document"],
                }
            )
    result = rules.evaluate(drawing, extractions, mapping)
    assert ordered
    return result


def test_packet_1_releases():
    result = _case("P01")
    assert result["disposition"] == "release"
    assert result["reasons"] == []


def test_packet_6_quarantines_on_bore():
    result = _case("P06")
    assert result["disposition"] == "quarantine"
    assert "out_of_tolerance" in result["reasons"]


def test_packet_9_is_a_revision_conflict_not_a_supplier_fail():
    result = _case("P09")
    assert result["disposition"] == "quarantine"
    assert "revision_conflict" in result["reasons"]
    assert "out_of_tolerance" not in result["reasons"]


def test_unknown_characteristic_holds():
    result = _case("P01")
    folder = PACKETS / "P01"
    drawing = json.loads((folder / "drawing.json").read_text())
    extractions = extract.extract_packet(folder)
    bad = [
        {
            "supplier_feature": "Bohrung A",
            "characteristic_id": "C99",
            "unit": "mm",
            "measured_value": 22.0,
            "source_document": "cmm_report",
        }
    ]
    checked = rules.evaluate(drawing, extractions, bad)
    assert checked["disposition"] == "hold"
    assert "mapping_invalid" in checked["reasons"]
    assert result["disposition"] == "release"


def test_row_without_a_measurement_holds():
    folder = PACKETS / "P01"
    drawing = json.loads((folder / "drawing.json").read_text())
    extractions = extract.extract_packet(folder)
    bad = [{"supplier_feature": "Bohrung A", "characteristic_id": "C4", "unit": "mm", "source_document": "cmm_report"}]
    checked = rules.evaluate(drawing, extractions, bad)
    assert checked["disposition"] == "hold"
    assert "mapping_invalid" in checked["reasons"]


def test_packet_11_holds_for_the_gauge():
    result = _case("P11")
    assert result["disposition"] == "hold"
    assert result["reasons"] == ["gauge_invalid"]
    assert result["gauge_valid"] is False
