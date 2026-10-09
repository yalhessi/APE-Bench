# A deployable convention reviewer: what the third adversarial round left of the specified design (2026-10-09)

**What was reviewed.** The design is the user's request (2026-10-09): *"Let's get more specific about
what exactly we would build and how it would work. Then let's run the adverserial reviewing on the
designs."* The draft specified five components:
- **A:** the per-place convention engine;
- **B:** aggregated solo;
- **C:** exhaustive execution checks;
- **D:** a history source;
- **E:** census robustness.

It also set out six measurements.

**The round's files** (`deployable-reviewer-review-2026-10/`):
- the draft (`draft.md`) and the briefs as sent (`briefs.md`);
- the four reports as returned: `R1_record_evidence.md`, `R2_mechanics_cost.md`, `R3_measurement.md`,
  `S_steelman.md`.

Nothing ran beyond counting. Figures a reviewer computed are marked *(R1)* and so on.

## 0. The answer

**The baseline in the draft was wrong, and that changes the picture** (R1, R3, S).
- **The union of three solo DeepSeek reps is already a deployable reviewer that beats one solo
  session.**
  - On dev it reaches 11 of 23 against a mean of 7.67, with 0, 0 and 2 control findings
    (`local-ds41-2026-10-06/README.md`).
  - On the probe set it reaches 16 of 46 against a mean of 13.
  - Even a two-rep union reaches 9.67 on dev *(R3)*.
- **So every new component is measured against that union, paired by rep.** Its gain is the share of
  asks a union of solo reps never reaches.

**What survives:**
- **A, the engine:** kept and narrowed, because it is the only component aimed at the two largest gap
  classes. It is measured as a **generator**, uncapped, with volume reported beside it. Every cap and
  threshold is selection under the user's 2026-09-22 ruling: it may be measured, not proposed.
- **B:** kept as the comparator, and as the deployable step it already is. Its agreement ranking is
  dropped.
- **C:** folded into the static-analysis thread, through Mathlib's own `tacticAnalysis` linters.
- **D:** a CPU ceiling probe only, broadened to library analogues.
- **E:** cut down to what A's syntactic gates need.

**Expected gain.**
- **A over the free union on dev:** +1 to +3 of 23 *(R1, S)*, which is the size of the judge's noise.
  That is why the out-of-sample test moves to a fresh set (§4).
- **A's cost:** about 1,000 one-turn calls for a median PR as specified, ~10× the draft's figure.
  Cheaper forms must be shown to give the same verdicts before any long run.

## 1. The round

- **Who ran it.** Four Opus 5.5 subagents, read-only and independent:
  - R1: the record and the evidence;
  - R2: mechanics, codebase and cost;
  - R3: measurement and evaluation;
  - S: the steelman.
- **Cost.** About 0.61M subagent tokens, run before and across the week's 10:00 reset.
- **A note on blindness.** R2 read interim places-test rows for throughput, and its report cites an
  interim unasked `departs` rate of about 0.29. That is recorded in the places README (`0cfbbb33`).
  The places rule and every reading were fixed before it.

## 2. What the four agree on

**2.1 The comparator is the solo union, paired by rep** (R1, R3, S).
- The draft's bars, such as "≥ +3 over DX's mean" on dev, are met by solo run twice.
- R3's corrected comparison is A ∪ DX_i against DX_i ∪ DX_j, under one seal. This replaces measurement
  4 as a design test: B becomes the comparator.

**2.2 B's agreement ranking is dropped** (R1, R3, S).
- Measured out of sample on solo passes, it is at chance: hit rates by agreement 0.50, 0.67, 0.29,
  0.44; within-PR AUC 0.482 (`ensemble-union-2026-10-02/README.md`).
- It is saturated, because every pass anchors at nearly every gold change. The draft cited only the
  earlier in-sample 0.29-0.89.
- Stated confidence has also been at chance as a selection signal three times (`selection-signal.md`:
  0.486-0.516).
- **Decorrelating by file order has a weak prior.** 15 of 36 PRs touch a single file *(R2)*, and reps
  differ in what they ask, not where they look (Jaccard 0.65, S).

