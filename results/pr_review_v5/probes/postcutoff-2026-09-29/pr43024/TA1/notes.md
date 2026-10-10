# Review notes: PR #43024 (`isMulCommutative_anti` for subobjects)

## What I did

- Read `brief.md`, `pr.md`, `model.md`, `diff.patch`.
- `ptool describe`, then read `target/Mathlib/Algebra/Group/Subsemigroup/Defs.lean` (header 1-90,
  section map 90-270, changed region 270-356), `Data/SetLike/Basic.lean` 180-300 (`IsConcreteLE`,
  `mem_of_le_of_mem`), and `Algebra/Group/Semigroup.lean` 160-230 (`IsMulCommutative`).
- declaration_search on `setLike_mul_comm`, `isMulCommutative_mono`, `isMulCommutative_anti`,
  `IsConcreteLE`, `IsMulCommutative`, `isMulCommutative_iff`, `IsMulCommutative.anti/.mono/.of_le`,
  `isMulCommutative_of_le`, `Subgroup.isMulCommutative_of_le`, `Subsemigroup.isMulCommutative_of_le`.
- content_search over Mathlib for every `IsMulCommutative` declaration and use, for every use of
  `of_setLike_mul_comm` / `setLike_mul_comm`, for `.anti` / `_anti` lemma names, for `-/ ]` against
  `-/]`, and for positional (`@`) uses of the sibling lemmas.
