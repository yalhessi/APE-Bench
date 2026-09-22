# The binding constraint is publication, not abstention (2026-09-22)

Written after the gold-site silence read (`specialist-silences-2026-09.md`) said that most
specialist silence is correct, which left the original question open: the system still misses most
of what maintainers ask for, so where does it go missing? Answer: mostly not at the arms. The run
already finds several times more of the gold than it ever publishes, and the stage that drops the
difference filters on an axis close to orthogonal to whether the ask is right.

Everything here is a re-scoring of three committed held-out repetitions. Nothing was run and nothing
was spent.

## The measurement

`report buckets --audit` now carries a `gate` block, per repetition:

| | rep1 | rep2 | rep3 |
|---|---|---|---|
| gold obligations hit by some finding | 7 | 5 | 6 |
| of those, hit by a **published** finding | **2** | **1** | **1** |
| findings | 285 | 318 | 304 |
| published | 25 | 28 | 27 |
| findings on a control PR | 3 | 4 | 5 |
| of those, published | **0** | **0** | **0** |

Counting distinct obligations rather than per-repetition hits: of the 22 counted obligations, **7
are found at least once across the three repetitions and 2 reach publication.**

The reason is one reason. Of rep1's 24 suppressed hit-findings, 21 carry
`no collector can support this claim's concern family`. That is a statement about a *kind* of claim,
not about the claim, and it is the gate working exactly as designed: `finalize` publishes what a
deterministic collector can warrant, and keeps the rest as `diagnostic` with no channel so the
system never claims credit for something it did not say.

## The inversion

Pooled over the three repetitions, by the concern family the finding declares:

| family | findings | gold hits | published | on control PRs |
|---|---|---|---|---|
| correctness | 161 | **39** | 2 | 0 |
| duplication | 112 | 11 | 44 | 0 |
| naming | 66 | **10** | **0** | 0 |
| scope | 87 | 6 | **0** | 0 |
| proof-golf | 41 | 3 | 25 | 0 |
| documentation | 77 | 2 | 3 | **11** |
| style | 348 | **0** | 0 | 1 |
| generalization | 15 | **0** | 6 | 0 |

The families that hit are not the families that publish. `correctness` finds 39 of the 71 hits and
publishes 2 of 161; `generalization` has never hit anything and publishes 40% of what it files.
By producing arm it is starker: the **generalist accounts for 64 of the 71 hits and is published
2.8% of the time**, while five specialist arms publish 86–100% of what they file and contribute 4
hits between them.

`style` deserves its own line. It is **348 findings, 38% of all output, and zero gold hits** across
three repetitions. Whatever the over-abstention problem is, it is not a shortage of `style` volume.

## What a different rule would do, tested out of sample

The obvious objection to opening the gate is precision, and the project measures precision by
emission on control pull requests, where maintainers asked for nothing. That objection is
answerable here, because **all 12 control findings across the three repetitions are `documentation`
(11) and `style` (1)** — the two families that also never hit.

Leave-one-pull-request-out, admitting a family only if, on the *other* eleven pull requests, it hit
at least once and emitted nothing on a control:

| | obligations published | findings published | control emission |
|---|---|---|---|
| the gate as it stands | **2** of 7 | 80 | 0 |
| the out-of-sample family rule | **6** of 7 | 241 | **0** |

Three times the obligations, three times the volume, and the control property intact. The admitted
set is stable across folds: `correctness`, `duplication`, `naming`, and usually `proof-golf` and
`scope`.

## What this does and does not establish

- **It does not say the gate is wrong.** The gate buys a real property and the write-ups that quote
  zero control emission are quoting it. It says the gate's axis — can a collector warrant this kind
  of claim — is close to orthogonal to the axis that matters, and that a family rule chosen out of
  sample dominates it on both measured axes at this scale.
- **Volume is the unmeasured cost.** 241 published against 80 means a maintainer reads three times
  more, and roughly 90% of it is off-gold and unadjudicated, so "dominates" holds on the two axes
  this project measures and on no others. `docs/todo/adjudication-rubric.md` is the blocker and the
  store is empty.
- **Small denominators.** 7 obligations found, 2 control pull requests, 3 repetitions, one release,
  one model. The control property rests on 6 control-PR-repetitions.
- **The judge splits its own vote**, and the 7 pre-gate hits are majority verdicts. Re-judging the
  same artifacts under unanimity is free and has not been done.
- **This is a re-scoring, not a run.** It says what the recorded findings would have done under a
  different rule. It does not say what a run would produce if the arms knew the rule had changed.

## What it means for over-abstention

The framing this thread started with — the specialists abstain too much, so change what they are
told — is aimed at the smaller of two losses. The arms abstain on roughly 75% of specialist
invocations, and the gold-site read found most of that silence to be correct. Meanwhile the output
they *do* produce reaches a maintainer about one time in eleven, and the obligations it covers drop
from 7 to 2 on the way.

So the order of work inverts. Fix the publication rule first, on data already paid for, then ask
whether the arms need to say more. Forcing the arms to speak, the one intervention measured here,
bought its recall by raising volume 49 to 179 and control emission 1 to 36 — while this costs
nothing and keeps control emission at zero.

## Evidence

- `cli report buckets --run <run> --audit`, the `gate` block; `src/mathlib_review/analysis/report.py`.
- Runs `pr5_A_lead_heldout12_v2_rep{1,2,3}` and their audits; release `dev-medium-0.3.0`.
- The admission logic: `src/mathlib_review/review/finalize.py` (`_unwarranted_findings`,
  `checkable_arms`), `src/ape/tasks/lean_tasks/formal_math/review/candidates.py`
  (`CHECKABLE_CONCERN_FAMILIES`).
- Prior record this corrects or picks up: `docs/dead-ends.md` "Specialists as the coverage floor";
  `docs/todo/selection-signal.md`; `docs/todo/specialist-arm-contents.md` (`style` publishes nothing,
  recorded there as an arm property rather than as 38% of total volume).
