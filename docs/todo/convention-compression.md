# Convention compression: would fewer, more general rules help or hurt?

**Status** — open, 2026-10-09; nothing built, nothing run. Low priority by the user's own prior:
*"This may be worth looking into but my intuition is that it wouldn't shift the overall picture too
much."*

**The user (2026-10-09).** *"Another direction to consider here is whether the set of conventions is
compressed sufficiently or whether we can further compress the ruleset. It may be the case that more
general rules exist that subsume multiple conventions here and it's unclear whether that is an
advantage or disadvantage."*

## Where the census's grain sits now

Reader A's codebook has 438 entries. Its grain was fixed by a test that keeps each entry about as
general as it can be while still fixing the content of the ask (`reader_rubric_census_v1.md`):
*"would the same sentence, applied to a different PR, produce an ask of the same content?"*
- A family is too coarse: "the proof can be shorter" is not a principle.
- An instance is too fine: "use `Finset.sum_comm` here" names this PR's fix.

Anything more general than that no longer fixes the change, so the reviewer has to instantiate it.

The ad hoc part is the execution, not the target:
- 107 entries (A) and 90 (B) were broadened along the way;
- the two readers ended at 409 and 407 entries, with ask-level agreement 0.809;
- the cross-map found 312 `same` pairs, plus 49 and 59 pairs where one reader's entry was broader;
- the census is not saturated: Good-Turing puts the chance that the next ask needs a new entry at
  about 0.10.

## Motivating measurements: the record cuts both ways

**Generality cost recall:**
- **p0010 (43167).** P254, "a declaration's name follows its siblings' and analogues' names", is
  already general. Every reviewer and the ladder compared against the local sibling
  (`commutator_le_left`), which agrees with the PR. The maintainer's ask relied on the library's
  orientation (`inf_sup_left`). No ceiling session ever reached it
  (`docs/research/ceiling-residual-2026-10.md`).
- **Stage C** lists "convention too general to pick the comparison" among Claude E1's ten misses.
- **Distilled community guides** ("statute", `docs/dead-ends.md`) were null at N=115.
- **Stage F**'s 25 true sentences diluted to +0.03.
- **Conflicts:** P014 and P133 are opposite rules on squeezing a `simp`. One general rule ("keep
  proofs robust and minimal") would hide that conflict, not resolve it.

**Specificity cost recall:**
- **p0004 (42814).** P153's precondition, "an iff whose directions are used separately", was read
  literally: "no iff here has its directions used separately" (Claude E1). The maintainer's reason was
  different ("I don't see any reasonable application"). Never reached.
- **The ladder** (`results/pr_review_v5/probes/conventions-ladder-2026-10-08/`, unmatched): adding DP's
  two examples, which are more specific instances, turned the model's verdict to "conforms" at three
  asks the bare sentence reached (v0064, v0067, v0093).
- **The tail:** 286 entries have three asks or fewer, so retrieval and exams have almost nothing to
  work from there. Broader rules would pool that evidence and saturate sooner.

## Four meanings of "compress"

| kind | example | expected effect |
|---|---|---|
| de-duplicate at the same grain | merge drifted near-synonyms via the cross-map | a pure gain; perhaps 10-20% fewer entries |
| templates with a parameter | "a goal that a standard tactic *T* closes is closed by *T*", *T* ∈ {`simp`, `positivity`, `gcongr`, `omega`, `grind`, a merged `simpa`}, over P005, P094 and parts of P018 | the parameter keeps the content fixed; evidence pools across instances; maps onto try-it checks (the execution misses v0092, v0093, v0067) |
| abstraction | "use the library's existing notion" over P007, P011 and P019 | fewer rules, but judgement calls that fire at many more places; p0010 is the risk |
| hierarchy | keep the leaves, add general parents above them | parents for selection and scoping; leaves for the instruction at a place |

**The working view, untested:** compress the index, keep the instruction specific. Templates are the
promising middle; abstraction alone looks like a disadvantage for application.

## What would close it

Two measurements; either can come first.

1. **The compression curve, offline.**
   - Group the 438 entries into parents, then templates, then families.
   - For the 269 other-years held-out asks, report at each level the share whose entry the level
     covers and the share for which the general rule still generates the ask's content (a blind
     reader judges).
   - **Closes as "compression gains nothing"** if every level coarser than de-duplication drops the
     share that generates the right content by more than 0.10, against no gain on held-out coverage.
2. **General against specific at the place** (the ladder's machinery, DeepSeek).
   - For the 39 probe asks, the parent rule replaces the specific sentence in the U and A forms.
   - Measure whether the model still writes the maintainer's change.
   - **Closes as "abstraction hurts application"** if parent-rule passes fall by 4 or more of 39
     against the sentence's.
   - **Opens templates** if template passes match the sentence's while one template covers several
     entries.

If both close negative, the entry goes to `docs/dead-ends.md`, with the de-duplication pass kept as
census hygiene.

## Cost

- **Measurement 1:** one reader run to write the parents and templates (about 200k subagent tokens),
  and one blind reader over 269 asks.
- **Measurement 2:** about 39 × 4 × 3 single-turn calls on `first`, under an hour, $0.
- **When:** only after the decompose-and-shrink measurements (M1-M4,
  `docs/research/decompose-and-shrink-review-2026-10.md`), unless one of them shows the candidate set
  per part is too large at the census's grain.

## Related

- `docs/todo/conventions-nature.md` (studies 2-4: scope, conflict, maturity).
- `docs/todo/conventions-dossiers-exams.md` (the thread this came from).
- `docs/research/decompose-and-shrink-review-2026-10.md` (rationale, the most general grouping, does
  not shrink: each of the top five rationales tags 25-29% of asks).
