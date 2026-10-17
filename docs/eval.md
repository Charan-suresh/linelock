# Evaluation

Run on 17 October 2026 against the gateway in this repo, with `LLM_BASE_URL=https://developer.amd.com.cn/radeon/api/v1`, model `Qwen3.8-Flash-Next`, `LLM_THINKING=off`. That is AMD's shared Radeon Cloud model API. It is not a private vLLM endpoint and not an MI300X droplet. Translation used the Evolus translate tool, and every case started the Evolus `LineLock NCR` workflow.

10 of 12 packets matched their labels (disposition, reasons, responsibility, clause, amount). All 12 dispositions and reasons matched; those come from code. The two misses are the model choosing `unclear` where the label says `internal`. No claim was raised on either.

| Packet | Disposition | Reasons | Responsibility | Clause | EUR | Time | Label |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P01 | release | — | — | — | 0.0 | 35 s | match |
| P02 | release | — | — | — | 0.0 | 24 s | match |
| P03 | release | — | — | — | 0.0 | 22 s | match |
| P04 | release | — | — | — | 0.0 | 27 s | match |
| P05 | release | — | — | — | 0.0 | 29 s | match |
| P06 | quarantine | out_of_tolerance | supplier | Q-4 | 110.4 | 70 s | match |
| P07 | quarantine | material_mismatch | supplier | Q-5 | 110.4 | 48 s | match |
| P08 | hold | heat_conflict | unclear | — | 0.0 | 40 s | match |
| P09 | quarantine | revision_conflict | unclear | — | 0.0 | 36 s | label says internal, Q-9 |
| P10 | quarantine | cosmetic_excluded | unclear | — | 0.0 | 63 s | label says internal, Q-7 |
| P11 | hold | gauge_invalid | unclear | — | 0.0 | 31 s | match |
| P12 | hold | low_confidence | unclear | — | 0.0 | 31 s | match |

The model's answers vary between runs at temperature 0. Two earlier full runs on the same endpoint, before the last prompt and rules changes, scored 10 of 12 and 11 of 12. P09 and P10 passed in at least one of those runs.

Packet 6 supplier email, written by the model and translated to German by Evolus, opens: "Sehr geehrte Damen und Herren der Müller Stahl GmbH, wir melden eine Nichtkonformität bei der jüngsten Lieferung zu unserer Bestellung. Das Merkmal C4 wurde mit 22,061 mm gemessen …"

## Hand timing

A second person still has to check three packets by hand with a stopwatch. That number is not measured, so it is not on the slides.

| Packet | What the person checks | LineLock | Hand check |
| --- | --- | --- | --- |
| P01 | German packet, bore named Bohrung A, all four sizes inside Rev C | 35 s | not measured |
| P06 | Bore 22.061 mm against Rev C upper limit 22.021 mm | 70 s | not measured |
| P11 | Gauge G-7 valid until 2026-09-01, measured 2026-10-04 | 31 s | not measured |
