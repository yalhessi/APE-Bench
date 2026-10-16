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

## The survivors read under the conventions as held (amendment 2; `readings/`, `score_reading.py`)

Two readers, independent, each on all 89 scored items (I090 dropped as a defective packet before
scoring): the 76 open survivors and 13 fixed departures as blind calibration. Both readers pass the
pre-registered calibration bar at exactly 9 of 13; agreement 85 of 89.

| convention | n | departure | excluded | invalid | contested | construct error (both agree) | rule's reading |
|---|---|---|---|---|---|---|---|
| placement in the predicate's namespace (P108) | 35 | 1 | 33-34 | 0 | 0-1 | **33 of 34 = 97%** | denominator ours |
| primed names (P113) | 25 | 4-6 | 19-21 | 0 | 0 | 19 of 23 = 83% | denominator ours, **but see below** |
| dot notation for a call (P057) | 16 | 12-13 | 0 | 3 | 0-1 | **3 of 15 = 20%** | enforcement where noticed |
| pooled | 76 | 17-20 | 52-54 | 3 | 0-2 | 55 of 72 = 76% | denominator ours |

Grounds for `excluded`, both readers: the lemma has a main hypothesis whose namespace the rule
prefers, so the detector's conclusion-namespace proposal is not what the convention asks (58); a
docstring explains the prime (17); a minor variant beside a primary sibling (15); other (17: mostly names
that already existed at base and were moved or given an attribute, which the detector reads as new; the
prime inherited from a function name such as `toLin'`). Invalid: the detector misparsed two calls
(`AlgEquiv.spectrum_eq Matrix.toLinAlgEquiv' A`; `Sieve.bind` taking a `Presieve`).

**Read by convention, not pooled; one finding is post hoc and says so.** The four calibration items the
readers labelled `excluded` are all primed names: of the 6 fixed primed names, both readers excluded 4
(I001 "docstring explains", I018 "an existing name, moved", I021 and I087 "a minor variant"), where
maintainers had in fact asked for the rename, including "you can remove the prime from the name of the
lemma above" on a lemma the PR was only moving. Placement passed its calibration (2 of 2) and dot
notation passed (5 of 5). So:

- **Placement (P108): the detector's construct was wrong.** It proposes the conclusion's namespace
  (`X.of_Y`) from the name and conclusion; the convention as held puts a lemma with a main hypothesis in
  that hypothesis's namespace, and the conclusion's namespace only when there is none. 97% of the
  unasked survivors are not departures from the convention as held. For this convention the low ask
  rate was ours.
- **Dot notation (P057): mostly real departures, unasked, merged.** 12-13 of 16 survivors depart from
  the convention as held; with the survival result (0 of 32 unasked calls fixed on control PRs) this
  convention is enforced where a maintainer notices, typically while rewriting a line (most asks under
  it are suggestion blocks that arrive with a golf). Its stated motivation is readability and
  compactness, not correctness.
- **Primed names (P113): not readable from this reading.** The written "as held" text permitted a
  prime beside a primary sibling and accepted a docstring as an explanation, and the readers followed it;
  the maintainers' actual line is stricter (they asked to unprime minor variants, documented ones and
  moved ones). The 83% is an upper bound on the construct error for primes, and the true convention is
  closer to "a new or touched primed name is renamed when a maintainer looks at it".

**Back to the question.** The "5% of applicable places" does not survive as a single number. For
placement it was our detector's sentence, broader than and partly contrary to the convention as held.
For dot notation it is real: departures from a readability convention pass to merge unless a maintainer
happens to rewrite the line. For primes our own written version of the convention was too permissive, so
the readers cannot settle it. What carries over to design: a convention has to be stated with its
precedence rules and the maintainers' actual line, read from their asks, and checked against what they
fixed; the one-line sentence and the detector's shape both misstate it.

Limits: two readers of one model family with the conventions as I wrote them; 76 items on 49 PRs; three
conventions with a countable shape; the calibration bar met exactly, and the per-convention calibration
split is post hoc.

## Primes, re-read with the convention re-derived (amendment 3; `score_primes.py`)

Two new readers on 31 items (the 25 open primes and the 6 fixed primes as blind calibration), with the
prime convention re-derived only from prime asks not on any calibration item.

| | reader C | reader D | both agree (27 of 31) |
|---|---|---|---|
| calibration: fixed primes labelled `departure` (bar 5 of 6) | **4** | **4** | |
| open primes: departure / excluded / contested | 10 / 14 / 1 | 14 / 11 / 0 | 10 / 11 / 0 |
| construct error | 58% | 44% | 52% |

**By the pre-registered rule, primes are not readable by this method:** the calibration failed again.
The two misses are the same for both readers: the moved lemma (`integral_countable'`, which the
amendment allowed to read either way, and the maintainer did ask to unprime) and `constantCoeff_subst'`,
excluded because the same file already uses `coeff_subst'` for the same difference; maintainers renamed it
anyway, so a file's own primed precedent did not license the prime for them.

What the two readings show together, without reading a number off either:
- the verdict moves with how the convention is written: the first version gave 83% construct error, the
  re-derived one 44-58%, and 6 of the 25 survivors flipped from "fine" to "departure" (4 were departures
  under both, 15 under neither);
- neither version reproduced what maintainers fixed; the asks hedge ("some Mathlib maintainers don't feel
  so fondly about primed theorem names"), and nine asks may be too few to fix the line. Whether primes are
  maintainer-dependent, or a rule that needs more asks to state, this reading cannot say.

**The method's own lesson.** Writing a convention from maintainers' words and checking it against what
they fixed caught a wrong statement twice, so the check works; producing a statement that passes it took
more than nine asks. For placement and dot notation, with more asks behind them, the first statement
passed its check.

## Corrections after the adversarial review (2026-10-16; `docs/plans/2026-10-16-principles-scope-currency/review2-departures.md`)

- **A defect in `survival.py`**: the tree-wide name search used Python regex syntax that `git grep -E` rejects, so
  it never matched. Fixed; 5 rows move toward survival (unasked fixed: 2 of 115, unchanged in substance);
  `scope.py` re-run (unasked survivors with a file practice: departure form 31 of 36). The tables above are the
  first run's and differ by these rows.
- **Placement**: 85-97% not departures, not 97%. 19 of 34 lemmas already sit in their main argument's namespace
  and 8 were not introduced by the PR; the one fixed case shaped like the contested exclusions (I044) went the
  detector's way, and its ask is quoted in `conventions_as_held.md`, so placement's blind calibration is one item.
  The direction (the detector's sentence is broader than the convention) stands.
- **Dot notation** stands. **Primes** stand as not readable. **Survival cannot tell** conforming code from an
  unasked departure; it says only that nothing but an ask changes these places.
