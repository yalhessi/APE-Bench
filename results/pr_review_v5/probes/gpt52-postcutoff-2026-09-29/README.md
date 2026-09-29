# Test (b): the pipeline's model on the post-cutoff set -- the model gap, and whether a construction brief makes it construct (2026-09-29)

Written before any run. Test (b) of `docs/todo/reviewer-model-gap.md`.

## What the record says, and why this is next

- On three in-window PRs, Claude with the pipeline generalist's brief reached five asks that
  `gpt_5.2` missed in both its lead and solo configurations. At those sites the pipeline's arms held
  `lean_verify_edit` and did not construct; Claude constructed unprompted.
- On ten PRs created after Claude's cutoff, Claude's reach is 79-107% of its in-window rate
  (`postcutoff-2026-09-29`), so that reach is not mainly recall.
- Open: is the gap the model, or the packet and brief? And does briefing the constructions make
  `gpt_5.2` construct? Neither model can have seen these PRs.

## Set and conditions

The 6 `probe-2026-07-08-v1` PRs with round-1 asks (41930, 42184, 42814, 43024, 43167, 43192), with the
16 asks both readers agree on (`postcutoff-2026-09-29/match/ask_manifest.json`).

The pipeline's model through the solo task (whole PR, `ape_agent`): `gpt_5.2`, reasoning as the
pipeline runs it, `solo_cost_cap` $1.50 a session. Each PR's pass-0 model is appended to the user
prompt (`model_context.jsonl`, from the committed `model_pr*.md`).

| condition | system prompt | runs |
|---|---|---|
| **G** | `brief_G.md`: the control brief of the construction demonstration and of Claude's post-cutoff sessions, verbatim except where the solo task supplies the packet and the submission | 2 |
| **K** | `brief_K.md`: the design's passes 3 and 4 (the construction briefs `brief_K3.md` and `brief_K4.md`), in one session | 2 |

**K is one session, not two chained ones.** The question here is whether briefing the constructions
makes `gpt_5.2` construct. On Claude, pass 4 cited pass 3's constructions, but no hit rested on that.
One session also keeps G and K compute-matched.

**Where this differs from Claude's sessions, stated:**
- **Harness:** `ape_agent` with MCP tools, against a Claude agent with a shell and `./ptool`.
- **Tools:** the solo grant is `file_read`, `content_search`, `lean_verify`, `get_lean_goal`,
  `code_hover`, `code_goto`, `lean_verify_edit`, `submit_findings`, and the same five context tools.
  Claude had `file_search` in place of the Lean navigation tools.
- **Submission:** through `submit_findings` (`SOLO_USER`: at most 20 findings, with a path, a line and
  labels), where Claude wrote a JSON file. `SOLO_USER` closes with "Review this PR. Investigate what
  you need to before deciding", the same for G and K.

## Matching

Two blind matchers with `postcutoff-2026-09-29/matcher_rubric.md`. Per PR, six reviewer sets are
shuffled: G1, G2, K1, K2, and Claude's post-cutoff X1, X2, so the model comparison is within one
matcher. A solo finding is shown as target (its path and line), claim, requested change (its
`suggested_fix`) and severity, with condition cues redacted.

## Reading rule

On each matcher, per-session reach is the asks `reached`, summed over sessions, divided by
(asks × sessions).

1. **The model gap, on all 16 asks:** `q = reach(G) / reach(Claude X)`.

   | on both matchers | reading |
   |---|---|
   | `q ≤ 0.5` | the pipeline's model reaches markedly less with the same brief and packet |
   | `q ≥ 0.8` | comparable: the gap in the record was the packet or the brief, not the model |
   | otherwise | inconclusive at this size |

2. **The construction brief on `gpt_5.2`**, on the 9 asks in pass-3/4 families (interface 3,
   derivation 2, statement design 2, generality 2). It is supported if, on both matchers:
   - K's asks reached by both runs exceed G's by at least 2;
   - K files no more findings per PR per run than G.

3. **Mechanism (read, not in the rule):** `lean_verify_edit` calls per session for G, K and Claude X.
   Does the brief make `gpt_5.2` construct?

## Cost and care

- 24 sessions. The worst case is 4 runs × $9.00. Expect about $3-6 (the solo baseline averaged $0.11
  a PR on validation).
- `OPENAI_API_KEY` is sourced in the launching command.
- In the first minutes, `completed with success` lines must appear, and "API call failed, retrying"
  must not.

---

## Result (2026-09-29): the pipeline's model reaches about a quarter of Claude's, and the construction brief does not close it

The runs were committed before any matcher input was built (`7757e55`): 24 sessions, all successful,
$1.69 billed. The two blind matchers agree on all 96 cells and read only their own folders.

| per-session reach | on all 16 asks | on the 9 asks in pass-3/4 scope |
|---|---|---|
| **Claude, the plain brief** (X, the post-cutoff sessions) | **0.47** | **0.44** |
| `gpt_5.2`, the plain brief (G) | 0.12 | 0.00 |
| `gpt_5.2`, the construction brief (K) | 0.06 | 0.00 |

