# The convention census: how many principles generate what maintainers ask for (results)

*Pre-registered 2026-09-29 (`reader_rubric_census_v1.md`, commit `30a0a22`); val1000 read
2026-09-29 to 2026-10-03; the held-out reading **paused 2026-10-04** at the point in §6.
`results.json` holds every count; `analyse.py --write` regenerates it.*

**The question** (`docs/todo/conventions-nature.md`, study 1). We kept assuming Mathlib's
conventions can be written down, and nothing measured how many there are. Two blind readers each
wrote the principle behind every round-1 maintainer ask on 973 validation PRs, in one seeded random
order, keeping a running codebook, so that the accumulation curve says whether review is a hundred
conventions or a thousand, and how much of it is one-off. The outside samples (300 fresh PRs in the
same window, 129 PRs from 2024-05..2025-05 and 2026-04..2026-08) are then read against the finished
codebook as the held-out saturation test.

## The instrument

- **Unit:** an agreed round-1 ask. val1000: 1,833 (both arm-coverage readers said `ask`). Held-out:
  801 same-window and 269 other-years asks (both stage-1 readers said anything but `not_an_ask`).
- **Order:** sha256 of a seed and the cid; batches of 125 (`order.json`).
- **Readers:** two blind Claude subagents, one fresh run per batch, each keeping its own codebook and
  never seeing the other's; the exact text each run received is `reader_instructions.md`. A
  principle is one general sentence, situation then preferred form, such that a reviewer holding it
  would make this ask on a different PR; an ask that is a fact about this PR alone gets `none`.
  Readers may broaden their own entries, never merge, split or delete them. Entries carry a
  rationale (eleven values) and a form (`rule`: checkable given the situation; `standard`: needs
  judgment).
- **Validation:** `provenance/check_batch.py` after every batch (every cid once and in order, ids
  consecutive and resolvable, `none_reason` consistent, the committed codebook a prefix of the
  working one). Three runs were killed by session limits: b01 (both readers, restarted from the
  committed b00 state), b05 (both, after writing both files; the validator passed them and they
  stand), b11 (B, before its codebook write; discarded and rerun).
- **Cross-map:** a third blind reader matched the two val1000-complete codebooks from sentences
  alone (`crossmap_rubric.md`, `crossmap.json`).

## 1. The count: 409 and 407 principles over 1,833 asks, and the curve has not flattened

New entries per batch of 125 asks (b14 has 83):

| batch | b00 | b01 | b02 | b03 | b04 | b05 | b06 | b07 | b08 | b09 | b10 | b11 | b12 | b13 | b14 | total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A new | 91 | 45 | 32 | 33 | 36 | 22 | 26 | 19 | 19 | 12 | 21 | 21 | 12 | 12 | 8 | **409** |
| B new | 92 | 44 | 39 | 31 | 30 | 23 | 23 | 15 | 20 | 18 | 20 | 21 | 10 | 12 | 9 | **407** |

Two readers who never saw each other's work end two entries apart, and coincided in size four
times along the way (91/92, 136/136, 259/259, 335/335).

**Saturation, as pre-registered.** The last three batches (333 asks) added 32 entries for A and
31 for B: **7.8% and 7.6% of the codebook, against the 5% rule. Not saturated, by both readers,
by the same margin.** The Good-Turing estimate (entries with exactly one ask, over asks with a
principle) puts the probability that the next ask needs a new entry at **0.099 (A) and 0.107
(B)**: at the end of 1,833 asks, about one ask in ten still brings a principle the census does not
hold. The curve is linear at roughly 10 to 12 new principles per 125 asks over the last four
batches, not decaying.

So the honest count is a lower bound: review on this corpus draws on **about 400 principles after
1,833 asks, and the number is still rising at about one per ten asks.** Not a hundred; not yet a
thousand; and the held-out test (§6) says whether other PRs, reviewers and years push it further.

## 2. Concentration: a familiar head and a long tail

| | A | B |
|---|---|---|
| asks with a principle | 1,669 | 1,685 |
| asks with none (`specific` / `unreadable`) | 164 (128 / 36), 8.9% | 148 (117 / 31), 8.1% |
| share of principled asks under the top 10 entries | 22.0% | 21.8% |
| under the top 25 | 39.1% | 37.9% |
| under the top 50 | 54.6% | 54.5% |
| entries with exactly one ask | 166 of 409 | 180 of 407 |
| entries with ten or more asks | 49 | |

Half of what maintainers ask for falls under about forty principles; the other half spreads over
roughly 370, two fifths of which were invoked once. The head is the part the project already knew
by name (§5); the tail is where the design-comparison reading's "written nowhere" lives.

**By family (reader A; principled asks by primary id):**

