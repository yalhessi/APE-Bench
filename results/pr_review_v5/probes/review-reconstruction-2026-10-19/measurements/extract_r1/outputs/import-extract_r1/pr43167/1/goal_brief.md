# Goal brief

## 1. Kind of contribution

- New results.
- API reorganization of an existing lemma, `Subgroup.normalizer_inf_normalizer_le_normalizer_sup`, and of its
  additive version. The lemma is currently in `Mathlib/Algebra/Group/Subgroup/Pointwise.lean`.

## 2. Capability

1. **Commutators distribute over joins against a normal subgroup.** Let G be a group and H, K, N subgroups of
   G with N normal in G. Then the subgroups [H ⊔ K, N] and [H, N] ⊔ [K, N] are equal.
   - [A, B] is the commutator subgroup of A and B, written `⁅A, B⁆` in
     `Mathlib/GroupTheory/Commutator/Basic.lean`.
   - ⊔ is the join of subgroups.
2. **The existing lemma above is reorganized.** It says that N_G(H) ∩ N_G(K) ≤ N_G(H ⊔ K), where N_G is the
   normalizer. Its mathematical content stays the same. Its location and its name are in scope.

## 3. What must keep working

- The content of `Subgroup.normalizer_inf_normalizer_le_normalizer_sup` and of its additive version.
- Existing references to that lemma under its current name, downstream ones included.
- The two lemmas in `Pointwise.lean` that use it, `conj_mem_sup_of_mem_inf_normalizer_of_mem_inf` and
  `normalizer_le_normalizer_sup_of_normalizer_le_left`, with their additive versions.
- The existing commutator API in `Commutator/Basic.lean` and the normalizer API in `Subgroup/Basic.lean`.

## 4. Open questions

- **Hypothesis.** The inputs ask for N normal in G. They do not say whether a weaker hypothesis is also
  wanted, such as N being normalized by H and K, or a hypothesis stated in terms of [H, N] ⊔ [K, N].
- **Breadth.** The inputs leave open whether the result should cover:
  - only binary joins, or arbitrary joins ⨆ᵢ Hᵢ;
  - the form with the join in the second argument of the commutator as well;
  - the analogue for additive subgroups.
- **The normalizer lemma.**
  - Where it should live, what it should be called, and how references to its current name keep working.
  - The inputs do not say whether the reorganization serves the new result or is a separate tidy-up
    bundled with it. Both readings are possible.

## 5. Where the requirements come from

- **2.1, with N normal:** the title, and the description's first paragraph. The title is the current
  title, not verified to be the one at review time.
- **2.2:** the description's third paragraph, and the change itself, which touches this lemma in
  `Pointwise.lean`.
- **3, the lemma and its current name:** the change itself. After the PR the lemma's content and its old
  name are both still available.
- **3, the two users in `Pointwise.lean`:** the change itself. The PR modifies the proofs of these lemmas.
- **3, the existing APIs:** the change itself. The PR adds declarations to `Commutator/Basic.lean` and
  changes none of the existing statements there.
- **The description's second paragraph** is about the proof and sets no requirement.
