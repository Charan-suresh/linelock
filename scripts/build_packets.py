"""Write the four Phase 1 packets. Run from the linelock/ directory."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdftext import make_pdf

ROOT = Path(__file__).resolve().parents[1]
PACKETS = ROOT / "data" / "packets"

REV_C = [
    {"id": "C1", "name": "overall length", "nominal": 120.0, "lower": 119.8, "upper": 120.2, "unit": "mm"},
    {"id": "C2", "name": "width", "nominal": 45.0, "lower": 44.9, "upper": 45.1, "unit": "mm"},
    {"id": "C3", "name": "thickness", "nominal": 12.0, "lower": 11.9, "upper": 12.1, "unit": "mm"},
    {"id": "C4", "name": "bore diameter", "nominal": 22.0, "lower": 22.0, "upper": 22.021, "unit": "mm"},
]
REV_B = [
    {**item, "upper": 22.050, "lower": 21.980} if item["id"] == "C4" else item for item in REV_C
]


def drawing(part_no: str = "BRK-220") -> dict:
    return {
        "drawing_no": "DRW-441",
        "part_no": part_no,
        "material": "42CrMo4",
        "revisions": {"B": {"characteristics": REV_B}, "C": {"characteristics": REV_C}},
    }


def write_pdf(path: Path, lines: list[str]) -> None:
    path.write_bytes(make_pdf(lines))


def packet(
    folder: str,
    *,
    supplier: str,
    language: str,
    po_no: str,
    po_revision: str,
    lot: str,
    heat_delivery: str,
    heat_cert: str,
    inspection_revision: str,
    features: list[tuple[str, float]],
    cmm: dict[str, float],
    gauge_until: str,
    measured_on: str,
    expected: dict,
    cert_grade: str = "42CrMo4",
    extra_supplier: list[str] | None = None,
    extra_delivery: list[str] | None = None,
) -> None:
    dest = PACKETS / folder
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "drawing.json").write_text(json.dumps(drawing(), indent=2))
    (dest / "calibration.json").write_text(
        json.dumps({"gauge_id": "G-7", "valid_until": gauge_until}, indent=2)
    )
    (dest / "expected.json").write_text(json.dumps(expected, indent=2))
    write_pdf(
        dest / "drawing.pdf",
        [
            "Drawing DRW-441",
            "Part BRK-220 brake caliper bracket forging",
            "Material 42CrMo4",
            "Revision C bore diameter C4 22.000 to 22.021 mm",
            "Revision B bore diameter C4 21.980 to 22.050 mm",
            "C1 overall length 119.8 to 120.2 mm",
            "C2 width 44.9 to 45.1 mm",
            "C3 thickness 11.9 to 12.1 mm",
        ],
    )
    write_pdf(
        dest / "po.pdf",
        [
            f"Purchase order {po_no}",
            f"Supplier {supplier}",
            "Part BRK-220",
            "Drawing DRW-441",
            f"Drawing revision {po_revision}",
            "Quantity 40",
            "Unit price EUR 18.40",
        ],
    )
    write_pdf(
        dest / "delivery_note.pdf",
        [
            f"Delivery note supplier {supplier}",
            f"Purchase order {po_no}",
            "Part BRK-220",
            f"Lot {lot}",
            f"Heat {heat_delivery}",
            "Quantity 40",
            *(extra_delivery or []),
        ],
    )
    write_pdf(
        dest / "material_cert.pdf",
        [
            "Material certificate type 3.1",
            f"Supplier {supplier}",
            f"Material grade {cert_grade}",
            f"Heat {heat_cert}",
            "Part BRK-220",
        ],
    )
    feature_lines = [
        f"Supplier inspection report {supplier}",
        f"Language {language}",
        f"Inspected to drawing revision {inspection_revision}",
        f"Lot {lot}",
        f"Heat {heat_delivery}",
    ]
    for name, value in features:
        feature_lines.append(f"Feature {name} {value} mm")
    feature_lines.extend(extra_supplier or [])
    write_pdf(dest / "supplier_report.pdf", feature_lines)
    cmm_lines = [
        "CMM report Officine Meccaniche Riviera",
        f"Drawing revision {inspection_revision}",
        f"Gauge G-7",
        f"Measured on {measured_on}",
        f"Lot {lot}",
    ]
    for cid, value in cmm.items():
        cmm_lines.append(f"Characteristic {cid} {value} mm")
    write_pdf(dest / "cmm_report.pdf", cmm_lines)


def main() -> None:
    packet(
        "P01",
        supplier="Mueller Stahl GmbH",
        language="de",
        po_no="PO-1001",
        po_revision="C",
        lot="L-100",
        heat_delivery="H-55",
        heat_cert="H-55",
        inspection_revision="C",
        features=[("Laenge", 120.01), ("Breite", 45.02), ("Dicke", 12.01), ("Bohrung A", 22.008)],
        cmm={"C1": 120.01, "C2": 45.02, "C3": 12.01, "C4": 22.008},
        gauge_until="2026-12-01",
        measured_on="2026-10-01",
        expected={
            "disposition": "release",
            "mapping": {"Bohrung A": "C4", "Laenge": "C1", "Breite": "C2", "Dicke": "C3"},
        },
    )
    packet(
        "P06",
        supplier="Mueller Stahl GmbH",
        language="de",
        po_no="PO-1006",
        po_revision="C",
        lot="L-106",
        heat_delivery="H-61",
        heat_cert="H-61",
        inspection_revision="C",
        features=[("Laenge", 120.00), ("Breite", 45.00), ("Dicke", 12.00), ("Bohrung A", 22.061)],
        cmm={"C1": 120.00, "C2": 45.00, "C3": 12.00, "C4": 22.061},
        gauge_until="2026-12-01",
        measured_on="2026-10-02",
        expected={
            "disposition": "quarantine",
            "reasons_contain": ["out_of_tolerance"],
            "responsibility": "supplier",
            "clause_id": "Q-4",
            "amount": 110.4,
        },
    )
    packet(
        "P09",
        supplier="Officine Bianchi",
        language="it",
        po_no="PO-1009",
        po_revision="B",
        lot="L-109",
        heat_delivery="H-70",
        heat_cert="H-70",
        inspection_revision="C",
        features=[("lunghezza", 120.00), ("larghezza", 45.00), ("spessore", 12.00), ("foro principale", 22.040)],
        cmm={"C1": 120.00, "C2": 45.00, "C3": 12.00, "C4": 22.040},
        gauge_until="2026-12-01",
        measured_on="2026-10-03",
        expected={
            "disposition": "quarantine",
            "reasons_contain": ["revision_conflict"],
            "responsibility": "internal",
        },
    )
    packet(
        "P11",
        supplier="Mueller Stahl GmbH",
        language="de",
        po_no="PO-1011",
        po_revision="C",
        lot="L-111",
        heat_delivery="H-80",
        heat_cert="H-80",
        inspection_revision="C",
        features=[("Laenge", 120.00), ("Breite", 45.00), ("Dicke", 12.00), ("Bohrung A", 22.010)],
        cmm={"C1": 120.00, "C2": 45.00, "C3": 12.00, "C4": 22.010},
        gauge_until="2026-09-01",
        measured_on="2026-10-04",
        expected={"disposition": "hold", "reasons_contain": ["gauge_invalid"], "amount": 0},
    )
    clean = [("Laenge", 120.0), ("Breite", 45.0), ("Dicke", 12.0), ("Bohrung A", 22.01)]
    italian = [("lunghezza", 120.0), ("larghezza", 45.0), ("spessore", 12.0), ("foro principale", 22.01)]
    for index, (folder, supplier, language, features) in enumerate(
        [
            ("P02", "Mueller Stahl GmbH", "de", clean),
            ("P03", "Officine Bianchi", "it", italian),
            ("P04", "Mueller Stahl GmbH", "de", clean),
            ("P05", "Officine Bianchi", "it", italian),
        ],
        start=2,
    ):
        packet(
            folder,
            supplier=supplier,
            language=language,
            po_no=f"PO-100{index}",
            po_revision="C",
            lot=f"L-10{index}",
            heat_delivery=f"H-2{index}",
            heat_cert=f"H-2{index}",
            inspection_revision="C",
            features=features,
            cmm={"C1": 120.0, "C2": 45.0, "C3": 12.0, "C4": 22.01},
            gauge_until="2026-12-01",
            measured_on="2026-10-01",
            expected={"disposition": "release", "amount": 0},
        )
    packet(
        "P07",
        supplier="Mueller Stahl GmbH",
        language="de",
        po_no="PO-1007",
        po_revision="C",
        lot="L-107",
        heat_delivery="H-71",
        heat_cert="H-71",
        inspection_revision="C",
        features=clean,
        cmm={"C1": 120.0, "C2": 45.0, "C3": 12.0, "C4": 22.01},
        gauge_until="2026-12-01",
        measured_on="2026-10-05",
        cert_grade="16MnCr5",
        expected={
            "disposition": "quarantine",
            "reasons_contain": ["material_mismatch"],
            "responsibility": "supplier",
            "clause_id": "Q-5",
            "amount": 110.4,
        },
    )
    packet(
        "P08",
        supplier="Mueller Stahl GmbH",
        language="de",
        po_no="PO-1008",
        po_revision="C",
        lot="L-108",
        heat_delivery="H-88",
        heat_cert="H-99",
        inspection_revision="C",
        features=clean,
        cmm={"C1": 120.0, "C2": 45.0, "C3": 12.0, "C4": 22.01},
        gauge_until="2026-12-01",
        measured_on="2026-10-06",
        expected={"disposition": "hold", "reasons_contain": ["heat_conflict"], "amount": 0},
    )
    packet(
        "P10",
        supplier="Mueller Stahl GmbH",
        language="de",
        po_no="PO-1010",
        po_revision="C",
        lot="L-110",
        heat_delivery="H-10",
        heat_cert="H-10",
        inspection_revision="C",
        features=clean,
        cmm={"C1": 120.0, "C2": 45.0, "C3": 12.0, "C4": 22.01},
        gauge_until="2026-12-01",
        measured_on="2026-10-07",
        extra_supplier=["Defect cosmetic marks on a non-functional face"],
        expected={
            "disposition": "quarantine",
            "reasons_contain": ["cosmetic_excluded"],
            "responsibility": "internal",
            "clause_id": "Q-7",
            "amount": 0,
        },
    )
    packet(
        "P12",
        supplier="Mueller Stahl GmbH",
        language="de",
        po_no="PO-1012",
        po_revision="C",
        lot="L-112",
        heat_delivery="H-12",
        heat_cert="H-12",
        inspection_revision="C",
        features=clean,
        cmm={"C1": 120.0, "C2": 45.0, "C3": 12.0, "C4": 22.01},
        gauge_until="2026-12-01",
        measured_on="2026-10-08",
        extra_delivery=["Low confidence heat_no 0.40"],
        expected={"disposition": "hold", "reasons_contain": ["low_confidence"], "amount": 0},
    )
    print(f"wrote packets under {PACKETS}")


if __name__ == "__main__":
    main()
