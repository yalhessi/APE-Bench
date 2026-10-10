import json, sys
D = sys.argv[1]
SET_ALL = ("lean_verify_edit on Mathlib/Algebra/Group/Pointwise/Set/Basic.lean, line mode 70-840, one combined edit "
           "applying every Set/Basic style change filed in this review (where-syntax for Set.one, mulOneClass, "
           "singletonMonoidHom, monoid, commMonoid, divisionMonoid, divisionCommMonoid; singletonOneHom split; "
           "divisionMonoid to_additive on one line; divisionCommMonoid header on one line): outcome `compiled`, no errors, no warnings.")
FIN_ALL = ("lean_verify_edit on Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean, line mode 768-1022, removing all four remaining "
           "`noncomputable` (coeMonoidHom, commMonoid, divisionMonoid, divisionCommMonoid): outcome `compiled`, no errors; the same "
           "span plus the trailing-space fixes and the one-line divisionCommMonoid header also `compiled`. Controls in the same file: "
           "`def ctrlUse : Finset ℕ →* Set ℕ := Finset.coeMonoidHom` fails with \"failed to compile definition, consider marking it as "
           "'noncomputable' because it depends on 'Finset.coeMonoidHom'\", and a `Classical.choice` def fails, so the tool does run "
           "the code generator's computability check.")
F = []
def add(target, claim, change, sev, ev):
    F.append({"target": target, "claim": claim, "requested_change": change, "severity": sev, "evidence": ev})

add("Finset.mulAction",
    "The PR removes the nightly-2025-04-07 `#adaptation_note` from `Finset.monoid` but leaves its identical twin above `Finset.mulAction` in `Mathlib/Algebra/Group/Action/Pointwise/Finset.lean` (lines 76-81), which says the definition \"now needs to be marked as noncomputable because of its dependence on `Set.monoid`\". After this PR `Set.monoid` is computable, so that note is false, and the `protected noncomputable def mulAction` it justifies is no longer needed.",
    "In `Mathlib/Algebra/Group/Action/Pointwise/Finset.lean`, delete the `#adaptation_note /-- nightly-2025-04-07 ... -/` block before `Finset.mulAction` and change `protected noncomputable def mulAction [DecidableEq α] [Monoid α] [MulAction α β] :` to `protected def mulAction [DecidableEq α] [Monoid α] [MulAction α β] :`.",
    "blocking",
    "content_search for `7824` over all of Mathlib finds exactly one remaining copy of the note, at Action/Pointwise/Finset.lean:76-81 above `Finset.mulAction`. zulip_search: Kim Morrison (2025-04-09, #23806 thread) \"I've added adaptation notes to the two `noncomputable`s that were flagged ... in review\" -- these are the two, and the PR removes only one. lean_verify_edit on that file, lines 76-87 replaced by the docstring, attribute and `protected def mulAction ...` header with the note and `noncomputable` removed: outcome `compiled`, no errors. A `Classical.choice` control def in the same file fails with \"not supported by code generator\", so computability is checked there.")

add("Finset.commMonoid",
    "The PR's title is about the Set/Finset monoid instances, but in the changed file `Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean` it removes `noncomputable` only from `Finset.monoid`; `Finset.commMonoid` (line 939) is still `protected noncomputable def`, although it is built the same way (`coe_injective.commMonoid _ coe_one coe_mul coe_pow`) and compiles without the modifier now that `Set.commMonoid` is computable.",
    "Change `protected noncomputable def commMonoid : CommMonoid (Finset α) :=` to `protected def commMonoid : CommMonoid (Finset α) :=`.",
    "advisory",
    "lean_verify_edit, line 939 alone replaced by `protected def commMonoid : CommMonoid (Finset α) :=`: outcome `compiled`, no errors, no warnings. " + FIN_ALL)

add("Finset.divisionMonoid",
    "`Finset.divisionMonoid` (Finset/Basic.lean line 964) is still `protected noncomputable def` while its sibling `Finset.monoid` loses the modifier in this PR; the modifier is no longer needed now that `Set.divisionMonoid` is computable.",
    "Change `protected noncomputable def divisionMonoid : DivisionMonoid (Finset α) :=` to `protected def divisionMonoid : DivisionMonoid (Finset α) :=`.",
    "advisory",
    FIN_ALL)

