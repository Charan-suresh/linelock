# LineLock

LineLock checks a supplier delivery before the parts go onto the line. Upload the packet. Code releases the batch, quarantines it, or holds it. The model maps the supplier's feature names onto the drawing, and on a failure it names the fault, quotes a contract sentence, and drafts the report. A person approves every claim and every release under concession.

The shop is fictional: Officine Meccaniche Riviera, Imperia. The part is a brake-caliper bracket forging, BRK-220. The packets, contracts, and procedure were written for this demo.

## Who decides what

| Decision | Who |
| --- | --- |
| Map a supplier feature name to a drawing characteristic | Model, on every packet |
| Tolerances, identities, gauge date, release / quarantine / hold | Code |
| Fault, quoted clause, non-conformance text, supplier email | Model, only after code has already failed the batch |
| Euro amount | Code, from the contract penalty rate, the unit price, and the quantity |
| Send the claim, or release under concession | A person |

The model cannot release a batch. A quoted sentence must appear verbatim in the named library file, or the case becomes `unclear` and nothing is sent. A supplier finding with no citation does the same.

## Architecture

```
Console (this repo's page, also deployed on Vercel)
        |
        v
Gateway (FastAPI, SQLite, append-only audit)
   extract -> map -> rules -> decide -> guardrails -> amount
        |
        v
Model endpoint (LLM_BASE_URL, OpenAI-compatible)
```

In this checkout the extractor is local (`EXTRACTOR=local`), translation uses the model endpoint, and the model endpoint is the stand-in in `llm_mock/`. That stand-in is not a 7B model and not an AMD GPU. The numbers in `docs/eval.md` and `docs/benchmark.md` are from that stand-in.

The Evolus calls, when the variables are set, use the paths in `docs/evolus-api.md`: workflow execute, the translate AI tool, and ask-file. `EVOLUS_WORKFLOW_ID` turns on the NCR workflow. `TRANSLATE_BACKEND=evolus` turns on the translate tool. Those ids come from the event workspace. Create that workspace from https://app.evolus.ai/join/AMDACT3. `scripts/setup-amd-evolus.sh` walks through the AMD droplet, vLLM, and that workspace. It does not create the accounts.

The public console is https://linelock-amber.vercel.app. It proxies to whatever gateway `GATEWAY_URL` was set to at deploy time. The free tunnel behind it expires about an hour after it starts. A droplet running this gateway on port 8080 is the URL that stays up. Judges can also use the gateway's own page at `http://127.0.0.1:8080`.

## Setup from a clean clone

Python 3.13. Python 3.14 cannot build the pinned `pydantic-core`.

```bash
cd linelock
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest gateway/test_rules.py gateway/test_guardrails.py
```

Two processes, from `linelock/`:

```bash
# model stand-in
cd llm_mock && uvicorn server:app --port 8001

# gateway, in a second shell, with the venv active
cd gateway
LLM_BASE_URL=http://127.0.0.1:8001/v1 \
LLM_API_KEY=dev-token \
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct \
uvicorn main:app --port 8080
```

Open http://127.0.0.1:8080. Health check: `curl http://127.0.0.1:8080/health`.

The packets are already in `data/packets/`. Rebuild them with `python scripts/build_packets.py` from `linelock/` if you change a packet.

## Environment

Copy `.env.example`. The processes above take the same names from the shell.

| Variable | Meaning |
| --- | --- |
| `LLM_BASE_URL` | OpenAI-compatible base URL, including `/v1` |
| `LLM_API_KEY` | Bearer token for that endpoint. `dev-token` for the stand-in |
| `LLM_MODEL` | Model name sent to the endpoint. Start with `Qwen/Qwen2.5-7B-Instruct` |
| `EXTRACTOR` | `local` reads the packet files. `evolus` calls ask-file |
| `TRANSLATE_BACKEND` | `local` uses the model endpoint. `evolus` calls the translate AI tool |
| `EVOLUS_BASE_URL` | `https://api.evolus.ai` once the workspace exists. Empty keeps the NCR step local |
| `EVOLUS_API_KEY` | `X-ApiKey`. Do not commit it |
| `EVOLUS_APPLICATION_ID` | Space id from the API keys page |
| `EVOLUS_WORKFLOW_ID` | Workflow that is turned on |
| `EVOLUS_AGENT_ID` | Agent id for ask-file. Used only when `EXTRACTOR=evolus` |
| `EVOLUS_EXTRACTOR_ID` | Extractor id for ask-file |
| `LLM_TIMEOUT` | Seconds for one model call. Default 180 |
| `DATABASE_URL` | SQLite path. The gateway currently uses `linelock/linelock.db` |

## Data

The shop, suppliers, contracts, drawing notes, and all twelve packets are fictional and written for this demo. Do not treat them as a customer's records. `expected.json` in each packet is the label. The gateway never reads it. The eval script does.

## Eval

With the gateway on port 8080 and the venv active, from `linelock/`:

```bash
python eval/run.py
```

That posts all twelve packets and compares disposition, reasons, responsibility, clause, and amount with `expected.json`. Pass one or more packet names to run a subset: `python eval/run.py P01 P06 P09 P11`.

The last recorded result is in `docs/eval.md`. It was produced with the local stand-in. It is not a measurement of a 7B model on AMD.

## What this demo does not claim

Incoming inspection already exists. LineLock does not replace a quality system. The four decisions in the pitch are the revision named on the purchase order, an expired gauge, a claim only when a contract sentence covers the defect, and a small-shop upload gate.
