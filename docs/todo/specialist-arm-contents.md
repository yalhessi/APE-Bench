# Specialist arm contents — seven of ten match nothing, for three different reasons

**Status** — open; the audit below is done, the fixes are not
**Cost** — most checks are re-scoring on committed artifacts; one 12-PR rep to confirm

## Motivating example

Across 38 joinable v5 audits the ten specialists produced **434 findings and 25 gold issue-matches**
against the generalist's **1,168 / 168**. The recorded headline — "six specialist types matched
nothing across three reps" (`3a3bf72`) — is **seven**, and collapsing them into one number invites
one fix when there are three distinct causes:

| Cause | Arms | Evidence |
|---|---|---|
| ran and asked the wrong thing | `docs`, `style`, `generality`, `proof_idiom`, `correctness` | findings filed, 0 matches |
| ran and had nothing | `family_design` | 26 lead invocations, 0 candidates |
| never ran | `api_reuse` | 107 proposals/rep, 107 pruned/rep, 0 invocations |

## The specific defects, each measured

**`style` is the second-most-expensive specialist and has never matched or published anything.**
126 findings corpus-wide, 0 published, 0 `issue_match` across all 50 audits. Admission reasons: 107
"no collector can support this claim's concern family", 18 "in an unresolved conflict at this
anchor", 1 dropped by the lead. $2.32 billed across three held-out reps. Its zero cannot be read as
"formatting does not matter": the evaluator's own `style` label is a different vocabulary from the
arm's brief — `arm.py:161-162` already records that 11 of the 19 gold obligations labelled `style`
are not what STYLE_SYSTEM asks about.

**The submission contract silently overrides the registry's `expected_concerns`.** `family_design`'s
prompt has a section headed "## Which concern to declare" saying it may declare either of two
concerns. The contract rendered **2,413 characters below it** opens "This supersedes any field list
above" and says every candidate must set one concern. Result corpus-wide: `family_design` 4/4
`generalization`, `style` 126/126 `style`, `correctness` 13/13 `correctness`. **Zero off-concern
tags have ever been emitted**, so the `OFF_CONCERN_TAG` diagnostic built to measure drift measures
nothing, and the registry's long justification for the widened sets is inert.

**`naming` is the most precise specialist and is throttled by an unreachable bar.** 10 issue-matches
from 29 findings (34%) — four times the generalist's per-finding rate — but it submits on 4 of 75
lead invocations (5%). `naming_norm` requires `support >= 20` **and** `support/members >= 0.80`
(`naming_norm.py:55-57`). Over 834 recorded calls: 596 (71.5%) return the empty branch, 238 carry a
counted population, and only 95 (11.4%) could ever clear `established`. PR 33337's gold prefix is
`toLinearMap` at **21 of 121 — a 17% modal share**; clearing 0.80 would need 97 of 121. The
maintainer made the ask anyway.

