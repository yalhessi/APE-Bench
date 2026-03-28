# Documentation Style For Reviewers

Use this file when a PR review depends on module headers, docstrings, comments, citations, or
other documentation expectations.

Derived from the official Mathlib documentation style guide.

## File-level documentation

- Each file should begin with a copyright header, the import list, and a module docstring.
- The module docstring should use ATX-style Markdown headers and normally include:
  title, summary, optional main definitions or statements, notation, implementation notes,
  references, and tags.
- References in module docs should point to entries in `docs/references.bib`.

## Declaration docstrings

- Every definition and every major theorem should have a docstring.
- Docstrings on useful lemmas are encouraged, especially when the statement has real mathematical
  content or is likely to be reused elsewhere.
- A good docstring describes the mathematical meaning, not just the implementation details.
- If the text is a full sentence, it should end with a period.
- Named theorems such as the mean value theorem should be bolded in prose.
- Tactics should have self-contained docstrings that start with a full sentence naming the tactic,
  list forms/options in bullets, and place examples in code blocks.

## Helpful supporting conventions

- Use backticks for Lean declarations and variables. Fully qualified names improve generated docs.
- Wrap raw URLs in angle brackets so they render correctly.
- LaTeX can be written inline, display-style, or with environments.
- Sectioning comments should use `/-! ... -/` and `###` headers when they are only for display.
- Documentation should be written in English. Different English spellings are acceptable in prose,
  but declaration names should still follow Mathlib naming conventions.

## Linting and citations

- `docBlame` checks definitions without docstrings.
- `docBlameThm` checks theorems and lemmas without docstrings.
- `tacticDocs` checks tactics without docstrings.
- Literature references should be added to `docs/references.bib` and cited from module docs or
  declaration docstrings.

## Review use

- Missing or weak documentation can be merge-blocking when it leaves a key definition, theorem,
  constructor, or warning effectively unusable to future readers.
- Requests for cross references, proof-sketch comments, or usage warnings are especially valuable on
  long statements, subtle interfaces, and declarations that are easy to misuse.
- Smaller prose polish is usually advisory unless the current wording is misleading or inaccurate.
