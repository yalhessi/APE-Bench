# Systematic opportunity pipeline phases 0-1 implementation

## Status

Phases 0 and 1 are complete. The frozen semantic report for `oracle-evidence-probe-0.2.0`
records two issue matches and one resolution match.

No new candidate-generation run is authorized yet.

## Implemented

- Production-only schemas for modifications, PR relations, methods, investigation tasks, operator
  runs, opportunities, terminal records, technical assessments, norms, worthiness, and synthesis.
- `ReviewOpportunity.source_provenance` accepts only `automatic`; oracle records remain a separate
  diagnostic schema.
- A four-method registry covering deterministic failures, canonical API search, wrapper composition,
  and naming contrast.
- Registry identity validation, resource allowlists, gold-signal rejection, and immutable output.
- Optional investigation IDs and registry hashes in run plans.
- Run sealing that requires exact investigation, operator, opportunity, candidate, evidence, and
  finding lineage without changing legacy candidate-only runs.
- A baseline lock and claim matrix that distinguish proven, diagnostic, refuted-for-tested-design,
  pending, and unproven claims.
- The baseline lock validates semantic-report completeness and records the observed issue and
  resolution counts without requiring a favorable result.

The Phase 2 visibility predicate extended the registry schema after this report. Current registry
hash: `88b7334f9e73ecd68d5d4911100c3ab0edc216988a914e235630c79d9cfec8c1`.

## Verification

- `161` dataset tests pass.
- Registry validation passes.
- Python compilation passes for all changed modules.
- The strict baseline lock is complete.
- Naming is confirmed as issue-and-resolution recovery; wrapper composition is confirmed as
  issue-only recovery because its candidate omitted the exact `by_cases!` transformation.

## Commands to run

Run the frozen semantic judge over the two existing oracle-evidence candidates:

```bash
test -n "${OPENAI_API_KEY:-}" || { echo "OPENAI_API_KEY is not set"; exit 1; }

./ape/bin/python -m src.datasets.pr_review_v4.semantic_judge \
  --judgments inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/judgments.jsonl \
  --views inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/intervention_views.jsonl \
  --candidates results/pr_review_v4/runs/oracle-evidence-probe-0.2.0/candidates.jsonl \
  --work-units inputs/pr_review_v4/treatments/oracle-evidence-probe-0.2.0/derived/work_units.jsonl \
  --work-unit-ids \
    wu:oracle-evidence:8df666b9fb141d606cb0 \
    wu:oracle-evidence:31e8ae1ffd989229d385 \
  --model gpt_5_mini \
  --concurrency 1 \
  --out-dir results/pr_review_v4/runs/oracle-evidence-probe-0.2.0/semantic-judge-v1
```

Then create the strict final baseline lock. This validates report completeness and freezes the
observed result:

```bash
./ape/bin/python -m src.datasets.pr_review_v4.systematic_baseline \
  --out-dir results/pr_review_v4/audits/systematic-opportunities-v1-baseline-lock
```

Return after both commands finish. The next implementation round is Phase 2: coarse modification
inventory and high-precision PR relations, followed by an offline schedule-opportunity audit before
any paid generation.
