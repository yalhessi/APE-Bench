# Mathlib PR Review Checklist

Use this as the default review pass before deciding whether a PR is merge ready.

This checklist is derived from the official Mathlib PR review guide. Its main evaluation areas are:
style, documentation, location, improvements, and library integration.

For `skilled_pr_review`, use this checklist after reading:
- `pr-review-guide-reviewer.md`
- `naming-conventions-reviewer.md`
- `documentation-style-reviewer.md`
- `style-guidelines-reviewer.md`

Treat those guide files, not free-form preference, as the source of review-quality judgments.

## Review posture

- Be respectful, encouraging, and specific.
- Stay humble: leave room for uncertainty and avoid overstating preferences as hard rules.
- Partial review is still useful; focus first on the areas where the evidence is clearest.
- Separate blocking issues from advisory suggestions. The benchmark is about merge readiness, not
  exhaustive polish.

## Default evaluation pass

1. Style and PR metadata

- Does the code follow established formatting conventions?
- Do new names follow Mathlib naming conventions?
- Is the PR title and description informative enough to belong in permanent git history?
- If this turns on house style, naming, or PR-metadata conventions, consult:
  `naming-conventions-reviewer.md`, `style-guidelines-reviewer.md`, and
  `commit-conventions-reviewer.md`.

2. Documentation

- Do new definitions have informative docstrings?
- Do important theorems have docstrings when the statement is long, subtle, or especially useful?
- Are there cross references to related declarations where that would help readers?
- Do complicated proofs need comments or a proof sketch?
- Are there warnings when a declaration is auxiliary, file-local in spirit, or dangerous to use
  naively?
- If the PR formalizes material from the literature, should it cite that literature?
- If this becomes the main issue, consult `documentation-style-reviewer.md` and
  `pr-review-guide-reviewer.md`.

3. Location

- Are the declarations in the right files?
- Do the results already exist, possibly under a different name or in greater generality?
- Are new imports introduced, and do they import too much for this file?
- Should some declarations move to a new file to avoid import creep?
- Should the file be split because it is too long or mixes weakly related material?
- If file placement or imports are in doubt, consult `style-guidelines-reviewer.md` and
  `pr-review-guide-reviewer.md`.

4. Improvements

- Should part of a long proof be split into supporting lemmas or definitions?
- Would different tactics materially improve readability?
- Would a different proof structure greatly simplify the argument?
- Is the chosen definition or formalization awkward enough that it likely reflects a deeper design
  problem?
- Treat this section as lower priority than correctness, documentation, placement, and API fit.

5. Library integration

- Does the change provide a sensible API?
- Are attributes such as `@[simp]`, `@[ext]`, or generated lemmas missing or misapplied?
- Is the result general enough for known or foreseeable future use?
- Does the change fit existing Mathlib design patterns and the library's overall direction?
- Could new instances create diamonds or awkward non-defeq behavior?
- If this turns on API design or compatibility conventions, consult
  `style-guidelines-reviewer.md`.

6. Specific technical checks from the review guide

- Do declarations use `Type*` rather than `Type _` where Mathlib expects arbitrary universe levels?
- Do new definitions come with the lemmas users will need?
- Are instance, simplification, and extensibility consequences acceptable?

## Blocking versus advisory

Treat a finding as blocking when it would plausibly justify "please change this before merge".

Typical blocking cases:
- Mathematical or semantic incorrectness.
- Requirement mismatch or unwanted scope expansion.
- Wrong file placement, harmful imports, or bad library integration.
- Missing key documentation or warnings that make the change hard to maintain or easy to misuse.
- API design problems serious enough to make the merged result a poor fit for Mathlib.

Typical advisory cases:
- Alternative names when the current one is acceptable under Mathlib conventions.
- Optional refactors or shorter proofs.
- Tactic golf that does not affect readability or maintainability much.
- Minor docstring or comment polish.

## Evidence gathering

- Inspect the changed files in `target/`, not just the diff preview.
- Read surrounding declarations and imports when reviewing names, instances, or API shape.
- Use `scratch/pr.diff` for the full patch context.
- Use Lean retrieval or navigation tools when checking whether a result already exists, where it
  belongs, or which nearby API patterns Mathlib already uses.
- Prefer concrete code evidence and explicit guide-backed conventions over generic taste.

## Final decision

- `merge_ready=true` means no blocking issue remains.
- Keep advisory tags sparse and useful.
- In final feedback, point to the concrete code or convention behind each important claim.
