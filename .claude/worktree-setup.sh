#!/usr/bin/env bash
# Make a worktree runnable. Links the machine-local, untracked trees from the main checkout
# -- the venv, `.ape/` run artifacts, the data stores, the bulk derived inputs/results --
# so runs and tests here see the same stores as the main tree. Tracked paths are never
# linked over: the worktree has its own copies of those. Idempotent.
#
#   usage: .claude/worktree-setup.sh [worktree-path]      (default: the current directory)
#
# Claude Code's own worktrees (EnterWorktree, --worktree) get `ape` and `.ape` from
# worktree.symlinkDirectories in .claude/settings.json; run this for the rest.
set -eu
wt=$(cd "${1:-.}" && pwd -P)
common=$(cd "$wt" && cd "$(git rev-parse --git-common-dir)" && pwd -P)
main=$(dirname "$common")
if [ "$wt" = "$main" ]; then echo "$wt is the main checkout; nothing to link." >&2; exit 1; fi

linked=0
link() {  # $1 = path relative to the repository root
  [ -e "$main/$1" ] || return 0
  git -C "$main" ls-files --error-unmatch -- "$1" >/dev/null 2>&1 && return 0   # tracked: the worktree has its own
  [ -e "$wt/$1" ] || [ -L "$wt/$1" ] && return 0                                  # already present or linked
  mkdir -p "$(dirname "$wt/$1")"
  ln -s "$main/$1" "$wt/$1"
  linked=$((linked + 1)); echo "linked $1"
}

link ape
link .ape
for root in data data/pr_review_v2/cache inputs/pr_review_v2 results; do
  [ -d "$main/$root" ] || continue
  for p in "$main/$root"/* "$main/$root"/.[!.]*; do
    [ -e "$p" ] && link "${p#"$main"/}"
  done
done
echo "$linked new link(s) into $wt from $main."
echo 'In your own shell here: export PYTHONPATH=$PWD/src   (pytest.ini and Claude Code sessions already put src first)'
