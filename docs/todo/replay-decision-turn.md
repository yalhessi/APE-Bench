# Decision-turn replay — test a change to what an arm decides without re-running what it investigated

**Status** — **built, not yet run** (branch `decision-replay`, 2026-09-15); prioritised by the user 2026-09-15
**Cost** — measured at preflight, and a function of where the cut is. On v2_rep1 at 3 samples,
billed if uncached: **$37.20** from the first submission (319 sessions), **$30.44** from the last
turn (320), **$91.12** replaying each task from its prompt (320). The stage re-sampled from the
first-submission cut is $4.87 billed / $12.40 nominal per sample — see "Built" below, which
corrects the cost argument in the motivating example
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

What it unlocks first, cheapest first: verdict/reason field order in both directions — OCR found
reasoning must come first, ByteDance's BitsAI-CR measured conclusion-first better (77.1% vs 65.8%
filter precision), so the replay decides it for this model rather than either paper; abstention wording; asking for
`model_confidence` in a way that does not come back null (null on every forced finding); the
per-target disposition from `batching-work-units` follow-ups.

## Built (2026-09-15) — and where it departs from the design above

- **Replay is a way to run a task, not a task** (the user's correction, mid-build). A first cut
  subclassed the arm task; replaced by a `session_replay` task-data key, carried like
  `execution_limits`, attached at the runtime boundary and honoured by the ape_agent conversation
  manager (`src/ape/scaffolds/ape_agent/replay.py`). The replayed task keeps its type and id, so
  any task family can be replayed and a replayed arm's results are ordinary arm results. Only the
  cut point and the submission summary are review code (`src/mathlib_review/review/replay.py`).
- **The cut is a parameter, not a policy** (the user's second correction). `CutPoint` names any
  point in a recording — an assistant turn from either end (`turn=-1`, `turn=1`), a raw node index,
  or a tool call — resolved per session, and refused per session when it cannot resolve or would
  land inside a turn. The decision turn is one choice of cut, not what the system is. One task
  identity per session means **one cut per run**, so the run name carries the cut label, and
  `report replay --against` states whether it compared conditions (same cut) or cuts (same
  condition). Measured on v2_rep1: `turn=-1` and `tool=submit_candidates:last` are the same 320
  sessions; `node=7` lands mid-turn in 232 of them, which is why a node index is the last resort.
- **Within the decision-turn cut it is the *first* `submit_candidates`, not the terminal one**
  (step 2 above). 26 / 31 / 28 of the 321 / 316 / 322 v2 sessions had a first submission refused
  and repaired; the task counts refusals on its instance and a replayed instance starts at zero,
  so only a prefix with no submission agrees with the live contract. Repairs are re-sampled with
  the decision.
- **The cost argument was overstated.** "One cached-prefix turn instead of a whole rep" is true
  of turns, not dollars: the decision turn carries the whole investigation as input, so the
  recorded decision stage is ~38% of arm billed spend per sample ($4.87 of $12.83 on v2_rep1) and
  nearer all of it uncached. What replay buys is **the investigation held fixed** — the noise
  argument — plus wall clock and selectability (one arm, one PR), not an order of magnitude.
- Also built on the way: a per-task `execution_limits.max_turns` was recorded on the Attempt and
  never bound the conversation (`d329b13`); arm pools were invisible in worktrees
  (`.claude/worktree-setup.sh` now links them).
- **Not built:** feeding replayed candidates through finalize and the judge (step 6's second
  half). Outcomes are compared at the submission level only — filed/abstained, abstention reason,
  anchors, candidate keys — which needs no judge and no gold.

Run it (preflight without `--execute`; `--cut turn=N|node=I|tool=NAME[:first|:last|:N]`
replaces the config's cut, while `--set dataset.cut=` deep-merges and leaves two spellings,
which is refused):

```
R="ape/bin/python -m src.mathlib_review.review.cli"
$R replay --config configs/v5_replay.yaml --of pr5_A_lead_heldout12_v2_rep1 \
    --run-name pr5_replay_null_first_submit_candidates_v2_rep1 --execute
$R replay --config configs/v5_replay.yaml --of pr5_A_lead_heldout12_v2_rep1 --cut turn=-1 \
    --run-name pr5_replay_null_last_turn_v2_rep1 --execute
$R report replay --run pr5_replay_null_first_submit_candidates_v2_rep1
$R report replay --run <condition run> --against pr5_replay_null_first_submit_candidates_v2_rep1
```

## What would close it

**Revised 2026-09-21, after the user refused the price.** The original condition was a null
replay of all 319 sessions, quoted at $37.20. Two things were wrong with it. The figure was the
*uncached* price: the case-study run measured billed/nominal = **0.48** (samples of one prefix
run back-to-back hit the provider cache), so it is ~$15-18 billed. And a standalone null buys
almost nothing — a condition experiment carries its own control on the same prefixes, and a
noise floor paid for today is only reusable while the model, the code and the session set stand
still, which this project already treats as a new-run-name event. Most of that $18 covered
sessions where nothing is contested: the generalist is 203 of 319 sessions and 69% of the cost,
and PR 33149 alone is 53%.

So the closing condition is the measurement that changes what we fund next:

**The diagnostic — $2.59 billed.** The 45 specialist invocations whose work unit carries a
*required gold* change and that abstained in `pr5_A_lead_heldout12_v2_rep1`, replayed at the
first-submission cut, 3 samples each under `null` (nominal $5.40; 0.48 cache ratio measured).
Every one is a site where a maintainer asked for something, an arm looked, and it said nothing.
The run splits them into

* **decision-limited** — some sample files instead of abstaining, so a bar, forcing or
  elicitation change can recover it (the `naming` 33337 session: the gold rename, 2 of 5); and
* **contract-limited** — every sample abstains identically, so no decision-stage change touches
  it, only a contract, prompt or investigation change (the `correctness` 33149 session on the
  axioms file: 5 of 5, established for $0.02).

At 3 samples the decision-limited fraction is a **lower bound** (a session that flips one time
in five is caught about half the time), which is the safe direction for deciding what to fund.
It measures *instability*, not recall: whether a flip produces the maintainer's ask needs the
judge or a hand read.

**Then, per condition, ~$5.20:** the condition and its null on those same 45 prefixes, run in
one window so both see the same code and the same cache, against $14.50 for two full reps plus
judge noise.

Priced from the recorded decision stages, billed at the measured 0.48 ratio, 3 samples:

| population | sessions | billed |
|---|---|---|
| everything (the old condition) | 319 | $17.85 |
| specialists only | 116 | $5.54 |
| **specialists at gold sites that abstained** | **45** | **$2.59** |
| specialists at gold sites (incl. the 10 that filed) | 55 | $3.16 |
| cross-rep unstable specialists (biased subset) | 23 | $1.14 |

Free before any of it: across the three v2 reps, **23 of 89** specialist invocations flip
filed/abstained — an *upper* bound on decision instability, since it also contains investigation
variance. The diagnostic says how much of that is the decision alone, at the sites where a flip
would change recall.

**What the cheap version gives up**, stated so a later reader does not overclaim: no run-level
recall number, no judge, and a floor measured only on abstaining specialists at gold sites — a
condition aimed at filing behaviour or at the generalist needs its control drawn from that
population instead. Gold-based selection is in-sample, which is fine for a diagnostic and is not
a precision claim.

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
