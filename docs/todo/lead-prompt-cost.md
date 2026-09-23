# Lead-mode prompt cost — one section is 43.6% of the prompt and 95% of it is a re-send

**Status** — **closed 2026-09-15.** Measured over three repetitions each: billed $13.44 -> $7.26
(46%), recall unchanged within noise. See `docs/research/batching-and-prompt-repair-2026-09.md`.
The finding worth keeping is that the saving did **not** come from prompt volume: the arms' 73.8%
volume cut bought 9.9% of arm spend, and the money was in the coverage floor (203 work units ->
92), which is the batching entry, not this one.
**Cost** — no spend to measure; one rep to confirm the fix changes nothing else
**Answer to the question asked** — the dominant part is *not* the instructions, the checklist or the
schema. It is `### Exact changed fragments`.

## Motivating example

`pr5_A_lead_heldout12_v2_rep1`, the 320 arm jobs that actually ran: 6,499,634 rendered prompt
characters, of which **`diff_fragments` is 2,834,441 — 43.6%**, and **61.8% of prompt-attributable
billed spend**. Replicated at 44.0% and 43.6% on reps 2 and 3.

Grouping hunk strings by PR: 2,792,993 hunk characters come from only **126,760 characters of
distinct hunk text**. So 2,666,233 characters — **41% of the entire rendered prompt volume of the
run** — are re-sends of a block already shipped to another job for the same PR.

For the generalist the mean per-target fragment block is 5,361 chars against a 236-char base region
and a 319-char reviewed region: **the diff is 10× the code it is a diff of.**

**PR 33149 is 48% of the run's billed cost** ($6.1415 of $12.8038). It has one changed file, 108
work units, and across all 120 executed jobs there is exactly **one distinct hunk string of 17,303
characters**, carried by every one of them — a 106:1 ratio of pasted diff to reviewed code, attached
to declaration, command, module_doc and namespace targets alike. Each of those jobs reviews exactly
one declaration averaging 163 characters.

## The cause, and the counterfactual

`change_graph.py:425,453` sets `diff_fragments` to the raw `@@` hunks covering the target's changed
ranges, so on a single-hunk file every target inherits the whole file diff.

Replacing each fragments block with `difflib.unified_diff(base_region, reviewed_region, n=3)` over
the 320 executed jobs: **2,792,993 → 280,824 characters** (3,210/target → 323/target), removing
89.9% of the section, 1,003,863 tokens, and **$2.04 of the run's $12.80 arm-billed cost — 16.0%.**

`review_overlay._pretty_diff` (`review_overlay.py:333`) already states the defect verbatim — "a
fragment can straddle two declarations, and the whole point of a target is that it is not a
fragment" — but it is an analysis renderer reached from `report.py:436` and **has never been on the
prompt path**. It is a precedent for the technique, not a fix already built.

## Three things this rules out

**Caching does not absorb it.** Turn-1 `cached_tokens` is a flat 3,584–4,608 across arms and does
not track system-prompt size; the user prompt diverges at the `Change ID (copy exactly):` line,
which precedes the fragments block. Turn 1 is 42.0% cached, turn 2 68.5%, turn 5 89.4% — the
run-wide 71.8% hit rate is within-conversation re-sending, not cross-job sharing. Turn-1 uncached
input is 1,888,478 tokens and a regression on section character counts (n=321, R²=0.990) attributes
**1,116,264 of them to hunk text — 59% of all uncached turn-1 tokens.**

**Cutting the instructions is the wrong lever, but not because they are free.** A user-prompt token
costs **4.70×** a token inside the cached prefix ($2.064/1M vs $0.439/1M at 3.51 calls/job). The
tool definitions genuinely are cheap — four tools (`code_hover`, `code_goto`, `get_lean_goal`,
`proof_profile`) ship 1,009,781 characters of schema for **12 calls in 321 sessions** and cost about
$0.13, so drop them for attention-menu reasons, not for the bill. But `user_contract_duplicate` —
the generalist's own system prompt pasted into its user message, 507,906 chars — is paid at the
*user* rate, so "the contract blocks are nearly free" is false for that block.

**The extra diff is not merely redundant, it is unusable.** All **268 of 268** candidates in the run
have `primary_change_id` and every `change_id` inside their own work unit — the contract rejects
anything else — so the other 107 declarations in 33149's pasted diff are text the job is forbidden
to act on. Meanwhile 265 of 321 sessions called `file_read` on one of the PR's changed files anyway.

## The ceiling

Output tokens are **31.2%** of lead-mode billed spend and the whole rendered prompt across all turns
is 29.6%; tool results re-sent across turns are most of the rest (`file_read` alone returned
1,957,106 chars, 52.2% of tool-result volume). Reconstruction matches the manifest to 0.44%. So a
perfect prompt fix caps at roughly two-thirds of the bill, and lead is ~17× solo mostly because it
runs 321 sessions to solo's 12.

## What would close it

1. ~~Bump the renderer version and make both changes together.~~ **Done in `9d4de8f`.** Measured on
   `dev-medium-0.3.0`: fragment characters 2,583,336 → 155,178 (94.0%); arm target-block volume over
   1,391 enumerated invocations 16,452,187 → 4,313,256 (73.8%); generalist user prompts at
   `candidate-prompt/13` 4,245,015 → 1,548,784 (63.5%, and 78.6% on 33149). The structural-target
   case turned out to be narrower than feared: only *import* targets lack regions (17 of 508 targets,
   2,195 characters), and they keep the raw hunk.
2. **Re-render the release at `candidate-prompt/13`** — `rerender_release --parent
   inputs/pr_review_v4/releases/dev-medium-0.3.0 --renderer-version candidate-prompt/13`. This is the
   step that has a cost beyond prompt size: `renderer_version` sits in the work-unit identity, so
   every `work_unit_id` changes and every `wu:` join in the recorded runs and audits stops resolving.
   Decide deliberately whether to move the evaluated configs onto the new release or keep the
   generalist at /12 until the next experiment needs a fresh release anyway.
3. **Confirm with one rep** against the per-obligation spine — especially 33149, where the removal is
   largest — and report `issue_recall` and control emission beside the cost. Prompt volume is
   measured; the billed effect is not. The projection from the section's measured share is ~16% of
   lead spend, and that number is not yet earned.
4. Re-measure the lead/solo ratio afterwards. If it moves from ~17× to ~14×, that is the whole
   prompt-side lever and any further reduction has to come from the schedule.

## Risk

The clean test of "is the whole-file diff load-bearing" is an A/B on one rep, because "no candidate
outside its targets" is also consistent with the extra diff being used as orientation. Run it per-PR.

One measured regression to keep in view: three documentation PRs render marginally *larger* under
the scoped section — 33304 +2.7%, 33305 +2.3%, 33315 +1.0%, a few hundred characters each on the
smallest prompts — because a region diff re-emits context a tight `@@` block did not. Two of those
are the control PRs. `min(raw, scoped)` would buy it back at the cost of the property that makes the
block trustworthy, so it was not taken; if control emission moves in the confirming rep, this is the
first thing to look at.

## Record correction this forces

`dead-ends.md` says "fanout costs $0.085/job against lead's $0.040 (arms are top-level tasks, so
they lose the nesting/caching benefit)". Those are **nominal vs billed**, and the mechanism is
backwards — fanout's cache hit rate is **80.2% against lead's 71.2%**. See
[record-corrections.md](record-corrections.md).
