# Convention detectors: what a deterministic check can state about the PR, and whether anyone asks

**Status** — open, 2026-10-06. The first detector is built and measured alone
(`dot_notation`, `src/mathlib_review/producers/dot_notation.py`;
`results/pr_review_v5/probes/convention-detectors-2026-10-06/README.md`). It is the first member
of the producer seam (`docs/research/codebase-redesign-2026-10.md` §4.4) and step 2 of
`docs/plans/2026-10-03-after-structure.md`.
**Cost** — no spend for the detector work; the recall measurement below needs change graphs for
census PRs (compute and tier-2 store reads); a reviewer rep only if a detector clears its bar.

**Motivating example.** Dot notation, stated deterministically on the three probe sets: one exact
in-sample ask (`d0038`, 33294, `IsFundamentalSequence.of_isNormal`), 0 facts on all 10 control PRs,
and **silence on 21 of 21 out-of-sample PRs** -- not structural, those PRs hold no situation of
either shape. In sample, 5 of 7 facts are valid as written (4 of 6 edits compile in the reviewed
workspace). The asked move (`Order.IsNormal.map_* H` -> `H.map_*`) is stated at five sibling places
where the maintainer commented once. And the ceiling probe's stage H says why recall may not be
the binding question: every census rule is raised by maintainers at 5% or fewer of the places a
blind pinpointer flags (`conventions-ceiling-probe.md`).

**What would close it.**
1. *Recall at scale.* The three probe sets hold about 0.8 dot-notation asks out of sample; the
   census holds 33 (P057 29, P034 4, on about 17 PRs). Build change graphs for the census PRs that
   carry them (the release builder over the PR store), run `cli producer bench`, and read the rate:
   asks at flagged places over places flagged, against stage H's 5%.
2. *The two refinements the in-sample misses name*, each pre-registered before it is run: a
   declaration lookup that checks the binder's own namespace before stating `x.lemma` (both invalid
   facts were `H : Ordinal.IsNormal f` resolving to `Ordinal.IsNormal.*` first), and the elaborated
   local context for proof-local names (`d0039`'s `fun h =>`), which is the try-it battery's
   (after-structure §3).
3. *The next detectors*, measured the same way: generated families (P201, 11 asks on 10 census
   PRs; dev `57bcc9fd`, `@[to_fun]`), primed names (P113 + P211, 9 on 9; dev `6b02b611`).

**Start here.**
- read: `results/pr_review_v5/probes/convention-detectors-2026-10-06/README.md` (rule, amendment,
  results); `src/mathlib_review/producers/__init__.py` (the seam: `Fact`, `PRODUCERS`,
  `context_rows`); `src/mathlib_review/producers/dot_notation.py`;
  `src/mathlib_review/analysis/producer_bench.py`;
  `results/pr_review_v5/adjudications/conventions-census-v1/reader_A/codebook.json` (the entries).
- run: `ape/bin/python -m src.mathlib_review.review.cli producer bench --producer dot_notation --set configs/probe_sets/dev_medium_0_3_0.yaml`
  (no spend); a fact's edit is checked with `ape/bin/python -m src.mathlib_review.review.cli tool
  lean_verify_edit --episodes <release>/input/episodes.jsonl --pr <n> --workdir <scratch>
  --run-config <dataset config> --arguments '{"path": ..., "line_start": L, "line_end": L, "replacement": ...}'`.
- bounded by: `docs/dead-ends.md` "Linter-as-convention-oracle" and "Surface proxies for convention
  discovery" (a detector states a fact about the code, never the convention's demand); the
  selection ruling of 2026-09-22 (a detector does not rank or withhold a reviewer's findings);
  `conventions-ceiling-probe.md` stage H (the demand side).

**Evidence** — commits `b54b29aa` (seam), `6128044d` (detector), `9e6569e0` / `90edef54`
(pre-registration, amendment 1), `d3df70b9` (results).

**Risk** — the demand side: if maintainers raise a convention at a few percent of the places it
applies, a quiet, valid section still adds little recall, and the lever is the decision to file
(stage G), not the fact.
