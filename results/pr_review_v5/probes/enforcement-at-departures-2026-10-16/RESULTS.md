# Enforcement at departures: the result (2026-10-16)

`survival.py` over the 283 detector facts (`survival.jsonl`), read by PROTOCOL.md's rule. Two defects
were found and fixed before reading: the declaration pattern ended in `\b`, which never matches after a
trailing prime, so every primed name read as gone and then "fixed" (99% fixed, a false pass of the
validity check); and the name search fell back to the whole tree even when the merged file existed, so a
rename could read as survival through an unrelated declaration of the same leaf. After both fixes the
numbers below did not move between the second and third runs.

## Outcomes

283 facts: survived 184, fixed 13 (dotted 5, renamed 8), rewritten 7, gone 32, no merged commit in the
clone 44 (28 PRs), file gone 3. `fixed` is the dotted call or the renamed declaration present at merge;
"rewritten" and "gone" are reported apart, since a rewrite cannot be attributed.

| stratum | n | fixed | survived | rewritten or gone | unchecked | enforcement = fixed / (fixed + survived) |
|---|---|---|---|---|---|---|
| **dot notation** (P057 calls, P108 placement) | 182 | 7 | 114 | 26 | 35 | **0.06** |
| &nbsp; co-located with a round-1 ask | 100 | 5 | 47 | 22 | 26 | 0.10 |
| &nbsp; unasked, PRs with asks | 49 | 2 | 35 | 4 | 8 | 0.05 |
| &nbsp; unasked, control PRs | 33 | 0 | 32 | 0 | 1 | 0.00 |
| **primed names** (P113) | 101 | 6 | 70 | 13 | 12 | **0.08** |
| &nbsp; co-located with a round-1 ask | 45 | 6 | 26 | 8 | 5 | 0.19 |
| &nbsp; unasked, PRs with asks | 38 | 0 | 27 | 4 | 7 | 0.00 |
| &nbsp; unasked, control PRs | 18 | 0 | 17 | 1 | 0 | 0.00 |
| **pooled, unasked** | 138 | 2 | 111 | 9 | 16 | **0.02** (0.10 if every rewrite and removal were a fix) |

## Validity of the method (rule 1)

"Co-located" is the detector's `located_asks`: a round-1 ask on the same change target, mostly about
something else, so the protocol's 80% line is read on the facts whose ask is stated *exactly* (the
detector README's hand lists). Dot notation, 5 distinct facts: `d.count` rewritten (the fix, in another
form), `Infinite.of_accPt` renamed, `hs.eq_iInter_nat` and `hp.ne_zero` dotted, `A.toLin'` **survived**
(`Matrix.toLin' A x` is in the merged file). Primed names, 5 facts: `nontrivial'`, `ext'`,
`fourier_bilin_convolution_eq'`, `integral_countable'` renamed, `mk_of_mem'` gone. **8 fixed, 1 gone, 1
survived: 8 of 9 = 89%.** The method sees a fix when a maintainer asked for one. Spot checks: four
surviving primed names are declared at merge as the detector found them (`min_def'`,
`integral_interval_add_Ioi'`, `div_eq_iff'`, `iIndepFun_iff_charFunDual_pi'`); a surviving dot-notation
call is in the merged line (`PullbackCone.IsLimit.lift ht`).

## Reading (rule 2)

**Unasked departures are fixed at 2% (2 of 113), and at 0 of 49 on the control PRs; at most 10% if
every rewrite and removal were a fix.** Far under the 30% line, for both conventions. Where a
maintainer asked, the departure was fixed (8 of 9). So for these two conventions:

- the "5%" is not a swollen denominator of places that already conform: these are departures by the
  detector's shape, hand-validated 19 of 20 and 20 of 20 as stated, and 98% of the unasked ones reach
  merge unchanged;
- enforcement at these departures is the ask, and nothing else: no later round, no author
  self-correction, no CI fixes them when no one asked.

What it does not decide, and the second half (survivors read under each convention's motivation and
scope) will: whether the maintainers hold a narrower convention than our sentence, so that most of
these "departures" are not departures to them, or hold the convention and enforce it only where they
notice. The cases already in view point at the first for dot notation: the detector's shape fires on
data binders (`A : Matrix`, where `Matrix.toLin' A` is the ordinary spelling of a definition applied to
data), while the convention as maintainers state it is about applying a *lemma to a hypothesis*; and
for primed names Mathlib declares primed variants in their thousands, so the convention as held must be
narrower than "no prime beside a sibling". Either way, the sentence we wrote measures something
maintainers do not enforce at 90-98% of the places it fires, which is the construct gap the user named.

## Limits

Two conventions with a countable shape; 44 facts on 28 PRs have no merged commit in the clone (HEAD
2026-05-14). The store's "closed, not merged" does not separate them: Mathlib merges through bors, so
GitHub marks a merged PR closed (31709 reads unmerged in the store and its merge commit is in the clone).
16 PRs (22 facts) closed before the clone's HEAD with no merge commit in it, so they are probably unmerged;
12 PRs (22 facts) closed after it, merge state unknown here. Corrected 2026-10-16 from a first reading
that called all 28 unmerged; "co-located" asks are not asks about the fact; the exact-ask list is 10 facts; one run,
deterministic, re-runnable in 15 s.
