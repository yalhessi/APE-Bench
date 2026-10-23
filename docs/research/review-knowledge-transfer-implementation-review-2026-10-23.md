# Knowledge-transfer build: independent implementation review

**Reviewed 2026-10-23: `knowledge-transfer@0372d936`.** The build includes the operations
foundation from `review-operations@01008813` and `develop@b8959bcd`. This review checks its new
Task, session composition, recipe, evaluation export and launch instructions against the revised
[plan](../plans/2026-10-23-review-knowledge-transfer.md). No model generation, ingestion or semantic
judging ran. The implementation worktree was left unchanged.

**Recommendation:** keep the design, fix the four findings below before launching the main pilot.
The two evaluation findings can corrupt the comparison; the two operational findings make the
documented launch behavior and resource bound inaccurate. They do not call for another research
redesign or a broader prerequisite audit. The already specified live transport smokes can proceed
separately under their own limits.

## Findings

### 1. [P1] Export canonical finalized findings independently of the submission join

[The pilot export](../../.claude/worktrees/knowledge-transfer/results/pr_review_v5/probes/knowledge-transfer-2026-10-23/eval/export.py),
`delivered`, lines 55-76, builds its primary findings list by iterating
`submissions_to_findings`. That shared function is a diagnostic attribution join, keyed by
submission ordinal. Its entries are not a unique, complete list of finalized findings.

Two local reproductions exercised the actual helper and `delivered` with temporary run artifacts:

| Valid artifact situation | Rows in `findings.jsonl` | Rows exported for matching and the panel |
|---|---:|---:|
| Two anchored candidates in the same work unit share the first 200 characters of their claim | 2 | 0 |
| One finalized finding cites two submitted candidates | 1 | 2 |

The first case fails because the join in
[analysis/runs.py](../../.claude/worktrees/knowledge-transfer/src/mathlib_review/analysis/runs.py),
lines 249-254, uses `claim.startswith(anchor['claim'])`. Both truncated anchor claims match both
candidates. Both entries become `no_unique_candidate`, and the export reports both findings as
lost even though their finalized rows exist. The second case maps two submissions to the same
`finding_id` and exports it twice. The production merger deliberately combines sources when
findings ask for the same thing at the same place (`review/merge.py::_merge_group`), so this is a
supported output shape.

**Consequence:** the matcher can miss delivered concerns, and the usefulness panel and burden
counts can omit or duplicate them. Successful serialization and existing join tests do not detect
this discrepancy.

**Fix:** construct primary output from the canonical finalized rows, once per `finding_id`, under
the declared channel. Use the submission join to explain attribution and losses. An ambiguous
attribution must remain unresolved rather than remove a primary finding or count as proven loss.
Recover an anchor through existing records where possible; otherwise expose the unresolved
location explicitly. This needs no new finding identity or execution store.

**Acceptance:** retain normal one-to-one behavior; add the two situations above. Compare the exact
IDs and count in the canonical selected channel with the matcher export and frozen panel. Each
canonical finding must occur once, including when submission attribution is ambiguous.

### 2. [P1] Refuse partial or missing consumer reviews before feedback and evaluation

[analysis/probes.py](../../.claude/worktrees/knowledge-transfer/src/mathlib_review/analysis/probes.py),
`unfinished_runs`, lines 1080-1101, considers a review run finished when `findings.jsonl` exists.
The runner writes that file even when a required PR task fails and the run closes `partial`.
It is also written before the final manifest is committed to disk.

The pilot export has the same problem. Its initial guard checks for `anchoring.jsonl`; its later
empty-session guard at lines 118-122 accepts a PR with no submissions whenever the run-level
`findings.jsonl` exists. Neither establishes that the particular PR was successfully reviewed.

**Reproduction:** six temporary consumer run directories each contained a finalized finding for
36784, no successful review for 37352, and a manifest marked `partial` with that coverage gap.
The actual helpers returned:

```text
unfinished_runs(all_six_runs) = []
export.main() = 0
C1/37352 = {submitted: 0, anchored: 0, finalized: 0, lost: {}}
```

All six missing 37352 reviews were exported as empty reviews, and a usefulness panel was frozen.

**Consequence:** an outage can become a 0/3 control result or a treatment coverage loss, affecting
the investment criterion. Feedback may also be exposed while failed reviews still need to resume.

**Fix:** use the existing run state, manifest and task outcomes to require completed coverage of
the expected PRs before publishing feedback or a primary comparison. Check the expected population
as well as a terminal state. Preserve a separately identified forensic path if useful. A successful
review that submits no findings must remain valid; a failed review must remain missing.

**Acceptance:** reject a partial run, a run missing its final manifest, and a complete run over
the wrong PR population. Accept successful coverage of both pilot PRs when either review has
zero findings. Both `probe feedback --write --after` and the export need this behavior.