**2.3 A4's per-rule calibration cannot be fitted as specified** (R1, R2, R3).
- **Underpowered.** 25 val1000 PRs carry a median of 67 asked pairs over 47-63 entries. Only 4-8
  entries get three asks or more, and 22-46 of the 100 head entries get any ask at all *(R3)*.
- **Contaminated.** The codebook was written from those very asks.
- **Selection.** It is selection under the 2026-09-22 ruling (`.claude/rules/mathlib-review.md`):
  *"we currently don't have a good enough reviewer to start talking about selection"*.
- **Stage H's per-rule rate was its worst design:** 2 of 12 at an ask.

**2.4 A as specified costs about 10× the draft's figure** (R2, R3, S).
- **Calls:** 25 rules × ~20 places × 2 samples is ~1,000 calls for a median PR.
- **Throughput:** read from the server log, ~600-700 calls an hour at 1,770 tokens a second with 56
  running *(R2)*.
- **What that means:**
  - one dev rep is ~19k calls, about 30 server-hours of `first`;
  - measurement 1 is 30-60 hours, not "a few hours";
  - a large PR (33294, 148 places) alone takes ~12 hours.
- **Cuts worth a fidelity test first** (R2, S):
  - a second sample only after a first `departs`, which saves about 35%;
  - one call per place answering every selected rule as a verdict table (open-code-review's pass per
    file);
  - hard syntactic gates that reuse `producers/` and `conventions/situations.py`.

**2.5 The evaluation set must change** (R3, R1).
- **Dev is development material** (the 2026-09-24 ruling in `eval-set-selection.md`). Contract v2 and
  some of the detectors were tuned there, and its share in census is unmeasured.
- **A fresher set exists:** the validation window minus small12, with 76 agreed asks on 35 PRs plus
  about 16 no-ask PRs. No conventions design touched it, and val1000 excludes it *(R3, computed)*.
  - Whether its reviewed workspaces are built is unverified.
- Dev and the probe sets stay reported, never gating.