**`docs` is told a linter settles the check it cannot run.** DOCS_SYSTEM says over-long lines and
malformed markup are settled by "the repository's own linter". The run's toolset is `file_read,
content_search, lean_verify, get_lean_goal, code_hover, code_goto` plus five context tools — no
linter. PR 33305's single obligation is BLOCKING and is exactly that ("wrap/split the overly long
doc comment line"); it has **0 pairs and 0 hits in every v5 audit ever run**. `docs` made 0 context
calls in 39 held-out lead invocations despite holding `precedent_search` and `zulip_search`.

**`api_reuse` is the only arm of eleven with zero mandatory rows.** 107 proposals, 107 eligible, 0
mandatory, identically in all three held-out reps; 321 pruned across three reps, 0 invocations. Its
one delegation ever — in the earlier `pr5_A_lead_heldout12_rep1` — produced the only `api_reuse`
gold match in the corpus, on 33117's `@[to_fun]` obligation. Note the cause is *not* simply absence
from `_GRAIN_REQUIREMENTS`: `generality`, `proof_golf` and `proof_idiom` are also absent and still
get mandatory rows through the `pr_intent` branch (`routing.py:174-183`). `api_reuse` reaches
neither path.

**`proof_golf` and `proof_idiom` share all seven routing fields and their `tools_sha256`.** They
differ only on `spec_id`, `prompt_sha256` and `rationale`. GOLF_SYSTEM's first sentence claims
idiom's remit verbatim ("shorter **or more idiomatically** … `simp`/`grind`/`omega`/`gcongr`"),
contradicting the registry's statement that idiom is "explicitly not about length". Across three
held-out reps idiom cost $1.95 for 45 invocations and 2 matches; golf $0.96 for 26 and 7.

**`family_design` is dead weight by content, and this is already half-recorded.** 26 lead
invocations → 0 candidates; 11 fanout → 0. PR 33117's gold obligation is literally its third prompt
bullet ("a generated form written by hand — search for the attribute before assuming there is
none"); it enumerated the family by name in all three reps and abstained `already_correct`. That
obligation was hit 10 times in the corpus, by `api_reuse`, `duplication`, generalist and solo —
never by `family_design`. `routing.py:78-80` already demoted it to `_ONCE_PER_PR` for a measured
reason, so this is an amendment to an existing decision, not a new finding. (Correction: it was not
"the only arm that kept refusing" under `forbid_abstention` — `generality` refused 6 of 11.)

## What would close it — cheapest first

1. **Split `naming_norm`'s zero branch.** 596 of 834 calls return "the corpus has no counted opinion
   … Submit nothing on naming", but that branch fires when
   `subject.token is None or subject.confidence != "high" or population is None` — a subject-resolution
   failure inside the tool, not a corpus fact. Separate "subject not resolved" (a tool limitation,
   reportable with the weakness stated) from "resolved, corpus has no opinion". Pure re-parse over
   snapshots on disk, no spend.
2. **Recompute the three naming verdicts** on the 238 recorded counted populations under a lower
   `MIN_SUPPORT_RATIO` with a conflict-ratio guard, and check against the naming golds before paying
   for any rerun. Half of this is free.
3. **Make the verification sentence conditional on the registry's `checkable` flag** and report
   per-arm publication split by checkable/non-checkable, so the admission gate's effect is never
   read as arm quality. Note the causal direction: the verify instruction is what *opens* publication
   (every published finding from a compile-warrantable arm carries "the proposed edit recompiled the
   reviewed file"); what *closes* it for `style`/`naming`/`docs` is their absence from
   `CHECKABLE_CONCERN_FAMILIES`.
4. **Give `api_reuse` a floor** (add it to the `introduction` grain beside `duplication`) or state in
   the registry that it is fanout-only. Either way the `lead` condition is currently not a test of it.
5. **Make SUBMISSION_CONTRACT emit the arm's full `expected_concerns`**, rerun one rep, and see
   whether any off-concern tag ever appears. This moves every specialist `prompt_sha256`.
6. **Merge golf and idiom, or make their prompts disjoint.** Measure whether the merged arm's
   matches are ≥ 7.
7. **Grant `family_design` a tool that can answer a group question** (it has no `declaration_search`;
   33% of its 246 context calls are rename-shaped queries it cannot run), rerun once, and if it still
   produces nothing, write the dead-ends entry and fold the `patch_set` grant into `duplication`.

## Risk

Items 3, 5 and 6 move prompt hashes. The `style` retirement decision should wait for the re-labelling
in item (1) of [judge-and-measurement.md](judge-and-measurement.md) — its zero may partly be a
vocabulary mismatch with the gold labels rather than an arm failure.

## Record correction this forces

The `dead-ends.md` 33337 clause says `naming_norm` returned `insufficient_evidence` and that the
obligation "was never hit by any condition". Both are false, and the true version is a *stronger*
case for the same conclusion. See [record-corrections.md](record-corrections.md).
