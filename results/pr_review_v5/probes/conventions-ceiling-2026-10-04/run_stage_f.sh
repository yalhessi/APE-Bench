#!/usr/bin/env bash
# Stage F's reviewer sessions and matching, unattended. Sessions A1 (brief X plus the applicable
# conventions) run on token C in batches of up to three while its window has room, in stage C's order;
# what does not fit waits for token B's reset. Then one seal a set over X1, X2, E1 and A1, two blind
# matchers a set, the unblinding, the reading and the decomposition. A step that fails stops it; an
# audit flag holds back the commits and is read by hand.
# usage: bash run_stage_f.sh <scratch dir> <HH:MM, when token B's window is back>
set -euo pipefail
S=$1; b_back=$2
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src PATH="$HOME/.elan/bin:$PATH"
P=results/pr_review_v5/probes/conventions-ceiling-2026-10-04
CB=results/pr_review_v5/adjudications/conventions-census-v1/reader_A/codebook.json
declare -A SET=([val]=configs/probe_sets/val_small12.yaml [post]=configs/probe_sets/postcutoff_2026_07_08_v1.yaml)
probe() { ape/bin/python -m src.mathlib_review.review.cli probe "$@"; }
flagged=0; n=0
# <set>:<pr>:<points of a window, at an unbriefed session's cost on that PR (the dearer bound)>
queue=(val:30641:10 val:29842:12 post:41930:10 val:32875:23 post:42814:24 val:30458:19 val:28649:19 post:42184:12 post:43167:23 val:34091:18)

