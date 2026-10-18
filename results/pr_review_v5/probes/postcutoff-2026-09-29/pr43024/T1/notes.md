# Review notes: PR #43024 (`isMulCommutative_anti` for subobjects)

Inputs read: `pr.md`, `model.md`, `diff.patch`, then the whole PR-state file
`target/Mathlib/Algebra/Group/Subsemigroup/Defs.lean` through `ptool file_read`.

## Scope of the change

The diff adds one declaration: `isMulCommutative_mono`, with a docstring and a `to_additive`
docstring, at the end of `Mathlib/Algebra/Group/Subsemigroup/Defs.lean`. `model.md` lists
`setLike_mul_comm` as "added", but it appears only as context in the diff, and `declaration_search`
reports it declared at the same line *before* this PR. I reviewed it only as a dependency.

## `isMulCommutative_mono` (new lemma)

- **naming (finding, blocking).** The statement goes from `IsMulCommutative t` to `IsMulCommutative s`
  under `s ≤ t`, so it is antitone. In Mathlib the `_mono` suffix means monotone. Root-level `_anti`
  lemmas, including Prop-valued ones of the same shape (`nth_mem_anti`), confirm the convention. The
  PR title already says `isMulCommutative_anti`. `naming_norm` returned `subject_unresolved`, so
  there is no prefix census either way. The rename compiles (`lean_verify_edit`, `compiled`), and
  the generated additive name `isAddCommutative_anti` resolves.
- **duplication.** None found. `declaration_search` finds nothing at the base for
  `isMulCommutative_anti` or `isMulCommutative_of_le`. A regex search over Mathlib for
  `IsMulCommutative` next to `≤` found only `isMulCommutative_iSup` variants and unrelated
  `Perm`/`alternatingGroup` lemmas, with no existing monotonicity lemma. The deprecated
  `Subgroup.mul_comm_of_mem_isMulCommutative` points to `setLike_mul_comm`, not to this lemma.
- **generalization.** The hypotheses look minimal. `[Mul M] [MulMemClass S M]` is needed for the
  `Mul` on `↥s`. `[LE S] [IsConcreteLE S M]` is the weakest order assumption from which
  `mem_of_le_of_mem` (an alias of `SetLike.le_def.mp`, `Data/SetLike/Basic.lean:261-265`) is
  available. Stating it for two different `SetLike` types with a set inclusion is possible, but it
  is not what siblings do, so I did not ask for it.
- **proof-golf.** The term proof `.of_setLike_mul_comm fun _ ha _ hb ↦ setLike_mul_comm (mem_of_le_of_mem h ha) (mem_of_le_of_mem h hb)`
  already uses the local API: the `of_setLike_mul_comm` alias and `setLike_mul_comm`. `h ha` cannot
  replace `mem_of_le_of_mem h ha`, because `LE S` is abstract here. I found nothing shorter or more
  canonical.
- **documentation.** The docstrings ("passes to smaller subobjects") are accurate for both the
  multiplicative and the additive versions.
- **style.** `@[to_additive /-- ... -/ ]` has a space before `]`. That spelling is rare in Mathlib
  (8 occurrences in 6 files), but it copies the preceding sibling `setLike_mul_comm` at line 344.
  It is a trivial nit, and I did not file it. Binder order and line breaks match the siblings.
- **scope / placement.** The lemma sits right after `setLike_mul_comm` and
  `isMulCommutative_iff_of_setLike`, in the same root namespace. The file already imports
  `Mathlib.Data.SetLike.Basic` (`IsConcreteLE`). Nothing is misplaced.
- **correctness.** The file compiles in the PR state (the verify run had no pre-existing errors).
  The lemma is not an instance, and correctly so, since `h` cannot be inferred.

## `doc_comment in Defs.lean`

This is the docstring of the new lemma, covered above. Nothing further.

## Tools used

`file_read`, `file_search`, `declaration_search` (setLike_mul_comm, isMulCommutative_mono,
isMulCommutative_anti, IsConcreteLE, mem_of_le_of_mem, isMulCommutative_of_le), `content_search`
(IsMulCommutative usages, `_anti` lemmas, `of_setLike_mul_comm` uses, `-/ ]` spelling),
`naming_norm`, `precedent_search` (nothing relevant), `zulip_search` (nothing specific),
and `lean_verify_edit` (the rename: compiled).
