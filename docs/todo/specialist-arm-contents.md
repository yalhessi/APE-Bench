# Specialist arm contents — seven of ten match nothing, for three different reasons

**Superseded as the route forward (2026-09-23)** — [`docs/plans/2026-09-23-work-enumeration.md`](../plans/2026-09-23-work-enumeration.md) replaces arm-by-arm repair with questions enumerated from maintainer comments, one verdict per target, and no generalist or lead; the defects below are what that design does not inherit (one grant for every question, no prefix-only naming oracle as the bar, no golf/idiom overlap). The free items here stay open and are not prerequisites.
**Status** — open; the audit below is done, the fixes are not. *2026-09-23:* item 1's prompt half (the naming prompt no longer says "Submit nothing on naming" when the tool could not resolve the subject) is addressed in `b7d67cf` (spec identity naming ee245f077b7e -> 1f4b176a45a4); the census-driven rewrite of the three convention arms is deferred there until one run shows the contract moves recall
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

**`naming_norm` counts prefixes, and at least one gold ask is a suffix change** (added
2026-09-21). `leaf_prefix` (`naming_norm.py:122-125`) is `leaf.split("_", 1)[0]`, so the counted
population is over first tokens only. PR 33421's obligation is "rename `round_eq'` to
`round_eq_div`" — both names have the prefix `round`, so the tool cannot distinguish them at any
threshold, and the arm duly reported `insufficient_evidence`. This is structural and separate from
the bar below: lowering `MIN_SUPPORT_RATIO` does not make a prefix oracle see a suffix convention.
Both `evidence_gap` labels in the 2026-09-21 silence read name this tool
(`docs/research/specialist-silences-2026-09.md`).

**Counted 2026-09-22, and it is worse than a threshold problem.** Of the release's four
naming-labelled gold obligations, **two are not prefix questions at all**: 33421 is a suffix change
(`round_eq'` -> `round_eq_div`, both prefix `round`) and 33294 is a dot-notation/namespace move
(`isFundamentalSequence_of_isNormal` -> `IsFundamentalSequence.of_isNormal`). The other two --
33337's `coe_` -> `toLinearMap_` pair -- the tool *did* express, correctly, as `emerging` (21 vs 7),
and the arm read `emerging` as grounds for silence. So on this set the tool is the wrong shape for
half the asks and correct-but-ignored on the rest, and forcing the same arm produced the gold rename
for both 33337 and 33145 (`docs/research/what-forcing-unlocks-2026-09.md`). Four obligations, one
release: a description, not a rate.

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
*2026-09-23:* the linter exists and v5 cannot reach it. `evidence/operators/lint_policy.find_long_lines`
is reachable only through `execution_release`, which is None in every held-out run; the reviewed
`Inverses.lean` has exactly one line over 100 characters (line 23, 101 chars), the gold site. A lint
pass over changed spans would add this obligation deterministically, +1 of 23 in every rep -- and it
is a V1 lexical hit, so it must be reported as that and never as a better reviewer.

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
2. ~~**Recompute the three naming verdicts** on the 238 recorded counted populations under a lower
   `MIN_SUPPORT_RATIO` with a conflict-ratio guard, and check against the naming golds before paying
   for any rerun. Half of this is free.~~ **Refuted 2026-09-15 on `arm-naming-bar`, do not redo**
   (`docs/dead-ends.md`, "Lowering `naming_norm`'s `MIN_SUPPORT_RATIO`"): no verdict moves from 0.80
   down to 0.20, and the bar is what suppresses bound-variable subjects.
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

## 2026-09-23: four specialist levers measured after the unified contract, and what each can reach

A read-only survey (four assessors, two adversarial verifiers) over every judged v5 run on disk, after
`pr5_V3_contract_fanout4_rep1` (3 / 10). **At every one of V3's seven misses an on-concern arm ran and
answered with a considered verdict; no lever below reaches more than one or two obligations on the sets we
can measure, all in-sample, below the judge's ±12 pp at n = 10.**

- **Design-move questions** (introduce a lemma for a repeated argument; generalize a constant). Reach: two
  obligations, both on 33421 (38e72250, 55f65304). Both questions are *already* in `family_design`'s brief as
  sent (11 / 11 jobs in V3), which filed neither; at 55f65304 it considered generalizing beyond `2` and
  declined, twice, and forcing did not produce either move. The question text is present; the judgement is
  what fails. Of the four "design-scale" misses, 8d887ce4 is a rename judged against mis-extracted gold and
  e8e02821 a golf-remit restructure. `generality`'s prompt excludes parameterizing a constant (one in-sample
  obligation).
