# The oracle ladder: at the ask's own place, what does each representation of a convention produce? (pre-registered 2026-10-08, before any call)

Step 2 of the convention-dossiers thread (`docs/research/conventions-dossiers-review-2026-10.md` §6;
`docs/todo/conventions-dossiers-exams.md`). The user (2026-10-08): *"okay let's start step 2"*. Step 1,
retrieval as the selector, is skipped for now. Nothing below has run.

## What it asks

Stage D (Result 7, `../conventions-ceiling-2026-10-04/README.md`) moved DeepSeek in two steps:
- the exact conventions' sentences (DE) took in-census reach from 0.22 to 0.44;
- the sentences with two maintainers' asks each and the precedence paragraph (DP) took it to 0.64.

A miss in review mixes four things:
- **where to look:** the session never reached the place;
- **applicability:** it reached the place and judged the code conforming;
- **the fix:** it judged a departure, but asked for another change;
- **the decision:** it saw the change and did not file it.

The adversarial round's separating test (§2.3) is a session's claim that the code conforms where the
maintainer asked. This stage runs that test at the place itself, where where-to-look and the decision
cannot intervene. Each ask is put to the model alone, one turn, in five forms.

**Two questions:**
1. **DP's 12 misses:** does DeepSeek get them right at the place, given DP's own text? If it does, the
   review lost them before or after understanding, and a richer representation (a dossier) has
   little to fix there.
2. **DP's 7 gains:** at the place, did the sentence already suffice? Or did the examples change
   what the model judges?

## The units

The 39 in-census asks of stage L and stage D's two sets: validation small12 (25) and post-cutoff (14).
- **Labels:** stage L's (`briefs_exact.json`). An ask's conventions are reader 1's entries (`r1`), as
  in its exact brief; eight asks have two.
- **The place:** the maintainer's comment's hunk, which GitHub ends at the commented line
  (`feedback.json` of `model-gap-val-small12` and `postcutoff-2026-09-29`).
  - p0000, v0053 and v0056 are comments on the PR as a whole.
  - v0016 is a file-level comment.
  - A comment's text never reaches the model.

## The arms

Every prompt begins with the same head: the PR's text (`probes.pr_markdown`, as in a reviewer's
`pr.md`), its whole diff (as in `diff.patch`), and the place. Then one of:

| arm | what follows the head | the model is told a maintainer asked here | DP's examples |
|---|---|---|---|
| **F** | "A Mathlib maintainer ... asked the author for a change at this place. What change did they most likely ask for?" | yes | no convention at all |
| **U** | the convention's sentence; "Does the code at this place conform? If it departs, write the change the convention calls for." | no | no |
| **UX** | U, with DP's two examples beneath the sentence | no | yes |
| **A** | "A maintainer ... asked ... a change at this place, under this convention:" the sentence; "Write the change they asked for." | yes | no |
| **AX** | A, with DP's two examples | yes | yes |

- **Output form.** U and UX answer `VERDICT: departs | conforms`, `CHANGE:`, `WHY:`. F, A and AX
  answer `CHANGE:` and `WHY:`. The exact text is `ladder.py` (`HEAD`, `ARM_TEXT`, `FORM_*`).
- **DP's examples** are rebuilt from `examples_prec.json` and the census bodies with DP's cuts and
  `probes.exemplified`.
  - All 46 convention blocks in the AX prompts were found verbatim in stage D's DP context files
    (checked 2026-10-08).
  - P392 has no example, so its three asks (34091 v0106-v0108) read the same in U and UX, and in A
    and AX.
  - P315 and P401 have one example each.
- **Size.** 195 prompts, 2.0k to 14.2k characters. They quote census bodies, so they are not
  committed (`.gitignore`). `items.json` lists each with its digest, `prompts.sha256` holds the
  digests, and `ladder.py build <bodies>` rebuilds them byte for byte.
- **The model and the call.** DeepSeek-V4.1-Flash on `first` (`serve_ds41.sbatch` defaults:
  patched nightly, DSpark, 1M context). Three samples an arm, single turn, no tools,
  `reasoning_effort: high`, `max_tokens` 32768, the server's default sampling. That is 585 calls
  (`run_ladder.sh`).

