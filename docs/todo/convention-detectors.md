# Convention detectors: what a deterministic check can state about the PR, and whether anyone asks

**Status** — open, 2026-10-06; **three detectors built and measured alone, none yet read by a
reviewer.** `src/mathlib_review/producers/` (the seam: `Fact`, `PRODUCERS`, delivery through the
per-PR `context_file`), `analysis/producer_bench.py`, `cli producer bench|context`. Pre-registered
stages 1-4 and their results: `results/pr_review_v5/probes/convention-detectors-2026-10-06/README.md`.
Step 2 of `docs/plans/2026-10-03-after-structure.md`; the second half of step 3 of
`docs/research/codebase-redesign-2026-10.md`.
**Cost** — no spend so far. The next step is one reviewer run with the sections (a subscription
window on validation small12 or dev), or judge-free reading as in the ceiling probe.

**Motivating results** (census = val1000, 973 PRs, 1,833 reader-A asks; probe sets = dev,
validation small12, post-cutoff):

| detector | census exact recall | census demand (located) | control-PR facts | validity |
|---|---|---|---|---|
| `dot_notation/3` (P057, P108) | **8 of 49** (16%, narrow) | 19 of 217 at /1 (8.8%) | 33 on 331 census controls; 0 on 10 probe-set controls | holdout 19 of 20 at /2; dev 4 of 4 compile or match |
| `primed_names/1` (P113) | **5 of 9** (a finder; coarse) | 5 of 101 (5.0%) | 18 on 331; 0 on 10 | 20 of 20 true; 1 out-of-sample exact ask on the probe sets (43167) |
| `generated_twins/2` (P201, `@[to_fun]` only) | 0 of 11 | -- | 0 | 11 of 11 in sample; the retired `@[to_additive]` shape was 0 of 29 |

Two things to carry. **Demand is the limit, as stage H found**: maintainers ask at 4-9% of the
places a detector flags, and three times a maintainer's own suggestion kept a prime the detector
flagged. And **recall is narrow by construction**: most dot-notation asks the detector misses are a
receiver it cannot type (a proof-local `h`, a projection `hϕ.2`) or another call at the same place.

**What would close it.**
1. *Does a section move a reviewer?* One run with `primed_names` and `dot_notation/3` sections in the
   packet (`cli producer context ... --base <the set's model_context.jsonl>`), read against the
   same reviewer without them, on asks the sections can reach. The stage-G lesson applies: a reviewer
   handed the right convention at the right place may verify it and still not file. **Not on the
   current probe sets** (checked 2026-10-06): `primed_names` and `dot_notation/3` fire on 1 of 11
   validation small12 PRs and 0 of 10 post-cutoff PRs, so a window there would read one fact. The
   run needs a set drawn where the sections fire -- census-like PRs outside every evaluation set, with
   reviewed workspaces built -- which is the design step before any spend.
2. *Typing the receivers the text shape cannot*: proof-local names and projections, by elaboration
   (the try-it battery, after-structure §3).
3. *The P201 asks the twin shape cannot see*: most are a missing attribute on a lemma with no
   hand-written twin (43167's p0011, "Missing `@[to_additive]` here"). A shape that compares a new
   declaration's attributes with its file siblings' is untried.
4. *The rest of after-structure §2*: sibling propagation of a filed rename (a post-pass on a
   ledger), and the area census promoted to a section.

**Where it stands (2026-10-06, later).** Item 3 was tried as stage 6 (`missing_attribute`): 8 of 19
census facts valid as written, two mechanisms fixed in `/2`, and then silent on the 60-PR
validation release, so a precise, nearly silent section with no census P201 ask reached.
Item 1 is set up as stage 5 -- 16 census PRs (10 where a section states the exact ask, 6 where the
sections fire unasked), a release cut from the sealed val1000 draw (`inputs/probes/census-detectors-v1`),
S0/S1 configs differing only in `context_file`, the workspaces building -- and **is not run**: the
two Pro subscription accounts now refuse ("organization has disabled Claude subscription access for
Claude Code"), so a run would spend the user's own primary quota (seven_day at 67% that day), about
two dev-run windows. Once the workspaces are built it is one command per condition:
`ape/bin/python -m src.mathlib_review.review.cli run --config configs/pr_review_v5_census_detectors_v1_opus55_hygiene_claude_sub.yaml --run-name probe_census_detectors_s0_rep1 --execute`
and the same with `..._hygiene_sections_claude_sub.yaml` and `..._s1_rep1`, read by hand by stage 5's rule.

**Item 1 on gpt-5.5 (2026-10-07): no effect.** Run on gpt-5.5 instead (the user's call; stage W's
condition), blind hand reading: the sections took 0 to 1 of the 13 exactly stated asks (S0 against S1,
one rep each, $52 billed), not a volume lever. S1's reasoning summaries show the stated fact considered
and dropped at four PRs, once on an explicit guess about maintainers (32674), and unmentioned at four.
S2, the disposition paragraph of `docs/plans/2026-10-06-generation-without-suppression.md`, run
the same day: asks 1 to 5 of 13 (+4, or +3 on one close mark), but unasked facts 0.50 to 2.17 a
stratum-B PR (13 of 14 filed), so **a volume lever** by the pre-registered gate: it files what the
sections state, asked or not. Where it still missed, it conformed on precedent twice, which the
paragraph excludes. What would move this: a reading of whether the unasked filings are welcome (the
open adjudication), since the gate counts them as cost without knowing. Opus untested.

**Start here.**
- read: the probe README above (rules, amendments 1-2, stages 1-4, the two corrections);
  `src/mathlib_review/producers/__init__.py`; `producers/dot_notation.py`, `primed_names.py`,
  `generated_twins.py`; `analysis/producer_bench.py`;
  `results/pr_review_v5/probes/convention-detectors-2026-10-06/census_set.py` (the census as a probe set).
- run (no spend): `ape/bin/python -m src.mathlib_review.review.cli producer bench --producer primed_names --set configs/probe_sets/val_small12.yaml`;
  the census needs its structure rebuilt first (`PYTHONPATH=$PWD:$PWD/src ape/bin/python
  results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/provenance/build_structure.py <dir>`,
  about four minutes, and `extract_draw_feedback.py val1000-2025-06-2026-03-v1 <out.json>`), then
  `census_set.py layout <dir> <out.json> <set_dir>`.
- bounded by: `docs/dead-ends.md` "Linter-as-convention-oracle" and "Surface proxies for convention
  discovery" (a detector states a fact about the code, never a convention's demand); the selection
  ruling of 2026-09-22 (a section does not rank or withhold a reviewer's findings);
  `conventions-ceiling-probe.md` stages G and H (the decision to file, and the demand side).

**Evidence** — seam `b54b29aa`, `750698b2`; detectors `6128044d`, `56a68489`, `ca6d6233`,
`64fe8d68`, `16e180fb`; pre-registrations `9e6569e0`, `90edef54`, `96e8225a`, `cba7591a`,
`a93a3e74`, `9f084595`; results `d3df70b9`, `a1fb3dba`, `301ea82d`.

**Risk** — the demand side: a quiet, valid section still adds little if maintainers raise a
convention at a few percent of the places it applies.
