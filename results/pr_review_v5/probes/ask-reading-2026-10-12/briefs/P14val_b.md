# Brief: batch P14val_b

Read `PROTOCOL.md` in this directory first; it is the whole method. Your batch: PRs 28649, 29842, 30458, 30641
(set P14_val), 15 asks.
Packets: `packets/<set>/<pr>.json`. Write `readings/P14val_b.jsonl` and `readings/P14val_b.md`, appending after
each ask.

Order of work:
1. asks no ask-free session on disk reaches (2): v0053, v0056
2. asks where DX and AP differ (6): v0029, v0030, v0031, v0062, v0063, v0066
3. the rest (7): v0055, v0060, v0061, v0064, v0065, v0067, v0068

Setting: worktree `/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/ask-reading` (branch
`ask-reading`); in every shell `cd` there and `export PYTHONPATH=$PWD/src`; Python is `ape/bin/python`.
Read `CLAUDE.md` for the project's rules. No model spend of any kind; no git state changes; write only
under `results/pr_review_v5/probes/ask-reading-2026-10-12/readings/`. Your final message: the batch
summary from your `.md` (counts by code for DX and AP, the AP-held asks and what happened, the three
most instructive readings), at most 400 words.
