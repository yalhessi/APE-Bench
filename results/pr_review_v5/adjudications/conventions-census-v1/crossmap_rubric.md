# Matching the two codebooks (cross-map rubric, pre-registered 2026-09-29)

Two readers each built a codebook of principles over the same asks, blind to each other. Their
sentences differ in wording and in grain. A third reader, who has seen neither reader's labels,
matches the entries, so that agreement can be read at the ask level (do the two readers' ids for
one ask name the same principle?) and the two counts can be compared.

**Inputs.** `reader_A/codebook.json` and `reader_B/codebook.json`: id, sentence, rationale, form.
Nothing else: no labels, no asks, no example.

**Output.** `crossmap.json`: `{"pairs": [{"a": "P0xx", "b": "P0yy", "relation": ...}, ...]}`.

- A pair is recorded when the two sentences state the **same principle**: the same situation and
  the same preferred form, allowing different words, different examples of the mechanism, and one
  sentence being slightly more general than the other. `relation` is `same` (equivalent),
  `a_broader` or `b_broader` (one covers the other and more).
- Many-to-many is allowed: one reader's entry may be two of the other's. Record every pair that
  holds.
- Do not pair entries that share a family or a rationale but differ in the preferred form ("split
  long proofs" and "extract a lemma used twice" are different principles), or that share a
  mechanism but differ in the situation.
- An entry with no counterpart is simply absent from `pairs`.

**Reported.** Entries in A with at least one match, entries in B with at least one match, the
number of `same` pairs, and, from the labels, the share of asks whose two ids form a recorded pair
(with `none`/`none` counted as agreement). The rubric that fixed this: `reader_rubric_census_v1.md`.
