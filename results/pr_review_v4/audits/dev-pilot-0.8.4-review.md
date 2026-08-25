# PR Review v4 development smoke set 0.8.4

This is a development diagnostic, not a temporal holdout. Candidate generation must read only the
release's `input/` and `derived/` artifacts. The `gold/` directory is evaluation-only.

| PR | Role | Targets | Units | Max est. tokens | Judgments | Intended pressure |
|---:|---|---:|---:|---:|---:|---|
| 33057 | intervention | 8 | 1 | 2,500 | 1 | blocking correctness from local semantics |
| 33066 | intervention | 40 | 12 | 6,113 | 3 | duplication plus docs/style separation |
| 33098 | intervention | 26 | 8 | 6,297 | 5 | proof-golf and full multi-obligation recall |
| 33117 | intervention | 30 | 5 | 6,457 | 1 | repository-backed duplication |
| 33305 | intervention | 7 | 7 | 1,703 | 1 | blocking style over structural targets |
| 33421 | intervention | 46 | 16 | 5,701 | 3 | naming, generalization, duplication, retrieval ablation |
| 33304 | control | 13 | 13 | 1,884 | 0 | approved documentation change, no revision |
| 33315 | control | 12 | 11 | 1,506 | 0 | second approved documentation shape |
| 33438 | control | 2 | 1 | 776 | 0 | approved substantive theorem change |

Total: 9 PRs, 184 complete targets, 74 work units, 14 judgment obligations, and 3 controls.

## Healthy-run checks

- All 74 work-unit IDs have exactly one successful terminal response.
- Empty candidate lists are common enough to demonstrate real abstention, especially on controls.
- Candidate recall is inspected before evidence selection; a publication miss is not mislabeled as
  a discovery miss.
- Proof-golf findings carry a structured edit and survive external Lean compilation.
- Duplication/generalization findings cite repository hits outside the changed target file.
- Historical precedents never select a finding without another supporting assertion.
- Controls have a low finding rate, reported separately from intervention recall.
- Scope-location hits are not interpreted as semantic issue or resolution matches.

## Stop conditions

Stop before a larger run if prompts differ from their stored hashes, any target is missing or
duplicated, failed work units are converted to empty reviews, local rationale is treated as
evidence, or control findings are accepted without a manual support audit.

## Run incident: 2026-07-13

The first candidate run completed 42/74 units successfully and reported 32 `failed_error` units.
All 128 failed attempts ended during workspace setup with zero turns and zero cost: base commits
`8c38971b...` and `51192f7a...` had not been prebuilt. This disproportionately removed PRs 33057,
33304, 33305, and 33315, so the partial output is not evaluable. Both commits are now built; use
the failed-unit retry command in the design runbook and merge responses before evaluation.
