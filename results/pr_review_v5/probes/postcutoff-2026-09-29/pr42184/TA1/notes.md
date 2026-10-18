# Review notes: PR #42184, `tprod_nonneg`

## What I did

1. Read `pr.md`, `model.md`, `diff.patch`, and the brief.
2. Read the whole reviewed file `Mathlib/Topology/Algebra/InfiniteSum/Order.lean` (as the PR leaves it)
   with `file_read`. Read the neighbours the change relies on or echoes: `tprod_bot` and
   `tprod_eq_one_of_not_multipliable` (`InfiniteSum/Defs.lean`), `finprod_induction`,
   `finprod_nonneg`, `one_le_finprod` (`BigOperators/Finprod.lean`), `Finset.prod_nonneg`
   (`Algebra/Order/BigOperators/GroupWithZero/Finset.lean`), and the `CommMonoidWithZero` section of
   `InfiniteSum/Basic.lean`.
3. `declaration_search`: `tprod_nonneg` (only in this PR), `HasProd.nonneg` (nowhere), `tprod_pos`
   (nowhere), `finprod_nonneg`, `tprod_bot`, `Finset.prod_nonneg`, `tprod_eq_one_of_not_multipliable`.
   `content_search` for `0 [≤<] ∏'` across Mathlib: only this PR's statement, so no duplicate.
4. `naming_norm tprod_nonneg`: subject unresolved (unmeasured). `precedent_search`, `zulip_search`:
   nothing bearing on this lemma.
