#!/usr/bin/env bash
# Default: local checks. --execute: the entire first sample on the user's subscription.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export PYTHONPATH="$PWD/src:$PWD"
export ELAN_HOME="${ELAN_HOME:-/research/projects/proofedit/ya475/.elan}"
export PATH="$ELAN_HOME/bin:$PATH"
unset OPENAI_API_KEY ELM_API_KEY OPENAI_ELM_API_KEY ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL
probe=results/pr_review_v5/probes/convention-scope-2026-11-24
case "${1:-check}" in
  check)
    if (( $# > 1 )); then echo 'check takes no options' >&2; exit 2; fi
    ape/bin/python "$probe/pilot/history.py"
    ape/bin/python "$probe/four_reviews.py" check
    ape/bin/python "$probe/pilot/conventions.py"
    ;;
  --execute)
    if (( $# != 1 )); then echo 'Use generate or compare for per-stage options' >&2; exit 2; fi
    ape/bin/python "$probe/pilot/history.py"
    ape/bin/python "$probe/pilot/conventions.py" --execute
    ape/bin/python "$probe/four_reviews.py" generate --execute
    ape/bin/python "$probe/four_reviews.py" compare --execute
    ;;
  generate|compare) exec ape/bin/python "$probe/four_reviews.py" "$@" ;;
  conventions) shift; exec ape/bin/python "$probe/pilot/conventions.py" "$@" ;;
  *) echo 'Use check, --execute, conventions, generate, or compare.' >&2; exit 2 ;;
esac
