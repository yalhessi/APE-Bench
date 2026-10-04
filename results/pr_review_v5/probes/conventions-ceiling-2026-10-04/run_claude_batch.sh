#!/usr/bin/env bash
# One batch of briefed Claude reviewer sessions on a named subscription token.
#
# X1 and X2 were `general-purpose` subagents of a Claude Code session (029323d7: claude-opus-5-5,
# effort xhigh, CLI 2.1.284), each given `probes.SESSION_PROMPT` for its packet. This starts a
# headless Claude Code session on another login and has it spawn the same subagents with the same
# prompt, so the reviewers differ from X in their brief and in what is listed in the README.
#
# usage: run_claude_batch.sh <TOKEN_VAR> <batch name> <log dir> <session> <set.yaml>:<pr> [...]
#   e.g. run_claude_batch.sh CLAUDE_CODE_OAUTH_TOKEN_C b1 /scratch/logs E1 configs/probe_sets/val_small12.yaml:30641
# The packets must exist (`cli probe packets`). Writes <log dir>/<batch>.prompt, .jsonl (the stream) and
# .err; `batch_report.py` reads the stream.
set -euo pipefail
token_var=$1; batch=$2; out=$3; session=$4; shift 4
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export PYTHONPATH=$PWD/src PATH="$HOME/.elan/bin:$PATH"
BIN=/research/projects/proofedit/ya475/APE-Bench/data/resources/claude-2.1.285-linux-x64
mkdir -p "$out"
ape/bin/python - "$out/$batch.prompt" "$session" "$@" <<'EOF'
import sys
from pathlib import Path
from src.mathlib_review.analysis import probes

out, session, items = sys.argv[1], sys.argv[2], sys.argv[3:]
parts = ["""You are launching reviewer sessions for a research study. Do none of the work yourself.

Call the Agent tool once for each session below, all in ONE message so that they run in parallel. For each call use subagent_type "general-purpose", run_in_background false, the description given, and the prompt given, copied verbatim and in full: add nothing, remove nothing, and do not summarise it. Do not read any file, run any command, or comment on the sessions.

When every session has returned, reply with one line per session: its description, then what it returned.
"""]
for item in items:
    if item.startswith("@"):
        # Blind judges instead of reviewers: the JSON lines `cli probe match-inputs` printed, one
        # folder and its prompt a line. The session argument is unused for these.
        import json
        with open(item[1:], encoding="utf-8") as handle:
            for row in map(json.loads, handle):
                if "prompt" in row:
                    parts.append(f"\n### Session\ndescription: {row.get('description') or 'Matcher ' + Path(row['folder']).name}\n"
                                 f"prompt:\n<<<\n{row['prompt']}\n>>>\n")
        continue
    spec_path, pr = item.rsplit(":", 1)
    packet = probes.load_probe_set(Path(spec_path)).session_dir(int(pr), session)
    if not (packet / "brief.md").exists() or probes.finished(packet):
        raise SystemExit(f"{packet}: no packet, or a finished session")
    parts.append(f"\n### Session\ndescription: Reviewer pr{pr} {session}\nprompt:\n<<<\n{probes.session_prompt(packet)}\n>>>\n")
Path(out).write_text("".join(parts))
EOF
[ "${DRY_RUN:-}" = 1 ] && { echo "$out/$batch.prompt"; exit 0; }   # the prompt only; spends nothing
set +u; source ~/.config/secrets/env.zsh; set -u
[ -n "${!token_var:-}" ] || { echo "$token_var is not set" >&2; exit 3; }
[ -z "$(env | grep '^ANTHROPIC_' || true)" ] || { echo "an ANTHROPIC_* variable is set: the CLI would bill or route elsewhere" >&2; exit 3; }
# The launching Claude Code session's own variables (effort, session id, socket) stay behind, as on
# the scaffold's subscription route; the login travels as the token.
drop=(); for v in $(env | grep -o '^CLAUDE[A-Z_0-9]*' || true); do drop+=(-u "$v"); done
exec env "${drop[@]}" CLAUDE_CODE_OAUTH_TOKEN="${!token_var}" ENABLE_CLAUDEAI_MCP_SERVERS=false \
  "$BIN" -p "$(cat "$out/$batch.prompt")" --model claude-opus-5-5 --effort xhigh \
  --dangerously-skip-permissions --output-format stream-json --verbose \
  < /dev/null > "$out/$batch.jsonl" 2> "$out/$batch.err"
