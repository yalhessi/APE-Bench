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

## Sample 2: outside the window (2024-03..2025-05 and 2026-04..2026-08)

Pending: tier-2 collection for 250 seeded pre-gate passes, then the same draw, packets and readers.
