# Wall clock — a run is ~38 min, the manifest measures 27, and one Python scan is written twice

**Status** — open; measurement done and one claim refuted (see *Correction* below), fixes not written
**Cost** — no spend to measure; one rep to confirm any fix
**Motivating example** — A 12-PR lead run spans **~38 min** end to end, but `run_manifest.json`
records `wall_seconds: 1627` (**27.1 min**) — it times the orchestrator only, so **29% of the
process is not in its own accounting**: **89 s** of agenda build before the first agent and
**9.5 min** of finalization after the orchestrator prints its last line. A full-tree Python scan
appears **twice, in two modules** — `content_search` (**26–30%** of all arm time) and
`repository_search` (dominates the 9.5-min tail) — costing **5.4 s and 32.7 s** where `grep` takes
**0.28 s**.
**What would close it** — one subprocess-grep primitive used by both call sites, a disk cache for
the exposure scan keyed by snapshot sha, and a bounded-concurrency evidence chain. Rerun one rep and
check that run wall drops, arm findings are unchanged, and `finalization_report.json` is identical.
**Evidence** — runs `pr5_A_lead_heldout12_v2_rep{1,2,3}`; `src/ape/toolkits/file_system/core.py:329-364`;
`src/mathlib_review/evidence/evidence.py:294-316`; `src/mathlib_review/evidence/chain.py:170`;
`src/mathlib_review/agenda/exposure.py:116-158`; `src/mathlib_review/review/runner.py:1115-1313`
**Risk** — grep's regex dialect is not Python's, so a swap needs `grep -P` or a fallback, and the
results contract (`A`/`B`/`C` context, `max_matches_per_file`, `max_results`, and
`repository_search`'s 20-hit break and target-path exclusion) must be preserved exactly or the runs
stop being comparable to the recorded ones. Parallelising the evidence chain changes nothing about
ordering only if the collectors are pure; `baseline_compile_cache` and `population_cache` are shared
mutable state and would need locking or sharding.

---

## Correction — `record_turn` is real but third-order, not 21%

The first version of this entry claimed per-turn bookkeeping was **21%** of arm wall and named
`record_turn` as the cause. **That was a residual, not a measurement** — it was arm wall minus the
phases I had attributed, so it absorbed everything unmeasured, including 1-second log rounding.

Measured directly (1,172 paired `Added nodes to session` → `Recorded turn` events), the **median
write is 0.0 s at every turn depth from 1 to 12**, and the whole window totals **15.9 min**; with
the raw-response write and `_save_session` it is **~20 min, or 7% of arm wall**. Snapshot size grows
46 → 99 KB over twelve turns, which is not the runaway an O(turns²) rewrite suggests.

What *is* true: `conversation.py:257-264` writes every node from the beginning on every turn, and
across one rep's arms that is **70.0 MB written where 22.2 MB of final snapshots would do — 68%
redundant, up to 16.3× amplification**. That is worth fixing as hygiene, and it is cheap. It is not
a wall-clock lever, and it should not be scheduled ahead of the two below.

A complete gap attribution — every inter-line gap charged to the line that opened it, summing to
100% of arm wall — replaces the residual:

| | min | % of arm wall |
|---|---|---|
| `_make_request_impl:113` — LLM HTTP | 75.3 | 26.7% |
| `content_search:162` | 73.5 | 26.0% |
| `_run_lean_verification:322` — `lake env lean` | 71.7 | 25.4% |
| `_call_llm_api:966` — the `record_turn` snapshot write | 15.3 | 5.4% |
| `file_read:120` | 11.3 | 4.0% |
| `_handle_llm_response:1024` — tool dispatch | 9.5 | 3.4% |
| `record_turn:267` + `:282` — raw write, session save | 4.7 | 1.7% |
| everything else (verify, cleanup, terminate, …) | 21.1 | 7.4% |

## The process, not the orchestrator

`runner.py` runs five phases; only the middle one is timed.

| Phase | `runner.py` | Time | Share |
|---|---|---|---|
| preflight + `build_agenda` | 1115–1124 | **89 s** | 4% |
| reviewed-workspace prebuild | 1233 | ~0 s warm | — |
| `TaskOrchestrator.run` | 1242 | **27.1 min** | 71% |
| `finalize` → evidence chain | 1283 | **9.5 min** | 25% |
| manifest + summary lines | 1312–1313 | ~0 s | — |

`wall_seconds` is the orchestrator span. The orchestrator prints its own final progress line when it
finishes, and **the 9.5 min of finalization runs silently after that** — which is exactly the "long
time after the summary is printed".

Measured on `pr5_A_lead_heldout12_v2_rep1`: artifacts at 16:33:57.8, orchestrator 16:33:58 → 17:01:06,
finalization artifacts at 17:10:34.

### Startup: the same index parsed 14 times, every run

`plan` on the real 12-PR set (203 work units, 1,409 proposals — matching the manifest) takes
**89.15 s / 1.08 GB RSS**, and it does not scale with work units: the 11-PR set (95 units) took 92 s.
Under cProfile, **`agenda/exposure.py:116(_scan)` is 119.2 s of 122.5 s — 97%** — called **14 times
at 8.5 s each**, once per distinct base snapshot. Inside it: **12,340,889 `json.loads` calls**
(51.6 s), because every key of `payload["references"]` is itself a JSON string parsed just to read
`["c"]["n"]`; **104,535 file opens** (26.9 s) across ~7,440 `.ilean` files per snapshot; 59,109
`scandir` (15.3 s).

`LazyExposureScan`'s own docstring says the answer is *"a property of the snapshot rather than of the
caller"* — and snapshots are immutable and content-addressed (88 of them under
`data/code_execute/repos/mathlib4/workspaces/`). The cache is in-process only, so **every rep re-pays
the full 89 s**. A disk cache keyed by snapshot sha makes this free from the second run onward.

