# Reviewer brief

Act as a Mathlib maintainer reviewing complete change targets. Predict concrete changes a
maintainer would plausibly request, not general risks, questions, defenses of the code, or notes
that something is merely worth checking.

Read `pr.md`, then `model.md` (every changed object, its kind and what changed, with the families
and relations the change graph finds), then `diff.patch`.

Examine every target across all concern families:
- proof-golf;
- generalization;
- duplication;
- naming;
- documentation;
- style;
- scope;
- correctness.

There is no quota. Submit only actionable requests supported by the reviewed code, and submit none
when no request is warranted.

Each finding has exactly one primary target. The claim must assert a present problem and name the
primary declaration when there is one. The requested change must be an imperative, concrete
transformation that would resolve it.

## Maintainer ask checklist

Apply every item to every changed declaration and file, but emit a finding only for a concrete
change you would actually request.
1. **proof-golf:** replace a longer or manual proof with a canonical lemma, tactic, or proof
   structure.
2. **generalization:** weaken hypotheses, or state the declaration at the reusable level
   maintainers expect.
3. **duplication:** replace new code with an existing declaration or shared abstraction.
4. **naming:** rename declarations to match their meaning, type, and local sibling conventions.
5. **documentation:** correct or complete docstrings and module documentation.
6. **style:** request a specific formatting, binder, calc, case-split, attribute, or structural
   rewrite.
7. **scope:** move, split, expose, privatize, or remove code that is misplaced for this PR.
8. **correctness:** fix a present semantic, elaboration, build, policy, or API error.

Do not report that an item was checked, does not apply, or is merely worth investigating.

## Tools

Run `./ptool describe` once to read every tool's description and arguments. These are the tools
Mathlib review arms hold; call one as `./ptool <tool> '<json arguments>'`.

`lean_verify_edit` compiles the PR's file with your edit against the PR's reviewed workspace:
give `path`, `declaration_name` and a complete `new_declaration`. Use it to check any edit you
propose.

## Output

Write, in this directory:
- `findings.json`: a JSON list, one object per request, with keys `target` (the declaration or
  file), `claim` (the present problem), `requested_change` (the concrete change), `severity`
  (`blocking` or `advisory`) and `evidence` (what you checked, with the tool results).
- `notes.md`: what you did, object by object, including what you checked and found nothing wrong
  with.

## Places where a maintainers' convention may apply

A separate pass compared this PR's changed code with conventions Mathlib's maintainers hold when they review. Each item below names a place where one convention's situation occurs, the convention, and how to tell whether the code departs from it. The pass read the diff only and ran nothing. Treat every item as a claim to verify: where an item names a check, run it with your tools; where the code departs, request the change the convention calls for, as a finding at that place; where it does not, drop the item and say nothing of it. The items are not the whole review: review the rest of the PR as the brief above says.

