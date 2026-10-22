# The thesis pilot was run in June, and nothing it produced can be read

**Status** — open, found 2026-09-23 by a read-only survey for a thread separate from the review arms;
the counts below are that survey's and are to be re-checked by whoever picks this up
**Cost** — free to record and to fix the plumbing (about half a day); the comparison itself is paid,
roughly $150-200 for three reps of both arms, and is **deferred by choice** (`docs/dead-ends.md`,
"Deferred by choice") -- nothing here reopens it
**Motivating example** — `docs/PROJECT-STATUS.md` §11 says the thesis experiment
(`lean_reviewed_proof_engineering`, the reviewer gate inside the generation loop) "is built and has pilot
configs; the comparison against compile-only feedback has not been run". It was run. `.ape/runs/` holds
compile-only pilots (`ape_bench_pe_gpt52_first5_semval_no_retrieve_tmux`, 3 of 5 passed, $5.07;
`ape_bench_pe_gpt52_first20_semval_no_retrieve_resume`, 12 of 20, $18.97) and four reviewed pilots
(`ape_bench_reviewed_pe_gpt52_first5`, `_fixed`, `_fixed2`, `_fixed3`: 0 of 5 each, $14.82 together, every
`_fixed3` task ending `paused_cost_limit` at $1.74-2.13). No commit message or doc mentions them.

## Why none of it can be read

Four defects, three still on the tree:

1. **The gate's `judge_mode` is dropped.** `configs/ape_bench_reviewed_proof_engineering_pilot.yaml`
   sets `judge_mode: generated_only`; `LeanReviewGateConfig` inherits `LeanJudgmentConfig.judge_mode =
   "with_ground_truth"` (`src/ape/tasks/lean_tasks/formal_math/judgment/task.py:28`), and
   `create_task_from_data` builds the child's config from overrides only -- the half of
   `framework-defects-2026-09.md` §1 that concerns this task. In `_fixed3`, 11 of 11 reviewer sessions
   had `<maintainer_reference_diff>` in the prompt.
2. **The reviewer inherits the generator's tool grant.** `src/ape/scaffolds/factory.py:61` copies the
   base config's `task_config_overrides`, so the reviewer was offered `file_write`, `file_edit`,
   `file_multi_edit` and `lean_verify` instead of the judge's read-only set (it never called them).
3. **The gold file was readable by both arms.** `blocked_path_patterns` are enforced only by the
   sandbox, isolated-local and container runtimes, and the pilot runs on the default local runtime.
   All 11 reviewer sessions read `target/<filename>`, the merged file; 10 of 16 unambiguous compile-only
   tasks read it too, including 8 of their 10 passes. One reviewer blocked 8 rounds on a typo that the
   merged Mathlib version itself keeps.
4. **No cap on review rounds**, so an over-flagging reviewer loops to the cost cap. And the entry point
   (`python -m ape.scaffolds.ape_agent.main <jsonl> --config <yaml>`) spends from the first call, with no
   `--execute` gate.

**Defects 1 and 2 closed 2026-10-22** (branch `dataflow-refactor`): the gate's reviewer runs in the
config's `judge_mode` and holds its own class's tool grant, not the generator's;
`tests/ape/test_task_config_resolution.py::test_the_pilots_review_gate_neither_sees_gold_nor_holds_write_tools`
builds it exactly as the task does, from the pilot config, and asserts both on the worker side. The fix
is in the shared resolution and the nested primitive, not at the gate's call site as recommended below:
the agreed refactor plan (F1, "do not broadcast a parent config into its children") takes the general
rule, and the v5 lead inheritance that recommendation protected was measured first -- on all 17 lead
configs the inherited setting equals the arms' own default. Defects 3 and 4 are untouched, and the four
pilot runs stay uninterpretable: `_fixed3`'s gate verdicts were given with the gold diff in view.

## What would close it

Record first, then plumbing, no spend: correct `PROJECT-STATUS.md` §11 ("attempted, uninterpretable",
not "not run"); a test that builds the pilot's reviewer exactly as `lean_review_gate` does and asserts
its `judge_mode` equals the gate config and that it holds no write tool -- fix at the gate's call site
(`reviewed_proof_engineering/review_gate.py` passing its own `task_config_overrides`), **not** in
`tasks/base.py` or `scaffolds/factory.py`, because v5 leads spawn arms through the same inheritance; a
test that `target/<filename>` is unreadable under the pilot's runtime once it is switched to a sandbox;
`max_review_rounds`; a preflight. Then the pilots are interpretable, which says nothing yet about
merge-readiness -- that needs an outcome metric independent of the reviewer, which the design says
must exist and does not.

## Start here

- **read:** `src/ape/tasks/lean_tasks/formal_math/reviewed_proof_engineering/task.py` (syntax -> gate ->
  semantic), `.../reviewed_proof_engineering/review_gate.py`, `configs/ape_bench_reviewed_proof_engineering_pilot.yaml`,
  `src/ape/scaffolds/factory.py`, the seven run directories above.
- **run:** nothing that spends; there is no preflight form yet.
- **bounded by:** `docs/dead-ends.md` "Deferred by choice"; the user's 2026-09-22 ruling that the reviewer is not
  yet good enough, which applies with more force to a reviewer that steers a generator; the research design's T5
  (defer-to-human, risk-coverage) is selection and stays out.

## Risk

It moves nothing on the review recall wall, which is the current priority. Its value is that no future thesis
run is valid until (1)-(4) are fixed, and that the record currently says something false.
