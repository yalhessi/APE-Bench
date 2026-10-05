#!/usr/bin/env bash
# One cross-model run: gpt-5.5 at high effort, reasoning carried, through ELM, on a probe set's PRs
# with asks, unbriefed (base: the PR model) or with the exact conventions section after it (exact).
# usage (any directory inside the tree): run_elm.sh <val|post> <base|exact> <rep>   [PLAN_ONLY=1: preflight]
# Both levels review the PRs the exact context file holds, so the two conditions cover the same PRs.
# The ELM key is read from the secrets file in this process.
set -euo pipefail
tag=$1; level=$2; rep=$3
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src PATH="$HOME/.elan/bin:$PATH"
set +u; source ~/.config/secrets/env.zsh; set -u
[ -n "${ELM_API_KEY:-}" ] || { echo "ELM_API_KEY is not set" >&2; exit 3; }
P=results/pr_review_v5/probes/conventions-ceiling-2026-10-04
case $tag in
  val) cfg=configs/pr_review_v5_val_small12_elm_gpt55_Grc.yaml ;;
  post) cfg=configs/pr_review_v5_probe_2026_07_08_v1_elm_gpt55_Grc.yaml ;;
  *) echo "set: val or post" >&2; exit 2 ;;
esac
prs=$(ape/bin/python -c 'import json, sys
print("[" + ",".join(str(json.loads(line)["pr_number"]) for line in open(sys.argv[1])) + "]")' "$P/context_${tag}_exact.jsonl")
if [ -n "${PLAN_ONLY:-}" ]; then verb=plan; execute=(); else verb=run; execute=(--execute); fi
exec ape/bin/python -m src.mathlib_review.review.cli $verb --config $cfg \
  --run-name probe_conv_${tag}_elmgpt55_${level}_rep${rep} \
  --set task_config.context_file=$P/context_${tag}_${level}.jsonl --set "dataset.pr_numbers=$prs" "${execute[@]}"
