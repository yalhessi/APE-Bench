# S — steelman (final report as returned, markdown layout normalised; 133k subagent tokens, 35 tool calls, 6.5 min)

Read = on disk; inferred = my estimate. No verdict of the running places test was read (its pre-registered reading stays clean); only token counts and timings from its 602 of 2,022 rows (08:53).

## 1. The strongest plan

The deployable reviewer is the **union of three DeepSeek solo reps (B, free and already measured: 11 of 23 on dev against a mean of 7.67, with 0, 0 and 2 control findings, read, local-ds41 README) plus a per-place convention engine (A) that files directly**, so no session decides whether to file; every A result is measured over that union, not over one rep. A asks one bare sentence per (place, rule) in the ladder's U form. A5 is kept, but its question ("can `simpa using h` close this?") is templated, not left to the model. Volume is controlled per rule (Tricorder-style: switch a rule off on a noisy measured record, calibrated on census PRs), with a per-place confidence threshold or cap only as a second, reported operating point. C's try-it facts come from Mathlib's own `tacticAnalysis` linters, not a hand-written battery, and reach the output through A's channel and per-rule policy, never as a packet section. D becomes a CPU ceiling probe that covers library analogues (orientation, siblings) as well as history. The residual classes: instability — union over reps plus two samples per (place, rule); asked something else at the place — A's per-place question; execution — A5 compiles the change and turns a failure into a question; outside the packet — only probed (ceiling 1-2 of 46 asks).

## 2. Components

**Kept.**
- *A1, A3 (per-place, one rule per call, bare sentence):* the ladder's unblinded look has U writing the change for 6 of DP's 7 gains; DP's examples lowered `departs` 93 → 88 of 117 and flipped three asks U had reached (read; unmatched, provisional).
- *A5, failure becomes a question:* v0092/v0093 were lost to "a failed check read as conforms"; stage G dropped the `gcongr` ask the same way. Templated, because DP filed no question-form finding over 131 anchored findings though its paragraph asked for them (read, Result 7).
- *A6, union and merge.*

**Changed.**
- *Baseline:* measurement 3's bar (≥ +3 over the DX mean) is already met by B's plain union at no cost (read). The bar should be the DX 3-rep union + 2, i.e. ≥ 13 of 23.
- *A4's confidence threshold:* the record closed stated confidence as an absolute signal for review findings (within-PR AUC 0.486, read, `selection-signal.md`). Lead with per-rule suppression plus 2-of-2 sample agreement; use the stated confidence only if the places test's AUC reaches ≥ 0.75. Report recall without the cap as primary — a cap is selection, and the user's 2026-09-22 ruling on selection still stands.
- *A's cost is about 10× the draft's figure* (read from the places run: mean 9.5k completion tokens a call, 19.4 places a PR, ~8.6 calls a minute while sharing the node, inferred). 25 rules × ~20 places × 2 samples ≈ 1,000 calls a PR ≈ 2 h a PR, ~150× a DX session's ~62k tokens; measurement 1 on 25 census PRs is about 50 h, not "a few hours", and one dev rep about 24 h. Cuts worth testing: a second sample only after a first `departs`; one call per place answering every selected rule as a verdict table (OCR's pass per file); hard syntactic gates for the token-triggered entries. Scoping by the selector's `where` looks lossy: a crude file-name match finds the asked file in `where` for only 10 of 26 picked asked pairs (computed; a lower bound).
- *E's `not_when`:* only for rules A4 would otherwise suppress, as a rescue; added globally it risks narrowing `departs` the way DP's examples did.

**Added.**
- A shuffled-rule control: each PR gets another PR's stage F picks, pricing how much of any gain is volume and judge leniency (the ensemble union's 12th obligation was a judge flip, read, `60628bfe`).
- Dev's census coverage, measured before dev is used (step 1).
- Measurement 2 simulated from the places test's outputs instead of run (step 2).

**Dropped.**
- *B2's agreement ranking and cap:* measured out of sample on solo passes, AUC 0.482; hit rates by k 0.50 / 0.67 / 0.29 / 0.44, not monotone, and saturated, since every pass anchors at nearly every gold change (read, `ensemble-union-2026-10-02`). The draft cites only the in-sample 0.29-0.89.
- *Measurement 4's matching:* union recall is on disk. The reading-order decorrelator stays as a free variant with a weak prior: reps differ in what they ask, not where they look (Jaccard 0.65).
- *C2's packet route:* detector sections reached 0-1 of 13 alone, and 13 of 14 unasked facts passed straight through under the disposition paragraph (read, dead-ends).
- *D as a reviewer that reads history:* another PR's review comment used as an example is Mode A, a dead end. D stays a probe only.

