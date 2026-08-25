# PR Review v4 0.8.6 smoke3 verdict

## Verdict

Candidate execution is a go. The end-to-end reviewer is a no-go for a full run until evidence
routing is corrected.

## Execution

- 10/10 work units completed successfully.
- 10/10 terminal submissions were non-empty and accepted.
- 17 canonical `c1` candidates were preserved with stable change IDs.
- No setup, prompt-visibility, ID-normalization, or submission-validation failures remained.
- Total cost was approximately $1.31.

## Candidate quality

- PR 33057: one blocking candidate correctly identified that simplifying
  `PowerSeries.expand_apply` dropped `MvPowerSeries.substAlgHom_apply` and may break compilation.
  This matches the blocking correctness intervention.
- PR 33098: fourteen candidates were generated. None matched the four eligible atomic maintainer
  asks. One candidate did identify the requested `card_maximalSeparatedSet` to
  `encard_maximalSeparatedSet` naming change, but that belongs to a compound intervention currently
  excluded pending decomposition. Most other candidates were speculative API/proof-robustness
  concerns or an unrelated documentation typo.
- Control PR 33438: two advisory candidates questioned proof robustness and `[simp]` policy. This is
  nontrivial raw false-positive pressure, though publication is supposed to filter it.

On the eligible atomic view represented in this smoke set, manual semantic candidate recall is 1/5
(20%): 1/1 on focused correctness and 0/4 on the complex proof/style PR. Exact target-location
coverage is higher but is not semantic recall.

## Evidence and selection

- 17/17 candidates reached evidence collection.
- Packet status: 17 inconclusive, 0 supported, 0 contradicted.
- Selected findings: 0.
- Eleven candidates requested Lean compilation without supplying a structured edit.
- One structured correctness edit reached the compiler but the collector process lacked the Elan
  `lake` path.
- One policy request could not run because the policy registry is not configured.
- Concern labels are currently free-form descriptions, while repository collectors route only the
  canonical duplication/generalization/naming labels. This prevents relevant collectors from
  certifying otherwise usable candidates.

## Required before a full run

1. Make concern labels a closed taxonomy, with a separate free-form rationale/title.
2. Require a structured edit whenever `lean_compile` is requested, or route claim-only compile
   requests to an explicit unsupported terminal state before publication.
3. Give the compile collector the configured Elan environment and test baseline-fails/edit-passes
   evidence for correctness separately from shorter-edit evidence for proof-golf.
4. Implement or explicitly exclude policy-backed style/docs publication.
5. Rerun this smoke set and require at least one supported correctness packet, zero selected control
   findings, and no unexplained incomplete collectors before launching all nine PRs.