add("Finset.divisionCommMonoid",
    "`Finset.divisionCommMonoid` (Finset/Basic.lean lines 1020-1021) is still `protected noncomputable def`, unlike `Set.divisionCommMonoid`, which this PR makes computable; and once the modifier goes, the signature fits on one line (90 characters) and should not be broken.",
    "Replace the two-line header `protected noncomputable def divisionCommMonoid [DivisionCommMonoid α] :` / `DivisionCommMonoid (Finset α) :=` with the single line `protected def divisionCommMonoid [DivisionCommMonoid α] : DivisionCommMonoid (Finset α) :=`.",
    "advisory",
    FIN_ALL + " Joined header line measured at 90 characters.")

add("Finset.coeMonoidHom",
    "`Finset.coeMonoidHom` (Finset/Basic.lean line 770) is still `noncomputable def`, but it compiles without the modifier once `Set.one`/`Set.monoid` are computable, so it is left over from the same nightly-2025-04-07 churn this PR cleans up.",
    "Change `noncomputable def coeMonoidHom : Finset α →* Set α where` to `def coeMonoidHom : Finset α →* Set α where`.",
    "advisory",
    FIN_ALL)

add("Set.divisionCommMonoid",
    "The signature of `Set.divisionCommMonoid` was split across two lines only because `noncomputable` pushed it to 101 characters; with the modifier removed by this PR it is 87 characters and fits on one line, so the break is no longer warranted.",
    "Write the header on one line: `protected def divisionCommMonoid [DivisionCommMonoid α] : DivisionCommMonoid (Set α) :=`.",
    "advisory",
    "Measured: with `noncomputable` the one-line header is 101 characters, without it 87. " + SET_ALL)

add("Set.mulAction",
    "`Set.mulAction` in `Mathlib/Algebra/Group/Action/Pointwise/Set/Basic.lean` (line 173) is still `protected noncomputable def`; it is the Set counterpart of `Finset.mulAction`, whose adaptation note attributes the modifier to `Set.monoid`, and it compiles without it after this PR.",
    "Change `protected noncomputable def mulAction [Monoid α] [MulAction α β] : MulAction (Set α) (Set β) where` to `protected def mulAction [Monoid α] [MulAction α β] : MulAction (Set α) (Set β) where` (here or in an immediate follow-up).",
    "advisory",
    "lean_verify_edit on Mathlib/Algebra/Group/Action/Pointwise/Set/Basic.lean, line 173 replaced without `noncomputable`: outcome `compiled`, no errors.")

add("Set.hasDistribNeg",
    "`Set.hasDistribNeg` in `Mathlib/Algebra/Ring/Pointwise/Set.lean` (line 30) is still `protected noncomputable def`; it is built from `Set.involutiveNeg`, which this PR makes computable (to_additive of `Set.involutiveInv`), and it compiles without the modifier.",
    "Change `protected noncomputable def hasDistribNeg [Mul α] [HasDistribNeg α] : HasDistribNeg (Set α) where` to `protected def hasDistribNeg [Mul α] [HasDistribNeg α] : HasDistribNeg (Set α) where`.",
    "advisory",
    "lean_verify_edit on Mathlib/Algebra/Ring/Pointwise/Set.lean, line 30 without `noncomputable`: outcome `compiled`, no errors.")

add("Finset.distribNeg",
    "`Finset.distribNeg` in `Mathlib/Algebra/Ring/Pointwise/Finset.lean` (line 29) is still `protected noncomputable def`, although it compiles without the modifier after this PR.",
    "Change `protected noncomputable def distribNeg [DecidableEq α] [Mul α] [HasDistribNeg α] :` to `protected def distribNeg [DecidableEq α] [Mul α] [HasDistribNeg α] :`.",
    "advisory",
    "lean_verify_edit on Mathlib/Algebra/Ring/Pointwise/Finset.lean, line 29 without `noncomputable`: outcome `compiled`, no errors.")

