# Review notes: PR #26755, "chore: remove `noncomputable` from Set/Finset Monoid instances"

## What I did

I read `pr.md`, `model.md` and `diff.patch`. The PR description is not recoverable. The diff
removes `noncomputable` from ten declarations in `Pointwise/Set/Basic.lean` and from
`Finset.monoid`, and deletes the nightly-2025-04-07 `#adaptation_note` above `Finset.monoid`.

All of the following went through `./ptool`:
- `content_search` for `noncomputable` under `Algebra/Group/Pointwise`, `Algebra/Group/Action/Pointwise`,
  `Algebra/Ring/Pointwise`, `Data/Set/Semiring.lean`, `Order/Filter/Pointwise.lean` and others.
- `content_search` for `7824` over all of Mathlib, to find other copies of the adaptation note.
- A regex search over Mathlib for `noncomputable (def|instance|abbrev) ... (Set|Finset) `.
- `zulip_search` on the nightly-2025-04-07 adaptation. It found Kim Morrison in the #23806 thread:
  "I've added adaptation notes to the two `noncomputable`s that were flagged ... in review".
- `precedent_search` on the removed note. None of the hits applied.
- `lean_verify_edit` for every edit I propose, plus negative controls.

The controls show the tool runs the code generator's computability check, both in the PR's own
file and in a downstream file:
- `def … := Classical.choice ⟨0⟩` fails in `Finset/Basic.lean` and in `Action/Pointwise/Finset.lean`.
- `def ctrlUse : Finset ℕ →* Set ℕ := Finset.coeMonoidHom` fails with "depends on
  'Finset.coeMonoidHom', which is 'noncomputable'".

Declaration-mode `lean_verify_edit` keeps the original modifiers, so with it I could not remove
`noncomputable` (the first try gave a parse error). I used line mode instead.

## Object by object

- **Removed `#adaptation_note` (Finset/Basic):** correct to remove, because `Finset.monoid` is now
  computable. Its twin above `Finset.mulAction` in `Action/Pointwise/Finset.lean` is now false and
  is left behind. Filed as blocking: delete the note and the `noncomputable`. Compile verified.
- **`Finset.monoid`:** the modifier removal is fine. The `to_additive` string has a trailing
  space (`is. "`), and `Finset.commMonoid` has the same one. Filed (style).
- **Rest of Finset/Basic:** `coeMonoidHom`, `commMonoid`, `divisionMonoid` and `divisionCommMonoid`
  are still `noncomputable`. All four compile without it, in one combined edit. Filed one finding
  each. The `divisionCommMonoid` finding also asks for its 90-character header to be joined onto
  one line.
- **`Set.one`:** the modifier removal is fine. Filed a `where` rewrite of `⟨{1}⟩` onto one line
  (anonymous-constructor and line-break conventions).
- **`Set.singletonOneHom`:** the modifier removal is fine. Its fields are packed on one line, while
  the sibling `singletonMulHom` has one per line. Filed.
- **`Set.involutiveInv`:** the modifier removal is fine. Its explicit name is needed: it is
  referenced as `Set.involutiveInv` in `Set.divisionMonoid` (line 771), so the instance-naming
  convention is satisfied.
  - It is a global `instance` carrying `@[simp]`, not a scoped def like its siblings. That
    predates the PR and no convention covers it, so I did not file it.
- **`Set.singletonMulHom`:** the modifier removal is fine, and it already uses `where` with one
  field per line. Only the docstring's full stop is filed (see the conventions below).
- **`Set.mulOneClass`, `Set.monoid`, `Set.commMonoid`, `Set.divisionMonoid`, `Set.divisionCommMonoid`,
  `Set.singletonMonoidHom`:** the modifier removals are fine. The bodies use `{ … with }` rather
  than `where`. Filed one `where`/`__ :=` rewrite each, verified in one combined compile.
  - `Set.divisionMonoid`: its `to_additive` line is broken although it fits (86 characters). Filed.
  - `Set.divisionCommMonoid`: its header was split only because `noncomputable` made it 101
    characters. It is 87 now, so I filed rejoining it.
- **Downstream noncomputables:** these all depend on the structures this PR makes computable and
  all compile without the modifier, so I filed each as advisory, "here or in a follow-up":
  - `Set.mulAction`
  - `Set.hasDistribNeg`
  - `Finset.distribNeg`
  - the `SetSemiring` instances and `imageHom`, as one finding on the file
  - `Filter.mulDistribMulActionFilter`
  - `convexAddSubmonoid`
- **Search coverage:** my searches were patterns and directories. I did not enumerate every
  noncomputable in Mathlib, so there may be more of these.
- **Correctness:** the PR's own files compile with no errors and no warnings; my verified edits
  ran against them. Nothing in the diff is wrong; what it leaves undone is the issue.

## Conventions: filed and left

- **Efficient decidable or computable implementation:** no `Decidable` instance or algorithmic def
  in the PR. Not applicable.
