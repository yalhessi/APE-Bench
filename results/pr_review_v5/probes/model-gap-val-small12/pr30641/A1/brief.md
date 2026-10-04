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

- A lemma whose left-hand side applies a definition to a canonical argument and whose right-hand side is simpler is tagged `@[simp]`.
- A hypothesis that the definition or proof does not need is dropped, or weakened to what it does need, so that the result holds in the greater generality.
- A `simp` call does not list lemmas that are already in the default simp set.
- A docstring explains the declaration on its own terms rather than by contrast with another declaration.
- An argument's binder kind follows inferability: one that the other explicit arguments or later hypotheses determine is implicit, and one that cannot be inferred from them is explicit.
- A docstring's closing `-/` follows the last line of text directly, on that line, with no blank line before it and not on a line of its own.
- The module docstring is kept in step with the code: it covers every main result the file contains, as currently stated.
- A line is broken when, and only when, it exceeds the 100-character limit; a call, short proof, one-line declaration with its attribute, or docstring that fits on one line stays on one line.
- A monotonicity or congruence step in an inequality is discharged by `gcongr`, not by applying the specific named monotonicity lemma.
- An attribute goes on its own line above a declaration whose header spans several lines, not inline before the keyword.
- A variant or improvement introduced for one member of a family of siblings (left/right or primed lemma variants, analogous tactics or attributes, parallel code paths in meta-code) is also provided for the other members.
- Side goals that a short tactic closes are discharged inline in a `refine` or `apply` (`(by fun_prop)`), leaving `?_` for the real goal, rather than handled afterwards as separate bullets or with `any_goals`/`try` combinators.
- The same construct or notation is spelled the same way throughout a file, in code and in docstrings (`have` vs `haveI`, one lambda arrow, one attribute placement, one notation for an interval).
- A change of marginal benefit (cosmetic spacing, docstring polish) is not made, or not merged, when its review cost exceeds the gain.
- A term applied with `?_` holes is applied with `refine`, not `apply`; `apply` is used only when the remaining arguments are left to unification.
- A lemma that merely instantiates, reshapes or combines existing lemmas, with no real simplification of the statement, is not added; the existing lemmas are used directly.
- A lemma's statement, especially a `@[simp]` right-hand side, and a simproc's output are in simp-normal form: they contain no subterm that `simp` would rewrite (`1`, not `exp 0`; a literal, not `n % 4`).
- A declaration's docstring states what the value or result is in words (its defining formula or meaning), not a restatement of its type or statement; a docstring that would only repeat the statement is omitted.
- A case split or lemma instantiation uses the form whose result substitutes or simplifies directly (`obtain rfl | h := eq_zero_or_pos n`), so that no hypothesis needs rewriting afterwards.
- A cross-reference to another module in documentation gives its file path, not its dotted module name.
- A declaration's name and namespace follow the pattern of its siblings' and analogues' names (the same abbreviation of a hypothesis, the same ordering of parts, the same namespace for the same kind of construction), not a fuller or different spelling.
- A declaration name or code fragment (a variable, a formula) mentioned in a comment or docstring is written in backticks and with its full name, so that it renders as code and links in the documentation.
- A pair or run of parallel one-line declarations is kept adjacent with no blank line between them, so that the parallel is visible.
- A docstring's text begins on the `/--` line, not on the line after it.
- A PR changes existing code only where its purpose requires; incidental rewrites of proofs or renames of declarations it does not need to touch are left out.
