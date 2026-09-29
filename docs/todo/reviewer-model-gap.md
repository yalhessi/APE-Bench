# The reviewer-model gap: is the binding constraint the model, not the coordination?

**Status** — open, 2026-09-29; **corrected the same day** (second reading, below). Two cheap tests.
**Cost** — (a) free: Claude session time plus reviewed-workspace builds; (b) about $3 on `gpt_5.2`.

**Motivating example.** `results/pr_review_v5/probes/construction-demo-2026-09-29/`. On three
validation small12 PRs (34091, 30458, 32875), Claude reviewers with the pipeline generalist's own
brief, the arms' tools and a pass-0 PR model reached **5-6 of 11** asks, stably across two
replicates and two blind matchers. The pipeline's lead run on `gpt_5.2` reached **none** of the 11.
The pipeline's whole-PR solo baseline (`val-small12-2026-09-25/match_solo`) holds the same tools and
has no work units and no pruning. It reached **none** of the five asks that every Claude reviewer
set reached:
- three instance-binder asks on 34091;
- two "does the old proof work?" asks on 30458.

The design-level interventions tried since September (facet brief, hard cells, PR-level job,
constructions) each moved Claude's reach little. The difference between Claude and `gpt_5.2` on
these asks is the whole distance.

**The causes this does not separate:**
- **recall:** every PR is inside Claude's training window (June 2026 cutoff);
- **the model:** `gpt_5.2` with reasoning off (`reasoning-in-the-arms.md`: 0 reasoning tokens in
  2,857 of 2,857 arm attempts) against Claude;
- **the harness:** `ape_agent` against a Claude agent with a shell;
- **the packet and brief:** X had the pass-0 model and the generalist checklist, while solo had the
  solo brief and no model.

## The two tests

1. **After the cutoff (free).**
   - Draw about five PRs created after 2026-06 from the PR store that hold round-1 asks of the
     binder, pre-PR-proof or golf kind, and build their reviewed workspaces.
   - Run the construction demonstration's X condition twice, with the same matchers.
   - If Claude reaches such asks at a similar rate, the gap is ability or harness, not recall.
2. **The pipeline's model on the same packet (~$1).**
   - Run `gpt_5.2` through `cli run` (the solo scaffold) on the three PRs, with the X brief and the
     pass-0 model as its prompt, reasoning off and then on.
   - If it reaches the binder and pre-PR-proof asks, the packet or brief matters.
   - If it does not, the model or the harness does.

**What would close it.** A small table of reach on the same asks, by model × brief/packet ×
window, with two runs a cell. The next generator change should then be decided by which factor
carries the gap. If it is the model, coordination designs should be measured on the model that will
run them, before any more are built.

## Corrected, second reading (2026-09-29)

**Where the pipeline lost the five asks.** Every one was lost at an arm's decision, not by a missing
arm:
- On 34091, `generality` and `style` ran on the unit and declined. `style` checked line breaks and `by`
  blocks.
- On 30458, the generalist, `generality` and `style` ran and declined, and the lead pruned the two
  proof arms.
- Every arm that ran held `lean_verify_edit`, and none replayed a proof or compiled a binder change.
- Claude sessions did both unprompted.

So the gap is the reviewer's initiative to construct. That is a property of the model and harness,
with the packet as a possible factor. The title's "not the coordination" was not tested: coordination
did not vary in the probe.

**Test (b), restated.** Run `gpt_5.2` through the solo scaffold on the three PRs under three prompts,
two runs each:
1. the plain brief;
2. the plain brief with the pass-0 model;
3. the construction briefs, pass 3 then pass 4.

Use the same matchers and the 11 asks. This separates the packet from the model, and it tests the
constructions on the reviewer that does not construct. If (3) reaches the binder and pre-PR-proof asks
and (1) does not, the design's construction protocol is worth building for the pipeline's model.

**Test (a) first.** Test (a) builds a post-cutoff probe set, so that a Claude probe carries no recall
caveat.

## Test (a) done (2026-09-29): Claude's in-window reach is not mainly recall

`results/pr_review_v5/probes/postcutoff-2026-09-29/` ran on 10 PRs created 2026-07..08 (sealed as
`probe-2026-07-08-v1`), 6 of them with round-1 asks. The construction demonstration's control, the
same brief, packet and tools, reached asks at 0.47 per session, against 0.44 and 0.59 in-window
under the same two matchers. So `r` is 1.07 and 0.79, and the pre-set reading is "not mainly recall"
on both. Matching was stable: 64 of 64 in-window cells were re-judged the same reached-or-not.

