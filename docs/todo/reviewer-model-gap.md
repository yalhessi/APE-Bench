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
billing $2.81 and $2.52 ($5.90 and $5.88 nominal). Two blind matchers agree on all 96 cells:
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

## Test (d)'s calibration (2026-09-29): on one PR, high effort closes most of the gap there

On 43192 (four asks), one session per effort, two blind matchers in full agreement:
- reasoning off reached 0.25;
- medium reached 0.25;
- high reached 0.75;
- Claude reached 1.00.

Medium and high both looked outward as much as Claude, with 28 and 31 comparison lookups against 3.
Only high concluded: it reached both `cat_disch` asks. Neither effort retrieved `homMk`, because each
searched with the PR's own spelling. So on this PR the reasoning setting, not the model, carries most of
the gap. That is provisional on one PR, and it comes at about 30 times the reasoning-off cost. The
six-PR runs (about $20-25 for two) would test it. The details are in the probe README.

## Reproducing the experiment on other sets (the user, 2026-09-29; for a fresh session)

*"We ideally want to be able to reproduce this experiment on a number of different sets: the dev set
from Dec 2025, 12 validation from Jan 2026, and any other interesting sets."* Every result above rests
on `probe-2026-07-08-v1`: 6 PRs and 16 asks. That set is a sealed draw of 10 from a frame of 1,075
eligible PRs created 2026-07..08, so it is not the remainder of anything. The PR store ends on
2026-08-31, so July and August 2026 are all the post-cutoff months held.

| set | created | PRs | what exists for this experiment |
|---|---|---|---|
| dev (`dev-medium-0.3.0`) | 2025-12-18..31 | 16 | pipeline runs throughout; v4 gold, not asks; tuned on |
| validation small12 (`val-2025-06-2026-03-v1`) | 2025-06..2026-03, about one a month | 12 (11 build) | lead and solo runs, 30 asks matched; Claude sessions on 3 PRs |
| test small12 (`eval-2025-06-2026-03-v1`) | same window | 12 | sealed and run once, so not a probe set |
| post-cutoff frame, not yet drawn | 2026-07..08 | 1,065 | a second sealed draw, excluding the first 10 |

The validation set is not a January 2026 set. January was the first window considered in
`eval-set-selection.md`; the sets were drawn over ten months instead.

**Leakage.** Only the post-cutoff frame is unseen by Claude, whose cutoff is June 2026. On the dev
and validation sets Claude may have seen the PRs and the comments. Test (a) found its reach there is
not mainly recall (79-107% of the post-cutoff rate), so those sets stay informative with that caveat.
`gpt_5.2`'s training cutoff is not recorded here, and it has to be stated before any comparison on
2025 PRs (`docs/plans/2026-09-25-align-decisions-with-maintainers.md`).

**What the tooling lacks.** `results/pr_review_v5/probes/gpt52-postcutoff-2026-09-29/` is hard-coded
to one set:
- the PR list, the release, the ask manifest and the Claude session directory are constants;
- Claude's sessions are driven by hand, as subagents with the `cli tool` wrapper, from a chat session;
- the asks come from two readers per set. The dev set has gold obligations instead, in another form.

A set-parametrised harness needs:
- one set spec: release, PRs, ask manifest;
- per-set gpt configs, which are two-line `extends` files;
- a scripted Claude driver, possibly Claude Code's headless mode;
- matching and unblinding that take the spec.

**Cost per 12-PR set, from this probe:**

| condition | cost |
|---|---|
| `gpt_5.2`, reasoning off | about $0.6 billed a run |
| lead mode | about $5 a run |
| high effort | about $20 a run |
| Claude sessions and matchers | session time only |

**The procedure as run on the post-cutoff set, step by step** (each step was committed before the next):
1. **The set.** A sealed draw (`projections.frame`), and a release outside
   `inputs/pr_review_v4/releases/` so it stays out of `scored_pr_numbers()`. Restore the base snapshots
   (`restore_bases.py`) before building the reviewed workspaces.
