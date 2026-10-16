<!-- Step-4 audit brief (PROTOCOL.md, step 4 amendment). Rendered with {PACKET}; the two lines above the
first heading are dropped when rendered. -->
# Audit: did each check follow its rule's literal check?

Working directory: `/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/ask-reading`.

Earlier agents each ran one written rule's **check** at a place in a Mathlib pull request and wrote a verdict,
`departs` or `conforms`, with evidence. Your job is to say, row by row, whether the verdict follows the rule's
check **as written**, or a looser reading of it. You are not asked whether the rule is a good rule, whether a
maintainer would want the change, or whether the verdict is right in some broader sense.

**Your input** is `{PACKET}`: a JSON list, one entry per row, with the rule's `applies_to`, `trigger`,
`required`, `check` and `not_when` text, the row's `verdict`, `evidence`, `calls` and `compiled_candidates`,
and `reviewed_code`, the path of the file as the pull request leaves it. You may read the packet and the
`reviewed_code` files (plain file reads). Read nothing under `results/`, `docs/` or `inputs/`, and run no
build or Lean command.

**Per row, decide `reading`:**
- a `departs` row is `literal` if the compiled or found candidate is a form the check names and does what
  the check asks; `looser` if it departs only under a broader reading: another combining form than the
  check lists, two calls where one is asked, or a judgement the check leaves open (for example P040's
  "reads no worse") that the evidence does not settle;
- a `conforms` row is `literal` if the check was done as described; `incomplete` if a form the check names
  was not tried.
Where the check's wording itself is open (it says "e.g." or lists examples), read the list as examples and
judge by the check's stated aim; say so in `why`.

**Per `departs` row, also record `longer`:** `true` if the departing candidate is longer, in characters, than
the code it replaces; `false` if it is not; `null` if the row has no candidate code (most search rules and the
read rules P048, P084) or the evidence does not let you tell. Compare the candidate as quoted in the evidence
with the code it replaces, which you read in `reviewed_code`. `longer` changes no verdict; it is recorded.

**Write** one line per row, in packet order, to
`/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/ask-reading/results/pr_review_v5/probes/stage-h-departures-2026-10-16/audit.jsonl`:
`{"item", "rule", "verdict", "reading": "literal|looser|incomplete", "longer": true|false|null, "why": "<one or two sentences>"}`
(`verdict` copied from the packet). Do not commit. Reply with the counts of each `reading` and every row you
marked `looser` or `incomplete`, one line each.
