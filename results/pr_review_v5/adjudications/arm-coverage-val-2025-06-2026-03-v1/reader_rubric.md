# Labelling rubric: does the specialist-arm division own this reviewer comment?

You are labelling first-round reviewer comments on 49 Mathlib pull requests (a validation set).
The question is NOT whether a model would find the issue. It is whether the **written remit** of one
of ten specialist reviewer arms asks the question this comment answers. The remits are in
`reader_packet_arms.md`: each arm's one-line registry remit, the non-declaration things it may
look at, and the full system prompt it receives. Read all ten before you start.

Inputs (read ONLY these three files; do not open anything else in this directory or the repo):
- `reader_rubric.md` (this file)
- `reader_packet_arms.md`
- `reader_packet_comments.jsonl` — one comment per line: `cid`, PR number and title, `kind`
  (review | review_comment | issue_comment), review `state`, `author`, `path`/`line`,
  `reply_to_cid` (the comment it replies to, if any), `diff_hunk` (the code it is attached to,
  last ~600 chars), `body`.

For EVERY comment, output one JSON object per line with exactly these keys:

- `cid`
- `is_ask`: `"ask"` or `"not_ask"`.
  - ask = the comment requests, proposes, or pointedly questions a change to the PR: code,
    statement, proof, attributes, names, docs, comments, imports, file layout, tests, the PR
    description, or the PR's scope. A ```suggestion block is an ask. A leading question is an
    ask ("does the old proof not work?", "Can `positivity` do this?", "What is the difference
    with `coe_sup`?" when it implies a redundancy).
  - not_ask = approval, thanks, bors / `maintainer merge` / `!bench` commands, a reviewer
    retracting their own comment, social or scheduling messages, a reply that only discusses
    without adding a request, discussion of a bug in some other tool that asks the author for
    nothing.
- `owners`: list of arm ids whose written remit covers this ask — **non-exclusive**, include every
  arm whose registry line or system prompt would have it raise this ask. `[]` means no arm's remit
  covers it. For a not_ask, `[]`.
- `primary`: the single best owner, or `"none"`. For a not_ask, `"none"`.
- `fit`: for the primary owner, `"explicit"` (the remit names this kind of ask, or it is a direct
  instance of a named check) or `"stretch"` (the remit could be read to include it but does not say
  so). `"n/a"` when primary is none.
- `excluded_by`: list of arms whose prompt explicitly tells them to IGNORE this kind of ask
  although it is otherwise close to them (e.g. a prompt saying "ignore ... scope"). Often `[]`.
- `question`: ONE generic sentence a reviewer checks when making this ask, stated so it applies to
  any PR — no names, lemmas or files from this PR. E.g. "Should this lemma be registered with an
  automation attribute such as `simp`, `gcongr`, `simps` or `grind`?" For a not_ask, `""`.
- `grain`: the smallest scope the reviewer had to look at to make this ask:
  `"line"` | `"declaration"` | `"declaration_group"` (several related declarations) | `"file"` |
  `"pr"` (the PR as a whole, its description, its relation to other PRs, or the library beyond
  the changed files). For a not_ask, `"n/a"`.
- `code_kind`: `"math"` (Mathlib mathematics), `"meta"` (tactic, linter or metaprogramming code),
  `"infra"` (scripts, config, CI, tests), `"prose"` (docstrings, comments, module docs, PR text).
- `note`: at most 25 words; required when primary is none or fit is stretch — say what is missing.

Rules:
- Judge the remit as WRITTEN. Do not reason about what a capable model "would probably also
  notice". If the golf prompt says "shorter or more idiomatically" then an idiom ask is inside golf's
  remit too; if no prompt mentions a kind of ask, it is outside every remit even if it is easy.
- A comment whose ask spans two remits (e.g. "use the existing lemma and so golf the proof") lists
  both in `owners`.
- Replies: label a reply on its own content. A reply that sharpens or restates the parent's request
  is an ask; one that only discusses is not.
- Do not look anything up. Label from the comment, its diff hunk and the PR title.

Write your output to the file path you were given, one JSON object per line, all 144 comments,
in cid order. Then reply with: the counts of ask / not_ask, the count of asks with primary none,
counts by primary arm, and the 5 most common generic questions among primary-none asks.
