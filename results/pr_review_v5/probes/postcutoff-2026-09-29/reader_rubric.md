# Labelling rubric: is each reviewer comment an ask, and which family of review work is it?

The val1000 reader rubric v2 (`arm-coverage-val1000-2025-06-2026-03-v1/reader_rubric_v2.md`) with the
arm-owner fields dropped: this reading needs only which comments are asks, their family and grain.

You are labelling first-round reviewer comments on Mathlib pull requests. Read ONLY this rubric and
your batch file. Do not look anything up.

Each batch line is a JSON object: `cid`, PR number and title, `kind` (review | review_comment |
issue_comment), review `state`, `author`, `path`/`line`, `reply_to_cid`, `diff_hunk` (the code it is
attached to, last ~600 chars), `body`.

## Output

For EVERY comment, one JSON object per line with exactly these keys:

- `cid`
- `is_ask`: `"ask"` or `"not_ask"`.
  - ask = the comment requests, proposes, or pointedly questions a change to the PR: code,
    statement, proof, attributes, names, docs, comments, imports, file layout, tests, the PR
    description, or the PR's scope. A ```suggestion block is an ask. A leading question is an ask
    ("does the old proof not work?", "Can `positivity` do this?"). An objection to the PR's premise
    is an ask.
  - not_ask = approval, thanks, bors / `maintainer merge` / `!bench` commands, a reviewer retracting
    their own comment, social or scheduling messages, a reply that only discusses without adding a
    request, CI or merge-queue chatter.
- `family`: exactly one code from the codebook below for an ask; `"n/a"` for a not_ask. Use `"NEW"`
  only when no family fits.
- `grain`: the smallest scope the reviewer had to look at: `"line"` | `"declaration"` |
  `"declaration_group"` | `"file"` | `"pr"`. For a not_ask, `"n/a"`.
- `note`: at most 20 words; required when family is NEW.

## The family codebook (one family per ask; pick the one that names what is being asked for)

- `F1` **Proof** — can this proof or proof step be shorter or more direct, closed by a standard
  tactic, or written with an existing lemma; does the previous proof still work?
- `F2` **Interface** — binders and implicitness (explicit / implicit / instance-implicit), argument
  order, section `variable`s and `variable ... in`, which hypotheses a declaration takes and in
  what form (not how general they are).
- `F3` **Registration** — should the declaration carry an attribute that registers it with
  automation (`simp`, `gcongr`, `grind`, `aesop`, `fun_prop`, `ext`, `norm_cast`, `simps` on
  a definition is F4), at what priority or rule strength; should it be an instance, global or
  local or scoped; is a linter suppression (`nolint`, `set_option linter...`) justified.
- `F4` **Derive, don't restate** — should this be generated (`simps`, `to_additive`, `to_dual`,
  `to_fun`; make it a structure so its projection lemmas come for free) or derived from its
  counterpart instead of written out.
- `F5` **Redundancy** — does it restate something existing, or something else in this PR; is
  anything unused or dead; does a rename or removal leave a deprecated alias; should existing
  declarations be deprecated.
- `F6` **Statement and API design** — is this the right statement, form or set of lemmas for users:
  canonical form, a different formulation (e.g. an ext lemma), extracting a definition or an
  intermediate construction, missing basic API lemmas, an upstream helper lemma, a different
  construction or approach, a definition's encoding (e.g. a `Set` rather than a predicate).
- `F7` **Generality** — is it stated at the right level of generality; can a hypothesis or typeclass
  be weakened or dropped; does it hold in an excluded case.
- `F8` **Naming** — are declaration, variable and hypothesis names conventional.
- `F9` **Formatting and file hygiene** — whitespace, indentation, line breaks, redundant
  parentheses, line length, import order, redundant imports, where a declaration or `namespace`
  sits in the file.
- `F10` **Documentation** — docstrings, module docs and code comments: complete, correct, clearly
  phrased, conventionally formatted; references and citations; TODOs.
- `F11` **Meta-code correctness** — does tactic, linter or metaprogramming code handle every input
  form, robustly, and do what it claims.
- `F12` **PR level** — is the change wanted and of library quality; should the PR be split or
  its scope changed; does the description explain it or link the discussion and related PRs; is
  there a test; does it coordinate with other PRs or projects; does it extend its change to the
  other places it applies.
- `CORR` **Mathematical correctness** — the build is broken, an axiom or `sorry` is introduced, a
  statement is false or does not say what it claims.

Boundary rules: redundant parentheses and layout are F9, not F2. A request to use an existing lemma
to shorten a proof is F1; a request to delete a declaration because it already exists is F5.
Whether a lemma should carry `@[simp]` is F3; where an attribute is written is F9. A missing
docstring is F10. A deprecation alias is F5. A request about the PR description or tests is F12.

## Rules

- Replies: label a reply on its own content. A reply that sharpens or restates the parent's request
  is an ask; one that only discusses is not.
- Do not look anything up. Label from the comment, its diff hunk and the PR title.

Write your output to the file path you were given, one JSON object per line, every comment in your
batch, in cid order. Validate it (every cid once, valid JSON, every key present, codes spelled
exactly as given). Then reply only with the counts of ask / not_ask and the counts by family.
