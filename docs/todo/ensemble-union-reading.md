# The ensemble's union, read for free from the passes already on disk

**Status** — open, 2026-10-02; spawned as its own session (`ensemble-union`, off `hygiene-layer`).
The free reading of Layer 2 in `docs/plans/2026-10-01-beyond-the-solo-baseline.md` §4, before any
K-pass run is paid for. The user's direction (2026-10-02): do this reading in its own session.
**Cost** — one judge call on the merged set, about $0.80 on `gpt_5_mini` (roughly 110 anchored
pairs, 3 samples each), capped at $2; no generation spend.

**Motivating example.** Four Opus 5.x passes on the dev set exist under the project harness, each
judged on the held-out 12 (23 obligations, judge v9):

| pass | run | obligations hit | control-PR findings (33304, 33315) |
|---|---|---|---|
| H-claude rep 1 | `probe_dev_opus55_contract2_claude_sub_rep1` | 7 | 1, 1 |
| H-claude rep 2 | `probe_dev_opus55_contract2_claude_sub_rep2` | 7 | 1, 1 |
| Opus 5 | `probe_dev_opus5_contract2_claude_sub_rep1` | 8 | 4, 4 |
| hygiene rep 1 | `probe_dev_opus55_contract2_hygiene_claude_sub_rep1` | 9 | 1, 1 |

Their per-obligation union is **11 of 23** (`results/pr_review_v5/probes/claude-models-2026-10-01/consistency.py`,
the spine), against 7-9 for any one of them; two reps of one configuration share 65% of their
change targets and ask different things at them. What no run has measured is the price: the
union's control emission (the passes' control findings add up to 7 and 7 before any
de-duplication) and whether the number of passes that agree on a finding separates the hits
(`docs/todo/selection-signal.md`'s cross-rep agreement, whose close condition is the same table
on a run set not used to find it; these four runs postdate that analysis). The literature's
case: union over decorrelated passes gains where voting loses (SWR-Bench, +43.7% F1 from
aggregation; Wisdom and Delusion of LLM Ensembles, arXiv 2510.21513: diversity beats consensus,
which is a "popularity trap"), as the plan's §3 records. `probe_dev_claude_swap_S1` (10 of 23,
the probe harness, same model) is an optional fifth pass for a sensitivity reading, not the
main one, since its harness differs.

**What to build.** `cli report union --runs <a,b,c,...> --as <derived run name>`, in
`src/mathlib_review/review/cli.py` beside the other `report` subcommands, which:
- concatenates the runs' `findings.jsonl` (the `review` channel, every admission);
- collapses only identical asks: the grouping key `merge_findings` uses
  (`src/mathlib_review/review/merge.py`: pr, change ids, concern family, canonical action), and
  **never its suppression step**, which demotes alternatives at one anchor and is selection;
- stamps each surviving finding `passes_agreeing: k` and `passes: [run names]` (its `sources`
  carry the originals), so agreement is a label and nothing else;
- writes `results/pr_review_v5/runs/<derived>/findings.jsonl` with whatever minimal manifest and
  `stages.jsonl` row the judge's `StageInput` accepts for a derived run (a run with no manifest is
  unchecked rather than refused), plus `union_report.json`: findings per run, union size, per-PR
  counts, control-PR counts, and the k distribution.
Then the one paid call, `cli judge --config configs/pr_review_v5_medium_heldout_judge.yaml --of
<derived> --execute`, and the reading in `results/pr_review_v5/probes/ensemble-union-2026-10-02/README.md`.

**Reading rule, stated before the run** (plan §5, Layer 2, adapted to a union of existing passes):
- the union of the four is **a lever** if its judged issue recall is at least 10 of 23 **and** its
  control emission is at most 2.0 findings per control PR;
- if control emission exceeds 2.0, report the K=2 and K=3 subsets (H-claude reps 1+2; those plus
  hygiene rep 1) and read the rule on them, flagged as chosen after the fact;
- the agreement label is reported as hit rate by k (1, 2, 3, 4 passes) and within-PR AUC, as the
  selection-signal todo asks, with no cut proposed (the ruling of 2026-09-22);
- the judge's per-finding verdicts on the union may differ from the four audits (self-agreement
  about 90%), so the union's judged count can land below the spine's 11; report both numbers
  and which obligations moved.

**Start here.**
- read: `docs/plans/2026-10-01-beyond-the-solo-baseline.md` §4 (Layer 2) and §5;
  `results/pr_review_v5/probes/claude-models-2026-10-01/consistency.py` (the spine, and the runs
  and audits by name); `src/mathlib_review/review/merge.py` (`finding_key`, `merge_findings`:
  the grouping is reusable, the suppression is not); `src/mathlib_review/review/cli.py` (the
  `report` subcommands; `judge --of`); `docs/todo/selection-signal.md`.
- run, spending nothing: `ape/bin/python results/pr_review_v5/probes/claude-models-2026-10-01/consistency.py`;
  the judge preflight, `ape/bin/python -m src.mathlib_review.review.cli judge --config
  configs/pr_review_v5_medium_heldout_judge.yaml --of <derived>` without `--execute`. In a worktree,
  `export PYTHONPATH=$PWD/src`; the judge needs `OPENAI_API_KEY` from `~/.config/secrets/env.zsh`
  sourced in the same command.
- bounded by: `docs/dead-ends.md` "Publication as selection" and `.claude/rules/mathlib-review.md`
  "Any proposal about which of the system's findings reach a maintainer is SELECTION": the union
  is generation, the agreement count is a label, and this reading proposes no threshold, ranking
  or gate.

**Evidence** — the four runs and their audits under `results/pr_review_v5/runs/` and
`results/pr_review_v5/audits/` (`probe-dev-opus55-contract2-claude-sub-rep{1,2}`,
`probe-dev-opus5-contract2-claude-sub-rep1`, `probe-dev-opus55-contract2-hygiene-claude-sub-rep1`);
the spine in `consistency.py`; `docs/research/code-review-systems-survey-2026-09.md` §1 (the
agreement signal measured on the lead reps).

**Risk** — a union's control emission adds up, and PR 33149 (AI-generated, 18-19 findings a
pass) dominates the counts; read per PR. The judge pairs at the anchor only, so a finding whose
anchor differs between passes is two findings to it. And this is dev, inside the Opus models'
training window: the union's recall confirms only on validation small12 and post-cutoff, through
the blind matchers (plan §5), which this reading does not do.
