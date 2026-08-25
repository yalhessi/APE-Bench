# PR Review v4 semantic judge one-pair smoke verdict

## Verdict

Pass. The v7.1 semantic rubric port behaves as intended on the precommitted near miss and its cache
replays immutably.

## Gates

| Gate | Result | Evidence |
|---|---|---|
| Pair construction | PASS | Exactly one candidate-obligation pair across three scoped atomic obligations |
| Issue judgment | PASS | `issue_match=false` |
| Resolution judgment | PASS | `resolution_match=false` |
| Reason quality | PASS | The judge distinguishes the candidate's unused nonempty binder from the maintainer's empty-branch `rfl` transformation |
| Scoped metrics | PASS | Location recall 1/3; issue recall 0/3; resolution recall 0/3 |
| Audit artifact | PASS | Full gold request, candidate request, overlap ID, verdict, reason, and empty human fields are preserved |
| Cache replay | PASS | Second run reported one total pair and zero uncached; immutable outputs were byte-identical |

## Human check

The automated rejection agrees with manual judgment. Both requests touch the same `rcases` line, but
they identify different specific problems and make different changes:

- candidate: remove the unused `h_nonempty` binder or case split;
- maintainer: replace `h_empty` with `rfl`, keep the nonempty branch, and close the empty case by
  `simp`.

This is a location hit only, not an issue or resolution match.

## Limitation

One rejected pair validates this known decision boundary and the pipeline mechanics, not the standing
20-pair agreement threshold. Every larger semantic evaluation must still sample up to ten accepted
and ten rejected pairs for human review before its metrics are used.

## Next gate

Freeze this judge, deterministic discovery, grounding, and strict publication. Add only generic
maintainer-ask exemplars to generation, rerun the same three work units, and use this judge to require
at least one of three PR 33098 issue matches while retaining zero selected control findings.
