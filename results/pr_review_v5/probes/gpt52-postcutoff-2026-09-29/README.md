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
