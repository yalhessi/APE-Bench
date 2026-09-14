# Selection signal — the absolute-threshold form is refuted; only the relative form is open

**Status** — mostly closed, and closed *against* the direction
`docs/plans/2026-09-14-selection-over-coverage.md` proposed. Kept here so the next session does not
re-derive it a fourth time.
**Cost** — no spend was needed to settle it, and no spend should be committed to it

## What was proposed, and what the data says

On `pr5_F_fanout_forced_stage1_rep1` a confidence threshold looked like a frontier: no cut → 179
candidates / 7 gold hits / 36 control findings; ≥0.4 → 89/5/9; ≥0.6 → 67/5/3; ≥0.8 → 14/3/1. That
table reproduces exactly under a principled id-based join (`findings.sources[0].candidate_id`, a
verified bijection here because coordinator merge is switched off). It does not survive four checks:

- **At 10× the data it is chance.** Three 12-PR lead reps, 907 candidates, 71 hit-candidates:
  within-PR AUC **0.486 / 0.485 / 0.516**; a ≥0.8 cut keeps ~50% of candidates and ~55% of hits, the
  base rate. At obligation level recall goes 7,5,6 of 23 down to 4,3,3. PR 33149 alone supplies ~69%
  of the candidates and its within-PR AUC is 0.487/0.484/0.515.
- **The forced-run separation is one PR.** Per-PR AUC: 33145 **0.914**, 33337 0.580, 33421 **0.208**
  (its only hit sits at conf 0.30, rank 57 of 73), 33315 no hits. Drop 33145 and the pooled AUC goes
  0.749 → **0.511**. 33145's confidence distribution is itself shifted up (median 0.715 vs 0.34–0.48),
  so "high confidence" and "gold hit" co-occur mostly as properties of that one PR.
- **Three of the seven hits are 2-of-3 judge majorities, all on 33145.** Under unanimity the hit set
  is four candidates, AUC 0.586, and a ≥0.4 cut keeps 50% of candidates for 50% of hits — no
  enrichment. Two of the five recovered obligations rest entirely on split votes: 5/10 recall becomes
  3/10 if both flip.
- **The unforced run of the same four PRs does not replicate it** — pooled AUC 0.351, within-PR
  0.468, and a ≥0.8 cut deletes both hits. (With 2 positives this is "does not replicate", not
  "refutes": one label flip moves that AUC by ~0.2.)

## This is prior art, with one important qualification

`docs/research/phase-c-corrected-history.md:45-46` already records it, in a single sentence whose
halves point opposite ways:

> Within-PR relative confidence ranking works (top-3 keeps ~67–72% of issue coverage) **even though
> absolute confidence thresholds were uninformative**.

The 179/89/67/14 table is the *absolute* form, and that form is closed. The **relative within-PR
top-k form is not closed** and measures 0.49 here — running that comparison explicitly, on runs
already paid for, is the only part of this thread worth any further time. `merge.py:256` and
`digest.py:145` say "falsified three times" with no citation; the three are
`phase-c-corrected-history.md:45-46`, `pr-review-v5-principled-design.md:58` (precision flat 9%→12%
across thresholds), and `pr-review-v4-evidence-pipeline-design.md:768`.

## What is still worth doing here

1. **Nothing that costs money.** The out-of-sample run the plan scheduled at $35–60 is not needed:
   the answer is already on disk, three reps deep.
2. **Test the relative form** (within-PR top-k) against the absolute one on the six committed
   held-out runs, and report both.
3. **Other signals in the same files beat it** — candidate-level AUC over the 907: `severity=blocking`
   **0.601**, `model_confidence` 0.538, `evidence_tier=verified_compile` 0.495, `admission=published`
   0.483. Per family, confidence is *below* chance where the hits are (correctness 0.441, duplication
   0.192, scope 0.213, naming 0.308). And control suppression at 12-PR scale is entirely a family
   effect: **11 of 12 control-PR candidates are `documentation`**; `style` is 0 hits in 348
   candidates, 38% of all volume. **Caveat that must travel with those numbers:** the drop set
   `{style, generalization, documentation}` was chosen by reading the hit table on the same 907
   candidates it is then scored on. It is in-sample, and the margin is 2 obligations per rep.
4. **Find out why `model_confidence` is null on all 126 solo candidates** while populated on all 907
   lead ones. Solo is the condition that already emits **0 control findings at ~1/17 the cost**, so
   it is the condition where a selection signal would actually matter.

## Corrections to the plan document and commit `5691ade`

- The stated spread "0.22–0.90" is wrong: the artifact range is **0.12–0.92** (median 0.38).
- `rejected_alternatives` is **not** a serialization drop with content behind it. Across all 54 runs
  with `arm_responses.jsonl`, 1,151 candidates predate the field and 1,528 carry it — of which **2
  are non-empty**. The drop at `candidates.py:374` is real; there is essentially nothing being lost,
  and the arms are not populating it. A pinning test would pass on an always-empty list.
- The "fifth instance of the serialization-drop bug" framing does not hold for that field.
- "Selection, not coverage" as a framing is **already stated as a rule** in
  `pr-review-v5-principled-design.md:47-51`: coverage is the dominant wall for one run, and only
  after flooding does selection dominate. On the held-out 12 the two losses are within one
  obligation of each other in every rep (location 0.652/0.609/0.609 against issue
  0.304/0.217/0.261). Only the forced fanout — 179 candidates on 4 PRs, produced by refusing
  abstentions — shows location 1.0 against issue 0.5. Quote the regime with the framing, every time.
