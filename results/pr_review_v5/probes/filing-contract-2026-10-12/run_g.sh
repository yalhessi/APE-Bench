#!/usr/bin/env bash
# One run of design G (`filing_contract`) on the self-hosted DeepSeek tier, with the DeepSeek AP sessions'
# conventions section (`context_<set>_apt.jsonl`, the registered bytes) and that file's PRs.
# usage (any directory inside the tree): run_g.sh <dev|val|post> <rep number|smoke> [plan]
#   smoke runs the pre-registered smoke PRs (README, amendment 1); a number runs every PR of the file.
#   With `plan`, the preflight (spends nothing); without, the run, which needs serve_ds41.sbatch's server
#   on 127.0.0.1:8012. A complete run is skipped; an interrupted one resumes.
set -euo pipefail
tag=$1; rep=$2; mode=${3:-run}
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src ELAN_HOME=/research/projects/proofedit/ya475/.elan
export PATH=$ELAN_HOME/bin:$PATH
C=results/pr_review_v5/probes/conventions-ceiling-2026-10-04
case $tag in dev|val|post) ;; *) echo "set: dev, val or post" >&2; exit 2 ;; esac
context=$C/context_${tag}_apt.jsonl
grep -F "$context" $C/context_apt.sha256 | sha256sum -c --quiet - || { echo "$context is not the registered file" >&2; exit 4; }
if [ "$rep" = smoke ]; then
  case $tag in dev) prs="[33145,33294]" ;; val) prs="[30641]" ;; post) prs="[42814]" ;; esac
  name=filing_g_smoke_$tag
else
  prs=$(ape/bin/python -c 'import json, sys
print("[" + ",".join(str(json.loads(line)["pr_number"]) for line in open(sys.argv[1]) if line.strip()) + "]")' "$context")
  name=filing_g_${tag}_rep$rep
fi
args=(--config configs/designs/filing_contract_${tag}_local.yaml --run-name "$name"
      --set task_config.context_file="$context" --set "dataset.pr_numbers=$prs")
if [ "$mode" = plan ]; then
  exec ape/bin/python -m src.mathlib_review.review.cli plan "${args[@]}"
fi
if grep -qs '"completion_status": "complete"' results/pr_review_v5/runs/$name/run_manifest.json; then
  echo "$name is complete; skipped"; exit 0
fi
resume=()
[ -d .ape/runs/$name ] && resume=(--resume)
curl -sf -m 5 http://127.0.0.1:8012/v1/models > /dev/null || { echo "no server on 127.0.0.1:8012" >&2; exit 3; }
exec ape/bin/python -m src.mathlib_review.review.cli run "${args[@]}" "${resume[@]}" --execute
