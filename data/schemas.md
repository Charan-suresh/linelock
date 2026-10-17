# Data formats

Agreed in Phase 0. Gateway, packets, and the agent prompt all use these names.

## Packet folder

```
data/packets/P01/
  po.pdf
  drawing.json
  drawing.pdf
  delivery_note.pdf
  material_cert.pdf
  supplier_report.pdf
  cmm_report.pdf
  calibration.json
  expected.json          # label, never read by the gateway
```

`data/library/` holds the quality agreements, supply contracts, and the plant non-conformance procedure. Team-written. Not copied from a standard.

## drawing.json

```json
{
  "drawing_no": "DRW-441",
  "part_no": "BRK-220",
  "revisions": {
    "C": {
      "characteristics": [
        {"id": "C4", "name": "bore diameter", "nominal": 22.0, "lower": 22.0, "upper": 22.021, "unit": "mm"}
      ]
    }
  }
}
```

## calibration.json

```json
{"gauge_id": "G-7", "valid_until": "2026-12-01"}
```

## Objects between steps

`Extraction`

```json
{"document": "supplier_report", "fields": {"heat_no": {"value": "H-55", "confidence": 0.95}}}
```

`Mapping` — agent output, one row per supplier or CMM feature

```json
[{"supplier_feature": "Bohrung A", "characteristic_id": "C4", "unit": "mm", "measured_value": 22.008, "source_document": "supplier_report"}]
```

`Conformance` — rules output

```json
{
  "characteristics": [{"id": "C4", "measured": 22.008, "lower": 22.0, "upper": 22.021, "pass": true}],
  "identities": [{"field": "heat_no", "values_by_document": {}, "match": true}],
  "gauge_valid": true,
  "low_confidence_fields": [],
  "disposition": "release",
  "reasons": []
}
```

`disposition` is `release`, `quarantine`, or `hold`.

`AgentDecision` — only after quarantine or hold

```json
{
  "responsibility": "supplier",
  "cited_clause": {"document": "qa-mueller.md", "clause_id": "Q-4", "quote": "..."},
  "mrb_recommendation": "return_to_supplier",
  "ncr_text": "...",
  "supplier_email": "..."
}
```

`responsibility` is `supplier`, `internal`, or `unclear`.
