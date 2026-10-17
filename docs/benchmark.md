# Benchmark

Twelve packets through the gateway on 17 October 2026. Model `Qwen3.8-Flash-Next` on AMD's shared Radeon Cloud API at `https://developer.amd.com.cn/radeon/api/v1`, with `LLM_THINKING=off`. The card behind that API is not reported to us, so no card is named here.

Median case time 33 s. Fastest 22 s. Slowest 70 s. A case makes one model call to map features, a second to decide responsibility on a failed batch, and Evolus calls for the workflow and, on a supplier claim, the translation.

With reasoning left on, one mapping call on packet 9 took 45 s and spent 550 of 1,027 completion tokens on reasoning. With `LLM_THINKING=off` the same call took 11 s.

Tokens per second and time to first token were not measured. They belong to a private vLLM endpoint, which this run did not use.
