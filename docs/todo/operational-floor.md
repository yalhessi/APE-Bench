# Operational floor — three items that can silently corrupt the next run

**Status** — open; all three are small and none is research
**Cost** — none, plus one GitHub fetch

## 1. An aborted fanout run is sitting untracked under a resumable name

`results/pr_review_v5/runs/pr5_F_fanout_heldout12_v2_rep1/` is untracked and holds a **sealed**
`run_plan.json` — `agenda_sha256 e5d0bc405a6f…`, `routing_mode: fanout`, `git_commit 3a3bf72`, tree
dirty — together with a 14 MB `arm_pool.jsonl` and 156 `context_trace` rows. That is an aborted
*run*, not a preflight artifact.

Why it matters: `TaskOrchestrator` resumes by run name. A resume under that name would seal onto a
12-PR fanout — the design `dead-ends.md` retired on 2026-09-14 — at roughly $111 nominal, and the
preflight for a fanout run reports the *lead's* floor-plus-discretionary model, which is the same
gap that already nearly cost a run.

What would close it: delete or rename the directory. Decide deliberately, because the name is the
only thing standing between it and a resume.

## 2. PR 33057's reviewed state genuinely does not compile, and nothing records that

One `unsolved goals` at `Expand.lean:35`. There is no representation for "this episode's reviewed
state cannot be built", so `prebuild --reviewed` re-attempts it on every invocation — and the
reviewed-workspace contract (`require_reviewed_workspaces`) has no way to distinguish "not built
yet" from "cannot be built".

What would close it: the cheapest of the four candidate designs is a per-episode
`reviewed_state_compiles: false` in the release, so `plan` can report it and `prebuild` can skip it.

## 3. The PR-store acceptance report is failing on one unexplained row

`inputs/pull_requests/acceptance_report.json` reads `passed: false`. The breakdown is 441
`association_changed_upstream`, **1 `unexplained`**, and one field mismatch on comment `2203417174`
(`line`, `commit_id`). The store is otherwise a strict superset: 97,661 projection rows against a
43,881-row baseline.

Why it matters: this store is the input for the fresh held-out window, which is the only thing that
can produce a generalization claim after the 12-PR set was consumed by failure analysis.

What would close it: fetch comment 2203417174 from GitHub and say whether the mismatch is a
collector bug or an upstream edit. Then commit the store extension — it is currently uncommitted
work spanning two threads, which is the pattern CLAUDE.md's standing instruction exists to prevent.

## 4. The reviewed-workspace reopen condition is half-satisfied

`dead-ends.md` says "the held-out rerun is still the check that the 16 compile claims vanish across
the set." It is now answerable and the answer splits:

- **Published phantom `broken_build` findings: 6 → 0.** `pr5_A_lead_heldout12_rep1` emitted 21
  `broken_build` findings, 6 published; the three reviewed-workspace reruns emit 5, 5 and 4, all
  `model_assertion`, all `diagnostic`, **0 published**.
- **Raw `Unknown constant` occurrences did not vanish**: 154 in the old run against 36 / 136 / 22 in
  v2 reps 1–3. Rep2 is nearly at the old level.

What would close it: classify each residual name in the three v2 reps as either introduced by the PR
under review — the stale-sibling defect, still live — or invented by the model, which is expected.
Ten distinct names across three reps; one `declaration_search` each.

## 5. `cli trajectory` silently finds no arms in runs made from a deleted worktree

Found 2026-09-15. `extract("pr5_A_lead_heldout12_rel050_rep1")` returns **0 invocations** although
the run has 206 arm rows in `execution_index.jsonl` and 218 `task_result.json` files on disk.
Every index row's `task_dir` is absolute and names
`.claude/worktrees/batching-work-units/.ape/runs/…`; that worktree has been removed, while `.ape/`
was a link into the main checkout, so the transcripts still exist at `.ape/runs/<run>/…`.
`_arm_result_paths` trusts the index when it is non-empty and never falls back to the globs, so
the result is an empty trajectory with no warning — all three `rel050` reps, which are the runs
the batching comparison rests on.

Why it matters: the worktree rule in `CLAUDE.md` makes every thread run from a worktree that is
later deleted, so this will be the common case, not an edge.

**The same deletion lost `arm_pool.jsonl` for all three `rel050` reps.** It is gitignored
(`.gitignore:43`), so merging the branch brought the tracked run artifacts across and left the pool
behind; `worktree-setup.sh` links `results/*` entries that exist at setup time, and a run created
afterwards lives in the worktree's own tree. The per-task directories keep no copy of task data.
The pool is the input any replay or re-audit of those runs needs (`replay-decision-turn.md`);
`run_plan.json`'s `prompt_sha256_by_invocation` would at least let a rebuilt pool be checked.

What would close it: resolve index paths relative to the `.ape` root (store them relative, or
re-root an absolute path whose worktree prefix is gone), and make `extract` refuse — not return
empty — when the index names directories none of which exist; and either write new run
directories through the main checkout's `results/` or refuse to remove a worktree holding an
untracked run artifact.
