# Why gpt_5.2 at high effort still reaches less than Claude: transcript inspection (2026-09-30)

Read after every result in `docs/todo/reviewer-model-gap.md`, not pre-registered. It spends nothing.
The question: with the same brief, pass-0 model and tools, Claude (`claude-opus-5-5`, X1 and X2) reaches
0.47-0.69 of the asks and `gpt_5.2` at `reasoning_effort: high` (Gr1) reaches 0.21-0.31. The record
called that "it looks twice as much as Claude and concludes less". What does the process show?

**Sources.** Four sets of transcripts:
- the Gr1 and G runs on the three sets (`gpt_sessions.json`);
- test (e)'s gpt-5.4 and gpt-5.5 runs;
- Claude's 66 subagent transcripts, which live outside the repository (`claude_sessions.json`, the
  directory in `process_profile.py`);
- the committed matchings.

`process_profile.py` reproduces every count in sections 1-4. Sections 5 and 6 are three reader
subagents' classifications, one reader each, in `readers/`. Four of their load-bearing claims were
spot-checked against the raw transcripts, and one was corrected (section 3). The capped reader's
scripts are in `readers/capped_scripts/`; run in order `extract, metrics, memloss, phantom, last25,
chase, build_capped`, they rebuild `readers/capped.json` exactly.

Everything here rests on one Gr1 run per set, so it is provisional.

## 1. Per finding, high-effort gpt_5.2 hits asks as often as Claude; it files fewer

| set | Claude: findings a PR / ask hits per finding | Gr1: findings a PR / hits per finding | G (off): findings a PR / hits per finding |
|---|---|---|---|
| post-cutoff | 4.0-4.2 / 0.29-0.32 | 1.8 / 0.45 | 3.7-4.0 / 0.08-0.09 |
| validation small12 | 5.0-5.9 / 0.30-0.40 | 3.1 / 0.36 | 1.8-2.0 / 0.21-0.31 |
| dev | 11.0-11.9 / 0.23-0.24 | 3.3 / 0.26 (6 of 12 ask PRs capped at zero) | 4.3-4.7 / 0.13-0.18 |

On test (e)'s seal, gpt-5.5 with reasoning off files 5-6 findings in six PRs and hits 0.60-0.67 per
finding, against Claude's 24-25 findings at 0.29-0.32.

"Hits per finding" is not precision. Gold is a lower bound, and a finding outside the asks may be
right. But the direction is the same on every set. **With reasoning off, gpt_5.2's findings rarely
hit. With reasoning on, and on gpt-5.5, they hit as often as Claude's, and there are far fewer of
them.** The newer gpt reviewers are accurate and quiet. The "concludes less" in the record is
concluding on fewer objects, not concluding worse.

Resampling does not help. The union of two gpt-5.5 runs reaches the same 4 asks as one, and Claude's
two sessions the same 8. Each reviewer's misses are systematic, not noise (16 asks, two runs).

## 2. The shape of a session

| reviewer | turns | calls | calls a turn | turns with any visible text | reasoning carried to the next turn |
|---|---|---|---|---|---|
| Claude (X) | 28-38 API messages | 27-38 | 0.97-0.99 | 1-2 text blocks a session, 59-122 characters in all | **yes**: thinking on 69-73% of messages, kept in context |
| `gpt_5.2` high (Gr1) | 45-47 | 81-98 | 1.8-2.1 | **0 of every turn** | **no**: 125-142k reasoning tokens a session, discarded |
| `gpt_5.2` / gpt-5.4 / gpt-5.5, off | 3.5-4.5 | 9-15 | 2.3-3.9 | 0 | none produced |

- **None of the 120 gpt sessions profiled wrote any visible text.** A session's only record of what it
  concluded from a result is its next call. On Chat Completions the reasoning is billed and then
  dropped, so at turn 40 Gr1 sees about 80 bare calls and their results. Claude's thinking stays in
  context across its tool loop.
- **The harness does the same to any provider.** `OpenAIMessageFormatter.format_for_api` keeps an
  assistant message's `content` and drops the `reasoning_content` the base formatter carries. So an
  ELM model's visible reasoning is dropped too. Visible `content` does survive, so a note written in
  text would persist on Chat Completions.
