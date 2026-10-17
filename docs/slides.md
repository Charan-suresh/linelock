# LineLock slides

Eight slides. Every number cites `docs/eval.md`, `docs/benchmark.md`, or is marked as an assumption. The PDF is `docs/slides.pdf`.

## 1. Problem

A wrong forging in a brake bracket is a safety problem. Giulia at receiving has a delivery note, a material certificate, the supplier's inspection report, and the shop's own measurement. The check is often late.

No number on this slide.

## 2. Product

LineLock releases the batch, quarantines it, or holds it for a person. Code checks sizes, identities, and the gauge. The model maps feature names and, when something fails, reads the contract.

No number on this slide.

## 3. Demo

Four packets, from `docs/eval.md`:

- P01 release
- P06 quarantine, supplier, EUR 110.40
- P09 quarantine, internal, EUR 0.00
- P11 hold, gauge invalid, EUR 0.00

## 4. Who decides what

Code: tolerances, document identities, gauge date, release or quarantine, the euro amount. Model: feature names, fault, the quoted clause, the report. A person: sending the claim, and any release under concession.

No number on this slide.

## 5. What we do not claim

Incoming inspection already exists. LineLock does not replace a quality system. The shop, the contracts, and the packets are written for this demo. Document extraction in this build reads the packet files locally until the Evolus workspace is connected. The model endpoint is the local stand-in until it is pointed at AMD.

The four decisions, each one a packet: the revision named on the purchase order (P09), an expired gauge held by code (P11), a claim only when a contract sentence covers the defect (P06, and not P10), and a small-shop upload gate.

## 6. Numbers

From `docs/eval.md`: 12 of 12 labelled packets agreed on disposition, reasons, responsibility, clause, and amount. Packet 6 claim is EUR 110.40. An edited C4 of 22.080 mm became quarantine.

From `docs/benchmark.md`: median case time 33 ms, fastest 21 ms, slowest 60 ms, on the local stand-in.

The hand-timed comparison is not measured. See `docs/eval.md`, section Hand timing. Do not invent it.

## 7. Buyer

Assumption, not a measured result: a quality engineer at a small shop that receives supplier parts. Offer shape: per receiving dock, per month. No price figure. Next step: one supplier at one shop in Imperia.

## 8. Appendix — the machine

From `docs/benchmark.md`: this run did not use an AMD card. There is no tokens-per-second number. Do not put one on the shop-floor screen. Replace this slide when vLLM is connected, and name the card.
