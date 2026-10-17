# Submission fields

Paste these. Counts were checked when this file was written.

## Title

LineLock: stop bad supplier parts at receiving

46 / 50 characters.

## Short description

LineLock checks a supplier delivery before the parts reach the line. Code releases, quarantines, or holds the batch. The model maps feature names and, on a failure, quotes the contract and drafts the claim for a person to approve.

230 / 255 characters.

## Long description

LineLock checks a supplier delivery before the parts reach the line at a small machine shop. The shop in this demo is fictional: Officine Meccaniche Riviera, in Imperia, receiving brake-caliper bracket forgings. Giulia has a delivery note, a material certificate, the supplier inspection report, and the shop's own measurement. Code compares every size with the drawing revision named on the purchase order, checks that the part, lot, and heat agree, and checks that the gauge was still in date. A passing batch is released. A failed size, material, or revision is quarantined. An uncertain field, a heat conflict, or an expired gauge is held. The model maps supplier names such as Bohrung A onto the drawing, and on a failure it names the fault, quotes a contract sentence verbatim, and drafts the report. Code computes the claim. A person approves every claim and every release under concession. The model cannot release a batch. An invented quote is rejected and nothing is sent. Incoming inspection already exists. LineLock does not replace a quality system. The twelve packets and the contracts were written for this demo. On those labels the local stand-in agreed 12 of 12, including a claim of EUR 110.40. That run was not on an AMD card. Extraction in this build reads the packet files locally until an Evolus workspace is connected. The buyer we want is a quality engineer at one receiving dock.

235 words. Minimum is 100.

## Tracks

Intelligent Industry. Evolus Business Agents on AMD.

## Tech tags

AMD Developer Cloud, ROCm, vLLM, Qwen, Evolus, FastAPI.

## Files

- Cover: `docs/cover.png`, 1920 by 1080.
- Slides: `docs/slides.pdf`.
- Video: `docs/linelock-demo.mp4`. The voice is a synthesized read of `docs/narration.txt`, over screenshots of https://linelock-amber.vercel.app. Replace it with a person's voice before the form is final.
- Demo URL: https://linelock-amber.vercel.app

## Still needs a person

Two timed rehearsals of the four-minute script. A hand stopwatch check of packets 1, 6, and 11. A git tag `v1.0` after the freeze commit. An AMD Developer Cloud droplet serving Qwen2.5-7B-Instruct, an Evolus event workspace, and a gateway URL that is not the one-hour tunnel. `bash scripts/setup-amd-evolus.sh` from `linelock/` walks those three. Until that run finishes, do not replace the stand-in numbers in `docs/eval.md`.
