#!/usr/bin/env bash
# The solo baseline on the same 11 validation PRs as pr5_val_small12_minus30714_lead_rep1.
#   tmux new-session -d -s val_solo "bash results/pr_review_v5/probes/val-small12-2026-09-25/launch_solo.sh"
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; REPO="$(cd "$HERE/../../../.." && pwd)"; cd "$REPO"
source ~/.config/secrets/env.zsh
export PYTHONPATH="$REPO:$REPO/src" PATH="/research/projects/proofedit/ya475/.elan/bin:$PATH"
LOG="$HERE/launch_solo.log"; RUN="pr5_val_small12_minus30714_solo_ape_rep1"
log() { echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
[ -n "${OPENAI_API_KEY:-}" ] || { log "ABORT: OPENAI_API_KEY is not set"; exit 2; }
log "solo: run $RUN"
ape/bin/python -m src.mathlib_review.review.cli run --config configs/pr_review_v5_val_small12_solo_ape.yaml --run-name "$RUN" --execute >> "$HERE/solo_run.log" 2>&1
log "solo: run exit $?; completed: $(grep -c 'completed with success' "$HERE/solo_run.log"); retry warnings: $(grep -c 'API call failed, retrying' "$HERE/solo_run.log"); paused: $(grep -ci 'paused' "$HERE/solo_run.log")"
log "DONE_SOLO"
