# Pass 4 (proofs) — PR #30458

All compiles use `lean_verify_edit` against the PR's reviewed workspace. The PR's files compile
as-is (a baseline check on Basic.lean with no edit: `compiles: true`, no warnings). The control c9
(`mul_left_cancel` in place of `mul_right_cancel`) fails with a real error, which shows the tool
reports failures. `proof_profile` was unavailable: no declaration table for base commit 586e9c38.
The library idiom was therefore read off the siblings in `Defs.lean` 129-177, `Basic.lean` 218-306,
`Finset/Basic.lean` 1147-1215 and `Set/Finite.lean` 99-123. `precedent_search` on the
`div_left_inj` proof returned nothing that applies.

Across the whole PR, every proof it modifies compiles in its **exact pre-PR text** against the
statements and sections as the PR leaves them (c1-c4, c20, c21, c24, c25). The generalisation needed
only the new `variable` lines. Every proof rewrite is optional, and each one is longer than the
proof it replaces. Most also add named arguments (`(a := …)`, `(b := …)`, `(G := G)`) that tie the
proof to other declarations' binder names.

## Basic.lean family

**`div_eq_inv_self`** (moved, proof unchanged). `simp [div_eq_mul_inv]` also closes it (c18), and so
does a derivation from `div_left_inj` via `rw [← one_div, div_left_inj]` after reordering (c17).
Neither beats the kept `rw [div_eq_mul_inv, mul_eq_right]`, which uses the library's `mul_eq_right`
directly. No request.

**`div_left_injective`** (proof rewritten). The pre-PR `simp only [div_eq_mul_inv]; exact fun a a' h ↦
mul_left_injective b⁻¹ h` compiles unchanged (c1), because `mul_left_injective` needs only
`IsRightCancelMul`. In the PR's own structure the final `simpa using (mul_right_cancel (a := a₁)
(b := b⁻¹) (c := a₂) h')` can be `exact mul_right_cancel h'` (c5). The `mul_right_cancel` one-liner
works (c6). The `simpa` form the deleted FIXME wanted, `simpa only [div_eq_mul_inv] using
mul_left_injective b⁻¹`, now compiles (c7), so the FIXME can be resolved rather than just deleted.
`simpa [div_eq_mul_inv] using h` also works but leans on the simp set (c8). Blocking request: c7,
or the pre-PR proof.

**`div_left_inj`** (proof rewritten, 2 → 6 lines). The pre-PR proof compiles (c2).
`div_left_injective.eq_iff` compiles as the declaration (c10), which is the
`mul_left_inj := (mul_left_injective a).eq_iff` pattern and what the PR itself does for
`div_right_inj`. The PR's forward direction repeats `div_left_injective`'s body. The extracted lemma
for it already exists: `⟨(div_left_injective ·), congrArg (· / a)⟩` compiles (c11). Blocking
request: `.eq_iff`.

**`div_eq_self`** (moved, proof unchanged). `simp [div_eq_mul_inv]` closes it (c19), and the
derivation from `div_right_inj` by the `mul_eq_left` calc compiles (c17). Neither is better, so no
request.

**`div_right_injective`** (proof unchanged, FIXME comment removed). The FIXME's `simpa` now works:
`simpa only [div_eq_mul_inv] using (mul_right_injective b).comp inv_injective` compiles, both with
`Function.comp_def` (c12) and without it (c13). Other forms compile but are not better (c14
`mul_left_cancel` term, c15 simp-set `simpa`). Advisory request: resolve the FIXME rather than drop
it from a proof that is still the workaround.

**`div_right_inj`** (`(G := G) (b := a)` added). The pre-PR `div_right_injective.eq_iff` compiles
(c3; pass-3 c6). Advisory: revert.

The whole family in idiomatic form compiles as one edit (c16): 25 lines against the PR's 36. So
does the whole family in its pre-PR proofs, FIXMEs included (c4). Pass 3's left/right bridge
(c12/c34 there) is a statement matter. Within the PR's hypotheses no left member's proof can be
derived from the right member's, so there is no proof request from it.

## Finset family

**`card_le_card_div_left` / `card_le_card_div_right`** (term proofs rewritten to `obtain`/`exact`
with `(b := _)`). Both pre-PR term proofs compile as declaration replacements (c20, c21). They are
the form of the siblings `card_le_card_mul_left/right` (`have ⟨_, ha⟩ := hs; …`, lines 1169-1170,
1202-1203). Derivations from the mul partners (`rw [div_eq_mul_inv, ← card_inv t]; exact
card_le_card_mul_left hs`, and `card_le_card_mul_right ht.inv`) compile (c22, c23) but are not
better. Advisory: revert to the pre-PR proofs. `card_le_card_div_self` is unchanged and compiles
in the file; pass 3 covered its right-cancel twin.

## Set family

**`finite_div` / `infinite_div`** (`div_left_injective.injOn` rewritten to
`(div_left_injective (b := b)).injOn` with named binders). Both pre-PR proofs compile (c24, and c25,
which pass 3 had not compiled). They match `finite_mul`/`infinite_mul` directly above. Both are
also derivable from the mul/inv partners (`rw [div_eq_mul_inv, finite_mul, finite_inv,
inv_eq_empty]`, c26, and the infinite analogue, c27). Extracting the repeated injOn pair into a
lemma compiles (c28). Neither is better than the sibling form, and the mul siblings repeat the same
pair inline. Advisory: revert to the pre-PR proofs.
