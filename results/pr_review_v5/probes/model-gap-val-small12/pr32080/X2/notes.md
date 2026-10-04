# Review notes: PR #32080, "feat(Topology): Completely Regular Space iff Uniformizable"

## What I did

I read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then ran `ptool describe`.

- **File access.** The file tools read the reviewed tree under the `target/` prefix; bare
  `Mathlib/...` paths return "not found". `lean_verify_edit` takes the bare path.
- **Baseline compile.** `lean_verify_edit` on `Mathlib/Topology/UniformSpace/Uniformizable.lean`,
  with no edit, reports that the file compiles, with no warnings.
- **Checking my proposals.** I checked every edit I propose with `lean_verify_edit`. Temporary
  argument files are in `tmp/`.

## Object by object

### `import in Mathlib.lean`
- The new entry `Mathlib.Topology.UniformSpace.Uniformizable` is in alphabetical order: after
  `UniformEmbedding` ('E' < 'i') and before `UnitInterval` ('f' < 't').
- Nothing to request.

### `SetRel.IsRefl.comp` (Data/Rel.lean)
- **Needed by this PR.** With `attribute [-instance] SetRel.IsRefl.comp`, Uniformizable.lean
  fails with `failed to synthesize (u3 ○ u3).IsRefl`. So the instance is used and belongs in
  this PR.
- **Naming.** The siblings are `isRefl_univ`, `isRefl_inter`, `isRefl_iInter`,
  `isRefl_preimage`, `isSymm_comp_inv` and `isSymm_comp_self`. `SetRel.isRefl_comp` does not
  exist at base. `isRefl_comp` stated with `○` compiles, and `(R₁.comp R₂).IsRefl` still
  synthesizes after the rename.
- **Finding:** rename, advisory.
- **Not a finding:** the proof `⟨_, R₁.rfl, R₂.rfl⟩` is already minimal.

### `P` (private def)
- **Visibility.** `#print P` shows `private def P`: the module system makes it private by
  default, so it does not pollute the root namespace for importers.
- **Unused conjuncts.** `uc.IsSymm`, `uc ∈ 𝓤 α` and `IsOpen uu` are never used, only
  re-proved. Removing them compiles, and removes `hos`, `hucd` and a `ds.IsRefl` from
  `urysohns_main`.
- **Findings:** the simplification, and the opaque single-letter, undocumented name. Both
  advisory.
- **`IsOpen uc`.** It may also be removable, since `d ○ uc ○ d` is open whenever `d` is open.
  But that needs a lemma other than `IsOpen.relComp` (which wants both factors open), so I did
  not propose it.

### `urysohns_main` (private theorem)
- It is private under the module default, and its name does not describe its statement.
- **Finding:** naming, advisory.
- **Proof, apart from the `P` simplification and the `ball` spelling:** it is a reasonable
  structured proof. The two `closure_preimage_subset` / `preimage_mono` bullets look
  duplicated, but the library has no `closure_ball_subset` lemma, so I did not ask for one.

### `UniformSpace.toCompletelyRegularSpace` (public instance)
- **No duplicate at base.** `example : CompletelyRegularSpace α := inferInstance` fails with
  the PR's instance replaced by `sorry`. `UniformSpace.completelyRegularSpace` is an unknown
  constant.
- **Findings, all advisory:**
  - **`ball` API.** Use `UniformSpace.ball` and its lemmas (`isOpen_ball`, `isClosed_ball`,
    `mem_ball_self`, `ball_mono`) instead of hand-written `Prod.mk x ⁻¹'` and
    `.preimage (.prodMk_right x)`. This is verified.
  - **Priority.** Use `(priority := 100)`, matching `UniformSpace.to_regularSpace`. This is
    verified.
  - **`fun ... ↦`.** Replace `fun ... =>`, and stop the inner lambda shadowing `x`. This is
    verified.
- **Not a finding.** The `id_subset_iff.1 (refl_le_uniformity h)` idiom for getting `IsRefl` is
  the library's own pattern (UniformSpace/Defs.lean:564, :583; Basic.lean:88).
- **Related open PR (not a finding).** Zulip (2025-05, Miyahara Kō) says another open PR,
  #24096, also proves that uniform spaces are completely regular. It is not at base, so I raise
  no duplication finding. A maintainer might ask the author to coordinate with it.

### `section` / `variable` commands
- **`variable [t : TopologicalSpace α] [CompletelyRegularSpace α]` is the root cause of the
  blocking bug.** `#check` shows `[CompletelyRegularSpace α]` is included in
  `of_exists_uniformSpace` and in the iff. The fix: drop it from `variable` and bind it on
  `exists_uniformSpace`. This compiles, and the `#check` output then has no such binder.
- `variable {α : Type*}`, `open Filter Set Uniformity SetRel` and `section/end UniformSpace` are
  fine.

### `CompletelyRegularSpace.exists_uniformSpace`
- The statement shape `∃ u : UniformSpace α, u.toTopologicalSpace = t` matches how
  Patrick Massot framed it on Zulip ("existence of a uniform structure inducing the given
  topology").
- The one-line proof is fine.
- **Not proposed.** I tried offering a `def CompletelyRegularSpace.uniformSpace` built with
  `replaceTopology`. It needs `@[expose]` and a `public import` of OfCompactT2, which is a
  design change I am not confident a maintainer would ask for.
- Its only issue is receiving the instance binder from `variable`, as it should once the
  binder is moved there explicitly.

### `CompletelyRegularSpace.of_exists_uniformSpace`
- **Finding, blocking:** it currently assumes `[CompletelyRegularSpace α]`, its own conclusion.

### `completelyRegularSpace_iff_exists_uniformSpace`
- **Finding, blocking:** it is vacuous for the same reason, and the proof `@...exists_uniformSpace α t`
  only works because of that.
- The fixed proof is `⟨fun _ ↦ CompletelyRegularSpace.exists_uniformSpace, .of_exists_uniformSpace⟩`.
  `.exists_uniformSpace` does not work there, because it resolves to `Exists.…`.

### `module_doc in Uniformizable.lean`
Three findings, all advisory:
- **Placeholder.** Resolve the `TODO: Explain proofs` placeholder and use the standard
  headings.
- **Dangling name.** It names `UniformSpace.completelyRegularSpace`, which does not exist;
  the instance is `UniformSpace.toCompletelyRegularSpace`.
- **Reference.** A course problem-set URL should become a bib reference.

### File imports
- **Finding, advisory.** `import Mathlib.Topology.UrysohnsLemma` is redundant, because
  CompletelyRegular.lean publicly imports it. Removing it compiles.
- **Not a finding:** `OfCompactT2` is needed (`uniformSpaceOfCompactR1`), and it is correctly a
  private import.

## Tools that gave nothing usable
- `naming_norm` returned `subject_unresolved` for `IsRefl.comp`, `of_exists_uniformSpace` and
  `urysohns_main`.
- `precedent_search` hits were unrelated.
