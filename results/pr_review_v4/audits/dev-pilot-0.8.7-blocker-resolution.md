# PR Review v4 0.8.7 blocker resolution

## Status

The 0.8.6 execution blockers are implemented and locally verified. A new paid smoke is still needed
to measure the revised candidate contract and end-to-end control behavior.

## Blocker origins

| Blocker | Earlier intervention design | Why v4 exposed it |
|---|---|---|
| Free-form concern labels could not route collectors | Fixed site facets supplied canonical labels by construction | V4 opened candidate labels but retained exact-string routing downstream |
| Claim-only compile requests had no usable evidence | Verification happened inside the generation task or was optional in apply-all mode | The decoupled evidence stage needs baseline state and edits transported explicitly |
| `lake` was unavailable | The agent workspace already configured Lean tools | Persisted evidence workspaces outlive the task process and inherited a minimal orchestrator `PATH` |
| Policy requests were unconfigured | Semantic judges compared predictions with hidden maintainer asks; policy was not a publication gate | V4 requires independent reviewer-visible grounds before publication |
| Candidate flood and weak multi-ask recall | Apply-all already showed high volume and roughly 9% precision; intervention grouping improved scoring | V4 controls and funnel metrics expose the generation problem rather than averaging it into one judge score |

## Implemented in 0.8.7

- Added a closed `concern_family` routing key and retained free-form `concern_label` text.
- Compiled the reviewed baseline even when no structured edit is supplied.
- Required baseline compiler diagnostics to overlap candidate target spans before supporting a
  correctness claim.
- Recorded baseline and proposed-edit compile results separately and recovered elan from workspace
  ancestors.
- Separated claim, proposed-edit, and context assertions. A valid diagnosis can now survive an
  invalid repair, while the unverified suggested fix is withheld.
- Registered the repository-owned `scripts/lint-style.py` checker for style claims. Unsupported
  policy families complete explicitly as inconclusive rather than failing an unconfigured registry.
- Built immutable pilot release `inputs/pr_review_v4/releases/dev-pilot-0.8.7` with renderer
  `candidate-prompt/6` and evidence collector version `evidence-collectors/2`.

## Verification

- `131` dataset tests pass, including target-local compile, elan environment, policy checker, and
  contradicted-repair selection fixtures.
- A live replay of PR 33057 starts Lean successfully, supports the target-local baseline correctness
  claim, contradicts the model's replacement, selects one finding, and omits its suggested fix.

## Remaining empirical blocker

Candidate discovery remains the dominant risk. The 0.8.6 smoke manually matched only 1 of 5
eligible atomic obligations and generated two raw advisories on the theorem control. The 0.8.7 smoke
must show that canonical routing yields supported evidence without publishing control findings; it
does not yet establish acceptable multi-obligation recall.
