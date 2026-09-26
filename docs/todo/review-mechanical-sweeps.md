# Mechanical sweeps: the linter tier below review

**Status** — open, **bounded** (user, 2026-09-26): build and measure its potential at no cost, and
stop there unless the numbers are strong. It finds an issue only by finding a fix, so it reaches
only asks whose fix is enumerable, encodes what has been asked before, and touches no judgment ask.
The main line is `review-design-comparison.md`.
**Cost** — code and Lean time for Steps 1-2; about $30 for Step 3, only if Step 2 passes.

**Motivating example.** `results/pr_review_v5/probes/closer-battery-2026-09-26/`: of 15 missed asks
tried as one-edit compiles in the PRs' reviewed workspaces (6-40 s each, controls clean), **eight
came out verbatim** from procedures with no false-positive mode (30458's pre-PR proofs compile under
the new variables; all four `noncomputable`s of 26755 compile away; 36822's dropped `@[simp]` is a
diff lint; 33294's dot-notation rewrite compiles; 33145's `inf` lemmas derive from the `sup` ones by
`(α := αᵒᵈ)`), one more with the proof's own lemmas seeded into `simp`, three maintainer questions
were answered "no", and the two duplicates were found by hypothesis shape and by docstring word
where `exact?` failed with the lemma in scope. 31 of the 38 misses of both sets are labelled
findable this way (`adjudications/miss-warrants-2026-09-26/finding_mechanism.jsonl`, one reader).

**What would close it.** The blind run of the seven procedures (old-proof replay, closer list,
binder sweep, attribute diff, twin check, three-radius existence search, lints) over every object
of the 23 PRs of both sets: **at least 15 of the 38 misses hit, and a median of at most 8 firings
per PR**. Below either, the entry moves to `dead-ends.md` with the numbers. Above both, Step 3 of
the plan: the facts in the arms' context, two lead runs per set.

**Start here.**
- read: the probe README and `battery.py` / `battery3.py` (the edits, and the
  `-Dexperimental.module=true` retry two Lean 4.26 workspaces need);
  `docs/plans/2026-09-25-align-decisions-with-maintainers.md`, the Step 1b paragraphs;
  `src/mathlib_review/review/toolbox.py` (the arms' own compile tool outside a run);
  `src/ape/toolkits/execute/lean/core/build_manager.py::reviewed_workspace_key`.
- run: `ape/bin/python results/pr_review_v5/probes/closer-battery-2026-09-26/battery.py v0016`
  reproduces one case in about 10 s.
- bounded by: filing a compiled fact is generator-side, not selection (`dead-ends.md`, the
  publication-rule ruling); verification needs the *reviewed* workspace (`.claude/rules/mathlib-review.md`).

**Risk** — noise: the edits so far were targeted by the ask, so the blind yield is unmeasured; it
covers no design, intent or PR-level ask; a norm that is still forming (`grind` tagging, an
emerging name prefix) is invisible to it.