2. **Packets** (`make_packets.py`), one per session:
   - `brief_X.md`, verbatim from the construction demonstration;
   - `pr.md` and `diff.patch`;
   - `model.md`, from `build_model.py <release> <out_dir> <prs>`, which reads input and derived files
     only;
   - `./ptool`, from `bin/ptool.template`, which calls `cli tool` against the reviewed workspace and
     logs every call through `log_call.py`.
3. **Claude sessions.** Two per PR, each a `claude-opus-5-5` subagent spawned from a chat session.
   The rules are instructions, checked afterwards by `audit_transcripts.py`: read only the packet,
   call tools only through `./ptool`, keep temporary files in `tmp/`, no git and no web. Each session
   writes `findings.json`.
4. **Asks, only after every session ends.**
   - `extract_draw_feedback.py <draw>` extracts round-1 feedback; it refuses test-set PRs.
   - Two blind readers label it with `reader_rubric.md`: is it an ask, its val1000 family, its grain.
   - Only the asks both readers agree on go into `match/ask_manifest.json`.
5. **`gpt_5.2` conditions.** `cli run` solo with `task_config.system_prompt_file` (`brief_G.md`) and
   `context_file` (the pass-0 models), plus lead runs. `--resume` continues an interrupted run.
6. **Matching.**
   - `build_match_inputs.py` strips findings to target, claim, change and severity, redacts cues and
     shuffles labels under a sealed blinding.
   - Two blind matcher subagents judge, and `audit_matchers.py` checks they stayed in their folders.
   - `unblind.py` applies the rule stated before the runs.

Steps 2-6 hard-code the probe's release and paths. Step 4's extractor needs a sealed draw, so the dev
set, a v4 release, needs a by-PR-list variant. Step 3 is reproducible as a procedure, not as a script.

## The experiment on three sets (2026-09-29, through the probe harness)

`docs/plans/2026-09-29-probe-harness.md`; each set's README has its rule, stated before matching, and
its result. Per-session reach, the two matchers' values:

| set | PRs created | asks | Claude (X) | `gpt_5.2` solo (G) | pipeline (L) | `q = G/X` | `L - G` |
|---|---|---|---|---|---|---|---|
| post-cutoff `probe-2026-07-08-v1` | 2026-07..08, unseen by Claude | 16 on 6 PRs | 0.47 | 0.12 | 0.12 | 0.27 | 0.00 |
| validation small12 | 2025-06..2026-03 | 30 on 8 | 0.48 / 0.50 | 0.13 | 0.27 | 0.28 / 0.27 | +0.13 |
| dev `dev-medium-0.3.0` | 2025-12 | 47 on 12 | 0.67 / 0.61 | 0.13 / 0.18 | 0.29 (31 asks) | 0.19 / 0.30 | +0.15 / +0.08 |

- **The model gap replicates on every set.** `gpt_5.2` with reasoning off reaches a fifth to a third
  of what Claude reaches with the same brief, packet and tools: markedly less by test (b)'s rule,
  on both matchers, three times.
- **The structure's contribution follows the ask mix.** It is nothing on the post-cutoff set, whose
  asks are naming and design. It is +0.13 on validation, all from proof asks. On dev it is +0.08 to
  +0.15, from naming and documentation, where the naming arm was tuned. The gate publishes almost
  none of it (0.00-0.07).
- **Claude's reach rises into the window:** 0.47 post-cutoff, about 0.49 on validation, about 0.64 on
  dev. The dev set is also the one the record knows best, so recall and ask mix are not separated.

