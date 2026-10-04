# Does ELM's Qwen reuse a prompt prefix? (2026-10-02)

The question came from the user: the ELM Qwen tier felt slow, and the suspicion was that prompt
caching is not used, so each turn of a growing tool-calling conversation is prefilled from scratch.
Three free measurements; `docs/todo/self-hosted-model-tier.md` is what they motivate.

## 1. Direct probe (`elm_cache_probe.py`, run once, 9 calls)

A fresh random ~59.5k-token prompt per trial, `max_tokens: 1`, so latency is prefill plus queueing.
Sent once, sent again unchanged, then extended by one assistant and one user turn.

| trial | cold | same again | extended by a turn |
|---|---|---|---|
| 0 | 16.09 s | 6.21 s | 1.90 s |
| 1 | 8.60 s | 0.92 s | **7.71 s** |
| 2 | 6.87 s | 1.45 s | 1.00 s |

ELM's vLLM (`system_fingerprint: vllm-0.21.0-tp4-...`) does reuse a prefix on this hybrid model:
4 of 6 repeat calls came back in 0.9-1.9 s against 6.9-16.1 s cold. Two missed, wholly (7.71 s)
or in part (6.21 s). Consistent with several replicas behind a router without prefix affinity, or
eviction under shared load; ELM's side cannot be inspected, so which is not known. n = 3 trials.

`prompt_tokens_details` is `null` on every response (vLLM fills it only under
`--enable-prompt-tokens-details`), so a hit or a miss is invisible in our own usage records.

## 2. Our side keeps the prefix (`prefix_stability.py` -> `prefix_stability.out`)

Over every logged ELM Qwen session in `data/llm_logs/2026-09-2*` and `2026-09-3*`: **1,172 of 1,172**
consecutive request pairs begin with the previous request's messages unchanged, with identical
tools. Any miss is the server's, not the scaffold's.

## 3. Latency against prompt size on real runs (`elm_latency.py` -> `elm_latency.out`)

1,282 calls in 133 sessions, all non-streamed. Latency is fitted by completion tokens alone at
R² 0.335; adding total prompt tokens gives 0.339 with a coefficient of about zero. Calls whose new
prompt is under 3k tokens decode at a median 30-35 ms per token in every prompt-size bin up to 50k.
Calls with replies under 60 tokens take a median 2.2 s (0-15k prompt) and 2.5 s (15-30k), with a
**p90 near 20 s** in both bins.

So on the runs on disk (prompts mostly under 30k, few past 50k) latency did not grow with the
conversation. What made the tier slow is the tail, queueing on a shared gateway plus the misses
in 1, and Qwen's ~5x tokens per arm against `gpt_5.2` (`configs/bases/v5_generation_qwen.yaml`).
Longer sessions, as under the solo scaffold, are where a miss costs most: a cold 59.5k prefill was
6.9-16.1 s here, paid on every turn that misses.

Reproduce from the repo root: `ape/bin/python <script>`; the probe needs `ELM_API_KEY`
(`set -a && . ~/.config/secrets/env.zsh && set +a`).
