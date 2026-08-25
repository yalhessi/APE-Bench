# The v4 judge prompt is not the v7.1 rubric it claims to be

*2026-08-05, prompted by the question "is the judge prompt different from the one used
before, and would including the review target code help?" Both answers are yes, and the
omissions explain the R0 failures.*

## The version string overstates fidelity

`semantic_judge.JUDGE_VERSION = "v4-semantic-v1-v7.1-rubric"` implies the v3-era v7.1
rubric was ported. It was reduced. Comparing against
`src/datasets/legacy/pr_review_v3/judge.py` (`JUDGE_PROMPT_VERSION = "v7.1"`):

### Context fields dropped

| field | what it gave the judge |
|---|---|
| `pr_summary` | PR-level context |
| `anchor_desc` | where the gold intervention anchors |
| `pred_loc`, `line_gap` | the candidate's location and its distance from the anchor |
| `rationale`, `rationale_source` | **why** the maintainer asked |
| `evidence` | the candidate's verified edit |

v4 shares exactly **one** field with v7.1 (`suggested_fix`). Everything else was renamed
or removed. **Neither prompt ever showed the judge the reviewed code itself** — v7.1 at
least supplied a PR summary and the candidate's verified edit; v4 supplies neither.

### Rubric clauses dropped

1. *"A finding about a DIFFERENT aspect of the same lines (**e.g. proof style when the ask
   is a rename**) does NOT [issue-match]."*
2. *"A vaguer fix that would not by itself produce the asked transformation is
   **issue_match only**."*
3. *"compare the CHANGES (the ask's transformation vs the finding's fix/edit), allowing
   different wording but the same result."*

v4 retained the no-change clause (v7.1's own correction) and the one-line "A different fix
may still issue-match", but not the worked negative example, not the explicit
issue-only rule, and not the instruction to compare transformations directly.

## Each omission maps onto an observed R0 failure

| R0 finding | dropped element that would address it |
|---|---|
| **Stable task-arm error** on `…e373aeb72a4b`: gold asks for a **proof** change, candidate asks for a **rename**; judge voted `issue=True` 3/3 | clause 1 is *literally this case*, in the same rename/proof-style vocabulary |
| **`gpt_5.2` collapsed the two levels** — `issue==resolution` on 18/18 pairs, never once `issue=True, resolution=False` | clause 2 is the explicit instruction to produce exactly that verdict |
| **2 bimodal obligations** (judge splits its own samples 2/3), e.g. "the split is dead code" vs "the empty-branch binder should be `rfl`" | the judge is deciding whether two *prose descriptions* concern the same code aspect **without ever seeing the code**; missing `rationale` compounds it |

The `gpt_5.2` result should be re-read in this light. I previously described its behaviour
as a prompt-adherence defect; that is too generous to the prompt. The instruction it
failed to follow **is not in the prompt** — v4 dropped it. A stronger model reading the
reduced rubric literally collapses the levels, which is arguably the correct reading of
what it was actually given.

## The suggested fix is feasible and cheap

The reviewed code for every judged pair is already carried by the release — the
obligation and candidate share `change_ids`, and the change graph holds each target's
`reviewed_code`. Measured over the 18 R0 pairs:

- code available for **6/6** overlap targets
- size: median **317 chars (~79 tokens)**, max 1214 chars (~303 tokens)

Injecting it is a rendering change, not a new data dependency, and it is affordable inside
the current 4000-token budget.

## Proposed `v8` rubric (requires re-baselining — not a quiet edit)

Restore what was dropped and add the code:

1. **The reviewed code of the overlapping change target(s)**, truncated with an explicit
   marker. This is what lets the judge check whether two prose descriptions name the same
   aspect instead of guessing.
2. **The gold rationale**, where the obligation carries one.
3. **The candidate's proposed edit / verified edit**, where present — v7.1 had it.
4. **Clause 1** (different aspect of the same lines, with the rename-vs-proof-style
   example).
5. **Clause 2** (a vaguer fix is `issue_match` only) and **clause 3** (compare the
   transformations).

## Discipline this must follow

The project has done judge revisions before (v6 → v7 → v7.1), each time by freezing the
old judge and its caches for historical comparability. The same applies:

- **New version string** (`v4-semantic-v2-v8-rubric` or similar). The current
  `v4-semantic-v1-v7.1-rubric` should also be corrected — it misstates what it is.
- **All cached verdicts are invalidated.** `_pair_key` includes `judge_version`, so this
  happens automatically; nothing is silently reused.
- **Re-baseline before quoting anything**: re-score the R0 pair set under v8 and re-run
  the bimodality measurement. The ~11% bimodal rate and the ±12.5pp-at-n=8 noise floor are
  properties of *v7.1-as-implemented*, not of the judge in general.
- **Re-run the `gpt_5.2` comparison under v8.** If clause 2 restores two-level behaviour,
  `gpt_5.2` becomes the better judge on every axis measured — deterministic (0/18 splits),
  correct on the hard pair, and correctly separating the levels. That would reverse the
  "keep `gpt_5_mini`" recommendation.
- **Do not re-score frozen historical results under v8.** Phase 9 and earlier were
  measured under v7.1-as-implemented and stay that way; v8 numbers are comparable only to
  other v8 numbers.

## Expected effects, stated in advance

Writing these down before the run so the outcome cannot be rationalised afterwards:

- The `…e373aeb72a4b` stable error should flip to `issue=False` (clause 1 addresses it
  directly).
- Bimodality should **fall** on the two contested obligations if the split was caused by
  missing code context, and **persist** if those asks are genuinely ambiguous. Either
  outcome is informative; persistence would mean the pairs need a human ruling rather than
  a better prompt.
- `issue=True, resolution=False` verdicts should **appear** for `gpt_5.2`, where they were
  0/18.
- Absolute issue recall may move in either direction. It is not a quality signal — it is a
  definition change, and that is precisely why history is not re-scored.
