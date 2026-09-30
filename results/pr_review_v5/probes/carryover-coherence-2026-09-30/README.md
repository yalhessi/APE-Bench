# Reasoning carry-over: does gpt_5.2 stay coherent when its reasoning persists? (pre-registered 2026-09-30, before its runs)

## Why

On Chat Completions, gpt_5.2's reasoning is dropped after every turn, so a high-effort session
reviews from bare call history. The transcript inspection (`docs/todo/reviewer-model-gap.md`, "Why
high effort still reaches less") read this as lost working memory: the ten sessions that stopped at a
cap repeat negative lookups 5.6 times per 100 turns against 2.9, and spend 33% of their turns with no
reasoning against 13% (this directory's `coherence.py` on the three Gr1 runs, which reproduces the
record's 5.6 / 2.9). The Responses provider (`docs/todo/llm-openai-responses-provider.md`) can send
each turn's encrypted reasoning back on every later turn (`openai_responses_reasoning_carryover`).
No session has yet run with it on. Every Responses session so far has carry-over off, which is the
Chat-equivalent condition by design, so none of them can say whether the API change helps.

Two questions, in order:
1. **Implementation.** In a real multi-turn session, does the reasoning reach the next turn?
   The unit tests cover the round trip in memory, and the provider's live checks sent one two-turn
   conversation by hand. Neither ran the agent loop.
2. **Coherence.** With the same model, effort, brief, tools and caps, does carrying reasoning cut
   the repeats that mark the looping sessions?

## Sessions

The three gpt_5.2 high-effort Chat sessions (Gr1) that repeated most, one per set, all stopped at a
cap:

| set | PR | Gr1 status | turns | calls | far repeats /100 calls | negative repeats /100 turns | zero-reasoning turns |
|---|---|---|---|---|---|---|---|
| post-cutoff | 42814 | 80-turn cap | 80 | 149 | 14.8 | 10.0 | 46% |
| validation | 32080 | 80-turn cap | 80 | 146 | 12.3 | 13.8 | 32% |
| dev | 33145 | token cap | 76 | 221 | 16.7 | 13.2 | 12% |

They were chosen as the worst, so a rerun is expected to look better by chance (regression to the
mean). **Gr1 is therefore a reference only.** The comparison is between two new sessions per PR that
differ in one switch:

| label | runs | endpoint | carry-over | configs |
|---|---|---|---|---|
| off | `probe_{postcutoff,val_small12,dev}_gpt52_Gr_resp_{42814,32080,33145}` | Responses | off | `configs/pr_review_v5_{probe_2026_07_08_v1,val_small12,dev_medium}_gpt52_Gr_resp.yaml` |
| on | `probe_{postcutoff,val_small12,dev}_gpt52_Gr_carry_{42814,32080,33145}` | Responses | on | `..._gpt52_Gr_carry.yaml` |

Everything else is Gr1's: `gpt_5.2`, `reasoning_effort: high`, brief G with the set's pass-0 model
context, the solo tools, and 80 turns. Carry-over re-sends every earlier turn's reasoning as input,
which on these sessions is projected to add 2.4M, 3.1M and 5.3M processed tokens. That would take
42814 and 33145 past Gr1's 7.2M-token cap. So both conditions get a 16.08M-token cap, and a $13.40
cap in step with it (the tree's 1.2M tokens a dollar, `test_token_budget.py`). The 80-turn cap is the
one that can bind. `declaration_search`'s fix (eec8d3a) is held out, as for every
run in this thread.

## Measures (`coherence.py`)

- **Carried reasoning.** For each run, `y(n) = prompt(n+1) - prompt(n) - visible_output(n)` is
  regressed on `reasoning(n)` and the characters of turn n's tool results. Reasoning re-sent at turn
  n+1 is billed as its input. On every carry-over-off session on disk, the coefficient is 0.00 to
  0.01 on the three Gr1 runs (1,493 turn pairs) and −0.12 and −0.03 on the gpt-5.4 and gpt-5.5
  Responses calibrations. **Turns carrying reasoning**: assistant messages whose `signature` holds
  reasoning items with `encrypted_content`.
- **Far repeats per 100 calls**: a call identical in tool and arguments to one at least 5 turns
  earlier, plus a `file_read` overlapping a range of the same file read at least 5 turns earlier.
- **Negative repeats per 100 turns**: a call identical to an earlier call whose result was empty or
  a failure.
- Secondary: zero-reasoning turns, turns used, and whether the session submitted before the cap.

## Reading rule

**1. Implementation, pass or fail, read before anything else.**
- **On** passes if every turn with reasoning tokens carries encrypted items, the coefficient is in
  [0.8, 1.2] on each run, and no request is refused.
- **Off** passes with no turn carrying reasoning and a coefficient in [−0.2, 0.2].
- A failure is a provider defect, and coherence is not read.

**2. Coherence, pooled over the three PRs, on versus off.**
- **Carry-over improves coherence** if on is at or under 0.5 of off on both far repeats per 100
  calls and negative repeats per 100 turns.
- **No improvement** if on is at or over 0.8 of off on either.
- Anything between is **partial**.
- If off does not loop, the test cannot read and is reported as such, not as a null. "Does not
  loop" means pooled far repeats under 5 per 100 calls, about uncapped Gr1's 3.8.

**Also read:**
- Off against Gr1: the endpoint at high effort, given the selection above.
- Sessions submitting before the cap, on against off.
- Findings each session filed. They are not matched here: reach is test (e)'s question, not this
  test's.

One session per cell, so any reading is provisional.

**Cost.** Gr1 billed $2.11, $2.33 and $4.13 on these PRs. Off is expected near that, and on about
$0.3-0.7 more a session for the re-sent reasoning, which is mostly cached. The expected total is
about $17-20. The ceiling is 6 × $13.50 = $81.
