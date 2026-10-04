#!/usr/bin/env bash
# One stage-L run: the local 397B under contract v2 on a probe set, at one brief level.
# usage (any directory inside the tree): run_local.sh <val|post> <base|exact|common|all> <rep>
# Needs the server of ../local-vllm-2026-10-02/serve.sbatch on port 8012, and for a briefed level the
# context file build_context.py writes. A briefed run reviews the PRs its context file holds.
set -euo pipefail
tag=$1; level=$2; rep=$3
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src PATH="$HOME/.elan/bin:$PATH" ELM_API_KEY=local-dummy
P=results/pr_review_v5/probes/conventions-ceiling-2026-10-04
case $tag in val) cfg=val_small12 ;; post) cfg=probe_2026_07_08_v1 ;; *) echo "set: val or post" >&2; exit 2 ;; esac
context=$P/context_${tag}_${level}.jsonl
prs=()
if [ "$level" != base ]; then
  prs=(--set "dataset.pr_numbers=$(ape/bin/python -c 'import json, sys
print("[" + ",".join(str(json.loads(line)["pr_number"]) for line in open(sys.argv[1])) + "]")' "$context")")
fi
curl -sf -m 5 http://127.0.0.1:8012/v1/models > /dev/null || { echo "no server on 127.0.0.1:8012" >&2; exit 3; }
exec ape/bin/python -m src.mathlib_review.review.cli run \
  --config configs/pr_review_v5_${cfg}_local397_contract2.yaml \
  --run-name iter_local397_conv_${tag}_${level}_rep${rep} \
  --set task_config.context_file="$context" "${prs[@]}" --execute
