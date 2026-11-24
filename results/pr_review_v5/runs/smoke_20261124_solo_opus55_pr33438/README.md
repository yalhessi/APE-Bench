# One-PR smoke run of the solo reviewer

On 24 November 2026, `develop` at `358a95ab` ran the normal APE review CLI on Mathlib PR 33438, a 24-line development control with a prebuilt reviewed workspace. Claude Opus 5.5 ran on the Claude Code subscription route using CLI 2.1.285. The one task succeeded on its first attempt. APE recorded 384 seconds, eight turns, 153,688 processed tokens and $0 in per-token charges. The containment audit recorded `clean` and `usable`. [Run plan](run_plan.json) · [Run manifest](run_manifest.json) · [Reviewed workspace](reviewed_workspaces.json)

The reviewer suggested shortening `Real.arctan_sqrt_three` and `Real.arctan_inv_sqrt_three` with `arctan_eq_of_tan_eq`. Each final `requested_change` matches a replacement declaration that returned `compiled` in the saved Lean tool results, after trimming outer whitespace. The two declaration searches and the precedent lookup appear in the [context trace](context_trace.jsonl). Both findings anchored. The finalizer retained both as advisory findings in the `review` channel and counted zero in `verified` or `published`. Their concern family was `other`, for which the evidence collector reported no support. The task's successful submission is a runtime result. This smoke run includes no semantic judge or convention-guided comparison. [Final findings](findings.jsonl) · [Anchoring report](anchoring_report.json) · [Finalization report](finalization_report.json)

The initial preflight identified a missing `lake` on `PATH`. The successful invocation set `ELAN_HOME` and added its `bin` directory. The MCP server logged a cancellation during shutdown after the successful sample. The CLI finished anchoring and finalization and exited zero. To repeat on this checkout, run the following in zsh from the repository root. A new run name preserves the original sample.

```zsh
source ~/.config/secrets/env.zsh
unset OPENAI_API_KEY ANTHROPIC_API_KEY OPENAI_ELM_API_KEY
export ELAN_HOME=/research/projects/proofedit/ya475/.elan
export PATH="$ELAN_HOME/bin:$PATH" PYTHONPATH=src
ape/bin/python -m src.mathlib_review.review.cli run \
  --config configs/pr_review_v5_dev_medium_opus55_contract2_claude_sub.yaml \
  --run-name "smoke_solo_opus55_pr33438_$(date -u +%Y%m%dT%H%M%SZ)" \
  --set 'dataset.pr_numbers=[33438]' \
  --set execution.max_concurrency=1 \
  --set dataset.solo_token_cap=600000 \
  --execute
```