1. **The model gap:** `q = 0.12 / 0.47 = 0.27` on both matchers, so **markedly less** by the rule
   (`q ≤ 0.5`).
2. **The construction brief on `gpt_5.2`: not supported.** No ask in scope was reached by both runs,
   under either condition. K filed fewer findings (2.2 against 3.8 per PR per run).
3. **Mechanism (read, not ruled):**

   | condition | compiles per session |
   |---|---|
   | `gpt_5.2`, plain brief | 2.2 and 2.5 |
   | `gpt_5.2`, construction brief | 6.2 and 6.8 |
   | Claude, plain brief | 9.3 and 6.8 |

   The brief made `gpt_5.2` construct almost as often as Claude does unprompted, and it still
   reached none of the substantive asks.

**Per ask.** `gpt_5.2` reached only the two surface asks: the unused import (every set) and the
title's missing word (G). Claude also reached:
- dropping an unneeded `[L.NeBot]`;
- a missing `@[to_additive]`;
- `cat_disch` defaults on `mk` and `mkHom`;
- the rename to `homMk`;
- in one run, the `_anti` rename.

**What it means, at probe altitude** (6 PRs, 16 asks, 2 runs a condition, matchers in full
agreement):
1. **On PRs neither model has seen, with the same brief, the same pass-0 model and the same tools,
   the pipeline's reviewer (`gpt_5.2` as the pipeline runs it) reaches about a quarter of what Claude
   reaches, and none of the substantive asks.** The binding constraint on these asks is the reviewer,
   not the brief, the packet or the coordination.
2. **Making it construct does not help.** The construction brief tripled `gpt_5.2`'s compiles and
   reached less. The gap is in what the reviewer concludes and chooses to ask, not in whether it
   compiles. That corrects the reading of the construction demonstration, which put the pipeline's
   loss on "the arm's initiative to construct".
3. **Every design comparison measured on `gpt_5.2` with reasoning off was measured on a reviewer
   that misses nearly all substantive asks here.** A null there says little about the design.

**Not separated here, and the next tests:**
- **Model against harness:** `ape_agent` and a submission tool, against a Claude agent writing a file.
  The solo task also runs under the `claude_code` scaffold (the B/C pair). Claude through the
  pipeline's own task and contract on this set separates the two.
- **Reasoning:** `gpt_5.2` ran as the pipeline runs it, and the in-window reasoning twin showed no gain
  at 3.8x the cost. It is untested here.
- **Size:** 16 asks. The gap is large (0.12 against 0.47, 96/96 matcher agreement) but rests on 6 PRs.


## Inspection (2026-09-29): where the difference comes from

Read after the result, not pre-registered. `inspect_sessions.py` reproduces every count here.

**A correction to the result above.** The tools were nearly the same, not the same. Claude's sessions
had `file_search` (54 calls) and lacked `lean_verify`, `get_lean_goal`, `code_hover` and `code_goto`.
The gap below survives removing `file_search` from Claude's counts.

**The process, per session (mean over 12 sessions a condition).** A lookup is PR-side when it reads or
searches a changed file or looks up a name the diff adds. A compile is a re-verification when 90% of
its lines are the PR's own, a usage when it writes an `example`, and a variant otherwise.

| | `gpt_5.2`, plain (G) | `gpt_5.2`, construction (K) | Claude (X) |
|---|---|---|---|
| review-tool calls | 10.9 | 14.2 | 38.1 |
| PR-side lookups | 4.8 | 4.2 | 6.7 |
| library-wide searches for the PR's own new names | 1.3 | 1.5 | 1.6 |
| **lookups of anything else in the library** | **2.3** | **1.9** | **21.7** (17.2 without `file_search`) |
| compiles: re-verification / usage / variant | 0.0 / 1.5 / 0.8 | 0.4 / 2.5 / 3.6 | 0.5 / 2.9 / 4.7 |

1. **The largest difference is lookups of comparison objects: about ten to one, on every one of the six
   PRs.** PR-side reading is about the same. The construction brief brought `gpt_5.2`'s variant
   compiles close to Claude's (3.6 against 4.7) and left its library lookups where they were (1.9).
2. **Per substantive ask, the misses are of two kinds.** The question is whether the comparison
   evidence the maintainer cited ever reached `gpt_5.2`'s context (four sessions, G1, G2, K1, K2):
   - *Never retrieved.* The `cat_disch` default arguments of the parent `PresheafOfModules` API
     (`p0014`, `p0015`) and the `_anti` naming (`p0008`) reached no session. Claude read the parent
     file, searched Zulip for the naming and compiled both variants.
   - *In view and not raised.* The new lemmas' neighbours all carry `@[to_additive]` (`p0011`), in
     view in 4 of 4 sessions. The PR's own file names the iso `isoMk` beside the hom `mkHom`
     (`p0016`), in view in 3 of 4. A sibling lemma in the same file removes the filter's `NeBot` by
     exactly the case split the maintainer asked for (`p0002`), in view in 2 of 4.
