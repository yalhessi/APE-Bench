#!/usr/bin/env bash
# Compile every harness file against the base workspace, 8 at a time; one .out per file.
set -u
S3=/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/b9848b08-eb04-43a7-9e77-0f87417755b6/scratchpad/fold/v3
H=/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/b9848b08-eb04-43a7-9e77-0f87417755b6/scratchpad/fold/harness
W=/research/projects/proofedit/ya475/APE-Bench/data/code_execute/repos/mathlib4/workspaces/7ee74e7d3f87077723e124e2e62a6dd1a9509c13
export PATH=/research/projects/proofedit/ya475/.elan/bin:$PATH
cd "$W"
one() { f="$1"; b=$(basename "$f" .lean); s=$(date +%s)
  timeout 1500 lake env bash -c "LEAN_PATH=$S3:\$LEAN_PATH lean -Dexperimental.module=true $f" > "$H/$b.out" 2>&1; rc=$?
  echo "$b rc=$rc $(( $(date +%s) - s ))s folds=$(grep -c '⇒' "$H/$b.out") errors=$(grep -c ': error' "$H/$b.out")"; }
export -f one; export S3 H W
ls "$H"/*.lean | xargs -P 8 -I{} bash -c 'one {}' | tee "$H/run.log"
echo DONE-HARNESS
