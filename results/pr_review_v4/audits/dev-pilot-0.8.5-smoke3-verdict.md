# PR Review v4 0.8.5 smoke3 verdict

## Verdict: no-go

Do not start the full 0.8.5 run. The smoke test successfully exposed one remaining protocol defect.

## Accounting

- Scope: PRs 33057, 33098, and control 33438; 10 work units total.
- Execution: 10/10 successful tasks, no workspace/setup failures.
- Cost: approximately $2.96.
- Contract visibility: 10/10 actual user prompts contained the review contract.
- Raw behavior: 28 non-empty submission attempts containing 42 typed candidate objects.
- Recorded behavior: 10 empty terminal results.

## Cause

Every one of the 42 candidate objects omitted the literal `change:` prefix from its otherwise
correct target hash. For example, the prompt displayed `change:efe8...`, while the model submitted
`efe8...`. Claims and evidence requests were present. Strict stable-ID validation rejected each
submission; agents eventually terminated with an empty list.

## Latent quality signal

- PR 33057: the model repeatedly identified that the revised `PowerSeries.expand_apply` proof may
  fail because it dropped `MvPowerSeries.substAlgHom_apply`. This aligns with the blocking
  correctness intervention and is encouraging.
- PR 33098: the model generated many speculative API/style candidates, including an unrelated
  module-doc typo, but did not identify the five exact maintainer requests in this smoke trace.
- Control PR 33438: the model proposed four advisory concerns about proof brittleness and the simp
  attribute. This is substantial raw candidate pressure; the evidence/selection stage must reject
  weak concerns for deployment precision to be acceptable.

These observations are trace diagnostics, not scored results, because rejected retries changed the
subsequent conversation and no non-empty terminal artifact was recorded.

## Correction

Release `dev-pilot-0.8.6` uses renderer `candidate-prompt/5`. It labels each stable ID as a
copy-exact quoted value and canonicalizes an unambiguous bare hash suffix back to its full
`change:<hash>` ID before validation. Rejection messages now identify the invalid field explicitly.
The three-PR smoke test must be rerun on 0.8.6 before a full run.