3. **Every session stopped on its own.** All 24 submitted, at a median of 61-88 seconds and
   $0.13-0.25 against the $1.50 cap. No cap bound.
4. **`gpt_5.2` wrote no text between tool calls.** Every turn is a bare call, and the request carried
   no reasoning effort, so it did not reason (`docs/todo/reasoning-in-the-arms.md`). Claude
   (`claude-opus-5-5`) reasons between calls.
5. **Tool misuse is a small loss.** Half of G's compiles were `lean_verify` on a path outside the
   workspace. K made no such error and reached less.

**What this says the sources are, ranked by the evidence:**
- **Retrieval breadth.** `gpt_5.2` reviews the PR against itself and its immediate neighbours, and
  Claude reviews it against the library. This alone accounts for the never-retrieved asks.
- **Inference from what is in view.** With the regularity on screen, `gpt_5.2` still did not raise
  the deviation. This accounts for the rest.
- **Not the sources:** the construction step (K constructs at near Claude's rate), the budget (no cap
  bound), tool errors (K had none) and the `file_search` tool (the gap survives without it).

Both sources fit a reviewer that does not deliberate: no reasoning, no text between calls, and an early
voluntary stop. They fit a less capable model equally well, and this inspection cannot separate the
two. The in-window reasoning twin (`c4e08d2`) does not settle it. It ran the arms, not a whole-PR
session, at medium effort, with 29 of 140 jobs paused at the cost cap.

**What would separate them (test (d), paid, held for approval).** G again with
`reasoning_effort=high`, two runs on the same six PRs, about $3. G's most expensive session was
$0.28, so about four times that fits the $1.50 cap. Stated before any run: reasoning is the lever if
G-with-reasoning makes at least 8 comparison lookups a session and reaches at least 0.30 on both
matchers. If lookups rise and reach does not, the inference half is the model's.


## A defect in test (b)'s matcher inputs, and the re-match (found 2026-09-29, before any re-match)

**The defect.** The solo task stores a finding's location under `anchor`, and
`build_match_inputs.py` read it from the top level. So all 73 of `gpt_5.2`'s findings reached the
matchers with the target `None:None`, while all 49 of Claude's carried a file and a declaration. A
matcher had to identify a `gpt_5.2` finding's object from its claim alone. That may have cost `gpt_5.2`
reached or partial cells, and it let the matchers tell the two systems apart, though not which was
which.

**The fix.** The builder reads `anchor`, and it now refuses any finding without a target.

**The re-match, stated before it runs.** Two new blind matchers get the same six sets under the same
seal (`blinding_SEALED.json`), with the same rubric and asks, on the corrected inputs. The reading
rule above is applied unchanged. The re-match supersedes the original reading, and the number of cells
that changed is reported by condition.


---

## The arms condition (pre-registered 2026-09-29, before its runs)

**The question.** Does the pipeline's structure (lead, work units, the ten arms, a generalist pass on
every unit) recover part of the gap on unseen PRs? On in-window validation PRs it beat the `gpt_5.2`
solo baseline, 8 of 30 asks against 2.

**The runs.** `configs/pr_review_v5_probe_2026_07_08_v1_lead.yaml`: lead mode as configured, `gpt_5.2`,
the same 6 PRs. Two runs, L1 and L2 (`probe_postcutoff_lead_rep{1,2}`). The runs get the pipeline's own
work-unit prompts; there is no pass-0 model and no probe brief.

**Matching.** Two new blind matchers. Per PR, six sets: L1, L2, and again G1, G2, X1, X2, so every
comparison is within one matcher. A lead finding is taken from the run's `findings.jsonl`, all
channels. That is the found set, since the admission gate discards most found hits.

**Reading rule**, on per-session reach over the 16 asks, on both matchers:

| L's reach | reading |
|---|---|
| ≥ 0.30 | the structure recovers at least half the gap between `gpt_5.2` solo (0.12) and Claude (0.47) |
| ≤ 0.18 | the structure does not help on unseen PRs; the model dominates |
| between | partial |

**Also read:**
- reach counting only published findings (the best-matching finding's admission);
- reach on the 9 asks in pass-3/4 scope;
- findings per PR.

**Test (c), revised.** The solo task's `claude_code` scaffold is a harness, not a model: it runs the
Claude Code SDK against a relay to the configured model, `gpt_5.2`. So it would give `gpt_5.2` in
Claude Code, not Claude in the pipeline. It has never run on reviews, and its own config records leak
paths that are not closed. The pipeline's clients have no Anthropic provider. Test (c) is held until
the transcript comparison of G against X shows whether the gap is process (turns, tool errors,
truncation) or judgment.