## Matching

- **One seal for the stage.** Per ask, the 15 outputs (5 arms × 3 samples) are shuffled into O1-O15
  by a seeded order (`blinding_SEALED.json`), written before any output is judged.
- **What a matcher sees.** Only each output's `CHANGE` text, never its verdict, its reason or its
  reasoning.
- **Two blind matchers,** subagents on the primary subscription, each judge every output against the
  maintainer's comment. The rubric (`matcher_rubric.md`) uses the reach matchers' value table
  verbatim, applied per output.
- `ladder.py unblind`, then `ladder.py read`.

## Reading rule, fixed before any call

- **An arm passes at an ask** on a matcher when at least 2 of its 3 samples are `reached`.
- **Each reading is made on matcher 1** and holds only if matcher 2 gives the same band; otherwise
  it is inconclusive.
- **The ask groups**, fixed from Result 7's matcher 1 tables before any call:
  - **DP's misses**, reached by DP in at most 1 of 3 reps, 12 asks: p0003, p0004, p0005, p0010,
    p0016, v0053, v0056, v0064, v0067, v0092, v0093, v0105.
  - **DP's gains**, reached by DP in at least 2 more reps than DE, 7 asks: p0000, p0007, v0029,
    v0062, v0063, v0068, v0090.
  - Matcher 2's own groups move only v0090, from gains to misses, and are reported beside.

**1. The floor.** If F passes at 24 or more of the 39 asks (0.6), the place alone carries most asks
for this model, and the representation contrasts below say little. They are still read, and that is
said.

**2. DP's misses: where were they lost?** Over the 12, sort each ask:
- **u:** UX passes. At the place, unasserted, with DP's own text, the model gets the ask. The review
  lost it to where it looked or to its decision.
- **s:** UX fails and AX passes. It writes the change when told, but judges the place conforming.
  This is applicability, the understanding of when a convention applies.
- **f:** UX and AX both fail. It cannot write the asked change even when told and shown examples. This is the
  fix shape, or what a check or a search would supply (single turn, no tools).

| reading | when |
|---|---|
| **the representation is not what DP's residual lacks on this model**: drop dossiers-as-understanding for DeepSeek (a `docs/dead-ends.md` entry naming this stage), and the residual goes to where-to-look and the decision | u ≥ 8 of 12 |
| **applicability is a measurable lever on the residual**: design V2's dossiers, with this ladder's UX form as their exam | s ≥ 4 of 12 |
| mixed: read the outputs at s and f | otherwise |

**3. DP's gains: what carried them, at the place?** Over the 7:

| reading | when |
|---|---|
| **not understanding at the place**: the sentence alone already passes, so DP's gain in review was where the session looked or what it would file (the precedence) | U passes at ≥ 5 of 7 |
| **the examples taught applicability** | U fails and UX passes at ≥ 4 of 7 |
| mixed | otherwise |

**4. Also read, all 39 asks, per matcher.**
- Gains and losses of each contrast: UX against U (examples, judged); AX against A (examples,
  told); A against U (being told, sentence); AX against UX (being told, with examples); A against F
  (the sentence once told).
- U pass against DE reach (≥ 2 of 3 reps), and UX pass against DP reach: whether the ladder's
  verdict at the place goes with what the review reached (the round's R2: the one validation the
  sizes allow).
- U and UX verdicts against their own CHANGE: a `departs` with a wrong change; a `conforms`.
- `finish_reason` other than `stop`, and answers without a `CHANGE` line.
- At s and f, the outputs and the kept reasoning, read by hand, sorted as rep 1's interim table
  sorted DP1's misses.

One ask is 1 of 12 in reading 2 and 1 of 7 in reading 3, so only the bands above are read.

## Limits, stated before

- **In-sample on the probe asks.** It diagnoses where the misses come from; it is not a gain. The
  exact conventions are a ceiling by construction, and here the place is given too.
- **One turn, no tools.** A miss that needs a search or a compile (v0105's library lemma, v0092 and
  v0093's merged forms, v0067's `positivity`) is disadvantaged in every arm alike. It sorts as f, and
  f is read as "the representation alone does not carry it", not as "a dossier would".
