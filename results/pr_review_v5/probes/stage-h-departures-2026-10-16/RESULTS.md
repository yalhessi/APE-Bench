# The 5% at its source: results

## Step 1: stage H's places followed to merge (`follow.py`, `follow.jsonl`)

| | n | unchanged | changed | gone | unlocated | no merge in clone | changed or gone, of located |
|---|---|---|---|---|---|---|---|
| asked places (validity) | 6 | 0 | 1 | 3 | 1 | 1 | **4 of 4** |
| unasked places | 199 | 100 | 23 | 22 | 13 | 41 | **45 of 145 = 31%** |
| baseline: other declarations the round-1 diff touched | 14 | 11 | 3 | 0 | 0 | 0 | 3 of 14 = 21% |

By rule, unasked, changed or gone: P005 46%, P011 43%, P254 41%, P040 36%, P048 33%, P084 33%, P126 24%,
P018 20%, P100 19%, P010 18%. By the pinpointer's status: `check` 31%, `departs` 33%.

**Read by the rule.** Validity passes: every asked place on a merged PR was changed or removed. The unasked
places against the baseline read "within 10 points" (31% against 21%), but **the baseline cannot bear the
reading**: the pinpointer flagged most of the declarations each PR touched (on PR 31081's new file, 3 of 3),
so only 14 unflagged touched declarations exist on the 13 merged PRs. What step 1 does establish: **100 of
the 145 located unasked places (69%) reach merge byte-for-byte unchanged**, and no rule has a majority of its
places changed. Whether those 100 are conforming code, places outside the rule, or departures nobody asked
about is step 2's question; "gone" includes renames and moves, so the 31% is an upper bound on fixes.
