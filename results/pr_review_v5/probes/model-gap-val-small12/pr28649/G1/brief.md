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

- `Mathlib/Probability/Distributions/Gaussian/Real.lean`, `gaussianPDFReal`: Changed docstrings capitalise 'Gaussian'; other docstrings and comments in the file may still spell it 'gaussian'. Convention: The same construct or notation is spelled the same way throughout a file, in code and in docstrings (`have` vs `haveI`, one lambda arrow, one attribute placement, one notation for an interval). Check: Search the file for the other occurrences of the same construct; a departure is a changed line whose spelling differs from the one used by the file's other occurrences or by the neighbouring declarations.
- `Mathlib/Probability/Distributions/Gaussian/Real.lean`, `gaussianPDFReal_pos`: Changed docstring 'The Gaussian pdf is positive ...' uses the identifier abbreviation 'pdf' (of `gaussianPDFReal`) as a word, not 'probability density function'. Convention: A docstring describes in full mathematical words (`homomorphism`, `multiplicative monoid`), not with the abbreviations used in identifiers (`hom`) or a pasted Lean expression. Decided by reading: the code departs.
- `Mathlib/Probability/Distributions/Gaussian/Real.lean`, `lintegral_gaussianPDFReal_eq_one`: Changed docstring 'The Gaussian distribution pdf integrates to 1' uses shorthand 'pdf' as a word instead of 'probability density function'. Convention: A docstring describes in full mathematical words (`homomorphism`, `multiplicative monoid`), not with the abbreviations used in identifiers (`hom`) or a pasted Lean expression. Decided by reading: the code departs.
- `Mathlib/Probability/Martingale/Convergence.lean`, `docstring of the theorem after upcrossings_eq_top_of_frequently_lt`: Existing docstring reworded 'bounded liminfs' to 'bounded limit inferiors', meaning unchanged. Convention: A purely stylistic change to existing code or prose that the style guide does not mandate is left to the original author's taste, not made by a third party. Check: Is each such change required by the style guide, or does it fix a spelling, grammar or factual error? If neither, it departs. Not when: The style guide mandates it, the original had a real error, or the original author agrees.
- `Mathlib/Probability/Martingale/Convergence.lean`, `module docstring (Almost everywhere martingale convergence theorem)`: 'Implementationwise' reworded to 'In terms of implementation': wording only, the original was correct English, no factual or egregious error corrected. Convention: A change of marginal benefit (cosmetic spacing, docstring polish) is not made, or not merged, when its review cost exceeds the gain. Decided by reading: the code departs. Not when: The change corrects an egregious error.
- `Mathlib/Probability/Martingale/Convergence.lean`, `module docstring (Almost everywhere martingale convergence theorem)`: Third-party rewording of the original author's 'Implementationwise' to 'In terms of implementation', meaning unchanged. Convention: A purely stylistic change to existing code or prose that the style guide does not mandate is left to the original author's taste, not made by a third party. Check: Is each such change required by the style guide, or does it fix a spelling, grammar or factual error? If neither, it departs. Not when: The style guide mandates it, the original had a real error, or the original author agrees.
- `Mathlib/Probability/Martingale/Upcrossing.lean`, `module docstring (Variant of the upcrossing estimate)`: Changed line hyphenates 'left-hand side'; the file's other prose occurrences of 'left hand side' or 'right hand side' may be spelled unhyphenated. Convention: The same construct or notation is spelled the same way throughout a file, in code and in docstrings (`have` vs `haveI`, one lambda arrow, one attribute placement, one notation for an interval). Check: Search the file for the other occurrences of the same construct; a departure is a changed line whose spelling differs from the one used by the file's other occurrences or by the neighbouring declarations.
- `Mathlib/Probability/Martingale/Upcrossing.lean`, `module docstring (Variant of the upcrossing estimate)`: 'left hand side' changed to 'left-hand side': hyphenation only, meaning unchanged, no factual or egregious error corrected. Convention: A change of marginal benefit (cosmetic spacing, docstring polish) is not made, or not merged, when its review cost exceeds the gain. Decided by reading: the code departs. Not when: The change corrects an egregious error.
- `Mathlib/Probability/Martingale/Upcrossing.lean`, `module docstring (Variant of the upcrossing estimate)`: Punctuation-only change 'left hand side' to 'left-hand side' in existing prose, meaning unchanged. Convention: A purely stylistic change to existing code or prose that the style guide does not mandate is left to the original author's taste, not made by a third party. Check: Is each such change required by the style guide, or does it fix a spelling, grammar or factual error? If neither, it departs. Not when: The style guide mandates it, the original had a real error, or the original author agrees.
- `Mathlib/Probability/Moments/Basic.lean`, `module docstring`: Changed lines capitalise 'MGFs'/'CGFs', while the same docstring keeps lowercase 'the cgf exists' and `mgf`/`cgf` in prose. Convention: The same construct or notation is spelled the same way throughout a file, in code and in docstrings (`have` vs `haveI`, one lambda arrow, one attribute placement, one notation for an interval). Check: Search the file for the other occurrences of the same construct; a departure is a changed line whose spelling differs from the one used by the file's other occurrences or by the neighbouring declarations.
- `Mathlib/Probability/Moments/Basic.lean`, `module docstring`: Changed lines write 'their MGFs'/'their CGFs', the identifier abbreviations `mgf`/`cgf` used as words, not 'moment generating functions'/'cumulant generating functions'. Convention: A docstring describes in full mathematical words (`homomorphism`, `multiplicative monoid`), not with the abbreviations used in identifiers (`hom`) or a pasted Lean expression. Decided by reading: the code departs.
- `Mathlib/Probability/Moments/Variance.lean`, `docstring 'Popoviciu's inequality' (lemma after variance_le_sub_mul_sub)`: Heading 'on variance' changed to 'on variances': a one-letter wording change, meaning unchanged, no egregious error corrected. Convention: A change of marginal benefit (cosmetic spacing, docstring polish) is not made, or not merged, when its review cost exceeds the gain. Decided by reading: the code departs. Not when: The change corrects an egregious error.
- `PR`, `title`: 'miscellaneous typo fixes' bundles independent doc edits in seven files, including rewordings ('Implementationwise', 'liminfs', 'variance') that need none of the other edits. Convention: A PR is cut at its natural seams: separable parts, whether a core and its extensions or a part needing more design work, are split so each is reviewed on its own, and parts that only make sense together are not split arbitrarily. Check: Does the diff contain a part (a file, a section, a batch of fixes) that the rest does not depend on and that could be reviewed alone, still bundled into this PR? Not when: The parts only make sense together, so splitting them would be arbitrary.
