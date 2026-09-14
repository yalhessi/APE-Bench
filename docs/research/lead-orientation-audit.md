# What the lead design actually does, measured on the held-out 12

*2026-09-14. Every number here is recomputed from the six runs and six audits committed at `3a3bf72`
(`results/pr_review_v5/runs/pr5_{A_lead,B_solo_ape}_heldout12_v2_rep{1,2,3}`). Judge-free except
where marked. Written because a design discussion about "adding an orientation stage" needs to know
which parts of the current design ran at all.*

---

## 1. The design's central loop did not run

`prompts.py:74` tells the lead: *"Call `delegate` with an empty `jobs` list to run just that sweep,
read what it found, and then decide where a specialist is worth sending."* The whole premise of
A — broad sweep, then depth where it mattered — is that loop.

Counting `wave_opened` events in `lead_journals/`:

| | |
|---|---:|
| episodes running exactly **one** wave | **26 of 36** |
| total waves over 36 episodes | 46 |
| jobs dispatched | 959 |
| of which mandatory coverage floor | **846 (88%)** |
| of which carried a brief | **113 (11.8%)** |

In a one-wave episode the floor and the lead's chosen specialists are dispatched **together**, so
the lead routed on the diff alone and never read the generalist's output. That is 72% of episodes.

Floor jobs carry `brief: null, brief_text: ""` by construction (`lead.py:600-620`). So 88% of A's
dispatched work is un-oriented by design, and the lead's comprehension reaches 12% of it.

Specialist count per episode is flat at 3–5 regardless of PR size: PR 33149 has 108 work units and
received **3** specialists; PR 33337 has 7 and received 3.

## 2. Orientation is already good, and it evaporates

The lead's `submit_comprehension` on PR 33149 (rep1) asks, verbatim:

> *"Which of the new axioms/lemmas duplicate existing Mathlib results (Fourier inversion, Parseval,
> orthogonality on the torus, intervalIntegral substitution), and can they be replaced by existing
> theorems?"*

That is gold obligation `61f68eed` — *"use Mathlib's existing Parseval identity instead of
axiomatising one"* — asked before any money was spent. The same question appears in all three reps.

It was also **routed correctly**. One of the three briefed jobs in rep1:

> arm `duplication`, unit `wu:2d93e574…`
> *question:* "Is `parseval_orthonormal` already available as a theorem about orthonormal Fourier
> basis on `UnitAddCircle` or `Torus`? Can the file instead use an existing Parseval/Plancherel
> lemma?"

The arm then **found the right lemmas and said nothing**:

> `abstention.reason: could_not_establish`
> *"Searched Mathlib for Parseval/Plancherel results and found existing Parseval lemmas for
> `AddCircle`/`UnitAddTorus` (`hasSum_sq_fourierCoeff`, `hasSum_sq_mFourierCoeff`), but could not
> prove they subsume the PR's `parseval_orthonormal` since the PR's custom `fourier3D`/`T3` setup is
> not connected to Mathlib's Fourier basis, so no verified replacement compiles."*

A scored `LLL` on `61f68eed` — the site was located three times by the *generalist*, which asked for
a proof-golf refactor instead. The specialist that had the answer was contractually mute.

**The arm's warrant standard is stricter than the maintainer's.** A maintainer does not need a
compiling replacement to say "don't axiomatise Parseval, Mathlib has it."

Of 99 `could_not_establish` abstentions over three reps, **43 name a declaration the arm found**
before abstaining — `orthonormal_fourier` in `Analysis/Fourier/AddCircle.lean`,
`LinearEquiv.symm_prodComm`, `upperBounds_closure`/`lowerBounds_closure`.

## 3. Arm silence, by arm

956 arm responses, 452 empty. Abstention reasons: `already_correct` 341, `could_not_establish` 99,
`nothing_of_this_kind_here` 5, `belongs_to_another_concern` 4, `below_my_bar` 3.

