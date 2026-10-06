#!/usr/bin/env bash
# PostToolUse hook (matcher: Bash). After a `git commit` has gone in, tells the session -- as a
# note, never a refusal -- when the commit mixed a framework (kernel) file with an exploration
# file. Nothing is blocked: the commit already happened, and a mixed commit is often right.
#
# Why (docs/research/codebase-redesign-2026-10.md §1.3, §4.1): about half the files of every
# wide thread were fixes to shared machinery found while exploring, committed together with the
# exploration. Split, the fix is one small commit another thread can take, and the kernel's
# history says what changed in the kernel. The guard (`guard.sh`) cannot see this: at PreToolUse
# the `git add` in `git add ... && git commit` has not run yet, so only the commit itself shows
# what went in.
#
# Kernel and exploration are listed below; tests, docs and everything else are neither.
set -u
input=$(cat 2>/dev/null || true)
[ "$(printf '%s' "$input" | jq -r '.tool_name // empty' 2>/dev/null)" = "Bash" ] || exit 0
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)
GIT='(^|[;&|(])[[:space:]]*git[[:space:]]+([^;&|]*[[:space:]])?'
printf '%s' "$cmd" | grep -qE "${GIT}commit([[:space:]]|$)" || exit 0
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null)
cd "${cwd:-.}" 2>/dev/null || exit 0

# Only a commit this command made: HEAD written in the last two minutes, and not a merge.
stamp=$(git log -1 --format=%ct HEAD 2>/dev/null) || exit 0
[ $(( $(date +%s) - stamp )) -le 120 ] || exit 0
[ "$(git rev-list --parents -n 1 HEAD 2>/dev/null | wc -w)" -le 2 ] || exit 0

R=src/ape/tasks/lean_tasks/formal_math/review
kernel=() exploration=()
while IFS= read -r f; do
  case "$f" in
    src/ape/orchestration/*|src/ape/toolkits/*|src/ape/scaffolds/*|src/ape/llm_clients/*|src/ape/runtime/*|\
    src/ape/tasks/base.py|$R/base.py|$R/candidates.py|$R/delegation.py|\
    src/mathlib_review/review/runner.py|src/mathlib_review/review/cli.py|src/mathlib_review/review/finalize.py|\
    src/mathlib_review/schema/*|src/mathlib_review/io.py|src/mathlib_review/run_state.py|\
    src/mathlib_review/run_config.py|src/mathlib_review/paths.py)
      kernel+=("$f") ;;
    configs/*|results/*|\
    $R/focused_prompts.py|$R/prompts.py|$R/structured.py|$R/structured_critic.py|$R/context_tools.py|\
    src/mathlib_review/agenda/registry.py|src/mathlib_review/evidence/operators/*|src/mathlib_review/conventions/*)
      exploration+=("$f") ;;
  esac
done < <(git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null)

[ ${#kernel[@]} -gt 0 ] && [ ${#exploration[@]} -gt 0 ] || exit 0

list() { local n=$#; local shown=("${@:1:4}"); local out; out=$(printf '%s, ' "${shown[@]}"); out=${out%, }; [ "$n" -gt 4 ] && out="$out and $((n - 4)) more"; printf '%s' "$out"; }
sha=$(git rev-parse --short HEAD)
note="Commit $sha mixes framework files ($(list "${kernel[@]}")) with exploration files ($(list "${exploration[@]}")). Nothing was blocked. If the framework change is a fix to shared machinery, it reads better as its own commit, ahead of the exploration: another thread can take it alone, and the framework's history says what changed in it (docs/research/codebase-redesign-2026-10.md section 4.1). If the two are one change, carry on."
jq -n --arg c "$note" '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$c}}'
exit 0
