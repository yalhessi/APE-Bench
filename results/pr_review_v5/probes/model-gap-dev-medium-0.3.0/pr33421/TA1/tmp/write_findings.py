import json, sys
out = sys.argv[1]
F = []
def add(target, claim, change, severity, evidence):
    F.append(dict(target=target, claim=claim, requested_change=change, severity=severity, evidence=evidence))

add("continuousAt_ceil",
    "`continuousAt_ceil` is not tagged `@[fun_prop]`, although its sibling `continuousAt_floor` (and both `continuousOn_floor_compl_range` / `continuousOn_ceil_compl_range`) added in the same hunk are, so `fun_prop` can prove continuity of `⌊·⌋` at a non-integer but not of `⌈·⌉`.",
    "Add `@[fun_prop]` to `continuousAt_ceil`, matching `continuousAt_floor` (or add a comment saying why it is excluded).",
    "advisory",
    "lean_verify_edit on Mathlib/Topology/Algebra/Order/Floor.lean with two inserted examples `example {x : α} (hx : x ≠ ⌊x⌋) : ContinuousAt (fun y : α => ⌈y⌉) x := by fun_prop (disch := exact hx)` and the same for `⌊y⌋`: the ceil example fails ('`fun_prop` was unable to prove ... No theorems found for `Int.ceil`'), the floor one compiles. Replacing the declaration with the `@[fun_prop]`-tagged version: outcome `compiled`, no errors or warnings.")

add("continuousAt_round",
    "The new continuity lemmas `continuousAt_round` and `continuousOn_round` state that `round` is continuous (at / on the non-half-integer points) but are not tagged `@[fun_prop]`, unlike the `continuousAt_floor` / `continuousOn_floor_compl_range` lemmas added in the same PR, so `fun_prop` cannot use them.",
    "Tag `continuousAt_round` and `continuousOn_round` with `@[fun_prop]`.",
    "advisory",
    "lean_verify_edit replacing lines 225-236 of Mathlib/Topology/Algebra/Order/Floor.lean with `@[fun_prop]`-tagged versions of both lemmas plus `example ... (hx : 2 * fract x ≠ 1) : ContinuousAt (fun y => round y) x := by fun_prop (disch := exact hx)`: outcome `compiled` (only a long-line warning on my test example).")

add("Mathlib/Topology/Algebra/Order/Floor.lean",
    "After adding `public import Mathlib.Algebra.Order.Round`, the existing `public import Mathlib.Algebra.Order.Floor.Ring` is redundant: `Mathlib.Algebra.Order.Round` itself starts with `public import Mathlib.Algebra.Order.Floor.Ring`.",
    "Delete the line `public import Mathlib.Algebra.Order.Floor.Ring` from `Mathlib/Topology/Algebra/Order/Floor.lean`.",
    "advisory",
    "file_read of target/Mathlib/Algebra/Order/Round.lean line 8: `public import Mathlib.Algebra.Order.Floor.Ring`. lean_verify_edit deleting line 8 of Mathlib/Topology/Algebra/Order/Floor.lean: outcome `compiled`, no errors, no warnings.")

add("Mathlib/Algebra/Order/Round.lean",
    "The PR demotes `public import Mathlib.Algebra.Order.Interval.Set.Group` to a private `import`, but after the proof changes (`round_eq_zero_iff` no longer uses `add_mem_Ico_iff_left`) nothing in the file needs it, and a private import is not re-exported, so the line is dead weight.",
    "Remove `import Mathlib.Algebra.Order.Interval.Set.Group` from `Mathlib/Algebra/Order/Round.lean` (the downstream files that now import it directly keep their imports).",
    "advisory",
    "lean_verify_edit deleting line 9 (`import Mathlib.Algebra.Order.Interval.Set.Group`) of Mathlib/Algebra/Order/Round.lean: outcome `compiled`, no errors, no warnings. Separately checked that each of the 12 downstream added imports is needed (deleting each gives compile errors, e.g. `Unknown identifier sub_mem_Ioo_iff_left` in AddCircle/Defs.lean), so only the Round.lean line is unneeded.")

