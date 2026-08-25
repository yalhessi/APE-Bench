# PR Review v4 0.8.11 temporal retrieval smoke replication verdict

## Verdict

Replication failed. Do not expand to the nine-PR pilot and do not treat the first run's semantic hit
as a stable retrieval effect. The first result remains a valid run-level issue match, but the
identical treatment produced no issue match in replication two.

The frozen semantic judge subsequently confirmed replication two at zero issue and resolution
recall, with the sole pair rejected for targeting the wrong branch binder.

The evidence and selector remain stable: both runs publish only the deterministic PR 33057 compile
failure and publish nothing on the control. Instability is concentrated in voluntary model candidate
generation.

## Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Execution | Pass | 3/3 calls succeeded with one terminal response per unit. |
| Semantic replication | Fail (manual, unambiguous) | Only `pr33098_i04` is location-paired; it repeats the wrong-binder near miss and is false/false under the frozen rubric. |
| Control | Pass at selection, unstable raw | PR 33438 produced two raw candidates but zero selected findings. |
| Deterministic stability | Pass | Exactly one supported and selected PR 33057 compile finding. |
| Transfer discipline | Pass | No retrieved historical transformation was copied verbatim. |
| Pending-decomposition diagnostic | No hit | The `encard_` naming recovery from run one did not recur. |

## Run comparison

| Metric | First smoke | Replication two |
| --- | ---: | ---: |
| PR 33057 model candidates | 0 | 1 |
| PR 33098 model candidates | 4 | 1 |
| PR 33438 model candidates | 0 | 2 |
| Overall location candidate recall | 0.75 | 0.25 |
| Included PR 33098 location recall | 1.00 | 0.33 |
| Included PR 33098 issue recall | 0.33 | 0.00 expected |
| Included PR 33098 resolution recall | 0.00 | 0.00 expected |
| Selected findings | 1 | 1 |
| Selected control findings | 0 | 0 |

Replication two has one semantic pair. The candidate says the unused `h_nonempty` binder should be
removed with `by_cases` or an unnamed branch. The maintainer asks to replace the distinct empty-case
`h_empty` binder with `rfl` while retaining `h_nonempty`. The frozen rubric explicitly treats a
different binder and transformation as `issue_match=false`, `resolution_match=false`.

## Interpretation

Identical prompt hashes produced large output changes in all three units, including PR 33057, which
has no retrieved precedent. Two samples are therefore insufficient to distinguish a retrieval effect
from ordinary model variance. The first run was promising evidence for a hypothesis, not a replicated
result.

## Next experiment

Keep both prompt versions frozen and run a small repeated paired ablation rather than another prompt
edit. Use only PR 33098 and PR 33438:

- bring the 0.8.9 no-retrieval baseline to three independent samples;
- bring the 0.8.11 retrieval treatment to three independent samples;
- judge every eligible pair with the same semantic cache/rubric;
- compare per-sample issue hits, pooled obligation recall, raw control candidates, and selected
  control findings.

Existing runs provide one baseline sample and two retrieval samples, so this requires only two new
baseline repetitions and one new retrieval repetition, six model calls total. Decompose
`pr33098_i01` separately as a dataset correction, but preserve the current included-obligation metric
so decomposition cannot retroactively rescue this treatment.

Generator cost reported by replication two: $0.179557.

## Commands to run

Run two additional no-retrieval baseline samples:

```bash
./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_pilot.yaml \
  dataset.release=inputs/pr_review_v4/releases/dev-pilot-0.8.9 \
  dataset.dry_run=false \
  'dataset.work_unit_ids=["wu:b5d86477bfa706af0077b107","wu:4ba70bd37a066bfd7486d2cf"]' \
  dataset.run_name=pr_review_v4_pilot_0809_paired_smoke2_rep2 \
  dataset.output_file=results/pr_review_v4/runs/dev-pilot-0.8.9-paired-smoke2-rep2/candidate_responses.jsonl

./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_pilot.yaml \
  dataset.release=inputs/pr_review_v4/releases/dev-pilot-0.8.9 \
  dataset.dry_run=false \
  'dataset.work_unit_ids=["wu:b5d86477bfa706af0077b107","wu:4ba70bd37a066bfd7486d2cf"]' \
  dataset.run_name=pr_review_v4_pilot_0809_paired_smoke2_rep3 \
  dataset.output_file=results/pr_review_v4/runs/dev-pilot-0.8.9-paired-smoke2-rep3/candidate_responses.jsonl
```

Run one additional retrieval sample:

```bash
./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_pilot.yaml \
  dataset.dry_run=false \
  'dataset.work_unit_ids=["wu:a0ca0f4fe2020cb90e566181","wu:a760602702a7288361685f67"]' \
  dataset.run_name=pr_review_v4_pilot_0811_paired_smoke2_rep3 \
  dataset.output_file=results/pr_review_v4/runs/dev-pilot-0.8.11-paired-smoke2-rep3/candidate_responses.jsonl
```

Return after all three runs finish. Postprocessing and semantic judging should be applied to each
run separately before pooling the three samples per treatment.
