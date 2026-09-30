# Phase 0: the carried-reasoning baseline on three sets (pre-registered 2026-09-30, before its runs)

Phase 0 of `docs/plans/2026-09-30-post-carryover-replan.md`. Every later reading in that plan is
against these runs, not against any run made before carry-over.

## What changed at this run boundary

- **`declaration_search` is fixed** (eec8d3a, cherry-picked onto this branch). Before, it reported a
  leaf-only match as the queried name, so reviewers were told declarations existed that did not.
  Every reviewer in every earlier seal, Claude included, used the defective tool. Tool text changed
  too, so sessions before and after read different output.
- **Carry-over is the condition.** `gpt_5.2`, `reasoning_effort: high`, `openai_api: responses`,
  `openai_responses_reasoning_carryover: true`, brief G, 80 turns, caps $13.40 and 16.08M tokens a
  session (the post-cutoff Grc config's).

## Runs

| run | set | PRs | config |
|---|---|---|---|
| `probe_postcutoff_gpt52_Grc_rep2` | post-cutoff | 6 | `configs/pr_review_v5_probe_2026_07_08_v1_gpt52_Grc.yaml` |
| `probe_postcutoff_gpt52_Grc_rep3` | post-cutoff | 6 | same |
| `probe_val_small12_gpt52_Grc_rep1` | validation small12 | 11 | `configs/pr_review_v5_val_small12_gpt52_Grc.yaml` |
| `probe_dev_gpt52_Grc_rep1` | dev medium 0.3.0 | 15 | `configs/pr_review_v5_dev_medium_gpt52_Grc.yaml` |

Ceilings $80.50 / $80.50 / $147.90 / $201.50; the expected total is about $30 (Grc rep1 billed
$2.70 on post-cutoff; Gr1 billed $14.85 / $26.4 / $36 on the three sets with capped sessions, and
carried sessions ran at about a fifth of Chat's cost).

## Seals, one per set, committed before any matcher runs

| set | reviewers | anchor |
|---|---|---|
| post-cutoff | X1 X2 Gr1 Grc1 Grc2 Grc3 | Gr1 (0.3125 in every earlier matching) |
| validation | X1 X2 Gr1 Grc1 | Gr1 |
| dev | X1 X2 Gr1 Grc1 | Gr1 |

Two blind matchers per seal, transcripts audited, then unblinded. Grc1 on post-cutoff is the run
from 96e9d12, re-matched here so the three reps sit in one seal.

## Reading rules

- **q = reach(Grc) / reach(X)** per set on both matchers, as before. On post-cutoff, mean / union /
  stable over the three reps.
- **Carry-over is confirmed as the standard condition** if q ≥ 0.8 on post-cutoff's three-rep mean
  and on at least one of validation and dev. If q ≤ 0.5 on either of those two, the post-cutoff
  result was set-specific and Phase 3 waits.
- **The tool fix is a confound the design names rather than removes.** Grc1 used the defective tool,
  Grc2 and Grc3 the fixed one, so the replication pair is Grc2 against Grc3, and Grc1 is the
  pre-fix point. If Grc2 and Grc3 agree with each other and both differ from Grc1 by more than they
  differ from each other, the fix is named as the cause. On validation and dev, X and Gr1 used the
  defective tool and Grc the fixed one, so q there carries the fix in Grc's favour; it is read with
  that stated.
- **Also read:** asks reached per finding against X's; turns, calls, capped sessions and cost per
  session; the coherence measures (`../carryover-coherence-2026-09-30/coherence.py`).
- **The residual list.** For each set, the asks reached by no reviewer in the seal, and the asks
  reached by X and not by any Grc. That list is Phase 1's population.

## Not in Phase 0

The carry-over default flip (plan step 2) is deferred: `LLMConfig` refuses carry-over without
`openai_api: responses`, so a bare `True` default would break every non-Responses config, and the
right shape is a tri-state resolved at load. The Grc configs set it explicitly, so no run here
depends on the default.