add("round_eq'",
    "`round_eq'` is distinguished from `round_eq` only by a prime, although the two state different formulas (`⌊x + 1 / 2⌋` over fields vs `(⌊2 * x⌋ + 1) / 2` over rings) and `round_eq'` is the more general one.",
    "Rename `round_eq'` to a name spelling its right-hand side, e.g. `round_eq_floor_two_mul_add_one_div_two`, and update its uses (`round_eq`, `round_eq_half_ceil_two_mul`, `tendsto_round_nhdsGE_pure`, `tendsto_round_nhdsLT_pure_half_ceil`).",
    "advisory",
    "Statements read from target/Mathlib/Algebra/Order/Round.lean lines 51 and 173. declaration_search: `round_eq_floor_two_mul_add_one_div_two` does not exist. naming_norm on `round_eq'`: leading prefix `round_` conforms (22/23), the tool does not measure primes.")

add("round_eq_half_ceil_two_mul",
    "The name `round_eq_half_ceil_two_mul` uses the informal 'half' for integer division `/ 2` and orders the tokens away from the statement `round x = ⌈2 * x⌉ / 2`.",
    "Rename to `round_eq_ceil_two_mul_div_two`.",
    "advisory",
    "Statement read at target/Mathlib/Algebra/Order/Round.lean line 85; `/ 2` here is `Int` division, for which the declaration name is `div`, read head-first as ceil(two_mul) div two.")

add("tendsto_round_nhdsLT_pure_half_ceil",
    "`tendsto_round_nhdsLT_pure_half_ceil` names the limit `⌈2 * x⌉ / 2` as `half_ceil`, while its siblings in the same file spell the limit from the declarations in it (`tendsto_floor_left_pure_ceil_sub_one` for `⌈x⌉ - 1`, `tendsto_ceil_right_pure_floor_add_one` for `⌊x⌋ + 1`).",
    "Rename to `tendsto_round_nhdsLT_pure_ceil_two_mul_div_two` (consistently with the rename of `round_eq_half_ceil_two_mul`).",
    "advisory",
    "Sibling names read in target/Mathlib/Topology/Algebra/Order/Floor.lean lines 139 and 151. naming_norm returned `subject_unresolved` (unmeasured).")

add("tendsto_round_nhdsGE_pure",
    "The four round lemmas `tendsto_round_nhdsGE_pure`, `tendsto_round_nhdsLT_pure_half_ceil`, `continuousAt_round` and `continuousOn_round` each repeat `[IsStrictOrderedRing α] [OrderClosedTopology α] [ContinuousAdd α]`, and they are wedged between `continuousAt_fract` and `tendsto_fract_left'`, just before a `variable [IsStrictOrderedRing α]` line.",
    "Move the four round lemmas after the `variable [IsStrictOrderedRing α]` line (e.g. after the fract lemmas) into a `section round` with `variable [OrderClosedTopology α] [ContinuousAdd α]`, and drop the repeated binders from their signatures.",
    "advisory",
    "lean_verify_edit replacing lines 205-238 of Mathlib/Topology/Algebra/Order/Floor.lean with `variable [IsStrictOrderedRing α]`, `section round`, `variable [OrderClosedTopology α] [ContinuousAdd α]` and the four lemmas without those binders: outcome `compiled`, no errors, no warnings.")

