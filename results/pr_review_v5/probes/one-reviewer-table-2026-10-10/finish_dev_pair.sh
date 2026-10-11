#!/usr/bin/env bash
# The dev pair's scoring, unattended (README, "The dev pair", pre-registered 2026-10-11): when T1 and
# TA1 are in on all 15 dev PRs, audit their transcripts, import both as runs and judge them, match the
# D12b seal (all 15 sessions a PR) in PR batches, and write table_D12b.txt and the weighted reading.
# Commits nothing. A flag not named in FLAGS_READ stops it before matching.
# Usage: systemd-run --user --collect --unit=dev-pair-finish --setenv=PATH="$PATH" --setenv=HOME="$HOME" \
#   /bin/bash -c "exec <this file> >> <log> 2>&1 < /dev/null"
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$(git -C "$HERE" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src
source ~/.config/secrets/env.zsh 2>/dev/null
P=results/pr_review_v5/probes/conventions-ceiling-2026-10-04
S=/research/projects/proofedit/ya475/table_scratch; DEV=configs/probe_sets/dev_medium_0_3_0.yaml
done_all() {
  ape/bin/python - <<'PY'
import sys
from pathlib import Path
from src.mathlib_review.analysis import probes
spec = probes.load_probe_set(Path("configs/probe_sets/dev_medium_0_3_0.yaml"))
sys.exit(0 if all(probes.finished(spec.session_dir(pr, s)) for pr in spec.pr_numbers for s in ("T1", "TA1")) else 1)
PY
}
until done_all; do sleep 300; done
echo "$(date -Is) dev pair sessions all in"
flag=0
for f in $S/claude_logs/pair_dev_T1_*.jsonl $S/claude_logs/pair_dev_TA1_*.jsonl; do
  python3 $P/audit_batch.py "$f" > "$f.audit" 2>&1 && continue
  echo "FLAG in $f (see $f.audit)"
  if [[ ",${FLAGS_READ:-}," == *",$(basename "$f" .jsonl),"* ]]; then echo "  read by hand and cleared (README)"; else flag=$((flag + 1)); fi
done
[ $flag -eq 0 ] || { echo "$(date -Is) STOP: a dev pair transcript is flagged; read it, then rerun with FLAGS_READ"; exit 4; }
for s in T1 TA1; do
  run=probe_dev_claude_$s; slug=probe-dev-claude-$s
  [ -d results/pr_review_v5/runs/$run ] || ape/bin/python -m src.mathlib_review.review.cli probe import --set $DEV --session $s --run-name $run | tail -3
  [ -f results/pr_review_v5/audits/$slug/semantic_report.json ] || ape/bin/python -m src.mathlib_review.review.cli judge \
    --config configs/pr_review_v5_medium_heldout_judge.yaml --of $run --execute 2>&1 | tail -1
done
[ -f $HERE/match_D12b/unblinded.json ] || bash $HERE/run_matching.sh D12b $DEV blinding_D12b_SEALED.json sources_D12b.json 3 || exit 6
python3 $HERE/read_table.py --seal "D12b=$HERE/match_D12b" --judge > $HERE/table_D12b.txt 2>&1
python3 $HERE/inspect_weighting.py > $HERE/inspect_weighting.txt 2>&1
echo "$(date -Is) dev pair scored: $HERE/table_D12b.txt"
