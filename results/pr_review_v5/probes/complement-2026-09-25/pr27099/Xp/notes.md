# PR #27099 review notes

The paths the tools accept start with `target/`. The file as the PR leaves it compiles with no
errors or warnings (as-is lean_verify_edit).

**`Mathlib.lean`**: the new import sits alphabetically between `ModelTheory.Algebra.*` and
`ModelTheory.Basic`, which is correct. Nothing to ask.

**File header, imports and module doc**: removing `import Mathlib.Algebra.Group.Basic` still
compiles (lean_verify_edit on line 6), so I asked to drop it. The module doc follows the `Ring/Basic.lean` layout. The TODO names
`Language.IsOrdered`, which exists in `Order.lean` (seen in content_search). The only doc ask is
the implementation-note one, filed under the instance.

**`presburgerFunc`, `Language.presburger`**: these are word-for-word parallel to `ringFunc` / `Language.ring`
in `ModelTheory/Algebra/Ring/Basic.lean` (file_read): same `deriving DecidableEq` / `IsAlgebraic`
and the same naming. Nothing to ask. A Zulip search on Presburger / model theory turned up no prior
convention discussion.

**`Zero`/`One`/`Add`/`NatCast`/`SMul` instances on `presburger.Term α`**: these mirror Ring's instances.
Using `Nat.unaryCast` and `nsmulRec` is sensible. Ring also has `zero_def`/`add_def` lemmas, but
here everything is `rfl`, so I did not ask for them.

**`natCast_zero`, `natCast_succ`**: raw `NatCast.natCast` in the statements. The coercion form
compiles (lean_verify_edit), so I filed a style ask. naming_norm had no population for this
subject, so there is no naming ask.

**`zero_nsmul`, `succ_nsmul`**: content_search found the root `zero_nsmul` / `succ_nsmul` in
`Algebra/Group/Defs.lean` (to_additive-generated, so declaration_search missed them). That gives the
`protected` ask. A probe example showed that `@[simp] succ_nsmul` unfolds `3 • t` and blocks
`realize_nsmul` (failed goal). Removing simp fixes it (lean_verify_edit success). Both results
mattered.

**`succ`**: this is a thin wrapper for `t + 1` with `realize_succ`, probably wanted by #27100. I
considered asking to remove it but have no evidence it is unwanted, so I did not.

**`finsum`**: content_search in `Finprod.lean` confirmed that the root `finsum` means the ∑ᶠ
finite-support sum, which gives the rename ask. The Finset generalization, with a body via
`List.sum`, compiled (lean_verify_edit), which gives the generalization ask. There is also a
docstring-indent nit. naming_norm could not resolve the subject for `finsum` (unmeasured).

**Structure instance**: content_search on `Order.lean` and file_read on `Ring/Basic.lean` show that
both sibling languages deliberately use a `def` rather than a global instance. I filed an advisory
asking to justify the choice or demote the instance. The unused `v` in the `.one` arm is a style nit
(the `_` version compiles). precedent_search returned only unrelated comments.

**`funMap_zero/one/add`**: the `@Structure.funMap presburger M _ _` form works, but the named-argument
form compiles (lean_verify_edit), so I filed an advisory style ask.

**`realize_zero/one/succ/add`**: `rfl` proofs with correct simp shape. Nothing to ask.

**`realize_natCast`**: the lemma itself is fine. A probe showed that `simp` cannot close
`realize v ((2:ℕ) : Term) = 2`, because `Nat.cast_ofNat` fires first. Adding `realize_ofNat`
(term proof `realize_natCast`) fixes it (lean_verify_edit). I filed this as a missing-API ask on
this declaration.

**`realize_nsmul`**: the statement and hypotheses are fine (`AddMonoidWithOne` is natural). The
only change is the `succ_nsmul` simp-set change above.

**`realize_finsum`**: the long manual proof collapses to `rw [sum, ← Finset.sum_map_toList];
generalize; induction … with simp [*]`. It compiled (lean_verify_edit, together with the other
edits; the combined edit succeeded). The existence of `Finset.sum_map_toList` came from content_search
(`Finset.prod_toList` is proved via `prod_map_toList`). This also removes the `←` spacing nits.

I made about 22 tool calls, 5 of them compiles. Nothing is blocking: the file builds, and every ask
is advisory.
