#!/usr/bin/env bash
# The same-day Claude pair of the one reviewer table (docs/plans/2026-10-10-one-reviewer-table.md,
# step 7; the user's choice, 2026-10-10): on P14's 14 ask PRs, T1 (Opus 5.5 solo, brief X, the X
# route) and TA1 (the same with the apt section DeepSeek's AP sessions read, byte for byte), one rep
# each. Two PRs a batch, T1 and TA1 side by side as two headless batches on the primary token, each
# batch only when the five-hour window has room for it (token_window.sh); it stops if the week passes
# 60%, since the login is the user's interactive one. A finished session is skipped.
# Usage: bash run_claude_pair.sh   (packets first: `cli probe packets ... --sessions T1|TA1`)
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$(git -C "$HERE" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src
P=results/pr_review_v5/probes/conventions-ceiling-2026-10-04
S=/research/projects/proofedit/ya475/table_scratch
TOKEN_VAR=CLAUDE_CODE_OAUTH_TOKEN
source $P/token_window.sh
VAL=configs/probe_sets/val_small12.yaml; POST=configs/probe_sets/postcutoff_2026_07_08_v1.yaml
# Stage C's order (missed asks per expected token), then the four PRs stage C did not run.
queue=($VAL:30641 $VAL:29842 $POST:41930 $VAL:32875 $POST:42814 $VAL:30458 $VAL:28649 $POST:42184
       $POST:43167 $VAL:34091 $VAL:26755 $VAL:36822 $POST:43024 $POST:43192)
unfinished() {  # unfinished <session> <set:pr>...: the items whose packet has no findings yet
  ape/bin/python - "$@" <<'EOF'
import sys
from pathlib import Path
from src.mathlib_review.analysis import probes
session = sys.argv[1]
for item in sys.argv[2:]:
    spec, pr = item.rsplit(":", 1)
    if not probes.finished(probes.load_probe_set(Path(spec)).session_dir(int(pr), session)):
        print(item)
EOF
}
n=0
for ((i = 0; i < ${#queue[@]}; i += 2)); do
  batch=("${queue[@]:i:2}")
  t1=($(unfinished T1 "${batch[@]}")); ta=($(unfinished TA1 "${batch[@]}"))
  need=$(( 4 * (${#t1[@]} + ${#ta[@]}) ))  # measured: a session is about 2.5 points (batches 1-4, 2026-10-10)
  [ "$need" -eq 0 ] && continue
  wait_for_room "$need" 92 60; rc=$?
  [ $rc -eq 2 ] && { echo "$(date -Is) STOP: the week is past 60%"; exit 2; }
  [ $rc -ne 0 ] && { echo "$(date -Is) STOP: no room after twelve tries"; exit 1; }
  n=$((n + 1))
  echo "$(date -Is) batch $n: T1 ${t1[*]:-none} | TA1 ${ta[*]:-none}"
  [ ${#t1[@]} -gt 0 ] && { $P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN pair_T1_$n $S/claude_logs T1 "${t1[@]}" & }
  [ ${#ta[@]} -gt 0 ] && { $P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN pair_TA1_$n $S/claude_logs TA1 "${ta[@]}" & }
  wait
  echo "$(date -Is) batch $n done; still unfinished: T1 $(unfinished T1 "${batch[@]}" | tr '\n' ' ')| TA1 $(unfinished TA1 "${batch[@]}" | tr '\n' ' ')"
done
echo "$(date -Is) pair finished; unfinished: T1 $(unfinished T1 "${queue[@]}" | tr '\n' ' ')| TA1 $(unfinished TA1 "${queue[@]}" | tr '\n' ' ')"
