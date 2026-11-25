#!/usr/bin/env bash
# Run in an authenticated subscription environment. By default, seal and preflight only.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
probe=results/pr_review_v5/probes/convention-scope-2026-11-24
run_name=${RUN_NAME:-scope_packets_opus55_20261124}
work=.ape/convention-scope-2026-11-24/"$run_name"
export PYTHONPATH="$PWD/src"
unset OPENAI_API_KEY OPENAI_ELM_API_KEY ELM_API_KEY ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL
case "${1:-}" in ""|--execute) ;; *) exit 2 ;; esac
mkdir -p "$work"
if [ ! -d "$work/packets" ]; then
  ape/bin/python "$probe/build_packets.py" "$work/packets" --intervention "$probe/intervention.md"
fi
cli=(ape/bin/python -m src.mathlib_review.review.cli)
"${cli[@]}" probe session-plan --packets "$work/packets" --brief "$probe/brief.md" \
  --output review.json:json --name convention-scope-whole-pr --replicates 2 --out "$work/plan"
exec "${cli[@]}" session --plan "$work/plan" --config configs/session/packet_session_opus55_claude_sub.yaml \
  --run-name "$run_name" --set execution.max_concurrency=3 --set execution.max_turns=40 \
  --set execution.sample_max_tokens=600000 "$@"
