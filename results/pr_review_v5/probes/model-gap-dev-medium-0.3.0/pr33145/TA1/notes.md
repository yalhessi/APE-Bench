# Review notes: PR #33145 (Mathlib/Topology/Order/IsLUB.lean)

## What I did

- Read `brief.md`, `pr.md`, `model.md`, `diff.patch`. Read the reviewed file through `file_read`
  (`target/Mathlib/Topology/Order/IsLUB.lean`, lines 1-330) and its section structure.
- Library lookups (`declaration_search`): `upperBounds_closure`, `bddAbove_closure`,
  `continuous_sup`, `continuous_inf` (root lemmas exist), `Continuous.range_subset_closure_image_dense`,
  `Set.image_subset_range`, `isLUB_ciSup_set`, `ciSup_subtype`, `csSup_image`, `ciSup_of_not_bddAbove`,
  `Set.image_eq_range`. I searched (`content_search`) for an existing dense/ciSup or upperBounds-of-image
  lemma and found none, so the PR does not duplicate an existing declaration. `to_dual` is used in
  `Mathlib/Order` but not anywhere in `Mathlib/Topology`, so I asked for `(α := αᵒᵈ)` (the file's own
  pattern) and not for `to_dual`.
- `naming_norm`: `Dense.continuous_upperBounds` gave verdict *established* (`upperBounds_` 27/27),
  candidate `Dense.upperBounds_image`. The two sup lemmas gave *subject_unresolved*, so I judged their names directly.
- `zulip_search`: the "Continuous function reaches its supremum on a dense set" thread. Kevin Buzzard
  first proposed `⨆ s ∈ S` and then called it a gotcha. Jireh Loreaux suggested
  `isLUB_iff_of_subset_of_subset_closure` + `Continuous.range_subset_closure_image_dense`.
- `lean_verify_edit`, all of which compiled:
  - `upperBounds` term proof via `upperBounds_closure`, in two variants;
  - `lowerBounds`, `inf` and `inf'` as `(α := αᵒᵈ)` instances;
  - `sup` with `image_subset_range` inline and unprefixed `range_eq_empty`;
  - a 4-line `sup'` proof reusing `continuous_sup` and `continuous_upperBounds`;
  - `sup'` with typed `have`s and `f '' S`;
  - `refine` with binders introduced (the first attempt failed and the second compiled);
  - `protected` on `continuous_sup`;
  - a whole-block replacement of lines 169-261, with `namespace Dense`, one `variable` line, the
    renames, standalone docstrings, the general `upperBounds_eq_of_subset_of_subset_closure` and every golfed proof.
- `precedent_search` on `Dense.continuous_sup` returned nothing that applies.

## Object by object

- `Dense.continuous_upperBounds`:
  - The name leads with a hypothesis. Rename to `upperBounds_image`.
  - The proof re-derives `upperBounds_closure`. Golf it.
  - It is a special case of `s ⊆ t ⊆ closure s`. Generalise it.
  - It writes `Set.` under `open Set`, uses `=>`, and leaves the binders for a following `intro`.
  - `[TopologicalSpace γ]` comes after `f`.
  - The docstring is ungrammatical and says "range of the universe".
  - The statement and hypotheses are correct; `ClosedIicTopology` + `Preorder` is already the right
    generality for the codomain.
- `Dense.continuous_lowerBounds`: a hand-copied dual. Derive it via `αᵒᵈ`. The same style and
  docstring issues apply, filed on `upperBounds`.
- `Dense.continuous_sup`:
  - The name uses `sup` for `⨆` and clashes with root `continuous_sup`, so rename it, or else make it `protected`.
  - Replace `by grind` with `image_subset_range`, discharged inline.
  - Drop the `Set.` prefix.
  - Fix the docstring wording.
  - A question on the subtype binder.
  - Otherwise the proof is correct. The `IsEmpty` case is needed because `isLUB_ciSup` and
    `Dense.nonempty` need `Nonempty γ`; plain `simp` without `range_eq_empty` fails there, which I checked.
- `Dense.continuous_inf`: a hand-copied dual. Derive it via `αᵒᵈ`.
- `Dense.continuous_sup'`:
  - Replace the prime by a name for the dropped `BddAbove`.
  - It duplicates the proof of `continuous_sup`, and its unbounded branch can be golfed to four lines.
  - Use `f '' S` in place of the `range` of a lambda.
  - Use `↦` and the coercion, not `Subtype.val`.
  - Give the `have`s types.
  - Make the docstring standalone, not an "analogue of".
- `Dense.continuous_inf'`: derive it via `αᵒᵈ`, and make the docstring standalone.
- PR level:
  - The title has no area.
  - The description omits three of the six lemmas.
  - The co-authors the author names are not credited.
- Checked and nothing to ask:
  - placement in `IsLUB.lean` next to `Dense.isLUB_inter_iff`, which fits;
  - the hypothesis strength: `Continuous f` is needed, and `ClosedIicTopology` is weaker than the
    `OrderTopology` or `SupConvergenceClass` raised on Zulip;
  - correctness of all six statements;
  - the copyright header: the file is an existing 2017 file, and adding three lemmas does not call
    for an Authors change; credit belongs in the PR's co-author trailers.

## Conventions: places filed and places left

