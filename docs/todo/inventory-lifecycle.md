# The inventory's `removed` lifecycle is wrong 38% of the time, and hides edits from every arm

**Status** — open, 2026-09-25, for a fresh session and worktree. Found by
`docs/research/removed-declarations-2026-09.md` §1; this is the first of that study's three steps.

**Cost** — no model spend. Code plus a rebuild of val1000's structure (~5 min).

**Motivating example.** `modification_inventory._lifecycle` calls a target `removed` whenever it
has base lines and no reviewed lines. On val1000 that is 912 declarations, and **344 (38%) are
still declared in the same file** after the PR:
- **172: lines deleted inside a declaration that stays.**
  - 33550: `intro v` inside `DirectSum.IsInternal.isometryL2OfOrthogonalFamily_symm_apply`;
  - 25824: an `open ENNReal in` prefix, beside a correct `modified` target for the same declaration;
  - 25447: a trailing blank line of `map_dvd`.

  A deletion-only range gets no reviewed entity, so its target has base lines only.
- **120: moved within the file**, statement unchanged, split into `removed` + `added`.
- **48: restated in place** (binders or statement edited), split the same way.

**What it costs the review.**
- **135** of the 344 have no other target. The PR's edit to them reaches no arm, because no arm is
  eligible on `removed` (`_BOTH_LIFECYCLES`, `src/mathlib_review/agenda/arms.py:89`).
- **147** have only an `added` sibling, so the arms review a moved or restated declaration as
  brand new and never see the old version. In round 1 a reviewer asked of a moved lemma whether it
  was needed, then saw it had moved (29086, v0741 and v0743).
- **Across files,** 147 more moves and 164 attribute-generated names (`to_dual` 112) are also
  `removed` + `added` pairs.
- The schema already has `moved` and `renamed` (`LifecycleFacet`, `src/mathlib_review/schema/identity.py`).
  The inventory never emits them.

**What would close it:** an inventory version that
- emits `removed` only when the full name is not declared on the reviewed side;
- makes an in-place deletion a `modified` target of the declaration that stays;
- pairs a same-name, same-conclusion declaration across files as `moved`, and a statement-equal
  one under a new name as `renamed`, with the old target in `context_change_ids`.

Measured on val1000 with the committed classifier:
- surviving declarations whose only target is `removed`: **135 → 0**;
- public names retired with no deprecation: **32 → at most 32**, each one read.

**Start here.**
- **read:**
  - `src/mathlib_review/release/modification_inventory.py`: `_lifecycle` at line 61, and the
    identity digest at 256-263, which includes the lifecycle;
  - `src/mathlib_review/release/change_graph.py`: how a deletion-only range becomes a target;
  - `src/mathlib_review/schema/identity.py`: `LifecycleFacet` and `ModificationRecord`;
  - `docs/research/removed-declarations-2026-09.md` §1.
- **run:** first
  `PYTHONPATH=$PWD:$PWD/src ape/bin/python results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/provenance/build_structure.py <scratch>/structure`,
  then
  `PYTHONPATH=$PWD:$PWD/src ape/bin/python results/pr_review_v5/adjudications/removed-declarations-val1000-2025-06-2026-03-v1/provenance/classify_removed.py <scratch>/structure <scratch>/removed.jsonl`.
  Its `survives_*` classes are the defect.
- **bounded by:**
  - The modification id digests the lifecycle, so the change moves every affected id and agenda
    hash. It needs a new `INVENTORY_VERSION`, and frozen releases must keep
    `modification-inventory/1` (`verify_frozen verify`).
  - Opening arms to `moved` / `renamed` is a separate scheduling decision (the §3 knob 4 of
    `docs/research/pipeline-overfit-2026-09-replication.md`). This todo only makes the lifecycle
    true.
  - The retirement check in `removed-declarations.md` reads the pairs this produces.

**Risk.** Pairing by name and conclusion text is a heuristic. A merged lemma that reuses an old
name with a new statement (30799, `pow_eq_one_iff`) must not be paired as a move. The classifier's
`moved_restated` class (25) is where such cases sit.
