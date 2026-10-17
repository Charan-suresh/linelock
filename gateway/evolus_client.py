"""Calls published Evolus REST paths. https://evolus.ai/en/developers"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import httpx

LANGUAGE_NAMES = {
    "de": "German",
    "it": "Italian",
    "en": "English",
    "fr": "French",
}


def _headers() -> dict[str, str]:
    return {
        "X-ApiKey": os.environ["EVOLUS_API_KEY"],
        "X-Application-Id": os.environ["EVOLUS_APPLICATION_ID"],
    }


def _base() -> str:
    return os.environ.get("EVOLUS_BASE_URL", "https://api.evolus.ai").rstrip("/")


def start_workflow(case_id: int, disposition: str, decision: dict | None, amount: float) -> dict:
    workflow_id = os.environ["EVOLUS_WORKFLOW_ID"]
    summary = json.dumps(
        {
            "case_id": case_id,
            "disposition": disposition,
            "responsibility": None if decision is None else decision.get("responsibility"),
            "amount": amount,
        }
    )
    response = httpx.post(
        f"{_base()}/api/v1/workflows/{workflow_id}/execute",
        headers=_headers(),
        files={"input": (None, summary)},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    execution_id = payload.get("executionId") or response.headers.get("X-Workflow-Execution-Id")
    status = "queued"
    result = payload
    for _ in range(8):
        time.sleep(1)
        try:
            poll = httpx.get(
                f"{_base()}/api/v1/workflows/{workflow_id}/executions/{execution_id}",
                headers=_headers(),
                timeout=30,
            )
            poll.raise_for_status()
        except httpx.HTTPError:
            continue
        result = poll.json()
        status = result.get("status", status)
        if status in ("Completed", "Failed"):
            break
    return {
        "execution_id": execution_id,
        "status": status,
        "target": "evolus",
        "result": result,
    }


def translate_text(text: str, language: str) -> str:
    target = LANGUAGE_NAMES.get(language.lower(), language)
    response = httpx.post(
        f"{_base()}/api/v1/ai-tools/translate/run",
        headers={**_headers(), "Content-Type": "application/json"},
        json={"text": text, "options": {"target": target, "style": "formal"}},
        timeout=60,
    )
    response.raise_for_status()
    return response.json().get("output", "")


def extract_documents(folder: Path) -> list[dict]:
    agent_id = os.environ["EVOLUS_AGENT_ID"]
    extractor_id = os.environ["EVOLUS_EXTRACTOR_ID"]
    names = [
        "po",
        "delivery_note",
        "material_cert",
        "supplier_report",
        "cmm_report",
        "drawing",
    ]
    extractions = []
    for name in names:
        path = folder / f"{name}.pdf"
        with path.open("rb") as handle:
            response = httpx.post(
                f"{_base()}/api/v1/agents/{agent_id}/json/{extractor_id}/ask-file",
                headers=_headers(),
                files={"file": (path.name, handle, "application/pdf")},
                timeout=120,
            )
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict) and "fields" in payload:
            extractions.append({"document": name, "fields": payload["fields"]})
            continue
        raise RuntimeError(
            f"Evolus extractor returned a shape this gateway does not read for {name}. "
            "The schema in the workspace has to return an object with a fields map."
        )
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