- **The ape_agent preamble pushes against text and toward batching.** The brief is wrapped in
  "Every response MUST include TOOL CALLS", "TEXT ALONE ... accomplishes NOTHING" and "CRITICAL: Call
  ALL needed tools in EACH response ... batch ALL tool calls". The reasoning-off sessions do exactly
  that: three or four turns of batched calls, then submit. Claude works one call per step.
- **Brief G is not quite brief X.** It dropped X's `notes.md` requirement: "what you did, object by
  object, including what you checked and found nothing wrong with". Claude writes that file once, at
  the end, so it is not Claude's working memory. It is a per-object accounting that G never asked for.
- **Tool parity has two more gaps.** Claude had a shell: it measured line lengths and switched the
  linter on. `lean_verify_edit` compiles without Mathlib's linters and reports `warnings: []`, and
  that hid d0041, a 101-character line, from Gr1. And both reviewers used the defective
  `declaration_search` of section 6.

## 3. Construction breadth: gpt looks broadly and builds narrowly

`lean_verify_edit` calls that change code, per session:

| set | Gr1 edits / distinct targets | Claude edits / distinct targets |
|---|---|---|
| post-cutoff | 2.7 / 2.0 | 7.1 / 4.6 |
| validation small12 | 4.2 / 2.3 | 8.3 / 5.6 |
| dev | 2.1 / 1.9 | 10.9 / 6.6 |

Gr1 makes 45.7 comparison lookups a session on post-cutoff, against Claude's 22. It edits about two
targets a session. Claude edits five to seven. On 32875, all eight of Gr1's edits went to three
declarations, and both missed asks were on others. The longest uncapped Gr1 sessions submitted right
after a burst of edits, and most of their findings name an edited declaration. Findings follow
constructions.

(Correction during inspection: counting only `new_declaration` edits put Claude *below* Gr1 on
validation. Claude mostly edits by line range, `replacement`, and the table counts both.)

## 4. The 35 asks Claude reached and Gr1 missed, split by whether Gr1 was capped

The reasoning seal: an ask counts as reached by Claude in at least 2 of its 4 cells, and by Gr1 in
neither of its 2.

| set | Gr1 submitted on the PR | Gr1 capped on the PR |
|---|---|---|
| post-cutoff | 4 | 0 |
| validation small12 | 7 | 0 |
| dev | 5 | **19** |

## 5. The 16 misses where Gr1 submitted: the evidence was nearly always in view

Readers: `readers/perask_val.{json,md}` and `readers/perask_post_dev.{json,md}`. A miss takes the
first class that fits.

