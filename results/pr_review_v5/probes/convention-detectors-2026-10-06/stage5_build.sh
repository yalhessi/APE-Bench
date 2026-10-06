#!/usr/bin/env bash
# Stage 5's workspaces, unattended: base snapshots, their restore, then the reviewed workspaces.
# Compute only -- no model is called. Run from the repository root (or a worktree with data/ linked):
#   nohup bash results/pr_review_v5/probes/convention-detectors-2026-10-06/stage5_build.sh &
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# ELAN_HOME as well as PATH: elan otherwise unpacks a missing toolchain into ~/.elan, and home is at
# quota (the first launch, 2026-10-06, failed there: "Quota exceeded (os error 122)").
export ELAN_HOME=/research/projects/proofedit/ya475/.elan
export PYTHONPATH="$PWD:$PWD/src" PATH="$ELAN_HOME/bin:$PATH"
LOG="$HERE/stage5/build.log"
log() { echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
log "bases: $(wc -l < "$HERE/stage5/base_build_rows.jsonl") rows"
ape/bin/python -m ape.toolkits.execute.lean.build --input_file "$HERE/stage5/base_build_rows.jsonl" --num_processes 4 > "$HERE/stage5/build_base.out" 2>&1
log "bases: exit $? ($(grep -c 'success: True' "$HERE/stage5/build_base.out") succeeded, $(grep -c 'success: False' "$HERE/stage5/build_base.out") failed)"
ape/bin/python -m src.mathlib_review.review.cli probe restore-bases --set configs/probe_sets/census_detectors_v1.yaml > "$HERE/stage5/restore.out" 2>&1
log "restore: exit $?"
ape/bin/python -m src.mathlib_review.release.prebuild --reviewed --execute --config configs/pr_review_v5_census_detectors_v1_opus55_hygiene_claude_sub.yaml > "$HERE/stage5/build_reviewed.out" 2>&1
log "reviewed: exit $? ($(grep -c 'success: True' "$HERE/stage5/build_reviewed.out") succeeded)"
ape/bin/python -m src.mathlib_review.release.prebuild --reviewed --config configs/pr_review_v5_census_detectors_v1_opus55_hygiene_claude_sub.yaml 2>&1 | grep -E 'reviewed workspaces for|ready|failed|not built' >> "$LOG"
log "done"
