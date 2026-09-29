# Review notes — PR #43024 (`isMulCommutative_anti` for subobjects), reviewer X2

## What I did

1. Read `brief.md`, `pr.md`, `model.md`, `diff.patch`; ran `ptool describe`.
2. Read `Mathlib/Algebra/Group/Subsemigroup/Defs.lean` (header, module doc, and lines 280–356) via
   `file_read` (workspace path `target/Mathlib/...`).
3. `lean_verify_edit` with no edit: the file compiles as the PR leaves it, no errors or warnings.
4. `declaration_search` for `setLike_mul_comm`, `isMulCommutative_iff_of_setLike`,
   `isMulCommutative_mono`, `IsConcreteLE`, `mem_of_le_of_mem`.
5. `content_search` over the whole corpus for sibling lemmas, existing duplicates, users of
   `of_setLike_mul_comm`, and the `-/ ]` spelling; `naming_norm`, `precedent_search`, `zulip_search`.
6. `lean_verify_edit` of the proposed rename (with an `example` exercising the additive twin): success.

## Object by object

### `setLike_mul_comm` (listed as added in `model.md`)
- `declaration_search` says it is declared **before** this PR, and the diff shows it only as hunk
  context. `model.md`'s "added" label is wrong; the PR does not change it. No finding.

### `isMulCommutative_mono` (the only new declaration)
- **Correctness**: compiles; statement is true and at the right level (`[LE S] [IsConcreteLE S M]`
  rather than a concrete partial order). `mem_of_le_of_mem` is a root alias of `SetLike.le_def`
  (Data/SetLike/Basic.lean:265) — `declaration_search` misses it because it is an alias, but it exists.
- **Naming — finding**: the statement is antitone in the subobject but is named `_mono`; the PR title
  itself says `isMulCommutative_anti`; library siblings with the same binder shape are
  `Subgroup.isCyclic_of_le` and `LieSubmodule.isNilpotent_of_le`. Requested rename to
  `isMulCommutative_of_le` / `isAddCommutative_of_le`, verified to compile. `naming_norm` could not
  resolve the subject (unmeasured), and Zulip shows Mathlib is loose about `mono` for weakening
  lemmas (`IsOpen.mono`, `Set.InjOn.mono`), so advisory, not blocking.
- **Duplication**: full-corpus searches found no existing lemma deriving `IsMulCommutative s` from
  `s ≤ t` for any subobject type (no `Subgroup`/`Submonoid` special case to deprecate). No finding.
- **Proof-golf**: the term proof (`.of_setLike_mul_comm` + `setLike_mul_comm` + `mem_of_le_of_mem`) is
  already two lines and uses the canonical API of the file; an anonymous-constructor/`Subtype.ext`
  version is not shorter. No finding.
- **Generalization**: could be stated for `s : S`, `t : T` of different `SetLike` types with a
  `(s : Set M) ⊆ t` hypothesis, but `≤` is the usable form and nothing in the tree needs the
  heterogeneous version. Not requested.
- **Documentation**: both docstrings (multiplicative and `to_additive`) are accurate. No finding.
- **Style**: the `@[to_additive /-- … -/ ]` spelling (space before `]`) is the minority form (6 files
  in the corpus) but copies the preceding `setLike_mul_comm` exactly; too minor to request.
  Binder order `(h : s ≤ t) [IsMulCommutative t]` matches `Subgroup.isCyclic_of_le`. No finding.
- **Scope**: placed right after `setLike_mul_comm`, which it uses, in the file that owns
  `isMulCommutative_iff_of_setLike`; correct place. It cannot be an instance (`h` is not a class
  argument). No existing proof in the tree was found that the new lemma would shorten
  (`of_setLike_mul_comm` users: iSup, map, comap, topologicalClosure, adjoin — none is an `≤` step).

### `doc_comment in Defs.lean`
- This is the new lemma's docstring, "Commutativity of multiplication passes to smaller subobjects.";
  accurate. No finding.

## Outcome
1 finding (naming, advisory). `precedent_search` hits were unrelated to this code.
