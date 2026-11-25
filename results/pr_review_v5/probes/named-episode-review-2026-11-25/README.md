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

Archives written by the code at `067749d3` still reopen on the new route, and a run that code left unfinished still resumes. The test at that commit writes them, with one correction in `pre-change-provider.patch`. Its local provider built the task result by hand, and that result lacked fields every real task result carries (`task_id`, `task_type`, `global_index`, `score`). APE's reconciliation refuses such a result. The patch builds the result through the task's result class, as the submission tool does, and changes nothing else. A new session raises in both checks below, and each check fails on any differing byte.

- `reopen_pre_change.py` reopens both 42184 archives, with one finding and with two. It prepares both readings, whose matcher input is byte-identical to `before/`. It then removes the guided archive, the state of an interruption before archiving, and rebuilds it from the run's `run_plan.json` byte for byte.
- `resume_pre_change.py` removes a finished run's archive and resumes it with `run --resume`, with no credential. It must run from the checkout that started the run, because the generation record hashes the scaffold, whose tool paths resolve inside the checkout. That was already true before this change. APE completes the task's missing outcome record without a session. The generation record is unchanged, no `inputs.json` is written because the run plan sealed the inputs, and the archive is byte-identical. The script restores the folder afterwards, so it can be run again.

From the root of this branch's checkout, in zsh or bash. The block runs in a subshell that stops at the first failure. It creates its worktree under a new temporary folder, so it never touches an existing one, and removes it on exit, whether the checks pass or fail.

```bash
(
  set -e
  export PYTHONPATH="$PWD/src:$PWD"
  repo=$PWD
  probe=$repo/results/pr_review_v5/probes/named-episode-review-2026-11-25
  scratch=$(mktemp -d)
  base=$scratch/baseline old=$scratch/old-archives
  git worktree add --detach "$base" 067749d3
  trap 'git -C "$repo" worktree remove --force "$base"' EXIT
  .claude/worktree-setup.sh "$base"
  git -C "$base" apply "$probe/pre-change-provider.patch"
  (cd "$base" && PYTHONPATH="$base/src:$base" ape/bin/python -m pytest -q tests/mathlib_review/test_named_reviewers.py --basetemp="$old")
  cp -a "$old/test_named_reading_reproduces_0" "$scratch/reopen"
  rm -rf "$scratch/reopen/.ape/review-comparisons"
  ape/bin/python "$probe/reopen_pre_change.py" "$scratch/reopen" "$probe/before"
  git -C "$base" checkout -- .
  git -C "$base" checkout --detach named-episode-review
  (cd "$base" && PYTHONPATH="$base/src:$base" ape/bin/python "$probe/resume_pre_change.py" \
    "$old/test_cli_accepts_empty_review_0" solo-42184-b "$base")
  echo "pre-change checks passed"
)
```