**2.6 Controls the draft lacked.**
- **A decoy engine** (R3; S's "shuffled rules"): the same engine fed random entries the selector did
  not pick, or another PR's picks, under the same seal. It prices how much of any gain is volume
  meeting a lenient matcher. The ensemble union's twelfth obligation was a judge flip.
- **The AP arm** (R1): the same ask-free picks delivered inside the session under DP's precedence, on
  DeepSeek. "The filing decision is where in-session delivery lost" was measured on Claude without
  precedence. On DeepSeek, precedence moved +0.20 with the exact picks. So AP is A's cheaper rival,
  and it has never run.

**2.7 The plumbing that exists and the plumbing that does not** (R2).
- **Exists:** the change graph, `anchor_submitted_findings`, `import_probe_session`,
  `merge.union_findings`, `cli tool lean_verify_edit`, and reviewed workspaces for all probe and
  census-detector PRs.
- **Does not exist:**
  - **Anchoring segments to targets.** Segments carry no line numbers and disagree with the
    change-graph targets (23 against 12 on 26755). `resolve_target` takes names or paths, not
    path:line.
  - **De-duplication.** `union_findings` folds only identical asks (6 of 375), so paraphrases at one
    target survive.
  - **A home for A5.** A5 must compile through `ape.toolkits.execute.lean`, not the battery's bare
    `lake env lean` with another worktree's path hard-coded.
- **Placement, once A earns a build:**
  - one single-turn `BaseTask` per (PR, place, rule) under `TaskOrchestrator`, resumable across 8-hour
    server jobs;
  - then a no-model chained stage that emits solo-contract findings.
  - Never one task per PR making ~1,000 calls inside it.

**2.8 C, D and E are small** (R1, S).
- **C.** The terminal-step sweep went 0 of 3 on its own targeted asks. Its recall ceiling over solo is
  +2 of 46 (old-proof replay: v0062, v0063); solo already reaches v0016, v0131 and v0132. Execution-
  checkable conventions hold about 7% of census asks (the detectors' dead end). Mathlib ships the
  sweep as `tacticAnalysis` linters, which need no persistent checker.
- **D.** At most +1 (v0053; p0010 is an analogue, not history). As drafted, D1 reads other PRs'
  comments on the same file, which is Mode A precedent priming. **Analogue retrieval**
  (`after-structure.md` §4) is the higher-ceiling evidence source: design asks are 23-24% of asks,
  and three of dev's nine never-reached obligations are analogues.
- **E** is needed only for A2's gates.

## 3. The design that survives

| component | as it stands now |
|---|---|
| **B, the solo union** | the comparator, paired by rep, and the deployable step it already is: dev 11 of 23 against 7.67 |
| **A1, places** | change-graph targets, or segments carrying explicit (path, line) passed to `anchor_submitted_findings`; PR-place findings stay unanchored and diagnostic |
| **A2, rules** | v0 = stage F's picks (10 probe PRs); v1 = a DeepSeek selector, **measured alone first**; syntactic gates reuse `producers/` and `situations.py` |
| **A3, the check** | the places form, in the cheapest variant that passes a fidelity test (sequential second sample; a verdict table per place) |
| **A4, policy** | none proposed. Recall is reported uncapped, with volume beside it. Caps and thresholds are measured as operating points only (the selection ruling). A stratified calibration (every census ask at its own place, plus a sample of unasked places per head entry, ~10k calls) only if volume rules the generator out |
| **A5, validity** | the proposed change compiled through `lean_verify_edit`. A failure becomes a templated question naming the convention and the change: DP filed no questions though asked to, and stage G lost `gcongr` by dropping. Validity is the generator's own check, not selection |
| **A6, output** | solo-contract findings, union with solo via `union_findings`; duplicates reported, not hidden |
| **Controls** | the decoy engine; the AP arm |
| **C** | `tacticAnalysis` linters plus old-proof replay, in the static-analysis thread |
| **D** | a CPU ceiling probe covering history and library analogues; analogue retrieval stays its own thread |
| **E** | cross-map duplicate merge; triggers for the ~40 token-triggered entries |

## 4. The sequence, each step with its threshold (none run)

| # | step | cost | continue if |
|---|---|---|---|
| 0 | the places test (running, done ~12:00), with the readings declared before (`78b9cd6f`) | $0 | not the detector band; within-PR AUC and the leave-one-PR-out range read beside the pooled one |
| 1 | **P**: the validation remainder's census share, its reviewed workspaces, and segment → gold change pairing; and on dev the same | CPU, plus one assign pass (~0.1-0.2M tokens) | ≥ 50% in census and ≥ 70% pairing, or the set is not used for gating (R3) |
| 2 | A2 v1 alone: the offline selection bench (248 other-years asks + 39 probe asks) | ~300 calls, < 2 h of `first` | recall@10 ≥ 0.60 (stage F's Opus: 0.45) |
| 3 | A3's cheap forms against the single-rule form, on the places items | ~300 calls, 1-2 h | verdict agreement ≥ 0.85, asked-pair `departs` within 0.05 |
| 4 | the engine, one rep, on the 10 stage F PRs (in-sample): A ∪ DX_i against DX_i ∪ DX_j, the decoy engine ∪ DX, and AP, under one seal | ~5.5k calls in the cheap form, 1-2 server jobs; matchers ~0.3-0.5M | ≥ +0.10 over DX ∪ DX' on both matchers; decoy gain ≤ +0.03; added findings yield ≥ half of DX's asks a finding |
| 5 | **the out-of-sample test**: the validation remainder, three reps, R3's rule below | ~3-5 server jobs a rep (inferred), the matchers | R3's rule |
| ∥ | C through the linters on the probe workspaces; D's ceiling probe with analogues | CPU | C: report facts a PR and asks produced; D: ≥ 3 asks no solo union or A pick reaches |

**R3's rule for "a better deployable reviewer than solo",** stated before any run. On the validation
remainder, three reps an arm, one seal, two blind matchers, all of the following on both matchers:
- (a) mean reach over all asks at least +0.06 above DX_i ∪ DX_j paired by rep, about 5 of 76;
- (b) a stable count at least S2's;
- (c) the added findings' yield (asks gained over findings added) at least half of DX's asks a
  finding;
- (d) control emission at most 2.0 a no-ask PR;
- (e) the decoy engine's gain at most +0.03; otherwise the reading is suspended as matcher leniency.

## 5. Decisions for the user

1. **Whether to name the three-rep solo union the current deployable reviewer.** It is free, already
   measured on dev (11 of 23 against 7.67), and the comparator for everything else.
2. **The selection ruling.** A is measured uncapped. Is reporting capped operating points beside it
   acceptable, or should even that wait?
3. **The evaluation set.** Step 1 decides whether the validation remainder can replace dev for gating.
4. **Compute.** Even in its cheap form, A is likely 10-100× a solo session. Steps 4 and 5 are days of
   `first`, shared with gg676's jobs.
5. **Subscription spend.** Matchers on the primary account: about 0.3-0.5M a seal.

## 6. Rejected, with the evidence

| proposal | why | reopens if |
|---|---|---|
| A single solo rep as the comparator | Solo run twice already meets the draft's bars (dev two-rep union 9.67, three-rep 11, against 7.67) (R1, R3, S) | -- |
| B2: rank or cap by cross-pass agreement | Out of sample at chance (AUC 0.482, non-monotone); saturated at gold anchors; "a label, never a vote" (plan 2026-10-01) (R1, R3, S) | agreement is monotone in hit rate on decorrelated DeepSeek passes |
| B2's confidence tie-break | Solo findings carry no `model_confidence`; stated confidence at chance three times (R2) | -- |
| A4: per-rule thresholds fitted on 25 val1000 PRs | Not identifiable (4-8 entries with ≥ 3 asks); contaminated; selection under the 2026-09-22 ruling; stage H's rate design the worst (R1, R2, R3) | the generator is good enough to discuss selection, and ≥ 10 asked places exist per calibrated rule |
| A cap or threshold as A's design | Selection (the same ruling); measured only as an operating point | the same |
| A as specified (25 rules × every place × 2 samples) | ~1,000 calls a PR; ~1.5 node-hours a median PR, ~12 for 33294 (R2) | a cheap form passes the fidelity test |
| One task per PR making ~1,000 calls inside it | The hand-rolled loop CLAUDE.md forbids; use one `BaseTask` per check under `TaskOrchestrator` (R2) | -- |
| `merge.py` as A6's de-duplication | It folds only identical asks (6 of 375) (R2) | -- |
| Dev held-out 12 as the gating evaluation | Development material since 2026-09-24; contract v2 and detectors tuned there (R3) | -- |
| Measurement 3 changing set and selector together | Two variables; a failure could not be attributed (R1, R3) | -- |
| Measurement 4 (decorrelated K = 3 with an agreement cap) as a design test | +4 against an existing +3 is one ask; the cap demotes exactly the union's gain (R3) | -- |
| C1's terminal-step sweep, hand-written | 0 of 3 on its own targeted asks; Mathlib ships it as `tacticAnalysis` (R1, S) | the linters miss what a sweep would find |
| C's facts delivered as a packet section | Detector sections reached 0-1 of 13 alone (dead-ends) (S) | -- |
| Measurement 5's recall bar | Already met by the targeted record; in-sample by construction (R1, R3) | -- |
| D1 as a reviewer reading other PRs' comments | Mode A precedent priming (dead-ends) (R1, S) | recognition or ranking use, not priming |
| Global `not_when` fields (E) | Risk narrowing `departs`, as DP's examples did in the ladder (S) | used only to rescue a rule a policy would suppress |
| The draft's names D1/D2 | They collide with the record's D1 (`structured`) and D2 (critic) (R1) | -- |

## 7. What this does not settle

- **Everything still hangs on discrimination,** the places test's verdict. A generator that says
  "departs" everywhere is a detector whatever the cost.
- **The gain on dev,** at +1 to +3 of 23, is inside the judge's noise. Only the fresh set can read it.
- **Selection stays open.** Stage F's Opus picks hold 0.67 of entries at 25. DeepSeek's v1 is
  unmeasured. The 286 thin tail entries cannot be calibrated.
- **Analogue retrieval** reaches what no convention engine can (design and comparison asks, about a
  third), and is its own thread.
- **The deployed systems that reach high precision are trained.** A prompted engine over 1,833 census
  asks may top out lower.
