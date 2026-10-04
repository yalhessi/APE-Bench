# Which conventions apply to this pull request? (selector rubric, fixed 2026-10-04 before any selection)

You are choosing, for a reviewer, which of Mathlib's review conventions are relevant to one pull
request. `conventions.md` lists 438 conventions the maintainers hold, one a line, `P001` to `P438`.
Each names a situation and the form preferred in it. They were written from maintainers' review
comments on other pull requests.

Read only the files in your working directory: this rubric, `conventions.md`, and the pull request:
`pr.md` (title, description, changed files), `model.md` (every changed object and what changed) and
`diff.patch`.

## What to select

A convention **applies** when its *situation* occurs in what this PR adds or changes: the kind of
declaration, statement, proof step, name, attribute, docstring, file structure, or circumstance of
the PR as a change that the convention is about is present here.

- Select on the situation, **not on whether the code follows the convention**. If the situation
  occurs, the convention applies, whether the code seems to conform or not. Deciding that is the
  reviewer's job, with tools you do not have. Never leave a convention out because the code looks
  fine.
- Leave out a convention whose situation does not occur in the changed code.
- Read every line of `conventions.md`. The relevant ones are not grouped, and a rarely used
  convention matters as much as a common one.

## How many

At most 25. If more apply, keep those whose situation occurs most squarely, or most often, in this
PR. Fewer is right when few apply.

## Output

Write `selected.json` in your working directory: a JSON list, most squarely applicable first, of
objects with exactly these keys:

- `id`: the convention's id, as in `conventions.md`.
- `where`: the declaration or declarations, file, or part of the PR where its situation occurs.
- `why`: at most 20 words: what in the PR is the convention's situation.

Check that the file parses, that every `id` is a line of `conventions.md`, that no id repeats and
that there are at most 25. Then reply with one line: the number of conventions selected.
