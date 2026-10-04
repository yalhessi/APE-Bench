# Notes: PR #42184, `tprod_nonneg`

## Inputs read
`brief.md`, `pr.md`, `model.md` and `diff.patch`. Through `ptool file_read`, I read all of
`target/Mathlib/Topology/Algebra/InfiniteSum/Order.lean` as the PR leaves it (lines 1-399).

## Tool calls
- `declaration_search`:
  - `tprod_nonneg`: new in this PR only, so it duplicates nothing.
  - `HasProd.nonneg`: absent.
  - `tprod_pos`: absent.
  - `finprod_nonneg`: exists at Finprod.lean:259, but needs `CommSemiring` + `IsOrderedRing`.
  - `Finset.prod_nonneg`: GroupWithZero/Finset.lean:31, needs `Preorder`/`ZeroLEOneClass`/`PosMulMono`.
  - `tprod_bot`: Defs.lean:184.
- `content_search` for `0 ≤ ∏'` across Mathlib: the only hit is this PR. No existing lemma under
  another name, so no duplication finding.
- `content_search` for positivity extensions: `tsum` and `Finset.prod` have one, `tprod` does not.
- `content_search` for section names: `CommMonoidWithZero` / `MonoidWithZero` are the precedent.
- `naming_norm tprod_nonneg`: `subject_unresolved`, so the naming census was not measured.
- `precedent_search`: no applicable precedent among the returned comments.
- `zulip_search`: no relevant prior discussion.
- `lean_verify_edit`, three calls, all `compiled`:
  1. The generalized declaration without `[L.NeBot]`.
  2. A line-mode replacement of lines 237-246 with a renamed `CommMonoidWithZero` section holding
     `HasProd.nonneg` and the generalized `tprod_nonneg`.
  3. The proof-golf alone, keeping the PR's signature.

## Object by object

### `section WithZero` / `end WithZero`
- The section is opened and closed, and both commands are separated by blank lines. No problem there.
- The name `WithZero` collides with the type constructor `WithZero`. The setting is
  `CommMonoidWithZero`. Finding 4 (advisory): rename it.
- The section has no `variable` line and holds one declaration. If `HasProd.nonneg` is added
  (finding 3), a shared `variable` line becomes justified. I verified that layout compiles.
- Placement between `OrderedCommGroup` and `CanonicallyOrderedMul` is acceptable. The
  `CommMonoidWithZero` typeclasses conflict with the `CommMonoid` `variable`s of the earlier
  sections, so a separate section is needed. No finding.

### `tprod_nonneg`
- **Generalization (finding 1, blocking):** `[L.NeBot]` is unnecessary. The siblings
  `one_le_tprod`, `tprod_le_one` and `tsum_nonneg` hold for all `L`. The bot case follows from
  `tprod_bot` plus `finprod_induction` with `mul_nonneg`. I used `finprod_induction` because
  `finprod_nonneg` assumes an ordered semiring, which is stronger than this lemma's classes.
  Verified to compile.
- **Proof-golf (finding 2, advisory):** use the file's own `le_hasProd_of_le_prod` instead of a
  raw `ge_of_tendsto'`. Verified.
- **Sibling completeness (finding 3, advisory):** add `HasProd.nonneg`, matching the
  `HasProd.one_le`/`one_le_tprod` and `HasProd.le_one`/`tprod_le_one` pairs. Verified.
- **Typeclass assumptions:** `CommMonoidWithZero` + `Preorder` + `ZeroLEOneClass` + `PosMulMono` is
  exactly what `Finset.prod_nonneg` needs, and `ClosedIciTopology` is the right closedness
  assumption (the same one as `le_hasProd_of_le_prod`). These are minimal, so no finding.
- **Binders:** `{f}` is implicit and inferable from `hf`. The order (classes, then data, then
  hypothesis) follows the convention. No finding.
- **Name:** `tprod_nonneg` matches `tsum_nonneg`, `Finset.prod_nonneg` and `finprod_nonneg`, and
  states the conclusion. No finding.
- **Non-multipliable branch:** `simp [tprod_eq_one_of_not_multipliable h]` is terminal, so it is
  correctly left unsqueezed and lists no default simp lemma. No finding.
- **Statement layout:** continuation lines are indented four spaces, the conclusion starts on its
  own line, and no line exceeds 100 characters. No finding.
- **`theorem` without a docstring:** the file uses `theorem` throughout without docstrings, so
  this is not something to ask of this PR.
- **Bound variable:** the statement writes `∏'[L] x, f x` where siblings use `i`. This is a
  trivial nit and I did not file it. My verified replacement already uses `i`.
- **Not filed:**
  - A `tprod` positivity extension, the analogue of `evalTsum`. It would be a follow-up, not a
    change to this PR.
  - Multiplicative/additive counterpart: none applies. `tsum_nonneg` already exists, as the
    additive form of `one_le_tprod`.

### PR title
`feat(Topology/InfiniteSum): ...` follows `type(Area): description`. The area abbreviates
`Topology/Algebra/InfiniteSum`, which is common practice, so I did not file it.
