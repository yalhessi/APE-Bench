#!/bin/bash
# The gpt-5.5 row of the one reviewer table (docs/plans/2026-10-10-one-reviewer-table.md, step 4):
# contract v2 on ELM, three reps on validation small12's 8 ask PRs, the post-cutoff probe's 6 and the
# dev release's 15. The three sets run in parallel, reps in sequence; a finished run is skipped and a
# started one resumed. Stops a chain whose log keeps retrying (a bad key retries for hours, CLAUDE.md).
# Usage: sbatch -p first -A first --mem=32G --time=16:00:00 -J gpt-table \
#   -o /research/projects/proofedit/ya475/localmodel/logs/gpt_table_%j.log --wrap "<this file>"
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src ELAN_HOME=/research/projects/proofedit/ya475/.elan
export PATH=$ELAN_HOME/bin:$PATH
source ~/.config/secrets/env.zsh 2>/dev/null
[ -n "$ELM_API_KEY" ] || { echo "ELM_API_KEY is not set" >&2; exit 3; }
LOGS=/research/projects/proofedit/ya475/localmodel/logs
chain() {  # $1 config stem, $2 run-name stem
  for rep in 1 2 3; do
    name=$2_elmgpt55_contract2_rep$rep
    if grep -qs '"completion_status": "complete"' results/pr_review_v5/runs/$name/run_manifest.json; then
      echo "$(date -Is) $name complete; skipped"; continue
    fi
    resume=(); [ -d .ape/runs/$name ] && resume=(--resume)
    echo "$(date -Is) $name started"
    ape/bin/python -m src.mathlib_review.review.cli run --config configs/pr_review_v5_$1_elm_gpt55_contract2.yaml \
      --run-name "$name" "${resume[@]}" --execute > "$LOGS/cli_$name.log" 2>&1 &
    pid=$!
    while kill -0 $pid 2>/dev/null; do
      if [ "$(grep -c 'API call failed, retrying' "$LOGS/cli_$name.log")" -gt 20 ]; then
        echo "$(date -Is) STOP: $name keeps retrying"; kill $pid; return 1
      fi
      sleep 60
    done
    wait $pid; echo "$(date -Is) $name exit $?: $(grep -c 'completed with success' "$LOGS/cli_$name.log") sessions ok"
  done
}
chain val_small12 probe_val_small12 &
chain probe_2026_07_08_v1 probe_postcutoff &
chain dev_medium probe_dev &
wait
echo "$(date -Is) gpt table runs finished"
