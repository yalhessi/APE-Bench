#!/usr/bin/env bash
# Stage G's reviewer sessions and matching, unattended, on token C alone (token B's login is
# disabled). Sessions G1 (brief X plus the pinpointed candidates) run in batches of up to three
# while the five-hour window has room, in stage C's order; when it has none the script sleeps to the
# window's reset. Then one seal a set over X1, X2, E1 and G1, two blind matchers a set, the
# unblinding, the reading and the decomposition. A step that fails stops it; an audit flag holds
# back the commits and is read by hand.
# usage: bash run_stage_g.sh <scratch dir>
set -euo pipefail
S=$1
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src PATH="$HOME/.elan/bin:$PATH"
P=results/pr_review_v5/probes/conventions-ceiling-2026-10-04
declare -A SET=([val]=configs/probe_sets/val_small12.yaml [post]=configs/probe_sets/postcutoff_2026_07_08_v1.yaml)
probe() { ape/bin/python -m src.mathlib_review.review.cli probe "$@"; }
flagged=0; n=0
# <set>:<pr>:<points of a window, at an unbriefed session's cost on that PR (the dearer bound)>
queue=(val:30641:10 val:29842:12 post:41930:10 val:32875:23 post:42814:24 val:30458:19 val:28649:19 post:42184:12 post:43167:23 val:34091:18)