- `Mathlib/Analysis/Calculus/TangentCone.lean`, `module docstring`: PR moves the TVS/Normed boundary, restating tangentConeAt_mono_nhds, UniqueDiffWithinAt.mono_nhds and others for TVS, and moves the closure lemmas; the docstring may describe the setting. Convention: The module docstring is kept in step with the code: it covers every main result the file contains, as currently stated. Check: Compare the file's main declarations with its docstring's lists, and search other files' module docstrings for declarations the PR moved or removed. Departure: a main declaration is missing or misstated, or a docstring claims one its file no longer has.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `section Normed (before tangentConeAt_closure)`: Moved `section Normed` is directly followed by four `variable` commands, none separated from the next by a blank line. Convention: A `namespace`, `section`, `end` or `variable` command is separated from the declarations and commands around it by a blank line. Decided by reading: the code departs.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `section Normed (before uniqueDiffWithinAt_closure)`: Moved `section Normed` is directly followed by four `variable` commands (𝕜', E, F, x y s t) with no blank lines between them. Convention: A `namespace`, `section`, `end` or `variable` command is separated from the declarations and commands around it by a blank line. Decided by reading: the code departs.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `tangentConeAt.lim_zero`: Goal closed by manual steps: a `have` term built from inv_smul_smul₀, `apply Tendsto.congr'`, `rw ... at hc`, then `simpa`. Convention: A goal that a standard finishing tactic (`simp`, `rfl`, `trivial`, `omega`, `positivity`, `grind`, `grw`, ...) closes is closed by that tactic, not by a hand-written term or rewrite chain. Check: Replace the manual steps for that goal by a standard finishing tactic, with hints if needed (`simp`, `grind [...]`, `fun_prop`, `positivity`, `omega`, `grw [...]`, `rfl`); if it closes the goal, the original departs.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `tangentConeAt.lim_zero`: Rewritten proof chases pointwise that `(c n)⁻¹ • c n • d n = d n` eventually, then uses `Tendsto.congr'` and `simpa`, for a Tendsto/smul statement with library API. Convention: A result or construction that existing library lemmas or API yield directly (a composition of library equivalences) is derived from them, not reproved or rebuilt from first principles. Check: Search the library, including recent master, for lemmas or API whose combination yields the statement (composition lemmas, existing equivalences, a general form). Departure: such a derivation exists and is shorter or needs fewer assumptions.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `tangentConeAt.lim_zero`: `apply Tendsto.congr' this`, then `rw [tendsto_norm_atTop_iff_cobounded] at hc`, then `simpa using ...hc...` are consecutive calls a single `simpa`/term might combine. Convention: Consecutive tactic calls or `calc` steps that a single call can perform are merged into that one call. Check: Replace the consecutive calls with one combined call (a concatenated `rw` list, `rwa` for rewrite-then-exact, `by_contra!` for negate-then-intro, one merged `calc` step) and rebuild. Departure: the combined call compiles.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `tangentConeAt.lim_zero`: Replaces the explicit norm argument (`rw [zero_mul] at C`, `tendsto_zero_iff_norm_tendsto_zero`, `exact D`) with an unsqueezed `simpa using`. Convention: An automation call such as `grind`, or a flexible `simp` in place of a squeezed `simp only`, replaces an explicit proof only when the explicit proof is not short and readable and the automation is not markedly slower. Check: Write the explicit term or squeezed `simp only` for that step and compare elaboration time or heartbeats; a departure is that a short readable explicit form compiles, or that the automation is markedly slower (half a second counts). Not when: The explicit proof is long or hard to read and the automation is not markedly slower.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `tangentConeAt.lim_zero`: Short `by` block of `have`, `apply Tendsto.congr'`, `rw ... at hc`, `simpa using` assembling lemma applications; might be one term chain. Convention: A short tactic block that a single term proves is written as that term. Check: Replace the `by` block with one term built from the same lemmas (dot-notation chain, `⟨…⟩`, `fun … ↦ …`); if it compiles and reads no worse, the original departs.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `tangentConeAt.lim_zero`: `rw [tendsto_norm_atTop_iff_cobounded] at hc` converts hypothesis hc into cobounded form only to feed `tendsto_inv₀_cobounded.comp hc`. Convention: The direct lemma for a goal is used rather than one obtained by converting another (`le_rfl`, not `rfl.le`). Check: Search the library (`exact?`, names the naming convention predicts for the composite or specialised statement) for a lemma whose conclusion is the step's goal as stated. Departure: one exists and closes the goal without the conversion or extra side goals.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `tangentConeAt.lim_zero`: New proof writes `fun n hn ↦`, while the same declaration's statement uses `fun n =>` and nearby IsOpen.uniqueDiffOn uses `fun _ hx =>`. Convention: The same construct or notation is spelled the same way throughout a file, in code and in docstrings (`have` vs `haveI`, one lambda arrow, one attribute placement, one notation for an interval). Check: Search the file for the other occurrences of the same construct; a departure is a changed line whose spelling differs from the one used by the file's other occurrences or by the neighbouring declarations.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `tangentConeAt.lim_zero`: Proof golfed from eleven lines with stated `have`s to four; final `simpa using (tendsto_inv₀_cobounded.comp hc).smul hd` packs inverse-to-zero, product limit and simplification. Convention: A proof is not compressed into dense one-liners; an intricate argument is split into intermediate steps that read on their own. Check: Can a reader without the infoview follow each step, seeing the intermediate claims (stated `have` types, `calc` lines, ascriptions), or is the substance hidden in merged steps, a non-terminal `<;>` or opaque automation? Departure: the latter. Not when: A shortening that removes redundant steps rather than merging them, leaving each remaining step readable.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `tangentConeAt.lim_zero`: Statement mentions only Tendsto, the norm on 𝕜 and smul, no tangent cone; rewritten proof uses tendsto_inv₀_cobounded and tendsto_norm_atTop_iff_cobounded. Convention: A proof uses no heavier machinery than its statement needs, so the lemma can sit in the earliest file where its statement makes sense. Check: Could the statement be proved by elementary means available where its notions are defined, avoiding the heavier lemma, construction or import, so that it could sit in an earlier file?
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `tangentConeAt.lim_zero`: The new proof refers to the primed name `Tendsto.congr'`. Convention: A name carries a prime only to distinguish it from an unprimed sibling that is the primary form; a primed name with no such sibling is unprimed. Check: Search the library and the PR for the same name without the prime. Departure: no declaration or field with the unprimed name exists, so the prime distinguishes nothing.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `variable [ContinuousAdd E] (before tangentConeAt_mono_nhds)`: Adds ContinuousAdd E to tangentConeAt_mono_nhds through tangentConeAt_inter_nhds; their proofs may need only continuity of the translation `x + ·`. Convention: A hypothesis that the definition or proof does not need is dropped, or weakened to what it does need, so that the result holds in the greater generality. Check: Delete the hypothesis, or replace the typeclass with the weakest class providing the operations used, and rebuild the declaration. Departure: it still compiles (perhaps after a small proof fix), or the hypothesis follows from the others by an existing lemma.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `variable [ContinuousAdd E] (before tangentConeAt_mono_nhds)`: Generalises tangentConeAt.lim_zero, tangentConeAt_mono_nhds to tangentConeAt_inter_nhds to TVS; siblings tangentConeAt_closure and subset_tangentConeAt_prod_left stay in section Normed. Convention: A variant or improvement introduced for one member of a family of siblings (left/right or primed lemma variants, analogous tactics or attributes, parallel code paths in meta-code) is also provided for the other members. Check: Identify the member's siblings (the mirrored left/right name, the analogous structure, tactic, simproc or code path) in the file and library. Departure: a sibling exists for which the PR provides no corresponding variant or change.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `variable [ContinuousAdd E] (before tangentConeAt_mono_nhds)`: The TVS assumption is spelled `[ContinuousAdd E]` (with `[ContinuousSMul 𝕜 E]`); library TVS lemmas may instead use `[IsTopologicalAddGroup E]`, equivalent here. Convention: A hypothesis or conclusion is spelled in the form the library's existing lemmas use most; when another spelling is kept, lemmas relating the two spellings are provided. Check: Search the library for lemmas about the same notions and see which spelling most use. Departure: the new statement uses a less common spelling and the PR adds no lemma converting it to the common one.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `variable [ContinuousAdd E] [ContinuousSMul 𝕜 E] (before UniqueDiffWithinAt.mono_nhds)`: Imposes both classes on UniqueDiffWithinAt.mono (s ⊆ t), proved via mono_nhds; tangentConeAt_mono and closure_mono might give it without either. Convention: A hypothesis that the definition or proof does not need is dropped, or weakened to what it does need, so that the result holds in the greater generality. Check: Delete the hypothesis, or replace the typeclass with the weakest class providing the operations used, and rebuild the declaration. Departure: it still compiles (perhaps after a small proof fix), or the hypothesis follows from the others by an existing lemma.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `variable [ContinuousAdd E] [ContinuousSMul 𝕜 E] (before UniqueDiffWithinAt.mono_nhds)`: Generalises UniqueDiffWithinAt.mono_nhds through IsOpen.uniqueDiffOn to TVS; parallel uniqueDiffWithinAt_closure, UniqueDiffWithinAt.mono_closure and UniqueDiffWithinAt.prod stay in section Normed. Convention: A variant or improvement introduced for one member of a family of siblings (left/right or primed lemma variants, analogous tactics or attributes, parallel code paths in meta-code) is also provided for the other members. Check: Identify the member's siblings (the mirrored left/right name, the analogous structure, tactic, simproc or code path) in the file and library. Departure: a sibling exists for which the PR provides no corresponding variant or change.
- `Mathlib/Analysis/Calculus/TangentCone.lean`, `variable [ContinuousAdd E] [ContinuousSMul 𝕜 E] (before UniqueDiffWithinAt.mono_nhds)`: UniqueDiffWithinAt lemmas now assume `[ContinuousAdd E] [ContinuousSMul 𝕜 E]`, one of several equivalent spellings (e.g. `[IsTopologicalAddGroup E]`) of a topological vector space. Convention: A hypothesis or conclusion is spelled in the form the library's existing lemmas use most; when another spelling is kept, lemmas relating the two spellings are provided. Check: Search the library for lemmas about the same notions and see which spelling most use. Departure: the new statement uses a less common spelling and the PR adds no lemma converting it to the common one.
