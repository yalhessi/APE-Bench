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

## The scope check (amendment 1; `scope.py`, `scope.jsonl`)

Each surviving or fixed departure's own file at the PR's base commit: does the file already use the
departure form (2 or more, at least as many as the convention form), the convention form, or neither?

| stratum | n | file uses the departure form | file uses the convention form | no practice | new file |
|---|---|---|---|---|---|
| dot notation, survived unasked | 67 | 10 (67%) | 5 (33%) | 41 | 11 |
| dot notation, survived, co-located with an ask | 47 | 2 | 8 (80%) | 19 | 18 |
| dot notation, fixed | 7 | 0 | 0 | 6 | 1 |
| primed names, survived unasked | 44 | 19 | 0 | 20 | 5 |
| primed names, survived, co-located | 26 | 2 | 0 | 11 | 13 |
| primed names, fixed | 6 | 2 | 0 | 2 | 2 |
| **pooled, survived unasked** | 111 | **29 (85%)** | **5 (15%)** | 61 | 16 |

**By the pre-registered rule, survival is explained by scope** (85% ≥ 60%), and the reading stops at
that altitude because the ground is thin:
- **Only 34 of 111 unasked survivors (31%) have a measurable file practice.** For the other 77 the file
  says nothing (no prior uses either way, or the file is new); scope as measured here explains nothing
  about them. Their directories, for the new files: 14 departure, 2 convention, 31 none.
- **For primed names the measure can only find the departure form** (the convention form, naming the
  differing term, is not countable), and the two *fixed* primed names sit in files full of primes too. So
  for primes the file practice does not separate what maintainers fixed from what they let through.
- **For dot notation the contrast is empty** (the 7 fixed calls have no measurable file practice), and 3
  of the 5 "convention form" survivors spot-checked are the detector's known invalid case
  (`PullbackCone.IsLimit.lift ht`, where `ht.lift` is a different, general lemma), so the file's dotted
  uses count another lemma.
- Library-wide, the surviving dot-notation calls' own spelling is rare: a median of 1 other undotted use
  of the same `Prefix.lemma` in all of Mathlib at base, 0 for 19 of 42.

**What it says, provisionally.** Where the file has a practice, the PR nearly always matches it, which
is what the user's picture predicts (the PR instantiates the convention as its scope does, and a
maintainer does not ask). But two thirds of the unasked survivors have no local practice to follow, and
for them this check is silent. Reading those (77) under each convention's stated motivation and scope
decides between "our sentence is broader than the convention" and "a departure nobody noticed".