add("Mathlib/Data/Set/Semiring.lean",
    "The `SetSemiring` instances built from the pointwise Set structures this PR makes computable (`NonAssocSemiring` from `Set.mulOneClass`, `IdemSemiring`, `IdemCommSemiring`, `CommMonoid`, `IsOrderedRing`, and `SetSemiring.imageHom`, lines 174-205) are still marked `noncomputable`, and all of them compile without it.",
    "Remove `noncomputable` from the five instances at lines 174, 181, 189, 193 and 200 and from `def imageHom` at line 205 of `Mathlib/Data/Set/Semiring.lean`.",
    "advisory",
    "lean_verify_edit on Mathlib/Data/Set/Semiring.lean, lines 174-205 with every `noncomputable instance`/`noncomputable def` turned into `instance`/`def`: outcome `compiled`, no errors.")

add("Filter.mulDistribMulActionFilter",
    "`Filter.mulDistribMulActionFilter` in `Mathlib/Order/Filter/Pointwise.lean` (line 1053), a `MulDistribMulAction α (Set β)` that needs the `Set.monoid` structure, is still `protected noncomputable def`, though it compiles without the modifier after this PR.",
    "Change `protected noncomputable def mulDistribMulActionFilter` to `protected def mulDistribMulActionFilter`.",
    "advisory",
    "lean_verify_edit on Mathlib/Order/Filter/Pointwise.lean, line 1053 without `noncomputable`: outcome `compiled`, no errors.")

add("convexAddSubmonoid",
    "`convexAddSubmonoid : AddSubmonoid (Set E)` in `Mathlib/Analysis/Convex/Basic.lean` (line 198), which depends on the pointwise `AddZeroClass (Set E)` this PR makes computable, is still `noncomputable def`, though it compiles without it.",
    "Change `noncomputable def convexAddSubmonoid : AddSubmonoid (Set E) where` to `def convexAddSubmonoid : AddSubmonoid (Set E) where`.",
    "advisory",
    "lean_verify_edit on Mathlib/Analysis/Convex/Basic.lean, line 198 without `noncomputable`: outcome `compiled`, no errors.")

add("Finset.monoid",
    "The additive docstring of `Finset.monoid` ends in a trailing space inside the string: `@[to_additive \"`Finset α` is an `AddMonoid` under pointwise operations if `α` is. \"]` (line 803); `Finset.commMonoid` (line 938) has the same `is. \"`.",
    "Drop the trailing space: `@[to_additive \"`Finset α` is an `AddMonoid` under pointwise operations if `α` is.\"]`, and the same in `Finset.commMonoid`'s `to_additive` string.",
    "advisory",
    "Lines 803 and 938 read `... if `α` is. \"]` in file_read. " + FIN_ALL)

add("Set.one",
    "`Set.one` builds its `One (Set α)` structure with the anonymous constructor `⟨{1}⟩`, on a line of its own although the whole declaration fits on one line (40 characters).",
    "Write it with `where` on one line: `protected def one : One (Set α) where one := {1}` (as `SetSemiring`'s `instance : One (SetSemiring α) where one := (1 : Set α).up` does).",
    "advisory",
    SET_ALL)

add("Set.singletonOneHom",
    "`Set.singletonOneHom` packs its two `where` fields on one line (`toFun := singleton; map_one' := singleton_one`), while its sibling `Set.singletonMulHom`, touched in the same PR, puts one field per line.",
    "Put one field per line:\n```\ndef singletonOneHom : OneHom α (Set α) where\n  toFun := singleton\n  map_one' := singleton_one\n```",
    "advisory",
    SET_ALL)

add("Set.mulOneClass",
    "`Set.mulOneClass` is written as a `{ Set.one, Set.mul with ... }` structure instance after `:=` rather than with `where`.",
    "Rewrite as\n```\nprotected def mulOneClass : MulOneClass (Set α) where\n  __ := Set.one\n  __ := Set.mul\n  mul_one := image2_right_identity mul_one\n  one_mul := image2_left_identity one_mul\n```",
    "advisory",
    SET_ALL)

