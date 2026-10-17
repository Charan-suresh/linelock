#!/usr/bin/env bash
# Serve Qwen2.5-7B-Instruct on the AMD Developer Cloud droplet.
# Run this on the droplet, after you are inside the vLLM container if the
# image starts one (the lablab quick-start guide uses: docker exec -it rocm /bin/bash).
#
# Published settings used here:
#   model Qwen/Qwen2.5-7B-Instruct, port 8000, --api-key, --tool-call-parser hermes
#   https://evolus.ai/en/developers
set -euo pipefail

if [[ $# -ne 1 || -z "$1" ]]; then
  echo "usage: serve-qwen-on-amd.sh <api-key>" >&2
  exit 1
fi

exec vllm serve Qwen/Qwen2.5-7B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --api-key "$1" \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
