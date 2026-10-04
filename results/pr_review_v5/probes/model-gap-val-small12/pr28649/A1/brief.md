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

- A module docstring's title states precisely what the file proves, not a generic heading that suggests a different or broader result.
- A docstring's closing `-/` follows the last line of text directly, on that line, with no blank line before it and not on a line of its own.
- The module docstring is kept in step with the code: it covers every main result the file contains, as currently stated.
- A cleanup PR leaves out a hunk whose change costs more readability than the cleanup gains.
- Punctuation, operators and application inside terms, and text in docstrings, carry the standard spacing: a space after commas in tuples and lists, around infix operators (`/`, `^`), around `:=` in named arguments and inside structure-instance braces, inside set-builder braces (`{ x | p x }`), around `|` in alternative patterns, and after `←` in a rewrite list, none after an opening bracket or a prefix `-`, one after a markdown heading marker, and never a doubled space or a trailing space at the end of a line or string.
- A docstring is written in full sentences ending in a period.
- The same construct or notation is spelled the same way throughout a file, in code and in docstrings (`have` vs `haveI`, one lambda arrow, one attribute placement, one notation for an interval).
- A module docstring uses only the standard section headings (Main definitions, Main results, Implementation notes, References, Tags); ad hoc headers are not added.
- A change of marginal benefit (cosmetic spacing, docstring polish) is not made, or not merged, when its review cost exceeds the gain.
- The PR title and description say precisely what the change is (what moves where, what is renamed to what), kept accurate as the PR evolves.
- A purely stylistic change to existing code or prose that the style guide does not mandate is left to the original author's taste, not made by a third party.
- A docstring that names a theorem (`The Rees theorem`) also states what the theorem says and links it to the notions it is about.
- In a docstring list, a continuation line of an item is indented two spaces, under the item's text.
- A declaration's docstring states what the value or result is in words (its defining formula or meaning), not a restatement of its type or statement; a docstring that would only repeat the statement is omitted.
- A term derived from a person's name is spelled and capitalised as the name is (Artinian, Noetherian, von Neumann), the same way throughout the file.
- A cross-reference to another module in documentation gives its file path, not its dotted module name.
- A PR title follows the commit convention `type(Area): description`.
- Notation, indexing and the spelling of a term for a standard notion follow the literature's usual convention; a departure is avoided or justified by a cited reference.
- A declaration name or code fragment (a variable, a formula) mentioned in a comment or docstring is written in backticks and with its full name, so that it renders as code and links in the documentation.
- A docstring describes in full mathematical words (`homomorphism`, `multiplicative monoid`), not with the abbreviations used in identifiers (`hom`) or a pasted Lean expression.
- Explanation of a file's main results, and its TODO list, belong in the module docstring at the top, not in a separate comment block (`/-! -/` further down or `/- -/` after the docstring).
- Mathematics in a comment or docstring that unicode and backticks can express is written that way, not in LaTeX; LaTeX is reserved for formulas unicode cannot express.
- A PR changes existing code only where its purpose requires; incidental rewrites of proofs or renames of declarations it does not need to touch are left out.
- A comment or docstring recording that a declaration was adapted from, or is similar to, another in-library declaration is not kept.
- A docstring that is a noun phrase rather than a complete sentence does not end with a full stop.
