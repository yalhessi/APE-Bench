# A local vLLM server on `first`, tested by hand before any code (2026-10-02)

The pre-build test for `docs/todo/self-hosted-model-tier.md`, run outside the codebase. Does the
stack serve on these GPUs, does prefix caching hit and get reported, does reasoning stay off, do tool
calls conform, and how does it compare with ELM on identical traffic? Stage 1 is the small model of
the same family, `Qwen/Qwen3.5-35B-A3B-FP8`, on one GPU. Stage 2, the 397B, is not yet run.

**Setup** (`serve.sbatch`):
- vLLM 0.30.0 (torch 2.13, CUDA 13 wheels) in a venv outside the repo,
  `/research/projects/proofedit/ya475/localmodel/vllm-env`.
- One RTX PRO 6000 Blackwell Server Edition: 96 GB, compute capability 12.0, driver 580.
- Flags: `--enable-prefix-caching --enable-prompt-tokens-details`, `--reasoning-parser qwen3`,
  `--tool-call-parser qwen3_coder`, `--language-model-only`, `--max-model-len 131072`, bound to
  127.0.0.1.
- vLLM picks the Mamba cache mode `align` for this hybrid model when prefix caching is on, and an
  attention block of 1,056 tokens. The engine reports a KV cache of **2,524,386 tokens**, 19.3x
  concurrency at 131k (`serve_35b_startup.log`).

## What it took to start: three failures, each now a line in `serve.sbatch`

1. **DeepGEMM.**
   - Job 417881: its SM120 kernels JIT-compile only under CUDA >= 13.0, and the system toolkit is
     12.9.
   - Job 417886: pointed at pip's CUDA 13 pieces instead, the build refused them as mismatched
     (nvcc 13.4, cccl headers 13.3).
   - Fix: `VLLM_USE_DEEP_GEMM=0 VLLM_MOE_USE_DEEP_GEMM=0`. vLLM already auto-disables it for
     `qwen3_5_moe` on Blackwell ("E8M0 scale format causes accuracy degradation"), but only for the
     dense layers. The MoE path then uses Triton FP8 kernels.
2. **FlashInfer sampler.** Job 417939: the sampler JIT-builds on first use and needs `ninja` on PATH.
   Fix: `VLLM_USE_FLASHINFER_SAMPLER=0`, and the venv's `bin` on PATH.
3. **Never pre-read weights over NFS in parallel.**
   - Reads from `/research` cap near **75 MB/s**: vLLM's own first load took 472 s for 35 GB, and 8
     parallel readers sampled 77 MB/s.
   - The pre-read starved the share: a server importing from the NFS venv printed nothing for 20
     minutes, then started in seconds once the readers stopped.
   - A second load of the 35B from the page cache took **9 s**.
   - `/data/local` (local NVMe) is root-only.

## Results, 35B on one GPU (`probe_basic_35b.out`, `replay_35b_c12.*`)

**Prefix cache.** ~59.5k-token prompt, `max_tokens: 1`, three fresh prompts:

| | cold | same again | extended by a turn |
|---|---|---|---|
| latency | 2.16-2.51 s | 0.18-0.19 s | 0.18-0.19 s |
| `cached_tokens` | 0 | 59,136 | 59,136 |

All 9 of 9 warm calls hit, and every hit is reported. 59,136 is 56 blocks of 1,056 tokens; the
partial block is recomputed. Against ELM's 4 of 6 hits, with no reporting
(`../elm-prefix-cache-2026-10-02/`).

**Reasoning off.**

| request | completion tokens | reasoning text |
|---|---|---|
| nothing sent | 260 | 689 chars |
| `reasoning_effort: none` (what `ElmProvider` sends) | 4 | none |
| `chat_template_kwargs: {enable_thinking: false}` | 4 | none |

**Tool calls under `tool_choice: auto`.** The first request of 16 logged ELM sessions, as sent: 16 of
16 replies made a tool call, and **29 of 29** calls validate against their tool's JSON schema.

**Replay of all 123 logged ELM Qwen sessions** (1,264 calls), 12 sessions at a time. Each request is
sent exactly as logged, with the completion forced to the logged length.

| | local 35B | ELM 397B (logged, same requests) |
|---|---|---|
| prompt tokens served from cache | **89.2%** (93.0% from turn 5) | not reported |
| latency median / p90 / max | 2.26 / 8.98 / 127 s | 5.53 / 22.48 / 306 s |
| model time summed | 5,431 s | 12,565 s |
| run wall | 546 s | |

- Later turns under 50% cached: 2 of 1,141.
- The six slowest calls are long completions (3,128-8,879 tokens), each cached at 87-95%.
- Decoding runs at a median 18.6 ms per token per session.

**What this does and does not show.**
- Shown: the stack serves on these GPUs, the cache hits and is reported, reasoning stays off, and
  tool calls conform.
- Not shown: speed for the target model. This is a 3B-active model against ELM's 17B-active one, so
  the latency rows show what serving can do, not what the 397B will do.
- The replay forces the logged completions, so it measures load, not answers. Whether the model
  reviews well enough is the todo's responsiveness gate, untouched here.