Two limits. The mixes differ: post-cutoff asks are naming and design, in-window ones proof and
interface. And the set is small: 16 asks.

So the five asks the pipeline missed and every Claude set reached are more likely capability,
harness or packet than memory. **Test (b) is now the open step, and the post-cutoff set is where to
run it:** neither model can have seen those PRs, so `gpt_5.2` against Claude there is a clean model
comparison.

## Test (b) done (2026-09-29): the model gap is real, and a construction brief does not close it

`results/pr_review_v5/probes/gpt52-postcutoff-2026-09-29/`. Six post-cutoff PRs, 16 asks, two blind
matchers in full agreement. With the same brief, pass-0 model and tools:
- Claude reached 0.47 per session, and `gpt_5.2` (as the pipeline runs it) reached 0.12, so
  `q = 0.27`: markedly less.
- On the 9 substantive asks in the construction passes' scope, Claude reached 0.44 and `gpt_5.2`
  0.00.
- The construction brief tripled `gpt_5.2`'s compiles (2.2 to about 6.5 a session, against Claude's
  about 8) and reached 0.06. So the gap is in what the reviewer concludes and asks, not in whether it
  compiles.
- $1.69 billed.

**What would close this entry:**
- **(c) Model against harness.** Run the solo task under the `claude_code` scaffold (the existing
  B/C pair) on the post-cutoff set. That is Claude through the pipeline's own task, submission contract
  and tools. If it reaches like the Claude probe sessions, the harness is not the constraint and the
  model is.
- **(d) Reasoning.** `gpt_5.2` with reasoning on, on the same set. The in-window twin showed no gain
  at 3.8x the cost.

Both are single-digit dollars.

## Where test (b)'s difference comes from (2026-09-29, transcript inspection)

The inspection section of `results/pr_review_v5/probes/gpt52-postcutoff-2026-09-29/README.md` has the
counts. The gap sits in what the reviewer compares the PR against:
- Claude made about 22 lookups of comparison objects a session, and `gpt_5.2` about 2, on all six PRs.
  PR-side reading was about equal.
- Of the substantive asks `gpt_5.2` missed, three never had their evidence retrieved (`cat_disch`
  defaults on two definitions, the `_anti` name). Three had it in view in at least half the sessions
  and were not raised (`@[to_additive]`, `homMk`, the `NeBot` case split).
- The construction brief raised variant compiles to near Claude's rate and left lookups at 2.
- Every `gpt_5.2` session stopped on its own, well under its cap, and wrote no text between calls.

So the sources are retrieval breadth and inference from context. Both fit reasoning off and a weaker
model equally well. Test (d), `reasoning_effort=high` on G, separates them, with its threshold stated
in the README.

The test (b) paragraph above says "the same tools". That is corrected there: Claude had `file_search`
in place of the Lean navigation tools, and the gap survives without it.

## The arms condition (2026-09-29): the pipeline's structure adds nothing on unseen PRs

The pipeline in lead mode (ten arms, work units, the generalist floor) ran twice on the same six PRs,
at $5.90 and $5.88. Two blind matchers agree on all 96 cells:
- Its reach is 0.12, the same as `gpt_5.2` solo (0.12), against Claude's 0.47.
- On the substantive asks it is 0.00, with no partial either.
- It reached only the unused import and the title's missing word. The gate published neither.

By the pre-registered rule the structure does not help here, and the model dominates. The context
traces add one thing the solo inspection could not show. Some arms did retrieve the comparison object,
the parent's `isoMk` and `finprod_nonneg`, and asked only their own arm's question of it. So retrieval
breadth alone is not the lever.

The test (b) matcher inputs had lost every `gpt_5.2` finding's location. Re-matched on corrected inputs,
test (b)'s numbers are unchanged. The fix and a refusal are in `build_match_inputs.py`.

**Where this leaves the entry.** On unseen PRs the binding constraint on substantive asks is the
reviewer. It is neither the brief, the construction protocol nor the pipeline's structure. The one
untested lever on the pipeline's own model is reasoning: test (d), stated with its threshold in the
probe README, about $3. Claude inside the pipeline's structure is the other untested cell. It needs an
Anthropic provider the clients do not have.
