# DeepSeek-V4.1-Flash, self-hosted: the level gate (pre-registered 2026-10-06, before its runs)

The user (2026-10-06): Qwen3.5 has not been a good enough local model to review with, because it does
not follow the conventions closely enough; would another local model do better? They chose
DeepSeek-V4.1-Flash, the largest recent open model that fits on `first`:
- 763B total parameters, 8B active, 552B backbone;
- FP8 with FP4 experts, 510 GB;
- MIT licence, released 2026-09-10.

## The condition

`configs/pr_review_v5_dev_medium_local_ds41_contract2.yaml`: contract v2 under `ape_agent`, the
gpt_5.2 config with only the model changed, as the local Qwen was. The model is
`local_deepseek_v4.1_flash` (`LLMProvider.LOCAL`), so the run plan names it.

The server is `/research/projects/proofedit/ya475/localmodel/serve_ds41.sbatch`:
- vLLM 0.30, 8 GPUs;
- the `deepseek_v41` tool and reasoning parsers, DeepGEMM off;
- weights downloaded to `/tmp` when the job starts.

Judged with judge v9 on `elm_gpt_5_mini` (`b36cd8ca`, checked against the direct judge in
`../judge-elm-2026-10-06/`), dev held-out 12, 23 obligations.

Runs, in order:
1. **Basic probes first** (`../local-vllm-2026-10-02/probes/probe_basic.py`): prefix cache hit and
   reported, reasoning on by default and `none` turning it off, tool calls schema-valid under
   `auto`. A failure here stops the gate, and the runs below are not made.
2. **`iter_ds41_contract2_high_rep1..3`**: `reasoning_effort: high`. This is the primary condition,
   because DeepSeek thinks by default and is evaluated at high effort, and every gpt cell on this
   scale ran at high effort. Its encoder drops earlier turns' thinking (`drop_thinking`), so
   reasoning is not carried across turns as it was for gpt.
3. **`iter_ds41_contract2_none_rep1`**: reasoning off, the setting Qwen's floor reading used. One rep,
   for speed and comparison.

## The scale and the reading rule (stated before any run)

Same scale as `../local-quality-2026-10-02/`:

| reviewer | obligations (of 23) |
|---|---|
| Opus 5.5 / Opus 5 | 7, 7 / 8 |
| gpt-5.5 / Opus 4.8 | 3 / 3 |
| gpt_5.2 | 2 |
| local Qwen3.5-397B (off) | 2, 0, 2 (mean 1.3) |

On the mean of the three `high` reps:
- **≥ 5 of 23: above the floor.** It can carry design iteration, subject to a design pair run on
  both it and Opus, as before.
- **4: between.** Better than every model short of Opus 5.x; useful for iteration on volume-driven
  designs, not yet for judging small design deltas.
- **≤ 3: at the floor** with gpt-5.5 and Opus 4.8. Early testing only, but still a better local
  model than Qwen if the mean exceeds 1.33 by a judge flip or more (≥ 2.5).

Read beside it: findings per PR, held-out PRs with no finding, judged pairs, hits per finding,
control emission (`../local-unlock-2026-10-03/screen.py`), and wall clock per rep.

Caveats carried into any reading:
- A one-obligation difference across the judge move is noise.
- The dev PRs (2025-12) are inside DeepSeek-V4.1's training window, as they are for every
  reviewer on this scale.

## Result (2026-10-07): it does not run on `first`'s GPUs. The gate was never reached

Two server starts, both stopped by `run_ds41_gate.sh` at the traceback, with the node released at
once. No review ran and nothing was spent.

