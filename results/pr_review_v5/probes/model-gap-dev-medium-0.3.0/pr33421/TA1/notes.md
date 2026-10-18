# Review notes: PR #33421, "chore(Algebra/Order/Floor): review API about `round`"

I read pr.md, model.md and diff.patch, then the full PR-state files `Round.lean`,
`Topology/Algebra/Order/Floor.lean`, and the relevant part of `Floor/Ring.lean`, all through `ptool file_read`.
Every proposed edit below was checked with `lean_verify_edit` unless stated otherwise. Compiling
`Topology/Algebra/Order/Floor.lean` as the PR leaves it gives no errors and no warnings.

## Object by object

### Mathlib/Algebra/Order/Floor/Ring.lean
- `Int.ceil_intCast_add`, `ceil_natCast_add`, `ceil_ofNat_add`, `ceil_one_add`: these are correct `@[simp]`
  mirrors of the existing floor lemmas. Statements and proofs are fine.
  - Family gap: `Int.floor_one_add` does not exist, while `fract_one_add` exists and `ceil_one_add` is
    now added. `simp` makes no progress on `⌊1 + a⌋ = 1 + ⌊a⌋`, and the proposed lemma compiles.
    **Filed.**
  - `round_one_add` is also missing, but no `*_one_add` lemma for round is in the PR's scope, so I did
    not file it.
- `Int.two_mul_fract_eq_one_iff_exists_int`: the statement is correct, and its placement in the
  LinearOrderedRing section is right.
  - `refine ⟨_, ?_⟩; rintro ⟨n, hn⟩` can bind in the refine instead. The edit compiles. **Filed**
    (refine convention).

### Mathlib/Algebra/Order/Round.lean
- import: the private `import Mathlib.Algebra.Order.Interval.Set.Group` is unneeded. Deleting it compiles.
  **Filed.**
  - All 12 downstream added imports are genuinely needed: deleting each one gives compile errors. Not filed.
- `round_eq'`:
  - The prime-only distinction from `round_eq` is **filed** (rename).
  - The first branch's proof golfs to one line. Verified. **Filed.**
  - In the second branch, I tried `linarith` for `0 < fract x`. It fails over a `Ring`, so I left that branch.
  - The TODO in the docstring is **filed**, advisory.
- `round_eq_half_ceil_two_mul`:
  - The statement and its hypothesis are correct and needed: at fract = 1/2 the two sides differ.
  - Naming ('half' for `/ 2`) is **filed**.
  - The proof is reasonable. `refine absurd ?_ hx; exact ...` could be one `exact absurd ... hx`. That is too
    minor to file.
- `round_eq` (new proof): a big simplification and fine.
- `round_eq_iff`: the new lemma is fine. It is not `@[simp]`, which is correct because `n` is generic.
  - `1 / 2` vs `2⁻¹` follows the file's existing spelling.
- `round_two_inv`, `round_neg_two_inv`: the incidental proof rewrites are **filed**. The old `simp only`
  proofs still compile.
- `round_eq_zero_iff`: the proof change is required to drop the `Interval.Set.Group` dependency. Fine.

### Mathlib/Topology/Algebra/Order/Floor.lean
- imports: `public import Mathlib.Algebra.Order.Floor.Ring` is now redundant because Round imports it
  publicly. Deleting it compiles. **Filed.**
- Module docstring:
  - It does not mention round or the new floor/ceil lemmas.
  - Its existing `continuousOn_ceil` interval is wrong (`Ioc n (n+1)` vs `Ioc (n - 1) n`).
  - **Filed.**
- `continuousOn_floor` / `continuousOn_ceil`:
  - The codomain change to ℤ is the right formulation.
  - The eta-expanded `fun x => floor x` should now be `floor`. Verified. **Filed** (lambda convention).
  - The statement change is breaking but no declaration is removed, so the deprecation convention does
    not apply. I folded a note on it into the scope finding.
  - `floor_eq_on_Ico'` and `ceil_eq_on_Ioc'` lose their only users. I am not requesting anything about that.