- **Memory.** Census merges predate DeepSeek-V4.1's release (2026-09-10); the probe PRs may be in its
  training data too. Only differences between arms on the same asks are read.
- **Telling is stronger than review.** U and UX ask about one place and one convention; the review
  held several of each and a whole PR. A U pass says the model *can* judge this place, not that a
  session would look there.
- **The matchers judge one line.** `CHANGE` only, so a correct change with its reason left in `WHY`
  is judged on the change.

## What it costs

- **Generation.** 585 single-turn calls on `first`, $0: about 12 minutes to serve, then perhaps one
  to two hours at 24 at a time. The node was empty when this was written (`squeue -w first`, 2026-10-08).
- **Matching.** Two matchers, 585 short answers, about 100k to 200k tokens each on the primary
  subscription (95% of its week when last read on 2026-10-08, resetting Friday 10:00). They wait for the
  user's word on when.

## Running note (2026-10-09): generated, not matched, and a provisional unblinded look

**Generated.** 585 of 585 answers, 11:18 to 13:21 on 2026-10-08 (`c0b90d93`). 66 stopped at the
pre-registered `max_tokens` with no answer, concentrated on hard asks: p0002 10, p0003 7, v0066 6,
v0105 6, p0010 5. No retry has run, and nothing is sealed or matched.

**An unblinded look, by the session that wrote this, at the 19 asks in the two groups.** It is not the
reading above, and every figure here is provisional.
- **DP's gains: the sentence alone (U) writes the maintainer's change at the place for 6 of the 7.**
  p0007, v0029, v0062, v0063, v0068 and v0090; p0000 is the exception. That is reading 3's first band:
  DP's gain in review was where the session looked, or what it would file, not understanding at the
  place.
- **DP's misses**, sorted into the three classes:
  - **u:** about 4-5 (p0004, p0016, v0056, v0092; p0005 borderline);
  - **s:** about 4-5 (p0003, v0064, v0067, v0093; v0105 borderline);
  - **f:** 2-3 (p0010, v0053; v0105 borderline).
- **In three of the s asks (v0064, v0067, v0093), U passes and UX does not.** With DP's examples the
  model judged the place `conforms`, where the bare sentence judged it `departs`. Over all 39 asks,
  `departs` verdicts are 93 of 117 for U against 88 for UX: UX is lower on 7 asks and higher on 4.
- **So the s band is reached, but not as the dossier idea needs it.** The applicability misses are
  ones that adding examples narrowed, not ones a richer representation would open.

**The user (2026-10-09):** DP without its examples is not a pressing question; choosing conventions
without the asks is the most important one. So the blind matching waits, and the thread turns to
selection.

## Deviation 1 (2026-10-09, recorded before it runs, at the user's word): the truncated calls are re-sent

**What happened.** 66 of the 585 answers stopped at the pre-registered `max_tokens` (32768) while
still thinking, and returned no answer: F 27, A 15, AX 10, U 9, UX 5. They concentrate on hard asks:
p0002 10, p0003 7, v0066 6, v0105 6, p0010 5. An empty answer would be judged `no`, so three of DP's
12 misses (p0003, p0005, p0010) would sort into "fails even when told" for want of room, not of
understanding.

**The change.** The user (2026-10-09): *"Yes let's queue the retry."*
- Each of the 66 calls is re-sent once (`ladder.py retry`): the same prompt, checked against its
  digest, and the same settings, but with `max_tokens` 131072.
- The answers go to `outputs_retry.jsonl`. `outputs.jsonl` stays as committed.
- `match-inputs` uses a retried row wherever one exists.
- A call that stops at the limit again is reported, and is matched as no answer.

**It runs** while the places test holds the server (`../conventions-places-2026-10-09/`), eight at a
time, as its own Slurm job on `first`.

**What it does not change.** Nothing is sealed or matched yet. The reading rule, the arms, the prompts
and the other 519 answers are untouched. The unblinded look in the running note above was made before
the retry and stays as written.

