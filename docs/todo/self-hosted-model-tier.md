# A self-hosted iteration model on `first`, with prompt caching that holds

**Status** — open, 2026-10-07: **DeepSeek-V4.1-Flash passes the level gate** on `first`, at 8, 6, 9 of
23 (mean 7.67) with each turn's thinking kept, at 45-53 min a rep and $0
(`results/pr_review_v5/probes/local-ds41-2026-10-06/`). Built on branch `local-deepseek`:
`LLMProvider.LOCAL`, the keyless preflight, and a formatter that keeps the thinking. What closes
this item: a design pair run on DeepSeek and Opus that moves both the same way. Until then it is
a level, not responsiveness. (2026-10-02 status: nothing built.) The user's requirement (2026-10-02): if this route is
taken, prompt caching must be handled, not assumed.

**Hand test, 2026-10-02** (`results/pr_review_v5/probes/local-vllm-2026-10-02/`). Stage 1 used
`Qwen3.5-35B-A3B-FP8` on one GPU, through vLLM 0.30 outside the repo.
- Every check passed: 9 of 9 warm calls hit the cache and report `cached_tokens`;
  `reasoning_effort: none` turns thinking off; 29 of 29 tool calls are schema-valid under `auto`.
- Replaying all 123 logged ELM sessions at concurrency 12 served **89.2%** of prompt tokens from
  cache, at a median 2.26 s against ELM's 5.53 s on the same requests. That is a smaller model, so
  it shows what serving can do, not what the 397B will do.
- Starting it needed `VLLM_USE_DEEP_GEMM=0 VLLM_MOE_USE_DEEP_GEMM=0` and
  `VLLM_USE_FLASHINFER_SAMPLER=0` (`serve.sbatch` there).
- NFS reads cap near 75 MB/s, so a cold 397B load is about 90 minutes and saturates the share.

**Stage 2, the 397B on 8 GPUs.**
- **Weights in `/tmp`.** tmpfs, kept across jobs, cleared only after 30 days unused or on a reboot.
  The download took 347 s, provided `HF_HOME` is in `/tmp`; on NFS the xet cache held it to
  76 MB/s.
- **Start-up** is 4-5 min from `sbatch` to serving.
- **Cache.** 9 of 9 warm calls hit, at 0.21-0.26 s. The 123-session replay at concurrency 12
  served 90.7% of prompt tokens from cache, at a median 4.41 s against ELM's 5.53 s on the same
  requests, ELM serving the same model at concurrency 4.
- **Long sessions.** Two logged gpt-5.2 sessions grown to 154k tokens hold a flat ~5.2-5.4 s per
  turn, 99.1% cached above 120k.
- **MTP** speeds a single stream ~1.75x, but a 12-session batch only ~10%.
- **End to end.** A real solo run through the CLI on three PRs took **2 min 58 s**: 3 findings, one
  session stopped at 40 turns.
- **The run plan does not name the endpoint** (only `scaffold_config_sha256` changes). Keep build
  item 1's own model name; do not ship the URL override as the interface.
