import json, sys
d = sys.argv[1]
notes = """Review of PR #33421 (round API, floor/ceil/round continuity). I checked edits with lean_verify_edit wherever I propose one.

- Downstream import additions (AddConstMap/Basic, Archimedean/Basic, ToIntervalMod, ApproximateUnit, Complex/Arctan, AkraBazzi/GrowsPolynomially, GroupTheory/Archimedean, IntervalIntegral/Basic, IntervalIntegral/DerivIntegrable, Liouville/Basic, AtTopBot/Archimedean, AddCircle/Defs). These are private imports of Mathlib.Algebra.Order.Interval.Set.Group or Mathlib.Algebra.Order.Group.Basic. They make up for Round.lean no longer re-exporting Interval.Set.Group. They are minimal and private, so nothing to ask.
- import in Round.lean (public import -> import of Interval.Set.Group). Checked whether Round.lean still needs it: with the line deleted the file compiles cleanly, because the only former user (add_mem_Ico_iff_left in round_eq_zero_iff) is gone. Finding: delete the import instead of making it private.
- public import of Mathlib.Algebra.Order.Round in Topology/Algebra/Order/Floor.lean. The round lemmas need it, and Round only imports Floor.Ring, so it is light. Nothing to ask.
- Int.ceil_intCast_add / ceil_natCast_add / ceil_one_add / ceil_ofNat_add. Duplication: declaration_search finds none of them at base. The statements mirror floor_intCast_add / floor_natCast_add / floor_ofNat_add, and fract_*_add exists too. The names follow those siblings and the @[simp] attributes match. The mod_cast proofs are fine. API completeness: the floor side has no floor_one_add (absent at base and in the PR), while fract_one_add exists and ceil_one_add is now added. Finding: add floor_one_add (verified to compile).
- Int.two_mul_fract_eq_one_iff_exists_int. I found no existing equivalent (no fract = 1/2 lemma). It works in any linear ordered floor ring, which is as general as it can be. The proof is short. The name is descriptive and placed in the LinearOrderedRing section. Nothing to ask.
- round_eq'. The proof is long but follows the two cases of the definition, and I did not find a clearly shorter canonical proof. The primed name is acceptable as the ring version of round_eq. The docstring carries a TODO about changing the definition, which is a note for developers and does not describe the lemma. Finding: move the TODO into a comment.
- round_eq_half_ceil_two_mul. The docstring is accurate. The hypothesis is needed, because at half-integers round x = ceil x while ceil(2x)/2 = floor x. The name is acceptable. Nothing to ask.
- round_eq, round_eq_iff, round_two_inv, round_neg_two_inv, round_eq_zero_iff. The new proofs go through round_eq' and round_eq_iff and are shorter than the old ones. round_eq_iff matches the Ico/1/2 form of round_eq_zero_iff. The simp attributes are kept. Nothing to ask.
- continuousOn_floor / continuousOn_ceil (now Z-valued, IsStrictOrderedRing dropped). Generalizing to Z-valued with the weaker assumptions is good. The lambda `fun x => floor x` only existed to insert the cast to alpha. With codomain Z it is just `floor`, as in the new continuousOn_floor_compl_range. Findings (one each): eta-reduce; verified to compile, including the downstream uses in the file. The module docstring entry for continuousOn_ceil is wrong; covered by the module-doc finding.
- Section/variable restructuring (section Ring ... end Ring, variable [OrderClosedTopology α] then variable [IsStrictOrderedRing α], omit removed). This is an improvement. The same treatment could reach the remaining `omit` on tendsto_ceil_right_pure_floor_add_one, but that is pre-existing, so I do not ask.
- continuousAt_floor / continuousOn_floor_compl_range. The statements are natural, the hypothesis matches continuousAt_fract, fun_prop is tagged and the proofs are short. Nothing to ask.
- continuousAt_ceil. It has no @[fun_prop], unlike its sibling continuousAt_floor (verified that adding it compiles). Its hypothesis is phrased with the floor (`x ≠ ⌊x⌋`), which forces a detour in the proof. `x ≠ ⌈x⌉` gives the one-line `(le_ceil x).lt_of_ne hx`, and continuousOn_ceil_compl_range still compiles unchanged. Two findings.
- continuousOn_ceil_compl_range. Fine. Nothing to ask.
- continuousOn_fract / continuousAt_fract. The proofs were adapted to the Z-valued floor via continuous_of_discreteTopology. They are fine. Nothing to ask.
- tendsto_round_nhdsGE_pure / tendsto_round_nhdsLT_pure_half_ceil. The names use the current nhdsGE/nhdsLT convention (cf. tendsto_inv_nhdsGT), so nothing to ask on naming. Golf: the shared `have` can be written with ContinuousWithinAt.tendsto_nhdsWithin (it compiles), but that saves only a line, so I do not ask. A simpa version uniform with the GE lemma did not compile. Placement: these four round lemmas repeat [IsStrictOrderedRing α] [OrderClosedTopology α] [ContinuousAdd α] right before `variable [IsStrictOrderedRing α]`. Finding: move them into a variable block (verified).
- continuousAt_round / continuousOn_round. The statements are correct and the hypothesis is necessary. They have no @[fun_prop], unlike the floor/ceil continuousAt/continuousOn lemmas added in this PR. Finding (verified to compile).
- ContinuousOn.comp_fract''. Only enclosed in the new section. Nothing to ask.
- Module docstring of Topology/Algebra/Order/Floor.lean. It is not updated for the new round results or the continuousAt lemmas, and its continuousOn_ceil entry states the wrong interval. Finding."""

F = []
def f(path, line, claim, fix, sev="advisory"):
    F.append({"path": path, "line_start": line, "claim": claim, "suggested_fix": fix, "severity": sev})

