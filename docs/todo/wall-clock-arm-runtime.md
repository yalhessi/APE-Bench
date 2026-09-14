# Wall clock — a 27-minute run spends a quarter of its agent time on 130 greps

**Status** — open; the measurement is done, the fixes are not
**Cost** — no spend to measure further; one rep to confirm any fix
**Motivating example** — Across three reps of the 12-PR heldout set, **26–30% of all arm wall time
is `content_search`**, and **96% of that is 123–132 whole-tree scans of `target/Mathlib`** at a mean
of **32.7 s each**. `grep -rE` over the same 8,504-file, 65 MB tree returns in **0.28 s**. The tool
is not slow because the search is hard; it is slow because it reads every file into Python and
dispatches a per-file regex into a 32-worker thread pool.
**What would close it** — replace the per-file scan in `content_search` with one subprocess grep,
rerun one rep, and check that (a) run wall drops and (b) arm findings are unchanged. Then, and only
then, re-measure whether `DEFAULT_NESTED_CONCURRENCY` can be raised.
**Evidence** — runs `pr5_A_lead_heldout12_v2_rep{1,2,3}`; `src/ape/toolkits/file_system/core.py:329-364`;
`src/ape/orchestration/subtasks.py:39`; `src/ape/scaffolds/ape_agent/conversation.py:257-264`
**Risk** — grep's regex dialect is not Python's. Some arm patterns use Python-specific syntax, so a
swap needs `grep -P` or a fallback, and the results contract (`A`/`B`/`C` context lines,
`max_matches_per_file`, `max_results`) has to be preserved exactly or arm behaviour changes and the
run is no longer comparable to the recorded ones.

---

## Where the 27 minutes go

Run wall is **26.0 / 26.6 / 27.1 min** across the three reps. It is set almost entirely by one task.

**The critical path is PR 33149's delegation wave.** That lead dispatches **120 arm jobs** — the
mandatory coverage floor, one per work unit, which by design is not charged against
`max_delegations` (`lead.py:295-307`). Those 120 arms carry **97.7 min** of summed wall and run at
`DEFAULT_NESTED_CONCURRENCY = 4`, so the wave takes 97.7/4 = **24.4 min predicted, 25.6 min
observed** — of a 27.1 min run. Every other PR finishes inside 13 min.

**The arm time budget**, summed over ~320 arms per rep and stable across all three:

| | rep1 | rep2 | rep3 |
|---|---|---|---|
| LLM API | 26.7% | 27.1% | 28.8% |
| `content_search` | 26.4% | 29.8% | 28.6% |
| — *of which whole-tree* | *25.5%* | *29.4%* | *27.7%* |
| `lean_verify` (`lake env lean`) | 25.4% | 20.6% | 19.8% |
| per-turn bookkeeping / IO | 20.9% | 22.1% | 22.3% |
| `file_read` | 0.5% | 0.4% | 0.4% |

Only about a quarter of arm time is the model thinking. Another quarter is a grep that should be
free, and a fifth is writing conversation files.

## Why raising concurrency is not the first move

The obvious fix — the machine has **64 cores and 1.1 TB of RAM**, and the run peaks at **16 arms in
flight** (4 outer × 4 nested), mean **10.4** — is to raise the nested cap. The stated reason it is 4
is in `subtasks.py:36-39`: *"each carries its own multi-gigabyte Lean workspace overlay."* **That is
not true of review arms.** All 120 of 33149's arms `target ->` symlink **one** shared read-only
checkout; there are zero real copies, one arm attempt is 261 KB, the whole 33149 attempt is 28 MB,
and the entire 12-PR run is 71 MB on disk.

But concurrency will not buy what it looks like it will, because **`content_search` does not scale**.
Measured in-run, mean duration against simultaneous arms:

| arms in flight | 6 | 8 | 10 | 12 | 16 |
|---|---|---|---|---|---|
| `content_search` mean | 2.7 s | 4.4 s | 11.6 s | 14.0 s | **25.0 s** (p90 85 s) |
| `lean_verify` median | 7 s | 7 s | 7 s | 6 s | 8 s |

Lean is flat — it is subprocesses on 64 cores. `content_search` degrades roughly 10×. Driven
directly, its **throughput is flat at 0.39 → 0.69 searches/s from concurrency 1 to 8**: extra
concurrency buys nothing and just makes each call proportionally slower. Eight concurrent greps over
the same tree take **0.87 s total**.

The mechanism is one saturated thread pool. A whole-tree `content_search` dispatches **~8,504
`asyncio.to_thread` calls** — one per `.lean` file — into the default 32-worker executor
(`core.py:343-354`). `aiofiles` defaults to `executor=None`, which is *the same pool*. So every
conversation write and file read in every concurrent arm queues behind thousands of regex tasks.
That also explains the 21% bookkeeping bucket: **3.2 s per turn** to write a 68 KB file.

Raising the nested cap before fixing this would push more arms onto the resource that already does
not scale.

## A third, independent waste: `record_turn` rewrites the whole conversation every turn

`conversation.py:257-264` writes *"every node from the beginning through the current turn"* into a
fresh file each turn, one `await f.write()` per node. It is O(turns²) and the session file is
already append-only. Across one rep's arms: **70.0 MB written where 22.2 MB of final snapshots would
do — 68% redundant**, and up to **16.3× amplification** on the longest conversations (24 turns,
1,753 KB written, 107 KB final).

## Suggested order

1. **`content_search` → one subprocess grep.** Removes ~26–30% of all arm work, and is the
   precondition for anything else, since it is what currently punishes concurrency.
2. **`record_turn` → write only new nodes.** Removes most of a 21% tax on the same thread pool.
3. **Then re-measure `DEFAULT_NESTED_CONCURRENCY`.** With 1 and 2 done, 33149's wave is ~61.6 min of
   genuinely parallel work (LLM + Lean); at 12 that is ~5 min rather than 24.4. Raise it for the
   review families only — the constant's memory argument may still hold for task families that
   materialise a real workspace, so it should become per-family rather than global.

## Connection to the cost todos

[Lead prompt cost](lead-prompt-cost.md) records the same PR from the spend side — 33149 is 48% of
billed cost, one 17,303-char hunk shipped to all 120 jobs, and target-scoping removes 89.9% of that
prompt section. That fix should cut the **LLM API** bucket here too, since it shrinks what every one
of those 120 arms sends. The two items share a root cause: **120 jobs against one oversized PR**,
and neither the cost cap nor the nested concurrency cap was designed with a PR that size in mind.