| family | asks | entries | singletons | top entry | top 5 |
|---|---|---|---|---|---|
| F1 proof | 406 | 89 | 40 | 14% | 41% |
| F6 statement and API design | 264 | 92 | 47 | 9% | 34% |
| F9 formatting | 220 | 65 | 37 | 13% | 39% |
| F8 naming | 169 | 36 | 16 | 32% | 63% |
| F10 documentation | 155 | 64 | 32 | 7% | 28% |
| F12 PR level | 122 | 38 | 19 | 16% | 48% |
| F3 registration | 80 | 28 | 15 | 30% | 55% |
| F5 redundancy | 80 | 25 | 13 | 20% | 61% |
| F7 generality | 70 | 14 | 9 | 33% | 87% |
| F2 interface | 61 | 24 | 14 | 16% | 59% |
| F4 derive, don't restate | 19 | 8 | 4 | 47% | 84% |
| F11 meta-code | 15 | 12 | 9 | 13% | 53% |

(B's entry counts per family are within a few of A's: F1 86, F6 93, F9 62, F10 67, F8 41, F12 45.)
Generality and naming are concentrated: five principles carry 87% and 63% of their asks. Statement
and API design and documentation are diffuse: five principles carry a third or less, and F6 has as
many entries as F1 on two thirds of the asks. That is the measured form of the todo's intuition:
the design taste is where the principles multiply. F10's `none` share is the highest (75 of 230
asks for A) because typos and wording fixes are facts about the text, not principles.

## 3. Rationale and form

Entries' rationales weighted by the asks assigned to them (an entry may carry two):

| rationale | A | B |
|---|---|---|
| readability | 488 | 579 |
| consistency | 475 | 446 |
| compactness | 466 | 497 |
| discoverability | 427 | 401 |
| maintainability | 416 | 354 |
| generality | 133 | 130 |
| process | 128 | 128 |
| automation | 121 | 126 |
| performance | 63 | 59 |
| correctness | 34 | 44 |
| mathematics | 35 | 17 |

Five rationales carry the bulk and in the same order for both readers; generality, process and
automation are each about a quarter of any of them. **Form splits evenly: rule 841 / standard 828
(A), 833 / 852 (B).** Half of what is asked for is checkable given the situation; half takes
judgment in application. The split is not the family split: F1 holds both "a `refine` that leaves
no goals is `exact`" (rule) and "a long proof is split" (standard).

## 4. Agreement

**Without any mapping** (labels only, val1000): the readers agree on none-versus-some for **97.9%**
of asks. Of the 1,658 asks both gave a principle, two asks placed under one principle by A are
under one principle for B with probability **0.608**, and conversely **0.639**; adjusted Rand
index **0.62**. 384 of A's 396 used entries have one B entry covering at least half their asks, 280
all of them; of the 152 A entries with three or more asks, 140.

**With the pre-registered cross-map** (third blind reader, sentences only): **420 pairs**, 312
`same`, 49 `a_broader`, 59 `b_broader`; **377 of A's 409 and 377 of B's 407 entries matched.** The
two readers' ids form a recorded pair for **1,483 of 1,833 asks: agreement share 0.809**
(none/none counted as agreement). Checked against the co-assignments the third reader never saw:
403 of 420 pairs have at least one ask both readers put under them, and 134 of the 140 strong
co-assignments were recorded; the six missed are grain near-misses (a squeezed-`simp` rule against
its converse; grouping beside placement). The third reader's own note names the systematic
difficulty: B folded several layout and scoping rules into single entries where A kept them apart.

The caveat that bounds all of this: one model family read both sides and did the matching, so the
agreement is an upper bound on what two independent humans would show.

## 5. What the head of the census looks like (reader A, asks assigned)

| asks | id | form | the principle |
|---|---|---|---|
| 60 | P005 | standard | a goal that a standard finishing tactic closes is closed by that tactic, not by a hand-written term or rewrite chain |
| 57 | P019 | rule | a lemma's name is built from the names of every declaration in its statement, spelled as they spell them |
| 48 | P011 | standard | a result that existing library lemmas or API yield directly is derived from them, not reproved |
| 42 | P004 | standard | the general core of a specific result is extracted as its own declaration about the general construction |
| 40 | P007 | standard | an expression that matches a library-named predicate or function is written with that name, not its unfolding |
| 40 | P018 | standard | consecutive tactic calls that a single call can perform are merged |
| 37 | P017 | rule | syntax that elaboration supplies on its own (coercions, ascriptions, redundant parentheses) is omitted |
| 33 | P059 | rule | punctuation, operators and application carry the standard spacing |
| 32 | P003 | standard | a lemma rewriting a canonical application to a simpler right-hand side is tagged `@[simp]` |
| 29 | P057 | rule | a namespaced function applied to a term of that type is written with dot notation |
| 27 | P063 | standard | a result stated for a concrete type but using only an abstract property is stated for every type with that property |
| 27 | P074 | standard | material off a file's topic, or adding heavy imports, goes where it belongs |
| 24 | P119 | rule | a step or hypothesis the proof does not need is removed |
| 23 | P013 | standard | a `have` whose proof is a short term is inlined |
| 23 | P043 | standard | a PR is cut at its natural seams |

Every one of these is a convention the project could already name. The census's contribution is
the other 390 and their weight: 1,669 principled asks, of which the fifteen above account for 542.

