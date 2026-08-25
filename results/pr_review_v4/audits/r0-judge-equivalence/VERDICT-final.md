# R0 final verdict: the gate was mis-specified; the migration is sound, with two caveats

*Round 3, 2026-08-05. 18 pairs, `gpt_5_mini`, `max_tokens=4000 / thinking_budget_tokens=3000`.
Complete coverage. Reports: `report-budgeted-rep{1,2,3}.json`.*

## The three rounds

| round | task-arm budget | coverage | issue agreement | split-vote pairs |
|---|---|---|---|---|
| 1 | unset (defaults 32000/30000) | 18/18 | 77.8% | 1 |
| 2 | 1200/512 (copied from script) | **14/18** | (85.7%, unusable) | 0 |
| 3 | **4000/3000** | 18/18 | **83.3%** | **4** |

Round 2 is void: it dropped 4 pairs, and they were the contested ones.

## The finding: the 95% gate is unachievable by any judge on this pair set

Round 3's three samples per pair let the judge's own per-pair distribution be estimated.
Using each pair's vote share as P(issue=True), the probability that **two independent
single draws of the same judge agree with each other** is:

| | |
|---|---|
| expected self-agreement of a single-sample judge vs itself | **90.1%** |
| observed script-vs-task agreement | 83.3% |
| **R0 gate as written** | **95.0%** |

So a judge compared against *itself* would be expected to fail this gate. The 95%
threshold silently assumed a deterministic judge; the judge is not deterministic, and R0
is the measurement that revealed it. **The gate, not the migration, is what failed.**

## Partitioning the pairs settles it

| pair class | pairs | judge self-agreement ceiling | script-vs-task agreement |
|---|---|---|---|
| deterministic | 12 | **100%** | **11/12 = 92%** |
| bimodal (2 obligations: `…4bfe0de1d5f6`, `…0898b0748443`) | 6 | ~50% | 4/6 = 67% |

On the 12 pairs where the judge is deterministic, the two arms agree on 11 — and the
single miss is diagnosable (below). The 6 remaining pairs sit on just two obligations
where the judge splits its own samples 2-of-3; pooled, **11 of 18 individual samples say
`issue=True` on them**, i.e. close to a coin flip.

The same two obligations were the round-1 disagreements and the round-2 hard failures.
Across three rounds and three configurations, the contested set is stable. That is the
signature of borderline *content*, not of a harness difference.

## The one non-bimodal disagreement is a task-arm error

`…e373aeb72a4b` (rep 2), task arm unanimous 3/3 in both round 1 and round 3:

- **Gold**: replace the manual `by_cases` proof of `coveringNumber_le_packingNumber` with
  the `by_cases!` pattern using `encard_maximalSeparatedSet` and
  `IsCover.coveringNumber_le_encard`.
- **Candidate**: rename `Metric.card_maximalSeparatedSet` to `…encard_…` — a naming ask
  about a *different declaration*.
- **Script** (`issue=False`): "the maintainer asked for a specific proof-style change …
  while the candidate only requests renaming".
- **Task** (`issue=True`): "the candidate correctly targets renaming … **but it does not
  perform the requested by_cases!/coveringNumber_le_encard proof transformation**".

The task arm's own stated reason contradicts its verdict. It appears to have anchored on
the incidental fact that gold's suggested proof text *mentions* `encard_maximalSeparatedSet`,
and treated a shared symbol as an issue match — precisely what the rubric's "sharing a
declaration … is not enough" clause forbids. The script is right here.

This matters more than a coin-flip pair, because it is **stable**: unanimous across three
samples and across two configurations, so majority voting cannot catch it.

## Verdict

**The migration is sound.** Nothing in three rounds indicates the task harness changes
verdicts. What R0 actually established:

1. The judge is **not deterministic**: ~11% of pairs (2 of 18) are genuinely bimodal.
   That is the noise floor every downstream comparison must be read against — at n=8
   obligation denominators it is roughly ±1 obligation, i.e. **±12pp**, which is larger
   than several deltas this project has previously discussed.
2. `sample_count=3` is a real improvement, because it **measures** that bimodality instead
   of hiding it inside a single draw. This is the migration's actual payoff, and it is
   what made the finding above visible at all.
3. The two arms are **not substitutable at a fixed token budget**: the script returns
   plain-text JSON, the task must emit a tool call, and the difference lands hardest on
   the pairs that need the most reasoning (round 2).
4. There is **one stable rubric-application error** in the task arm that voting will not
   fix.

## Actions

1. **Restate the R0 gate.** Replace "≥95% agreement over all pairs" with: (a) agreement on
   pairs the judge decides deterministically, threshold ≥95%; (b) an explicitly published
   bimodal set with its measured split rate; (c) zero unexplained coverage loss. Under
   that gate round 3 reads: (a) 92% — one diagnosable error, (b) 2 obligations at ~50%,
   (c) clean.
2. **Adopt the task arm for new measurements**, keeping the script arm frozen as the
   historical producer. Nothing already measured gets re-scored.
3. **Publish the noise floor.** ~11% bimodal pairs ⇒ ±1 obligation at n≈8. Every future
   comparison — routed-hybrid, generalized checkers, medium — must be read against it, and
   3 repetitions is a floor, not a luxury.
4. **Add both contested obligations and the `…e373aeb72a4b` error to the standing judge
   audit.** The bimodal ones test the rubric's "a different fix may still issue-match"
   clause; the error tests "sharing a declaration is not enough". A human ruling on all
   three would let the rubric be tightened where it is actually ambiguous.
5. **Do not tune the rubric from these three pairs alone.** n=18 on one PR; a rubric
   change should be pre-registered and validated against a wider audit sample.

## Standing lessons

- "Same judge" means prompt **and** decode parameters **and** model **and** submission
  protocol. Rounds 1 and 2 each violated a different one of those.
- An equivalence gate must be calibrated against the *self*-agreement of the thing being
  compared. A threshold above a judge's own reproducibility is unachievable by
  construction, and will be misread as a failure of whatever is being tested.
