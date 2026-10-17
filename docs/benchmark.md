# Benchmark

This run did not use an AMD card. `LLM_BASE_URL` was the local stand-in, which returns a prepared answer and does not generate tokens. There is no tokens-per-second number, and none should be shown as if it were measured on AMD.

Twelve packets through the gateway. Median case time 33 ms. Fastest 21 ms. Slowest 60 ms.

When a droplet answers `/v1/models` for `Qwen/Qwen2.5-7B-Instruct`, run `python eval/run.py` against that endpoint and replace this file with tokens per second, time to first token, the median case time, and the card name. Those figures are not in this file.