- naming_norm (`subject_unresolved`), zulip_search, precedent_search (nothing relevant).
- lean_verify_edit: (1) rename to `isMulCommutative_anti`, with `-/]` and the conclusion joined: compiled;
  (2) `IsMulCommutative.anti` plus an additive `example`: compiled; (3) `section` and `variable` block over
  the three SetLike lemmas: compiled; (4) dropping `[IsConcreteLE S M]`: fails ("failed to synthesize
  IsConcreteLE S M"), so that hypothesis is needed.

## Object by object

### `setLike_mul_comm` (model says added; diff shows it as context)
The diff's hunk header puts it at old line 346, and declaration_search finds it at the base commit.
It is pre-existing, not changed by this PR, and I file nothing on it. It does share the repeated binder
block that finding 4 groups into a `variable`.

### `isMulCommutative_mono` (added)
- Correctness: it compiles. The statement is true and antitone in the subobject.
- Generalization: every hypothesis is used. `[Mul M] [MulMemClass S M]` give `Mul s`. `[LE S]
  [IsConcreteLE S M]` are what make `mem_of_le_of_mem` apply, and dropping `IsConcreteLE` fails to compile.
  A version with `s : S`, `t : T` of different types and `(s : Set M) ⊆ t` would be more general, but it
  gives up the `≤` form every SetLike user writes. I do not file it.
- Duplication: nothing in the base states this. No `IsMulCommutative.*` lemma, `*isMulCommutative_of_le`
  or `_anti`/`_mono` variant exists.
- Proof-golf: the term proof is already minimal. With a generic `[LE S]`, `h ha` does not typecheck, so
  `mem_of_le_of_mem` is needed. Joined, the proof is 103 characters, so the break is justified.
- Naming: filed `_mono` → `_anti` (finding 1) and the `IsMulCommutative` namespace (finding 2).
- Style: filed the `-/ ]` spacing (finding 3) and the repeated binders (finding 4).
- Documentation: the docstring says what the lemma means ("passes to smaller subobjects") rather than
  restating the type, and the `to_additive` docstring is present. Nothing to file.
- Scope: it sits next to its siblings `isMulCommutative_iff_of_setLike` and `setLike_mul_comm`, which is
  the right file. Nothing to file.

### `doc_comment in Defs.lean`
This is the new lemma's docstring, covered above. Nothing to file.

### PR as a whole
- Filed: the title names `isMulCommutative_anti`, which the diff never declares (finding 5).
- Filed: the title has no `(Area)` scope (finding 6).
- The description is not recoverable, so I cannot judge the motivation.

## Message: conventions, places filed and places left

1. Drop or weaken unneeded hypotheses. **Left**: `isMulCommutative_mono`. Every binder is used, and the
   check without `[IsConcreteLE S M]` fails with "failed to synthesize IsConcreteLE S M".
2. Name built from the declarations in the statement. **Covered by finding 1**: `isMulCommutative`
   spells `IsMulCommutative` as declared; only the `_mono`/`_anti` part is wrong.
3. Break after the colon, conclusion on its own line. **Left**: line 353 ends `[IsMulCommutative t] :`
   and line 354 is `    IsMulCommutative s :=`, which is already that form.
4. Binder kinds follow inferability. **Left**: `{s t : S}` are inferred from `(h : s ≤ t)`, `h` is
   explicit, and `[IsMulCommutative t]` is an instance.
5. Motivation for a new lemma. **Left**: its use is evident from the docstring, and the PR description is
   not recoverable, so it cannot be checked.
6. Shared arguments declared once with `variable`. **Filed**: finding 4, on `isMulCommutative_mono` and
   its two predecessors.
7. Standard spacing. **Filed**: finding 3, `-/ ]` → `-/]`. The term spacing (`fun _ ha _ hb ↦`,
   `(h : s ≤ t)`) is already standard.
8. Break only past 100 characters. **Left**: joining `IsMulCommutative s :=` onto line 353 would fit
   (96 characters), but the current layout is the form convention 3 asks for, so I do not file a join.
   The proof's break is needed (103 characters joined).
9. No new declaration when one already exists. **Left**: declaration_search and content_search found no
   existing statement of this.
10. Dot-notation namespace. **Filed**: finding 2 (`IsMulCommutative.anti`).
11. Name states the conclusion. **Left**: `isMulCommutative_…` names the conclusion, and no hypothesis
    name is spelled into it.
12. Title and description precise. **Filed**: finding 5, the title names `isMulCommutative_anti` but the
    code adds `isMulCommutative_mono`.
13. Docstring says what it means. **Left**: "Commutativity of multiplication passes to smaller
    subobjects." gives the meaning, not the type.
14. Theory namespace, not root. **Covered by finding 2.** The siblings `isMulCommutative_iff_of_setLike`
    and `setLike_mul_comm` are pre-existing at the root.
15. Title `type(Area): description`. **Filed**: finding 6.
16. Sibling and analogue naming pattern. **Filed**: finding 1. The analogues `Loopless.anti`,
    `Simple.anti`, `IsAcyclic.anti`, `CliqueFree.anti` and `Set.Subsingleton.anti` use `anti`.
17. `_mono` is the one-directional monotone implication. **Covered by finding 1**: the lemma is
    one-directional but antitone, so `_mono` is the wrong word.
18. Multiplicative/additive counterpart. **Left**: `@[to_additive]` generates `isAddCommutative_mono`,
    and the additive `example` in check (2) elaborates.
19. Hand-built instance → global instance. **Left**: not applicable. The lemma cannot be an instance
    because `h : s ≤ t` is not inferable, and the proof builds no instance by hand.
20. Apply the new lemma to existing hand proofs. **Left**: I searched every `of_setLike_mul_comm` /
    `setLike_mul_comm` use (iSup, closure, adjoin, map, comap, topologicalClosure). Each proves
    commutativity some other way (directedness, centralizers, images), and none transfers commutativity
    along an inclusion `s ≤ t` by hand.
21. Added lemma is used, tagged or intended API. **Left**: the lemma is the PR's stated API (the title).
22. Bundled function-property naming. **Left**: not applicable.
23. Class hypothesis as instance-implicit. **Left**: `[IsMulCommutative t]` already is.
24. Generator docstrings on both. **Left**: line 350 has the multiplicative docstring and line 351 the
    additive one.
25. Argument order from ambient inward. **Left**: the order is class assumptions, then
    `{s t : S}`, then `(h : s ≤ t) [IsMulCommutative t]`.
