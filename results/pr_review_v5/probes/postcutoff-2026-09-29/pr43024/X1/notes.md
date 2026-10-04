# Review notes: PR #43024, reviewer X1

Inputs read: `brief.md`, `pr.md`, `model.md`, `diff.patch`. I read the changed file in the tool
workspace in full (`target/Mathlib/Algebra/Group/Subsemigroup/Defs.lean`). The PR as left compiles:
`lean_verify_edit` with no edit returned `compiles: true` and no errors.

## `isMulCommutative_mono` (the only declaration the diff adds)

- **naming** (finding, blocking): the statement is `s ≤ t → [IsMulCommutative t] → IsMulCommutative s`,
  so the predicate is antitone in the subobject, and Mathlib names that direction `_anti`
  (`Set.Subsingleton.anti`, `IsAcyclic.anti`, `CliqueFree.anti`, `Loopless.anti`, `Salient.anti`,
  `Blunt.anti`, `Filter.Subsingleton.anti`; `Pointed.mono` is used for the upward direction). The PR
  title already says `isMulCommutative_anti`. `isMulCommutative_anti` is free in the base, and the
  renamed lemma compiles, with `isAddCommutative_anti` generated. Checked with `lean_verify_edit`
  in line mode. Mathlib also has some `.mono` names for inheritance by subsets (`Set.InjOn.mono`,
  `IsOpen.mono`), so the convention is not uniform. The `_anti` family is the one that matches the
  title and the `Antitone` reading, so I kept the finding.
- **duplication**: I searched every declaration mentioning `IsMulCommutative`, and every one that
  combines it with `≤`. No existing lemma derives `IsMulCommutative s` from `s ≤ t` for any subobject
  type (Subgroup, Submonoid, Subsemigroup, Subalgebra and so on), so the lemma is new. Nothing found.
- **generalization**: `[Mul M] [MulMemClass S M]` are needed for `IsMulCommutative ↥s` to typecheck.
  `[LE S] [IsConcreteLE S M]` is the weakest order assumption that `mem_of_le_of_mem` needs, which
  is more general than asking for `PartialOrder S`. Nothing to weaken.
- **proof-golf**: the proof is the term `.of_setLike_mul_comm fun _ ha _ hb ↦ setLike_mul_comm
  (mem_of_le_of_mem h ha) (mem_of_le_of_mem h hb)`, which is already short and uses the existing
  API (`IsMulCommutative.of_setLike_mul_comm`, `setLike_mul_comm`, `mem_of_le_of_mem`). `h ha`
  cannot replace `mem_of_le_of_mem h ha` under an abstract `LE`. Nothing to request.
- **documentation**: the multiplicative and additive docstrings are accurate ("passes to smaller
  subobjects"). Nothing found.
- **style**: the `to_additive` docstring ends `-/ ]` with a space before `]`. Mathlib's usual
  spelling is `-/]`, and the edit with `-/]` compiles. But the same spelling is already merged on
  the preceding `setLike_mul_comm` (line 344), in `Algebra/Group/Semigroup.lean` and five times in
  `Algebra/Group/IsCommutative.lean`, so maintainers have not enforced this in this area. I did not
  file it as a finding. The binder order `(h : s ≤ t) [IsMulCommutative t]` is fine: this cannot be
  an instance because `h` is not inferable.
- **scope**: placing it right after `setLike_mul_comm` in Subsemigroup/Defs.lean, in the root
  namespace like its siblings `isMulCommutative_iff_of_setLike` and `setLike_mul_comm`, is
  consistent. Nothing found.
- **correctness**: the file compiles, and the additive translation is produced correctly. Nothing
  found.

## `setLike_mul_comm`

`model.md` lists it as added, but it appears only as unchanged context in the diff's hunk header,
and `declaration_search` reports it as declared before this PR. The PR does not change it, so it is
not a target.

## `doc_comment in Defs.lean`

This is the docstring of `isMulCommutative_mono`, covered above. It is accurate.

## Tools used

`describe`, `file_search`, `file_read`, `declaration_search` (setLike_mul_comm, isMulCommutative_mono,
isMulCommutative_anti, mem_of_le_of_mem, IsConcreteLE, IsMulCommutative.of_setLike_mul_comm),
`content_search` (IsConcreteLE API; IsMulCommutative declarations; IsMulCommutative with `≤`; `_anti`
lemma names; `-/ ]` occurrences), `naming_norm` (subject_unresolved), `precedent_search` (nothing
relevant), `zulip_search` (no discussion of this lemma), and `lean_verify_edit` (the as-is check, and
the rename with `-/]`, which succeeded).