- **`where` syntax:**
  - Filed: `Set.one`, `Set.mulOneClass`, `Set.monoid`, `Set.commMonoid`, `Set.divisionMonoid`,
    `Set.divisionCommMonoid`, `Set.singletonMonoidHom`.
  - Left, as they already use `where`: `Set.singletonMulHom` (`def singletonMulHom : α →ₙ* Set α where`)
    and `Set.involutiveInv` (`instance involutiveInv : InvolutiveInv (Set α) where`).
  - Left: `Finset.monoid`, which is a term (`coe_injective.monoid _ …`), not a structure instance.
- **def rather than instance when it may conflict:** the PR changes no instance/def status. Nothing filed.
- **`abbrev` only when needed:** no `abbrev`s. Not applicable.
- **`protected` for root-name clashes:** `Set.one`, `monoid` and the others are already `protected`
  (quoted in the diff). The `singleton*Hom` names do not clash with root names. Nothing filed.
- **Motivation in the description:** the description is not recoverable, so I cannot claim it is
  missing. Not filed.
- **Spacing:** filed the trailing space in `Finset.monoid`'s `to_additive` string, with the
  `Finset.commMonoid` one noted in the same finding. No other spacing departures in the touched
  lines.
- **Workarounds rechecked:** the PR removes one adaptation note. Filed the identical remaining one
  (`Finset.mulAction`).
- **Family consistency (attribute or modifier on some siblings):**
  - Filed the `noncomputable`s left on Finset siblings: `commMonoid`, `divisionMonoid`,
    `divisionCommMonoid`, `coeMonoidHom`.
  - Filed the Set/Finset action and distribNeg siblings.
  - Filed `singletonOneHom` against `singletonMulHom` for field layout.
- **Line breaks only past 100 characters:**
  - Filed: `Set.divisionCommMonoid` header (87), `Finset.divisionCommMonoid` header (90, in its
    finding), `Set.divisionMonoid` `to_additive` line (86), `Set.one` (40).
  - Left: `Set.divisionCommMonoid`'s `to_additive` line, which would be 120 characters joined, so
    its break is warranted.
- **One field per line:** filed `Set.singletonOneHom`.
- **Comments kept in step with the code:** the stale `Finset.mulAction` note is filed (above).
  - Unfiled: the docstrings of `Set.one` and `Set.inv` say "in locale `Pointwise`", Lean 3
    terminology, on lines this PR does not change.
  - Unfiled: `Finset.coeMonoidHom`'s additive docstring says "`set`" for `Set`; I would add it if
    that def is edited per the filed finding.
- **Precise title and description:** the title says "Monoid instances", but the PR also changes the
  `singleton*Hom` defs and `Set.involutiveInv`. That is minor, and the description is missing, so
  not filed.
- **Explicit instance names:** `Set.involutiveInv` is referenced by name (line 771). Left.
- **`__ := obj` inheritance:** covered by the `where` findings, which use `__ :=` for the parents.
- **Proof on the statement line only if both fit:** `Set.one` is filed. The other bodies are
  multi-line and correctly start on their own line.
- **`noncomputable section` against per-def `noncomputable`:** after the PR, only a few defs in
  Finset/Basic still need the modifier, and the filed findings would remove those too. No section
  is warranted. Nothing filed.
- **Benchmark low-level instance changes:** removing `noncomputable` does not change elaboration or
  instance search. Not filed.
- **Minimal changes:** the PR touches only modifiers and one note. Nothing incidental to flag. My
  style findings on unchanged body lines pull against this convention; they are advisory for
  that reason.
- **Explicit `to_additive` target names:** `@[to_additive subtractionCommMonoid …]` on
  `Set.divisionCommMonoid`. The file compiles with no warnings, so `to_additive` did not report
  the name as redundant, and the scoped attribute line references `Set.subtractionCommMonoid`.
  Left.
- **Reducible non-instances:** no instance-building abbrevs. Not applicable.
- **Noun-phrase docstrings without a full stop:**
  - Filed: `Set.singletonOneHom`, `Set.singletonMulHom` and `Set.singletonMonoidHom`. Each has a
    noun-phrase docstring and additive string ending in a full stop ("The singleton operation as a
    `OneHom`."), the same situation as the brief's example. Dropping the stops compiles.
  - Left: the monoid-structure docstrings ("`Set α` is a `Monoid` under pointwise operations if
    `α` is."), which are complete sentences, so the stop is correct. Also left: "The set `1 : Set α`
    is defined as …", also a sentence.
- **Docstrings on both `to_additive` sides:** every touched declaration has a docstring plus a
  `to_additive` string, except `Set.involutiveInv`, which has neither. That is pre-existing and
  instances are not required to have docstrings. Left.
- **`..` for trailing underscores:** `@Set.NPow α _ _` and `@Set.ZPow α _ _ _` are explicit-argument
  applications inside structure instances. `..` would change the `@`-application meaning. Left.
