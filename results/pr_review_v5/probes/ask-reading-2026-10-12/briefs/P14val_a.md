# Brief: batch P14val_a

Read `PROTOCOL.md` in this directory first; it is the whole method. Your batch: PRs 32875, 34091, 26755, 36822
(set P14_val), 15 asks.
Packets: `packets/<set>/<pr>.json`. Write `readings/P14val_a.jsonl` and `readings/P14val_a.md`, appending after
each ask.

Order of work:
1. asks no ask-free session on disk reaches (4): v0090, v0091, v0093, v0105
2. asks where DX and AP differ (5): v0094, v0095, v0106, v0107, v0108
3. the rest (6): v0016, v0092, v0109, v0110, v0131, v0132

Setting: worktree `/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/ask-reading` (branch
`ask-reading`); in every shell `cd` there and `export PYTHONPATH=$PWD/src`; Python is `ape/bin/python`.
Read `CLAUDE.md` for the project's rules. No model spend of any kind; no git state changes; write only
under `results/pr_review_v5/probes/ask-reading-2026-10-12/readings/`. Your final message: the batch
summary from your `.md` (counts by code for DX and AP, the AP-held asks and what happened, the three
most instructive readings), at most 400 words.