R = "Mathlib/Algebra/Order/Round.lean"
T = "Mathlib/Topology/Algebra/Order/Floor.lean"
FR = "Mathlib/Algebra/Order/Floor/Ring.lean"

f(R, 9,
  "Round.lean no longer uses `Mathlib.Algebra.Order.Interval.Set.Group`. The PR turns it into a private `import`, but its only user (`add_mem_Ico_iff_left` in the old `round_eq_zero_iff` proof) is gone, and the file compiles with the import deleted.",
  "Delete `import Mathlib.Algebra.Order.Interval.Set.Group` from Mathlib/Algebra/Order/Round.lean instead of demoting it to a private import. The downstream files keep the explicit imports they now add.")
f(R, 48,
  "The docstring of `round_eq'` contains a development TODO (\"decide if we want to use this as a definition...\"). That is a note for maintainers, not documentation of the lemma, and it will show up in the API docs.",
  "Keep the docstring as `/-- Formula for `round` in terms of `Int.floor`, a version that works over any ring. -/` and move the TODO into a `-- TODO: ...` comment above the declaration (or into the module docstring's TODO section).")
f(T, 88,
  "`continuousOn_floor` is now stated for the `ℤ`-valued floor but keeps the lambda `fun x => floor x : α → ℤ`. The lambda only existed to insert the cast to `α`. With codomain `ℤ` it is just an eta-expanded `floor`, which is inconsistent with the new `continuousOn_floor_compl_range : ContinuousOn (floor : α → ℤ) ...`.",
  "State it as `theorem continuousOn_floor (n : ℤ) : ContinuousOn (floor : α → ℤ) (Ico n (n + 1) : Set α)`, keeping the same proof (verified to compile together with its uses in the file).")
f(T, 92,
  "`continuousOn_ceil` is now stated for the `ℤ`-valued ceil but keeps the eta-expanded `fun x => ceil x : α → ℤ`, which was only needed for the old cast to `α`.",
  "State it as `theorem continuousOn_ceil (n : ℤ) : ContinuousOn (ceil : α → ℤ) (Ioc (n - 1) n : Set α)`, keeping the same proof (verified to compile).")
f(T, 117,
  "`continuousAt_ceil` has no `@[fun_prop]` attribute, though its sibling `continuousAt_floor` and `continuousOn_ceil_compl_range`, both added in this PR, are tagged. `fun_prop` therefore cannot use it.",
  "Add `@[fun_prop]` to `continuousAt_ceil` (verified to compile).")
f(T, 117,
  "`continuousAt_ceil` states its non-integrality hypothesis via the floor (`hx : x ≠ ⌊x⌋`). This is unnatural for a ceil lemma and forces the detour `fun h ↦ hx <| by rw [h, floor_intCast]` in the proof.",
  "State the hypothesis as `(hx : x ≠ ⌈x⌉)` and close the proof with `(le_ceil x).lt_of_ne hx`: `(continuousOn_ceil ⌈x⌉).continuousAt <| Ioc_mem_nhds (sub_lt_iff_lt_add.mpr <| ceil_lt_add_one _) <| (le_ceil x).lt_of_ne hx`. `continuousOn_ceil_compl_range` still compiles unchanged (verified).")
f(T, 205,
  "`tendsto_round_nhdsGE_pure`, `tendsto_round_nhdsLT_pure_half_ceil`, `continuousAt_round` and `continuousOn_round` each repeat the binders `[IsStrictOrderedRing α] [OrderClosedTopology α] [ContinuousAdd α]`. They sit right before `variable [IsStrictOrderedRing α]`, and this PR restructured the file's variable blocks precisely to avoid such repetition.",
  "Move the four round lemmas below `variable [IsStrictOrderedRing α]`, inside a `section` with `variable [OrderClosedTopology α] [ContinuousAdd α]`, and drop the per-lemma instance binders (verified to compile).")
f(T, 225,
  "`continuousAt_round` and `continuousOn_round` have no `@[fun_prop]`, although this PR tags the analogous `continuousAt_floor`, `continuousOn_floor_compl_range` and `continuousOn_ceil_compl_range`.",
  "Add `@[fun_prop]` to `continuousAt_round` and `continuousOn_round` (verified to compile).")
f(T, 13,
  "The module docstring of Topology/Algebra/Order/Floor.lean is out of date after this PR. The title and 'Main declarations' still cover only `floor`/`ceil`/`fract` and do not mention the new `continuousAt_floor`/`continuousAt_ceil`/`continuousAt_round`/`continuousOn_round`. The `continuousOn_ceil` entry gives the interval `Ioc n (n + 1)`, but the statement is about `Ioc (n - 1) n`.",
  "Update the module docstring: add `round` to the title, list `continuousAt_floor`, `continuousAt_ceil`, `continuousAt_round` and `continuousOn_round` under Main declarations, and correct the `continuousOn_ceil` entry to `Ioc (n - 1) n`.")
f(FR, 656,
  "The PR completes the left-addition API for `ceil` with `Int.ceil_one_add`, but the floor side still lacks `Int.floor_one_add`. `floor_intCast_add`, `floor_natCast_add`, `floor_ofNat_add` and `fract_one_add` all exist, so `floor` is now the only one of the three without its `one_add` lemma.",
  "Add `@[simp] theorem floor_one_add (a : R) : ⌊1 + a⌋ = 1 + ⌊a⌋ := mod_cast floor_natCast_add 1 a` next to `floor_natCast_add` (verified to compile).")

out = {"notes": notes, "findings": F}
json.dump(out, open(d + "/submission.json", "w"), ensure_ascii=False, indent=1)