packet_dir() {
  case "$1:$2" in
    val:30458|val:32875|val:34091) echo results/pr_review_v5/probes/construction-demo-2026-09-29/pr$2/A1 ;;
    val:*) echo results/pr_review_v5/probes/model-gap-val-small12/pr$2/A1 ;;
    post:*) echo results/pr_review_v5/probes/postcutoff-2026-09-29/pr$2/A1 ;;
  esac
}
window() {  # window <B|C>: prints "<status> <percent of the five-hour window used>"
  local name=$1 var=CLAUDE_CODE_OAUTH_TOKEN_$1
  ( set +eu; source ~/.config/secrets/env.zsh; mkdir -p "$S/home_$name"; cd "$S/home_$name"
    HOME=$S/home_$name CLAUDE_CODE_OAUTH_TOKEN="${!var}" timeout 120 claude -p "Reply with the single word: ok" \
      --model claude-haiku-4-5-20251001 --output-format stream-json --verbose < /dev/null 2> /dev/null ) > "$S/limit_$name.jsonl" || true
  python3 - "$S/limit_$name.jsonl" <<'EOF'
import json, sys
status, used = "unknown", 100
for line in open(sys.argv[1]):
    try:
        d = json.loads(line)
    except ValueError:
        continue
    if d.get("type") == "rate_limit_event":
        info = d.get("rate_limit_info") or d
        status = str(info.get("status"))
        used = round(100 * (((info.get("unifiedWindows") or {}).get("five_hour") or {}).get("utilization") or 0))
        break
print(status, used)
EOF
}
room() {  # room <B|C> <points needed> <ceiling>
  local status used
  read -r status used < <(window "$1")
  echo "$(date '+%H:%M:%S') token $1: $status, $used% used; need $2 under $3" >&2
  [[ "$status" == allowed* ]] && [ $(( used + $2 )) -le "$3" ]
}
run_sessions() {  # run_sessions <B|C> <ceiling>
  local token=$1 ceiling=$2
  while [ ${#queue[@]} -gt 0 ]; do
    local status used
    read -r status used < <(window "$token")
    [[ "$status" == allowed* ]] || break
    local batch=() items=() dirs=() need=0
    for job in "${queue[@]:0:3}"; do
      IFS=: read -r tag pr est <<< "$job"
      [ $(( used + need + est )) -le "$ceiling" ] || break
      batch+=("$job"); items+=("${SET[$tag]}:$pr"); dirs+=("$(packet_dir $tag $pr)"); need=$(( need + est ))
    done
    [ ${#batch[@]} -gt 0 ] || break
    n=$(( n + 1 ))
    echo "$(date '+%H:%M:%S') batch a$n on token $token ($used% used, up to $need expected): ${items[*]}"
    $P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_$token a$n $S/claude_logs A1 "${items[@]}"
    python3 $P/batch_report.py $S/claude_logs/a$n.jsonl $S/claude_logs/a$n.prompt > $S/report_a$n.txt
    grep -E '^Reviewer|^five-hour|^result' $S/report_a$n.txt
    local clean=1
    python3 $P/audit_batch.py $S/claude_logs/a$n.jsonl > $S/audit_a$n.txt || { clean=0; flagged=1; }
    cat $S/audit_a$n.txt
    for d in "${dirs[@]}"; do [ -f $d/findings.json ]; done
    if [ $clean = 1 ]; then
      { echo "results: stage F batch a$n on token $token -- sessions briefed with the applicable conventions, audited clean; committed by run_stage_f.sh unattended"
        echo; grep -E '^Reviewer|^five-hour' $S/report_a$n.txt; echo; cat $S/audit_a$n.txt; } > $S/msg_a$n.txt
      git add "${dirs[@]}"
      git commit -q -F $S/msg_a$n.txt
    fi
    queue=("${queue[@]:${#batch[@]}}")
  done
}

python3 - $P/applicable_retrieval.json <<'EOF'
import json, sys
held = json.load(open(sys.argv[1]))
print(f"retrieval gate: the applicable briefs hold the entry of {sum(held.values())} of {len(held)} in-census asks (sessions run at 11 or more)")
sys.exit(0 if sum(held.values()) >= 11 else 5)
EOF
if [ ! -f $S/claude_stage_A/packets.done ]; then
  mkdir -p $S/claude_stage_A
  probe packets --set ${SET[val]} --sessions A1 --prs 30641 29842 32875 30458 28649 34091 --scratch $S/claude_stage_A \
    --conventions $P/briefs_applicable.json --codebook $CB > /dev/null
  probe packets --set ${SET[post]} --sessions A1 --prs 41930 42814 43167 42184 --scratch $S/claude_stage_A \
    --conventions $P/briefs_applicable.json --codebook $CB > /dev/null
  touch $S/claude_stage_A/packets.done
fi
echo "sentences in 30641's brief: $(grep -c '^- ' "$(packet_dir val 30641)/brief.md")"
DRY_RUN=1 $P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_C dry_a $S/claude_logs A1 ${SET[val]}:30641 > /dev/null
echo "$(date '+%H:%M:%S') packets built; sessions on token C while they fit"
run_sessions C 88
if [ ${#queue[@]} -gt 0 ]; then
  echo "$(date '+%H:%M:%S') ${#queue[@]} session(s) wait for token B at $b_back: ${queue[*]}"
  pause=$(( $(date -d "today $b_back" +%s) - $(date +%s) )); [ "$pause" -le 0 ] || sleep "$pause"
  for try in 1 2 3 4 5 6; do if room B 0 50; then break; fi; sleep 300; done
  run_sessions B 72
fi
[ ${#queue[@]} -eq 0 ] || { echo "sessions left unrun: ${queue[*]}"; exit 6; }

printf '{"X1": {"kind": "claude"}, "X2": {"kind": "claude"}, "E1": {"kind": "claude"}, "A1": {"kind": "claude"}}\n' > $P/sources_F.json
declare -A PRS=([val]="30641 29842 32875 30458 28649 34091" [post]="41930 42814 43167 42184")
for tag in val post; do
  [ -f $P/blinding_F_${tag}_SEALED.json ] || probe seal --set ${SET[$tag]} --sessions X1 X2 E1 A1 --prs ${PRS[$tag]} --out $P/blinding_F_${tag}_SEALED.json
  probe match-inputs --set ${SET[$tag]} --seal $P/blinding_F_${tag}_SEALED.json --sources $P/sources_F.json --out $S/match_F_$tag > $S/match_F_$tag.prompts
done
mt=""
for try in 1 2 3 4 5 6 7 8; do
  if room B 30 98; then mt=B; break; fi
  if room C 30 94; then mt=C; break; fi
  pause=$(( $(date -d "today $b_back" +%s) - $(date +%s) )); [ "$pause" -ge 300 ] || pause=300
  sleep "$pause"
done
[ -n "$mt" ] || { echo "no token has room for the matchers"; exit 7; }
for tag in val post; do
  echo "$(date '+%H:%M:%S') matchers, $tag, on token $mt"
  $P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_$mt m_F_$tag $S/claude_logs - @$S/match_F_$tag.prompts
  python3 $P/batch_report.py $S/claude_logs/m_F_$tag.jsonl $S/claude_logs/m_F_$tag.prompt | grep -E '^Matcher|^five-hour'
  python3 $P/audit_batch.py $S/claude_logs/m_F_$tag.jsonl || flagged=1
  python3 $P/check_matches.py $S/match_F_$tag/m1 $S/match_F_$tag/m2
  mkdir -p $P/match_F_$tag
  cp $S/match_F_$tag/m1/matches.json $P/match_F_$tag/matches.1.json
  cp $S/match_F_$tag/m2/matches.json $P/match_F_$tag/matches.2.json
  cp $S/match_F_$tag/inputs/session_stats.json $P/match_F_$tag/session_stats.json
  probe unblind --set ${SET[$tag]} --seal $P/blinding_F_${tag}_SEALED.json --matches $P/match_F_$tag > $P/match_F_$tag/unblinded.json
done

echo "$(date '+%H:%M:%S') THE READING (rule: A - X on in-census asks, pooled, three PRs imputed; E beside it)"
python3 $P/read_stage.py F A X --impute 26755 36822 43192 > $S/read_F.txt
cat $S/read_F.txt
echo "--- E - X under the same seals ---"
python3 $P/read_stage.py F E X --impute 26755 36822 43192 > $S/read_F_E.txt
grep -E 'pooled' $S/read_F_E.txt
echo "--- the ten run PRs alone: asks per finding ---"
python3 $P/read_stage.py F A X > $S/read_F_run.txt
sed -n '/asks reached per finding/,/agreement/p' $S/read_F_run.txt
echo "--- retrieval against application ---"
python3 $P/decompose_floor.py > $S/decompose_F.txt
cat $S/decompose_F.txt
if [ "$flagged" = 0 ]; then
  { echo "probes: stage F matched -- the floor's tables and decomposition, committed by run_stage_f.sh unattended; the write-up follows"
    echo; cat $S/read_F.txt; echo; grep -E 'pooled' $S/read_F_E.txt; cat $S/decompose_F.txt; } > $S/msg_F.txt
  git add $P/sources_F.json $P/blinding_F_val_SEALED.json $P/blinding_F_post_SEALED.json $P/match_F_val $P/match_F_post
  git commit -q -F $S/msg_F.txt
fi
echo "$(date '+%H:%M:%S') STAGE F PIPELINE DONE flagged=$flagged"
