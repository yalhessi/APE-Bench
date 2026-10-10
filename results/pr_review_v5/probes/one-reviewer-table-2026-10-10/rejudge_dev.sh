#!/bin/bash
# Step 1 of docs/plans/2026-10-10-one-reviewer-table.md: every D12 run judged on gpt_5_mini before the
# 2026-10-06 move is re-judged on the current judge base (elm_gpt_5_mini, b36cd8ca) into its own
# audit node `audits/<slug>.elm`, as results/pr_review_v5/probes/judge-elm-2026-10-06/ did.
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src
source ~/.config/secrets/env.zsh 2>/dev/null
for run in probe_dev_claude_X1 probe_dev_claude_X2 probe_dev_opus55_contract2_claude_sub_rep2 probe_dev_gpt55_Grc_contract2_rep1 \
           probe_dev_opus55_contract2_hygiene_claude_sub_rep1 probe_dev_opus55_contract2_hygiene_claude_sub_rep2 \
           probe_dev_opus55_contract2_hygiene_claude_sub_rep3; do
  slug=$(echo "$run" | tr '_' '-')
  [ -f results/pr_review_v5/audits/$slug.elm/semantic_report.json ] && { echo "$run: already re-judged"; continue; }
  echo "$(date -Is) $run"
  ape/bin/python -m src.mathlib_review.review.cli judge --config configs/pr_review_v5_medium_heldout_judge.yaml \
    --of "$run" --set dataset.out_dir=results/pr_review_v5/audits/$slug.elm \
    --set dataset.run_name=pr_review_v5_judge_${run}_elm --execute 2>&1 | tail -3
done