| arm | filed | empty | silence |
|---|---:|---:|---:|
| generalist | 422 | 187 | 31% |
| proof_golf | 14 | 12 | 46% |
| style | 27 | 31 | 53% |
| docs | 15 | 24 | 62% |
| generality | 4 | 10 | 71% |
| proof_idiom | 9 | 36 | 80% |
| duplication | 7 | 38 | 84% |
| correctness | 2 | 17 | 89% |
| **naming** | 4 | 71 | **95%** |
| **family_design** | **0** | **26** | **100%** |

Candidates reaching the pipeline: specialists 17 / 23 / 20 against the generalist's 251 / 263 / 258.
The ten specialists take 37% of delegated spend and contribute ~7% of candidates.

## 4. The wrong-ask rows are not grain failures

All 16 `issue_match: false` rows in rep1 read the same way: **the system accepts the artifact's
shape as given and proposes the smallest local edit compatible with it, where the maintainer asked
to change the shape.**

| obligation | gold asked | system asked |
|---|---|---|
| `3dacf72e` | remove the axiom entirely | add a docstring to the axiom `cMoser_pos` |
| `f54010d8` | remove the newly introduced axioms | add a docstring for `cMoser_pos` |
| `5ffba48e` | redefine `baseOf` as a set comprehension | fix the spelling "crystallographic" in the docstring |
| `0bb42bd2` | add an Implementation-details section on ordered coefficients | minor grammatical fix to the existing sentence |
| `e83e6544` | rename **both** lemmas, reprove the lower by `OrderDual` | generic rename of one of them |
| `bd8a8d8c` | refactor into `Dense.ciSup`/`ciInf`, derive by duality | flag a duplicate, ask removal/rename |
| `61f68eed` | replace custom Parseval with Mathlib's | remove an intermediate `have`, use `simpa` |

A work unit's framing — *"here is a change target, what is wrong with it?"* — **presupposes the
target belongs**. A maintainer's first question is whether it should exist in that form at all.

A keyword classifier over all 87 wrong-ask rows in both conditions puts 31% in this bucket; that is
a crude floor, not a measurement. The 16 read verbatim are the evidence.

## 5. Three things that are built, wired, tested, and off

Each is checkable for $0 and none is a design question.

**(a) `repository_measurement` is structurally zero.** `finalization_report.json`, every rep:
`by_evidence_tier: {model_assertion: 268, verified_compile: 17, repository_measurement: 0,
lexical_rule: 0}` — while `evidence.by_status.supported: 13` and the assertions include
*"naming_norm supports: 27/27 declarations with subject `upperBounds` use the `upperBounds_`
prefix"*. `conditions.py:74-77` maps `naming_norm.v1 → repository_measurement`, but that map is read
only at `conditions.py:131`, in the **v4 deterministic** path. `generalist_findings`
(`conditions.py:136-166`) never passes `evidence_tier`, so `merge.py:83`'s default
`model_assertion` stands. The D2 maturity ladder is unwired for the channel that produces 96% of
findings. **Caveat that must travel with this:** the judge scores `counts.candidates = 285`, i.e.
all of `findings.jsonl`, so fixing the tier moves `post_publication` only — a channel the A/B spine
does not report.

**(b) `lead_synthesis.applied: false`** while the lead recorded 18 `duplicate_of` and 30 `drop`
assessments, against 37 merge conflicts in the same run. `lead_synthesis.py` exists precisely
because a lead that spotted two arms saying the same thing watched the merge suppress both.

**(c) `FILE_COHERENCE_SPEC` has never been scheduled.** Defined at `schema/findings.py:354`, wired
into `merge.py:105`, `conditions.py:215,257`, the overlay, and enforced at submission by
`file_claim_error` → `LeanPRReviewV4FileTask._extra_candidate_error` (`file_scoped.py:54-57`,
tested at `test_pr_review_v4_file_scoped.py:118-123`). It appears **nowhere** in
`src/mathlib_review/agenda/` and in no config. `finalization_report.by_arm.file_generalist: 0`.