add("Set.divisionMonoid",
    "`Set.divisionMonoid` is written as a `{ Set.monoid, Set.involutiveInv, Set.div, @Set.ZPow α _ _ _ with ... }` structure instance with `fun s t => by` fields rather than with `where`.",
    "Rewrite with `where`: `protected def divisionMonoid : DivisionMonoid (Set α) where`, then `__ := Set.monoid`, `__ := Set.involutiveInv`, `__ := Set.div`, `__ := @Set.ZPow α _ _ _`, and the fields as `mul_inv_rev s t := by ...`, `inv_eq_of_mul s t h := by ...`, `div_eq_mul_inv s t := by ...`, each one level less indented.",
    "advisory",
    SET_ALL)

add("Set.divisionMonoid",
    "The `to_additive` attribute of `Set.divisionMonoid` is broken over two lines although `@[to_additive \"`Set α` is a subtraction monoid under pointwise operations if `α` is.\"]` fits on one line (86 characters).",
    "Put the attribute on one line: `@[to_additive \"`Set α` is a subtraction monoid under pointwise operations if `α` is.\"]`.",
    "advisory",
    "Measured at 86 characters. " + SET_ALL)

add("Set.monoid",
    "`Set.monoid` is written as `{ Set.semigroup, Set.mulOneClass, @Set.NPow α _ _ with }` after `:=` rather than with `where`.",
    "Rewrite as `protected def monoid : Monoid (Set α) where` followed by `__ := Set.semigroup`, `__ := Set.mulOneClass`, `__ := @Set.NPow α _ _`, one per line.",
    "advisory",
    SET_ALL)

add("Set.commMonoid",
    "`Set.commMonoid` is written as `{ Set.monoid, Set.commSemigroup with }` after `:=` rather than with `where`.",
    "Rewrite as `protected def commMonoid [CommMonoid α] : CommMonoid (Set α) where` followed by `__ := Set.monoid` and `__ := Set.commSemigroup`, one per line.",
    "advisory",
    SET_ALL)

add("Set.singletonMonoidHom",
    "`Set.singletonMonoidHom` is written as `{ singletonMulHom, singletonOneHom with }` after `:=` rather than with `where`, unlike its siblings `singletonMulHom`/`singletonOneHom`, which use `where`.",
    "Rewrite as `def singletonMonoidHom : α →* Set α where` followed by `__ := singletonMulHom` and `__ := singletonOneHom`, one per line.",
    "advisory",
    SET_ALL)

add("Set.divisionCommMonoid",
    "`Set.divisionCommMonoid` is written as `{ Set.divisionMonoid, Set.commSemigroup with }` after `:=` rather than with `where`.",
    "Rewrite as `protected def divisionCommMonoid [DivisionCommMonoid α] : DivisionCommMonoid (Set α) where` followed by `__ := Set.divisionMonoid` and `__ := Set.commSemigroup`, one per line.",
    "advisory",
    SET_ALL)


DOC_EV = ("lean_verify_edit on Set/Basic.lean, lines 70-840, with the final full stop dropped from the three singleton-hom "
          "docstrings and their to_additive strings: outcome `compiled`, no errors, no warnings.")
for name, mul, add_ in [("Set.singletonOneHom", "OneHom", "a `ZeroHom`"), ("Set.singletonMulHom", "MulHom", "an `AddHom`"),
                        ("Set.singletonMonoidHom", "MonoidHom", "an `AddMonoidHom`")]:
    art = "a"
    add(name,
        f"The docstring of `{name}`, `/-- The singleton operation as a `{mul}`. -/`, and its additive string `\"The singleton operation as {add_}.\"` are noun phrases, not sentences, but end with a full stop.",
        f"Drop the final full stop: `/-- The singleton operation as a `{mul}` -/` and `@[to_additive \"The singleton operation as {add_}\"]`.",
        "advisory", DOC_EV)

json.dump(F, open(D + "/findings.json", "w"), ensure_ascii=False, indent=1)
print(len(F))
