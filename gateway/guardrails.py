"""The model may explain a failure. It may not release a batch or invent a clause."""

from __future__ import annotations

from pathlib import Path


def apply(decision: dict | None, library: Path) -> tuple[dict | None, list[str]]:
    if decision is None:
        return None, []
    notes: list[str] = []
    decision.pop("disposition", None)
    quote = (decision.get("cited_clause") or {}).get("quote") or ""
    document = (decision.get("cited_clause") or {}).get("document") or ""
    clause_id = (decision.get("cited_clause") or {}).get("clause_id") or ""
    named = library / Path(document).name
    quote_ok = bool(quote) and named.is_file() and quote in named.read_text()
    if quote and not quote_ok:
        notes.append("citation_rejected")
    if decision.get("responsibility") == "supplier" and not (quote_ok and clause_id):
        notes.append("supplier_without_citation")
    if notes:
        decision["responsibility"] = "unclear"
        decision["mrb_recommendation"] = "hold_for_review"
        decision["cited_clause"] = {"document": "", "clause_id": "", "quote": ""}
    notes.append("agent_cannot_release")
    return decision, notes
