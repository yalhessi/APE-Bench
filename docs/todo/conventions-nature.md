# The nature of Mathlib's conventions

**Status** — study 1 read on val1000 2026-10-03; its held-out reading **paused 2026-10-04** (A read
the other-years sample, 269 of 1,070 asks; B none; about 17 reader runs left). Studies 2-4 open,
**for a fresh session**. Whether the census helps a reviewer, at best: the ceiling probe,
[`conventions-ceiling-probe.md`](conventions-ceiling-probe.md).
**Cost** — no spend beyond reader labelling; a 125-ask reader run is about 200k subagent tokens.

**The user (2026-09-29).** *"The conventions problem is very much the heart of this project. I suspect
the LLM can reasonably follow any rule we give it with sufficient clarity, but it's really learning
what conventions hold at a given point and in a given window/scope that is fundamentally hard. The
conventions presumably honor some Mathlib philosophy that should be followed above all… From this it
should follow that everything added must consider its correctness, its compactness, and possibly
other questions, instantiated to concrete questions about the objects modified. We keep assuming
we can write down the conventions, but this is fundamentally underexplored. When do type classes get
used as opposed to preconditions? How does the answer vary in each area? We don't even know how many
conventions one can reasonably use to describe Mathlib. Are there conflicting conventions? Do we use
the most specialized, or arbitrarily?"*

**Motivating examples.** `design-comparison-val1000-v1`: both readers could write the principle
behind 30 of 31 variant design asks as a one-sentence rule, but only 8 are in any document, 12 are
covered by a maxim that says *that* not *which*, and 11 (the encoding choices) are written nowhere.
The naming arm stalled on 33337 because a prefix at 21 against 7 is a norm to one reader and noise to
another. `naming_norm` counts a leading token globally and cannot see a suffix or an area.

**A working definition to test.** A convention is a regularity in how the community writes
something, with: a **scope** (global, area, file, era); a **rationale** tracing to the philosophy
(maintainability, generality, automation, discoverability, readability, compactness); a **form**
(a rule that can be checked, or a standard needing judgment in application); a **maturity**
(settled, emerging, contested) and its exceptions. The typeclass-versus-hypothesis question is the
exemplar: structural and inferable assumptions (`Finite`, `NeZero`) are classes, specific facts
(`0 < r`) are hypotheses, and the balance shifts by area. That is a regularity of an area, not a
rule in a document, and it is known by measuring it.

**Where to look.** Learning coding conventions statistically from code (the NATURALIZE line):
a convention as a regularity of the corpus at a scope, deviation flagged, the rule never written.
Legal theory on rules versus standards and on conflict resolution by specificity and precedent.
Style guides derived from a stated philosophy with rationale (the Zen of Python to PEP 8, the Rust
API guidelines). Rule-following in philosophy: practices learned from cases, not statements.
Mathlib's own written guidance and 33 library notes (`design-comparison-val1000-v1/written_sources.md`).

**Studies, all readings of material we hold.**
1. **Saturation count**: write the principle behind each labelled ask across families
   (val1000's 1,833 and the outside samples' 1,070) until new principles stop appearing; the
   accumulation curve says whether review is a hundred conventions or a thousand.
2. **Scope**: the same principle measured by directory and by year, with a census where the
   principle is countable (typeclass vs hypothesis by area); how much is area-specific, how much drift.
3. **Conflict**: the asks where two principles collide and which won; does specificity decide, or
   a priority among rationales, or the surrounding file?
4. **Maturity**: migrations (`to_dual`, `grind`, `fun_prop`) traced through the corpus over time;
   how a convention is born, and how an emerging one licenses an ask.

**What would close it.** A convention census with the five parts filled for each, a count with
its saturation curve, the scope and conflict findings, and, from them, the list of conventions that
are measurable regularities (mined, not written) against those that are standards (judgment, with
their anchors). That list is the input to `review-coordination-design.md`.

**Risk.** Readers who are language models on merged PRs; principles written after the fact
rationalise. The guard is the corpus: a principle that is not a regularity in the library or the
asks is a wish.

