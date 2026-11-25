# Whole-PR review and finalization on 42184

The ordinary Opus 5.5 reviewer requested one change, dropping `[L.NeBot]` from `tprod_nonneg`. The reviewer given the comparison instruction requested that same generalization and, second, the companion theorem `HasProd.nonneg`. Its stated caller has `HasProd f a L` and needs `0 ≤ a`. The rewrite through `HasProd.tprod_eq` adds a Hausdorff hypothesis. The guided reviewer compiled a single replacement that proved the companion and used it in the generalized aggregate theorem. It declined a strict positivity analogue because a product of positive factors can converge to zero. The ordinary reviewer compiled two replacements for the aggregate theorem. Its visible searches and submission contain no explicit companion proposal. [Accepted text, compile calls and finalized channels](full_tool_reviews.json)

| One sample per arm | Submitted | In review | In verified | Published admission | Turns | Processed tokens |
|---|---:|---:|---:|---:|---:|---:|
| Ordinary | 1 | 1 | 1 | 1 | 9 | 269,471 |
| Comparison | 2 | 2 | 0 | 0 | 7 | 179,400 |

Both completed on their first attempt. The serialized scaffold configs differ only in the system brief path and digest. Both used the original G contract, the same pass-0 PR description and diff model, cutoff-gated retrieval, reviewed workspace, CLI 2.1.285 at xhigh effort, a 40-turn limit and a 600,000-token ceiling. Both containment audits were clean and usable and each session recorded $0 in per-token charges. [Ordinary run plan](../../runs/scope_solo_opus55_42184_ordinary_20261124/run_plan.json) · [Comparison run plan](../../runs/scope_solo_opus55_42184_comparison_20261124/run_plan.json) · [Generation command](solo.sh)

## Where the compatible changes were lost

The solo response adapter writes an empty verification-artifact list and projects the submitted wording into candidates. The two guided candidates reach finalization with no proposed edit, the same primary declaration and the same concern family, `generalization`. Both evidence packets have status `supported` from the repository-search collector. Both therefore enter the merge with `published` admission and evidence tier `model_assertion`. The successful joint Lean check survives in the conversation, outside these finding records. [Solo projection](../../../../src/mathlib_review/review/runner.py#L783) · [Candidate projection](../../../../src/mathlib_review/review/runner.py#L802) · [Evidence packets](../../runs/scope_solo_opus55_42184_comparison_20261124/evidence/packets.jsonl) · [Admission before merge](../../../../src/mathlib_review/review/finalize.py#L125)

After deduplication the merge groups by PR, primary change ID and concern family. Different requests within this group have equal rank. Its verified-alternative branch requires a structured edit and the `verified_compile` tier on every finding. The fallback marks both guided findings diagnostic. Channel assignment keeps them in `review` and excludes them from `verified`. The saved conflict therefore describes two requests that can coexist, and in this instance one requested proof actually calls the other requested declaration. [Grouping](../../../../src/mathlib_review/review/merge.py#L313) · [Equal-rank resolution](../../../../src/mathlib_review/review/merge.py#L336) · [Channel assignment](../../../../src/mathlib_review/review/finalize.py#L229) · [Recorded conflict](../../runs/scope_solo_opus55_42184_comparison_20261124/conflicts.jsonl)

## Regression target

Replay the saved guided submissions `finding:2a7a85d5443d897864b28b71` and `finding:3e04aee23aa9b9242b5e8a65` against the reviewed source. Under the current code they produce `conflict:8384c7a30a5972f8eebbe380`. A future implementation should retain both supported actions through finalization when supplied with that successful combined edit, whether displayed in one comment or two. A genuine same-anchor counterexample already runs in the suite. “Delete the helper” and “Keep the helper but rename it” cannot both be satisfied. Their equal-warrant versions must remain unresolved. Two separately compiling replacements for the same proof are a third case with an existing one-winner test. Joint compilation establishes compatibility here. Request usefulness is a separate judgment. [Replay](replay_full_tool.py) · [Competing requests](../../../../tests/datasets/test_pr_review_v4_merge.py#L143) · [Alternative proof replacements](../../../../tests/datasets/test_pr_review_v4_merge.py#L359)

Run these local checks from the repository root.

```sh
export ELAN_HOME=/research/projects/proofedit/ya475/.elan
export PATH="$ELAN_HOME/bin:$PATH" PYTHONPATH="$PWD/src:$PWD"
ape/bin/python results/pr_review_v5/probes/convention-scope-2026-11-24/replay_full_tool.py
ape/bin/python -m pytest -q tests/datasets/test_pr_review_v4_merge.py tests/datasets/test_pr_review_v5_evidence_tier.py
```
