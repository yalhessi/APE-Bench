# Where do these conventions' situations occur in this pull request? (pinpointing rubric, fixed 2026-10-05 before any pinpointing)

You are preparing notes for a reviewer. `rules.md` lists 52 conventions Mathlib's maintainers hold,
each written as a rule: what it applies to, the situation in which it is in play (its trigger), the
preferred form, how to tell a departure and what kind of check that takes (`read`, `compile`,
`lookup` or `judge`), and when it does not apply. The rules were written from maintainers' review
comments on other pull requests.

Read only the files in your working directory: this rubric, `rules.md`, and the pull request:
`pr.md` (title, description, changed files), `model.md` (every changed object and what changed) and
`diff.patch`.

## What to do

Go through **every** rule, one by one. For each, look through what this PR adds or changes for
places where the rule's trigger holds. Only added or changed code counts, not unchanged context.

- A rule whose trigger holds nowhere in the changed code is left out.
- **A `read` rule**: reading settles it, so decide. List a place only if the changed code there
  departs from the preferred form (`status: departs`). Where it conforms, leave it out.
- **A `compile`, `lookup` or `judge` rule**: you cannot run or search anything, so do not decide.
  Where the trigger holds and no `not_when` circumstance is visible, list the place with
  `status: check`, whether or not the code looks fine to you. Never leave such a place out because
  the code seems acceptable: deciding that is the reviewer's job, with tools you do not have.
- **A place** is one declaration, command, docstring, file, or the PR's title or description. At
  most three places a rule. If its trigger holds at more, keep the three where it holds most
  squarely.

## Output

Write `candidates.json` in your working directory: a JSON list of objects with exactly these keys:

- `id`: the rule's id, as in `rules.md`.
- `file`: the file's path as the diff gives it, or `PR` for the title or description.
- `declaration`: the name of the declaration, or what the place is (`variable` command, `section
  Foo`, `module docstring`, `imports`, `title`, `description`).
- `fact`: at most 30 words: what at this place is the rule's situation, said about this code (name
  the hypothesis, the tactic, the step, the binder).
- `status`: `departs` or `check`.

Check that the file parses, that every `id` is a rule of `rules.md`, that every `status` is one of
the two values, and that no id has more than three items. Then reply with one line: the number of
items.