This last one matters beyond itself: `_extra_candidate_error` is the **only** enforced ownership
boundary in the codebase — a claim outside the stage's remit is refused at submission rather than
left to prompt discipline. Everything else (`expected_concerns`, the arm briefs' "this does not
widen your scope") is prompt text. `registry.py:56-71` says so explicitly: `expected_concerns` is
"**not** an admission rule".

## 6. What this does and does not license

- It does **not** show that a depth-ordered redesign would help. The obligation grain distribution
  is whole-pr 0 / file 3 / family 7 / declaration 9 / proof 4 — the top rung is empty, and 19 of 23
  obligations lie inside a single already-scheduled work unit.
- It does show that **A has never been measured as designed**: the sweep-then-route loop ran in 10
  of 36 episodes, three downstream mechanisms are off, and the coarse arm that does exist
  (`family_design`) returned nothing in 26 invocations.
- Any comparison of a new architecture against A should first re-measure A with (a), (b), (c) on,
  or the new design will be credited with fixing plumbing.

---

## 7. Increment 0, measured (2026-09-14)

The three dormant mechanisms of §5, each taken as far as free evidence allows. Replays are in
`scratchpad`-style scripts, use no model calls, and read only tracked run artifacts.

### (1) Evidence tier — **done, small, real**

Attaching the warrant a holistic finding's evidence earned, replayed over each rep's recorded
findings with pre-merge admission restored from the gate (the "before" reproduces each run's
own conflict count exactly, 37/35/34):

| rep | conflicts | published | gain |
|---|---|---|---|
| 1 | 37 → 35 | 25 → 27 | naming +2 |
| 2 | 35 → 33 | 28 → 30 | naming +2 |
| 3 | 34 → 32 | 27 → 29 | naming +2 |

Two conflicts resolved per rep in all three, both on PR 33145's `Dense.continuous_*` renames.
`naming` published **zero** in all three reps before. Read narrowly: the judge scores
`counts.candidates` = all 285 findings, so this moves `post_publication` only and **does not
move the A/B spine's reported recall.**

### (2) `apply_lead_synthesis` — **do not turn on**

This was never dormant plumbing. It has been off since 2026-09-08 with a measured regression
on `pr5_smoke4_rep9`, and the held-out 12 reproduces it worse. Replaying the recorded
assessments and intersecting removals with the candidates that carried an issue hit:

| rep | obligations hit | lost entirely if applied |
|---|---:|---|
| 1 | 7 | **3** — `073625ed`, `57bcc9fd`, `64e1164f` |
| 2 | 5 | **1** — `073625ed` |
| 3 | 6 | **2** — `073625ed`, `c9739efc` |

43%, 20% and 33% of each run's hits. **`073625ed` goes in all three reps** — PR 33285's
proof-golf obligation, `HHH` in the spine, one of the five stable hits that are A's only
distinguishing claim over solo. Folding is meant to be lossless and is not.

### (3) `FILE_COHERENCE_SPEC` — **a feature, not a switch**

Reach on the held-out 12, computed from `schedule_files` over the release's change graphs:
**78 file invocations**, 52 single-target (which may only make a `scope_placement` claim) and
**26 multi-target**. Of the 17 obligations whose gold `change_ids` the audits record, **4 span
more than one work unit** — `3dacf72e`, `f54010d8` (33149's axioms, which A already hits
`HHH` through the generalist) and `57bcc9fd`, `bd8a8d8c`, both currently `L` rows whose ask is
inherently multi-target. So the distinctive new reach is **2 obligations**, at roughly
+78 jobs/rep (~$1.2, ~8% on A's $14.59).

It cannot be switched on. `AgendaProposal.work_unit_id` is a required, non-optional field and
a file-scoped invocation spans several work units, so scheduling one needs either a widened
agenda schema — which rewrites every agenda hash — or a synthetic per-file pseudo-unit. That
is a design decision with sealing consequences, not a config line, and it is why this arm has
sat wired-but-unscheduled.

### A worktree note

`tests/datasets/test_claude_code_containment.py::test_a_review_workspace_resolves_git_upward_into_this_repository`
**fails in any worktree and passes in the main checkout.** `.claude/worktree-setup.sh` symlinks
`data/`, so a review workspace reached through it resolves `git rev-parse --show-toplevel` to
the main checkout rather than to the worktree. It is a property of the worktree arrangement,
not a regression.
