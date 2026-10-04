# A local vLLM server on `first`, tested by hand before any code (2026-10-02)

The pre-build test for `docs/todo/self-hosted-model-tier.md`, run outside the codebase. Does the
stack serve on these GPUs, does prefix caching hit and get reported, does reasoning stay off, do tool
calls conform, and how does it compare with ELM on identical traffic? Stage 1 is the small model of
the same family, `Qwen/Qwen3.5-35B-A3B-FP8`, on one GPU. Stage 2 is the target,
`Qwen/Qwen3.5-397B-A17B-FP8`, the model ELM serves, on all 8 GPUs (below).

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

## Stage 2: the 397B on 8 GPUs, from a copy in `/tmp`

**Where the weights live.**
- `/tmp` on `first` is tmpfs: RAM, 544 GB free. A Slurm job sees the host's `/tmp`, and
  systemd-tmpfiles removes files there only after 30 days unused.
- So the weights are downloaded once to `/tmp/ya475-models/Qwen3.5-397B-A17B-FP8` and survive
  `scancel`. They go only on a reboot.
- The download took **347 s** for 406.2 GB, but only once `HF_HOME` pointed into `/tmp`. With
  `HF_HOME` on NFS, the xet chunk cache held the download to the NFS read cap (76 MB/s); in `/tmp`
  it ran at up to 1,250 MB/s.

**Start-up, measured from `sbatch` to serving.** The flags are in `serve.sbatch`, with
`ALIAS=Qwen/Qwen3.5-397B-A17B-FP8` so a client sending the HF id reaches the local copy.
- 237 s plain (job 417986, including this model's first torch.compile), with weights read in
  46 s.
- 275 s with MTP (job 418033).
- KV cache: 2,412,975 tokens plain, 2,092,001 with MTP, at `--max-model-len 262144`.
- vLLM disables its custom all-reduce ("not supported on more than two PCIe-only GPUs"), so
  tensor parallelism across the 8 GPUs runs on NCCL.

**Basic probes** (`probe_basic_397b.out`, `probe_basic_397b_mtp.out`):

| | plain | MTP | ELM, same model |
|---|---|---|---|
| ~59.5k prompt, cold | 6.78-6.92 s | 6.94-7.37 s | 6.87-16.09 s |
| warm repeat | **0.21-0.26 s, 9/9 hits**, reported | 0.30-0.42 s, 9/9 hits, reported | 0.92-1.90 s on hits; 2 of 6 missed; never reported |
| `reasoning_effort: none` | 4 tokens, no reasoning | 4 tokens | |
| tool calls under `auto` | 16/16 call; 23/23 schema-valid | 16/16; 25/25 | |

**Replay of all 123 logged ELM sessions at concurrency 12.** The same requests ELM's runs sent,
at its `max_concurrency: 4`:

| | plain (`replay_397b_c12.*`) | MTP (`replay_397b_mtp_c12.*`) | ELM, logged |
|---|---|---|---|
| prompt tokens from cache | **90.7%** (94.3% from turn 5) | 87.2% (91.6%) | not reported |
| latency median / p90 / max | 4.41 / 17.55 / 244.9 s | 4.08 / 15.31 / 205.0 s | 5.53 / 22.48 / 306.0 s |
| model time summed | 10,485 s | 9,325 s | 12,565 s |
| wall for the workload | 1,089 s | 978 s | |

- At 12 sessions, aggregate generation is ~320-350 tokens/s with or without MTP (server stats),
  about 28 tokens/s per session.
- MTP is accepted at 88-91% (mean acceptance length 2.8; `serve_397b_mtp_specdecode.log`). It
  speeds a single stream about 1.75x: a 387-token reply in 2.97 s against 329 in 4.43 s. Under a
  batch it gains about 10%, consistent with cross-GPU communication over PCIe, not per-token
  compute, binding there.

**Replay of two long sessions** (`replay_397b_long.*`): the logged 58- and 76-turn gpt-5.2
sessions, reasoning forced off, replies capped at 256 tokens. They grow to **154,303 tokens**, and
latency stays flat as they grow:

| prompt size | calls | median latency | cached |
|---|---|---|---|
| < 40k | 6 | 6.73 s | 78.3% |
| 40-80k | 11 | 5.91 s | 81.9% |
| 80-120k | 42 | 5.37 s | 97.9% |
| >= 120k | 75 | 5.20 s | 99.1% |

The `ELM logged` column in `replay_397b_long.out` is gpt-5.2 at `reasoning_effort: high`. It is not
comparable and is ignored here.

**What one test session costs in time.** About 4-5 min from `sbatch` to serving, then the testing,
then `scancel` frees the GPUs. The weights wait in `/tmp`; a reboot costs one ~6-minute
re-download.

## Stage 2, end to end: one real solo run through the CLI

`results/pr_review_v5/runs/iter_local397_solo_smoke4_rep1`. The project's own client,
`ElmProvider` and `ape_agent` scaffold reached the local server with no code change, through a URL
override on the existing model:

    ELM_API_KEY=local-dummy ape/bin/python -m src.mathlib_review.review.cli run \
      --config configs/pr_review_v5_solo_ape_smoke4.yaml --run-name iter_local397_solo_smoke4_rep1 \
      --set llm_config.model_name=elm_qwen_3.5 --set llm_config.reasoning_effort=none \
      --set llm_config.base_url=http://127.0.0.1:8012/v1/chat/completions \
      --set "dataset.pr_numbers=[33066,33098,33438]" --execute

This ran on the MTP server (job 418033). PR 33057 was left out because it has no prebuilt reviewed
workspace.

- **Wall clock 2 min 58 s** for three whole-PR sessions, $0.00 billed, 0 "API call failed,
  retrying".
- The sessions processed 753,334, 396,434 and 936,707 tokens over 30, 31 and 40 turns. The third
  stopped on `paused_max_turns` without submitting, so the run reports `completion_status=partial`.
- Output: 3 findings on two PRs, all evidence packets `inconclusive`, 0 published.
- Tool use, roughly, from each session's transcript:
  - file reads 26-32;
  - content searches 10-26;
  - `lean_verify` 2-4;
  - one session about 12 `lean_verify_edit` calls, so it tried edits and compiled them.
- This is one rep on three PRs, unjudged. It says the loop works and how long it takes. It says
  nothing about review quality, which is the todo's responsiveness gate.

**The run plan does not name the endpoint.** `run_plan.json` records `model_name: elm_qwen_3.5`, and
the local URL appears only inside `scaffold_config_sha256`. The hash keeps the orchestrator from
resuming across endpoints, but a reader cannot tell this run from an ELM run. That is the concrete
case for the todo's own provider entry (`local_qwen_3.5`) over a URL override.
