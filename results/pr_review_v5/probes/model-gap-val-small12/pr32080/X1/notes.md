# Review notes: PR #32080 (Completely Regular Space iff Uniformizable)

I read `brief.md`, `pr.md`, `model.md` and `diff.patch`. Tool paths need the `target/` prefix
(e.g. `target/Mathlib/...`). `lean_verify_edit` takes the bare `Mathlib/...` path. The PR's file
compiles as the PR leaves it, with no errors or warnings.

## Object by object

- **`import in Mathlib.lean`**: the new module is inserted in sorted position between
  `UniformEmbedding` and `UnitInterval`. Nothing to request.
- **`SetRel.IsRefl.comp`** (Data/Rel.lean): the proof is correct. The instance is used by the new
  file: with `attribute [-instance] SetRel.IsRefl.comp`, the file fails with
  `failed to synthesize (u3 ○ u3).IsRefl`. Finding: rename it to `isRefl_comp` and use `○`, to match
  the sibling names `isRefl_inter`, `isRefl_iInter`, `isRefl_preimage` and `isSymm_comp_self`. The
  renamed version compiles. `naming_norm` gave no measurement (subject unresolved).
- **`module_doc`**: three findings.
  - The Implementation Details section cites `UniformSpace.completelyRegularSpace`, which does not
    exist (`#check` gives Unknown constant; the declaration_search hit was a fuzzy suffix match).
  - The placeholder `TODO: Explain proofs` should be replaced by a proof sketch.
  - The reference is a course problem-set URL; the sibling file cites through a
    `references.bib` key.
- **Section commands** (`variable {α : Type*}`, `open Filter Set Uniformity SetRel`,
  `section UniformSpace`, `variable [UniformSpace α]`, `end UniformSpace`): fine.
- **`variable [t : TopologicalSpace α] [CompletelyRegularSpace α]`**: this is the blocking bug,
  filed on `CompletelyRegularSpace.of_exists_uniformSpace`. The instance variable is auto-included
  in `of_exists_uniformSpace` and in `completelyRegularSpace_iff_exists_uniformSpace`, so both
  assume their own conclusion. I showed this with an `example` on a fresh type `β` (failed to
  synthesize `CompletelyRegularSpace β`). I then verified a fix: the section line becomes
  `[t : TopologicalSpace α]`, the binder moves onto `exists_uniformSpace`, and the iff is
  `⟨fun _ ↦ CompletelyRegularSpace.exists_uniformSpace, .of_exists_uniformSpace⟩`. With the fix,
  both examples compile. (A version using `.exists_uniformSpace` fails to elaborate: it resolves to
  `Exists.exists_uniformSpace`.)
- **`P`**: a single-letter root-namespace def with no docstring. Finding: rename it (e.g. to
  `private def IsUrysohnBallPair`) and add a docstring. Verified to compile.
- **`urysohns_main`**: finding: rename it to a statement-descriptive private name tied to the
  predicate (e.g. `IsUrysohnBallPair.exists_between`). Verified to compile together with the `P`
  rename. The proof itself is sound. `hdss` from the second `obtain` is unused, but the compile
  gave no linter warning, so I did not file it. The `hos` rewrite chain and the calc are fine.
- **`UniformSpace.toCompletelyRegularSpace`**: the mathematics is correct and it reuses
  `Urysohns.CU` well. I found no existing Mathlib proof that uniform spaces are completely regular:
  content_search over Mathlib for `CompletelyRegularSpace`, completely-regular and uniformizable
  wording, and pseudometric-`iInf` decompositions of uniformities that would allow a shorter proof
  through `completelyRegularSpace_iInf`. Three findings:
  - Add `(priority := 100)`, as on the sibling `UniformSpace.to_regularSpace`.
  - Style: `let` instead of `set`, Mathlib brace layout, `↦` instead of `=>`, and no shadowing of
    `x` in the final term. Verified to compile.
  - Add a `T35Space` instance for T0 uniform spaces. `inferInstance` currently fails; with the
    instance added it compiles.
- **`CompletelyRegularSpace.exists_uniformSpace`**: a neat proof (Stone-Čech plus
  `uniformSpaceOfCompactR1.comap`). The only issue is the variable-inclusion bug above.
- **`CompletelyRegularSpace.of_exists_uniformSpace`**: the proof is fine once the spurious
  instance is removed.
- **`completelyRegularSpace_iff_exists_uniformSpace`**: its name matches the sibling
  `completelyRegularSpace_iff_isInducing_stoneCechUnit`. `naming_norm` returned
  insufficient_evidence. The only issue is the correctness bug above.

## Context checked, not filed

- On Zulip, a 2025-05 message says another open PR (#24096) also proves that uniform spaces are
  completely regular. I could not check that PR's state, so I filed no duplication finding.
- Precedent search for the `exists_uniformSpace` block returned only unrelated comments.

Findings: 10 (1 blocking, 9 advisory).
