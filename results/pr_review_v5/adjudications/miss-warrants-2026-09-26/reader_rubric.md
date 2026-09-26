# What would settle this ask, and what tool would a reviewer have needed?

You are labelling requests that Mathlib maintainers made in code review, and that an automated
reviewer failed to make. For each, decide what evidence would have let a careful reviewer make the
same request WITHOUT deep knowledge of Mathlib's design, and which tool would produce it.

Read ONLY this file and your batch file. Do not look anything up.

Each batch line is a JSON object: `id`, `path` (may be empty), `code_at_comment` (the code the
request was attached to, may be empty), `ask` (the maintainer's request, or a summary of it),
`context` (the comment it replied to, or the request's resolution criteria; may be empty).

## Output

One JSON object per line, every `id` once, keys exactly: `id`, `warrant`, `tool`, `knowledge`,
`note` (at most 20 words).

### `warrant`: the cheapest check that settles whether the ask is right

| value | the check |
|---|---|
| `compile` | make the change and build it: a shorter proof, a weaker hypothesis, an existing lemma closing a step, a removed instance |
| `exhibit` | point at something that exists in the library: the duplicate, the general version, the existing predicate, the file where it belongs |
| `count` | the library's prevailing practice or a style rule settles it: naming, statement form, binder style, layout, docstring conventions |
| `judgment` | nothing mechanical settles it: design taste, whether it is worth having, mathematical meaning, the PR's scope or description |

Precedence: `exhibit` if showing an existing thing settles it; else `compile` if building the
change settles it; else `count`; else `judgment`.

### `tool`: what would have produced the evidence

| value | the tool |
|---|---|
| `compile_edit` | compiling a proposed edit to the declaration |
| `type_search` | searching the library for a declaration BY ITS TYPE or statement shape (as `exact?`, `apply?` or Loogle do), to find one that exists under another name |
| `name_search` | searching by name or identifier text |
| `sibling_compare` | comparing the declaration with its siblings in the same file or family: their attributes, binders, forms, names |
| `census` | counting how the library spells or shapes things: name prefixes and suffixes, statement forms, binder styles, layout |
| `linter` | a style or environment linter would flag it |
| `read_pr` | reading the PR's description, title, tests or file layout |
| `none` | no tool gives it; it needs knowledge of Mathlib's design or of the maintainers' plans |

### `knowledge`: does the ask need deep Mathlib knowledge to make, even with the tool?

| value | meaning |
|---|---|
| `no` | a careful reviewer with the tool's output would make this ask |
| `partly` | the tool narrows it, but choosing to ask needs some sense of Mathlib's conventions or design |
| `yes` | the ask rests on knowing Mathlib's design, history or plans; no tool output would lead to it |

Validate your file (every id once, valid JSON, values spelled exactly as given) and reply only with
the counts by `warrant`, by `tool`, and by `knowledge`.

## Finding mechanism (added 2026-09-26, one reader, provisional)

`finding_mechanism.jsonl` labels each miss with the *exhaustive procedure that would surface the
ask without a reviewer noticing anything*, run over every object of the named kind. It answers a
different question from `tool` (which settles the ask once raised): what enumerates it.
- `closer_battery`: a fixed tactic list tried on every new or changed proof and proof step
  (`simp`, `simpa using`, `positivity`, `gcongr`, `omega`, `grind`, `exact?`).
- `old_proof_replay`: for every modified declaration, the pre-PR proof compiled under the new
  statement.
- `binder_sweep`: every instance argument weakened, every class-typed explicit hypothesis made
  instance-implicit, every `noncomputable` dropped, each followed by a compile.
- `library_shape_search`: the same file, then the family, then the library, matched on hypothesis
  and conclusion shape (a duplicate, a one-liner, a missing dual).
- `name_lint`, `diff_lint`, `census`: deterministic from the source, the diff, or a count.
- `generalisation_heuristic`: a literal constant in a statement, a fragment repeated across proofs.
- `none`: judgment or PR-level; no procedure surfaces it.

One reader labelled it in the session that designed the battery, so it carries no kappa and is a
planning label, not a measurement. The battery itself (`battery/`) is the measurement.
