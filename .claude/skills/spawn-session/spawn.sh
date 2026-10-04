#!/usr/bin/env bash
# Start one thread in its own background Claude Code session: a topic branch and worktree off
# develop (the CLAUDE.md recipe), then `claude --bg` there with a written brief. Model, effort and
# permission mode default to the spawning session's own, read from its transcript. See SKILL.md.
#
#   spawn.sh start <topic> --brief <file> [--model M] [--effort E] [--permission-mode P] [--base REF]
#   spawn.sh defaults           what start would inherit from this session
#   spawn.sh report <id|name>   a spawned session's status and its last message
#   spawn.sh wait <id|name>     block while it is busy (run it in the background to be woken)
set -eu

die() { echo "spawn-session: $*" >&2; exit 1; }
command -v jq >/dev/null || die "needs jq"
common=$(git rev-parse --git-common-dir 2>/dev/null) || die "run inside the repository"
main=$(cd "$(dirname "$(cd "$common" && pwd -P)")" && pwd -P)

transcript_of() {  # $1 = session id -> its transcript, wherever its working directory was
  find "$HOME/.claude/projects" -maxdepth 2 -name "$1.jsonl" -print -quit 2>/dev/null
}

defaults() {  # sets model, effort, mode from this session's transcript (SPAWN_TRANSCRIPT overrides)
  local t=${SPAWN_TRANSCRIPT:-}
  [ -n "$t" ] || { [ -n "${CLAUDE_CODE_SESSION_ID:-}" ] && t=$(transcript_of "$CLAUDE_CODE_SESSION_ID"); }
  [ -n "$t" ] && [ -r "$t" ] || die "cannot find this session's transcript (CLAUDE_CODE_SESSION_ID unset?); pass --model, --effort and --permission-mode"
  model=$(jq -r 'select(.type=="assistant") | .message.model // empty' "$t" | grep -v '^<synthetic>$' | tail -1 || true)
  effort=$(jq -r 'select(.type=="assistant") | .effort // empty' "$t" | tail -1)
  effort=${effort:-${CLAUDE_EFFORT:-}}
  mode=$(jq -r '.permissionMode // empty' "$t" | tail -1)
}

case "${1:-}" in
  defaults)
    defaults; printf 'model=%s\neffort=%s\npermission-mode=%s\n' "$model" "$effort" "$mode"; exit 0 ;;
  report)
    [ -n "${2:-}" ] || die "usage: spawn.sh report <id|name>"
    row=$(claude agents --json --all 2>/dev/null | jq -c --arg k "$2" '[.[] | select(.name==$k or (.sessionId|startswith($k)))] | last // empty')
    [ -n "$row" ] || die "no session '$2' in claude agents --all"
    echo "$row" | jq -r '"\(.name) · \(.sessionId[0:8]) · \(.kind) · \(.status) · \(.cwd)"'
    t=$(transcript_of "$(echo "$row" | jq -r .sessionId)")
    [ -n "$t" ] || die "no transcript yet"
    jq -rs '[.[] | select(.type=="assistant") | [.message.content[]? | select(.type=="text") | .text] | join("")
             | select(. != "")] | last // "(no message yet)"' "$t"
    exit 0 ;;
  wait)  # for run_in_background: returns once the session is not busy (idle, waiting, or gone)
    [ -n "${2:-}" ] || die "usage: spawn.sh wait <id|name>"
    while claude agents --json 2>/dev/null | jq -e --arg k "$2" \
        'any(.[]; (.name==$k or (.sessionId|startswith($k))) and .status=="busy")' >/dev/null; do sleep 20; done
    exit 0 ;;
  start) shift ;;
  *) sed -n '2,9p' "$0" >&2; exit 2 ;;
esac

[ -z "${APE_SPAWNED_BY:-}" ] || die "this session was itself spawned (by $APE_SPAWNED_BY), and spawned sessions do not spawn: write the follow-on thread into docs/todo/ and name it in your report"
topic=${1:-}; shift || true
case "$topic" in ''|-*|*[!a-z0-9._-]*) die "topic must be a branch-safe name: lower case, digits, . _ -" ;; esac
brief='' model='' effort='' mode='' base=develop
while [ $# -gt 0 ]; do
  case "$1" in
    --brief) brief=${2:?}; shift 2 ;;
    --model) model=${2:?}; shift 2 ;;
    --effort) effort=${2:?}; shift 2 ;;
    --permission-mode) mode=${2:?}; shift 2 ;;
    --base) base=${2:?}; shift 2 ;;
    *) die "unknown argument: $1" ;;
  esac
