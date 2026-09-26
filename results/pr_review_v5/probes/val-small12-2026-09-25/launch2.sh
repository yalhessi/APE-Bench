#!/usr/bin/env bash
# Second launch of the validation chain, after the first failed on two things launch.sh did not
# know: the reviewed build needs each base RESTORED from its snapshot first, and PR 30714's base
# fails inside `lake build` (replaying dependency oleans: "no such file or directory"), so the
# run is the other 11 of small12, named for it.
#   tmux new-session -d -s val_probe2 "bash results/pr_review_v5/probes/val-small12-2026-09-25/launch2.sh"
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; REPO="$(cd "$HERE/../../../.." && pwd)"; cd "$REPO"
source ~/.config/secrets/env.zsh
export PYTHONPATH="$REPO:$REPO/src" PATH="/research/projects/proofedit/ya475/.elan/bin:$PATH"
LOG="$HERE/launch2.log"; STATUS="$HERE/status.txt"
R="ape/bin/python -m src.mathlib_review.review.cli"
PRS="26185,26755,28649,29842,30458,30641,32080,32875,34091,34935,36822"
RUN="pr5_val_small12_minus30714_lead_rep1"
CFG="configs/pr_review_v5_val_2025_06_2026_03_v1_small12.yaml"
log() { echo "$(date '+%F %T') $*" | tee -a "$LOG"; echo "$*" > "$STATUS"; }
[ -n "${OPENAI_API_KEY:-}" ] || { log "ABORT: OPENAI_API_KEY is not set"; exit 2; }
log "restore: 11 base workspaces from their snapshots"
ape/bin/python "$HERE/restore_bases.py" "$PRS" >> "$HERE/restore_bases.log" 2>&1; log "restore: exit $? ($(grep -c '^restored' "$HERE/restore_bases.log") restored)"
log "build: reviewed workspaces for the 11"
ape/bin/python -m src.mathlib_review.release.prebuild --reviewed --execute --config "$CFG" >> "$HERE/build_reviewed2.log" 2>&1
log "build: reviewed exit $? ($(grep -c 'success: True' "$HERE/build_reviewed2.log") succeeded)"
log "validation: plan $RUN"
if $R plan --config "$CFG" --run-name "$RUN" --set "dataset.pr_numbers=[$PRS]" >> "$HERE/val_plan2.log" 2>&1; then
  log "validation: run $RUN"
  $R run --config "$CFG" --run-name "$RUN" --set "dataset.pr_numbers=[$PRS]" --execute >> "$HERE/val_run.log" 2>&1
  log "validation: run exit $?; completed: $(grep -c 'completed with success' "$HERE/val_run.log"); retry warnings: $(grep -c 'API call failed, retrying' "$HERE/val_run.log"); paused: $(grep -ci 'paused' "$HERE/val_run.log")"
else
  log "validation: plan refused; see val_plan2.log. NOT run."
fi
log "DONE2"