- **Review quality: measured, gate 2 failed** (`results/pr_review_v5/probes/local-quality-2026-10-02/`,
  pre-registered in 8558192d).
  - Contract v2 under `ape_agent` on the dev held-out 12 reaches **2, 0, 2 of 23** with reasoning
    off: a mean of 1.3, union = stable = the two obligations gpt_5.2 reaches.
  - It reaches **0** with reasoning `high`.
  - That is the floor, so this model is the **early-testing tier only**: plumbing, tool parsing,
    output conformance. It cannot drive design iteration.
  - The direction is closed in `docs/dead-ends.md` ("The self-hosted Qwen3.5-397B as the
    design-iteration reviewer"), with the untried models and what reopens it.
  - Build item 1 (the provider entry) is now worth building only for the early-testing use.
  - **Used as that tier, 2026-10-04** (`results/pr_review_v5/probes/conventions-ceiling-2026-10-04/`):
    twelve runs on the two probe sets shook out the conventions ceiling probe before any
    subscription window. Given the conventions behind each PR's asks, the model's per-session reach
    on those asks went from 0.034 to 0.085 on both matchers: steadier on what it already reached,
    one new ask of 39. Supplying the knowledge did not lift it either.
- **Steering screen, 2026-10-03** (`results/pr_review_v5/probes/local-unlock-2026-10-03/`, branch
  `local-model-unlock`).
  - 13 settings over 23 judged runs, one variable each: system role, over-file, conventions,
    temperature, examples, brainstorm, specialists, diff-only, tool-free, evidence mandate, Claude
    Code harness, comments-first, and over-file with reasoning.
  - No single pass leaves the floor (best 3 of 23).
  - Over-file is the best direction: 3, 3, 0, 1, 0, and its five passes reach 4 in union.
  - Reach across every run is capped at 5 of 23.
  - The branch also carries `ApeAgentConfig.system_prompt_role` and a preflight refusal of a
    missing brief or context file.

**Cost** — no spend for generation: GPU time on the `first` partition. Judging the calibration runs
is the only bill.

**Motivating example.**
- **The free tier was set aside for speed.** The ELM Qwen tier (`configs/bases/v5_generation_qwen.yaml`)
  was dropped on 2026-09-23 because its runs took much longer than paid ones
  (`docs/plans/2026-09-23-work-enumeration.md`, "Decision, 2026-09-23 (no Qwen shakeout)").
  The Claude subscription route holds about one dev run per five_hour window, shared with
  interactive use.
- **ELM's prefix cache hits only sometimes**
  (`results/pr_review_v5/probes/elm-prefix-cache-2026-10-02/`):
  - On a ~59.5k-token prompt, 4 of 6 repeat calls returned in 0.9-1.9 s, against 6.9-16.1 s cold.
    One missed wholly (7.71 s) and one partly (6.21 s).
  - The scaffold's side is clean: 1,172 of 1,172 consecutive logged requests extend the previous one
    exactly, with identical tools.
  - ELM returns `prompt_tokens_details: null`, so our records cannot tell a hit from a miss.
- **On the runs on disk the slowness is the tail, not prompt growth.**
  - Latency does not grow with prompt size up to ~50k tokens (R² 0.335 on completion tokens alone,
    0.339 with prompt size added).
  - Short replies take a median 2.2-2.5 s and a p90 near 20 s.
  - Qwen spends ~5x `gpt_5.2`'s tokens per arm.
  - Solo-scaffold sessions run longer, so a miss costs more there: each missed turn re-pays the cold
    prefill.
- **The hardware is here and idle.** This repo's host is `first.cs.rutgers.edu`: 8x RTX PRO 6000
  Blackwell, 96 GB each, 768 GB in all. The account has the `first` partition, with no time limit and
  no owner preemption. GPUs are visible only inside a Slurm job (`srun -p first --gres=gpu:8`).
  Server and harness share localhost.

**What to build** — native, and small:
1. **A provider entry** beside the `elm_*` ones in `src/ape/llm_clients/config.py`:
   - its own canonical name (e.g. `local_qwen_3.5`), so the run plan records the endpoint;
   - priced 0.0, so `cli plan`'s zero-price token-limit refusal applies;
   - the same weights, `Qwen/Qwen3.5-397B-A17B-FP8`, so the ELM tier's token ceilings and iteration
     runs carry over.

   Every harness then reaches the model unchanged: APE-Agent directly, Claude Code through
   `scaffolds/claude_code/relay.py`, Codex through its relay. vLLM's own `/v1/messages` endpoint is
   not needed (open Claude Code bugs: vllm-project/vllm #58647, #44000).
2. **A launch script** for one vLLM engine over all 8 GPUs.
   - 400 GB of FP8 weights do not fit on 4x96 GB, so there is no two-replica split. That gives one
     prefix cache and no router to defeat it, which removes the likely cause of ELM's misses.
   - It also reaches the per-request structured-output parameters ELM's proxy drops
     (`elm-tool-schema-enforcement.md`).
3. **Caching as a checked property, not a default trusted:**
   - **Report it.** Start vLLM with `--enable-prompt-tokens-details` and state prefix caching
     explicitly. `providers/base.py::parse_usage` already reads `prompt_tokens_details.cached_tokens`
     into `UsageBreakdown`, so no client change is needed.
   - **Check it per run.** The share of prompt tokens served from cache is computed from that
     record. A run under **80%** is flagged in its report (APE-Agent on OpenAI, prefix-stable, cached
     79% of input). On a refused or flagged run, read vLLM's `/metrics` prefix-cache counters first.
   - **Size the KV cache.** It must hold the run's concurrency times its longest session without
     eviction. vLLM logs its KV capacity at start; check it against the sessions on disk.
   - **Reasoning on.** Before any reasoning-on run, check that the chat template renders earlier
     turns identically each request. A template that drops past reasoning text breaks the prefix at
     the first reasoning turn.
4. **A config twin** of the solo config, with runs named `iter_`, as the ELM tier's comment block
   requires.

**What would close it** — two gates, stated before any run:
1. **Speed.** 12 concurrent solo sessions on the dev held-out 12, with cache share at or above 80%.
   Wall clock compared with the Opus subscription run on disk.
2. **Responsiveness**, three reps a cell. Run the pair Opus already separates: the probe harness at
   11, 11 against the project harness at 7, 7, at contract v2. Accept the tier if:
   - a single pass reaches 5 or more of the 23 obligations, above the 2-3 floor where gpt_5.2,
     gpt-5.5 and Opus 4.8 sit (`docs/plans/2026-10-01-beyond-the-solo-baseline.md` §1); and
   - the probe-harness lead reproduces in the mean.

   Fail the first condition and the tier is for pipeline debugging only. The record says the model
   is what limits review (`reviewer-model-gap.md`), so a floor-bound model cannot show a design
   change.

**Start here** — `configs/bases/v5_generation_qwen.yaml` (tier boundary, token ceilings),
`src/ape/llm_clients/providers/elm_provider.py` (the workaround to drop if constrained decoding
works), `src/ape/llm_clients/config.py` (the `elm_*` entries),
`results/pr_review_v5/probes/elm-prefix-cache-2026-10-02/`.
