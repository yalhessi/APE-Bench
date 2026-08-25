# R0 verdict (round 2): the two arms are not substitutable at a fixed token budget

*Run 2026-08-05, same 18 pairs, `gpt_5_mini`, decode parameters pinned to the script's
`max_tokens=1200 / thinking_budget_tokens=512`. Reports: `report-pinned-rep{1,2,3}.json`.*

## Headline: do not read the agreement numbers

| rep | issue agreement | comparable pairs | task-arm failures |
|---|---|---|---|
| 1 | 1.000 | 4/6 | 2 |
| 2 | 0.800 | 5/6 | 1 |
| 3 | 0.800 | 5/6 | 1 |

All three reps return `judge_migration_not_equivalent` — but on the **coverage** gate, not
the agreement gate. Four of eighteen pairs produced no verdict at all, so the agreement
figures above are computed on survivors and are not comparable to round 1's 77.8%.

The coverage gate did exactly the job it was added for: it refused to certify a headline
computed on a silently shrunken denominator.

## What failed, and why it matters

Every failure is `All samples failed: ['failed_model', 'failed_model', 'failed_model']` —
the model never emitted the `submit_result` tool call, three times over, and the
conversation was stopped.

The failures are not random. Cross-referencing round 1:

| | |
|---|---|
| round-1 disagreements that failed outright in round 2 | **3 of 5** |
| round-2 failures that never disagreed in round 1 | 1 |
| obligations involved | almost entirely two: `…0898b0478443`, `…4bfe0de1d5f6` |

**The pairs that fail under the tight budget are the same borderline pairs the two arms
disagreed about.** So round 2's improved-looking agreement is a selection effect: it
dropped the hard cases and scored the easy ones.

## The mechanism: the submission protocol changes the token requirement

| | script arm | task arm |
|---|---|---|
| how a verdict is returned | plain-text JSON in the reply, parsed by `parse_verdict` | an MCP `submit_result` **tool call** |
| completion at 1200/512 | 18/18 | **14/18** |
| completion unpinned | — | 18/18 |

At an identical nominal budget the task arm has strictly less room: it must fund the same
reasoning *plus* a structured tool call. Round 1 measured the task arm at 832–2752
reasoning tokens (median 1728) against a 512 budget, so on hard pairs it exhausts the
budget mid-reasoning and never reaches the tool call.

This is the substantive R0 finding, and it is sharper than "the arms disagree":

> **Matching decode parameters does not make the two arms the same judge, because they do
> not use the same submission protocol.** The migration changes how a verdict is returned,
> and that change has a token cost that falls hardest on exactly the pairs where the
> verdict is contested.

## Where this leaves the two arms

- **Round 1** (task arm unconstrained): complete coverage, internally stable (1 split
  vote in 18), but 77.8% agreement with the script — with disagreements concentrated on
  two borderline obligations and directional (3 of 4 task-looser).
- **Round 2** (task arm at the script's budget): 4/18 no-verdicts, concentrated on those
  same obligations.

Neither round establishes equivalence. Together they establish something more useful: the
contested pairs are **deliberation-dependent**. Given room to think, the judge reaches a
confident verdict that differs from the script's single 512-budget draw; denied that room,
it cannot decide at all.

## Recommended next step

Stop trying to equalise the arms by budget — that conflates two different questions. Split
them:

1. **Adopt a budget adequate for the tool-call protocol.** Round 1's usage (max 2752
   reasoning tokens) implies roughly `max_tokens: 4000`, `thinking_budget_tokens: 3000` —
   generous enough that no pair fails, bounded enough to stay cheap. Re-run for complete
   coverage. Expect agreement near round 1's, because that is the same regime.
2. **Adjudicate the residual disagreement directly, not by matching harnesses.** The
   script has one cached sample per pair, so its own per-pair distribution has never been
   measured. Sample the *script* arm three times on the ~2 contested obligations. If it
   splits, the pairs are inherently borderline and the flip rate is the R0 finding — the
   number every n≈8-denominator comparison must be read against. If it is stable at
   `issue=True` while the task arm is stable at `issue=False`, the two judges genuinely
   differ on rubric interpretation and one of them needs a human ruling.
3. **Add the contested pairs to the standing judge audit** regardless of outcome. The
   `coveringNumber_two_mul_le_externalCoveringNumber` case — gold wants the `rcases` binder
   replaced by `rfl`; the candidate calls the split dead code — is a clean test of the
   rubric's "a different fix may still issue-match" clause against its "sharing a
   declaration is not enough" clause, and reasonable readings diverge.

## Standing lesson (extends round 1's)

Round 1: "same judge" means prompt **and** decode parameters **and** model.
Round 2: it also means **the same submission protocol** — because the protocol consumes
part of the budget the reasoning needs, an ostensibly identical configuration can silently
become a harsher one.
