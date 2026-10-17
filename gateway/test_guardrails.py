from pathlib import Path

import guardrails

LIBRARY = Path(__file__).resolve().parents[1] / "data" / "library"


def test_invented_clause_is_rejected():
    decision = {
        "responsibility": "supplier",
        "cited_clause": {"document": "qa-mueller.md", "clause_id": "Q-4", "quote": "This sentence is not in the contract."},
        "mrb_recommendation": "return_to_supplier",
    }
    result, notes = guardrails.apply(decision, LIBRARY)
    assert "citation_rejected" in notes
    assert result["responsibility"] == "unclear"
    assert result["cited_clause"]["quote"] == ""


def test_supplier_without_a_citation_escalates():
    decision = {"responsibility": "supplier", "cited_clause": {"document": "", "clause_id": "", "quote": ""}}
    result, notes = guardrails.apply(decision, LIBRARY)
    assert "supplier_without_citation" in notes
    assert result["responsibility"] == "unclear"


def test_verbatim_quote_is_kept():
    quote = "Dimensional nonconformities against the drawing revision named on the purchase order are the supplier's responsibility. The supplier bears the cost of return or replacement of the affected quantity."
    decision = {
        "responsibility": "supplier",
        "cited_clause": {"document": "qa-mueller.md", "clause_id": "Q-4", "quote": quote},
        "disposition": "release",
    }
    result, notes = guardrails.apply(decision, LIBRARY)
    assert result["responsibility"] == "supplier"
    assert "disposition" not in result
    assert notes == ["agent_cannot_release"]
