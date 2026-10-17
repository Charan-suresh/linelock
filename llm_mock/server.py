"""Local stand-in for vLLM. Logs every chat call. Not the AMD endpoint."""

from __future__ import annotations

import json
import logging
import re

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("llm-mock")
app = FastAPI()

ALIASES = {
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


def _map(user: str) -> list[dict]:
    rows = []
    for match in re.finditer(r"^(.+?) \| ([0-9.]+) \| (\w+) \| (\w+)\s*$", user, re.M):
        name, value, unit, source = match.groups()
        cid = ALIASES.get(name.strip().lower())
        if cid is None:
            continue
        rows.append(
            {
                "supplier_feature": name.strip(),
                "characteristic_id": cid,
                "unit": unit,
                "measured_value": float(value),
                "source_document": source,
            }
        )
    return rows


QUOTES = {
    "Q-4": "Dimensional nonconformities against the drawing revision named on the purchase order are the supplier's responsibility. The supplier bears the cost of return or replacement of the affected quantity.",
    "Q-5": "A material grade that differs from the grade named on the drawing is the supplier's responsibility. The affected quantity is not machined.",
    "Q-7": "Marks that do not affect a functional surface are excluded from supplier liability. The plant decides whether to use the parts under concession.",
    "Q-9": "The supplier is only responsible for the drawing revision written on the purchase order. A part that meets that revision is not a supplier defect, even if it fails a later revision.",
}


def _decide(user: str) -> dict:
    if "gauge_invalid" in user or "heat_conflict" in user or "mapping_invalid" in user or "low_confidence" in user:
        responsibility = "unclear"
        quote = ""
        clause_id = ""
        document = ""
        recommendation = "hold_for_review"
    elif "cosmetic_excluded" in user:
        responsibility = "internal"
        document = "qa-mueller.md"
        clause_id = "Q-7"
        quote = QUOTES["Q-7"]
        recommendation = "use_as_is"
    elif "revision_conflict" in user:
        responsibility = "internal"
        document = "qa-bianchi.md"
        clause_id = "Q-9"
        quote = QUOTES["Q-9"]
        recommendation = "no_claim"
    elif "material_mismatch" in user:
        responsibility = "supplier"
        document = "qa-mueller.md"
        clause_id = "Q-5"
        quote = QUOTES["Q-5"]
        recommendation = "return_to_supplier"
    elif "out_of_tolerance" in user:
        responsibility = "supplier"
        document = "qa-mueller.md"
        clause_id = "Q-4"
        quote = QUOTES["Q-4"]
        recommendation = "return_to_supplier"
    else:
        responsibility = "unclear"
        quote = ""
        clause_id = ""
        document = ""
        recommendation = "hold_for_review"
    return {
        "responsibility": responsibility,
        "cited_clause": {"document": document, "clause_id": clause_id, "quote": quote},
        "mrb_recommendation": recommendation,
        "ncr_text": f"Disposition follows the rules. Responsibility: {responsibility}.",
        "supplier_email": "",
    }


@app.post("/v1/chat/completions")
def chat(body: dict) -> dict:
    messages = body.get("messages") or []
    user = next((item["content"] for item in messages if item["role"] == "user"), "")
    system = next((item["content"] for item in messages if item["role"] == "system"), "")
    if "translate" in system.lower():
        log.info("step=llm task=translate")
        content = json.dumps(
            {
                "supplier_email": "Die gemessene Bohrung liegt außerhalb der Toleranz. Bitte nehmen Sie die Charge zurück."
            }
        )
    elif "map supplier" in system.lower() or user.startswith("CHARACTERISTICS"):
        log.info("step=llm task=map features=%s", len(_map(user)))
        content = json.dumps(_map(user))
    else:
        log.info("step=llm task=decide")
        content = json.dumps(_decide(user))
    return {"choices": [{"message": {"role": "assistant", "content": content}}]}


@app.get("/health")
def health() -> dict:
    return {"ok": True, "role": "local-stand-in"}
