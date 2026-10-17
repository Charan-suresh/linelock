"""Local NCR id when no Evolus workflow is configured."""

import workflow


def test_ncr_stays_local_without_a_workflow(monkeypatch):
    monkeypatch.delenv("EVOLUS_BASE_URL", raising=False)
    monkeypatch.delenv("EVOLUS_WORKFLOW_ID", raising=False)
    result = workflow.start_ncr(1, "quarantine", {"responsibility": "supplier"}, 110.4)
    assert result["target"] == "local"
    assert result["execution_id"].startswith("local-")
    assert result["status"] == "waiting_approval"
