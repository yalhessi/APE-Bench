#!/usr/bin/env bash
# Reproduce one whole-PR arm. The default runs only the local APE preflight.
# Usage: bash solo.sh ordinary|comparison [--execute] [--resume]
set -euo pipefail
probe=results/pr_review_v5/probes/convention-scope-2026-11-24
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
base=results/pr_review_v5/probes/gpt52-postcutoff-2026-09-29/brief_G.md
arm=${1:?choose ordinary or comparison}
shift
for option in "$@"; do
  case "$option" in --execute|--resume) ;; *) exit 2 ;; esac
done
case "$arm" in
  ordinary) brief=$base ;;
  comparison)
    brief=.ape/convention-scope-2026-11-24/solo-comparison.md
    mkdir -p "$(dirname "$brief")"
    { cat "$base"; printf '\n'; cat "$probe/intervention.md"; } > "$brief.tmp"
    mv "$brief.tmp" "$brief"
    ;;
  *) exit 2 ;;
esac
export ELAN_HOME=${ELAN_HOME:-/research/projects/proofedit/ya475/.elan}
export PATH="$ELAN_HOME/bin:$PATH" PYTHONPATH="$PWD/src"
unset OPENAI_API_KEY ELM_API_KEY OPENAI_ELM_API_KEY ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL
exec ape/bin/python -m src.mathlib_review.review.cli run \
  --config configs/pr_review_v5_probe_2026_07_08_v1_opus55_G_claude_sub.yaml \
  --run-name "scope_solo_opus55_42184_${arm}_20261124" \
  --set 'dataset.pr_numbers=[42184]' \
  --set execution.max_concurrency=1 \
  --set dataset.solo_token_cap=600000 \
  --set "task_config.system_prompt_file=$brief" "$@"
