# PR Review v4 0.8.4 first-run preliminary assessment

## Verdict

The run completed mechanically but is not a valid candidate-generation measurement. Do not run
evidence selection or report recall from its terminal records.

## Mechanical accounting

- 74/74 work units eventually completed: 42 in the original run and 32 in the workspace retry.
- All terminal records contain `candidates: []`.
- Recorded candidate recall is therefore 0/12 eligible atomic obligations, but this is a protocol
  artifact rather than a meaningful model score.
- Total usage across successful tasks was approximately 3.59M input tokens, 63.8k output tokens,
  and $12.21.

## Root cause

The shared renderer stored the candidate contract in `system_prompt`, but the APE agent scaffold
used its own system message and did not place the task system prompt in the actual conversation.
The model received target code without the required candidate schema. The MCP tool also exposed
candidate items as unconstrained objects.

Agents consequently submitted intuitive records using fields such as `file`, `issue`, `comment`,
and `evidence`. The task rejected those records because they lacked stable `change_ids`, a canonical
`claim`, and `evidence_requests`. Agents then discovered that an empty list was accepted and used it
to terminate. Thus the terminal empty lists do not represent their initial review judgments.

## Latent trace diagnostics

- 65/74 units attempted at least one non-empty submission before terminating empty.
- Those attempts contained 257 candidate-like objects; a coarse text heuristic classified 197 as
  issue-like, but this count is contaminated by acceptance summaries and repeated retries.
- Non-empty attempts occurred on 12/13 PR 33304 control units, 10/11 PR 33315 control units, and the
  sole PR 33438 control unit. This indicates task misunderstanding and/or severe candidate flooding,
  not measured false-positive precision.
- Every gold obligation's target unit received some non-empty activity, but exact resolution
  signatures were absent. Searches found no `round_eq_div`, `Tactic.ToFun`/`to_fun`, generalized
  `Tendsto (2 * ...)`, `isSeparated_insert_of_notMem`, requested `rfl` case split, `:= calc`,
  “isometric linear equivalence”, `ContinuousAlgEquiv.mk`, or requested line-wrap proposal.
- Manual inspection likewise found mostly unrelated suggestions or statements that the changed code
  was acceptable. Location activity must not be treated as semantic recall.

## Correction

Release `dev-pilot-0.8.5` uses renderer `candidate-prompt/4`. It embeds the full contract in the
actual user prompt and exposes a typed MCP candidate schema with required stable IDs, concern,
severity, claim, evidence requests, and optional structured edit. Regression tests assert that the
user prompt contains both the review contract and the required submission tool.

The next run must use a fresh run name and the 0.8.5 release. Version 0.8.4 remains an immutable
negative execution test and must not be merged into later candidate metrics.
