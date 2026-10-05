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
. $P/token_window.sh
# Sessions run one at a time. Each is started only if the five-hour window has room for it at the
# dearest cost metered so far (stage F's per-session points times cost_scale/10, 2.5x until a
# session here is metered: on 2026-10-05 subagents used token C's window about three times faster
# than stage F's did), and only while the week is under SESSION_WEEK_CAP. A session the limit kills
# leaves no findings.json; the runner then stops uncommitted, to be read by hand.
SESSION_WEEK_CAP=${SESSION_WEEK_CAP:-72}; MATCH_WEEK_CAP=${MATCH_WEEK_CAP:-85}; cost_scale=25
run_sessions() {
  local status used0 used1 reset week rc
  while [ ${#queue[@]} -gt 0 ]; do
    IFS=: read -r tag pr est <<< "${queue[0]}"
    local need=$(( est * cost_scale / 10 )) dir; dir=$(packet_dir $tag $pr)
    rc=0; wait_for_room "$need" 97 "$SESSION_WEEK_CAP" || rc=$?
    if [ $rc = 2 ]; then echo "$(date '+%H:%M:%S') the week is at ${SESSION_WEEK_CAP}%: sessions stop; unrun: ${queue[*]}"; break; fi
    if [ $rc != 0 ]; then echo "$(date '+%H:%M:%S') no room after twelve tries; unrun: ${queue[*]}"; break; fi
    read -r status used0 reset week < <(window)
    n=$(( n + 1 ))
    echo "$(date '+%H:%M:%S') batch g$n (five-hour $used0%, week $week%, about $need expected): ${SET[$tag]}:$pr"
    $P/run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_C g$n $S/claude_logs G1 "${SET[$tag]}:$pr"
    read -r status used1 reset week < <(window)
    if [ "$used1" -gt "$used0" ]; then
      local scale=$(( (used1 - used0) * 10 / est ))
      [ "$scale" -le "$cost_scale" ] || cost_scale=$scale
    fi
    python3 $P/batch_report.py $S/claude_logs/g$n.jsonl $S/claude_logs/g$n.prompt > $S/report_g$n.txt
    grep -E '^Reviewer|^five-hour|^result' $S/report_g$n.txt
    echo "metered: five-hour $used0% -> $used1%, week now $week%; cost_scale now $cost_scale"
    [ -f $dir/findings.json ] || { echo "pr$pr: no findings.json (killed?); stopping uncommitted"; exit 8; }
    local clean=1
    python3 $P/audit_batch.py $S/claude_logs/g$n.jsonl > $S/audit_g$n.txt || { clean=0; flagged=1; }
    cat $S/audit_g$n.txt
    if [ $clean = 1 ]; then
      { echo "results: stage G batch g$n on token C -- the session on $pr briefed with pinpointed candidates, audited clean; committed by run_stage_g.sh unattended"
        echo; grep -E '^Reviewer|^five-hour' $S/report_g$n.txt; echo "metered: five-hour $used0% -> $used1%, week $week%"; echo; cat $S/audit_g$n.txt; } > $S/msg_g$n.txt
      git add "$dir"
      git commit -q -F $S/msg_g$n.txt
    fi
    queue=("${queue[@]:1}")
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
run_sessions

printf '{"X1": {"kind": "claude"}, "X2": {"kind": "claude"}, "E1": {"kind": "claude"}, "G1": {"kind": "claude"}}\n' > $P/sources_G.json
# Match the PRs whose G1 session finished: all ten, or the prefix the week allowed (reported as partial).
declare -A PRS=([val]="" [post]="")
for job in val:30641 val:29842 val:32875 val:30458 val:28649 val:34091 post:41930 post:42814 post:43167 post:42184; do
  IFS=: read -r tag pr <<< "$job"
  [ -f "$(packet_dir $tag $pr)/findings.json" ] && PRS[$tag]="${PRS[$tag]} $pr"
done
echo "matching: val [${PRS[val]} ] post [${PRS[post]} ]"
[ -n "${PRS[val]}" ] && [ -n "${PRS[post]}" ] || { echo "a set has no finished G1 session; matching waits"; exit 9; }
for tag in val post; do
  [ -f $P/blinding_G_${tag}_SEALED.json ] || probe seal --set ${SET[$tag]} --sessions X1 X2 E1 G1 --prs ${PRS[$tag]} --out $P/blinding_G_${tag}_SEALED.json
  probe match-inputs --set ${SET[$tag]} --seal $P/blinding_G_${tag}_SEALED.json --sources $P/sources_G.json --out $S/match_G_$tag > $S/match_G_$tag.prompts
done
for tag in val post; do
  rc=0; wait_for_room 40 97 "$MATCH_WEEK_CAP" || rc=$?
  [ $rc = 0 ] || { echo "no room for the matchers on $tag (week cap ${MATCH_WEEK_CAP}% or no window); sessions are committed, matching waits"; exit 7; }
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