1. **Job 432149 (vLLM 0.30, 2026-10-06 19:37):** the weights downloaded in 493 s (476 GB). Startup
   then died on "FLASHINFER_MLA_SPARSE_DSV4 on SM120 requires a FlashInfer DSV4 sparse MLA decode
   specialization for (num_q_heads=8, top_k=128)".
   - That shape *is* in the installed FlashInfer's table.
   - The real cause: vLLM's `has_flashinfer()` is False without prebuilt cubins or an `nvcc` on
     PATH, and every FlashInfer check after it reports a missing kernel.
   - Fixed by installing `flashinfer-cubin` and `flashinfer-jit-cache` for cu130
     (`python -m flashinfer download-kernels --cuda-version cu130`). The node's own CUDA 13.0
     toolkit, `/usr/local/cuda-13.0` (the default `/usr/local/cuda` is 12.9), is now on PATH too.
2. **Job 432871 (vLLM 0.30, 2026-10-07 04:48):** the model loaded (47.8 GiB a GPU in 116 s), then
   died building attention metadata on DeepGEMM's `block_kv == 32 or block_kv == 64`.

**Why no setting fixes it, in 0.30 or in 0.31.0** (released 2026-10-05 with "DeepGEMM ... SM120
fixes"; installed alongside as `localmodel/vllm031-env` and checked statically, not run):
- On SM120, V4.1's sparse attention has one backend, `FLASHINFER_MLA_SPARSE_DSV41`, whose only
  kernel block size is 128.
- Its indexer computes paged MQA logits with DeepGEMM: "DeepGEMM is required for the paged MQA
  logits on CUDA devices". The only other implementations are for ROCm and CPU.
- DeepGEMM's compiled assertion is the same in both versions: on arch 12 it accepts `block_kv` 64
  for FP8, or 32/64 for FP4.
- The indexer passes `block_size // tokens_per_state`, which differs by layer compression ratio,
  so no single block size gives every layer 64.
- The FP4 indexer cache, which would allow 32, is refused below SM10x ("requires Blackwell
  datacenter GPUs").

**What would reopen it:**
- a vLLM release with an SM120 indexer path;
- a local patch routing the CUDA indexer to the Triton kernel vLLM ships for ROCm, which is
  unverified for correctness;
- another serving engine;
- datacenter GPUs (H100/H200/B200).

## Correction (2026-10-07): not a hard limit. It runs with patches on the same hardware

The conclusion above holds for **stock** vLLM 0.30/0.31 only. Others serve DeepSeek-V4.1-Flash on
8x RTX PRO 6000 (SM120). The record, from `vllm-project/vllm#59203` (17 comments), `#56700`,
`#53635`, `vllm-project/DeepGEMM#28` and `sgl-project/sglang#40877`:

- **The cause is as diagnosed here.** V4.1 has compress-ratio 1 and 2 layers, and the indexer sees
  `block_size // cr` states, while DeepGEMM's arch-12 FP8 path needs exactly 64. So block 128 hits
  `attention.hpp:409`, our failure, and block 64 hits `attention.hpp:484`.
- **2026-09-30, validated on 8x RTX PRO 6000:** correct output, GSM8K 99/100, ~90 tok/s single
  stream. The stack was nightly `0.30.1rc1.dev382` with PR #57292 (64-token kernel blocks),
  FlashInfer built from main (runtime page sizes, flashinfer#5197) and DeepGEMM from
  vllm-project/DeepGEMM@17ca18f (page-32 support, #14). DeepGEMM was built into vLLM, needing
  gcc >= 13, with `FLASHINFER_DISABLE_VERSION_CHECK=1`. An earlier geometry (#56509) started but
  returned all-NaN logits, so a wrong geometry fails silently, not loudly.
- **2026-10-07, the author's follow-up:** #57292 no longer suffices on newer nightlies. The fix is
  per-layer block sizes, five Python-only changes:
  - `get_supported_kernel_block_sizes()` returns `[64, 128]` on SM120 in `indexer.py`,
    `deepseek_v41/sparse_mla.py` and `deepseek_v41/nvidia/flashinfer_sparse.py`;
  - `deepseek_v41/attention.py` gives the MLA, indexer and SWA specs `block_size = 64 * max(1,
    compress_ratio)`, so every indexer view is 64 states.

  Validated on nightly dev738 (2026-10-06) with FlashInfer main and NCCL 2.32.3: 17x19=323, all
  CUDA graphs captured, 117 tok/s at concurrency 1 and 1,061 at 32. Not yet a PR; vLLM main
  unchanged as of 2026-10-07.

Pitfalls reported there:
- an FP8 KV-cache scale-layout corruption visible only past 100K tokens (#56700);
- the FlashInfer cutlass MoE autotune hanging (use `--no-enable-flashinfer-autotune`).

## It serves and computes correctly (2026-10-07, job 432906)

The patch in `patch/` on vLLM nightly `0.31.1rc1.dev29+g42ecc8eeb`, with FlashInfer 0.7.1rc4
(cubin + sm120f jit-cache, `FLASHINFER_DISABLE_VERSION_CHECK=1`) and CUDA 13.0.

- **Serve flags:** `--kv-cache-dtype fp8 --attention-config
  '{"backend":"FLASHINFER_MLA_SPARSE_DSV41","indexer_kv_dtype":"fp8"}'
  --no-enable-flashinfer-autotune`, with DeepGEMM on (vLLM's default).
- **Startup:** launch to serving in **4 min** with the weights already in `/tmp`.
  - vLLM logged "Setting kv cache block size to 64 for
    FLASHINFER_MLA_SPARSE_DSV41/DEEPSEEK_SPARSE_SWA/DEEPSEEK_V41_INDEXER/CompressorBackend";
  - MoE on `DEEPGEMM_MXFP4`;
  - KV cache 4,329,003 tokens; CUDA graphs captured.
- **The first patched start (job 432885) had DeepGEMM off,** a holdover from the Qwen setup.
  - The dense FP8 layers fell to FlashInfer's `mxfp8_gemm`, which autotuned for over 50 minutes
    without finishing or saving its results; MoE fell to Marlin.
  - DeepGEMM's JIT works here now with the node's CUDA 13.0 toolkit and gcc 13.
- **`probe_correct.py`** (`probe_correct_ds41.out`): 17x19 -> `323`, and GSM8K **19/20** (the
  miss off by one). This passes the bar of 17, so the per-layer geometry does not produce the
  all-NaN output a wrong geometry gives.
- **The gate script now runs as a Slurm job** (`ds41-gate`, no GPUs, 120 GB) on the same node. Run
  under `setsid nohup`, it did not survive the Claude session that started it ending.

## Correction (2026-10-07): the thinking was dropped by our client, not by the encoder

The pre-registration above says DeepSeek's encoder drops earlier turns' thinking. It does not do so
here. `encoding.py` turns `drop_thinking` off whenever a message defines tools ("if any message has
tools defined, don't drop thinking"), and even with it on, only turns before the last user message
lose their thinking. Our client dropped it: `LLMProvider.LOCAL` used `OpenAIMessageFormatter`, which
rebuilds each message from an allowlist without `reasoning_content`.

- **Measured on the live server.** One tool round with 1,020 tokens of earlier thinking gives a
  prompt of 355 tokens with no reasoning field and 1,375 with it, under either `reasoning_content`
  or `reasoning`.
- **Seen in the runs.** In `iter_ds41_contract2_high_rep1`, PR 33362 generated 189k tokens over 21
  turns while its 21st prompt was 56.5k. Each turn re-derived its reasoning, about 8k tokens a turn.
- **Fixed in `client.py`.** LOCAL now takes the plain `MessageFormatter`
  (`tests/ape/test_elm_provider.py::test_a_local_model_gets_its_earlier_thinking_back`).

So the four reps started on 2026-10-07 ran with every turn's thinking discarded. The `none` rep is
unaffected, since it has no thinking to carry. The three `high` reps measure re-derived thinking, not
the condition the pre-registration meant.