## 3. Cheapest decisive sequence

| # | step | cost | proceed if |
|---|---|---|---|
| 0 | places test, as pre-registered (running) | $0 | not the detector band (decoy `departs` < 0.40 and AUC > 0.60); otherwise A is volume and the deployable is B's union alone |
| 1 | label dev's 23 obligations, especially the 12 outside DX's union, with census entries and segments | reading; a subagent ~100k subscription tokens (user's call) | ≥ 4 of the 12 have an in-census entry at a changed segment; otherwise dev cannot show A's mechanism and the out-of-sample test moves to a census-labelled held-out set never developed on |
| 2 | simulate A(v0) ∪ DX on the probe set: step 0's verdicts × stage F's picks × DX's matched cells; volume as decoy rate × places × 25 under a leave-PR-out per-rule policy | CPU, plus blind matching of asked-pair changes (~0.2-0.4M subscription tokens) | projected (A ∪ DX) − DX ≥ +0.10 in census at ≤ 10 filings a PR |
| 3 | cheap-form fidelity on the places items: multi-rule per place, sequential second sample, reasoning medium | ~300 calls, ~1-2 h on `first` | per-pair verdict agreement with single-rule ≥ 0.85 and asked-pair `departs` within 0.05; adopt the cheapest form that passes |
| 4 | DeepSeek v1 selector on the 10 stage F PRs | ~20 calls, < 1 h | hit@25 ≥ 0.55 in census (Opus 0.67); otherwise two selector samples in union |
| 5 | A4's census record, in step 3's form | 2-50 h on `first`, by form | as drafted: leave-PR-out keeps ≥ 0.6 of asked pairs at ≤ 10 a PR |
| 6 | out-of-sample test, 3 reps, beside the shuffled control | $0 generation + the judge | mean ≥ DX 3-rep union + 2; gain obligations hit by findings tagged with their convention; shuffled control ≤ +1; control findings ≤ 3 a PR |
| ∥ | C through `tacticAnalysis` linters on the probe workspaces; D's ceiling probe with analogues | CPU, minutes a file | C ≥ 5 of the ~10 try-it asks, facts per PR reported; D ≥ 5 asks |

The linters need no persistent checker. Steps 0-4 cost under 3 h of GPU and can kill A before the ~50 h steps.

## 4. Recall ceiling (inferred)

**Probe set, in census (33 asks on the 10 stage F PRs; in-sample).** Picks hold the entry 0.67 (read) × `departs` at the asked place 0.79 (read, unmatched) × right change given `departs` ~0.7 × 2-of-2 agreement ~0.75 × policy keep 0.6-0.8 ≈ 0.22-0.30, 7-10 asks for A alone; after overlap with DX, a union gain of about +5 to +8 (+0.15 to +0.24). The uncapped bound is about DE's level.

**Dev held-out 12 (23 obligations).** 12 lie outside DX's union; 9 are reached by no Opus cell — five conventions a check can state (dot notation twice, `@[to_fun]`, a primed name, a rename's sibling), three design or analogue asks, one documentation structure (read, after-structure §0). With census coverage ~0.85 × selection ~0.55 × right change at the place ~0.5 × policy ~0.7 × judge ~0.8, about 0.13 of the eligible obligations get through. **Expected 12-14 of 23** (+1 to +3 over the free union, +4 to +6 over the DX mean); **optimistic 15** — the same size as the judge's noise of 1-2 obligations.

## 5. Where the steelman fails

- Everything hangs on discrimination. Stage H's rate index (maintainers raise 1 in 20 to 1 in 400 of flagged places) means even a discriminating engine meets a volume guard that cuts recall; a recall-only metric with a lenient judge rewards volume; the shuffled control is the only defence.
- Dev is too small to read A: an expected +1-3 at ±1-2 noise needs three reps and a second held-out set; one maintainer wrote 30 of dev's 52 comments.
- Selection is unsolved: the best ask-free selector is Opus at 0.67 for 25 picks; DeepSeek's is unmeasured; the 286 thin tail entries cannot be calibrated.
- Compute: even in the cheap form A is likely 10-30× a solo session; matched to that compute, more solo reps saturate, so A's case rests on reaching what the union never does — the nine dev obligations nothing reaches.
- The smaller classes stay small: execution-checkable conventions hold ~7% of census asks (read, dead-ends); D's ceiling 1-2 of 46; half of dev's residual is design and analogue asks no rule engine reaches.
- All design is in-sample on 14 probe PRs.
- Trained checkers: the deployed systems that reach high precision are trained on outcomes; with 1,833 census asks, a prompted A may top out below these estimates.
