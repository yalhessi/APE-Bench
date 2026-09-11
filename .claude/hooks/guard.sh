#!/usr/bin/env bash
# PreToolUse hook (matcher: Bash|Edit|Write|MultiEdit|NotebookEdit). Refuses the
# two mistakes the code cannot refuse on its own:
#   1. `git commit` while on main -- main is the upstream APE-Bench drop.
#   2. Edit/Write under a frozen artifact root -- release manifests hash these
#      trees, so a hand edit breaks `verify_frozen verify` for every release.
# Anything else falls through to the normal permission flow (no output, exit 0).
set -u
input=$(cat 2>/dev/null || true)
tool=$(printf '%s' "$input" | jq -r '.tool_name // empty' 2>/dev/null)
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null)
cd "${cwd:-.}" 2>/dev/null || exit 0

deny() {
  jq -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
  exit 0
}

# FROZEN_ROOTS in src/mathlib_review/release/verify_frozen.py, plus the cached
# GitHub bundles that 11 frozen v4 manifests hash as trees.
FROZEN_ROOTS="inputs/pr_review_v4/ results/pr_review_v4/ data/pr_review_v2/"

case "$tool" in
  Bash)
    cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)
    if printf '%s' "$cmd" | grep -qE '(^|[;&|(])[[:space:]]*git[[:space:]]+([^;&|]*[[:space:]])?commit([[:space:]]|$)'; then
      branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')
      if [ "$branch" = "main" ]; then
        deny "Refused: 'git commit' on main. main is the upstream APE-Bench drop; nothing is committed there. Commit on develop or a topic branch (git switch develop)."
      fi
    fi
    ;;
  Edit|Write|MultiEdit|NotebookEdit)
    path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null)
    [ -n "$path" ] || exit 0
    root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
    case "$path" in /*) abs="$path" ;; *) abs="$PWD/$path" ;; esac
    rel="${abs#"$root"/}"
    for fr in $FROZEN_ROOTS; do
      case "$rel" in
        "$fr"*)
          deny "Refused: '$rel' is under the frozen root '$fr'. Frozen release manifests hash this tree (src/mathlib_review/release/verify_frozen.py; the data/pr_review_v2 write guards). Add or change artifacts only through the release tooling, never by hand."
          ;;
      esac
    done
    ;;
esac
exit 0
