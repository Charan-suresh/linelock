"""NCR workflow. Posts to a real Evolus workflow when one is configured."""

from __future__ import annotations

import os
import uuid

import httpx

import evolus_client


def start_ncr(case_id: int, disposition: str, decision: dict | None, amount: float) -> dict:
    base = os.environ.get("EVOLUS_BASE_URL", "").strip()
    workflow_id = os.environ.get("EVOLUS_WORKFLOW_ID", "").strip()
    if not base or not workflow_id:
        return {
            "execution_id": f"local-{uuid.uuid4().hex[:8]}",
            "status": "waiting_approval",
            "target": "local",
        }
    try:
        return evolus_client.start_workflow(case_id, disposition, decision, amount)
    except httpx.HTTPError:
        return {
            "execution_id": f"local-{uuid.uuid4().hex[:8]}",
            "status": "evolus_unreachable",
            "target": "local",
        }
