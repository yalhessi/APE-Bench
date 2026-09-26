# A reviewer that compares designs against the library's analogues

**Status** — **in progress**, 2026-09-26: the two free readings are done
(`results/pr_review_v5/adjudications/design-comparison-val1000-v1/results.md`); next is the
shape-match retrieval and its test on the 43. It is the main line the user chose over the
mechanical sweeps (`review-mechanical-sweeps.md`), with one named risk.
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

**Results of the two readings (2026-09-26, two blind readers).** The taste is articulable: both
readers wrote the principle as a one-sentence rule for **30 of 31** variant asks. It is mostly
unwritten: checked against the style guide, review guide, values page, naming page and the 33
library notes, **8 are written, 12 covered by a maxim only, 11 nowhere**, the eleven being the
encoding choices. The comparison object is unambiguous: the readers named the **same analogue in
43 of 43**. It is reachable by API shape in 17-23 of 43 (the PR wrote out the body of something the
library names), by name in 3-10, by role in 3-6. A wrong analogue is plausible in 2 (agreed) to 7
(either) of 43. A **name-token search from the PR's own declarations finds the analogue in the top
ten for 0 of 43**, and its top hits are lookalikes: the wrong-sibling risk lives in retrieval, not
in judgment. The exemplar that defeats shape matching: v2006, where the PR wrote the sequential
form and the maintainer asked for the filter form used by `IsCompact` and `IsLindelof`.

**Shape search through Loogle, tried the same day** (`provenance/loogle_shape_test.md`): with one
fixed derivation rule (bound identifiers to `_`), the analogue ranks first in **1 of 15** and is
absent in 13, because the PR's spelling differs from the library's (`Ideal.span` against
`Submodule.span`, a literal `1` where `Pi.single_apply` has a variable), because the analogue is a
definition body that only unfolding reaches (`MulAction.orbit`, `QuotSMulTop`), or because the
analogue is a role (`FunLike`, `Module.Invertible`, `IsCompact`) and has no shape.

**Generalisation check, 2026-09-26** (`results/pr_review_v5/adjudications/design-comparison-outside-v1/results.md`).
The user asked whether this matters outside our immediate focus before any build. Two new samples,
two blind readers each, stage-1 kappa 0.91 and 0.95: 300 PRs in no set from the same window (801
asks) and 129 PRs from 2024-05..2025-05 and 2026-04..2026-08 (269 asks, tier 2 collected for the
purpose). Comparison asks are **9.1% (CI 7.3-11.3) and 9.7% (CI 6.7-13.8)** of round-1 asks, against
8.5% on the validation set, on one PR in six; design asks are 23-24% everywhere. The decoy rate is
higher than the first reading showed: **18 agreed of 99** comparison asks have a plausible wrong
analogue, every one a twin of the right object along one axis (direction, dual, strength, bundling,
carrier, continuity, scope, idiom). Findable by the PR's own siblings 29, API shape 25, neighbourhood
10, role 9, name 9. Prevalence is settled; the build is warranted on that count, with the family
return along the decoy axes as a requirement.

**Next: unification against definitions, inside Lean.** For each hypothesis and definition body
the PR writes, search the library's definitions, classes and `_apply`/`_def` lemmas for one whose
body unifies with it modulo reducible unfolding and generalisation of literals (an `exact?`-shaped
search whose targets are definitions, not the goal). Test on the 43 for recall and decoy rate; v2006
must come out as "no analogue by shape", never as `IsSeqCompact`. Role retrieval, for the remainder,
after that.

**Retrieval built and measured, 2026-09-26** (`results/pr_review_v5/probes/fold-search-2026-09-26/`).
A Lean metaprogram that unifies a declaration's subterms, hypotheses included, at three spellings
against definition bodies, one-field class fields and rewrite-lemma sides, keeping folds that
replace the subterm's distinctive constants by a new named concept, tiered into naming folds and
rewrites, and dropping folds that reverse a simp lemma. On the labelled comparison asks, each PR's
file at its review commit against the latest built base at or before the review with the base's
whole library imported: **50 sites present, 33 folded, 6 hits** (`QuotSMulTop`, `IsBipartite`,
`Pi.single`, `FiniteIndex`, `IsPrincipal`, `Set.preimage`), all in the naming tier with families of
2 to 4; **2.1 naming folds per non-site declaration**. The six are the "wrote out the body of a
named concept" class; the rest of what the readers called API shape is primed constructor
variants, structure literals owed a smart constructor, missing twins, and two-step relations, each
a different mechanical route. Binder order defeats unification (`Antitone` written with swapped
binders). The closing criterion below is not met by this route and is not its measure.

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
