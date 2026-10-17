"""OpenAI-compatible client. Points at vLLM on AMD, or the local stand-in."""

from __future__ import annotations

import json
import os

import httpx

MAPPING_SYSTEM = """You map supplier measurement names to drawing characteristic ids.
Reply with JSON only: a list of objects
{supplier_feature, characteristic_id, unit, measured_value, source_document}.
Use only characteristic ids you were given. Do not judge pass or fail."""

DECISION_SYSTEM = """You decide supplier responsibility for a quarantined or held batch.
Reply with JSON only:
{responsibility, cited_clause: {document, clause_id, quote}, mrb_recommendation, ncr_text, supplier_email}.
responsibility is supplier, internal, or unclear.
quote must be copied verbatim from the library text you were given.
You cannot release the batch."""

TRANSLATE_SYSTEM = """Translate the supplier email into the requested language.
Reply with JSON only: {supplier_email}."""


def _chat(system: str, user: str) -> str:
    base = os.environ["LLM_BASE_URL"].rstrip("/")
    response = httpx.post(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['LLM_API_KEY']}"},
        json={
            "model": os.environ["LLM_MODEL"],
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        timeout=float(os.environ.get("LLM_TIMEOUT", "180")),
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _json_from(text: str):
    start = text.find("[")
    obj = text.find("{")
    if start >= 0 and (obj < 0 or start < obj):
        return json.loads(text[start : text.rfind("]") + 1])
    return json.loads(text[obj : text.rfind("}") + 1])


def map_features(drawing_revision: dict, extractions: list[dict]) -> list[dict]:
    lines = ["CHARACTERISTICS"]
    for item in drawing_revision["characteristics"]:
        lines.append(f"{item['id']} | {item['name']} | {item['unit']}")
    lines.append("FEATURES")
    for extraction in extractions:
        features = extraction["fields"].get("features")
        if not features:
            continue
        for feature in features["value"]:
            lines.append(
                f"{feature['name']} | {feature['value']} | {feature['unit']} | {extraction['document']}"
            )
    return _json_from(_chat(MAPPING_SYSTEM, "\n".join(lines)))


def translate(text: str, language: str) -> str:
    if os.environ.get("TRANSLATE_BACKEND") == "evolus":
        import evolus_client

        return evolus_client.translate_text(text, language)
    payload = _json_from(_chat(TRANSLATE_SYSTEM, f"Language {language}\n\n{text}"))
    return payload.get("supplier_email", "")


def decide(conformance: dict, library_text: str) -> dict:
    user = "REASONS\n" + "\n".join(conformance["reasons"]) + "\nLIBRARY\n" + library_text
    return _json_from(_chat(DECISION_SYSTEM, user))
