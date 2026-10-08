# Matching proposed changes to maintainer asks

You are judging, for a research study, whether proposed changes reach real maintainer requests on
Mathlib pull requests. For each maintainer ask, fifteen anonymous outputs, `O1` to `O15`, each
propose one change at the ask's place, without having seen the maintainer's comment. Some outputs
say `none`. Their labels are shuffled per ask, so `O1` on one ask has nothing to do with `O1` on
another.

**Inputs.** Read only the files in your folder:
- `asks_pr<N>.json`: the maintainers' first-round asks on PR N, a list. Each has an `ask_id`, the
  file `path` (null for a comment on the pull request as a whole), `code_at_comment` (the code the
  comment is attached to, ending at the commented line; empty when there is none), the `comment`,
  the comment it replies to (`in_reply_to`), if any, and `outputs`, the fifteen proposed changes.

## For every ask, and each output

Choose one value:

| value | when |
|---|---|
| `reached` | The output asks for the same change on the same thing, or for a change that, if the author made it, would satisfy the maintainer's ask. Wording may differ. "Use the existing `foo`" reaches "this is `foo`". |
| `partial` | The output is about the same thing and the same kind of issue, but asks for a different change that would not satisfy the maintainer. For example, both say the name is wrong but propose different names, and the maintainer's reason is absent. |
| `no` | Anything else, including `none`. |

Judge only whether the output would lead the author to the maintainer's change. Do not judge
whether the output is otherwise good.

## Output

Write `matches.json`, a JSON object with one key, `"asks"`: one entry per ask, of the form
`{"pr": N, "ask_id": "...", "O1": "reached|partial|no", ..., "O15": "...", "note": "<= 25 words"}`.

Then reply with the counts of `reached` and `partial` over all outputs.
