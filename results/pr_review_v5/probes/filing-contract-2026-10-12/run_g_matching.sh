#!/usr/bin/env bash
# The filing contract's matching (README, "Matching"), unattended: once the nine G runs are complete,
# match the three seals -- per PR G1, G2, G3 and the anchors DX1, AP1, harness-blind, two matchers a
# batch, the question-form rubric -- with the one reviewer table's run_matching.sh on the primary token,
# and unblind each. It reads no bar and commits nothing: read_g.py reads the bars, by hand, after.
# Usage: sbatch -p first -A first --mem=8G --time=12:00:00 -J filing-g-match \
#   -o /research/projects/proofedit/ya475/localmodel/logs/filing_g_match_%j.log --wrap "<this file>"
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$(git -C "$HERE" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src
source ~/.config/secrets/env.zsh 2>/dev/null
[ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] || { echo "$(date -Is) STOP: CLAUDE_CODE_OAUTH_TOKEN is not set"; exit 2; }
R=results/pr_review_v5/runs
TABLE=results/pr_review_v5/probes/one-reviewer-table-2026-10-10
export MATCH_DIR=${HERE#$PWD/} MATCH_FLAGS=--question-form
runs=(); for t in val post dev; do for n in 1 2 3; do runs+=(filing_g_${t}_rep$n); done; done
complete() { for r in "${runs[@]}"; do grep -qs '"completion_status": "complete"' $R/$r/run_manifest.json || return 1; done; }
until complete; do sleep 300; done
echo "$(date -Is) the nine G runs are complete"
for x in "G_P14_val configs/probe_sets/val_small12.yaml 4" "G_P14_post configs/probe_sets/postcutoff_2026_07_08_v1.yaml 3" \
         "G_D12 configs/probe_sets/dev_medium_0_3_0.yaml 4"; do
  set -- $x
  [ -f "$HERE/match_$1/unblinded.json" ] && continue
  bash $TABLE/run_matching.sh "$1" "$2" "blinding_$1_SEALED.json" "sources_$1.json" "$3" || { echo "$(date -Is) STOP: matching $1 exited $?"; exit 5; }
done
echo "$(date -Is) matching finished: $HERE/match_G_*/unblinded.json"
