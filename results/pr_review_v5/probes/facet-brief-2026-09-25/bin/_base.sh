#!/usr/bin/env bash
# Resolve the base commit of a probe PR; every search is pinned to it so the merged outcome is invisible.
CLONE="${MATHLIB_CLONE:-data/code_execute/repos/mathlib4/source}"
PROBE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
pr="$1"; f="$PROBE/pr$pr/base_sha"
[ -f "$f" ] || { echo "unknown PR $pr" >&2; exit 2; }
BASE=$(cat "$f")
