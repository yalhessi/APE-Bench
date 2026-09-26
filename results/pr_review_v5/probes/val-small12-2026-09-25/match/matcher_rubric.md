# Matching reviewer findings to maintainer asks

You are judging, for a research study, which review findings reach which real maintainer requests
on five Mathlib pull requests. One anonymous reviewer, `R1`, reviewed each PR without
seeing the maintainers' comments. 
**Inputs.** Read only the files named in your task:
- `asks_pr<N>.json`: the maintainers' first-round asks on PR N. Each has:
  - an `ask_id`;
  - the file `path`;
  - `code_at_comment`: the code the comment is attached to, ending at the commented line;
  - the `comment`;
  - the comment it replies to, if any.
- `R1_pr<N>.json`: the reviewer's findings, a list, indexed from 0.

## For every ask

Choose one value:

| value | when |
|---|---|
| `reached` | Some finding asks for the same change on the same thing, or for a change that, if the author made it, would satisfy the maintainer's ask. Wording may differ. "Use the existing `foo`" reaches "this is `foo`". |
| `partial` | Some finding is about the same thing and the same kind of issue, but asks for a different change that would not satisfy the maintainer. For example, both say the name is wrong but propose different names, and the maintainer's reason is absent. |
| `no` | Anything else. |

Also give the index of the best finding, or `null`.

Judge only whether the finding would lead the author to the maintainer's change. Do not judge
whether the finding is otherwise good.

## For every finding that reaches no ask

Count it as unmatched. Do not judge it.

## Output

Write `matches.json`, a JSON object with two keys:
- `"asks"`: a list with one entry per ask, of the form
  `{"pr": N, "ask_id": "...", "R1": "reached|partial|no", "R1_finding": i|null, "note": "<= 20 words"}`.
- `"unmatched"`: `{"<pr>": {"R1": <count of R1 findings reaching no ask>}}`.

Then reply with, pooled over PRs, the counts of `reached` and `partial`, and the
unmatched counts.
