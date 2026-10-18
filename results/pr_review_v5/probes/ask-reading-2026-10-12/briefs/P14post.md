# Brief: batch P14post

Read `PROTOCOL.md` in this directory first; it is the whole method. Your batch: PRs 41930, 42184, 42814, 43024, 43167, 43192
(set P14_post), 16 asks.
Packets: `packets/<set>/<pr>.json`. Write `readings/P14post.jsonl` and `readings/P14post.md`, appending after
each ask.

Order of work:
1. asks no ask-free session on disk reaches (6): p0000, p0004, p0005, p0006, p0010, p0012
2. asks where DX and AP differ (4): p0007, p0008, p0014, p0016
3. the rest (6): p0002, p0003, p0009, p0011, p0013, p0015

Setting: worktree `/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/ask-reading` (branch
`ask-reading`); in every shell `cd` there and `export PYTHONPATH=$PWD/src`; Python is `ape/bin/python`.
Read `CLAUDE.md` for the project's rules. No model spend of any kind; no git state changes; write only
under `results/pr_review_v5/probes/ask-reading-2026-10-12/readings/`. Your final message: the batch
summary from your `.md` (counts by code for DX and AP, the AP-held asks and what happened, the three
most instructive readings), at most 400 words.
