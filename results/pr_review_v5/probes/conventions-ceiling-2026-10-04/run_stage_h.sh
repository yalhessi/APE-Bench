#!/usr/bin/env bash
# Stage H, unattended on token C: the census pinpointers (negatives), the rates, design `rate`, then
# the deciders design by design, then the score. Every batch is metered; no work starts once the
# week reaches WEEK_CAP (80%). An audit flag or an invalid file stops it uncommitted, to be read by hand.
# usage: bash run_stage_h.sh <scratch dir> <census bodies.json>
set -euo pipefail
S=$1; BODIES=$2
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD:$PWD/src PATH="$HOME/.elan/bin:$PATH"
P=results/pr_review_v5/probes/conventions-ceiling-2026-10-04
. $P/token_window.sh
WEEK_CAP=${WEEK_CAP:-80}
mkdir -p $S/claude_logs $P/census_pinpoints $P/stage_h_decisions

wait_or_stop() {  # wait_or_stop <points needed> <what>
  local rc=0; wait_for_room "$1" 96 "$WEEK_CAP" || rc=$?
  [ $rc = 0 ] && return 0
  echo "$(date '+%H:%M:%S') stopping before $2: week at ${WEEK_CAP}% or no window"; exit 6
}
batch() {  # batch <name> <prompts file>: run, report, audit (exit 4 on a flag)
  $P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_C $1 $S/claude_logs - @$2
  python3 $P/batch_report.py $S/claude_logs/$1.jsonl $S/claude_logs/$1.prompt | grep -E '^(Pinpointer|Decider)|^five-hour|^result'
  python3 $P/audit_batch.py $S/claude_logs/$1.jsonl > $S/audit_$1.txt || { cat $S/audit_$1.txt; echo "audit flag in $1: stopping uncommitted"; exit 4; }
  tail -1 $S/audit_$1.txt
}

# 1. the census pinpointers, three a batch
PRS=$(python3 -c "import json; print(' '.join(str(p['pr']) for p in json.load(open('$P/census_sample.json'))['prs']))")
todo=(); for pr in $PRS; do [ -f $P/census_pinpoints/pr$pr.json ] || todo+=($pr); done
k=0
while [ ${#todo[@]} -gt 0 ]; do
  k=$(( k + 1 )); chunk=("${todo[@]:0:3}")
  : > $S/census_b$k.prompts
  for pr in "${chunk[@]}"; do grep "\"Pinpointer pr$pr\"" $S/census_pinpoint.prompts >> $S/census_b$k.prompts; done
  wait_or_stop $(( 16 * ${#chunk[@]} )) "census pinpoint batch $k"
  echo "$(date '+%H:%M:%S') census pinpoint batch hc$k: ${chunk[*]}"
  batch hc$k $S/census_b$k.prompts
  for pr in "${chunk[@]}"; do
    python3 - $S/census_pinpoint/pr$pr/candidates.json $P/rules.json <<'PY'
import json, sys
from collections import Counter
c = json.load(open(sys.argv[1])); ids = {r["id"] for r in json.load(open(sys.argv[2]))}
per = Counter(i["id"] for i in c)
ok = all(set(i) == {"id", "file", "declaration", "fact", "status"} and i["id"] in ids and i["status"] in ("departs", "check") for i in c)
sys.exit(0 if ok and max(per.values(), default=0) <= 3 else 3)
PY
    cp $S/census_pinpoint/pr$pr/candidates.json $P/census_pinpoints/pr$pr.json
  done
  git add $P/census_pinpoints
  git commit -q -m "probes: stage H census pinpointing batch hc$k (${chunk[*]}) -- blind, audited clean; committed by run_stage_h.sh unattended"
  todo=("${todo[@]:${#chunk[@]}}")
done

# 2. the rates and the model-free design
python3 $P/stage_h.py mined $S/census_release $BODIES | tee $S/mined.txt
python3 $P/stage_h.py rate
git add $P/census_mined.json $P/census_rates.json $P/stage_h_decisions/rate.json
{ echo "probes: stage H's record -- negatives and rates from 16 census PRs, and design rate's decisions; committed by run_stage_h.sh unattended"; echo; cat $S/mined.txt; } > $S/msg_mined.txt
git commit -q -F $S/msg_mined.txt

# 3. the deciders, design by design, both halves in one batch
for design in examples judge retrieve examples_rate; do
  [ -f $P/stage_h_decisions/$design.json ] && continue
  python3 $P/stage_h.py folders $design $BODIES $S/deciders > $S/deciders_$design.prompts
  wait_or_stop 40 "design $design"
  echo "$(date '+%H:%M:%S') deciders, $design"
  batch hd_$design $S/deciders_$design.prompts
  python3 - $S/deciders/$design $P/stage_h_decisions/$design.json <<'PY'
import json, re, sys
from pathlib import Path
root, out = Path(sys.argv[1]), Path(sys.argv[2]); got = []
for half in ("half1", "half2"):
    want = set(re.findall(r"^### (c[0-9a-f]{6}) ", (root / half / "candidates.md").read_text(), re.M))
    d = json.loads((root / half / "decisions.json").read_text())
    seen = [x["cid"] for x in d]
    assert set(seen) == want and len(seen) == len(want), (half, len(want), len(seen))
    assert all(isinstance(x["raise"], bool) and 0 <= float(x["p"]) <= 1 for x in d)
    got += d
out.write_text(json.dumps(got, indent=1, ensure_ascii=False) + "\n")
print(f"{out.stem}: {len(got)} decisions, {sum(x['raise'] for x in got)} raised")
PY
  git add $P/stage_h_decisions/$design.json
  git commit -q -m "probes: stage H design $design decided -- two blind deciders, audited clean; committed by run_stage_h.sh unattended"
done

# 4. the score
python3 $P/stage_h.py score | tee $S/score.txt
{ echo "probes: stage H scored -- each design's raises against the maintainers' asks; committed by run_stage_h.sh unattended, the write-up follows"; echo; cat $S/score.txt; } > $S/msg_score.txt
git commit -q --allow-empty -F $S/msg_score.txt
echo "$(date '+%H:%M:%S') STAGE H DONE"