5. `lean_verify_edit`:
   - as-is file: compiles, no warnings.
   - `tprod_nonneg` without `[L.NeBot]` (bot case through `tprod_bot` + `finprod_induction`): compiled.
   - section renamed `CommMonoidWithZero` with a shared `variable` line, new `HasProd.nonneg`, and
     `tprod_nonneg` derived from it: compiled.
   - that plus an `evalTprod` positivity extension and a test `example ... 0 ≤ ∏' i, f i ^ 2 := by
     positivity`: compiled. The same `example` against the PR as is fails ("failed to prove
     positivity"), so the extension is what proves it.
   - `lemma` + docstring version of `tprod_nonneg`: compiled, no warnings.

## Object by object

### `section WithZero` / `end WithZero`
- Blank lines around both: present. Closed with a matching `end`: yes.
- Name: `WithZero` is the type constructor `WithZero α`; the notion here is `CommMonoidWithZero`, and
  the sibling file `InfiniteSum/Basic.lean` and the `Finset.prod_nonneg` file both use
  `section CommMonoidWithZero`. **Filed** (finding 2).

### `tprod_nonneg`
- Correctness: compiles; statement true; the junk-value case (`tprod = 1` when not multipliable) is
  handled by `ZeroLEOneClass`. Nothing wrong.
- Generalization: `[L.NeBot]` is not needed (siblings `one_le_tprod`, `tprod_le_one` drop it and
  handle `⊥` by `tprod_bot`). **Filed** (finding 1, blocking). The other assumptions are each used:
  `ZeroLEOneClass` (`0 ≤ 1`, and in `prod_nonneg`), `PosMulMono` (`mul_nonneg`), `ClosedIciTopology`
  (`ge_of_tendsto'`), `Preorder` is already the weakest order. `CommMonoidWithZero` is the natural
  algebraic level (`tprod` needs `CommMonoid`, the statement needs `0`).
- Duplication: no existing `tprod` nonnegativity lemma (declaration and content searches).
  `finprod_nonneg` needs `IsOrderedRing`, so it cannot be reused for the bot case at this generality;
  `finprod_induction` is used, as `finprod_nonneg` itself does.
- Sibling family: `HasProd.one_le`/`one_le_tprod`, `HasProd.le_one`/`tprod_le_one` come in pairs;
  `HasProd.nonneg` is missing, and the proof uses `ge_of_tendsto'` rather than the file's
  `le_hasProd_of_le_prod`. **Filed** (finding 3, advisory).
- Positivity: `evalTsum` exists in the file; no `tprod` extension. **Filed** (finding 5, advisory;
  checked to compile and to make `positivity` close a `tprod` goal).
- Naming: `tprod_nonneg` matches `Finset.prod_nonneg` and `tsum_nonneg`; nothing to ask.
- Documentation: `theorem` without docstring. **Filed** (finding 4, advisory).
- Proof golf: three-line proof; nothing shorter found beyond the `le_hasProd_of_le_prod` wrapper
  (folded into finding 3). The terminal `simp` is fine unsqueezed.
- Style: bound variable `x` in `∏'[L] x, f x` versus `i` in `hf` and the siblings; folded into the
  statement suggested in finding 1, not filed separately.
- No additive counterpart exists for a `CommMonoidWithZero` statement, so no `to_additive`.

### PR-level
- Title `feat(Topology/InfiniteSum): non-negativity of tprod` follows `type(Area): description`.

## Conventions (submission message)

- Library-named predicate instead of unfolding: left. `hf : ∀ i, 0 ≤ f i` is the form the siblings
  use (`one_le_tprod (h : ∀ i, 1 ≤ g i)`); no named predicate is unfolded.
- Drop unneeded hypotheses: **filed** at `tprod_nonneg` (`[L.NeBot]`, finding 1). The other
  assumptions are each used (see above).
- Blank line around `section`/`end`/`variable`: left. The diff has a blank line after
  `section WithZero`, before and after `end WithZero`.
- Terminal `simp` not squeezed: left. `· simp [tprod_eq_one_of_not_multipliable h]` is terminal and
  unsqueezed.
- `simp` lists no default-simp lemmas: left. `tprod_eq_one_of_not_multipliable` is `@[to_additive]`
  only (Defs.lean:200-201) and takes a hypothesis.
- Name built from the statement's declarations: left. `tprod_nonneg` = `tprod` + `nonneg`, as in
  `Finset.prod_nonneg`, `tsum_nonneg`.
- Break after the colon: left. Lines `... (hf : ∀ i, 0 ≤ f i) :` / `0 ≤ ∏'[L] x, f x := by`.
- Binder kind follows inferability: left. `{f : ι → α}` is determined by `hf`, `L` by the goal.
- Four-space continuation indent: left. Both continuation lines start with four spaces.
- Attribute on some siblings only: left. Siblings carry `@[to_additive]`; this one cannot (no additive
  analogue of `CommMonoidWithZero`), like the file's `HasProd.abs` section.
- Break lines only past 100 chars: left. Lengths 96, 84, 26; joining the conclusion onto line 2 would
  be 107.
- No new declaration when one exists: left. `declaration_search tprod_nonneg` finds it only in this
  PR; `content_search '0 [≤<] ∏''` finds no other statement.
- Variant provided for the whole sibling family: **filed** `HasProd.nonneg` (finding 3) and the
  `tprod` positivity extension beside `evalTsum` (finding 5).
- Name states the conclusion: left. `tprod_nonneg` names only the conclusion.
- Every `section` closed: left. `end WithZero` is present.
- PR title `type(Area): description`: left. Title is `feat(Topology/InfiniteSum): ...`.
- Name follows siblings' pattern: left. `tprod_nonneg` parallels `tsum_nonneg`; the suggested
  `HasProd.nonneg` parallels `HasSum.nonneg`.
- Grouping beside lemmas about the same notion: left. It sits in `InfiniteSum/Order.lean` among the
  `tprod` order lemmas, in its own section because its typeclasses differ.
- Additive/multiplicative counterpart: left. No additive analogue of a `CommMonoidWithZero` statement.
- Sections instead of `omit`: left. The PR uses its own section, no `omit`.
- `theorem` needs a docstring: **filed** at `tprod_nonneg` (finding 4).
- Most-used spelling: left. `0 ≤ ∏'[L] ...` with `∀ i, 0 ≤ f i` matches `Finset.prod_nonneg`.
- `variable` only for shared arguments: left for the PR as it stands (one lemma, arguments bound in
  its signature); a shared `variable` line is suggested only if `HasProd.nonneg` is added
  (finding 2).
- Section named after its notion: **filed** at `section WithZero` (finding 2).
- Arguments ordered ambient-first: left. Typeclasses, then `{f}`, then `hf`. Finding 2 suggests the
  file's algebra, order, topology order of the instances inside the shared `variable` line.
