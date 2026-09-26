# Does the comparison-design problem generalise? (results)

Two blind readers per batch, every comment labelled; `results.json` holds every count. The
question (user, 2026-09-26): is this a problem that matters in PRs outside our immediate focus,
enough to invest in retrieval?

## Sample 1: same window, PRs in no set (2026-09-26)

300 tier-2 PRs outside every evaluation and development set, seeded walk, 967 round-1 comments,
60 reviewers, 6 AI-authored PRs (7 comments). Months are mostly 2025-12 and 2026-01, where the
store's tier-2 coverage outside the sets lies.

| | this sample | validation reading (`design-comparison-val1000-v1`) |
|---|---|---|
| stage-1 agreement | kappa 0.91 on the seven-way label, 0.94 coarse | (facet readers: 0.86-0.95) |
| asks (agreed, not `not_an_ask`) | 801 | 506 |
| design asks | 194 = **24.2%** (CI 21.4-27.3) | 95 + 26 generality = 24% |
| comparison asks (library or siblings) | 73 = **9.1%** (CI 7.3-11.3); 87 by either reader, 10.7% | 43 = **8.5%** |
| PRs carrying a comparison ask | 49 of 300 | |
| analogue named or implied (agreed) | 65 of 73 | 43 of 43 |
| findable by (agreed; kappa 0.79) | PR siblings 21, API shape 20, name 8, role 6, neighbourhood 6 | API shape 13, siblings 5, role 3, name 3 (kappa 0.37) |
| wrong analogue plausible | **12 agreed, 20 by either** of 73 (kappa 0.71) | 2 agreed, 7 by either of 43 |

**The rate replicates.** On fresh PRs and reviewers the comparison-design share is the same
number as on the validation set, within its interval, and one PR in six carries such an ask.
Design asks as a whole are a quarter of round-1 asks in both. With 7 comments on AI PRs, nothing
can be said about AI authorship from this sample.

**The decoys are the analogue's twins, not random lookalikes.** All 12 agreed decoys sit one axis
away from the right object:
- direction: `Antitone` against `Monotone`;
- dual or side: `compCoyonedaSectionsEquiv` against `compYonedaSectionsEquiv`, `Fork.ofι` against
  `Cofork.ofπ`, `Multifork.ofι` in the same file;
- strength: `IsEmbedding` against `IsInducing`; `HasSum` against `Summable`/`tsum`;
- bundling: the `IsSymm` class against the `Symmetric` predicate;
- carrier: `Pi.single` against `Finsupp.single` and `Matrix.one`;
- continuity: `ContinuousLinearEquiv.arrowCongr` against `LinearEquiv.arrowCongr`;
- role neighbours: `Basis.coord` against `Basis.dualBasis`, `toDual`, `repr`; `QuotientGroup.lift`
  against `QuotientGroup.map`.

So the risk the user named is structured: a retrieval that returns one best match will be wrong
along one of these axes in a sixth to a quarter of cases, and the axis is usually decidable
mechanically (the carrier's type, continuity, the direction of an inequality, the side of a
limit). The retrieval should return the analogue's family along these axes and let a typed check
or the reviewer discriminate, rather than commit to a single sibling.

**What is findable.** Unlike the validation reading, the PR's own siblings are the largest class
here (21 of 73): a missing twin, an inconsistency between two of the PR's declarations, a
duplicated proof. Those need no library retrieval at all; they need the PR read as a whole. API
shape is the next (20), then name, role and neighbourhood.

## Sample 2: outside the window (2024-05..2025-05 and 2026-04..2026-08)

250 seeded pre-gate passes collected at tier 2 (150 early, 100 late); 129 had round-1 feedback:
349 comments, 53 reviewers, 7 AI-authored PRs (10 comments).

| | this sample | early 2024-05..2025-05 | late 2026-04..2026-08 |
|---|---|---|---|
| stage-1 agreement | kappa 0.95 | | |
| asks (agreed) | 269 | 139 | 130 |
| design asks | 62 = **23.0%** (CI 18.4-28.4) | | |
| comparison asks | 26 = **9.7%** (CI 6.7-13.8); 30 by either, 11.0% | 18 = 12.9% (CI 8.4-19.5) | 8 = 6.2% (CI 3.2-11.7) |
| PRs carrying one | 23 of 129 | | |
| findable by (agreed; kappa 0.75) | PR siblings 8, API shape 5, neighbourhood 4, role 3, name 1 | | |
| wrong analogue plausible | **6 agreed, 8 by either** of 26 (kappa 0.90) | | |

The six agreed decoys are again the analogue's twins: carrier (`Real`/`NNReal`/`ENNReal.IsConjExponent`;
`signHom.mrange` against `castHom.mrange`), direction (`Submodule.comap` against `map`), strength
(`Algebra.botEquiv` against `botEquivOfInjective`), scope neighbours (the other scoped matrix norms),
idiom against instance (`ConnectedComponent.supp` against its `SetLike` membership).

## Verdict: the problem generalises

| sample | PRs | reviewers | asks | design | comparison asks | decoy plausible (agreed) |
|---|---|---|---|---|---|---|
| validation reading (2025-06..2026-03) | 973 (506-ask sample) | 80 | 506 | 24% | **8.5%** | 2 of 43 |
| same window, PRs in no set | 300 | 60 | 801 | 24.2% | **9.1%** (7.3-11.3) | 12 of 73 |
| outside the window, 2024-05..2026-08 | 129 | 53 | 269 | 23.0% | **9.7%** (6.7-13.8) | 6 of 26 |

- **Prevalence is stable**: one round-1 ask in eleven compares the PR against something that
  already exists, on one PR in six, across 2024-05..2026-08, three disjoint PR pools and three
  reviewer populations, with stage-1 kappa 0.91-0.95. Design asks as a whole are a quarter of
  round-1 asks in every sample. The late-2026 period is lower (6.2%) with a wide interval and 130
  asks; it does not contradict the others and is worth watching as AI-authored PRs grow.
- **AI authorship cannot be read from these samples**: 17 comments on 13 AI PRs in all.
- **The wrong-sibling risk is structural and larger than the first reading showed**: 18 agreed
  decoys of 99 comparison asks across the two new samples (18%), every one a twin of the right
  object along a single axis. Retrieval must return the family along those axes and discriminate
  by a typed check or the reviewer; a single best match is wrong about a fifth of the time.
- **What retrieval must cover**: over the 99 new comparison asks (agreed), the PR's own siblings
  29, API shape 25, name 9, role 9, neighbourhood 10. The siblings class needs no library
  retrieval, only the PR read as a whole; API shape is the mechanisable library class; role and
  neighbourhood are the remainder.

So the investment question is answered on prevalence: this is a general, stable tenth of what
maintainers ask for, and the pipeline has never hit it. What is not yet shown is that the
retrieval can be built to the guard's standard; that is the next step in
`docs/todo/review-design-comparison.md`.