### Tail: a serial loop on a 64-core machine

`chain.py:170` is a plain `for candidate in candidates:` over **268 candidates**, each running up to
five collectors — `local_context` 268, `repository_search` 200, `policy` 151, `lean_compile` 102,
`issue_kind_verifier` 6. No concurrency of any kind.

`repository_search` (`evidence.py:307-316`) is **a second, independent implementation of the
full-tree Python scan** — `for path in sorted(workspace.rglob("*.lean")): path.read_text()` — in a
different module from `content_search`, with the same defect. Timed on the real workspace it is
**5.44 s per scan over 8,504 files**; ×200 candidates is 18.1 min worst case, against the 9.5 min
observed because many short-circuit at the 20-hit break or bail with
`query_has_no_identifier_terms`. `grep` does the same search in **0.28 s**.

`configs/pr_review_v5_heldout11.yaml` already records this from the cost side — *"the evidence chain
compiles and lints per candidate — measured at 8.9 s each, dominated by `repository_search`'s
full-tree scan"* — so the diagnosis is confirmed independently and is not new. What is new is that it
is the **same defect as the arms'**, and one primitive fixes both.

## Why the arm fix has to come before raising concurrency

The run peaks at **16 arms in flight** (4 outer × 4 nested, mean 10.4) on **64 cores / 1.1 TB**. The
cap's stated reason (`subtasks.py:36-39`, *"each carries its own multi-gigabyte Lean workspace
overlay"*) **does not hold for review arms**: all 120 of PR 33149's arms `target ->` symlink **one**
shared read-only checkout, zero copies, one arm attempt 261 KB, the whole run 71 MB on disk.

But `content_search` does not scale, so raising the cap first makes things worse. Driven directly its
**throughput is flat at 0.39 → 0.69 searches/s from concurrency 1 to 8**; in-run its mean goes
**2.7 s (6 arms) → 25.0 s (16 arms, p90 85 s)** while `lean_verify`'s median holds at 6–8 s. The
mechanism: a whole-tree search dispatches **~8,504 `asyncio.to_thread` calls** into the default
32-worker executor, and `aiofiles` defaults to `executor=None` — *the same pool* — so every
conversation write and file read queues behind thousands of regex tasks. Eight concurrent greps take
**0.87 s** total.

The critical path is one PR: **33149 dispatches 120 arm jobs** — the mandatory coverage floor, one
per work unit, which `lead.py:295-307` deliberately exempts from `max_delegations` — carrying 97.7 min
of arm wall at `DEFAULT_NESTED_CONCURRENCY = 4`, so 97.7/4 = **24.4 min predicted, 25.6 observed** of
a 27.1 min orchestrator span. Every other PR finishes inside 13 min.

## Suggested order

1. **One subprocess-grep primitive, used by both `content_search` and `repository_search`.** It is
   the largest arm lever (26–30% of arm time), the largest tail lever, and the precondition for
   step 3. CLAUDE.md's no-duplicate-helpers rule applies: this should land as one primitive, not two
   fixes.
2. **Bound-concurrency the evidence chain** and **disk-cache the exposure scan** by snapshot sha.
   Together these attack the 29% of the process the manifest does not even measure, and neither
   changes what the run decides.
3. **Then re-measure `DEFAULT_NESTED_CONCURRENCY`**, per-family rather than globally — the memory
   argument may still hold for families that materialise a real workspace.
4. **`record_turn` incremental writes** as hygiene, on its own merits, not for wall clock.

Also worth fixing while here: **`wall_seconds` should cover the process**, or be renamed. Every
timing number in the record is currently 71% of the truth.

## Connection to the cost todos

[Lead prompt cost](lead-prompt-cost.md) records the same PR from the spend side — 33149 is 48% of
billed cost, one 17,303-char hunk shipped to all 120 jobs, and target-scoping removes 89.9% of that
prompt section. That fix also shrinks the **LLM** bucket here, since it shrinks what all 120 arms
send. Shared root cause: **120 jobs against one oversized PR**, and neither the cost cap nor the
nested concurrency cap was designed for a PR that size.