- `continuousAt_floor`: `@[fun_prop]`, the statement and the proof are fine.
- `continuousAt_ceil`:
  - The missing `@[fun_prop]` is **filed**. `fun_prop` fails on ceil and succeeds on floor; the tagged
    version compiles.
  - The hypothesis `x ≠ ⌊x⌋` vs `x ≠ ⌈x⌉` is **filed**. The simpler proof compiles.
  - I checked whether `IsStrictOrderedRing` is needed: it is (`ceil_lt_add_one`), so nothing to file.
- `continuousOn_floor_compl_range` / `continuousOn_ceil_compl_range`:
  - The name omits `intCast`. **Filed**, citing `isOpen_compl_range_intCast` and others.
  - The proofs (`intro; refine; simp_all`) are fine.
  - A term-mode form like `continuousOn_round`'s would be marginally more consistent. Not filed.
- `tendsto_floor_right_pure_floor`: the `omit` is removed by reordering, which is good.
  - `tendsto_ceil_right_pure_floor_add_one` still has `omit [IsStrictOrderedRing α] in`. Moving it up
    compiles. **Filed.**
- `continuousOn_fract`, `continuousAt_fract`: the new proofs are fine.
  - I tried `unfold fract; fun_prop (disch := exact h)`. It fails because there is no fun_prop lemma for
    `Int.cast`. With a helper it would be no shorter than the two-line term, so it is not filed.
- `tendsto_round_nhdsGE_pure`, `tendsto_round_nhdsLT_pure_half_ceil`, `continuousAt_round`,
  `continuousOn_round`:
  - The repeated binders are **filed** (variable/section, verified).
  - The `half_ceil` naming of the LT lemma is **filed**.
  - The missing `@[fun_prop]` on `continuousAt_round` / `continuousOn_round` is **filed** (verified).
  - The `continuousAt_round` proof golf via `nhdsLT_sup_nhdsGE` is **filed** (verified).
  - The duplicated `Tendsto (2 * ·)` `have`s are **filed** as extraction (verified compile).
  - I tried to make the LT proof mirror the GE one with `simpa using (tendsto_pure_pure ...).comp ...`.
    It fails (`⌈2x⌉ - 1 + 1` is not simplified inside the ediv), so the existing `filter_upwards` stays.
- `ContinuousOn.comp_fract''`: unchanged apart from the enclosing `end Ring`. Its prime is pre-existing.
  Nothing filed.
- `section Ring` / `end Ring` wrapper: fine.

### Downstream import additions (10 files)
Each added import is needed: deleting any one of them gives compile errors. Nothing filed.

### Scope
The floor/ceil continuity API is separable from the round API: `continuousAt_round` does not use
`continuousAt_floor`/`continuousAt_ceil`. **Filed**, advisory.

## Conventions: where filed, where left

- **simp on definition-applied-to-canonical-argument:** the new `ceil_*_add` lemmas are `@[simp]`.
  - `round_eq'`, `round_eq` and `round_eq_iff` have a generic argument or would unfold `round`.
  - `round_eq_half_ceil_two_mul` has a hypothesis.
  - None filed.
- **Name built from statement declarations:**
  - Filed `round_eq_half_ceil_two_mul`, `tendsto_round_nhdsLT_pure_half_ceil` and
    `continuousOn_floor_compl_range` (ceil sibling included).
  - Left `Int.two_mul_fract_eq_one_iff_exists_int`, which spells every term, and `round_eq_iff`, which
    matches `floor_eq_iff`.
- **Automation only when the explicit proof is long:** filed `round_two_inv` (`round_neg_two_inv`
  included).
  - Left `round_eq_iff` (`norm_num` for a new lemma; no explicit proof was replaced) and `round_eq`
    (it replaces an 18-line proof).
  - Left `round_eq_zero_iff`: its change is needed to drop the import.
- **Unneeded or redundant imports:** filed `Topology/Algebra/Order/Floor.lean` (`Floor.Ring`) and
  `Round.lean` (`Interval.Set.Group`). The 12 downstream additions were each checked to be needed.