packet_dir() {
  case "$1:$2" in
    val:30458|val:32875|val:34091) echo results/pr_review_v5/probes/construction-demo-2026-09-29/pr$2/G1 ;;
    val:*) echo results/pr_review_v5/probes/model-gap-val-small12/pr$2/G1 ;;
    post:*) echo results/pr_review_v5/probes/postcutoff-2026-09-29/pr$2/G1 ;;
  esac
}
window() {  # prints "<status> <percent of the five-hour window used> <epoch of its reset, or 0>"
  ( set +eu; source ~/.config/secrets/env.zsh; mkdir -p "$S/home_C"; cd "$S/home_C"
    HOME=$S/home_C CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_CODE_OAUTH_TOKEN_C" timeout 120 claude -p "Reply with the single word: ok" \
      --model claude-haiku-4-5-20251001 --output-format stream-json --verbose < /dev/null 2> /dev/null ) > "$S/limit_C.jsonl" || true
  python3 - "$S/limit_C.jsonl" <<'PY'
import json, sys
status, used, reset = "unknown", 100, 0
for line in open(sys.argv[1]):
    try:
        d = json.loads(line)
    except ValueError:
        continue
    if d.get("type") == "rate_limit_event":
        info = d.get("rate_limit_info") or d
        five = (info.get("unifiedWindows") or {}).get("five_hour") or {}
        status = str(info.get("status"))
        used = round(100 * (five.get("utilization") or 0))
        reset = int(five.get("resetsAt") or five.get("resets_at") or 0)
        break
print(status, used, reset)
PY
}
wait_for_room() {  # wait_for_room <points needed> <ceiling>: returns 0 once the window has room, 1 after twelve tries
  local need=$1 ceiling=$2 status used reset pause
  for try in $(seq 1 12); do
    read -r status used reset < <(window)
    echo "$(date '+%H:%M:%S') token C: $status, $used% used; need $need under $ceiling" >&2
    if [[ "$status" == allowed* ]] && [ $(( used + need )) -le "$ceiling" ]; then return 0; fi
    pause=$(( reset - $(date +%s) + 180 ))
    if [ "$reset" -eq 0 ] || [ "$pause" -lt 300 ]; then pause=900; fi
    [ "$pause" -le 19000 ] || pause=19000
    echo "$(date '+%H:%M:%S') no room; sleeping $pause s" >&2
    sleep "$pause"
  done
  return 1
}
run_sessions() {  # one pass: batches of up to three while they fit under the ceiling
  local ceiling=$1 status used reset
  while [ ${#queue[@]} -gt 0 ]; do
    read -r status used reset < <(window)
    [[ "$status" == allowed* ]] || break
    local batch=() items=() dirs=() need=0
    for job in "${queue[@]:0:3}"; do
      IFS=: read -r tag pr est <<< "$job"
      [ $(( used + need + est )) -le "$ceiling" ] || break
      batch+=("$job"); items+=("${SET[$tag]}:$pr"); dirs+=("$(packet_dir $tag $pr)"); need=$(( need + est ))
    done
    [ ${#batch[@]} -gt 0 ] || break
    n=$(( n + 1 ))
    echo "$(date '+%H:%M:%S') batch g$n ($used% used, up to $need expected): ${items[*]}"
    $P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_C g$n $S/claude_logs G1 "${items[@]}"
    python3 $P/batch_report.py $S/claude_logs/g$n.jsonl $S/claude_logs/g$n.prompt > $S/report_g$n.txt
    grep -E '^Reviewer|^five-hour|^result' $S/report_g$n.txt
    local clean=1
    python3 $P/audit_batch.py $S/claude_logs/g$n.jsonl > $S/audit_g$n.txt || { clean=0; flagged=1; }
    cat $S/audit_g$n.txt
    for d in "${dirs[@]}"; do [ -f $d/findings.json ]; done
    if [ $clean = 1 ]; then
      { echo "results: stage G batch g$n on token C -- sessions briefed with pinpointed candidates, audited clean; committed by run_stage_g.sh unattended"
        echo; grep -E '^Reviewer|^five-hour' $S/report_g$n.txt; echo; cat $S/audit_g$n.txt; } > $S/msg_g$n.txt
      git add "${dirs[@]}"
      git commit -q -F $S/msg_g$n.txt
    fi
    queue=("${queue[@]:${#batch[@]}}")
  done
}

python3 - $P/candidate_retrieval.json <<'PY'
import json, sys
held = json.load(open(sys.argv[1]))
n = sum(r["entry"] for r in held.values())
print(f"retrieval gate: a candidate carries the entry of {n} of {len(held)} in-census asks (sessions run at 11 or more)")
sys.exit(0 if n >= 11 else 5)
PY
if [ ! -f $S/claude_stage_G/packets.done ]; then
  mkdir -p $S/claude_stage_G
  probe packets --set ${SET[val]} --sessions G1 --prs 30641 29842 32875 30458 28649 34091 --scratch $S/claude_stage_G \
    --candidates $P/briefs_candidates.json > /dev/null
  probe packets --set ${SET[post]} --sessions G1 --prs 41930 42814 43167 42184 --scratch $S/claude_stage_G \
    --candidates $P/briefs_candidates.json > /dev/null
  touch $S/claude_stage_G/packets.done
fi
echo "items in 30641's brief: $(grep -c '^- `' "$(packet_dir val 30641)/brief.md" || true)"
DRY_RUN=1 $P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_C dry_g $S/claude_logs G1 ${SET[val]}:30641 > /dev/null
echo "$(date '+%H:%M:%S') packets built; sessions on token C while they fit"
while [ ${#queue[@]} -gt 0 ]; do
  IFS=: read -r tag pr est <<< "${queue[0]}"
  wait_for_room "$est" 88 || { echo "sessions left unrun: ${queue[*]}"; exit 6; }
  run_sessions 88
done

printf '{"X1": {"kind": "claude"}, "X2": {"kind": "claude"}, "E1": {"kind": "claude"}, "G1": {"kind": "claude"}}\n' > $P/sources_G.json
declare -A PRS=([val]="30641 29842 32875 30458 28649 34091" [post]="41930 42814 43167 42184")
for tag in val post; do
  [ -f $P/blinding_G_${tag}_SEALED.json ] || probe seal --set ${SET[$tag]} --sessions X1 X2 E1 G1 --prs ${PRS[$tag]} --out $P/blinding_G_${tag}_SEALED.json
  probe match-inputs --set ${SET[$tag]} --seal $P/blinding_G_${tag}_SEALED.json --sources $P/sources_G.json --out $S/match_G_$tag > $S/match_G_$tag.prompts
done
for tag in val post; do
  wait_for_room 16 96 || { echo "no room for the matchers on $tag"; exit 7; }
  echo "$(date '+%H:%M:%S') matchers, $tag"
  $P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_C m_G_$tag $S/claude_logs - @$S/match_G_$tag.prompts
  python3 $P/batch_report.py $S/claude_logs/m_G_$tag.jsonl $S/claude_logs/m_G_$tag.prompt | grep -E '^Matcher|^five-hour'
  python3 $P/audit_batch.py $S/claude_logs/m_G_$tag.jsonl || flagged=1
  python3 $P/check_matches.py $S/match_G_$tag/m1 $S/match_G_$tag/m2
  mkdir -p $P/match_G_$tag
  cp $S/match_G_$tag/m1/matches.json $P/match_G_$tag/matches.1.json
  cp $S/match_G_$tag/m2/matches.json $P/match_G_$tag/matches.2.json
  cp $S/match_G_$tag/inputs/session_stats.json $P/match_G_$tag/session_stats.json
  probe unblind --set ${SET[$tag]} --seal $P/blinding_G_${tag}_SEALED.json --matches $P/match_G_$tag > $P/match_G_$tag/unblinded.json
done

echo "$(date '+%H:%M:%S') THE READING (rule: G - X on in-census asks, pooled, three PRs imputed; E beside it)"
python3 $P/read_stage.py G G X --impute 26755 36822 43192 > $S/read_G.txt
cat $S/read_G.txt
echo "--- E - X under the same seals ---"
python3 $P/read_stage.py G E X --impute 26755 36822 43192 > $S/read_G_E.txt
grep -E 'pooled' $S/read_G_E.txt
echo "--- the ten run PRs alone: asks per finding ---"
python3 $P/read_stage.py G G X > $S/read_G_run.txt
sed -n '/asks reached per finding/,/agreement/p' $S/read_G_run.txt
echo "--- candidates against application ---"
python3 $P/decompose_stage_g.py > $S/decompose_G.txt
cat $S/decompose_G.txt
if [ "$flagged" = 0 ]; then
  { echo "probes: stage G matched -- the guarded-rule delivery's tables and decomposition, committed by run_stage_g.sh unattended; the write-up follows"
    echo; cat $S/read_G.txt; echo; grep -E 'pooled' $S/read_G_E.txt; cat $S/decompose_G.txt; } > $S/msg_G.txt
  git add $P/sources_G.json $P/blinding_G_val_SEALED.json $P/blinding_G_post_SEALED.json $P/match_G_val $P/match_G_post
  git commit -q -F $S/msg_G.txt
fi
echo "$(date '+%H:%M:%S') STAGE G PIPELINE DONE flagged=$flagged"
