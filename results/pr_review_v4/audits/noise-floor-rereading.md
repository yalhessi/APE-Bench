# Re-reading existing results against the R0 noise floor

*2026-08-05, immediately after R0. No new runs — this applies a measured quantity to
results already on disk, and it changes which claims survive.*

## The measured quantity

R0 established that the judge (`gpt_5_mini`, `sample_count=3`) splits its own samples on
**2 of 18 pairs (~11%)**. At an obligation denominator of *n*, that is ≈ 0.11·*n*
obligations of pure judge noise, and a single flipped verdict moves recall by 1/*n*.

## Phase 9, re-read

Phase 9's matched scope is **n = 8**, so one flipped verdict is **12.5%** of recall and
the expected noise is ≈ 0.9 obligations.

| claim | delta | in obligations | survives? |
|---|---|---|---|
| mean issue recall | 0.0pp (tie) | 0.00 | no claim was made |
| mean resolution recall | +8.3pp | **0.67** | **within the noise floor** |
| paired-candidate precision | +27.2pp | 2.4 flips on a 9-candidate denominator | probably, but not comfortably |
| control candidates | 0 vs 2 per rep | — | **yes — a raw count, never judged** |
| identical accepted opportunity IDs 3/3 | — | — | **yes — artifact-level, never judged** |
| cost (~35% cheaper) | — | — | **yes — measured, never judged** |

**The resolution-recall advantage is not supportable at n = 8.** 0.67 obligations sits
below a single flip and well below the ~0.9 expected from bimodality alone. The Phase 9
verdict already declined to claim an issue-recall gain; the resolution-recall line should
now be demoted the same way.

Precision is more robust — 2.4 flips' worth — but on a 9-candidate denominator where one
flip is 11pp, it is a directional finding rather than a measured effect size.

## What this does *not* touch

The Phase 9 conclusions that carried the most weight were never judged quantities:

- **Reproducibility**: identical accepted opportunity IDs in 3/3 repetitions, compared at
  the artifact-hash level.
- **Control safety**: 0 vs 2 candidates on the control PR — a count of emissions.
- **Cost**: ~35% cheaper on positive scope.
- **Coverage**: the C0–C2 census is fully deterministic; no judge is involved anywhere in
  it, so `static_reachability_rejected` and C2 = 5/40 are immune to this entirely.

That the durable findings are exactly the judge-free ones is not a coincidence, and it is
the most useful planning input R0 produced.

## Planning consequence: several roadmap results are mis-sized

The roadmap specifies R2, R3, and R4 on **tier-small** (3 PRs, ~6–8 obligations) with
recall-based gates:

| result | gate as written | at n ≈ 8 |
|---|---|---|
| R3 checker-as-tool ablation | "precision ≥ 61.7%" | one flip = 11pp on a ~9-candidate arm |
| R4 routed hybrid | "routed recall ≥ max(arm recalls) and ≥ union − 1" | one flip = 12.5pp; the gate's tolerance *is* the noise |

Both would be measuring judge noise as often as treatment effect. They need one of:

1. **A larger denominator.** Medium has 40 included obligations — one flip is 2.5pp, and
   expected bimodal noise ~4.4 obligations. But medium is pre-registered-only and the
   census already spent one look.
2. **Noise-immune endpoints.** Control-candidate counts, candidate volume, reproducibility
   of accepted opportunities, cost per candidate, and C2 coverage are all judge-free and
   measurable at tier-small today.
3. **More repetitions,** which shrinks the mean's standard error but not the per-pair
   bimodality — it makes the *mean* stabler without making a 0.67-obligation difference
   real.

Option 2 is the cheap and honest one, and it is what Phase 9 already demonstrated by
accident.

## Recommended re-scoping

- Keep tier-small for **mechanism** questions with judge-free endpoints (does routing
  partition cleanly? does exposing checkers as tools change candidate volume or control
  pressure? do accepted opportunities stay reproducible?).
- Move **recall/precision effect-size** questions to a denominator where a flip is small,
  and pre-register them.
- Report every recall figure at n < 20 with its one-flip increment stated inline (e.g.
  "33.3% (±12.5pp per flipped verdict, n = 8)"), so no reader mistakes a sub-flip
  difference for a result.
- Prefer **C2 / coverage** as the decision variable wherever a decision can be framed on
  it, because it is deterministic. This is the strongest argument for making checker
  generalization the next build: the gate it feeds cannot be corrupted by judge noise.
