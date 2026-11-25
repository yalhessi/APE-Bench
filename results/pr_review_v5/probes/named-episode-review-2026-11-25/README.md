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
| Generation record | After the change, each record also names its design. The search record also names its index identity, which matches the named history (`1a7b0736…`). Nothing else differs. |
| Final matcher message for the two saved 42184 samples, both question policies | Identical before and after for the historical solo loader and for the named projection |
| Historical loader vs named projection of the same findings | Only `severity` differs. It is `"advisory"` in the historical loader and `null` in the named projection: one line for the ordinary sample and two for the guided one. |

The saved samples are `scope_solo_opus55_42184_ordinary_20261124`, which filed one request, and `..._comparison_20261124`, which filed two, the first at line 239. Both guided requests reach the named reading, although the verified channel kept neither. The comparison fixes the reference, blind label and policy, and it says nothing about scores.

`tests/mathlib_review/test_named_reviewers.py` replays the same two submissions through `run` with a local provider. It scores them in a new process in which generation raises, and checks the matcher messages against the named files in `before/`.

## Archives written before the change

Archives written by the code at `067749d3` still reopen on the new route. The test at that commit wrote the archives, and `reopen_pre_change.py` opened them with the current code. Generation raised in that process. Both 42184 archives, one finding and two findings, reopened. Each reading prepared matcher input byte-identical to `before/`. A pre-change generation with its archive removed, the state of an interruption before archiving, was rebuilt from its `run_plan.json` into a byte-identical archive.

```bash
base=.claude/worktrees/named-baseline-check old=<scratch>/old-archives
git worktree add --detach "$base" 067749d3 && .claude/worktree-setup.sh "$base"
(cd "$base" && PYTHONPATH="$PWD/src:$PWD" ape/bin/python -m pytest -q tests/mathlib_review/test_named_reviewers.py --basetemp="$old")
cp -a "$old/test_named_reading_reproduces_0" <scratch>/reopen && rm -rf <scratch>/reopen/.ape/review-comparisons
PYTHONPATH="$PWD/src:$PWD" ape/bin/python results/pr_review_v5/probes/named-episode-review-2026-11-25/reopen_pre_change.py \
  <scratch>/reopen "$PWD/results/pr_review_v5/probes/named-episode-review-2026-11-25/before"
```

A pre-change run interrupted after acceptance also resumes. Use the folder of a test run written at `067749d3` and remove its archive. Then run `run --resume` with the current code, from the checkout that started the run. It archives the accepted session without another session. The archive is byte-identical to the original, and the pre-change `generation.json` is kept as it was. Archiving reads that run's inputs from its `run_plan.json`. The checkout matters because the generation record hashes the scaffold, whose tool paths resolve inside the checkout. That was already true before this change.

```bash
PYTHONPATH="$PWD/src:$PWD" ape/bin/python results/pr_review_v5/probes/named-episode-review-2026-11-25/resume_pre_change.py \
  "$old/test_cli_accepts_empty_review_0" solo-42184-b "$PWD"
```