done
[ -n "$brief" ] && [ -s "$brief" ] || die "--brief <file> is required: the thread starts from a written brief, not from this conversation"
given_model=$model given_effort=$effort given_mode=$mode
if [ -z "$model" ] || [ -z "$effort" ] || [ -z "$mode" ]; then defaults; fi
model=${given_model:-$model} effort=${given_effort:-$effort} mode=${given_mode:-$mode}
[ -n "$model" ] || die "no model given and none found in this session's transcript"
case "$effort" in low|medium|high|xhigh|max) ;; *) die "effort '$effort' is not one of low medium high xhigh max" ;; esac
case "$mode" in acceptEdits|auto|bypassPermissions|manual|dontAsk|plan) ;; *) die "permission mode '$mode' is not one claude accepts" ;; esac
# `claude --bg` refuses bypass until the disclaimer is accepted in the CLI itself (VSCode's own
# allowDangerouslySkipPermissions does not count), and auto until it is opted into once. Accepting
# writes skipDangerousModePermissionPrompt to ~/.claude/settings.json (2.1.287); the CLI also
# honours bypassPermissionsModeAccepted in ~/.claude.json.
if [ "$mode" = bypassPermissions ] \
   && [ "$(jq -r '.bypassPermissionsModeAccepted // false' "$HOME/.claude.json" 2>/dev/null)" != true ] \
   && [ "$(jq -r '.skipDangerousModePermissionPrompt // false' "$HOME/.claude/settings.json" 2>/dev/null)" != true ]; then
  die "--bg in bypassPermissions needs the disclaimer accepted once: the user runs \`claude --dangerously-skip-permissions\` in a terminal. Or pass another --permission-mode"
fi
claude agents --json 2>/dev/null | jq -e --arg n "$topic" 'any(.[]; .name==$n)' >/dev/null \
  && die "a live session is already named '$topic' (claude agents)"

wt="$main/.claude/worktrees/$topic"
if git -C "$main" worktree list --porcelain | grep -qxF "worktree $wt"; then
  others=$(cd "$wt" && bash -c 'source "$1"; sessions_sharing_tree' _ "$main/.claude/hooks/lib.sh" || true)
  [ -z "$others" ] || die "a session is already working in $wt (pids $others): one working tree per session"
elif git -C "$main" show-ref --verify -q "refs/heads/$topic"; then
  git -C "$main" worktree add -q "$wt" "$topic"
else
  git -C "$main" worktree add -q -b "$topic" "$wt" "$base"
fi
"$main/.claude/worktree-setup.sh" "$wt" >/dev/null

parent=${CLAUDE_CODE_SESSION_ID:-unknown}
rules="You were started by another Claude Code session (${parent:0:8}) through the spawn-session skill, to work one thread with nobody watching. On top of CLAUDE.md:
- Your thread is the brief in your first message, on branch $topic in $wt. Work only that thread; any other hypothesis you surface goes into docs/todo/ as CLAUDE.md says.
- Commit at every step boundary on $topic. Never merge into develop, push, rewrite history or delete a branch: merging is the spawning session's or the user's step.
- Spend nothing: no command with --execute and no paid API call, unless your brief names that exact command as authorized.
- Do not start sessions yourself (spawn.sh refuses in a spawned session); name follow-on threads in your report.
- Nobody answers questions while you run, so do not use AskUserQuestion. When a decision is the user's, stop and put it in your report.
- Your last message is your report, read by the spawning session: what is committed (hashes), what was measured, what is left, and any decision needed."
out=$(cd "$wt" && claude "$(cat "$brief")" --bg -n "$topic" --model "$model" --effort "$effort" \
  --permission-mode "$mode" --settings "$(jq -cn --arg p "$parent" '{env:{APE_SPAWNED_BY:$p}}')" \
  --append-system-prompt "$rules" 2>&1) || die "claude --bg failed: $out"
id=$(printf '%s\n' "$out" | sed -n 's/^backgrounded · \([0-9a-f]*\) · .*/\1/p')
[ -n "$id" ] || die "claude --bg did not report a session id: $out"
printf 'spawned %s · %s\n  branch %s  worktree %s\n  model %s  effort %s  permission-mode %s\n' \
  "$topic" "$id" "$topic" "$wt" "$model" "$effort" "$mode"
printf '  watch: claude logs %s   report: %s report %s   open: claude attach %s\n' "$id" "$0" "$id" "$id"
