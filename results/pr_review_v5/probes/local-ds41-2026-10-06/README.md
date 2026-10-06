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
