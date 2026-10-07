#!/usr/bin/env bash
# Stage 5 on gpt-5.5 (README, the 2026-10-07 amendment): one run a condition through ELM.
# usage (any directory in the tree): stage5_run_gpt.sh <s0|s1|s2|smoke>   [PLAN_ONLY=1: preflight, spends nothing]
#                                                                         [RESUME=1: continue an interrupted run]
# Launch as a user unit, outside the login-session scope (CLAUDE.md, Running): S0 and S1 died with the
# Claude Code process that started them (05:40), and S2 under setsid nohup when the session scope went
# (07:18); a `systemd-run --user` unit survived the next restart.
# `smoke` is S2's configuration on elm_qwen_3.5 (priced 0) on two PRs: plumbing only, never read for a result.
set -euo pipefail
cond=$1
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export ELAN_HOME=/research/projects/proofedit/ya475/.elan
export PYTHONPATH=$PWD/src PATH="$ELAN_HOME/bin:$PATH"
set +u; source ~/.config/secrets/env.zsh; set -u
[ -n "${ELM_API_KEY:-}" ] || { echo "ELM_API_KEY is not set" >&2; exit 3; }
base=configs/pr_review_v5_census_detectors_v1_elm_gpt55_Grc_request
case $cond in
  s0) cfg=$base.yaml; name=probe_census_detectors_elmgpt55_s0_rep1 ;;
  s1) cfg=${base}_sections.yaml; name=probe_census_detectors_elmgpt55_s1_rep1 ;;
  s2) cfg=${base}_sections_disposition.yaml; name=probe_census_detectors_elmgpt55_s2_rep1 ;;
  smoke) cfg=configs/pr_review_v5_census_detectors_v1_elmqwen35_smoke.yaml; name=iter_elmqwen35_census_detectors_s2_smoke ;;
  *) echo "condition: s0, s1, s2 or smoke" >&2; exit 2 ;;
esac
if [ -n "${PLAN_ONLY:-}" ]; then verb=plan; execute=(); else verb=run; execute=(--execute); fi
[ -n "${RESUME:-}" ] && execute+=(--resume)
exec ape/bin/python -m src.mathlib_review.review.cli $verb --config $cfg --run-name $name "${execute[@]}"
