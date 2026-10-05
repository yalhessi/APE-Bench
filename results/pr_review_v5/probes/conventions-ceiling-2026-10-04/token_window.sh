# Sourced by stage G's runners: token C's windows, read from a one-word call, and a wait until the
# five-hour window has room. Needs $S (a scratch dir). Token B's login is disabled, so there is one
# token, and it is shared with the user's other sessions: the weekly window is guarded too.
window() {  # prints "<status> <five-hour % used> <five-hour reset epoch, or 0> <seven-day % used>"
  ( set +eu; source ~/.config/secrets/env.zsh; mkdir -p "$S/home_C"; cd "$S/home_C"
    HOME=$S/home_C CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_CODE_OAUTH_TOKEN_C" timeout 120 claude -p "Reply with the single word: ok" \
      --model claude-haiku-4-5-20251001 --output-format stream-json --verbose < /dev/null 2> /dev/null ) > "$S/limit_C.jsonl" || true
  python3 - "$S/limit_C.jsonl" <<'PY'
import json, sys
status, used, reset, week = "unknown", 100, 0, 100
for line in open(sys.argv[1]):
    try:
        d = json.loads(line)
    except ValueError:
        continue
    if d.get("type") == "rate_limit_event":
        info = d.get("rate_limit_info") or d
        windows = info.get("unifiedWindows") or {}
        five, seven = windows.get("five_hour") or {}, windows.get("seven_day") or {}
        status = str(info.get("status"))
        used = round(100 * (five.get("utilization") or 0))
        reset = int(five.get("resetsAt") or five.get("resets_at") or 0)
        week = round(100 * (seven.get("utilization") or 0))
        break
print(status, used, reset, week)
PY
}
# wait_for_room <points needed> <five-hour ceiling> <seven-day cap>: 0 once the five-hour window has
# room, 2 at once if the week is at or over its cap, 1 after twelve tries.
wait_for_room() {
  local need=$1 ceiling=$2 week_cap=$3 status used reset week pause
  for try in $(seq 1 12); do
    read -r status used reset week < <(window)
    echo "$(date '+%H:%M:%S') token C: $status, five-hour $used%, week $week%; need $need under $ceiling, week under $week_cap" >&2
    if [ "$week" -ge "$week_cap" ]; then return 2; fi
    if [[ "$status" == allowed* ]] && [ $(( used + need )) -le "$ceiling" ]; then return 0; fi
    pause=$(( reset - $(date +%s) + 180 ))
    if [ "$reset" -eq 0 ] || [ "$pause" -lt 300 ]; then pause=900; fi
    [ "$pause" -le 19000 ] || pause=19000
    echo "$(date '+%H:%M:%S') no room; sleeping $pause s" >&2
    sleep "$pause"
  done
  return 1
}
