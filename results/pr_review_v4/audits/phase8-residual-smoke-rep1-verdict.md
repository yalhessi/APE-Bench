# Phase 8 residual-review smoke rep1 verdict

## Verdict

Execution and ingestion pass, but residual discovery fails its semantic smoke gate. Do not run the
semantic judge, merge these candidates into synthesis, or expand the residual pass yet.

The two work units completed successfully and produced three candidates, but deterministic evidence
supports none of them. Selection consequently publishes zero findings. The result is safe only
because the downstream evidence gate rejects the generator's output; the residual generator itself
did not recover useful novelty.

## Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Execution | Pass | 2/2 terminal responses succeeded. |
| Ingestion | Pass | 3 candidates from 2 PR units; report is complete. |
| Verification discipline | Fail | Both responses contain zero verification artifacts. |
| Evidence support | Fail | 0/3 candidates supported; all packets are inconclusive. |
| Selection | Pass as safety gate | 0/3 candidates selected. |
| Positive recovery | Fail | PR 33098 produced one false correctness claim and no issue match. |
| Control precision | Fail | Control PR 33438 produced two false blocking correctness claims. |

## Candidate inspection

### PR 33098

The candidate claims that `ring_nf` cannot reliably establish the NNReal equality in
`Metric.coveringNumber_subset_le`. The reviewed file compiles, with no target-local diagnostic. The
gold obligation at this exact location asks for a calc-layout style rewrite, not a correction to the
ring step. This is a location overlap but an issue and resolution miss.

### PR 33438 control

Both candidates claim that an `all_goals` block with one bullet fails to discharge the goals created
by `arctan_tan`. The reviewed file compiles. In Lean, the tactic after `all_goals` is applied to every
remaining goal; the candidates misread the tactic structure. Worse, both proposed replacement
declarations fail compilation. The evidence assertions therefore contradict the proposed edits.

## Root cause

Each agent called `lean_verify` with a `target/...` path. That tool only accepts files in the scratch
workspace and returned an error. The available `lean_verify_edit` tool was not used, and terminal
submission accepted the candidates anyway. Prompt-level requests to verify are therefore not an
enforced invariant.

The residual task also turns "uncovered" inventory into pressure to invent a concern. On the control,
this converted an unfamiliar but valid tactic pattern into two blocking findings. This is the same
search-allocation problem the opportunity pipeline is meant to solve, now appearing in the residual
fallback.

## Decision

Keep deterministic Phase 8 synthesis, but stop the current residual-review path. Before another
model run:

1. Compile the baseline through `lean_verify_edit(path=...)` before accepting a correctness claim
   about compilation or proof validity.
2. Compile every proposed Lean edit; reject terminal submission when verification is absent, failed,
   or contradictory.
3. Require a target-local baseline diagnostic for blocking correctness claims. Treat unsupported
   brittleness claims as abstentions, not blocking findings.
4. Persist verification artifacts in the response and make ingestion reject candidates that violate
   these contracts.
5. Carry completed `no_request` outcomes into residual review as exclusions unless the agent supplies
   new contrary evidence.

Rerun the same two-PR smoke after these changes. Its minimum gate is: zero control candidates, no
unsupported candidates, and at least one genuinely supported positive candidate before expansion.

## Inspection commands

```bash
jq . results/pr_review_v4/runs/phase8-residual-smoke-rep1/ingested/report.json

jq -s 'map({candidate_id, pr_number, claim, proposed_edit})' \
  results/pr_review_v4/runs/phase8-residual-smoke-rep1/ingested/candidates.jsonl

jq -s 'map({candidate_id, status})' \
  results/pr_review_v4/runs/phase8-residual-smoke-rep1/ingested/evidence/packets.jsonl

jq -s 'map({candidate_id, assertion_scope, polarity, claim})' \
  results/pr_review_v4/runs/phase8-residual-smoke-rep1/ingested/evidence/assertions.jsonl

wc -l results/pr_review_v4/runs/phase8-residual-smoke-rep1/ingested/findings.jsonl
```

Do not run the paid semantic judge on this repetition; deterministic compilation already disposes of
all three candidates.