## Result (2026-10-09): at the place, the convention's sentence carries the ask; DP's gains were within the bare sentence's reach; DP's examples lower the model's verdicts

**How it was matched.**
- **The answers:** 585, with deviation 1's retried rows used where present (`d2cf4c53`). One answer is
  empty (p0003 A, sample 1), truncated twice.
- **The seal:** committed before any judging (`15c8b3e2`).
- **The matchers:** two blind matchers, subagents of the session, each handed its generated prompt
  verbatim. Each saw only each answer's `CHANGE`, shuffled per ask.
  - Audit: 14 tool calls each, 0 flagged.
  - Totals: 322 and 355 `reached`; agreement on reached-or-not 552 of 585.
  - Tokens: 132k and 128k on the primary subscription, after the weekly reset.
- **The reading:** `ladder.py unblind`, then `ladder.py read`.

**Arms passing at the 39 asks** (at least 2 of 3 samples `reached`), matcher 1 / matcher 2:

| F (told, no convention) | U (sentence, judged) | UX (with examples, judged) | A (sentence, told) | AX (with examples, told) |
|---|---|---|---|---|
| 5 / 6 | 25 / 29 | 21 / 25 | 29 / 29 | 27 / 29 |

**By the rule, on both matchers:**
- **1. The floor holds:** F passes at 5 / 6 of 39, far under 24. So the place alone does not carry the
  asks, and the contrasts below say something.
  - **The convention's sentence is what carries them:** A against F gains 24 / 23 asks and loses
    none.
- **2. DP's 12 misses: mixed**, on both matchers.

  | class | matcher 1 | matcher 2 |
  |---|---|---|
  | u (UX passes) | 4 | 6 |
  | s (UX fails, AX passes) | 3 | 3 |
  | f (both fail) | 5 | 3 |

  - **Neither band is reached:** u would need 8 or more, s 4 or more.
  - **Stable across both matchers:**
    - **u:** p0004, p0016, v0067, v0092. These are lost in review to where it looked or to its
      decision.
    - **s:** p0005, v0064, v0093. These are judged conforming with examples, and written when told.
    - **f:** p0003, p0010, v0105.
  - **The matchers split on v0053 and v0056** (matcher 2: u; matcher 1: f), the two PR-description
    asks.
- **3. DP's 7 gains: the sentence alone already passes at the place**, for 5 of 7 (matcher 1) and 6
  of 7 (matcher 2): p0007, v0029, v0062, v0063, v0068, plus v0090 on matcher 2. That is the band "not
  understanding at the place". DP's gain in review was where the session looked, or what it was
  licensed to file.

**Also read.**
- **The examples lower the judged verdicts.** UX against U is +1 / −5 on matcher 1 and +0 / −4 on
  matcher 2. Told, they are about neutral: AX against A is +1 / −3 and +2 / −2. The provisional
  look's direction holds blind.
- **Being told helps a little:** A against U is +4 / −0 and +3 / −3.
- **At the place, the sentence reaches more than the review did.**
  - Matcher 1: U passes at 25 asks. DE's review reached 17 (at least 2 of 3 reps).
  - Of U's passes, 13 are asks DE's review did not reach, and only 5 asks go the other way.
  - DP's review gets 18 / 17 of what UX gets at the place; UX passes at 4 / 7 asks DP's review did
    not reach.

**What it means, at this altitude** (one model, one turn without tools, in sample, two matchers).
- **The knowledge in the sentence is enough for most asks once the place is fixed.** What the
  reviewer lacks in review is putting the question at the place: attention, plus the licence to file.
- **A richer representation (more examples) did not help understanding at the place;** in the
  judged form it hurt. So the dossier thread's understanding hypothesis, as a lever for DeepSeek,
  finds no support here.
  - What remains of "understanding" is three stable s asks and three f asks.
  - The f asks need a fact (p0010's orientation), a search (v0105), or the right comparison (p0003's
    `HasProd` sibling).
- **This is the measured ground for the per-place engine,** which asks every convention's question
  at every place. Whether that question also says `departs` where no maintainer asked is the places
  test's question (`../conventions-places-2026-10-09/`).
