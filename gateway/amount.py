"""Claim amount is arithmetic. The model does not price the claim."""

from __future__ import annotations

import re
from pathlib import Path


def penalty_rate(library: Path) -> float:
    text = "\n".join(path.read_text() for path in library.glob("supply-*.md"))
    found = re.search(r"Penalty rate ([0-9.]+)", text)
    return float(found.group(1)) if found else 0.0


def claim_amount(extractions: list[dict], decision: dict | None, library: Path) -> float:
    if not decision or decision.get("responsibility") != "supplier":
        return 0.0
    price = quantity = None
    for item in extractions:
        if item["document"] != "po":
            continue
        price = float(item["fields"]["unit_price"]["value"])
        quantity = float(item["fields"]["quantity"]["value"])
    if price is None or quantity is None:
        return 0.0
    return round(price * quantity * penalty_rate(library), 2)
