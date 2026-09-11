#!/usr/bin/env bash
# UserPromptSubmit hook. Prints one [session] status line per prompt, plus a
# warning line for each threshold crossed. Stdout is added to Claude's context;
# it never blocks the prompt. Companion to the "Session discipline" and "Git"
# sections of CLAUDE.md: the rules live there, the facts they need arrive here.
set -u
input=$(cat 2>/dev/null || true)
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null)
transcript=$(printf '%s' "$input" | jq -r '.transcript_path // empty' 2>/dev/null)
cd "${cwd:-.}" 2>/dev/null || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# The median commit on this repo touches 5 files (p90: 16); past this much
# uncommitted work a step has almost certainly finished without its commit.
MAX_FILES=10
MAX_LINES=400

branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')
changed=$(git status --porcelain --untracked-files=all 2>/dev/null | wc -l | tr -d ' ')
untracked=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')
read -r ins del < <(git diff HEAD --numstat 2>/dev/null | awk '{a+=$1; d+=$2} END {print a+0, d+0}')
lines=$((ins + del))

compactions=0
if [ -n "$transcript" ] && [ -f "$transcript" ]; then
  compactions=$(grep -c '"subtype":"compact_boundary"' "$transcript" 2>/dev/null)
  compactions=${compactions:-0}
fi

echo "[session] branch=$branch  uncommitted=$changed files (+$ins/-$del, $untracked untracked)  compactions=$compactions"

if [ "$branch" = "main" ]; then
  echo "[session] WARNING: on main. main is the upstream APE-Bench drop and the guard hook refuses commits here. Switch to develop or a topic branch first."
fi
if [ "$changed" -gt "$MAX_FILES" ] || [ "$lines" -gt "$MAX_LINES" ]; then
  echo "[session] Uncommitted work is past the small-commit threshold ($MAX_FILES files / $MAX_LINES lines). Commit the finished part as one logical commit before taking on more."
fi
if [ "$compactions" -ge 1 ]; then
  echo "[session] This session has compacted ${compactions}x. If this prompt starts a new thread (a different feature, experiment or subsystem), say so in one line and recommend a fresh session before continuing."
fi
exit 0