| class | asks |
|---|---|
| never retrieved | **0** |
| searched with the wrong term (`mkHom` for `homMk`, the PR's own spelling) | 1 |
| in view, no call aimed at the issue | 7 (one of them, d0041, hidden by the linter-free compile) |
| examined, the change never compiled | 4 |
| filed a different fix, scored partial (in two, one Claude session chose the same fix) | 3 |
| compiled the fix and did not file it (low confidence) | 1 |

- **Gr1's misses are not in finding things.** They are in which objects and which aspects get an
  attempt: the other five declarations on 32875, the signatures on 34091, where binders were never
  varied and every edit changed a proof, and the sibling `isoMk` beside `mkHom` on 43192.
- **One failed drastic variant ends the line.** On 43192, Gr1 compiled "drop `map_id`/`map_comp`",
  it failed, and it never tried keeping them with defaults. The calibration session calib2 reached
  both `cat_disch` asks. It had `#check`ed `PresheafOfModules.mk`, whose printout shows the
  `:= by cat_disch` defaults, and compiled that form. The two sessions spent about the same on
  reasoning (221k and 225k tokens).
- **Gr1 never called `precedent_search` on the validation PRs.** That tool gave Claude X1 v0055's proof
  shape.
- Only 6 of the 9 post/dev misses were reached by both Claude sessions (p0014, p0015, p0016, d0014,
  d0016, d0041). The rest are weak gap evidence.

## 6. The 10 capped sessions: a tool defect, forgetting, and no building

Reader: `readers/capped.{json,md}`.

- **`declaration_search` reports false duplicates.** It matches a name's last component and reports
  the queried name as found. So `Dense.continuous_sup` "is declared in Lattice.lean (before this PR)",
  which holds only the root `continuous_sup`. The capped sessions spent 22% of their turns following
  such hits, against 7.6% in uncapped sessions. 33145, a one-file PR, made 58 calls on Lattice.lean.
  **This defect was found and fixed twice:**
  - `be65387`, 2026-09-15, on `arm-naming-bar`;
  - `eec8d3a`, 2026-09-24, on `arm-division`, whose message names the same `Dense.continuous_inf`.

  Neither fix is on `develop` or on this branch, so **every run in the reviewer-model-gap thread, G,
  Gr, K and the lead runs, used the defective tool.** Claude got the same false hits and did not
  loop on them.
- **Forgetting signatures, stronger in capped sessions:**

  | per session | capped | uncapped |
  |---|---|---|
  | repeats of a call that had already come back negative, per 100 turns | 5.6 | 2.9 |
  | turns with zero reasoning | 32% | 10% |

  The share of zero-reasoning turns rose after turn 20 in all ten capped sessions. The submit turn of
  an uncapped session carries a reasoning spike, a median of 10k tokens and up to 25k, where the whole
  review is written from the bare call history.
- **No building.** Capped sessions proposed 10 edits in 774 turns, and 8 of the 10 proposed none.
  Uncapped sessions proposed 73 in 712 turns. Only 4 of the capped sessions' last 250 turns built
  anything. The cap cut off wandering, not a compile loop.
- **What the cap threw away is small.** Of the 19 dev asks on capped PRs, 10 were examined, 9 were in
  view and never targeted, and none had its fix built. A submission at the cap would plausibly have
  reached 3, with 4 more partial. Strong unfiled candidates existed on 33145, 33285 and 33321.
- **Bigger caps are not supported.** Each extra turn on a token-capped session re-sends 100-145k tokens,
  and the late turns were not building.

## What this says the gap is, at probe altitude

This is one Gr1 run per set, one reader per classification, and 16 asks and 35 gap asks in all.

1. **Not retrieval.** The evidence was in Gr1's context for 15 of its 16 judgment misses, and
   high-effort gpt_5.2 looks up more than Claude.
2. **Not per-finding judgment.** Where it files, it hits as often as Claude.
3. **Construction breadth.** Asks are reached where a reviewer tries the change, and Gr1 tries changes
   on about two targets a session against Claude's five to seven. It concentrates on the first
   declarations and on proofs over signatures, and it stops after one failed variant.
4. **Working memory,** most plausibly. Every gpt turn is a bare call with its reasoning discarded, and
   the forgetting signatures, repeat negatives and zero-reasoning turns, are highest where sessions
   wandered to the cap. This is inferred, not tested: nothing here varies persistence.
5. **Harness defects that cost gpt more than Claude:** false duplicates from `declaration_search`
   (the capped sessions' largest single sink), and a linter-free compile.

Not separated: whether the narrow building is the model's or the product of 3 and 4 together, since a
reviewer that cannot keep its conclusions may re-verify instead of moving to the next object.

## Levers, in the order the evidence supports them (none is tested)

| lever | evidence here | cost |
|---|---|---|
| **Merge `eec8d3a` (the qualified-name `declaration_search`) before any further run in this thread** | 22% of capped sessions' turns; all runs so far used the defect | code only |
| **An object ledger in the submission, restoring X's `notes.md` parity:** every changed declaration, its proof and its signature, what was compiled, which sibling or parent was compared, and the verdict | the dominant miss class (in view, not attempted); 2 against 5-7 targets built | prompt and schema |
| **Visible working notes on Chat Completions:** a short note of what the last results established, in text beside each call or as a `note` tool, and the preamble's "TEXT ALONE accomplishes NOTHING / batch ALL" removed for review tasks | 0 text turns in 120 sessions; forgetting signatures; the formatter keeps `content` | prompt, scaffold |
| **Reasoning carried across turns (Responses API, encrypted reasoning items),** with `gpt_5.2` as a condition beside gpt-5.4 and gpt-5.5 | the same model and effort with only persistence changed: the clean test of item 4 | the provider being built |
| A linter-on compile, or a style check the arms can call | d0041 | small tool |
| Submit-at-cap, or incremental recording of findings | about 3 dev asks and 4 partials; only after the `declaration_search` fix, or it files false duplicates | scaffold |
| *Not supported:* bigger caps, resampling or unions, more retrieval breadth | sections 1, 5, 6 | |

**The construction brief is not this lever.** Test (b)'s K brief raised gpt_5.2's compiles near
Claude's and reached less. But it ran with reasoning off, where findings rarely hit (section 1), and
it asked for construction passes, not per-object coverage. The ledger on a reviewer whose findings
hit, high effort or gpt-5.5, is untested.
