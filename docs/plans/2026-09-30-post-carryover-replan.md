# After carry-over: what to re-measure, what to keep, and what the residual wall is made of (plan, 2026-09-30)

**Status** — plan, written on `pipeline-overfit-review` at bc65c1d. **Phase 0 ran 2026-09-30** on
`post-carryover-replan` (`results/pr_review_v5/probes/phase0-carried-baseline-2026-09-30/`, $20):
carry-over does not close the model gap (q 0.71 mean / 0.57 / 0.33-0.38 on the three sets, against
Chat's 0.67 / 0.57-0.64 / 0.29-0.30) and is adopted as the standard condition on process grounds
(every session concludes, a fifth of the cost, no loss of reach). Section 1's "closed on one set"
is superseded by that. The residual population is 93 asks: 37 reached by nobody, 30 only by
Claude — `phase1_population.json`. **Phase 1 is next**, in a fresh session in that worktree; the
carry-over default flip (Phase 0 step 2) is deferred to it, since `LLMConfig` needs a tri-state. The user's framing (2026-09-30): the wall this project has run into
for most of its life is plausibly explained by reasoning being off, and by reasoning not carrying
across turns. Both are now fixed for the OpenAI models. So the diagnoses built on the old runs are
outdated, the built system must be re-evaluated against the new reviewer, and the question is what
to give the models to get past 0.4-0.5 toward 0.7-0.8.

## 1. What the record supports today, and what it does not

Two different gaps have been called "the wall". Carry-over closes one and does not touch the other.

**The model gap** (gpt against Claude, same brief, tools and PRs) is closed on one set, one run:

| gpt_5.2 condition | post-cutoff, q = reach / Claude |
|---|---|
| reasoning off | 0.27 |
| high, Chat Completions (reasoning dropped each turn) | 0.67 |
| high, Responses, reasoning carried | **0.93** ($2.70 for 6 PRs) |

Every diagnosis of the pipeline made on gpt sessions before 2026-09-30 was made on a reviewer that
did not reason, or that lost its reasoning every turn: arm silences, the gate's suppression,
construction breadth, "retrieval is not the gap", the 22% of capped turns chasing a tool defect.
Those numbers describe a reviewer we no longer run. They are not wrong; they are about something
else.

**The ceiling gap** (any reviewer against the maintainers) is untouched, because Claude's reasoning
always persisted and Claude is the ceiling:

| set | asks | Claude, either session | asks nobody reaches |
|---|---|---|---|
| post-cutoff (6 PRs) | 16 | 0.50 | 7 (44%) |
| validation small12 (11 PRs) | 30 | 0.53 | 11 (37%) |
| dev (15 PRs) | 47 | 0.72 | 12 (26%) |

("Nobody" = neither Claude session nor any gpt condition in that set's reasoning seal.) A target of
0.7-0.8 is therefore not a model-choice question. It requires reaching asks that no reviewer, with
persistent reasoning and the full toolset, has reached. Section 4 says what those 30 asks are.

**gpt-5.4 and gpt-5.5** reach less than gpt_5.2 because they verify the maintainers' asks and then
decline to file them ("not something I would expect a maintainer to require"), not because they
investigate less (`results/pr_review_v5/probes/model-inspection-2026-09-30/`). That is a filing bar,
and it is the cheapest lever on the table.

**Untried here:** carry-over on any set but post-cutoff; a second run of anything carried; the lead
path under a reasoning-carried model; Claude on a set it cannot have seen with more than 16 asks.

## 2. Phase 0 — the new baseline replaces the old runs (about $30, matching free)

Nothing later in this plan is read against a pre-carry-over gpt run.

1. **Merge `eec8d3a`** (`declaration_search` false duplicates, on `arm-division`). Every run to date
   used the defective tool; this is the run boundary that was waited for.
2. **Flip the default**: `openai_responses_reasoning_carryover: true` whenever `openai_api: responses`
   and a reasoning effort is set. `cli plan` already refuses Chat Completions with tools and
   reasoning on gpt-5.4/5.5; extend the refusal note to say carry-over is the standard condition.
3. **Runs**, all `gpt_5.2`, high, Responses, carried, brief G:
   - post-cutoff reps 2 and 3 (`probe_postcutoff_gpt52_Grc_rep{2,3}`), about $6;
   - validation small12 rep 1 (`probe_val_small12_gpt52_Grc_rep1`), about $6-8;
   - dev rep 1 (`probe_dev_gpt52_Grc_rep1`), about $8-12 (Gr1 on dev billed $36 with 6 of 12 ask
     PRs capped; carried sessions ran at a fifth of Chat's cost).
   Caps: the `Grc` configs' (80 turns, 16.08M tokens, $13.40 a session).
4. **Seals**: one per set, the existing Claude X1 X2 plus the Gr1 anchor plus the new Grc runs. Two
   blind matchers each, audited, unblinded.
5. **Read**: q per set on both matchers; mean / union / stable over the three post-cutoff reps; the
   per-set "nobody reaches" list recomputed with Grc in the seal.

**Closes Phase 0**: three-set q for the carried reviewer, and the residual list. **Rule**: carry-over
is confirmed as the standard condition if q ≥ 0.8 on post-cutoff's three-rep mean and on at least
one of the other two sets; if it falls to ≤ 0.5 on either, the post-cutoff result was set-specific
and Section 5 waits.

## 3. Phase 1 — label the residual wall on the new baseline (free, plus about $5)

The unit is an ask. The population is every ask on the three sets that (a) no reviewer reaches, or
(b) Claude reaches and carried gpt_5.2 does not. On today's seals that is 30 asks in (a) and a
handful in (b); Phase 0 revises both.

**Labels are mechanisms, non-exclusive** (`.claude/rules/mathlib-review.md`: a forced-choice
vocabulary hid the mechanism it was built to count). Two blind readers, the project's standard,
each labelling from the reviewer transcripts and the ask text. The vocabulary, from reading the 30
today:

| mechanism | what the transcript shows | first guess at count (my reading, not a label) |
|---|---|---|
| **verified, withheld** | the reviewer compiled or confirmed the change and did not file it | gpt-5.4/5.5: 6 edits; gpt_5.2 and Claude: unknown |
| **object never attempted** | no tool call touched the declaration the ask is about | unknown |
| **attempted, concluded otherwise** | looked, and judged fine or judged the opposite (gpt-5.4 on 43192's wrappers) | unknown |
| **try-it ask, not tried** | "can `positivity` do this", "one-liner with `X`", "`simpa using`": decidable by one compile, nobody compiled it | about 7 of 30 (all F1) |
| **convention or mechanism knowledge** | `mk_iff`, `grind` tags, `to_fun`, `_left`/`_right` direction, `HasProd` companion "as is the convention in this file" | about 8 of 30 |
| **design against an analogue** | statement form, companion lemma, alias direction, UFD generality | about 7 of 30 (F6/F7) |
| **PR-level or history** | "explain why in the PR description", relation to #24163 | about 3 of 30 |
| **not reachable from the reviewed code** | needs author intent or discussion the packet does not hold | overlaps the row above |

For the gpt sessions, add the model's own account: replay the session with its carried reasoning
(`model-inspection-2026-09-30/ask_why.py`, about $0.30 a question) and ask why the ask was not
raised. For Claude sessions, `notes.md` already records what was checked object by object. The
reader labels from both.

**Also label reachability**: whether the ask is decidable from the reviewed code plus the library
(the project's `issue_recall_reachable` notion). Report reach on reachable asks beside reach on
all asks; the 0.7-0.8 target should be stated on the former.

**Closes Phase 1**: a mechanism table with counts per set, and per reviewer family. **Rule**: an
intervention in Section 5 is funded only for a mechanism with at least 5 asks across the three sets;
below that, it is a wish.

## 4. Phase 2 — what of the built system to keep (about $30-50)

The criterion for every built part is one question: does it add reach or aim for a
reasoning-carried generalist? The evidence today, and the test where one is needed:

| part | evidence today | verdict | test |
|---|---|---|---|
| **Solo path**: brief G, the context tools, `lean_verify_edit`, reviewed workspaces, Responses carried | reaches 0.93 of Claude on post-cutoff; every model uses the tools heavily (257 `content_search`, 106 `declaration_search`, 75 `lean_verify_edit` in 18 sessions) | **keep; this is the reference** | Phase 0 |
| **Probe harness** (`analysis/probes.py`, `cli probe`), sealed blinding, two matchers, transcript audit | every result in this thread runs through it; matchers agree 128/128 on the last seal | **keep** | none needed; grow the set (Section 6) |
| **Reviewed workspaces** | the compile claims depend on them | **keep** | none |
| **Responses provider + carry-over** | end to end verified (coefficient 0.99-1.01) | **keep; make default** | Phase 0 step 2 |
| **Lead + arms + gate + finalize** (the v5 pipeline) | L − G = 0.00 / +0.13 / +0.08-0.15 on the three sets, all with reasoning **off**; the gate publishes 1-2 of 5-7 hits; the arms were designed to compensate for a reviewer that did not look outward or construct | **undecided; test** | lead mode with `gpt_5.2` high carried on post-cutoff and validation, `probe_{postcutoff,val_small12}_lead_carried_rep1`, against Grc. Rule: L_c − Grc ≤ 0.03 on both → shelve the decomposition and the gate together (dead-ends entry, code kept); ≥ 0.10 on either → keep and re-diagnose the arms under reasoning. Cost about $30-50. |
| **The gate specifically** | suppresses most hits; the precision it is meant to buy is unmeasured | decided with the row above; **no new gate is designed** (selection is refused, `.claude/rules`) | precision stays the open measurement |
| **Construction brief K, facet briefs, object ledger, `notes.md`** | designed for a non-constructing reviewer; K's null was with reasoning off; carried gpt_5.2 built 7 edits on 6 PRs, Claude 4.6-6.6 targets a session | **defer to Phase 1** | funded only if "object never attempted" is a top mechanism |
| **Coordination design** (six consumer perspectives) | demonstration failed on Claude, which already reasons; its reopen condition named the non-constructing gpt, now moot | **parked** | reopen only if sibling-class misses dominate Phase 1 |
| **Ask census / conventions codebook** (`conventions-nature`, 237 principles after 625 asks) | in flight on its own branch; only 8 of 31 variant-design principles are written anywhere | **keep; it is the knowledge source for the convention row of Phase 1** | its own thread; Section 5 names how it is consumed |
| **Design-comparison retrieval** (`review-design-comparison`) | in progress; the F6 class is 95 of 506 validation asks | **keep** | its own thread; Section 5 |
| **Closer battery / fold search** | "reaches the mechanical asks and nothing else" (`remaining-misses-kind.md`) | **keep as an evidence input**, not an arm | Section 5 |

## 5. Phase 3 — interventions, one at a time, each with its rule before its run

Ordered by the strength of today's evidence. Phase 1's counts reorder them. Every one runs on both
reviewer families (gpt_5.2 carried; Claude Opus 5.5 through the probe packets), because a fix that
works for one model is a fix for that model. Every one is judged on post-cutoff **and** validation:
post-cutoff is in-sample for anything designed from the inspection of its six PRs.

The general rule for each: reach up by ≥ 0.10 on both matchers on at least one set and down on
none, with asks reached per finding no lower than Claude's on that set, so that filing more is not
read as aiming better.

1. **The filing bar** (mechanism: verified, withheld). Directly observed on gpt-5.4/5.5. Two edits,
   in generic terms: the brief says maintainers routinely request small polish and every verified
   change the reviewer would suggest is filed, optional ones as `advisory`; and `merge_ready_as_is`
   leaves the solo submission (the severity line's "withhold merge" wording goes with it). Run
   gpt-5.4, gpt-5.5 and gpt_5.2 carried. Expected: gpt-5.5 toward 0.5 on post-cutoff. About $12
   post-cutoff, $25 validation. Separately, brief-only against schema-only tells which of the three
   sources binds; that is a second step, funded only if the first moves.
2. **The try-it class** (about 7 asks today, all proof-golf by a named tactic or lemma). The closer
   battery already reaches mechanical asks; feed its compiled results into the reviewer's packet as
   evidence ("`positivity` closes this goal", "`simpa using h` compiles") rather than running it as
   an arm. Zero extra model cost for the battery; one run per set to read.
3. **Convention and mechanism knowledge** (about 8 asks: `mk_iff`, `grind`, `to_fun`,
   `_left`/`_right`, file conventions). The census codebook is the source. The test is a
   conventions section in the brief drawn from principles labelled on **val1000**, with the
   examples' PRs disjoint from every evaluation set (the PR-level leakage rule). Scope matters: the
   census finds conventions vary by area, so a principle carries its area.
4. **Design against analogues** (about 7 asks). The design-comparison line's shape-match retrieval,
   delivered as packet evidence: "the analogous file states this as ...". Its own thread decides
   when it is ready to test.
5. **Object coverage** (if Phase 1 finds "never attempted" large): the object ledger, now as a
   coverage-forcing device rather than as memory, since carried reasoning is the memory.

Not on the list: more sampling (the union of reps has not moved the nobody-reached set), a new
gate or ranking, and a bigger turn cap.

## 6. The evaluation set

Sixteen asks make 0.10 one and a half asks, and the semantic matchers' self-agreement puts one
ask at ±12pp. The post-cutoff set is also the only set clean for both reviewer families (Claude's
cutoff is June 2026; validation and dev are inside it, and the recall check found Claude's in-window
reach 79-107% of post-cutoff, so they serve for gpt replication, not for a Claude ceiling).

Grow it: PRs created 2026-07..09 with round-1 feedback, through the existing draw frame
(`projections.frame walk`), one PR per author, AI-generated PRs kept and labelled, to about 20
ask-bearing PRs (about 50 asks). Reviewed workspaces prebuild at 2.4-16.6 min each, no model cost.
Feedback is extracted only after every reviewer has run, as before. The current six ask PRs stay as
they are; the new PRs are the held-out half for anything Section 5 designs.

## 7. Cost and order

| phase | spend | wall time |
|---|---|---|
| 0: baseline on three sets, three reps on post-cutoff | about $30 | half a day, including matching |
| 1: labelling + ask-why replays | about $5 | a day of reader subagents |
| 2: lead under carried reasoning, two sets | about $30-50 | half a day |
| 6: grow the post-cutoff set | $0 | prebuild hours; Claude sessions are subagents |
| 3.1: filing bar, three models, two sets | about $40 | half a day |
| 3.2-3.5 | about $15-30 each | after Phase 1 |

Phases 0, 6 and the free half of 1 can start together. Phase 2 and 3.1 start after Phase 0's
post-cutoff reps are matched. Everything else waits for Phase 1's table.

## 7b. Order decided after Phase 0 (2026-09-30)

Phase 0 verified that the carried runs reasoned at high effort and carried it (3a3138f2), and that
carry-over changes process, not reach. So:
1. **Phase 1 now, free**: label the 67 residual asks (37 nobody, 30 Claude-only) by non-exclusive
   mechanism, two blind readers, with the carried gpt sessions replayed and asked why, Claude's
   `notes.md` read for what it checked and dismissed, and **the arms' remit test over the same asks**
   (the validation audit put 21% of asks outside every arm's remit; if most residual asks are, the
   arms cannot help by construction and Phase 2 is a formality).
2. **Phase 3.1 in parallel, about $45**: the filing bar on gpt-5.4 and gpt-5.5 with reasoning
   carried, since its mechanism is already observed. Fixed on post-cutoff (in-sample; the unfixed
   runs exist) and validation, with unfixed validation controls. Rule before the run.
3. **Phase 2 after Phase 1's table**, with two lead reps on validation, only if coverage is a top
   mechanism or the remit pre-check leaves the arms in play. Within-condition variance on
   post-cutoff (0.19-0.44) makes a one-rep lead result unreadable against ≤ 0.03 / ≥ 0.10.
Replicating gpt-5.4 and 5.5 unchanged is not run: it would re-measure a known defect.

## 8. Execution

- A fresh session in a new worktree. `pipeline-overfit-review` (167 commits past `develop`, suite
  green at 2467) holds the harness, the configs and the results this plan reads; merging it into
  `develop` first, then branching, is the clean start. That merge is the user's call.
- Every run name carries the condition (`Grc`, `lead_carried`, `Grc_bar` ...); every seal is committed
  before its matchers run; every rule is written in the probe README before the run.
- Record each phase's result in `docs/todo/reviewer-model-gap.md` (the thread's ledger) and a new
  `docs/todo/residual-wall.md` for Phases 1 and 3, with the mechanism table as its motivating
  measurement.
