# Facet rubric v1: describing a Mathlib reviewer's ask by what it looks at and how it is settled

You are labelling first-round reviewer comments on Mathlib pull requests. Every comment in your
batch has already been judged to be an **ask**: it requests, proposes, or pointedly questions a
change. You do not decide whether it is an ask. You describe it along five facets.

**Inputs.** Read ONLY this rubric and your batch file. Do not open anything else in the directory
or the repository, and do not look anything up.

Your batch file has one JSON object per line, with these fields:
- `cid`, and the PR's `pr_title`;
- `path`;
- `diff_hunk`: the code the comment is attached to, ending at the commented line;
- `body`: the comment;
- `parent_body`: the comment it replies to, if any, truncated;
- `commented_declaration_kind`: the kind of declaration the commented line sits in, when it could
  be found (`theorem`, `lemma`, `def`, `instance`, `structure`, `class`, `abbrev`, `command`,
  `module_doc`, …), or `""`.

## Output

For every comment, one JSON object per line, with exactly these keys:
`cid`, `object`, `reference`, `second_reference`, `mechanism`, `remedy`, `warrant`, `note`.

`note` is at most 20 words. It is required when you hesitated between two values of a facet: name
both.

## The facets

### `object`: the thing the ask would change

Label what would be edited, not what is mentioned.

| value | what it is |
|---|---|
| `proof` | the proof of a theorem or lemma, or a proof obligation inside a definition or instance: tactics, proof terms, proof steps |
| `name` | the name of a declaration, variable or hypothesis; its namespace, when chosen for the name or for dot notation |
| `binders` | explicit, implicit or instance-implicit binders, argument order, section `variable`s, `omit`/`include` |
| `statement` | a theorem's or lemma's statement: its hypotheses and conclusion, their form and generality |
| `attributes` | registration with automation: `simp`, `ext`, `gcongr`, `fun_prop`, `norm_cast`, `aesop`, `grind`, `simps`, `to_additive`, `to_dual`, `reassoc`, `csimp`; a `nolint` or linter option |
| `definition` | a definition, structure, class or abbreviation: its value or fields, its encoding, its parameters and their generality, and its reducibility (`abbrev`, `@[reducible]`, `irreducible_def`), computability and universes |
| `instance` | an instance declaration: whether it should exist, its hypotheses, priority, scope or visibility, and how it relates to other instances |
| `family` | several related declarations at once: an API to add, duals or variants, consistency across siblings, a lemma to extract from or merge into others |
| `location` | where code lives: which file or directory, file organisation, imports, placement within the file |
| `prose` | docstrings, module docs, comments, references, TODOs |
| `layout` | whitespace, indentation, line breaks, parentheses, redundant qualification, keyword and syntax spelling |
| `pr` | the PR as a change: description, title, scope, splitting, tests, AI disclosure, motivation, dependencies |
| `meta` | tactic, linter, command or other metaprogramming code, and scripts |
| `build` | whether the PR builds or passes CI as a whole |

**Boundaries:**
- A hypothesis's *form* or *generality* is `statement` for a theorem and `definition` for a
  definition. Its *binder kind* is `binders`.
- `@[reducible]`/`abbrev` on a definition is `definition`, and instance priority is `instance`.
  Automation attributes are `attributes`.
- "Add a missing lemma" is `family`. "State this one lemma differently" is `statement`.
- Deprecation aliases for renamed or removed declarations are `name` for a rename, and `family`
  when several declarations are deprecated.
- A proof inside meta code is `meta`.

### `reference`: what the reviewer compares the object against