**What this leaves open.** High reasoning effort on `gpt_5.2` reached 0.75 of four asks against
0.25 on one post-cutoff PR (test (d)'s calibration). That is the one lever measured to move the
model half. It costs about $3.74 billed per session on a large PR, so one high-effort run per set is
about $20-60. It has run on one PR only, and it needs the user's go-ahead.

## Reasoning on, all three sets (2026-09-30): it closes part of the gap

One high-effort run per set (`reasoning_effort: high`, condition G's brief and pass-0 model),
$77.05 billed in all. Two new blind matchers per set re-judged X, G and Gr1 together. Per-session
reach, the two matchers' values:

| set | asks | Claude (X) | off (G) | **high (Gr1)** | `q_r = Gr1/X` | reading |
|---|---|---|---|---|---|---|
| post-cutoff | 16 | 0.47 | 0.125 | **0.31** | 0.67 | partial |
| validation small12 | 30 | 0.50 / 0.47 | 0.13 | **0.30 / 0.27** | 0.60 / 0.57 | partial |
| dev | 47 | 0.69 / 0.67 | 0.18 / 0.12 | **0.21 / 0.19** | 0.31 / 0.29 | gap remains* |

\*Dev's Gr1 stopped at its turn or token cap on 6 of 12 ask PRs (28 of 47 asks). On the PRs where it
finished, `q_r` is 0.71 / 0.69 (0.56 without the AI-generated 33149), post hoc.

- **Reasoning roughly doubles `gpt_5.2`'s reach and closes about a third to a half of the gap to
  Claude.** It does not close it on any set.
- **It restores the looking and more:** comparison lookups a session on post-cutoff are 45.7 at high
  effort, against 22 for Claude and 2-3 with reasoning off. So what remains is concluding from what is
  looked up, not finding it.
- **High effort outgrows the caps set for it:** 10 of 32 sessions stopped at 80 turns or 7.2M tokens,
  still searching. A clean full-set reading, dev above all, needs those sessions rerun with higher
  caps. Rerunning dev's six would cost roughly $30-60.

## gpt-5.4 and gpt-5.5 (test (e), 2026-09-30): high effort needs a Responses-API provider

The user asked for the test with gpt-5.4 and gpt-5.5. Reasoning off runs, with `reasoning_effort: none`
sent explicitly, because gpt-5.5 reasons by default. **High effort cannot run through the pipeline as
it stands.** On Chat Completions both models reject function tools combined with a reasoning effort
(HTTP 400), and `OpenAIProvider` speaks only Chat Completions. gpt-5.2 accepts the combination, which
is why its high-effort runs worked.

Running high effort on the newer models needs an OpenAI Responses-API provider in `src/ape/llm_clients/`:
tools, function-call items, and reasoning items carried between turns. That is a framework build, and
it changes the condition. Responses keeps a turn's reasoning available to the next, which Chat
Completions discards, so gpt-5.2's high-effort runs would not be a like-for-like comparison.

**Test (e)'s result, reasoning off (post-cutoff, 16 asks, two matchers agreeing 112/112):** gpt-5.5
reaches 0.22 (`q = 0.47`), gpt-5.4 0.06 (0.13), gpt-5.2 0.125 (0.27, test (b)), and gpt-5.2 at high
effort 0.31 (0.67), against Claude's 0.47. With reasoning off the gap remains for every gpt model,
gpt-5.5 closest; gpt-5.4 is the weakest reviewer measured. Both newer models file under one finding
a PR, against Claude's four. Their high-effort half waits on a Responses-API provider.

**The Responses-API route, probed (2026-09-30, one tiny call each; for the session that builds it):**
- The ELM gateway's `/v1/chat/completions` returns the same HTTP 400 for gpt-5.4 and gpt-5.5, so it
  forwards to OpenAI and is no way round. It does answer on `/v1/responses` (HTTP 200).
- OpenAI `/v1/responses` with a function tool, `reasoning: {effort: high}`, `store: false` and
  `include: ["reasoning.encrypted_content"]` works for both models. gpt-5.4 returned a `reasoning`
  item carrying `encrypted_content`, then a `function_call` item.
- Usage keys are `input_tokens`, `input_tokens_details.cached_tokens`, `output_tokens` and
  `output_tokens_details.reasoning_tokens`, not Chat Completions' names.
- The client is Chat-Completions-shaped end to end: `OpenAIMessageFormatter` emits `messages`,
  `ResponseProcessor` reads `choices[0].message`, `StreamingProcessor` merges `delta` chunks, and
  `parse_usage` reads `prompt_tokens`. The narrowest seam is a provider that translates at its own
  boundary, so nothing downstream changes.

The build, and the steps to rerun the blocked runs afterwards, are in `llm-openai-responses-provider.md`.

## Why high effort still reaches less: transcript inspection (2026-09-30, no spend)

`results/pr_review_v5/probes/transcript-inspection-2026-09-30/README.md`, which has the tables.
`process_profile.py` there reproduces the counts, and three reader subagents classified the misses.
It rests on one Gr1 run per set, so it is provisional.

- **Gr1 does not conclude worse; it concludes on fewer objects.** Its findings hit asks as often
  as Claude's:

  | set | Gr1 hits per finding | Claude hits per finding |
  |---|---|---|
  | post-cutoff | 0.45 | 0.29-0.32 |
  | validation | 0.36 | 0.30-0.40 |
  | dev | 0.26 | 0.23-0.24 |

  But it files 1.8-3.3 findings a PR, against Claude's 4-12. gpt-5.5 with reasoning off is the
  extreme case: 0.60-0.67 hits per finding, at under one finding a PR. Reasoning-off gpt_5.2 is the
  opposite failure: it files about as many findings as Gr1 or more, and they rarely hit. Hits per
  finding is not precision, because gold is a lower bound.
- **Retrieval is not the gap.** Of the 16 asks Gr1 missed on PRs where it submitted, the evidence
  was in its context for 15. The exception is `homMk`, searched under the PR's own spelling. The
  misses are in which objects and aspects get an attempt:
  - Gr1 builds edits on 1.9-2.3 targets a session, against Claude's 4.6-6.6.
  - It favours the first declarations in the diff, and proofs over signatures.
  - It stops after one failed variant. calib2 reached the `cat_disch` asks by `#check`ing the
    parent constructor and compiling the printed form.
- **Working memory, by inference.** None of the 120 gpt sessions profiled wrote any visible text.
  Chat Completions discards the reasoning, and `OpenAIMessageFormatter` drops `reasoning_content`
  for every provider, so gpt reviews from bare call history. Claude's thinking persists across its
  tool loop. Two signatures of forgetting are highest in the 10 capped sessions:
  - repeated negative lookups: 5.6 against 2.9 per 100 turns;
  - zero-reasoning turns: 32% against 10%.
- **The cap losses (19 of dev's 24 gap asks) are mostly a tool defect, not the budget.**
  `declaration_search` reports leaf-only matches as the queried name. For example, it says
  `Dense.continuous_sup` is declared in Lattice.lean. Capped sessions spent 22% of their turns
  chasing such false duplicates, and 8 of the 10 built no edit at all. Submitting at the cap would
  have reached about 3 of the 19 asks. The fix exists twice, `be65387` on `arm-naming-bar` and
  `eec8d3a` on `arm-division`, and is on neither `develop` nor this branch. **Every run in this
  thread used the defective tool.**
- **Two more asymmetries the record had not named:**
  - brief G dropped X's `notes.md`, the object-by-object account including objects checked and
    cleared;
  - the ape_agent preamble says "TEXT ALONE ... accomplishes NOTHING" and "batch ALL tool calls".

  Claude also had a shell and a linter; `lean_verify_edit` runs without Mathlib's linters, which hid
  d0041.
- **Not supported:** bigger caps, since the late capped turns do not build; resampling, since the
  union of two gpt-5.5 runs reaches the same 4 asks as one; and more retrieval breadth.

**Next, proposed, not run.** One condition that removes the harness asymmetries together, so the wall
moves or does not before any ablation:
1. merge `eec8d3a`;
2. an object ledger in `submit_findings`: every changed declaration, its proof and its signature,
   what was compiled, what was compared, and the verdict;
3. visible notes beside each call, and the preamble's anti-text and batching lines dropped for this
   task.

Run it on gpt_5.2 high and on gpt-5.5 off, post-cutoff first, against Gr1 and Gb. State the rule
before any run: reach on both matchers, with hits per finding at or above X's, so that a gain is not
padding.

Separately, the Responses provider's carry-over switch (`llm-openai-responses-provider.md`) is the
clean test of the working-memory reading, if it runs with `gpt_5.2` high as a condition: the same
model and effort as Gr1, with only persistence changed. The K brief's null does not answer this. It
ran with reasoning off, where findings rarely hit, and it briefed constructions, not coverage of
every object.

**The carry-over switch, run as a coherence test (2026-09-30, $9.18,
`results/pr_review_v5/probes/carryover-coherence-2026-09-30/`).** gpt_5.2 high through Responses, on
the three Gr1 sessions that looped most (42814, 32080, 33145):

| | far repeats /100 calls | negative repeats /100 turns | submitted before the cap |
|---|---|---|---|
| carry-over off | 6.7 | 6.8 | 1 of 3 |
| carry-over on | 2.0 | 0.0 | 3 of 3 |

- The on sessions used about a third of the reasoning tokens, at $2.46 against $6.72.
- By the rule, carry-over improves coherence, and the provider carries reasoning end to end.
- Length-matched, post hoc, the far-repeat ratio is 0.59. So the effect is mainly that sessions
  conclude instead of repeating to the cap. That is the working-memory reading's prediction, at
  process altitude.
- Reach is not measured: 42814's on session filed no findings (no reviewer has reached its four
  asks), and 33145 filed 7 against off's 10.
- The next measurement is gpt_5.2 high with carry-over on across the six post-cutoff ask PRs,
  matched in one seal with Gr1.

**Carry-over's reach, test (e) amended (2026-09-30, $11.06; `gpt52-postcutoff-2026-09-29/README.md`,
the last section).** The seal held eight reviewers on the six post-cutoff PRs (16 asks). The two
matchers agree on all 128 cells. q is each reviewer's reach over Claude's (X = 0.47):

| reviewer | reach | q |
|---|---|---|
| gpt_5.2 high, Chat (Gr1) | 0.31 | 0.67 |
| **gpt_5.2 high, reasoning carried (Grc)** | **0.44** | **0.93** |
| gpt-5.4 high, carried | 0.19 | 0.40 |
| gpt-5.5 high, carried | 0.31 | 0.67 |

- **By the rules, Grc closes the gap and carry-over adds reach** (+0.125, two asks net).
- **The gain is aim, not volume.** Grc filed fewer findings (9 against 11) and hit more asks per
  finding (0.78 against 0.45).
- **It is cheaper.** Grc used 83 turns against 284, for $2.70 against $14.85.
- **The newer models do not beat it here.** gpt-5.5's reading is conditional on an underpowered
  implementation check.
- **Provisional.** One run each, and the endpoint changed along with persistence.

**Next:**
- replicate Grc;
- a carry-over-off gpt_5.2 run on these six PRs, to separate the endpoint from persistence;
- Grc on the validation and dev sets, where Gr1 reached 0.57-0.60 and 0.29-0.31 of Claude.

**Phase 0 of the re-plan (2026-09-30, $20; `results/pr_review_v5/probes/phase0-carried-baseline-2026-09-30/`):
the 0.93 did not replicate.** Three carried reps on post-cutoff and one each on validation and dev,
`declaration_search` fixed, six audited matchings:

| set | asks | q(Chat) | q(carried) |
|---|---|---|---|
| post-cutoff | 16 | 0.67 | 0.44 / 0.375 / 0.19 → **mean 0.71**, union 0.93, stable 0.40 |
| validation | 30 | 0.57-0.64 | **0.57** |
| dev | 47 | 0.29-0.30 | **0.33-0.38** |

- **Carry-over does not close the model gap.** Against Chat it is +0.02 / 0.00 / +0.02-0.04 absolute.
  The gap stands at q 0.33-0.71 across sets.
- **It is adopted as the standard condition anyway**, on process grounds that hold on every set and
  rep: every session concludes (44 of 44 against 22 of 32), repeats fall about tenfold, and cost
  falls to a fifth, with no loss of reach.
- **Dev's cap losses were not the cap or the tool.** Uncapped and tool-fixed, the carried run gained
  two dev asks. This corrects d23fbde's "mostly a `declaration_search` defect".
- **gpt_5.2 files what it verifies** (1 of 56 unfiled). Its misses are in what it attempts.
- **The residual population**: of 93 asks, 37 (40%) are reached by nobody and 30 (32%) only by Claude.
  Phase 1 labels both (`phase1_population.json`).

**Why every gpt condition looks alike on the judge (2026-10-01, no spend; dev held-out 12, judge v9).**
Hits per finding are the same for every reviewer, Claude included; what differs is how much each says
and about how many objects:

| reviewer | findings per PR | change targets with a finding (of 432) | obligations hit per finding |
|---|---|---|---|
| Claude X1 / X2 | 7.5 / 8.1 | 76 / 83 | 0.12 / 0.11 |
| gpt_5.2 off / carried | 3.2 / 2.6 | 35 / 30 | 0.11 / 0.10 |
| gpt-5.5 / gpt-5.4 carried | 2.8 / 2.1 | 32 / 25 | 0.09 / 0.08 |

Inputs are identical (full diff, PR text, pass-0 model in every gpt prompt) and the tools work
(`lean_verify` failures are the model's own unknown names and proof errors; `proof_profile` is dead
on dev: no declaration tables were built). The common factor is the harness and contract, which every
gpt condition shares and Claude's packet does not:
- Claude's brief X requires `notes.md`, "what you did, object by object, including what you checked
  and found nothing wrong with" -- median 22 object entries a PR, each closed with a verdict. Brief G
  drops it; gpt's only output is the final `submit_findings` call.
- the `ape_agent` preamble: every response must be tool calls, "TEXT ALONE ... accomplishes NOTHING",
  batch all calls, submit only when "COMPLETED and VALIDATED"; Claude Code imposes none of it.
- turn caps and a submit tool with a finding budget and merge framing, against an uncapped session
  (Claude: 57 tool calls a session at the median; gpt: 37-49 calls in 18 turns); and gpt's grant lacks
  `file_search`, which Claude called 102 times on post-cutoff.
Not the whole story: on validation the filing bar widened gpt-5.5 from 20 to 37 targets and reach
stayed at 0.20, so breadth without the per-object pass did not help. The untried design is the
contract itself -- an object-by-object ledger in the submission, the preamble's anti-text and
batching lines dropped, `file_search` granted -- on gpt_5.2 carried, judged on the held-out 12.

**The contract condition, as built (2026-10-01, $9.36; `results/pr_review_v5/probes/contract-2026-10-01/`).**
It has all four differences: `review_notes`, `filing_bar: request`, `batch_preamble: plain` and
`file_search`. Issue recall is 0.130 (3 of 23, reachable 0.167), the same count as Grc1, so by the
pre-registered rule it is **not a lever as built**. gpt said a third more (42 findings on 40
targets, against 31 on 30) and hit less per finding (0.071). Its ledger, a median of 8.5 bullets
per PR against Claude's 23.5-33.5, names each object and concludes about its proof or docs. It does
not take objects through the concern families, as Claude's "concern families checked with nothing
to request" does. In the sessions read, the misses are still `attempted_concluded_fine`. Untried,
listed there: a family-by-object ledger, the account written during the session, a Claude
Code-like harness, the contract on gpt-5.5, identical grants. One run; provisional.
**gpt is not a proof specialist** (`focus.py`). Its proof share is no higher than Claude's (16-21%
against 28-33%), and gpt_5.2 misses both proof-golf asks, which Claude hits. Claude does about three
times as much in every family: 9.5-11.5 candidate edits compiled a session against 1.5-3.5, and
17-19.5 library lookups against 1.5-3.5, with the same reading and grepping. The same notes
instruction gave Claude a family-by-object pass (naming on 92-100% of PRs) and gpt none (50%).
The open test that separates model and harness from prompt is the swap: Claude given gpt's rendered
prompt verbatim.
**Contract v2 (2026-10-01, $8.36).** It removes every item of gpt-only prompt text and asks for
Claude's per-declaration ledger. Issue recall is 0.087 (2 of 23): **not a lever**. The ledger was
carried over. The notes name 73% of the PR model's declarations, as Claude's do (v1: 37%), and
mention naming on 83% of PRs. But gpt's investigation did not grow: 30 tool calls a session, 2
edits compiled and 2.5 library lookups, against Claude's 57, 10 and 18. So its entries assert
checks it did not run, and the misses read as "nothing to ask" on the very declarations the
maintainers asked about. The prompt is now as close to Claude's as these runs make it. **Next is
the swap**, which says whether the remainder is the model or the harness.
**Contract v2 on gpt-5.5, and the swap (2026-10-01).** gpt-5.5 under v2 reached 0.130 (3 of 23),
not a lever, but it closes every input-side gap: its notes cover 82% of declarations, they mention
naming and generality on 100% and 92% of PRs, and it compiles 9.5 edits a session, Claude's level.
It files 30 findings to Claude's 90-97. **The swap**, Claude given gpt's v2 messages verbatim,
reaches 0.435 (10 of 23; X 11), so by the rule the prompt is not what holds gpt back. It got there
with fewer tool calls, compiles and lookups than gpt-5.5 made under the same prompt: 35, 6 and 2.5
against 41, 9.5 and 6. Across every condition run, recall tracks how many changes the reviewer
decides to ask for. Coverage, attention, compiles and lookups do not move it. Not separated:
model from harness, and judgement from memory of these in-window PRs. The clean check is the swap
on the post-cutoff set, by blind matchers.
**Next: `docs/plans/2026-10-01-claude-models-under-the-harness.md`** (user, 2026-10-01). It crosses
harness and model: gpt and Opus 5.5 under the project's Claude Code harness, and Opus 5 and 4.8 on
the subscription. It is read on the dev judge and the post-cutoff matchers, after the harness merge.

