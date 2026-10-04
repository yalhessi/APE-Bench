# Review notes: PR #43167 (reviewer X1)

I read `brief.md`, `pr.md`, `model.md` and `diff.patch`. I read the three changed files through
`ptool file_read` (workspace root `target/`). Every edit proposed in `findings.json` was compiled
with `lean_verify_edit`. I first checked that the verifier is real: a deliberately wrong edit, and
an edit importing a nonexistent module, both failed as expected. `proof_profile` was unavailable
("no declaration table for 3ed2ddca…"), so it gave no proof-golf evidence.

## Mathlib/Algebra/Group/Subgroup/Basic.lean

- **`Subgroup.inf_normalizer_le_normalizer_sup` (moved and renamed)**: the statement and proof are
  unchanged from the old Pointwise lemma. The move is needed: `Commutator/Basic.lean` uses the lemma
  and does not import Pointwise. It is placed next to `inf_normalizer_le_normalizer_inf` and
  `iInf_normalizer_le_normalizer_iInf`, and the new name follows those siblings and
  `iInf_normalizer_le_normalizer_iSup`.
  - `naming_norm` returns only "emerging" for a `normalizer_` prefix, which does not fit a `≤`
    statement.
  - `content_search` finds `stabilizer_inf_stabilizer_le_stabilizer_*`, which favours the old
    spelling. The rename is a judgement call, so I made no finding.
  - `zulip_search` found no prior discussion.
- **Deprecated aliases (`attribute in Basic.lean` ×2)**: both are correct and date-stamped, and
  the separate `_root_.AddSubgroup` alias also appears elsewhere in this file (line 409). A single
  `@[to_additive (attr := deprecated …)] alias` compiles and produces the correctly targeted
  additive alias → advisory finding.
- I also checked whether `iInf_normalizer_le_normalizer_iSup` should move with its binary sibling.
  It compiles in Basic.lean, but asking for it would widen the PR, so I did not file it.

## Mathlib/Algebra/Group/Subgroup/Pointwise.lean

- **`import in Pointwise.lean`**: the new `public import Mathlib.GroupTheory.Commutator.Basic` is
  unused. Nothing in the file mentions commutators, and the file compiles with the import removed.
  Without it, `Subgroup.commutator_comm` is unknown, so the import adds a genuinely new dependency
  → blocking finding.
- **`Subgroup.normalizer_inf_normalizer_le_normalizer_sup` (removed)**: its deprecated aliases are in
  Basic.lean, so there is nothing further to ask.
- **`conj_mem_sup_of_mem_inf_normalizer_of_mem_inf`, `normalizer_le_normalizer_sup_of_normalizer_le_left`**:
  the only change is the renamed reference, which is correct and compiles. Nothing to ask.

## Mathlib/GroupTheory/Commutator/Basic.lean

- **`commutator_mono_left` / `commutator_mono_right`**: the names and statements match the Lie
  analogues `mono_lie_left` and `mono_lie_right`, and both have `to_additive`. The problem is
  `gcongr` placement. With the PR's attributes, a two-sided goal `⁅H₁,K₁⁆ ≤ ⁅H₂,K₂⁆` fails
  ("gcongr did not make progress"). Tagging `commutator_mono` covers the one-sided and two-sided
  goals, which is the `LieSubmodule.mono_lie` pattern → advisory finding.
- **`commutator_le_of_le`**: correct and `to_additive`. The name is somewhat generic, but
  `naming_norm` could not resolve its subject and I have no convention to hold it to. It is a
  one-line consequence of `commutator_le_sup`, but a reasonable API lemma. No finding.
- **`commutator_sup_left'` (private helper)**: correct. It carries redundant `Subgroup.` prefixes
  inside `namespace Subgroup` (advisory finding, verified) and lacks `to_additive`, which is needed
  for the main lemma's additive version (covered by the `to_additive` finding). I considered golfing
  the final `rw [map_sup]; exact sup_le hH hK`, but the gain is not worth an ask.
- **`commutator_sup_left`**:
  - Missing `@[to_additive]` → blocking finding. With it added, `AddSubgroup.addCommutator_sup_left`
    and `_right` generate with no proof change.
  - Generalization: `[N.Normal]` is used only to bound `⁅H,N⁆ ⊔ ⁅K,N⁆ ≤ N`, so `H ≤ normalizer N`
    and `K ≤ normalizer N` suffice. A one-line change to `hHKN` compiles, and the `[N.Normal]`
    version follows from it → advisory finding.
  - Otherwise the proof strategy (quotient by the sup, inside `M = H ⊔ K ⊔ N`) is sound. I
    considered a direct proof by closure induction, but it would not be shorter, so no golf ask.
  - I considered `@[simp]`, by analogy with `LieSubmodule.sup_lie`, and a docstring. Neither is
    clearly expected given the instance hypothesis, so no finding.
- **`commutator_sup_right`**: correct via `commutator_comm`, and the argument order `(N H K)`
  follows the statement. It lacks `to_additive`; that is included in the `commutator_sup_left`
  finding.

Findings written: 6 (2 blocking, 4 advisory).