add("tendsto_ceil_right_pure_floor_add_one",
    "The PR reorganises the `OrderClosedTopology` section so that `tendsto_floor_right_pure_floor` no longer needs `omit [IsStrictOrderedRing α] in` (it now precedes `variable [IsStrictOrderedRing α]`), but leaves `omit [IsStrictOrderedRing α] in` on `tendsto_ceil_right_pure_floor_add_one`, which also does not need the assumption.",
    "Move `tendsto_ceil_right_pure_floor_add_one` up next to `tendsto_floor_right_pure_floor`, before `variable [IsStrictOrderedRing α]`, and delete its `omit [IsStrictOrderedRing α] in`.",
    "advisory",
    "lean_verify_edit replacing lines 111-156 of Mathlib/Topology/Algebra/Order/Floor.lean with `tendsto_ceil_right_pure_floor_add_one` placed before `variable [IsStrictOrderedRing α]` and the `omit` removed: outcome `compiled`, no errors, no warnings.")

add("continuousOn_floor",
    "Now that the codomain is `ℤ` there is no coercion left, so the restated `continuousOn_floor` (and `continuousOn_ceil`) spell the function as the eta-expanded `(fun x => floor x : α → ℤ)` / `(fun x => ceil x : α → ℤ)`, unlike the new lemmas in the same PR that write `(floor : α → ℤ)`.",
    "Write the statements as `ContinuousOn (floor : α → ℤ) (Ico n (n + 1) : Set α)` and `ContinuousOn (ceil : α → ℤ) (Ioc (n - 1) n : Set α)`.",
    "advisory",
    "lean_verify_edit replacing lines 88-94 of Mathlib/Topology/Algebra/Order/Floor.lean with the eta-reduced statements (proofs unchanged): outcome `compiled`, no errors, no warnings; the call sites `continuousAt_floor`, `continuousAt_ceil`, `continuousOn_fract` still compile.")

add("Int.floor_one_add",
    "The PR adds `Int.ceil_one_add` (`⌈1 + a⌉ = 1 + ⌈a⌉`, `@[simp]`) and `Int.fract_one_add` already exists, but there is no `Int.floor_one_add`, so `simp` cannot simplify `⌊1 + a⌋` while it now simplifies `⌈1 + a⌉`.",
    "Add `@[simp] theorem floor_one_add (a : R) : ⌊1 + a⌋ = 1 + ⌊a⌋ := mod_cast floor_natCast_add 1 a` next to `floor_natCast_add` in `Mathlib/Algebra/Order/Floor/Ring.lean`.",
    "advisory",
    "declaration_search: `Int.floor_one_add` absent at base and in the PR; `Int.fract_one_add` exists (Floor/Ring.lean:360). lean_verify_edit inserting `example (a : R) : ⌊1 + a⌋ = 1 + ⌊a⌋ := by simp` after line 225: `simp` made no progress. Inserting the proposed lemma: outcome `compiled`.")

add("round_eq'",
    "In `round_eq'` the first `split_ifs` branch spends six lines, including proving `fract x < 1` from `fract x ≤ 2 * fract x < 1` via `lt_of_le_of_lt` and `le_mul_of_one_le_left`, though this is just `fract_lt_one x`.",
    "Replace the first branch with `· rw [Int.floor_eq_zero_iff.mpr, Int.floor_eq_zero_iff.mpr] <;> simp [h, fract_lt_one]`.",
    "advisory",
    "lean_verify_edit of `round_eq'` with that branch (rest unchanged): outcome `compiled`, no errors, no warnings. An intermediate variant `· simpa using fract_lt_one x` for the third subgoal also compiled.")

add("continuousAt_round",
    "`continuousAt_round` goes through `continuousAt_iff_continuous_left'_right'`, which forces a detour (`.mono_left` with `gcongr; apply Ioi_subset_Ici_self`, and `pure_le_nhds_iff`) to use the `𝓝[≥]` lemma on `𝓝[>]`.",
    "Split `𝓝 x` as `𝓝[<] x ⊔ 𝓝[≥] x` instead: `rw [ContinuousAt, ← nhdsLT_sup_nhdsGE, tendsto_sup]; refine ⟨?_, (tendsto_round_nhdsGE_pure x).mono_right (pure_le_nhds _)⟩; rw [round_eq_half_ceil_two_mul hx]; exact (tendsto_round_nhdsLT_pure_half_ceil x).mono_right (pure_le_nhds _)`.",
    "advisory",
    "declaration_search: `nhdsLT_sup_nhdsGE` exists (Topology/Order/LeftRight.lean:114). lean_verify_edit of `continuousAt_round` with that proof: outcome `compiled`, no errors, no warnings.")

