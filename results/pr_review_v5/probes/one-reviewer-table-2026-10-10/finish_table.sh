#!/usr/bin/env bash
# Steps 6 and 8 of the one reviewer table, unattended: when P14's sessions are all in (the apt runs
# and the Claude pair, whose transcripts are audited first), match P14's two seals; when D12's runs
# are all in, judge the new ones and match D12's seal; then write table.txt with read_table.py. It
# commits nothing: the record is committed by hand, suite green, after the flags are read.
# Usage: sbatch -p first -A first --mem=8G --time=30:00:00 -J table-finish \
#   -o /research/projects/proofedit/ya475/localmodel/logs/table_finish_%j.log --wrap "<this file>"
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$(git -C "$HERE" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src ELAN_HOME=/research/projects/proofedit/ya475/.elan
source ~/.config/secrets/env.zsh 2>/dev/null
T=${HERE#$PWD/}; P=results/pr_review_v5/probes/conventions-ceiling-2026-10-04
S=/research/projects/proofedit/ya475/table_scratch; R=results/pr_review_v5/runs
complete() { for r in "$@"; do grep -qs '"completion_status": "complete"' $R/$r/run_manifest.json || return 1; done; }
pair_done() {
  ape/bin/python - <<'EOF'
import sys
from pathlib import Path
from src.mathlib_review.analysis import probes
left = [(s, pr) for path, prs in (("configs/probe_sets/val_small12.yaml", [26755, 28649, 29842, 30458, 30641, 32875, 34091, 36822]),
                                  ("configs/probe_sets/postcutoff_2026_07_08_v1.yaml", [41930, 42184, 42814, 43024, 43167, 43192]))
        for pr in prs for s in ("T1", "TA1") if not probes.finished(probes.load_probe_set(Path(path)).session_dir(pr, s))]
sys.exit(1 if left else 0)
EOF
}
apt=(); for t in val post; do for n in 1 2 3; do apt+=(iter_ds41_conv_${t}_apt_rep$n); done; done
until complete "${apt[@]}" && pair_done; do sleep 300; done
echo "$(date -Is) P14 sessions all in"
flag=0
for f in $S/claude_logs/pair_T1_*.jsonl $S/claude_logs/pair_TA1_*.jsonl; do
  python3 $P/audit_batch.py "$f" > "$f.audit" 2>&1 && continue
  echo "FLAG in $f (see $f.audit)"
  if [[ ",${FLAGS_READ:-}," == *",$(basename "$f" .jsonl),"* ]]; then echo "  read by hand and cleared (README)"; else flag=$((flag + 1)); fi
done
# FLAGS_READ: the comma-separated batches whose flags were read by hand and recorded in the README;
# set it inside the wrapped command (sbatch --export splits on commas).
[ $flag -eq 0 ] || { echo "$(date -Is) STOP: a pair transcript is flagged; read it before matching"; exit 4; }
bash $HERE/run_matching.sh P14_val configs/probe_sets/val_small12.yaml blinding_P14_val_SEALED.json sources_P14_val.json 4 || exit 5
bash $HERE/run_matching.sh P14_post configs/probe_sets/postcutoff_2026_07_08_v1.yaml blinding_P14_post_SEALED.json sources_P14_post.json 3 || exit 5
python3 $HERE/read_table.py > $HERE/table.txt 2>&1
echo "$(date -Is) P14 matched; table.txt holds P14"

dev=(probe_dev_elmgpt55_contract2_rep2 probe_dev_elmgpt55_contract2_rep3)
for n in 1 2 3; do dev+=(iter_ds41_conv_dev_base_rep$n iter_ds41_conv_dev_apt_rep$n); done
until complete "${dev[@]}"; do sleep 300; done
echo "$(date -Is) D12 runs all in"
for r in "${dev[@]}"; do
  slug=$(echo "$r" | tr '_' '-')
  [ -f results/pr_review_v5/audits/$slug/semantic_report.json ] && continue
  ape/bin/python -m src.mathlib_review.review.cli judge --config configs/pr_review_v5_medium_heldout_judge.yaml \
    --of "$r" --execute 2>&1 | tail -1
done
bash $HERE/run_matching.sh D12 configs/probe_sets/dev_medium_0_3_0.yaml blinding_D12_SEALED.json sources_D12.json 4 || exit 6
python3 $HERE/read_table.py --judge > $HERE/table.txt 2>&1
echo "$(date -Is) table finished: $HERE/table.txt"