**Phase 3.1, the filing bar (2026-09-30, $47.64; `results/pr_review_v5/probes/filing-bar-2026-09-30/`).**
`SoloReviewConfig.filing_bar: request` removes every merge verdict from the task. On post-cutoff
(in-sample) gpt-5.5 files the three 43192 asks it had withheld, q 0.67 → 0.93. **On validation it
is not the mechanism**: gpt-5.4 0.233 → 0.200, gpt-5.5 0.200 → 0.200, although the bar cut unfiled
verified edits from 9 and 8 to 4 and 6 and nearly doubled gpt-5.5's findings. The newer models verify
2-4x the edits gpt_5.2 does and reach fewer asks: their validation deficit is aim, not filing.
gpt_5.2 carried stays the reference gpt reviewer (0.267, $5.60).

**Phase 1, the residual asks by mechanism (2026-09-30; `phase1-residual-mechanisms-2026-09-30/mechanisms.md`).**
Two blind readers, 141 pairs, no disjoint label set. Of 67 residual asks: the object was attended
in 63 (`never_attempted` 4), withheld after verifying 2; the misses are judgement, concluded fine
(40 asks) or changed differently (25), explained by `knowledge_convention` (25: `to_fun`, `mk_iff`,
`grind` tags, `_left`/`_right`, namespace short names, `naming_norm` misleading on d0045) and
`try_it_not_tried` (19: `positivity`, `gcongr`, `simpa`, "does the old proof work"). Same shape for
Claude and gpt. Phase 2 not funded; Phase 3.2 (try-it) next, then 3.3 (conventions).

**Why gpt-5.4 and gpt-5.5 reach less than gpt_5.2 (2026-09-30, read by hand, about $0.90;
`results/pr_review_v5/probes/model-inspection-2026-09-30/`).**
- **They verify more and file less.** Against gpt_5.2: 10 compiled edits each against 7, and 6
  findings against 9. They left 4 of 10 (gpt-5.5) and 2 of 10 (gpt-5.4) verified edits unfiled,
  against 0 of 7.
- **gpt-5.5's whole deficit is 43192.** It compiled the maintainers' `cat_disch` defaults and the
  `homMk` rename, which no gpt reviewer had reached, then filed only the typo, calling the PR
  merge-ready.
- **gpt-5.4 withheld the verified typo fix**, and filed the opposite design: delete the wrappers the
  maintainers asked to improve.
- **Asked why**, each replayed with its carried reasoning: the edits were "not something I would
  expect a maintainer to require", "optional ergonomic improvement", "minor docstring polish".
- **The explanation.** The newer models read the brief's "would plausibly request", the severity
  line and `merge_ready_as_is` as "would require". They drop verified polish, which is what these
  maintainers asked for.
- **Not yet measured:** how much reach the bar costs across sets. Any brief change designed from
  this is in-sample on the post-cutoff set.