add("continuousAt_ceil",
    "`continuousAt_ceil` takes the hypothesis as `x ≠ ⌊x⌋`, a floor-based condition, and its proof has to convert it (`fun h ↦ hx <| by rw [h, floor_intCast]`); the natural hypothesis for ceil is `x ≠ ⌈x⌉`.",
    "State it as `theorem continuousAt_ceil {x : α} (hx : x ≠ ⌈x⌉) : ContinuousAt ceil x` with proof `(continuousOn_ceil ⌈x⌉).continuousAt <| Ioc_mem_nhds (sub_lt_iff_lt_add.mpr <| ceil_lt_add_one _) <| (le_ceil x).lt_of_ne hx`.",
    "advisory",
    "lean_verify_edit replacing lines 117-126 with this statement and proof (and the unchanged `continuousOn_ceil_compl_range`, whose `simp_all [eq_comm]` still closes the goal): outcome `compiled`, no errors, no warnings.")

add("Int.two_mul_fract_eq_one_iff_exists_int",
    "In `two_mul_fract_eq_one_iff_exists_int`, `refine ⟨fun hx ↦ ⟨⌊x⌋, hx⟩, ?_⟩` leaves a `∀`-goal that the next line destructures with `rintro ⟨n, hn⟩`.",
    "Bind the reverse direction in the refine: `refine ⟨fun hx ↦ ⟨⌊x⌋, hx⟩, fun ⟨n, hn⟩ ↦ ?_⟩` and delete the `rintro` line.",
    "advisory",
    "lean_verify_edit of `Int.two_mul_fract_eq_one_iff_exists_int` with that change: outcome `compiled`, no errors, no warnings.")

add("tendsto_round_nhdsLT_pure_half_ceil",
    "`tendsto_round_nhdsGE_pure` and `tendsto_round_nhdsLT_pure_half_ceil` each re-prove inside the proof the same general fact, which has nothing to do with `round`: `Tendsto (2 * ·) (𝓝[≥] x) (𝓝[≥] (2 * x))` and its `𝓝[<]` twin, as four-line `have`s that differ only in `add_le_add`/`add_lt_add`.",
    "Extract the two facts as lemmas stated without `FloorRing`, e.g. `tendsto_two_mul_nhdsGE` and `tendsto_two_mul_nhdsLT`, in a section that does not carry `FloorRing` or in a general ordered-topology file, and use them in both round lemmas.",
    "advisory",
    "lean_verify_edit replacing lines 205-223 with two extracted lemmas and the two round lemmas using them: outcome `compiled`, no errors, no warnings (in that test the lemmas needed `omit [FloorRing α] in` because they sat in the FloorRing section, which is why I ask for a section without it).")

add("Mathlib/Topology/Algebra/Order/Floor.lean",
    "The module docstring still describes the file as 'Topological facts about `Int.floor`, `Int.ceil` and `Int.fract`'. It does not mention the `round` continuity results this PR adds (`continuousAt_round`, `continuousOn_round`) or the new `continuousAt_floor`/`continuousAt_ceil`. Its entry for the restated `continuousOn_ceil` gives the interval as `Ioc n (n + 1)`, but the statement is `Ioc (n - 1) n`.",
    "Update the module docstring: add `round` to the title and main-declarations list (`continuousAt_round`, `continuousOn_round`, `continuousAt_floor`, `continuousAt_ceil`), and correct the `continuousOn_ceil` entry to `Ioc (n - 1) n`.",
    "advisory",
    "file_read of target/Mathlib/Topology/Algebra/Order/Floor.lean lines 13-28 (docstring) versus line 92-94 (`continuousOn_ceil (n : ℤ) : ContinuousOn ... (Ioc (n - 1) n ...)`).")

