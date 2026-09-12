#!/usr/bin/env bash
# Sourced by the hooks. Which other Claude Code sessions exist, and which of them share
# this working tree or this repository. Linux /proc only; elsewhere every function prints
# nothing and the callers fall through to "no other session".
#
# A branch is a pointer; the working tree is the files. Two sessions in one directory share
# the files whatever branch each believes it is on (2026-09-12: a branch created in a shared
# tree took the other session's commit with it, and develop had to be reset by hand).

_argv() {  # a pid from pgrep can be gone by the time it is read; then it is nobody
  [ -r "/proc/$1/cmdline" ] || return 1
  { tr '\0' '\n' < "/proc/$1/cmdline"; } 2>/dev/null | sed -n "${2}p"
}

_is_claude_session() {  # $1 = pid. The native binary is `claude`; an npm install is `node .../claude`.
  local a0 a1
  a0=$(basename "$(_argv "$1" 1)" 2>/dev/null)
  case "$a0" in
    claude) return 0 ;;
    node) a1=$(_argv "$1" 2); case "$a1" in *claude*) return 0 ;; esac ;;
  esac
  return 1
}

_self_session_pid() {  # the claude process this hook runs under
  local p=$$ i=0
  while [ "${p:-1}" -gt 1 ] && [ "$i" -lt 8 ]; do
    if _is_claude_session "$p"; then echo "$p"; return; fi
    p=$(awk '/^PPid:/{print $2}' "/proc/$p/status" 2>/dev/null); i=$((i+1))
  done
}

other_claude_sessions() {  # "pid<TAB>cwd" for every other session of this user
  [ -d /proc ] || return 0
  local me p c
  me=$(_self_session_pid)
  for p in $(pgrep -u "$(id -un)" -f claude 2>/dev/null); do
    [ "$p" = "$me" ] && continue
    _is_claude_session "$p" || continue
    c=$(readlink "/proc/$p/cwd" 2>/dev/null) || continue
    printf '%s\t%s\n' "$p" "$c"
  done
}

_common_dir() { local d; d=$(git -C "${1:-.}" rev-parse --git-common-dir 2>/dev/null) || return 1; (cd "${1:-.}" && cd "$d" && pwd -P); }

sessions_sharing_tree() {  # pids of other sessions whose working tree is this one
  local top p c
  top=$(git rev-parse --show-toplevel 2>/dev/null) || return 0
  other_claude_sessions | while IFS=$'\t' read -r p c; do
    [ "$(git -C "$c" rev-parse --show-toplevel 2>/dev/null)" = "$top" ] && echo "$p"
  done
}

sessions_sharing_repo() {  # pids of other sessions in any worktree of this repository
  local common p c
  common=$(_common_dir .) || return 0
  other_claude_sessions | while IFS=$'\t' read -r p c; do
    [ "$(_common_dir "$c")" = "$common" ] && echo "$p"
  done
}

describe_pids() {  # "pid (age)" list for a message
  local p out=""
  for p in "$@"; do out="$out$p ($(ps -o etime= -p "$p" 2>/dev/null | tr -d ' ')) "; done
  printf '%s' "${out% }"
}

WORKTREE_HOWTO='git worktree add -b <topic> .claude/worktrees/<topic> develop && .claude/worktree-setup.sh .claude/worktrees/<topic>'
