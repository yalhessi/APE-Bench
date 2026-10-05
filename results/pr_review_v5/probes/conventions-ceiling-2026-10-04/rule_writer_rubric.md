# Writing a convention as a guarded rule (rule-writer rubric, fixed 2026-10-05 before any rule)

You are turning review conventions into rules a checker could apply. `entries.md` lists conventions
that Mathlib's maintainers hold. Each has an id, its sentence (a situation and the form preferred in
it), and up to four review comments from other pull requests in which a maintainer asked for it,
each with the code the comment was attached to.

Read only the files in your working directory: this rubric and `entries.md`. Do not look anything up.

## What to write

One rule for every entry, with exactly these fields:

- `id`: the entry's id.
- `applies_to`: the kind of thing the convention is about, in a few words: a new theorem's name, a
  proof step, a hypothesis binder, a docstring, a `variable` command, the PR description, and so on.
- `trigger`: the situation, as a test a reader can apply to the changed code of some *other* pull
  request and answer yes or no **without judging its quality**: what must be present for the
  convention to be in play. Make it as specific as the sentence and the examples allow, and no more:
  it must cover the examples, and it must name nothing particular to them (no lemma, file or
  mathematical object from an example). A trigger true of nearly every declaration is too wide: if
  the examples show what distinguishes the cases where maintainers raise it, say that.
- `required`: the form the convention calls for where the trigger holds.
- `check_kind`: how one tells that code where the trigger holds *departs* from the convention. One of
  - `read`: reading the changed code settles it;
  - `compile`: one must try an edit and see whether it compiles;
  - `lookup`: one must search the library, the file or the PR for something;
  - `judge`: it takes judgment that no single check settles.
- `check`: the check itself, as an instruction. For `read`, what to look at. For `compile`, the edit
  to try and the outcome that shows a departure. For `lookup`, what to search for and the finding
  that shows a departure. For `judge`, the question to answer.
- `not_when`: a circumstance in which the trigger holds and the convention still calls for no
  change, if the sentence or the examples show one. Otherwise the empty string. Do not invent one.

Keep `trigger` and `check` under 45 words each and the other fields under 25.

## Output

Write `rules.json` in your working directory: a JSON list with one object per entry, in the order of
`entries.md`. Check that the file parses, that every entry of `entries.md` has exactly one rule,
that every `check_kind` is one of the four values, and that no field but `not_when` is empty. Then
reply with one line: the number of rules written.
