# Systematic opportunity pipeline Phase 2 verdict

## Verdict

Pass the offline Phase 2 gate. Proceed to the narrowly scoped canonical API operator in Phase 3. No
paid model run is authorized or needed for Phase 2.

The inventory and relation layer is now deterministic, complete over the nine-PR pilot, physically
separate from gold, and explicit about the three smoke obligations whose methods remain unimplemented.
This is infrastructure readiness, not evidence of improved review judgment.

## Results

| Artifact | Result |
|---|---:|
| Modification records | 184 |
| Complete classifications | 184 |
| Unknown classifications | 0 |
| Added / modified / removed | 116 / 67 / 1 |
| PR relations | 283 |
| Relation evidence records | 283 |
| Exact / high-confidence relations | 111 / 172 |
| Applicable method tasks | 421 |
| Tasks with related changes | 236 |
| Cross-work-unit tasks | 176 |
| Maximum related-change references | 23 |

Relations by kind:

- 47 signature-level declaration dependencies;
- 64 direct body uses of another changed declaration;
- 94 parser-adjacent changed siblings;
- 78 same-namespace name-family relations using distinctive tokens of at least seven characters.

## Smoke opportunity audit

The active method registry schedules the intended investigations for:

1. `isCover_maximalSeparatedSet` through `canonical_api_search.v1`;
2. `coveringNumber_le_packingNumber` through `wrapper_composition.v1`;
3. `card_maximalSeparatedSet` through `naming_contrast.v1`.

The remaining three obligations are preserved as explicit gaps:

- two require `proof_compression.v1`;
- one requires `structural_rewrite.v1`.

The gate is therefore 3/3 active-method coverage and 6/6 accounted, not an artificial 6/6 schedule
claim. The deferred cases are not routed through canonical API or open review merely to satisfy a
coverage number.

## Audit corrections

Two issues were found and fixed before freezing the artifacts:

1. A six-character shared name token created dense family cliques. Name-family relations now require
   a distinctive token of at least seven characters.
2. A trailing ordinary comment on `Vector3.unexpandNil` was outside the parsed declaration body and
   initially disappeared. Parser-external comments are now a documentation component, and every
   `modified` record must contain at least one changed component.

## Caveats for Phase 3

The 421 tasks are deterministic method obligations, not 421 model calls. Relation fan-out reaches 23
references on one task. Phase 3 must rank and bound delivered relation context, retain the complete
relation artifact, and record every omitted reference. Otherwise the PR map would trade silent
work-unit loss for prompt overload.

The relation graph establishes scope and source candidates. It does not establish that any linked
declaration is the right API or that any name family encodes a review norm.

## Verification

- 164 dataset tests pass.
- Treatment manifest: `e535cbb90995fe089317eded0b7db6a0c155430a7ce4c7c1659c0a4015afb8dc`.
- Method registry: `88b7334f9e73ecd68d5d4911100c3ab0edc216988a914e235630c79d9cfec8c1`.
- Schedule-opportunity audit: pass, active coverage 3/3, planned method gaps 3.

## Commands to run

No paid command is required. Reproduce and validate Phase 2 with:

```bash
./ape/bin/python -m src.datasets.pr_review_v4.phase2_release
./ape/bin/python -m pytest tests/datasets -q
```

Both commands are immutable/idempotent. The next implementation step is Phase 3; its first real smoke
will be restricted to `isCover_maximalSeparatedSet` and one canonical-API control.
