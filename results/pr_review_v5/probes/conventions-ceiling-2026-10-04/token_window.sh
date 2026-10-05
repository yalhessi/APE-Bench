# Sourced by stage G's runners: token C's five-hour window, read from a one-word call, and a wait
# until it has room. Needs $S (a scratch dir). Token B's login is disabled, so there is one token.
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
