# Labelling rubric v2: which arm owns each reviewer comment, and which family of review work it is

You are labelling first-round reviewer comments on Mathlib pull requests. There are two questions
per comment:
1. Does the **written remit** of one of ten specialist reviewer arms ask the question this comment
   answers? (Not whether a model would find the issue.)
2. Which **family of review work** does the ask belong to, from a fixed codebook below?

The remits are in `reader_packet_arms.md`: each arm's one-line registry remit, the non-declaration
things it may look at, and the full system prompt it receives. Read all ten before you start.

Inputs (read ONLY the files you are given; do not open anything else in the directory or the repo):
- this rubric
- `reader_packet_arms.md`
- your batch file of comments, one JSON object per line: `cid`, PR number and title, `kind`
  (review | review_comment | issue_comment), review `state`, `author`, `path`/`line`,
  `reply_to_cid` (the comment it replies to, if any; replies stay in the same batch as their
  parent), `diff_hunk` (the code it is attached to, last ~600 chars), `body`.

## Output

For EVERY comment, one JSON object per line with exactly these keys:

- `cid`
- `is_ask`: `"ask"` or `"not_ask"`.
  - ask = the comment requests, proposes, or pointedly questions a change to the PR: code,
    statement, proof, attributes, names, docs, comments, imports, file layout, tests, the PR
    description, or the PR's scope. A ```suggestion block is an ask. A leading question is an ask
    ("does the old proof not work?", "Can `positivity` do this?", "What is the difference with
    `coe_sup`?" when it implies a redundancy). An objection to the PR's premise is an ask.
  - not_ask = approval, thanks, bors / `maintainer merge` / `!bench` commands, a reviewer
    retracting their own comment, social or scheduling messages, a reply that only discusses
    without adding a request, discussion of a bug in some other tool that asks the author for
    nothing, CI or merge-queue chatter.
- `owners`: list of arm ids whose written remit covers this ask — **non-exclusive**, include every
  arm whose registry line or system prompt would have it raise this ask. `[]` means no arm's remit
  covers it. For a not_ask, `[]`.
- `primary`: the single best owner, or `"none"`. For a not_ask, `"none"`.
- `fit`: for the primary owner, `"explicit"` (the remit names this kind of ask, or it is a direct
  instance of a named check) or `"stretch"` (the remit could be read to include it but does not say
  so). `"n/a"` when primary is none.
- `excluded_by`: list of arms whose prompt explicitly tells them to IGNORE this kind of ask
  although it is otherwise close to them (e.g. a prompt saying "ignore ... scope"). Often `[]`.
- `family`: exactly one code from the codebook below for an ask; `"n/a"` for a not_ask. Use `"NEW"`
  only when no family fits, and then fill `new_family_question`.
- `new_family_question`: when `family` is `"NEW"`, one generic sentence naming the kind of review
  work (no names from this PR); otherwise `""`.
- `question`: ONE generic sentence a reviewer checks when making this ask, stated so it applies to
  any PR — no names, lemmas or files from this PR. For a not_ask, `""`.
- `grain`: the smallest scope the reviewer had to look at to make this ask:
  `"line"` | `"declaration"` | `"declaration_group"` (several related declarations) | `"file"` |
  `"pr"` (the PR as a whole, its description, its relation to other PRs, or the library beyond
  the changed files). For a not_ask, `"n/a"`.
- `code_kind`: `"math"` (Mathlib mathematics), `"meta"` (tactic, linter or metaprogramming code),
  `"infra"` (scripts, config, CI, tests), `"prose"` (docstrings, comments, module docs, PR text).
- `note`: at most 25 words; required when primary is none, fit is stretch, or family is NEW.

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

- Judge each arm's remit as WRITTEN. Do not reason about what a capable model "would probably also
  notice". If the golf prompt says "shorter or more idiomatically" then an idiom ask is inside golf's
  remit too; if no prompt mentions a kind of ask, it is outside every remit even if it is easy.
- A comment whose ask spans two remits lists both in `owners`; `family` still takes one code, the
  one that names what the reviewer is asking for.
- Replies: label a reply on its own content. A reply that sharpens or restates the parent's request
  is an ask; one that only discusses is not.
- Do not look anything up. Label from the comment, its diff hunk and the PR title.

Write your output to the file path you were given, one JSON object per line, every comment in your
batch, in cid order. Validate it (every cid present exactly once, valid JSON, every key present,
arm ids and family codes spelled exactly as given). Then reply only with: the counts of ask /
not_ask, the counts by family, the count of asks with primary none, and every NEW family question
you used.
