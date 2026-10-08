# Judge v9 on `elm_gpt_5_mini`: does it score as the direct judge did? (2026-10-06)

**Why.**
- The project's OpenAI key stopped working on 2026-10-05, and judge v9 ran on `gpt_5_mini` through
  it, so no new run could be judged.
- The user's decision (2026-10-06): move the judge to `elm_gpt_5_mini`, the same snapshot through
  the ELM gateway.
- The model name is in `judge_identity`, so the move forfeits the cache. Old audits stay as they
  were, and new verdicts are written under a new identity.

**Check.** Four already-judged runs were re-judged into their own audit nodes
(`audits/<run>.elm`; the judge refuses a second identity in an existing audit):

    ape/bin/python -m src.mathlib_review.review.cli judge --config configs/pr_review_v5_medium_heldout_judge.yaml \
      --of <run> --set llm_config.model_name=elm_gpt_5_mini --set llm_config.openai_api=responses \
      --set llm_config.openai_responses_reasoning_carryover=true \
      --set dataset.out_dir=results/pr_review_v5/audits/<slug>.elm --set dataset.run_name=pr_review_v5_judge_<run>_elm --execute

Pairs are keyed on (candidate, obligation), since `pair_id` carries the judge identity.

| run | pairs | issue verdicts agree | resolution agree | obligations, direct -> ELM |
|---|---|---|---|---|
| `iter_local397_contract2_dev_rep1` | 3 | 3 / 3 | 3 / 3 | 2 -> 2 |
| `iter_local397_unlock_O_rep1` | 12 | 12 / 12 | 10 / 12 | 3 -> 3 |
| `iter_local397_unlock_E_rep1` | 31 | 31 / 31 | 28 / 31 | 2 -> 2 |
| `probe_dev_opus55_contract2_claude_sub_rep1` | 30 | 27 / 30 | 28 / 30 | 7 -> 8 |
| **all** | **76** | **73 / 76 (96.1%)** | **69 / 76 (90.8%)** | |

**Reading.**
- No agreement threshold was set before the check.
- The judge's self-agreement is about 90% (CLAUDE.md), and the ELM judge agrees with the direct one
  at 96% on issue verdicts. So the two are interchangeable within the judge's own noise.
- The one obligation that moved (Opus 5.5 rep 1, 7 -> 8) is inside the stated noise of one to two
  obligations at 23.
- Carry the identity change when comparing a new run with an old one: a difference of one
  obligation between judges is noise, not a result.

**Cost.** $0.0154 + $0.0662 + $0.1773 + $0.1767 at list prices, against the ELM key's £500 limit
(£475.25 left that morning).
