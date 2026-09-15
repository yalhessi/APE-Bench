# Decision-turn replay — test a change to what an arm decides without re-running what it investigated

**Status** — open; **prioritised by the user 2026-09-15** ("worth adding to our system asap")
**Cost** — code; then one cached-prefix turn per replayed session instead of a whole rep
**Owner question** — how cheaply, and with how little noise, can a decision-stage change be measured?

## Motivating example

The decision, not the investigation, is where this system's findings go missing:

- **Forcing the decision alone took issue recall 0.20 → 0.50** (location 0.80 → 1.00) on the same 4
  held-out PRs, strictly dominating — 3 forced-only hits, 0 unforced-only. `naming` produced
  `Dense.upperBounds_image`, character for character the gold rename, on an obligation it had
  abstained on (`dead-ends.md`, "Specialists as the coverage floor", amended 2026-09-14).
- **Abstaining arms investigate as much as filing ones**: median 6.0 tool calls before an empty
  submission against 7.0 before a finding, n=95/23 (`.claude/rules/mathlib-review.md`, "Last tool
  before submit").
- **The arm can hold the right answer and not pick it**: on 33098 rung 3c it compiled
  `grind [minimalCover]` — the maintainer's request — and submitted `simpa [...]` instead
  (`review/candidates.py:163-169`, the reason `rejected_alternatives` exists).

Yet every change aimed at that decision — abstention wording, the bar, field order, confidence
elicitation — is tested with a full rep: **$7.26 billed and ~38 minutes** per held-out rep
(`docs/research/batching-and-prompt-repair-2026-09.md`; `wall-clock-arm-runtime.md`), with the
investigation re-sampled too, read through a judge that splits its own vote on ~11% of pairs
(`judge-and-measurement.md` §2). A decision change therefore competes with investigation variance
it did not cause.

**External precedent.** open-code-review settled its review-filter fix by replaying all 455 recorded
filter calls with unchanged inputs: precision 36% → 88%, real findings deleted 8 → 0
(`alibaba/open-code-review@c8b6a39`; `docs/research/open-code-review-comparison-2026-09.md`). The
same replay found that a verdict field serialised before the reasoning field could not be
retracted — a schema property no end-to-end run would have isolated.

## The design

1. **Select** recorded arm sessions from a finished run through `execution_index.jsonl`, never by
   globbing (CLAUDE.md, "Reading run artifacts").
2. **Truncate** each `ape_agent_session_*.jsonl` (`scaffolds/ape_agent/conversation.py:233`, the
   append-only full session) at the last assistant node *before* the terminal `submit_candidates`
   call. Everything the arm read stays byte-identical.
3. **Rebuild the task** from the run's `arm_pool.jsonl` payload for that `invocation_id`, so
   `submit_candidates` validates against the same `change_ids`, subjects and entity maps.
4. **Swap exactly one thing** — the tool schema (field order, required-ness), the closing
   instruction, or the abstention contract — and **resume** through the existing path
   (`resume_or_create_session`, `conversation.py:367-408`; `_create_session_from_existing` already
   drops an incomplete trailing assistant turn). Cap the replay at a couple of turns.
5. **Resample N times per session** and record, per session: candidates, abstention reason and
   detail, `model_confidence`, and whether a submission was refused. Write it as a normal
   orchestrator run under its own `--run-name` so it resumes and reports like everything else
   (`TaskOrchestrator`, not a loop).
6. **Report** the paired difference per session (same prefix, old vs new decision) and pass the
   emitted candidates through the existing merge and judge, so recall and control-PR emission are
   read on the same scale as a rep.

What it unlocks first, cheapest first: the reason-before-verdict field order (`abstention_detail`
before `abstention_reason`, `claim` before `severity`); abstention wording; asking for
`model_confidence` in a way that does not come back null (null on every forced finding); the
per-target disposition from `batching-work-units` follow-ups.

## What would close it

A replay run on `pr5_A_lead_heldout12_v2_rep1` that (a) reproduces the original submission when
nothing is swapped — the null replay, at a rate that sets its own noise floor — and (b) reports one
swapped condition against it. Without (a), no replay difference can be read.

## Evidence

- Session and resume machinery: `src/ape/scaffolds/ape_agent/conversation.py:227-289` (three files
  per turn), `:313-335` (`find_latest_session_path`), `:367-465`.
- Replayable inputs exist for `v2_rep1-3`: `arm_pool.jsonl` 14 MB each, 332 / 327 / 334 session
  files.
- **Not for `rel050_rep1-3`**: 218 / 216 / 221 session files but `arm_pool.jsonl` is missing, and
  their index paths point into a deleted worktree — `operational-floor.md` §5.

## Risk

- **A replayed decision sits on an investigation shaped by the old contract.** It measures the
  decision, not an investigation the new contract would have caused; a change meant to alter what
  arms look at still needs a rep.
- **Resampling one turn is not independent of the prefix.** Report per-session paired outcomes, not
  pooled rates, and replicate across the three `v2` reps before believing a delta.
- **`submit_candidates` compiles checkable edits** (`verify_checkable_edits`), so a replay needs the
  reviewed workspaces the original run used; cost is compile time, not model spend.
- **Provider cache affinity.** The cost argument assumes the prefix is served from cache; a replay
  weeks later pays the prefix once uncached per session. Measure billed cost on the first replay.