- **Compound asks** (one candidate spanning several targets). The tool and the judge already accept it. 10 of
  40 obligations have several change_ids (7 genuinely several declarations); 129 of 3,683 candidates ever
  spanned targets, none covering both targets of any compound obligation it could win. The naming arm split
  e83e6544 in 15 of 15 sessions, 13 of which never saw the new per-target text, so the split is the model's own
  decomposition, not the contract's; and the gold's third part (reprove via `OrderDual`) is outside naming's
  remit and draws 0 / 3 when proof_idiom files it. Reach: one obligation, already hit in 10 of those 15 runs.
  The free first test is judge-side: merge each run's two naming halves into one candidate and judge it (cents);
  majority in <= 2 of the 4 missing runs means the lever is dead for recall whatever the arm does.
- **Naming evidence.** Porting `arm-naming-bar`'s three fixes changes 0 of 6 gold-site verdicts (precision
  only: 29 of 183 queries answered about a different declaration). The real defect: at both missed naming
  sites the arm quotes the tool's over-claim -- "does not back a rename. Submit nothing on naming" after
  measuring only the prefix (round_eq' `round` 22 / 23), and a 39% `→ₗ` coercion bucket read as a convention
  (d2466bcc `coe_` 48 / 124). Fix: resolve an ascription to its coercion function (or report the mixed bucket
  unresolved) and scope the counted verdict to the prefix, in tool *and* prompt. Test with `cli bench` on
  33337 / 33421 / 33315 under the V3 knobs, ~$1-2; the null (three V runs) is on disk. Reach 0-2, in-sample;
  the d2466bcc positive is near-tautological (the naming prompt quotes that site's counts). Precision exposure
  is real: where the tool does not say "submit nothing", the arm de-primes non-gold names (comp_fract'' in 3 of
  3 runs). Suffix and dot-notation censuses fail on free recounts (3,694 of 5,029 primed-with-sibling lemmas
  state a different conclusion; dot notation 28.9%, population 6 at 33294).
- **The roster.** A cost lever, not a recall lever. In fanout, removal is a pure subtraction: dropping style,
  docs, generality, proof_idiom and family_design loses no hit at any vote threshold in 8 runs and halves
  four-PR arm spend (V3 $5.60 -> $2.75; 140 jobs -> 55) -- in-sample by construction, so say only "no hit lost
  on these runs", never "as good", and never justify it by control emission (that is selection). The one
  roster move that could add a hit is an `api_reuse` floor (57bcc9fd, its only sole-finder hit on record):
  replay its two recorded 33117 sessions whole, ~$0.40, reading rule in the survey. Do not retire `docs`: it
  has never run at its one counted on-concern obligation.

What this says about where specialist improvement is bounded: by judgement at the right site, which the
parked reasoning test (`reasoning-in-the-arms.md`) is the only lever on, and by measurement -- the burned
4-PR and 12-PR sets cannot resolve a one- or two-obligation effect, which the 46-PR unseen window
(`eval-unseen-window.md`, one flip = 1.7 pp) can.

**Naming-evidence fix, built and measured 2026-09-24 (`adcc7ba`).** The tool's counted verdicts now claim
only the leading prefix they count, and the naming prompt says so. Measured with `cli bench` (naming arm, PRs
33337 / 33421, 2 positive units + 4 negatives, the unified contract), three attempts
(`results/pr_review_v5/benches/naming_prefix_scoped_contract_a{3,4,5}.json`, ~$1.06 nominal together), against
the null on disk (three V runs, 0 of 3 at each miss site). **Reading rule, fixed before running: a site passes
at >= 2 of 3 attempts filing a rename there.**

| site | filed | the arm's reason |
|---|---|---|
| 6b02b611, `round_eq'` | **0 of 3** | considered the prime, as the new text asks, and judged it fine: "primed names are used widely ... for simple restatements", "many `*_eq'` variants" |
| ce7b5d2e, the coercion lemma | **0 of 3** | read the plurality wording ("48/124 plurality", "no stronger established rule") and answered `no_issue` |
| 64e1164f sibling (internal control) | 3 of 3 | the `toLinearMap_` rename, as always |
| negatives | 0 of 12 | the feared de-prime filings did not appear |

Both sites fail. The over-claim was real and the fix stays -- it costs nothing measured and a question-based
design inherits the honest text -- but it was not what held those two silences: the arm now engages the
unmeasured part of the name and decides against the ask. This is the survey's conclusion measured directly
at the two naming misses: judgement at the right site, not evidence.

**Roster allowlist, built 2026-09-24 (`e2db044`).** `RunDataset.arm_ids` restricts a run's specialists and is
sealed into the plan; `configs/pr_review_v5_contract_fanout4_lean.yaml` is the five-arm four-PR config (55 jobs,
~$2.75 expected against V3's $5.60 billed), for affordable reps of a four-PR condition, not for another set.
Still open from the lever survey, both cheap and recorded above: the `api_reuse` floor replay (~$0.40) and the
compound-ask judge check (cents).
