#!/usr/bin/env bash
set -u
REPO=/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/pipeline-overfit-review; S=$(dirname "$0"); cd "$REPO"
source ~/.config/secrets/env.zsh
export PYTHONPATH="$REPO:$REPO/src"
[ -n "${GITHUB_TOKEN:-}" ] || { echo "ABORT: GITHUB_TOKEN unset"; exit 2; }
echo "$(date '+%F %T') candidates"; ape/bin/python "$S/candidates_outside_window.py" "$S" 150 100 || exit 1
echo "$(date '+%F %T') collect tier 2 for $(grep -vc '^#' "$S/outside_window_prs.txt") PRs"
ape/bin/python -m src.datasets.pull_requests.collect --tier 2 --start 2024-03-01 --end 2026-08-31 --prs "$S/outside_window_prs.txt"
echo "$(date '+%F %T') collect exit $?"; echo DONE
