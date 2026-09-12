#!/usr/bin/env bash
# PreToolUse hook (matcher: Bash|Edit|Write|MultiEdit|NotebookEdit). Refuses what the
# code cannot refuse on its own:
#   1. `git commit` while on main -- main is the upstream APE-Bench drop.
#   2. Edit/Write under a frozen artifact root -- release manifests hash these trees,
#      so a hand edit breaks `verify_frozen verify` for every release.
#   3. Rewriting a working tree that other Claude Code sessions are using (switch,
#      checkout, rebase, clean, reset --hard/--merge): a branch is a pointer, the tree is
#      the files, and their files change under them. That work goes in a worktree.
#   4. A bare `git stash`, or `stash pop`/`clear`, while other sessions are anywhere in
#      this repository: the stash stack is shared by every worktree.
# Anything else falls through to the normal permission flow (no output, exit 0).
# Escape hatch for 3 and 4, once the other sessions are known to be finished:
# prefix the command with CLAUDE_ALLOW_TREE_SWITCH=1.
set -u
. "$(dirname "$0")/lib.sh"
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

# `git <global opts> <subcommand>` at the start of a shell segment.
GIT='(^|[;&|(])[[:space:]]*git[[:space:]]+([^;&|]*[[:space:]])?'

case "$tool" in
  Bash)
    cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)
    if printf '%s' "$cmd" | grep -qE "${GIT}commit([[:space:]]|$)"; then
      branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')
      if [ "$branch" = "main" ]; then
        deny "Refused: 'git commit' on main. main is the upstream APE-Bench drop; nothing is committed there. Commit on develop or a topic branch (git switch develop)."
      fi
    fi
    case "$cmd" in *CLAUDE_ALLOW_TREE_SWITCH=1*) exit 0 ;; esac
    if printf '%s' "$cmd" | grep -qE "${GIT}(switch|checkout|rebase|clean)([[:space:]]|$)|${GIT}reset[[:space:]]+[^;&|]*--(hard|merge)"; then
      others=$(sessions_sharing_tree)
      if [ -n "$others" ]; then
        deny "Refused: this rewrites the working tree, and other Claude Code sessions are using it: $(describe_pids $others). A switch, checkout, rebase, clean or hard reset here changes their files under them (this is what happened on 2026-09-12). Do the work in a worktree: $WORKTREE_HOWTO. If those sessions are finished, close them; or, having checked, prefix the command with CLAUDE_ALLOW_TREE_SWITCH=1."
      fi
    fi
    if printf '%s' "$cmd" | grep -qE "${GIT}stash([[:space:]]|$)"; then
      others=$(sessions_sharing_repo)
      if [ -n "$others" ]; then
        recipe="Set work aside with a WIP commit instead. If you must stash: git stash push -u -m <tag>, find its SHA with git stash list --format='%H %gs', restore with git stash apply <sha> (never pop), then drop that entry. Prefix with CLAUDE_ALLOW_TREE_SWITCH=1 to override."
        if printf '%s' "$cmd" | grep -qE "${GIT}stash[[:space:]]+(pop|clear)([[:space:]]|$)"; then
          deny "Refused: 'git stash pop/clear' while other Claude Code sessions are active in this repository ($(describe_pids $others)); the stash stack is shared by every worktree, so this can take or drop their entries. $recipe"
        fi
        if printf '%s' "$cmd" | grep -qE "${GIT}stash([[:space:]]+(push|save))?([[:space:]]+-[^m[:space:]][^[:space:]]*)*[[:space:]]*($|[;&|)])" \
           && ! printf '%s' "$cmd" | grep -qE -- "(^|[[:space:]])(-m|--message)"; then
          deny "Refused: an untagged 'git stash' while other Claude Code sessions are active in this repository ($(describe_pids $others)); the stash stack is shared by every worktree. $recipe"
        fi
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
