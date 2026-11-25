# Named review from the episode alone on PR 42184

25 November 2026. `run --reviewer` now goes from a reviewed episode to the accepted submission. It no longer builds a specialist agenda or run plan, and it does not continue into anchoring or finalization. This directory records the reviewer's input and the matcher's input for 42184 at `c5474cb4`, before and after the change. [Plan](../../../../docs/plans/2026-11-25-named-whole-pr-review.md) · [Decision](../../../../docs/adr/0002-run-named-reviewers-on-episodes.md)

`before/` was captured at `067749d3`, the merged baseline. `after/` was captured on the changed route. Both used the same command, the pinned Mathlib workspace and the frozen search index. No model was called.

```bash
export PYTHONPATH="$PWD/src:$PWD"
ape/bin/python results/pr_review_v5/probes/named-episode-review-2026-11-25/capture.py <new-folder>
diff -r results/pr_review_v5/probes/named-episode-review-2026-11-25/before <new-folder>
```

| What was compared | Result |
|---|---|
| First message and tool schemas, `solo-v1` and `pr-search-v1`, profile release vs a release holding only `input/episodes.jsonl` | Identical in all four previews, before and after |
| Tool grants | Search adds only `precedent_search` |
| Generation record | Identical before and after. The run's design and, for search, its granted index (`1a7b0736…`) are written to a separate `inputs.json` before the reviewer is dispatched, and `plan` prints them. |
| Final matcher message for the two saved 42184 samples, both question policies | Identical before and after for the historical solo loader and for the named projection |
| Historical loader vs named projection of the same findings | Only `severity` differs. It is `"advisory"` in the historical loader and `null` in the named projection: one line for the ordinary sample and two for the guided one. |

The saved samples are `scope_solo_opus55_42184_ordinary_20261124`, which filed one request, and `..._comparison_20261124`, which filed two, the first at line 239. Both guided requests reach the named reading, although the verified channel kept neither. The comparison fixes the reference, blind label and policy, and it says nothing about scores.

`tests/mathlib_review/test_named_reviewers.py` replays the same two submissions through `run` with a local provider. It scores them in a new process in which generation raises, and checks the matcher messages against the named files in `before/`.

## Archives written before the change

Archives written by the code at `067749d3` still reopen on the new route, and a run that code left unfinished still resumes. The test at that commit wrote them, with one correction: its local provider built a task result by hand, which lacked fields every real task result carries (`task_id`, `task_type`, `global_index`, `score`). APE's own reconciliation refuses such a result, so the provider was changed to build its result through the task's result class, as the submission tool does. No other line of the earlier code changed. A new session raises in the processes below.

- `reopen_pre_change.py` reopens both 42184 archives, with one finding and with two. It prepares both readings, whose matcher input is byte-identical to `before/`. It then removes the guided archive, the state of an interruption before archiving, and rebuilds it from the run's `run_plan.json` byte for byte.
- `resume_pre_change.py` removes a finished run's archive and resumes it with `run --resume`. The run is resumed from the checkout that started it, because the generation record hashes the scaffold, whose tool paths resolve inside the checkout. That was already true before this change. APE completes the task's missing outcome record without a session, and no credential is needed. The archive is the original apart from the digest of the `inputs.json` the resume now records. Every archived file is unchanged, and the recorded design agrees with the run plan the earlier code sealed.

```bash
base=.claude/worktrees/named-baseline-check old=<scratch>/old-archives
git worktree add --detach "$base" 067749d3 && .claude/worktree-setup.sh "$base"
# In tests/mathlib_review/test_named_reviewers.py, build `raw` with task.create_result(success=True, score=1.0,
# pr_number=..., review_message=..., findings=..., submitted_findings=...).model_dump(mode="json").
(cd "$base" && PYTHONPATH="$PWD/src:$PWD" ape/bin/python -m pytest -q tests/mathlib_review/test_named_reviewers.py --basetemp="$old")
cp -a "$old/test_named_reading_reproduces_0" <scratch>/reopen && rm -rf <scratch>/reopen/.ape/review-comparisons
PYTHONPATH="$PWD/src:$PWD" ape/bin/python results/pr_review_v5/probes/named-episode-review-2026-11-25/reopen_pre_change.py \
  <scratch>/reopen "$PWD/results/pr_review_v5/probes/named-episode-review-2026-11-25/before"
# Then, with the current code checked out in "$base":
(cd "$base" && git checkout --detach <this branch> && PYTHONPATH="$PWD/src:$PWD" ape/bin/python \
  <this checkout>/results/pr_review_v5/probes/named-episode-review-2026-11-25/resume_pre_change.py \
  "$old/test_cli_accepts_empty_review_0" solo-42184-b "$PWD")
```

Both scripts fail with an assertion if any compared byte differs.