**A conflict datum for study 3**, flagged by reader A in b01 and visible in the cross-map's misses:
one maintainer asks that a `simp` feeding a finisher be squeezed to `simp only` (A's P133, stated
explicitly in the comment), another that it be left unsqueezed before a flexible finisher (A's
P014, 19 asks). Both readers kept them as separate entries; the census records that two
maintainers hold opposite rules on one situation.

## 6. The held-out test (paused 2026-10-04)

Rule, fixed before any label: entries created over the 1,070 outside asks, as a share of the
val1000 codebook; **saturated at or under 10% (41 entries for A), not saturated at or over 25%
(102)**, ambiguous between. Order of reading: the other-years sample (y00..y02, 269 asks) first,
then the same-window sample (w00..w06, 801 asks); the rubric fixes the thresholds and the 1,070
asks, not the order between the two samples, and the smaller era-spanning sample first makes a
budget-forced stop cleaner. The total is the same if everything is read.

| held-out batch | A new | A cumulative | B new | B cumulative |
|---|---|---|---|---|
| y00 (125) | 14 | 14 | not read | |
| y01 (125) | 11 | 25 | not read | |
| y02 (19) | 4 | 29 | not read | |

**Where it stopped.** Reader A read the whole other-years sample (269 asks) and added **29 entries,
7.1% of its val1000 codebook**; reader B read none of it. Neither read the same-window sample
(801 asks). Two runs were killed by the session limit on 2026-10-03 (A on w00, B on y00) after
rewriting their codebooks and before any labels; those unlabelled entries were discarded and both
codebooks stand at their last committed state (A 438, B 407).

**No held-out verdict is read.** The rule is cumulative over the 1,070 outside asks, and a third of
them have been read by one reader. A's pace on the other-years sample (29 per 269 asks) would reach
about 115 over the full set, on the not-saturated side, but that is a projection from one reader
and one sample, not the pre-registered reading.

**What is left, if resumed:** B on y00..y02 (3 runs), both readers on w00..w06 (14 runs), about
17 reader runs at about 200k subagent tokens each (3.4M tokens, two to three 5-hour windows). Each
run follows `reader_instructions.md` and is validated with `provenance/check_batch.py`.

## 7. Reading, provisional (the held-out test is paused)

- **At this grain, review draws on about 400 principles and the census is not saturated.** Both
  pre-registered val1000 readings say so, by two readers who agree on the count to within two.
  The user's "we don't even know how many conventions one can reasonably use to describe Mathlib"
  now has a floor: more than four hundred, with one new principle per ten asks still arriving.
- **The head is small and known; the tail is the work.** Forty principles cover half the asks and
  are the conventions every reviewer brief already states. The other half is a tail of 370 in
  which two fifths were seen once. The design-comparison reading found 8 of 31 variant principles
  in any document; this census says why handing over a document cannot close the gap: the
  document holds the head.
- **Rules and standards are half and half**, so half the census is in principle checkable by a
  linter or a situated query, and half is judgment with an anchor. That split is the input the
  coordination design (`review-coordination-design.md`) asked for.
- **What this does not show.** A principle written from a merged PR's comment can rationalise
  (`conventions-nature.md`, Risk). The guard is study 2: every ask carries its path and month, so
  each principle's scope by directory and by year is a measurement away, and a principle that is
  not a regularity in the library or the asks is a wish. Nothing here measures prevalence in the
  library.

**Does knowing the conventions change a review? (2026-10-04,
`results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md`.)** Reader A's codebook was
used as a brief on 14 PRs it never read. Two readers assigned an entry to 39 of their 46 maintainer
asks (85%), the same entry on all 38 both assigned. A Claude reviewer given, for each PR, the entries
behind that PR's asks reached 0.74 of those asks per session against 0.46-0.49 unbriefed (+0.26 and
+0.28 on two blind matchers; a ceiling, since the entries were chosen from the asks). The local
397B given the same went from 0.034 to 0.085. So the census holds knowledge a strong reviewer lacks
at the moment of review and can use; whether it can be delivered without the asks is untested.

## Caveats

- Readers are language models of one family, on merged PRs, reading the comment and hunk only;
  the family label (κ 0.94 between its own readers) was shown.
- The grain rule held, but codebooks were stretched as well as grown: 107 (A) and 90 (B) entries
  were broadened at least once by their owner, most in the later batches.
- The b05 outputs were validated, not re-read, after their runs were killed post-write.
- `unsure` was set on 20.6% (A) and 16.4% (B) of labels.

## Files

`reader_rubric_census_v1.md`, `reader_instructions.md`, `crossmap_rubric.md` (pre-registered);
`order.json` (seed, batches); `reader_A/`, `reader_B/` (`codebook.json`, `labels_<batch>.jsonl`);
`crossmap.json`; `analyse.py`, `results.json`; `provenance/` (`materialise_bodies.py`,
`build_order.py`, `build_batches.py`, `check_batch.py`). Bodies are never committed; they are
rebuilt from the store by event id.
