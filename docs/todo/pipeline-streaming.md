# Judging a PR while the rest of the run is still reviewing

**Status** — open, written 2026-09-21 when the stage graph landed stage-granular
**Cost** — code; it reduces wall clock rather than spend, and the judge's own resume means the
final aggregate is free
**Owner question** — is a run's finalization per-PR, or is it whole-run by necessity?

## Motivating example

`cli pipeline` starts a downstream stage as soon as the stage it reads has *closed*. That is
the honest granularity today, because the artifact a judge reads is written once for the whole
run: `finalize` (`review/finalize.py`) ingests every arm response together, merges across the
run, digests per PR only at the very end, and writes one `findings.jsonl` through `write_once`.
There is no point at which PR 33117's findings exist and PR 33149's do not.

The cost is measurable. A held-out rep is **~38 minutes** of which **9.5 minutes is
finalization that runs after the last arm line prints** (`wall-clock-arm-runtime.md`), and the
judge is a separate ~several-minute stage after that. Meanwhile the run's own spend is
dominated by one PR: **33149 is 48% of the billed cost** of a rep and **68.9%** of condition
A's findings (`lead-prompt-cost.md`, `judge-and-measurement.md` §3). A pipeline that judged the
other eleven PRs while 33149 was still running would overlap most of the judge with most of the
run.

The judge already has the property that makes this cheap: its task identity is a content hash
of the pair, so resume *is* its cache. Judging eleven PRs early and then the twelfth costs
exactly what judging all twelve costs, and the final aggregate report is the only thing that
has to wait.

## What would close it

Per-PR finalization, or a demonstration that it cannot be had:

1. whether `merge_findings` and `digest_findings` are genuinely per-PR. `_issue_key` already
   carries `pr_number`, and `pr_finding_limit` is applied per PR -- the 2026-06 defect was
   applying it to a flat list across PRs -- which suggests the merge is separable. The evidence
   chain and the lead-synthesis pass are the parts to check.
2. an artifact shape that lets a downstream stage read part of a run without reading a file
   that will later change. `write_once` forbids revision, so this is a new per-PR artifact
   rather than an incrementally-grown `findings.jsonl`; the aggregate stays what it is.
3. `StageNode` would then carry an item, and `is_done` a per-item predicate. The primitive was
   written with that in mind and does not need it today.

## Risk

The aggregate is the thing that is judged and reported. A per-PR path that produced findings
differing in any way from the whole-run path -- through the merge, the per-PR limit, or the
evidence gate -- would make a streamed run and a batch run two different systems with one name.
The first check is byte-identity of `findings.jsonl` assembled both ways on a committed run,
and if that cannot be had, the item closes as a dead end rather than shipping.
