#!/usr/bin/env bash
# One stage-D run: DeepSeek-V4.1-Flash (keepthink, reasoning high) under contract v2 on a probe set, at
# one level: base (the PR model alone, every PR of the set), exact (stage L's exact section), prec (the
# exact section with census examples and the precedence paragraph), ap (stage AP: prec on stage F's blind
# picks), apt (the one reviewer table: ap's picks extended to P14's other four PRs and the dev release).
# A briefed run reviews the PRs its context file holds, or those in $PRS (`[26755,36822]`) when it is set.
# The dev set (`dev`, the release's 15) takes base and apt; its base reads the dev probe's model context.
# usage (any directory inside the tree): run_ds41.sh <val|post|dev> <base|exact|prec|ap|apt> <rep> [plan]
#   with `plan`, the preflight of the same run (spends nothing); without, the run itself, which needs the
#   server of serve_ds41.sbatch on 127.0.0.1:8012. A complete run is skipped; an interrupted one resumes.
set -euo pipefail
tag=$1; level=$2; rep=$3; mode=${4:-run}
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src ELAN_HOME=/research/projects/proofedit/ya475/.elan
export PATH=$ELAN_HOME/bin:$PATH
P=results/pr_review_v5/probes/conventions-ceiling-2026-10-04
case $tag in val) cfg=val_small12 ;; post) cfg=probe_2026_07_08_v1 ;; dev) cfg=dev_medium ;; *) echo "set: val, post or dev" >&2; exit 2 ;; esac
case $level in base|exact|prec|ap|apt) ;; *) echo "level: base, exact, prec, ap or apt" >&2; exit 2 ;; esac
case $tag:$level in dev:base|dev:apt|val:*|post:*) ;; *) echo "dev takes base or apt" >&2; exit 2 ;; esac
context=$P/context_${tag}_${level}.jsonl
[ "$tag:$level" = dev:base ] && context=results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/model_context.jsonl
name=iter_ds41_conv_${tag}_${level}_rep${rep}
# The prec context files hold census bodies, which are never committed; they are rebuilt by
# build_context.py and must be the bytes this stage pre-registered.
if [ "$level" = prec ] || [ "$level" = ap ] || [ "$level" = apt ]; then
  grep -F "$context" $P/context_${level}.sha256 | sha256sum -c --quiet - || { echo "$context is not the pre-registered file" >&2; exit 4; }
fi
prs=()
if [ -n "${PRS:-}" ]; then
  prs=(--set "dataset.pr_numbers=$PRS")
elif [ "$level" != base ]; then
  prs=(--set "dataset.pr_numbers=$(ape/bin/python -c 'import json, sys
print("[" + ",".join(str(json.loads(line)["pr_number"]) for line in open(sys.argv[1])) + "]")' "$context")")
fi
args=(--config configs/pr_review_v5_${cfg}_local_ds41_contract2.yaml --run-name "$name"
      --set task_config.context_file="$context" "${prs[@]}")
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
