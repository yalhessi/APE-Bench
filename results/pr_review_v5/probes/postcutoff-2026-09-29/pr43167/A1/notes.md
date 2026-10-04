# Review notes: PR #43167

I read `pr.md`, `model.md` and `diff.patch`, then used `ptool` to read the three changed files as the PR leaves them (`target/...`). I checked every edit I propose with `lean_verify_edit`. Raw tool outputs are in `tmp/*.json`.

## Mathlib/Algebra/Group/Subgroup/Basic.lean

- **`Subgroup.inf_normalizer_le_normalizer_sup`** (moved from Pointwise and renamed). The new name matches its sibling `inf_normalizer_le_normalizer_inf` directly below. `naming_norm` says `normalizer_` is "emerging" as the leading prefix (advisory at most), but the local sibling convention is the stronger signal, so I make no naming request. The statement and proof are unchanged from the original. The lemma takes explicit `(H K)` while its siblings use the section variables; changing that would break the `H.inf_normalizer_le_normalizer_sup K` callers, so I make no request. The move is justified: `Commutator/Basic.lean` does not import Pointwise.
- **Deprecated aliases.** Both multiplicative and additive aliases are present with a date, as the deprecation convention asks. Finding: the multiplicative one puts the attribute inline while the declaration runs onto a second line, unlike the additive one below it. The two-line form compiles.

## Mathlib/Algebra/Group/Subgroup/Pointwise.lean

- **The new import `Mathlib.GroupTheory.Commutator.Basic`.** Finding (blocking): it is not needed. The file compiles without it. A control edit that removes a needed import fails, so the tool does honour header changes.
- **`conj_mem_sup_of_mem_inf_normalizer_of_mem_inf` and `normalizer_le_normalizer_sup_of_normalizer_le_left`.** These are only updated to the new name, which is correct. Nothing to ask.
- **Removal of `normalizer_inf_normalizer_le_normalizer_sup`.** It is replaced by deprecated aliases in Basic.lean, as the convention requires. `iInf_normalizer_le_normalizer_iSup` stays in Pointwise. I considered asking for it to move as well, but did not, because the PR does not need it.

## Mathlib/GroupTheory/Commutator/Basic.lean

- **`commutator_mono_left` / `commutator_mono_right`.** They are tagged `@[gcongr]`, as the monotonicity convention asks. Finding: they only instantiate `commutator_mono`. Tagging `commutator_mono` with `@[gcongr]` is enough for `gcongr` and `grw` to vary one argument alone: I verified a whole-file edit that deletes the two lemmas, and it compiles. One Zulip thread from 2025 says `gcongr` needed a lemma for each set of varying arguments; the reviewed workspace no longer behaves that way.
- **`commutator_le_of_le`.** This is `(commutator_le_sup _ _).trans (sup_le h₁ h₂)`. I considered a "mere combination" request and a naming request (`naming_norm` could not resolve its subject). I did not file either: it is a natural API statement, and I had no convention evidence against the name. `declaration_search` finds no existing duplicate.
- **`commutator_sup_left'` (private).**
  - Findings: it has no docstring and uses `theorem` (I verified `private lemma` with a docstring); it lacks `@[to_additive]`; it writes `Subgroup.` prefixes that are redundant inside `namespace Subgroup`.
  - Its two `have`s are rewritten `at` and so are not inlinable. I considered renaming it `_aux` and did not file that, since a private name matters little.
- **`commutator_sup_left`.**
  - Findings:
    - It can be stated for indexed suprema. A verified `commutator_iSup_left` compiles, and the binary version follows in one line by `iSup_bool_eq`.
    - The hypothesis `[N.Normal]` can be weakened to `H, K ≤ normalizer N` (verified).
    - `@[to_additive]` is missing (verified).
    - There is no docstring and no comment explaining the strategy.
    - The one-term `hHNM` and `hKNM` sit far from their single use in the `simp` (verified inlined).
  - Checked and fine: `hHKN` is placed right before its use. The `grw` steps are idiomatic. Removing `hHNM`/`hKNM` outright fails, so they are needed, only inlined.
- **`commutator_sup_right`.** The proof is a short `simp_rw` from `commutator_sup_left`, which is fine. It shares the missing `@[to_additive]`; I covered that in the `commutator_sup_left` finding as one decision.
- **Naming of the `commutator_sup_*` family.** It is consistent with the file's `commutator_bot_left` / `commutator_bot_right`: the suffix names the side where the `⊥` or `⊔` sits. Nothing to ask.

## Tools used

- `describe`, `file_read`, `file_search`, `declaration_search` (`commutator_mono_left`, `commutator_le_of_le`, `commutator_sup_left`, `commutator_iSup_left`, `map_iSup`), `naming_norm`, `precedent_search` (two queries), `zulip_search` (two queries).
- 10 `lean_verify_edit` runs: 8 compiled, 2 deliberate failures (the import control and the no-`have` variant).
