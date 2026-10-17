# Evolus API paths used by this gateway

Source: [Evolus developers](https://evolus.ai/en/developers), read 14 October 2026. The event link on [evolus.ai/en/hackathon](https://evolus.ai/en/hackathon) is https://app.evolus.ai/join/AMDACT3. A workspace created somewhere else is not an event workspace. A workflow id, extractor id, and library id still come from that workspace. This file does not invent those ids.

Base URL: `https://api.evolus.ai`

REST headers on every call below: `X-ApiKey` and `X-Application-Id`. The space id on the workspace API keys page is `X-Application-Id`.

Agent chat is a different base, `https://api.evolus.ai/v1`, with `Authorization: Bearer` and `model` set to `<applicationId>:<agentId>`. LineLock's mapper and decider call vLLM directly. They do not go through agent chat.

## Workflow

`POST /api/v1/workflows/{workflowId}/execute` as multipart form data. The text field is `input`. The response is `202 Accepted` with `executionId`.

`GET /api/v1/workflows/{workflowId}/executions/{executionId}` until `status` is `Completed` or `Failed`. A workflow that is off returns `409`.

`gateway/workflow.py` sends the case id, disposition, responsibility, and amount in `input`, then polls up to eight seconds. With `EVOLUS_BASE_URL` or `EVOLUS_WORKFLOW_ID` empty, it records a local execution id and does not call the network.

A workflow named LineLock NCR can be created with `POST /api/v1/workflows` and a step of type `AiTool` (`stepType` 16). The step catalog is `GET /api/v1/workflows/step-catalog`. An empty workflow returns 409. The one wired from this workspace summarizes the case text. Library calls to `/api/v1/memories` returned 401 for the current key, so the contract files are not uploaded yet.

## Translation AI tool

`POST /api/v1/ai-tools/translate/run` with JSON `{ "text", "options": { "target", "style" } }`. The reply field used here is `output`. This uses platform credits. It runs only when `TRANSLATE_BACKEND=evolus`. Otherwise the model endpoint translates.

## Extractor

`POST /api/v1/agents/{agentId}/json/{extractorId}/ask-file` with a multipart `file`. Used only when `EXTRACTOR=evolus`. The gateway expects each reply to be an object with a `fields` map in the same shape as the local extractor. Calibration still comes from `calibration.json` in the packet.

## Library

`POST /api/v1/memories/{libraryId}/documents?language=en` with a multipart `file`. Indexing is asynchronous and uses credits. The gateway still reads `data/library/*.md` from disk for the verbatim-quote check. Uploading the same files to a library is the second copy Evolus can search. It does not replace the local check.
