# Evaluation

Run against the local gateway and the local model stand-in, not an AMD GPU and not Evolus.
12 of 12 packets matched their labels (disposition, reasons, responsibility, clause, amount).

| Packet | Disposition | Reasons | Responsibility | EUR | Time |
| --- | --- | --- | --- | --- | --- |
| P01 | release | — | — | 0.0 | 60 ms |
| P02 | release | — | — | 0.0 | 22 ms |
| P03 | release | — | — | 0.0 | 22 ms |
| P04 | release | — | — | 0.0 | 21 ms |
| P05 | release | — | — | 0.0 | 21 ms |
| P06 | quarantine | out_of_tolerance | supplier | 110.4 | 41 ms |
| P07 | quarantine | material_mismatch | supplier | 110.4 | 40 ms |
| P08 | hold | heat_conflict | unclear | 0.0 | 32 ms |
| P09 | quarantine | revision_conflict | internal | 0.0 | 33 ms |
| P10 | quarantine | cosmetic_excluded | internal | 0.0 | 32 ms |
| P11 | hold | gauge_invalid | unclear | 0.0 | 33 ms |
| P12 | hold | low_confidence | unclear | 0.0 | 36 ms |

Packet 6 supplier email, translated to German: Die gemessene Bohrung liegt außerhalb der Toleranz. Bitte nehmen Sie die Charge zurück.

Edited case 21: C4 changed to 22.080 mm. Disposition became quarantine.

## Hand timing

A second person still has to check three packets by hand with a stopwatch. That number is not measured, so it is not on the slides.

LineLock times for the three packets a person should check, from the table above. Same run: local stand-in, not an AMD card.

| Packet | What the person checks | LineLock | Hand check |
| --- | --- | --- | --- |
| P01 | German packet, bore named Bohrung A, all four sizes inside Rev C | 60 ms | not measured |
| P06 | Bore 22.061 mm against Rev C upper limit 22.021 mm | 41 ms | not measured |
| P11 | Gauge G-7 valid until 2026-09-01, measured 2026-10-04 | 33 ms | not measured |
