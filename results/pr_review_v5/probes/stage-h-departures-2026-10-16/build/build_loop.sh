#!/usr/bin/env bash
# Step 4's workspaces as they become ready: every 5 minutes, restore each base whose snapshot is ready and whose
# workspace is not yet there, then run the reviewed prebuild (it builds what it can and skips the rest), until
# every PR has a reviewed workspace or nothing is left building. Compute only. Run from the repository root.
#   systemd-run --user --collect --unit=stageh-loop /bin/bash -c "cd <root> && exec bash <this file>"
set -u
export ELAN_HOME=/research/projects/proofedit/ya475/.elan PYTHONPATH="$PWD:$PWD/src" PATH="/research/projects/proofedit/ya475/.elan/bin:$PATH"
HERE="results/pr_review_v5/probes/stage-h-departures-2026-10-16/build"
CFG=configs/pr_review_v5_stage_h_v1_build.yaml
SET=configs/probe_sets/stage_h_v1.yaml
R=data/code_execute/repos/mathlib4
log() { echo "$(date '+%F %T') $*" >> "$HERE/loop.log"; }
while true; do
  # wait for any reviewed build already running (one prebuild at a time, one host)
  while systemctl --user is-active --quiet stageh-reviewed-1; do sleep 60; done
  ready=$(ape/bin/python - <<'EOF'
import json, os
from pathlib import Path
draw = {a["pr_number"]: a["base_sha"] for a in json.load(open("inputs/pull_requests/evaluation/val1000-2025-06-2026-03-v1/draw.json"))["accepted"]}
prs = [26301, 26979, 27054, 28678, 30652, 31081, 32598, 33879, 35140, 36430, 36577, 37052, 37190, 37341]
R = Path("data/code_execute/repos/mathlib4")
out = []
for pr in prs:
    base = draw[pr]
    st = R / "snapshots" / f"{base}.state"
    if st.is_file() and json.loads(st.read_text()).get("status") == "ready" and not (R / "workspaces" / base).is_dir():
        out.append(str(pr))
print(" ".join(out))
EOF
)
  if [ -n "$ready" ]; then
    log "restoring bases for PRs: $ready"
    ape/bin/python -m src.mathlib_review.review.cli probe restore-bases --set "$SET" --prs $ready >> "$HERE/restore.out" 2>&1
  fi
  status=$(ape/bin/python -m src.mathlib_review.release.prebuild --reviewed --config "$CFG" 2>&1 | grep -E "reviewed workspaces for")
  log "$status"
  if echo "$status" | grep -qE "to build" && ! echo "$status" | grep -qE " 0 to build"; then
    ape/bin/python -m src.mathlib_review.release.prebuild --reviewed --execute --config "$CFG" >> "$HERE/build_reviewed.out" 2>&1
    log "reviewed prebuild exit $?: $(ape/bin/python -m src.mathlib_review.release.prebuild --reviewed --config "$CFG" 2>&1 | grep -E 'reviewed workspaces for')"
  fi
  if echo "$status" | grep -qE " 0 to build, 0 base not built"; then log "done"; break; fi
  if ! systemctl --user is-active --quiet stageh-bases && [ -z "$ready" ] && echo "$status" | grep -qE " 0 to build"; then
    log "bases finished; nothing more to build"; break
  fi
  sleep 300
done
