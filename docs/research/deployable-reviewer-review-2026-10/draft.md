# Draft under review (2026-10-09): a deployable convention reviewer, specified

## The user's direction, verbatim

> "What is the most worthwhile investigation at the moment in order to reach a better deployable reviewer than the solo reviewer?"

> "What does that suggest we should try in our specific project? What ideas should we include from these systems and what ideas are likely to help us in our reviewing system and are worth adding or at least designing probes or experiments to investigate"

> "Let's flesh out what we want to do further. Let's get more specific about what exactly we would build and how it would work. Then let's run the adverserial reviewing on the designs"

## The target

**A deployable reviewer** is one that sees no maintainer asks. It must beat the solo reviewer on
issue recall: the share of maintainers' round-1 asks reached, matched blind. Its volume is reported,
and kept within a stated guard.

**The model.** Development runs on DeepSeek-V4.1-Flash, self-hosted on `first` at $0. The solo
baseline there (DX, three reps on stage L/D's 46 probe asks) reaches:

| | asks of 46 |
|---|---|
| mean of a rep | 13 |
| union of 3 | 16 |
| at least 2 of 3 | 12 |
| all 3 | 11 |

On the dev held-out 12 (23 obligations, the standard judge) it reaches 8, 6, 9.

**For reference, the exact-brief ceilings, which are not deployable:**
- DP (the exact conventions with examples and precedence) reaches 30 of 46 a rep and 35 in union.
- The union of every ceiling session ever run reaches 40 of 46.

## What the record says the designs must address

From `docs/research/ceiling-residual-2026-10.md`; one probe set, provisional:
1. **Instability:** a DP session reaches about 25 of 39 in-census asks, its union 29, the all-model
   union 34.
2. **At the right place, asked something else:** golfing, judging on merits, applying the convention
   next door. Asked alone at the place, the bare sentence produces the change for most of these (the
   ladder, unmatched).
3. **Execution:** a check run on the wrong variant, read as "conforms" (`simpa` forms, `positivity`).
4. **Information outside the packet:** a PR's history, the library's orientation.

Every ask-free delivery inside an agentic session so far moved nothing: stage F +0.03, stage G +0.00,
the detectors only as volume. The decision to file is where they lost.

## Five components

### A. The convention check engine (per-place rule checkers: BitsAI, AutoCommenter, Tricorder)

**A1. Places.** The PR's changed declaration segments plus one PR place. This is
`places.py::segments`: hunks split at declaration headers and top-level commands, docstrings and
attributes kept with their declaration, a segment kept only if it holds a changed line. There are 4
to 43 places on the probe PRs. Each segment maps to its change target in the PR's change graph, so
its findings carry a `primary_change_id` the judge can pair.

**A2. Rules per place, chosen ask-free.**
- **v0:** stage F's blind Opus picks, 25 per PR. They exist for 10 probe PRs, and hold the right entry
  for 22 of 33 in-census asks.
- **v1, for any PR:** a DeepSeek selector with stage F's rubric, reading the PR text, the diff and all
  438 sentences, and returning 25 per PR. It selects on whether the situation occurs, not on whether
  the code conforms.
- **Plus syntactic gates** for the about 40 token-triggered entries: imports, attributes,
  `variable`/section, named arguments, primes in names, docstring prose. Each gate is a regex or Lean
  syntax test on the segment, and adds its entry at that place whatever the selector said.
- **Part kind** (proof, statement, docs, command, import, PR) orders the rules at a place. It never
  removes one.

**A3. The check.** One DeepSeek turn per (place, rule): the ladder's U form plus `CONFIDENCE`, with
the PR text and whole diff in the head. Two samples. This is exactly what the places test is
measuring now.

**A4. Calibration per rule** (AutoCommenter's per-URL thresholds, Tricorder's disable rule).
- **The record.** A1-A3 run on about 25 census PRs, all val1000 and disjoint from every probe and
  evaluation set, with reader A's labels as the asked places. The per-rule record is departs rate and
  confidence at asked, unasked and non-selected places.
- **The policy:**
  - suppress a rule whose unasked departs rate exceeds a cut;
  - otherwise file a (place, rule) only if both samples say `departs` and the mean confidence is
    above the rule's threshold (set on the census PRs);
  - cap at N filings per PR, ordered by confidence.
- **What the policy is chosen to optimise:** asked pairs kept per filing on the census PRs, under a
  volume guard. It is never tuned on the probe or evaluation PRs.

**A5. Validity by execution** (open-code-review's refutation-only filter; Lean makes falsity
checkable).
- For a `CHANGE` that is code, apply it to the reviewed file and compile against the PR's reviewed
  workspace, with the closer battery's compile path (`lake env lean` on the edited file).
- **If it compiles**, it is filed.
- **If it fails**, it is turned into a question that names the convention and the change ("can
  `simpa using h` close this?"), not dropped. Stage G lost the `gcongr` ask by dropping.
- A prose change is filed as is.

**A6. Output.** Findings in the standard schema (claim, requested change, `primary_change_id`, the
convention as `concern_tags`), unioned with the solo reviewer's findings. A finding duplicating a
solo finding at the same change target is merged (`review/merge.py`).

**Where it is built, and when.** Probe scripts first (`places.py`, extended), until the end-to-end run
passes. Only then a review design `convention_checks` in the runner (`design` field, beside `solo`),
with each check a single-turn call under `ExecutionLimits`, launched by `TaskOrchestrator` one task
per PR.

### B. Aggregated solo (Bugbot's passes, SWR-Bench's aggregation)

- **B1.** K = 3 solo passes, decorrelated (Bugbot's decorrelator): the PR's files in a seeded random
  order in the diff and the PR model, and a different seed per pass. Existing reps are K = 3
  undecorrelated passes: union 16 against a mean of 13 (+3 of 46), majority vote 12.
- **B2.** Findings are keyed `(pr, primary_change_id, issue_kind)`, the key on which the record
  measured cross-run agreement, with in-sample hit rates 0.29-0.89 at 2 of 2.
  - **Union** is published for recall.
  - **The count of agreeing passes** ranks the findings.
  - A cap per PR by agreement then confidence controls volume.

### C. Exhaustive execution checks for template conventions (Infer, Tricorder; the closer battery as a producer)

**C1. The procedures, each a set of single edits compiled against the reviewed workspace:**
- **terminal-step replacement:** each `by` block's last one to three steps replaced by each of
  `simp`, `simpa`, `positivity`, `gcongr`, `omega`, `norm_num`, `linarith`, `grind`, `aesop`;
- **merge:** consecutive `simp only [...]` / `rw [...]` then `exact h`, merged to
  `simpa [...] using h`;
- **old-proof replay:** the pre-PR proof of a changed declaration, under the new statement;
- **drop a `noncomputable`**;
- **restore a dropped attribute.**

Every compiling variant is a fact: "this step closes with `positivity`".

**C2.** The facts reach the review in one of two ways: as findings directly (the engine's channel),
or as a producer section of the solo packet (the `producers` seam). The closer battery measured the
right edit at the right place producing the maintainer's ask for 8 of 15 try-it asks. Exhaustive
yield and its volume are unmeasured.

**C3. Compute.** About 10-40 s per compile. It needs the persistent checker
(`docs/todo/lean-persistent-checker.md`) to be affordable over every proof in a PR.

### D. A history source for the residual no packet carries (Anthropic's plugin: git history and prior PR comments)

- **D1.** For each touched file and declaration: the PR store's earlier review comments on that file
  (before the PR's creation), and the file's git log in the Mathlib clone. A one-turn reviewer then
  reads these with the diff: "do earlier reviews or the file's history imply a change here?"
- **D2.** Built only if its ceiling probe passes: for each of the 46 probe asks, does an earlier
  comment on the same file or declaration carry the same ask or convention?

### E. Census robustness for A and C

- **Each entry gets:**
  - a `part_kind` set;
  - a `trigger` tagged syntactic or semantic, with stage G's rule-writer rubric as the template;
  - `not_when`;
  - `check_kind`;
  - a template id, for the entries C can execute.
- **Merge the readers' duplicates** through the cross-map.
- **First for the about 100 head entries** that A4's calibration can measure; the tail is selected by
  A2's model and checked by A3 unscoped.

## Measurements, in order (none run; the places test is running now)

| # | what | set | cost | threshold to continue |
|---|---|---|---|---|
| 0 | the places test (A3's discrimination), running | probe | $0 | its pre-registered rule: AUC asked vs decoy ≥ 0.75 and (decoy departs ≤ 0.10 or a cap of 10 keeps ≥ 0.50 of asked pairs) |
| 1 | A4's calibration record and policy | 25 census PRs | $0, a few hours on `first` | the chosen policy keeps ≥ 0.6 of asked pairs at ≤ 10 filings per PR on held-out census PRs (leave-PR-out) |
| 2 | A end-to-end, v0 selection (stage F's picks), A4's policy, unioned with DX | the 10 stage F probe PRs (33 in-census asks), three reps, matched blind | $0 plus matchers ~0.5M tokens | (A ∪ DX) − DX ≥ +0.10 of in-census asks on both matchers; findings per PR ≤ DX + 10; control-PR emission reported |
| 3 | A end-to-end, v1 selection, on the evaluation set | the dev held-out 12, the standard judge | $0 plus the judge | ≥ +3 of 23 obligations over DX's mean (8, 6, 9) across three reps |
| 4 | B: decorrelated K = 3, union and agreement cap | probe sets and dev | $0 plus matchers | union − single ≥ +4 of 46; the agreement cap keeps ≥ 0.8 of the union's gain at ≤ 1.5× single's findings |
| 5 | C: the exhaustive battery on the probe PRs' proofs | probe | compute | ≥ 5 of the ~10 try-it probe asks produced, with facts per PR reported |
| 6 | D's ceiling probe | the 46 probe asks | CPU, reading | ≥ 5 asks covered, or D is dropped |

## Known risks, for the review to press

- **Everything was designed on the stage L/D probe sets.** Measurements 2 and 4 are in-sample; 3 is
  the out-of-sample test.
- **Volume.** Maintainers raise 1 in 20 to 1 in 400 of the places a convention's situation occurs. A4
  calibrates on census asks, which are a lower bound on what would be welcome.
- **The deployed systems that reach high precision are trained.** A4 is calibration over a prompted
  checker, on 1,833 census asks.
- **A2 v1** (a DeepSeek selector) is unmeasured. Stage F's Opus selector reached 0.45 at 10 and 0.67
  at 25.
- **Compute** for C, and for A5's compiles.
