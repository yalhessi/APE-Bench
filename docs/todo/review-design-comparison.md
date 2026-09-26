# A reviewer that compares designs against the library's analogues

**Status** — open, 2026-09-26, **for a fresh session in a worktree**. It is the main line the user
chose over the mechanical sweeps (`review-mechanical-sweeps.md`), with one named risk.
**Cost** — free to scope (two readings of labelled asks, then a retrieval test against them); a
judged probe of the `facet-brief-probe` shape after that, or one validation run.

**Motivating example.** On the 506-ask validation relabel
(`results/pr_review_v5/adjudications/facet-relabel-val1000-v1/`), the 95 design-family (F6) asks
refer to:

| reference | asks | what the maintainer compared the PR against |
|---|---|---|
| variant | 31 | a different design, from taste |
| library | 22 | an existing analogue in Mathlib that does it differently |
| siblings | 21 | the PR's own declarations, inconsistent with each other |
| norms | 12 | a stated convention |
| mechanism, other | 9 | |

Warrants: judgment 47, compile 25, exhibit 7, count 5. Objects: family 45, statement 26,
definition 15. So nearly half of design asks are comparisons against something that exists, in the
library or in the PR: an ask without a fix, "this departs from how that is done; align it or justify
it". The pipeline's hits on the validation small12 are all proof (F1) and docs (F10), none in any
other family, and `generalization` has never hit in the record. The one design gain in the Claude
probes (`docs/research/facet-brief-probe-2026-09.md`, the central `ConvexSpace` ask) came from
analogues the reviewer recognised from memory: the monad-algebra form, `PMF`'s API as the template,
`stdSimplex` as "the free convex space". No tool supplies analogues.

**The user's framing (2026-09-26).** The asks should reflect *"a general taste or design choice the
community follows, not repeat historically asked reviews"*; gold is for evaluation, not for the
reviewer's knowledge. The library is the largest expression of that taste, since every declaration
in it is a design decision that passed review; the written principles (style guide, library notes,
naming conventions) are the second; the tacit rest is the third. The review corpus's legitimate use
is the taxonomy of what matters, not a lookup.

**The named risk, and the guard.** *"It would be very bad if we were deciding something isn't aligned
because it's being compared to the wrong sibling."* Three guards, all before any reviewer uses it:
1. The analogue is chosen by **role**, evidenced (same object kind, same position in the class
   hierarchy, same API shape), and the finding **names it**, so a wrong analogue is a visible,
   refutable claim rather than a hidden premise.
2. Analogue choice is **measured on gold first**: for the 22 library-reference and 21
   sibling-reference design asks, does retrieval return the analogue the maintainer used? Report the
   wrong-analogue rate beside the recall.
3. In any probe, the blind matcher labels findings whose analogue is wrong, reported beside hits.

**What to find out first, free.**
- Read the 31 `variant` asks: is the design principle stated in the comment? Does it appear in
  Mathlib's written guidance? If it is written, the reviewer can be given principles instead of
  precedents; if not, the question becomes which model holds the taste, and the cutoff caveat applies.
- For the 43 library- and sibling-reference asks, how was the analogue findable: by name, by role,
  by API shape, by import neighbourhood?
- Build retrieval for the findable kinds and test on those 43: analogue recall and wrong-analogue rate.

**What would close it.** Retrieval returns the maintainer's analogue on at least two thirds of the
43 with a wrong-analogue rate at or below one in five; then a judged test with the analogues in the
arms' context. **The small12 validation set holds no design asks** (its 30 asks are F1 11, F10 5,
and 14 in F2/F3/F8/F12), so the test needs the full 60-PR validation set's design asks or a
design-stratified subset, and reviewed workspaces for them.

**Start here.**
- read: `docs/research/review-work-structure-2026-09.md` §7 (the facets and their kappa);
  `results/pr_review_v5/adjudications/facet-relabel-val1000-v1/reader_rubric_facets_v1.md`, `reader_A.jsonl`,
  `reader_B.jsonl` (fields `cid, object, reference, warrant, note`); family labels in
  `results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/*.jsonl` (`cid, family`);
  `docs/todo/review-context-needs.md` (this entry is its "design precedent by role" collector made
  concrete); `docs/research/facet-brief-probe-2026-09.md` (the gain, the run variance, the cutoff
  caveat); `.claude/rules/mathlib-review.md`, the probe-cutoff rule.
- run (spends nothing), the cross-tab above:
  ```
  ape/bin/python - <<'EOF'
  import json, glob
  from collections import Counter, defaultdict
  D = "results/pr_review_v5/adjudications/facet-relabel-val1000-v1/"
  A = {r["cid"]: r for r in map(json.loads, open(D + "reader_A.jsonl"))}
  B = {r["cid"]: r for r in map(json.loads, open(D + "reader_B.jsonl"))}
  fam = defaultdict(dict)
  for f in glob.glob("results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/*.jsonl"):
      for r in map(json.loads, open(f)):
          if "cid" in r and "family" in r: fam[r["cid"]][f] = r["family"]
      agreed = {c: list(v.values())[0] for c, v in fam.items() if len(set(v.values())) == 1 and len(v) >= 2}
  tab = defaultdict(Counter)
  for c in A.keys() & B.keys():
      if A[c]["reference"] == B[c]["reference"] and agreed.get(c) == "F6": tab["F6"][A[c]["reference"]] += 1
  print(dict(tab["F6"]))
  EOF
  ```
- bounded by: `docs/dead-ends.md` (precedent retrieval's hits are chance-level; any keep rule is
  selection, and the generator comes first); the probe-cutoff rule; `review-context-needs.md`.

**Evidence** — the relabel results `results.json` (`S3`, `C.family_division`: design is 48%
judgment); the cross-tab above, computed 2026-09-26; `facet-brief-probe-2026-09.md` rounds 1-3.

**Risk** — the wrong analogue (guarded above); taste that is not articulable; no design asks in
small12, so the cheap run cannot measure it; a Claude probe's own Mathlib memory confounds
analogue retrieval, so the retrieval test is on gold, not on a reviewer.
