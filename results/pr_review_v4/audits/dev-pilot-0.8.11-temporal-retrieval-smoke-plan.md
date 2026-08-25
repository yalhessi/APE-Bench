# PR Review v4 0.8.11 temporal retrieval smoke plan

## Treatment

Version 0.8.11 removes the rejected synthetic exemplars and adds only deterministic temporal
context-to-ask retrieval. Each retrieved row maps one current stable change target to a prior
rostered maintainer's top-level line comment by similarity between the current complete target and
the historical reviewed diff context. The source PR must differ from the target and the comment must
predate the target's review start. Replies and unresolved phrases such as `same here` are excluded.

Retrieval consumes `retrieval-cutoff1`, which contains only episode identity and review start. It
cannot receive feedback event IDs or outcome fields. Removing the rendered retrieval block restores
every 0.8.9 prompt byte-for-byte; grounding, deterministic discovery, evidence, selection, and the
semantic judge are frozen.

## Three-unit roles

- PR 33057, `wu:2b90f62f628fe3c4b85f80e6`: intervention with no qualifying precedent. This
  checks unchanged model behavior and the retained deterministic compile channel.
- PR 33098, `wu:a0ca0f4fe2020cb90e566181`: treatment unit. Its precedent is a temporally prior
  maintainer request from the same file and domain, but not one of the hidden target asks.
- PR 33438, `wu:a760602702a7288361685f67`: approved theorem control with a cross-domain
  structural precedent, testing whether retrieval induces unsupported copying.

## Real-run command

```bash
./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_pilot.yaml \
  dataset.dry_run=false \
  'dataset.work_unit_ids=["wu:2b90f62f628fe3c4b85f80e6","wu:a0ca0f4fe2020cb90e566181","wu:a760602702a7288361685f67"]' \
  dataset.run_name=pr_review_v4_pilot_0811_temporal_retrieval_smoke3 \
  dataset.output_file=results/pr_review_v4/runs/dev-pilot-0.8.11-temporal-retrieval-smoke3/candidate_responses.jsonl
```

## Acceptance gates

1. Execution and ingestion: 3/3 calls succeed and every candidate passes grounded ingestion.
2. Attribution: only work units with stored precedents differ from 0.8.9; no synthetic exemplar text
   or post-cutoff event appears.
3. Frozen deterministic channel: exactly one supported blocking PR 33057 compile finding and no
   deterministic control finding.
4. Semantic effect: the frozen judge finds at least one issue match among the three visible PR 33098
   obligations. Location or candidate-count gains alone do not pass.
5. Transfer discipline: manually identify copied precedent transformations. A request to make an
   unrelated PR 33098 declaration an iff lemma is a retrieval-induced false positive, not success.
6. Control: PR 33438 has zero selected findings; all raw candidates and any precedent copying are
   reported.
7. Replication: a passing semantic result must repeat once before expanding to nine PRs.

If semantic issue recall remains zero, reject this lexical temporal retrieval policy. The next
design step should improve the retrieval representation or judgment process, not add another prompt
layer to the same ranker.