**Two worked cases from the construction demonstration (2026-09-29).** No reviewer condition reached
either, and each is one of the studies above in miniature.
- **Scope conflict (study 3).** On 30458 the maintainer asked for `variable [IsLeftCancelMul α] in`
  in place of the PR's subsections: "just keep things the same as before, collect the common
  variables". At the base commit the idiom is in 1,129 of 6,947 Mathlib files (2,695 lines), 20 of 141
  in `Algebra/Group`, 1 of 13 in `Algebra/Group/Pointwise`, and 0 in the file itself. Library practice
  won over local practice, together with a minimal-diff rationale. A census at file scope gives the
  wrong answer, and one at library scope gives the right one.
- **Maturity (study 4).** On 32875 the maintainer asked to tag two lemmas `grind`. At base,
  `Data/Finset/Image.lean` holds 18 `grind` uses, `Data/Rat/Lemmas.lean` none, and 137 files
  library-wide. The first ask has a file regularity behind it, and the construction pass reached it in
  one of two runs. The second has only the migration behind it, and nothing reached it.

**Study 1 result (2026-10-03; `results/pr_review_v5/adjudications/conventions-census-v1/results.md`,
pre-registered in `reader_rubric_census_v1.md` at `30a0a22`).** Two blind readers wrote the principle
behind each of the 1,833 val1000 asks in one seeded order, each keeping a running codebook. They end
at **409 and 407 principles**, two apart, having coincided in size four times. The last three batches
added 7.8% and 7.6% of the codebook against the pre-registered 5% rule: **not saturated, by both
readers**; Good-Turing says one ask in ten still brings a principle the census does not hold. The
head is small and known: the top 10 entries cover 22% of principled asks and the top 50 cover 55%,
and every one of the top fifteen is a convention the project could already name; the tail is 370
entries, two fifths seen once. Generality and naming are concentrated (five principles carry 87% and
63% of their asks); statement-and-API design and documentation are diffuse (34% and 28%). Rules and
standards split evenly (841 / 828 asks). Agreement: a third blind reader paired 377 of each codebook's
entries, giving an ask-level agreement share of 0.809; without any mapping the adjusted Rand index is
0.62 and none-versus-some agreement 0.979. One conflict datum for study 3 fell out: two maintainers
hold opposite rules on squeezing a non-terminal `simp` (A's P014 against P133). The held-out reading
stopped after A read the other-years sample (29 new entries on 269 asks, 7.1% of its codebook; no
verdict, since the rule is over all 1,070 outside asks). So the answer to "how
many" is a floor: more than four hundred at this grain, still rising at about one per ten asks, with
the written guidance covering the head and not the tail.

**Start here** (studies 2-4, or extending the census).
- read: `results.md` in the census directory; `reader_rubric_census_v1.md` (what a principle is, the
  grain rule, the thresholds); `reader_A/codebook.json` and `reader_B/codebook.json` (the census
  itself: id, sentence, rationale, form); `crossmap.json` (the pairing of the two).
- run (spends nothing): `python3 results/pr_review_v5/adjudications/conventions-census-v1/analyse.py`
  prints the curves, the saturation readings, concentration by family, rationale and form, and the
  agreement with and without the cross-map; `--write` rewrites `results.json`.
- to re-read or extend: bodies are never committed; `provenance/materialise_bodies.py <out.json>`
  rebuilds them from the store by event id (run from the repo root with `PYTHONPATH=$PWD:$PWD/src`
  under `ape/bin/python`); `provenance/build_batches.py` writes the batch files; each reader run
  follows `reader_instructions.md` with READER and BATCH set, costs about 200k subagent tokens and
  10-24 minutes, and is validated with `provenance/check_batch.py <dir> <reader> <batch>` before its
  commit. Killed runs are validated, not assumed partial.
- study 2 (scope): join `reader_*/labels_*.jsonl` to
  `results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/events.jsonl` on cid
  for `path` and `month`; per principle, the directory and month distribution of its asks is the
  first scope reading, and it needs no new label. The typeclass-versus-hypothesis census by area
  needs the base-commit source under `data/code_execute/`.
- study 3 (conflict): start from the entries the readers kept apart as opposite rules (A: P014 and
  P133; B: P015/P025 and P392), the cross-map's near-misses (`crossmap.json` against the label
  co-assignments, listed in the cross-map commit `998840d1`), and rows with a `second_principle_id`.