### 3. [P2] Make the launch recipe respect the stated total token allocation

[The protocol](../../.claude/worktrees/knowledge-transfer/results/pr_review_v5/probes/knowledge-transfer-2026-10-23/PROTOCOL.md)
states a 110M-token main-batch maximum at lines 125-126 and calls it a cap at lines 268-269.
Step 3 checks preparation use, but step 5 then starts all six consumer runs with their original
limits. No subsequent command checks cumulative use or limits these runs to the remaining
allocation.

The effective consumer config allows 32.16M per two-PR run: six runs allow 192.96M additional
tokens. Preparation use of 60M passes the checkpoint, leaving a configured total of 252.96M
before retries. The expected 20-64M main-batch usage is an estimate, not enforcement of 110M.

**Fix:** make the commands and allocation agree before launching. A small solution is to run
bounded tranches, read actual use between them, and admit the next tranche only within the
remaining allocation using existing execution limits. Alternatively allocate conservative
per-run ceilings whose sum fits the remaining budget. Account for retries explicitly. Do not
add a private generic budget manager to this probe.

**Acceptance:** a local admission/configuration check should show that a preparation result just
under the checkpoint cannot launch consumer ceilings exceeding the remaining allocation. If the
intended rule is instead a manual stop, label it as such and supply the monitoring and stopping
procedure; the current detached commands alone do not implement it.

### 4. [P2] Correct the claim that separate detached runs queue on one subscription

The protocol's step 2 starts two independent preparation units; step 5 starts six independent
review units. Lines 226-227 say they queue on the same login because `max_concurrency` is one.
That setting is per orchestrator worker, not per login or across processes
(`ape/orchestration/config.py`, `worker.py`). Both effective configs have `num_processes: 0` and
`max_concurrency: 1`; each detached command owns its own worker and queue. The supplied path has
no shared account queue.

**Consequence:** the commands permit two preparations or six final reviews concurrently, rather
than the documented one session at a time. This changes account pressure and the wall-time basis,
and makes a manual cumulative stop harder to apply.

**Fix:** use a single sequential foreground command sequence inside one detached unit, waiting for
each run before starting the next, if one active session is intended. If parallel runs are
intentional, state their actual concurrency and revise resource control accordingly. Sharing a
login does not itself supply queueing.

**Acceptance:** validate the command sequence with a non-model stub that logs start and finish;
the maximum number of simultaneously active run commands must match the protocol. This can be
fixed entirely in the recipe instructions.

## What passed independently

- **Focused checks: 97 passed.** Review-session setup and grants, sample separation/readback,
  submission attribution, probe behavior, task-data fields and schema registration.
- **Full suite: 3,213 passed** in the implementation worktree, with its `src` first on
  `PYTHONPATH`:

  ```sh
  PYTHONPATH="$PWD/src" ape/bin/python -m pytest tests -q -n auto --dist loadfile
  ```

- **Frozen verification: `status: ok`.** 717 manifest references and 1,180 locked files checked,
  no failures or unlocked files.
- **Producer preflight:** the conditional plan resolves to two PRs times three repetitions,
  `review_session`, the eight declared grants, the intended Opus route, and built reviewed
  workspaces with cutoffs 2026-03-18 and 2026-03-30. The CLI confirmed nothing ran.
- **Architecture:** the new Task extends `PacketSessionTask`, uses the shared review operations,
  and keeps output publication and observation selection on the existing session path. The
  edit-verifier extraction reuses the existing implementation. I found no reason to replace this
  composition or introduce another framework for the pilot.
- **Boundaries:** the build identifies the four worked choices and their source selection as
  development assistance; distinguishes eligible sources from sources its tools actually reach;
  and keeps the pilot's main conditions and downstream consumer contract explicit.

The successful suite does not cover the reproduced export failures. The new Task's offline tests
also substitute fixture trees for the compiled-workspace setup steps; the two planned live smokes
remain necessary to verify transport on the actual routes. No live verification or reviewing
benefit is established by this review.

## Handoff

1. Fix findings 1-2 and add the focused regressions; no new research run is needed to reproduce them.
2. Correct the allocation and scheduling instructions in findings 3-4 before the main batch.
3. Run the already specified two transport smokes, inspecting tools, source views and retained
   outputs on each route. These remain user-run.
4. Proceed with the staged pilot under its declared limits. Judge usefulness and historical
   recovery separately, using the corrected final-output export.

Do not expand the worked-example audit, add another old-fixture campaign, or rebuild the retrieval
corpus to resolve these implementation findings. Source availability and the benefit of the
candidate method remain research uncertainties for the planned test.