- **Cut at natural seams:** filed the floor/ceil continuity split.
- **Shared arguments via `variable`:** filed for the four round lemmas, anchored at
  `tendsto_round_nhdsGE_pure`.
  - The `Int.ceil_*_add` lemmas use the section's variables already.
- **Head-first name order:** I checked the new names and left them; each reads lhs-relation-rhs.
- **Deprecate removed or moved declarations:** nothing is removed. The `section` removal in model.md is a
  restructure.
  - The `continuousOn_floor/ceil` statement change is folded into the scope finding.
- **Justify non-obvious constructs:** the remaining `omit` is filed for removal rather than comment.
  - No other workaround or private import is left once the Round.lean import is removed.
- **Attribute on part of a sibling family:** filed `continuousAt_ceil` (vs `continuousAt_floor`).
- **gcongr for monotonicity steps:**
  - The `add_le_add ha ha` / `add_lt_add ha ha` terms in the `Tendsto (2 * ·)` haves: I tried
    `simp only [mem_Ici]; gcongr`. It leaves `x ≤ id a` goals and is longer, so I left them.
  - `le_mul_of_one_le_left` in `round_eq'` disappears with the filed golf.
  - The `gcongr` in `continuousAt_round` is replaced by the filed golf.
- **Sibling variants for all members:** filed `Int.floor_one_add`.
- **Primes vs naming the differing term:** filed `round_eq'`.
- **Docstrings for opaque statements:** `round_eq_half_ceil_two_mul` has one.
  - The filter statements `tendsto_round_nhds*_pure*` are in the same style as their undocumented
    siblings `tendsto_floor_*_pure*`. Not filed.
- **Extract independent facts:** filed the `Tendsto (2 * ·)` haves (target
  `tendsto_round_nhdsLT_pure_half_ceil`).
- **Prime only with an unprimed sibling:** `round_eq'` has the unprimed sibling `round_eq`. It is
  covered by the rename finding above.
- **Sibling name pattern / namespace:** `tendsto_round_nhdsLT_pure_half_ceil` is filed against
  `tendsto_floor_left_pure_ceil_sub_one`.
  - Left the `nhdsGE`/`nhdsLT` vs `left`/`right` spelling. The newer `nhdsGE` spelling is the library's
    direction.
- **Eta / `·` lambdas:** filed `continuousOn_floor` (ceil included).
  - `fun n ↦ (n + 1) / 2` and `fun a ha ↦ add_le_add ha ha` are not single applications of their binders.
- **`refine` binds subgoal hypotheses:** filed `Int.two_mul_fract_eq_one_iff_exists_int`.
  - `round_eq'`'s `refine lt_of_le_of_lt ?_ h` disappears with the golf.
  - The `intro x hx; refine (continuousAt_floor ?_)...` in `*_compl_range` introduces the goal's own
    binders, not a subgoal's.
- **`@[fun_prop]` on preservation lemmas:** filed `continuousAt_ceil`, and `continuousAt_round` (with
  `continuousOn_round`).
  - `continuousAt_floor` and the `*_compl_range` lemmas already have it.
- **Unnecessary changes to existing code:** filed `round_two_inv`/`round_neg_two_inv`.
  - Left `continuousAt_fract`/`continuousOn_fract`: they are rewritten to use the new lemmas and the
    changed codomain.
- **Sections instead of `omit`:** filed `tendsto_ceil_right_pure_floor_add_one`.
- **Library's usual spelling of hypotheses:** filed `continuousAt_ceil` (`x ≠ ⌈x⌉`).
  - Left `2 * fract x ≠ 1`: the ring setting has no `1 / 2`.
- **`fun_prop` with a discharger instead of `.add`/`.comp`:** tried on `continuousAt_fract`. It fails
  because there is no `Int.cast` fun_prop lemma, and the term proof is two lines, so I left it.
- **Equation lemma `_eq` suffix:** `round_eq'` is covered by the rename. `round_eq` is pre-existing.
  `round_eq_iff` is an iff.