| value | the reviewer's comparison |
|---|---|
| `variant` | a better version of the same object that the reviewer imagines: shorter, simpler, more direct, more general, weaker hypotheses, better decomposed, clearer |
| `library` | a specific existing declaration, construction, predicate, notation or file in the library: "this already exists", "use `X`", "this follows from `Y`", "state it with the existing predicate" |
| `norms` | the library's conventions: naming, style, spelling, syntax, formatting, how things are usually written, what a linter or the style guide wants |
| `siblings` | other declarations in the same PR or family: duplicates within the PR, consistency with its siblings, a missing dual or variant, the same fix applied to the analogous places |
| `mechanism` | how a Lean or Mathlib mechanism will treat the object: `simp` and other automation, generators, typeclass inference, definitional unfolding, elaboration, compile time, the build |
| `module_graph` | the file and import structure: where things belong, import weight or direction, file organisation |
| `intent` | what the author or the mathematics means: does it say what it claims, is it correct, does the code do what its documentation says, does it handle every case |
| `process` | the maintainers' expectations of a PR and of the library's direction: is it wanted and worth it, is it scoped, described, disclosed and tested |

- **Pick the comparison the ask's justification rests on.** "Use `foo` to shorten this proof"
  rests on the existing `foo`, so it is `library`. "This proof can be shorter" with no named
  declaration is `variant`. "Rename to match the convention" is `norms`. "Rename to match the
  sibling lemma" is `siblings`.
- **If a second comparison is clearly also present,** put it in `second_reference`. Otherwise
  write `""`.

### `mechanism`: which one, when `reference` is `mechanism`

Otherwise write `""`.

| value | the mechanism |
|---|---|
| `registration` | automation that uses registered lemmas: `simp` sets and simp normal form, `gcongr`, `fun_prop`, `ext`, `norm_cast`, `aesop`, `grind` |
| `generators` | attributes and commands that generate declarations: `simps`, `to_additive`, `to_dual`, `reassoc`, `deriving` |
| `typeclass` | instance search: whether inference finds something, instance priority, diamonds |
| `defeq` | definitional unfolding and reducibility: `rfl` proofs, `show`/`change`, `erw`, abbreviations, irreducibility |
| `performance` | compile or elaboration time, heartbeats, slow tactics, import cost |
| `build` | whether the code builds at all |

### `remedy`: the shape of the fix the reviewer wants

| value | the fix |
|---|---|
| `local` | rewrite inside one declaration or one piece of text, with no change to any interface: a proof, a comment, spacing |
| `interface` | change a statement, binders, a name or attributes, which callers or users see |
| `delete` | remove something and use or generate what exists instead: a duplicate, a generated lemma, a redundant instance or import |
| `add` | add declarations, lemmas, instances, tests or documentation that are missing |
| `reencode` | change how a definition, structure or class is built |
| `move` | move code to another file, section or namespace |
| `pr` | change the PR itself: its description, title, scope or split |
| `none` | the reviewer asks for a justification or an answer, not an edit |

### `warrant`: the cheapest check that would settle whether the ask is right

| value | the check |
|---|---|
| `compile` | make the change and build it. Does the shorter proof, the weaker hypothesis, the proof using `X`, the removed instance still work? |
| `exhibit` | point at something that exists: the duplicate, the general version, the existing predicate or file. Seeing it settles the ask, without first changing the author's code. |
| `count` | the library's prevailing practice, a style-guide rule or a linter settles it |
| `judgment` | nothing mechanical settles it: intent, clarity, worth, design taste, mathematical meaning |

**Precedence.** Use `exhibit` when showing an existing thing settles it. Otherwise use `compile`
when building the change settles it. Otherwise `count`, and otherwise `judgment`.

For example:
- "This lemma already exists as `X`" is `exhibit`.
- "Use `X` to shorten this proof" is `compile`: the question is whether the shorter proof works.
- "Can this hypothesis be dropped?" is `compile`.
- "Is this the right definition?" is `judgment`.

## Rules

- Label each comment on its own content. For a reply, `parent_body` only tells you what "this"
  refers to.
- One value per facet, from the lists above, spelled exactly as given.
- Do not reason about what the author should do beyond what the reviewer asks.

Write your output to the file path you were given, one JSON object per line, every `cid` in your
batch in the batch's order. Then validate it:
- every `cid` is present exactly once;
- every line is valid JSON with every key;
- every value comes from the lists.

Then reply only with:
- the counts by `reference`;
- the counts by `warrant`;
- the number of comments whose `note` names a hesitation.
