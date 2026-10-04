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

## Result (2026-09-30): carry-over is the standard condition on process grounds; the claim that it closes the model gap is withdrawn

Six matchings (two blind matchers per set, all six transcripts audited clean), 93 asks over 26 PRs,
$20.02 billed for the four runs. Matcher agreement 94/96, 116/120 and 181/188 cells.

### Reach

| set | asks | X (Claude, mean of two) | Gr1, Chat | Grc, carried | q(Grc) | q(Gr1) |
|---|---|---|---|---|---|---|
| post-cutoff | 16 | 0.469 | 0.3125 | 0.4375 / 0.375 / 0.1875; **mean 0.333**, union 0.4375, stable 0.1875 | **0.71** mean, 0.93 union, 0.40 stable | 0.67 |
| validation | 30 | 0.467 | 0.267 / 0.300 | 0.267 | **0.57** | 0.57 / 0.64 |
| dev | 47 | 0.564 / 0.585 | 0.170 | 0.213 / 0.191 | **0.38 / 0.33** | 0.30 / 0.29 |

**By the pre-registered rule, carry-over is not confirmed as closing the gap.** The post-cutoff
three-rep mean is 0.71, not ≥ 0.8, and dev is ≤ 0.5. The single run read as 0.93 in 96e9d12 was the
top of a 0.19-0.44 spread. Over three sets, carried reasoning against Chat is +0.02 on the
post-cutoff mean, 0.00 on validation (two asks gained, two lost) and +0.02 to +0.04 on dev (two
gained, one lost). The gpt_5.2 model gap stands at q 0.33-0.71 across sets, Chat or carried.

**Anchor.** Gr1 reproduces exactly on post-cutoff (0.3125) and within one ask on validation. On dev
this matcher pair is stricter than the earlier one (X 0.55-0.60 against 0.68-0.70, Gr1 0.170 against
0.19-0.21), mostly through "a different name with no stated reason is partial", so dev's q is read
within this matching only.

**The tool fix is not the cause of the post-cutoff spread.** rep1 (old `declaration_search`) and
rep2 (fixed) differ on one ask; rep2 and rep3, both fixed, differ on three.

**Dev's "cap losses" were not the cap or the tool.** d23fbde read 19 of dev's 24 gap asks, on PRs
where Gr1 was capped, as mostly a `declaration_search` defect. With the fix and every session
concluding, Grc1 gained two asks, one on a capped PR. The reviewer does not reach those asks when
it concludes either.

### Process

| run | sessions submitted | turns | far repeats /100 calls | edits verified | verified, not filed | findings | reasoning tokens | billed |
|---|---|---|---|---|---|---|---|---|
| post Gr1 (Chat) | 5 / 6 | 284 | 5.5 | 7 | 2* | 11 | 817K | $14.84 |
| post Grc1 / 2 / 3 | 18 / 18 | 83 / 116 / 109 | 0.5 / 0.6 / 1.1 | 7 / 5 / 3 | 0 / 0 / 0 | 9 / 6 / 4 | 117K / 123K / 102K | $2.70 / $3.05 / $2.47 |
| val Gr1 (Chat) | 8 / 11 | 493 | 5.1 | 22 | 1* | 25 | 1,558K | $26.56 |
| val Grc1 | 11 / 11 | 165 | 0.6 | 14 | 0 | 26 | 247K | $5.60 |
| dev Gr1 (Chat) | 9 / 15 | 709 | 6.3 | 29 | 14* | 43 | 1,870K | $35.65 |
| dev Grc1 | 15 / 15 | 282 | 3.4 | 27 | 1 | 48 | 340K | $8.90 |

\* mostly capped sessions that never reached submission, not a filing choice.

On every set, carried sessions all conclude, repeat about a tenth as often, use a sixth of the
reasoning tokens and bill a fifth, with no loss of reach. **So carry-over is adopted as the standard
condition for OpenAI reasoning models** — for what it does to the process, not for reach. The
Chat-plus-reasoning condition is not run again.

**gpt_5.2 files what it verifies**: 1 of 56 verified edits across the five carried runs went
unfiled. Its variance across reps, and its misses against Claude, are in what a session chooses to
attempt (rep3 never compiled a rename on 43024 and built less on 43192), not in a filing bar. That
is a different mechanism from gpt-5.4's and gpt-5.5's (`../model-inspection-2026-09-30/`).

### The residual population (`phase1_population.json`)

An ask is "reached" by a reviewer only when both matchers say so.

| set | asks | nobody | Claude only | both | gpt only | disputed |
|---|---|---|---|---|---|---|
| post-cutoff | 16 | 7 | 1 | 7 | 0 | 1 |
| validation | 30 | 12 | 9 | 6 | 2 | 1 |
| dev | 47 | 18 | 20 | 8 | 1 | 0 |
| **total** | **93** | **37 (40%)** | **30 (32%)** | 21 | 3 | 2 |

Two populations of about equal size: the ceiling (37 asks no reviewer reaches) and the remaining
model gap (30 asks only Claude reaches). Together they are 72% of the asks. Phase 1 labels both by
mechanism; the file holds each ask's text, family code, class and which reviewers reached it.

**Altitude.** One carried run on validation and dev, three on post-cutoff; dev's matching is not
comparable to the earlier one. The process result is the same on every set and every rep and is
not provisional. The reach result is: the direction (no gain) is consistent across sets, the size is
inside one-rep noise on each.

## Verification (2026-09-30): the carried runs did reason at high effort, and did carry it

Asked because the carried reach resembles the Chat runs'. Checked from the artifacts, not the
configs:

- **Requests.** `data/llm_logs/2026-09-30/09/` holds 672 Responses requests in the Phase 0 window,
  exactly the four runs' 116 + 109 + 165 + 282 turns, all to `gpt-5.2-2025-12-11` with
  `reasoning.effort: high`, `include: [reasoning.encrypted_content]`, `store: false`. 634 carry at
  least one encrypted reasoning item (median 9, max 44); the 38 that carry none are the 38 sessions'
  first turns.
- **Responses.** Every raw turn has a `resp_` id; 98-99% of turns spent reasoning tokens (the
  reasoning-off runs: 0 on every turn); every reasoning turn's assistant message holds encrypted
  items; and the next turn's input grows by the previous turn's reasoning at 0.99-1.05, against
  0.00 on every Chat run.
- **Plans.** Each sealed plan's `scaffold_config_sha256` equals the digest recomputed from its
  config today; with carry-over off or effort unset the digest differs.

**Against reasoning off**, where the comparison exists: validation 0.10 / 0.17 off, 0.267 carried,
0.267 / 0.300 Chat-high; post-cutoff 0.12 off, 0.33 carried mean, 0.31 Chat-high. Carried equals
Chat-high and is about twice off. The resemblance is to Chat-high, which on validation and dev is
itself low. Carried sessions spend fewer reasoning tokens a turn (median 470-1,010 against
Chat-high's 1,280-1,790), as the coherence test found at matched effort: the model does not
re-derive its state each turn.