1. **Namespace grouping / no redundant prefix.**
   - Filed:
     - the file, for `namespace Dense`;
     - `Set.image_subset_range` in `continuous_upperBounds`/`lowerBounds`;
     - `Set.range_eq_empty` in `continuous_sup`/`inf`/`sup'`/`inf'`.
   - Left: none.
2. **Library-named predicate or function.**
   - Filed: `range (fun s : S => f (Subtype.val s))`, which is `f '' S`, in `continuous_sup'` (and `inf'`).
   - Left: `BddAbove (range f)`, `upperBounds (f '' S)` and `Continuous f`, which already use the library names.
3. **Name built from the statement's declarations.**
   - Filed:
     - `continuous_upperBounds` becomes `upperBounds_image`;
     - `continuous_sup` becomes `ciSup_eq_ciSup_subtype_of_bddAbove`, whose `sup` should be `ciSup`.
4. **Automation such as grind, or flexible simp, versus an explicit proof.**
   - Filed: under convention 22, the four `by grind`s.
   - Left: `simp [Set.range_eq_empty]` in the empty case, which is a terminal `simp` and fine. The
     final `simp [csSup_of_not_bddAbove ...]` in `sup'` is removed by the golf.
5. **Docstring on its own terms.**
   - Filed: `continuous_sup'` and `continuous_inf'`.
   - Left: the other four docstrings, which do not compare; they are filed for wording instead.
6. **`protected` on a root-name clash.**
   - Filed: `continuous_sup` and `continuous_inf`, whose root names were found by `declaration_search`.
   - Left: `continuous_upperBounds`/`lowerBounds`. `declaration_search` showed no root
     `continuous_upperBounds`.
7. **`fun` with `↦`.**
   - Filed:
     - `fun _ =>` in `continuous_upperBounds`/`lowerBounds`;
     - `fun s : S =>` in `continuous_sup'`/`inf'`.
   - Left: none.
8. **Shared arguments via `variable`.**
   - Filed: the file. The block was verified.
9. **Side goals inline in `refine`.**
   - Filed: `isLUB_ciSup_set ?_` followed by `exact h.mono (by grind)` in `continuous_sup` (same in the other three).
   - Left: `refine (isLUB_csSup ...).unique ?_`, whose `?_` is the main goal.
10. **Variant named by the differing term, not a prime.**
    - Filed: `continuous_sup'` and `continuous_inf'`.
11. **Coercion, not raw projection.**
    - Filed: `Subtype.val` in `continuous_sup'` (and `inf'`).
12. **Explicit types on non-evident `have`s.**
    - Filed: the two anonymous `have :=` in `continuous_sup'` (and `inf'`).
    - Left: `have h2 : ¬ BddAbove ...`, which is already typed.
13. **Name states the conclusion; a hypothesis only to distinguish.**
    - Filed: the `continuous_` lead in `continuous_upperBounds`, merged with the rename in 3.
    - Filed: `continuous_sup`, covered by the same rename finding. `_of_bddAbove` is kept only where
      it distinguishes the bounded version.
14. **Copyright, Authors and co-author credits.**
    - Filed: the PR co-author trailers for @plp127 and @j-loreaux.
    - Left: the file header, an existing 2017 file with its original authors.
15. **Title and description precise.**
    - Filed: the description omits `lowerBounds`/`inf`/`inf'`.
16. **Extract facts of independent use.**
    - Filed as a generalization: `upperBounds_eq_of_subset_of_subset_closure`. Its core is
      independent of continuity and is also inlined in `isLUB_iff_of_subset_of_subset_closure`.
    - Left: the `h2` block in `sup'`, which the golf removes rather than extracts.
17. **Generator for dual or twin lemmas.**
    - Left, unfiled: no `to_dual` use exists anywhere in `Mathlib/Topology`, which I checked with
      `content_search`, and the file's own idiom is `(α := αᵒᵈ)`. That form is requested under 19.
18. **Lighter tactic or direct lemma, not grind or aesop.**
    - Filed: `h.mono (by grind)`, which becomes `image_subset_range f S`, in `continuous_sup` (the
      finding covers all four).
19. **Dual by instantiating at `αᵒᵈ`.**
    - Filed: `continuous_lowerBounds`, `continuous_inf` and `continuous_inf'`, each verified.
20. **Comment recording adaptation or similarity removed.**
    - Filed: "This is an analogue of ..." in `continuous_sup'`/`inf'`, together with 5.
21. **Argument order, ambient first.**
    - Filed: `[TopologicalSpace γ]` after `{f : γ → α}`, in all six lemmas.
22. **No bare `_eq`.**
    - Left: the current names have no `_eq` suffix. The names I propose are `lhs_eq_rhs`, not a bare `_eq`.
23. **PR title `type(Area): ...`.**
    - Filed.
24. **Bounded binder, not the subtype.**
    - Filed as a question on `continuous_sup`. The bounded `⨆ s ∈ S` would change the meaning in a
      conditionally complete lattice (`sSup ∅` junk; `ciSup_subtype''` needs an extra hypothesis),
      so the request offers `sSup (f '' S) = sSup (range f)` instead.
25. **`refine` introduces the binders of its subgoals.**
    - Filed: `refine subset_trans ?_ ...; intro x hx i hi` in `continuous_upperBounds` (and
      `lowerBounds`). The fix was verified.
