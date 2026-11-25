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
