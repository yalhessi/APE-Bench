# Reader rubric: why was this ask not reached?

You are one of two independent readers in a research study of Mathlib (Lean 4) code review. Several
automated reviewers reviewed real pull requests; afterwards the maintainers' actual round-1 review
comments ("asks") were compared with what each reviewer filed. This folder holds the asks that some
reviewers did not reach, with each reviewer's own record of its session. Your job: for each listed
(ask, reviewer) pair, say **by what mechanism** the reviewer missed it, from the evidence.

## Files

- `pairs.json`: the (ask, reviewer) pairs to label, one row each, with the PR.
- `pr<N>/asks.json`: that PR's asks: `ask_id`, the maintainer's text, its family and the family's
  definition, and which reviewers reached it.
- `pr<N>/pr.md` and `pr<N>/diff.patch`: the PR as the reviewers saw it.
- `pr<N>/<reviewer>/`: the reviewer's record.
  - Claude reviewers `X1`, `X2`: `findings.json` (what it filed), `notes.md` (its own object-by-object
    account of what it checked), `calls.jsonl` (every tool call it made).
  - The gpt reviewer `Grc1`: `transcript.txt` (every tool call and a truncated result, in order, then
    its submission), and `askwhy.txt` when present: the model's own answer, after the fact, to "did
    you notice this, and why did you not file it". **That answer is a self-report. Weigh it against
    the transcript; it is not evidence on its own.**

## Labels

For each pair, give **every mechanism that applies** from this list. They are not alternatives; a
miss usually has more than one. Do not pick a winner.

| label | applies when |
|---|---|
| `never_attempted` | no call, note or finding touched the declaration, file region or question the ask is about |
| `attempted_concluded_fine` | the reviewer read, searched or compiled the object or aspect and concluded nothing was needed |
| `attempted_opposite` | the reviewer proposed a different or opposite change to the same object (delete instead of improve, another name) |
| `verified_withheld` | the reviewer compiled or otherwise confirmed the asked change, or an equivalent, and did not file it |
| `filed_elsewhere` | the reviewer filed a finding on this object about something else |
| `try_it_not_tried` | the ask is decidable by one compile (does tactic X close it, does lemma Y apply), and nobody ran it |
| `knowledge_convention` | reaching the ask needs a convention or mechanism (an attribute, a naming rule, a file's local convention, a tactic's existence) the reviewer shows no sign of knowing |
| `analogue_not_compared` | reaching the ask needs comparing against an existing analogue (a sibling lemma, another file's API shape) the reviewer did not retrieve or read |
| `pr_level_or_history` | the ask is about the PR description, its scope, prior PRs or the author's intent |
| `not_reachable_from_code` | the reviewed code plus the library do not determine the ask; it needs discussion or intent the reviewer could not have had |
| `ask_unclear` | the ask text is too terse or context-bound to judge ("I disagree with this one") |

Also give `reachable`: `yes` if a reviewer with the reviewed code, the library and the tools could
have reached this ask; `no` if not; `unclear`.

## Output

Write `labels.jsonl` in this folder, one JSON object per pair, in the order of `pairs.json`:

```
{"ask_id": "...", "pr": N, "reviewer": "X1|X2|Grc1", "mechanisms": ["..."], "reachable": "yes|no|unclear",
 "evidence": "<= 40 words citing what you read: a transcript turn, a notes line, a finding index, a call>",
 "note": "<= 25 words, optional"}
```

Every pair gets a row. `mechanisms` is never empty: if nothing else fits, say which of the list is
closest and explain in `note`. Judge from the files here only; do not open, list or search anything
outside this folder, do not use git or the web. Scratch files go in `tmp/`. When done, reply with the
count of pairs labelled and the count of each mechanism.
