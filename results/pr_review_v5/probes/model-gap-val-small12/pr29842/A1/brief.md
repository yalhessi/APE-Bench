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

## Conventions the maintainers hold

These are conventions Mathlib's maintainers hold when they review, one sentence each: a situation and the form preferred in it. They are stated in general, and none names a place in this PR. Check the changed code against each one. Where it departs from a convention, request the change that convention calls for, as a finding at the place it applies.

- A new declaration reuses the `variable`s already declared in the file rather than introducing duplicates of them.
- A hypothesis that the definition or proof does not need is dropped, or weakened to what it does need, so that the result holds in the greater generality.
- A `namespace`, `section`, `end` or `variable` command is separated from the declarations and commands around it by a blank line.
- An auxiliary `have` or `let` whose proof is a short term is inlined at its use sites rather than named.
- Consecutive tactic calls or `calc` steps that a single call can perform are merged into that one call.
- An automation call such as `grind`, or a flexible `simp` in place of a squeezed `simp only`, replaces an explicit proof only when the explicit proof is not short and readable and the automation is not markedly slower.
- The module docstring is kept in step with the code: it covers every main result the file contains, as currently stated.
- Lambda abstractions are written with `fun` and `↦`, not `λ` or `=>`.
- Arguments shared by consecutive declarations are declared once with `variable`, not repeated in each signature.
- A result stated for a concrete type, object or value (a specific filter, a default element) but using only an abstract property of it, or none, is stated for every type, object or value with that property.
- A declaration that is moved, generalised or deduplicated keeps exactly the attributes of the original, transferred to its replacement; attributes are not added or dropped in the process.
- The PR title and description say precisely what the change is (what moves where, what is renamed to what), kept accurate as the PR evolves.
- A filter hypothesis or goal (`∀ᶠ`) is handled through the filter API (`.self_of_nhds`, `.mono`, `filter_upwards`) rather than unpacked by hand into an explicit set, ε or membership proof.
- A proof is not compressed into dense one-liners; an intricate argument is split into intermediate steps that read on their own.
- Every `section` or `namespace` is closed with a matching `end`, not left open to the end of the file.
- A proof uses no heavier machinery than its statement needs, so the lemma can sit in the earliest file where its statement makes sense.
- Docstring terminology matches the declaration's actual generality (an element of an algebra, not an operator, when no operators are involved).
- A PR title follows the commit convention `type(Area): description`.
- Declarations about one notion are grouped together, beside the existing lemmas about it, not scattered among sections or files about other notions.
- A PR changes existing code only where its purpose requires; incidental rewrites of proofs or renames of declarations it does not need to touch are left out.
- Declarations needing different typeclass assumptions are organised in sections that declare exactly what each needs, not one section whose surplus assumptions are removed with `omit`.
- A declaration is not stated in a generality (semilinear maps, extra parameters) that no use needs when that generality complicates the statement; it is generalised when a use arrives.
- A hypothesis or conclusion is spelled in the form the library's existing lemmas use most; when another spelling is kept, lemmas relating the two spellings are provided.
- A `variable` command, and a section around it, serves an argument shared by many declarations; an argument used by one declaration or only a few is bound in their signatures.
- A goal that is a lemma's conclusion up to simp-normalisation is closed by `simpa using` the lemma applied to explicit arguments, not by rewriting the goal backwards with `←` simp lemmas into the lemma's form.