add("round_two_inv",
    "The PR rewrites the proofs of `round_two_inv` and `round_neg_two_inv` from short squeezed `simp only [round_eq, ...]` calls to `norm_num [round_eq_iff]`, though the old proofs still work (`round_eq` keeps its statement). The rewrite is incidental to the PR and swaps a squeezed `simp only` for heavier automation.",
    "Keep the original proofs: `simp only [round_eq, ← one_div, add_halves, floor_one]` for `round_two_inv` and `simp only [round_eq, ← one_div, neg_add_cancel, floor_zero]` for `round_neg_two_inv`.",
    "advisory",
    "lean_verify_edit replacing lines 180-184 of Mathlib/Algebra/Order/Round.lean with the pre-PR proofs: outcome `compiled`, no errors, no warnings.")

add("continuousOn_floor_compl_range",
    "The name `continuousOn_floor_compl_range` omits the function whose range is taken, though the statement fixes it to `Int.cast` (`(range Int.cast)ᶜ`). Library names with a concrete function spell it out: `isOpen_compl_range_intCast`, `compl_range_inl`, `compl_range_some`.",
    "Rename to `continuousOn_floor_compl_range_intCast`, and likewise `continuousOn_ceil_compl_range` to `continuousOn_ceil_compl_range_intCast`.",
    "advisory",
    "content_search over target/Mathlib for `compl_range` declaration names: `isOpen_compl_range_intCast : IsOpen (Set.range ((↑) : ℤ → ℂ))ᶜ`, `compl_range_inl`, `compl_range_inr`, `compl_range_some`, `compl_range_coe`; only lemmas about a variable `range m` stop at `compl_range`. naming_norm: `subject_unresolved`.")

add("round_eq'",
    "The docstring of the public lemma `round_eq'` carries a design TODO ('TODO: decide if we want to use this as a definition. It may be slightly faster over `ℚ`.'), which would be rendered in the API documentation of the lemma.",
    "Move the TODO out of the docstring into a `-- TODO` comment above the lemma (or the module docstring's TODO section), leaving the docstring to describe the statement.",
    "advisory",
    "Read at target/Mathlib/Algebra/Order/Round.lean lines 48-50.")

add("Mathlib/Topology/Algebra/Order/Floor.lean",
    "The PR, titled as a review of the `round` API, also carries a separable floor/ceil continuity change: `continuousOn_floor` and `continuousOn_ceil` are restated with codomain `ℤ` instead of `α` (a breaking change for users), and `continuousAt_floor`, `continuousAt_ceil` and `continuousOn_{floor,ceil}_compl_range` are added. None of this is used by the round lemmas: `continuousAt_round` depends only on `tendsto_floor_*_pure*`.",
    "Split the floor/ceil continuity changes (the `continuousOn_floor`/`continuousOn_ceil` restatement, the new `continuousAt_floor`/`continuousAt_ceil`/`*_compl_range` lemmas and the `continuousOn_fract`/`continuousAt_fract` proof changes) into their own PR, or at least call out the `continuousOn_floor`/`continuousOn_ceil` statement change in the PR description.",
    "advisory",
    "Dependency read from the diff and model.md relations: `continuousAt_round -> round_eq_half_ceil_two_mul, tendsto_round_nhdsGE_pure, tendsto_round_nhdsLT_pure_half_ceil` only; `continuousAt_floor/ceil` are used only by `continuousOn_*_compl_range` and `continuousAt_fract`. content_search shows no other users of `continuousOn_floor`/`continuousOn_ceil` in the tree.")

json.dump(F, open(out, "w"), ensure_ascii=False, indent=1)
print(len(F))
