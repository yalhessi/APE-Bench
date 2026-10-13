#!/usr/bin/env bash
# Matching for one of the one reviewer table's seals (plan step 6): harness-blind matcher inputs
# (`probe match-inputs --harness-blind`), the seal's PRs split into batches of N with two blind
# matchers each (review finding 8), one headless batch on the primary token once the five-hour window
# has room, the outputs checked and the transcripts audited, the batches' matches concatenated per
# matcher, and the seal unblinded whole. A flag stops it before the unblinding.
# usage: bash run_matching.sh <name> <set.yaml> <seal file> <sources file> <PRs a batch> [merge]
#   merge: the matchers have run and a flag was read by hand (README); check, merge and unblind only.
#   e.g. bash run_matching.sh P14_val configs/probe_sets/val_small12.yaml blinding_P14_val_SEALED.json sources_P14_val.json 4
# Another probe's seals: MATCH_DIR=<its directory> (seal, sources and match_<name> live there) and
# MATCH_FLAGS for `probe match-inputs` (the filing contract's `--question-form`, 2026-10-13).
set -euo pipefail
name=$1; set_yaml=$2; seal=$3; sources=$4; size=$5; mode=${6:-run}
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$(git -C "$HERE" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src
T=${MATCH_DIR:-${HERE#$PWD/}}; P=results/pr_review_v5/probes/conventions-ceiling-2026-10-04
S=/research/projects/proofedit/ya475/table_scratch
TOKEN_VAR=CLAUDE_CODE_OAUTH_TOKEN
source $P/token_window.sh
probe() { ape/bin/python -m src.mathlib_review.review.cli probe "$@"; }
work=$S/match_$name
if [ "$mode" != merge ]; then
rm -rf "$work"; mkdir -p "$work"
ape/bin/python - "$T/$seal" "$size" "$work" <<'EOF'
import json, sys
from pathlib import Path
seal, size, work = json.loads(Path(sys.argv[1]).read_text()), int(sys.argv[2]), Path(sys.argv[3])
prs = sorted(seal, key=int)
for k in range(0, len(prs), size):
    d = work / f"b{k // size + 1}"
    d.mkdir()
    (d / "seal.json").write_text(json.dumps({pr: seal[pr] for pr in prs[k:k + size]}, indent=1) + "\n")
    print(d.name, prs[k:k + size])
EOF
: > "$work.prompts"
for b in "$work"/b*/; do
  probe match-inputs --set "$set_yaml" --seal "$b/seal.json" --sources "$T/$sources" --out "$b" --harness-blind ${MATCH_FLAGS:-} \
    | grep '"prompt"' >> "$work.prompts"
done
echo "$(date -Is) $name: $(wc -l < "$work.prompts") matcher folders"
wait_for_room 30 92 60 || { echo "no room for the matchers"; exit 3; }
$P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN m_$name $S/claude_logs - @"$work.prompts"
python3 $P/audit_batch.py $S/claude_logs/m_$name.jsonl || { echo "audit flagged; read by hand before unblinding"; exit 4; }
fi
python3 $P/check_matches.py "$work"/b*/m1 "$work"/b*/m2
mkdir -p "$T/match_$name"
ape/bin/python - "$work" "$T/match_$name" <<'EOF'
import json, sys
from pathlib import Path
work, out = Path(sys.argv[1]), Path(sys.argv[2])
stats = {}
for m in ("1", "2"):
    merged = {"asks": [], "unmatched": {}}
    for b in sorted(work.glob("b*")):
        d = json.loads((b / f"m{m}" / "matches.json").read_text())
        merged["asks"] += d["asks"]
        merged["unmatched"].update(d.get("unmatched") or {})
    (out / f"matches.{m}.json").write_text(json.dumps(merged, indent=1, ensure_ascii=False) + "\n")
for b in sorted(work.glob("b*")):
    stats.update(json.loads((b / "inputs" / "session_stats.json").read_text()))
(out / "session_stats.json").write_text(json.dumps(stats, indent=1) + "\n")
print(f"merged {len(list(work.glob('b*')))} batches: {len(merged['asks'])} asks a matcher")
EOF
probe unblind --set "$set_yaml" --seal "$T/$seal" --matches "$T/match_$name" > "$T/match_$name/unblinded.json"
echo "$(date -Is) $name unblinded: $T/match_$name/unblinded.json"
