# Review notes: PR #42184 (non-negativity of tprod)

The PR adds one theorem, `tprod_nonneg`, to `Mathlib/Topology/Algebra/InfiniteSum/Order.lean`, inside a new
`section WithZero ... end WithZero`.

## What I did

- Read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then the whole file as the PR leaves it
  (`file_read target/Mathlib/Topology/Algebra/InfiniteSum/Order.lean`).
- `declaration_search` for `tprod_nonneg` (new in this PR, no earlier copy), `finprod_nonneg` (Finprod.lean:259,
  `CommSemiring` + `IsOrderedRing`), `tprod_bot` (Defs.lean:184), `Finset.prod_nonneg` (same typeclass level as the
  new lemma), and `tprod_pos`, `HasProd.nonneg` and `tprod_eq_zero_iff` (none of the three exists).
- `content_search` for `0 ≤ ∏'` across Mathlib: only the new lemma, so it is not a duplicate. Searched for a
  `tprod` positivity extension: none. `HasSum.nonneg` comes only from `to_additive` of `HasProd.one_le`.
- `naming_norm tprod_nonneg`: subject unresolved, so naming is unmeasured. Judged by hand: `tprod_nonneg` sits beside
  `tsum_nonneg`, `finprod_nonneg` and `Finset.prod_nonneg` and is the expected name. No naming finding.
- `precedent_search` and `zulip_search`: nothing that bears on this lemma.
- `lean_verify_edit`, four checks:
  1. `tprod_nonneg` without `[L.NeBot]`, using `tprod_bot` + `finprod_induction` in the trivial-filter case and
     `le_hasProd_of_le_prod` otherwise: compiled.
  2. The same, plus an `evalTprod` positivity extension modelled on `evalTsum`: the extension elaborates, and
     `positivity` proves `0 ≤ ∏' n : ℕ, ((n : R) * n)` and a nested `∑' ∏'` goal. With a free filter `L`, the
     `∏'[L]` goal fails, but `evalTsum` fails the same way on `∑'[L]`. That limitation was already there and is not
     caused by the new code.
  3. A restructured section: a `variable` line, `HasProd.nonneg`, then `tprod_nonneg` proved from it: compiled.
  4. A plain `(n : R) + 1` positivity goal fails in this file's context with or without the change. It says
     nothing about the PR; I used `n * n` examples instead.

## Object by object

### `tprod_nonneg`
- **generalization:** `[L.NeBot]` is not needed. The sibling lemmas `one_le_tprod`/`tsum_nonneg`, `tprod_le_one`
  and `tprod_le_of_prod_le'` handle the trivial filter with `tprod_bot`. Verified that the generalized form compiles.
  Finding 1, blocking.
- **proof-golf / duplication:** `ge_of_tendsto' h.hasProd ...` is exactly the body of the file's own
  `le_hasProd_of_le_prod`. Finding 2, advisory.
- **family (sibling convention):** the file pairs each `tprod` order lemma with its `HasProd` form
  (`HasProd.one_le`/`one_le_tprod`, `HasProd.le_one`/`tprod_le_one`). `HasProd.nonneg` is missing. Finding 3,
  advisory.
- **typeclass assumptions:** `CommMonoidWithZero`, `Preorder`, `ZeroLEOneClass`, `PosMulMono` match
  `Finset.prod_nonneg` exactly. `ClosedIciTopology` is what `ge_of_tendsto'` needs. `ZeroLEOneClass` is also used in
  the non-multipliable branch (`0 ≤ 1`). None can be dropped. No finding.
- **correctness:** the statement is right, and the non-multipliable branch uses the `tprod = 1` convention
  correctly. No finding.
- **naming:** fine (see above). The bound variable is `x` while the hypothesis and the siblings use `i`. That is
  minor, and I folded it into the restated declaration in finding 1 rather than making it a separate ask.
- **documentation:** no other lemma in this file has a docstring, so no docstring ask.

### `section WithZero` / `end WithZero`
- **style:** named after the type `WithZero`, which is unrelated to this code, and declares no `variable`s. Every
  other section names its algebraic setting and opens with a `variable` line. Finding 5, advisory.
- **scope:** `Order.lean` is the right file, and placing the section after the ordered-group section is reasonable.
  No move requested.

### File level (`Order.lean`)
- **sibling tactic support:** `evalTsum` gives `positivity` a `tsum` extension. The PR adds the multiplicative
  counterpart lemma but no `tprod` extension. Verified that an extension of the same shape works once `NeBot` is
  dropped. Finding 4, advisory.
- No module-docstring change is needed: the header already covers "infinite sums and products and order".

## Findings: 5 (1 blocking, 4 advisory)
