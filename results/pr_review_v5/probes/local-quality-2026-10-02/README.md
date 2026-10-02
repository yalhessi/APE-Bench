# Review quality on the self-hosted 397B: the level gate (pre-registered 2026-10-02, before its runs)

The question (the user, 2026-10-02): can the local model drive design iteration, or only help with
early testing? `docs/todo/self-hosted-model-tier.md`, gate 2. The serving side is settled in
`../local-vllm-2026-10-02/`. This measures review quality, on the scale every other reviewer in the
record is on.

## The condition

Contract v2 under `ape_agent`: `configs/pr_review_v5_dev_medium_gpt52_Grc_contract2.yaml`, which
gave gpt_5.2 2 of 23 and, as its gpt-5.5 twin, 3 of 23. The model is the only thing changed:

    ELM_API_KEY=local-dummy ape/bin/python -m src.mathlib_review.review.cli run \
      --config configs/pr_review_v5_dev_medium_gpt52_Grc_contract2.yaml --run-name <name> \
      --set llm_config.model_name=elm_qwen_3.5 --set llm_config.openai_api=chat_completions \
      --set llm_config.openai_responses_reasoning_carryover=false \
      --set llm_config.reasoning_effort=<none|high> \
      --set llm_config.base_url=http://127.0.0.1:8012/v1/chat/completions \
      --set execution.max_concurrency=12 --execute

The server is `Qwen/Qwen3.5-397B-A17B-FP8` on 8 GPUs on `first`, with MTP
(`../local-vllm-2026-10-02/serve.sbatch`). The preflight seals 1,605 prompt hashes, the contract-v2
count, with 15 of 15 reviewed workspaces prebuilt. `run_plan.json` names `elm_qwen_3.5`, not the
endpoint; the `local397` in each run name is what says where it ran.

Runs, in order:
1. `iter_local397_contract2_dev_rep1..3`: reasoning off, the iteration-tier setting.
2. `iter_local397_contract2_high_dev_rep1`: reasoning `high`. This runs only if the off cells read
   "at the floor" below. Every gpt cell ran at high effort and Opus at xhigh, so reasoning is the
   first untried design to try before a negative is concluded.

Judged with `configs/pr_review_v5_medium_heldout_judge.yaml` (judge v9, `gpt_5_mini`, about
$0.1-0.2 a run): the dev held-out 12, 23 obligations, 12 reachable. Scored with
`cli report score`, and across reps with `cli report conditions`.

## The scale (all contract v2, dev held-out 12, judge v9)

| reviewer | harness | obligations | findings (held-out) |
|---|---|---|---|
| Opus 5.5 (swap) | probe harness | 10 | 99 |
| Opus 5 | project harness (Claude Code) | 8 | 73 |
| Opus 5.5 | project harness | 7, 7 (union 8, stable 6) | 77 |
| Opus 4.8 | project harness | 3 | 29 |
| gpt-5.5 | `ape_agent` | 3 | 30 |
| gpt_5.2 | `ape_agent` | 2 | 34 |

## Reading rule (stated before any run)

On the mean of three reps. The judge's noise at 23 obligations is about one to two.
- **Above the floor: ≥ 5 of 23** (0.217). That is two above the 2-3 band of gpt_5.2, gpt-5.5 and
  Opus 4.8 under this prompt. This is necessary for driving iteration, not sufficient: designs can
  register here, but whether they register the way they do on Opus needs a design pair run on both.
  No such pair exists on disk. The only replicated Opus design gap, probe against project harness,
  is Claude-only.
- **At the floor: ≤ 3 of 23.** Early testing only. Every design the record tried at this level
  moved nothing, so a design change cannot be read here. This is concluded only after the
  reasoning-`high` rep is also ≤ 3.
- **4: undecided.** Run the reasoning-`high` rep, and two more reps of whichever setting is higher,
  before reading.

Read beside the score, from `../contract-2026-10-01/breadth.py` (the local runs added to its
table): findings and findings per PR; change targets with a finding (of 432); obligations hit per
finding (every reviewer so far sits at 0.06-0.12, and recall follows volume); notes bullets; turns,
processed tokens, capped sessions, and wall clock per rep.

**Caveat carried into any reading.** The dev PRs were created 2025-12-18..31, and Qwen3.5 was
released in February 2026, so they may be inside its training window, as they are for the Claude
and gpt reviewers above. A level that passes is checked on the post-cutoff set before anything is
built on it.
