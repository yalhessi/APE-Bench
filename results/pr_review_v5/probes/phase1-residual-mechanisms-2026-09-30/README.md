# Phase 1: the residual asks, labelled by mechanism (pre-registered 2026-09-30, before any reader runs)

Phase 1 of `docs/plans/2026-09-30-post-carryover-replan.md`. A labelling study, about $10 of model
spend for the ask-why replays; the readers are Claude subagents.

## Population

From Phase 0's six matchings (`../phase0-carried-baseline-2026-09-30/phase1_population.json`), an
ask counted as reached by a reviewer only when both matchers said so:

| set | asks | nobody reaches | only Claude reaches |
|---|---|---|---|
| post-cutoff | 16 | 7 | 1 |
| validation | 30 | 12 | 9 |
| dev | 47 | 18 | 20 |
| **total** | 93 | **37** | **30** |

Pairs to label: for a nobody ask, each of X1, X2 (Claude) and Grc1 (gpt_5.2, reasoning carried);
for a Claude-only ask, Grc1. **141 pairs**: post 22, validation 45, dev 74 (halved by PR into two
folders). Two independent readers per folder, eight reader sessions.

## What the readers see

Per PR: the asks with the maintainer's text, the family and its definition from the validation
codebook, and who reached it; `pr.md` and `diff.patch`; each Claude session's `findings.json`,
`notes.md` (its object-by-object account) and `calls.jsonl`; the gpt session's rendered transcript
(every call and a truncated result, then the submission) and, when present, its own after-the-fact
account (`ask_why.py`: the session replayed with its carried reasoning, tools off, asked per ask
whether it noticed, what it concluded, what was missing). The rubric marks the account as a
self-report to be weighed against the transcript. Readers see no matcher notes.

## Labels (`reader_rubric.md`)

Non-exclusive, per pair: `never_attempted`, `attempted_concluded_fine`, `attempted_opposite`,
`verified_withheld`, `filed_elsewhere`, `try_it_not_tried`, `knowledge_convention`,
`analogue_not_compared`, `pr_level_or_history`, `not_reachable_from_code`, `ask_unclear`; plus
`reachable` (yes / no / unclear) and an evidence citation of at most 40 words. The vocabulary is
non-exclusive on purpose: a forced choice hid the mechanism it was built to count once already
(`.claude/rules/mathlib-review.md`).

## The arms' remit pre-check (done before the readers, no spend)

Joining the validation audit's arm-owner labels (two readers, 144 comments) with its family codes,
and applying each family's "no arm owns it" share to the 67 residual asks:

| family | residual asks | share no arm owns (validation) | expected unowned |
|---|---|---|---|
| F1 proof | 15 | 0% | 0 |
| F8 naming | 14 | 50% (of 6) | 7 |
| F2 interface | 6 | 0% | 0 |
| F6 statement and API design | 6 | 50% | 3 |
| F4 derive, don't restate | 5 | 20% | 1 |
| F9 formatting | 5 | 6% | 0.3 |
| F10 documentation | 5 | 12% | 0.6 |
| F12 PR level | 4 | 97% | 3.9 |
| F3 registration | 2 | 100% | 2 |
| F5, F7, CORR | 5 | 0-40% | 0.8 |
| **total** | 67 | | **about 19 (28%)** |

So about 72% of the residual asks are in some arm's remit by family. The arms are not ruled out by
construction, and Phase 2 stays live pending the mechanism table. The F8 estimate rests on six
validation asks and is the weakest row.

## What closes Phase 1

A mechanism table: counts per label, per set and per reviewer family, with both readers' labels
side by side and disagreement reported rather than averaged. **An intervention in Phase 3 is funded
only for a mechanism with at least 5 asks across the three sets.** Two readings that matter for the
plan's open questions:
- **`never_attempted` against `attempted_*`** decides whether coverage forcing (arms, an object
  ledger) is a live lever, which is Phase 2's premise.
- **`try_it_not_tried`, `knowledge_convention`, `analogue_not_compared`** are the input-side
  mechanisms; their counts order Phase 3's items 2-4.

Also reported: `reachable` per ask, so reach can be restated on reachable asks; and, for the
Claude-only asks, whether gpt_5.2's mechanism is attempt (consistent with Phase 0's "files what it
verifies") or something else.

## Files

- `ask_why.py`, `ask_answers.json`: the gpt sessions' own accounts.
- `build_packets.py`: the reader folders (`OUT/<split>/m{1,2}/`), from the population file, the
  probe packets and the runs.
- `labels/<split>.<reader>.jsonl`: the readers' outputs, copied in after their transcripts are
  audited.
- `mechanisms.md`: the table, written after both readers finish.
