# The conventions ceiling probe, stage L: the local model first (pre-registered 2026-10-04, before any session)

The probe is `docs/todo/conventions-ceiling-probe.md`: brief a reviewer with census conventions at
four levels of specificity and compare it with unbriefed sessions. Its reviewer is Claude Opus 5.5,
at about 1.5 subscription windows for the exact step. The user (2026-10-04): *"Let's start with
testing the local model first before any paid API runs."* This file fixes what the local stage runs
and how it is read. The Claude stage's sets, briefs and reading rule are the todo's, unchanged.

## What stage L can and cannot say

- **It tests the machinery for nothing:** labels, the exact brief, its delivery, the seal and the
  matching all run once on a free reviewer before a subscription window is spent.
- **It measures a design the record names as untried.** Thirteen prompt settings left this model at
  the floor (`local-unlock-2026-10-03`, branch `local-model-unlock`: best single pass 3 of 23), and
  that screen closed on "supplying the knowledge rather than asking for it". Its conventions
  setting (C: 1 of 23, the most volume and the worst aim) held guide summaries, never the
  conventions that apply to the PR. The exact brief is that supply.
- **It is not Claude's ceiling.** The model sits at the floor and does not carry out process
  instructions (same screen). A null here bounds nothing for Claude, so the Claude step does not
  wait on this stage's sign.

## Sets

The todo's two, PR-disjoint from the census: reader A labelled 2,102 asks on 754 PRs, and none is
among these 21 (re-checked 2026-10-04 against `arm-coverage-val1000-*/events.jsonl` and the outside
sets' packet manifests).

| set | asks | PRs with asks | controls |
|---|---|---|---|
| validation small12 | 30 | 8 | 3 |
| post-cutoff | 16 | 6 | 4 |

## Conditions

The reviewer is `Qwen/Qwen3.5-397B-A17B-FP8` on `first` (`../local-vllm-2026-10-02/serve.sbatch`,
8 GPUs, MTP, port 8012), contract v2 under `ape_agent`, reasoning off: the setting of its dev record
(2, 0, 2 of 23, `../local-quality-2026-10-02/`). Contract v2's brief is brief X with the reading
order changed, so it is this harness's X. It has never run on either set, so the stage runs its own
baseline. Configs: `configs/pr_review_v5_val_small12_local397_contract2.yaml` and
`configs/pr_review_v5_probe_2026_07_08_v1_local397_contract2.yaml`.

| label | the reviewer reads | PRs | reps | run name |
|---|---|---|---|---|
| LB | the PR model | all 11 and all 10 | 3 | `iter_local397_conv_<val\|post>_base_rep<n>` |
| LE | the PR model, then the exact section | the 8 and the 6 with asks | 3 | `iter_local397_conv_<val\|post>_exact_rep<n>` |

- **The exact section** is the todo's: two readers label the 46 asks against reader A's codebook
  (438 entries at `2bb3063a`), assign-only (`reader_rubric_assign.md`); a PR's section is the union
  of their entries, as sentences, in codebook order, with no location.
- **The section's text is fixed here**, the same for every level and both stages; only the entries
  differ (`probes.conventions_section`):

  > These are conventions Mathlib's maintainers hold when they review, one sentence each: a
  > situation and the form preferred in it. They are stated in general, and none names a place in
  > this PR. Check the changed code against each one. Where it departs from a convention, request
  > the change that convention calls for, as a finding at the place it applies.

- **Delivery differs from the Claude stage, and is stated, not fixed.** The solo task's brief is
  one file a run, and its per-PR channel is `context_file`, so the section follows the PR model in
  the user message, before the diff. A Claude packet will carry it at the end of `brief.md`.
- **Common and all** (the top 50, all 438) run on the local model only if LE clears the bar below.
  Generating them is free; matching them is not.

## Matching

One seal per set, on the PRs with asks, holding LB1-3, LE1-3 and Claude's X1 and X2 from the
baselines on disk. X is the anchor: it read 0.48 / 0.50 (validation) and 0.47 (post-cutoff), and a
matcher that reads it far from that is read with that in mind. Two blind matchers per set, the
harness's rubric, labels shuffled per PR, condition cues redacted, then the audit.

## Reading rule, fixed before any session runs

Per-session reach on the **in-census asks** (at least one reader assigned an entry), on each
matcher, pooled over the two sets and reported per set. Asks reached per finding must be no lower
under LE than under LB.

| LE − LB, on both matchers, pooled | reading |
|---|---|
| **≥ +0.15** | **the conventions that apply move even the floor model.** Knowledge supply is a lever where thirteen prompt settings were not. The local tier can then carry the ladder (common, all) for nothing. |
| **≤ +0.05** | **this model does not turn a stated convention into the ask.** A fourteenth setting that leaves it at the floor, recorded beside the local-unlock screen. Nothing about Claude's ceiling. |
| between | inconclusive at this size (138 cells a condition): read the transcripts before saying more. |

**Also read, not in the rule:**
- the in-census share of the 46 asks, per reader and in union: it bounds the ceiling for every
  reviewer before any session runs;
- out-of-census asks under LE, the within-session control (they should not move);
- findings per PR, and findings per control PR under LB;
- how many LE findings restate an entry of their brief without a place in the code, and how many
  matched asks came from such a finding: how much of any gain is the brief handing over the ask;
- for an in-census ask LE still misses, whether the session's `notes` mention the convention.

## What the stage costs

- **Generation:** GPU time on `first`. The dev held-out 12 took a few minutes a run at concurrency 12.
- **Subagent runs on the subscription:** 2 readers (46 asks and a 16k-token codebook each) and 4
  matchers (2 a set). No Claude reviewer session. Measured tokens are recorded below as they run.

## Result 1 (2026-10-04): 39 of the 46 asks are in census, and the two readers agree on every one

The todo's first step. Two blind readers, each in a folder holding the rubric, the codebook and the
batch (`build_reader_folders.py`); both transcripts audit clean (6 and 8 tool calls, none outside the
folder). Labels are `readers/labels_{1,2}.jsonl`, the briefs `briefs_exact.json`
(`build_exact_briefs.py --print-briefs` prints each PR's).

| | asks | reader 1 assigned | reader 2 | in census (either) | both | same primary entry |
|---|---|---|---|---|---|---|
| validation small12 | 30 | 25 | 24 | **25** | 24 | 24 |
| post-cutoff | 16 | 14 | 14 | **14** | 14 | 14 |
| both | 46 | 39 | 38 | **39 (85%)** | 38 | **38 of 38** |

- **Census coverage does not bound the ceiling.** 85% of the asks have an entry behind them, on PRs
  the census never read, and 14 of 16 on PRs created after it was written from.
- **The seven outside** are, on both readers: four `specific` (three docstring slips or typos and a
  doubt about one wording), two `out_of_census` (no index on a hypothesis name when the plain name is
  free; `_anti`, not `_mono`, for passing to smaller objects) and one `unreadable` (a bare "Same
  here."). The one ask the readers split on, 26755's file-wide `noncomputable` clean-up, reader 1
  put under P100 (a change made for one sibling is made for the others) and reader 2 left out with
  P100 as the nearest.
- **By family:** proof 11 of 11, interface 8 of 8, PR level 4 of 4, derive 2 of 2, statement design
  2 of 2, generality 2 of 2, formatting 1 of 1, registration 3 of 4, naming 4 of 6, documentation 2
  of 6. The asks outside the census are mostly documentation slips, which have no principle.
- **The briefs are short and general:** 28 distinct entries, 0 to 5 a PR (18 sentences on the 8
  validation PRs, 15 on the 6 post-cutoff). One PR, 43024, has an empty brief: its only ask is out of
  census, so its briefed session reads the model alone.
- **Where the union matters:** reader 1 gave a second entry on 7 asks and reader 2 on 1. Four briefs
  hold an entry only reader 1 gave: P100 on 26755 and on 43192, P401 on 32875 and P086 on 42814.
- **Cost:** 134,923 and 136,802 subagent tokens, 5.3 and 5.6 minutes.

## Result 2 (2026-10-04): +0.051 on both matchers, at the lower edge of the rule; the brief steadies what the model already reaches and opens one new ask

Twelve local runs (105 sessions, every one completed, no retry, 98.6M processed tokens, $0.00), one
seal a set, two blind matchers a set, all four transcripts audited clean. The matchers agree on
236 of 240 cells on validation and 127 of 128 post-cutoff. `read_stage.py L LE LB` prints the tables.

| per-session reach, in-census asks | LB (unbriefed) | LE (exact section) | LE − LB | Claude X, same seal |
|---|---|---|---|---|
| validation, 25 asks | 2/75 = 0.03 | 7/75 = 0.09 | | 0.36 / 0.44 |
| post-cutoff, 14 asks | 2/42 = 0.05 | 3/42 = 0.07 | | 0.43 / 0.43 |
| **pooled, 39 asks** | **4/117 = 0.034** | **10/117 = 0.085** | **+0.051** | 0.38 / 0.44 |

The local model's cells are identical on the two matchers; only Claude's differ.

**By the rule: +0.0513 is six cells of 117, where the `≤ +0.05` line is 5.85 cells. So the letter
says "between: inconclusive at this size", at the very bottom of that band.** It is far from the
+0.15 that would make knowledge supply a lever for this model. Provisional: one model, three reps,
39 asks.

**What the six cells are.**
- Four are one PR. 36822's two asks (a moved declaration keeps its attributes, P098: `to_dual`
  dropped `simp`) go from 1 of 3 reps to 3 of 3.
- One is 43167's unused import (P030), from 2 of 3 to 3 of 3.
- One is new: 28649's docstring abbreviation ask (P278), reached once.
- So the asks reached in any rep go from 3 to 4 of 39, where Claude's X1 and X2 together reach 16
  (matcher 1) and 18 (matcher 2). **The section makes this model's reach repeatable; it does not
  widen it.**

**Also read.**
- **Near misses appear only under the section:** `partial` cells on in-census asks are 0 for LB and
  4 for LE, on both matchers. Each is the right convention at a neighbouring place or in another
  form: three sibling `noncomputable`s removed but not the one the maintainer named (26755); a
  `grind =` tag asked for on the lemma itself, not the two it rewrites with (32875); two golfs of
  the right lines with another tactic (30641). Reached or partial: 4 against 14 of 117.
- **Asks per finding did not fall:** 13 of 29 findings for LB, 21 of 42 for LE (0.45, 0.50). The
  section adds findings on the ask PRs (29 to 42 submissions over three reps) at the same aim.
- **The out-of-census asks moved too, 9/21 to 11/21, and for a reason.** Both cells are 28649's
  doubt about "variance" against "variances", which sits in the docstring hunk the brief's two
  documentation entries sent the model to. An out-of-census ask that shares a hunk with an
  in-census one is not a control; the other six such asks did not move.
- **No finding hands the brief back.** All 42 LE findings name a file and a line; none restates an
  entry without a place.
- **Where it missed, the notes show the convention checked and the code passed, or the convention
  never raised.** Read on four validation PRs, three reps each, by the brief's own terms:
  - 30641: `gcongr` is named in 2 of 3 briefed sessions' notes and in no unbriefed one. One wrote
    "`gcongr` doesn't apply here as verified", at the step the maintainer asked `gcongr` for.
  - 32875: the brief's terms appear in 2 of 3 briefed sessions. One quoted "A short tactic block
    that a single term proves is written as that term" as something the PR already follows.
  - 29842 and 34091: none of the six briefed sessions' notes names its brief's entries (motivation
    for a new concept; a class hypothesis taken instance-implicit). 29842 draws no finding, and
    34091 the three docstring findings it draws unbriefed.
- **Empty reviews persist with the conventions in hand.** 29842 draws no finding in six sessions
  and 41930 none from any of the eight reviewers, Claude included.
- **Controls, LB only:** 32080 draws 5 findings in each rep and 26185 and 34935 between 0 and 3;
  the four post-cutoff controls draw none.

**The anchor.** Claude's X on all asks reads 0.37 / 0.43 on validation, under the 0.48 / 0.50 its
own matching gave, and 0.50 / 0.47 post-cutoff against 0.47. Validation's matchers here are
stricter, mostly on whether a different golf of the same lines reaches the ask. LE − LB is within
one seal, so it does not depend on that; a comparison with the published X figures would.

**What it means, at this altitude.**
- For this model, on 35 of 39 in-census asks, being told the convention that applies is not what
  was missing. The step it fails is seeing where the code departs from the convention.
- That is the local-unlock screen's reading again ("judgement at attended sites"), now with the
  knowledge supplied rather than asked for.
- It says nothing about Claude's ceiling, as stated before the runs.

**Untried on this model:** the section with the over-file brief (the one setting that raised its
single-pass reach); the conventions with their places, as candidate asks the model only vets;
reasoning `high`; a stronger open model.

**Caveat.** Whether Qwen3.5's training data holds the validation PRs is not known. Only the
between-brief difference is read, where both conditions share the same memory.

**Cost.** Generation: 12 runs of 7 to 14 minutes, two queues side by side on one server. Subagents:
773,270 tokens over six runs (readers 134,923 and 136,802; matchers 136,359, 185,433, 92,199 and
87,554). No Claude reviewer session ran.

**What ran, in order.** `build_reader_folders.py`, two readers, `build_exact_briefs.py`,
`build_context.py base|exact`, `run_local.sh <val|post> <base|exact> <1-3>`, then per set
`cli probe seal`, `cli probe match-inputs` with `sources_L_<set>.json`, two matchers,
`cli probe audit`, `cli probe unblind` into `match_L_<set>/unblinded.json`, and `read_stage.py`.
`session_stats.json` counts a session's submission; a run directory's `findings.jsonl` is after
anchoring and can be shorter.

## Stage C: the Claude exact step, sized to the window (pre-registered 2026-10-04, before any session)

The user (2026-10-04): run Claude, *"but let's try to think about how we can get a result
efficiently. We have less than the estimated subscription window (we can use tokens B and C, but one
of them has used 80% of the session already)."* The step as the todo wrote it is two briefed
sessions on each of 14 PRs. This section fixes a smaller step that reads the same rule, and what
was measured to justify each cut. Nothing below has run.

**Measured before designing.**
- **The todo's estimate was low.** X's sessions on disk (session `029323d7`: `general-purpose`
  subagents, `claude-opus-5-5`, effort xhigh, CLI 2.1.284) processed a median 2.26M tokens on
  validation and 1.74M post-cutoff. 28 sessions on these PRs is about 62M, near three five-hour
  windows at the record's 20-24M a window, not 1.5.
- **The windows, read at 09:10:** token C at 0% (resets 14:10); token B at 81-83% and rising
  (resets 11:50).
- **Unbriefed Claude is close to deterministic per ask.** X1 and X2 give the same outcome on 37 of
  the 39 in-census asks, on both of stage L's matchers. On the construction demonstration's 16 asks,
  which have four unbriefed sessions, an ask X1 and X2 both missed was reached by X3 or X4 in 0 of
  18 cells (matcher 1) and 0 of 12 (matcher 2), and an ask both reached was missed in 0 of 14 and 0
  of 18.
- **The headroom is on ten PRs.** Neither X session reaches 23 (matcher 1) or 21 (matcher 2) of the
  39 in-census asks, and every one of those is on ten PRs. On 26755, 36822 and 43192 both sessions
  reach all six in-census asks on both matchers; 43024 has no in-census ask.

**The step.**

| | the todo | stage C |
|---|---|---|
| briefed sessions a PR | 2 (E1, E2) | **1 (E1)**: a second session repeats the first on 37 of 39 asks |
| PRs | 14 | **10**, those with an in-census ask no X session reached |
| the other PRs | run | 26755, 36822, 43192 enter as E = X (6 of 6 asks, from stage L's matching); 43024 has no in-census ask |
| expected processed tokens | about 62M | **about 23M** (X's own cost on the ten) |

- **Order:** missed asks per expected token, so a spent window leaves the most informative prefix:
  30641, 29842, 41930 (batch 1, about 3.6M, which also meters the window), then 32875, 42814, 30458
  (about 9.4M), then 28649, 42184, 43167, 34091 (about 10M).
- **Metering:** each batch's stream reports the window's utilisation (`batch_report.py`). A batch
  starts only if its expected tokens fit what the window has left; the rest waits for token B's
  reset.
- **Route:** `run_claude_batch.sh` starts a headless Claude Code session on the token and has it
  spawn each reviewer as a `general-purpose` subagent with `probes.SESSION_PROMPT`, as X1 and X2
  were spawned. `claude-opus-5-5`, effort xhigh, real `HOME`. It differs from X's route in three
  ways: CLI 2.1.285 for 2.1.284 (the nearest binary on disk), a headless parent, and foreground
  subagents. Model, effort and version are read back from the first batch's stream.
- **Packets** (`cli probe packets --conventions briefs_exact.json --codebook …`): `pr.md`,
  `model.md` and `diff.patch` are byte-identical to X1's, and `brief.md` is brief X followed by the
  section. `briefs_exact.json` is the file stage L read.
- **What sits beside the packets now.** When X ran, no feedback had been extracted. Now `asks.json`,
  `feedback.json`, X's findings and this README are in the tree. The session prompt's rule (read
  only your own directory) is the same; every E transcript is audited before matching, and a session
  that read outside its packet is dropped and rerun.

**Reading rule: the todo's, unchanged.** Per-session reach on the 39 in-census asks, pooled, on each
of two blind matchers: E − X, with `≥ +0.15` conventions are a good direction, `≤ +0.05` low
ceiling, between inconclusive. With the six imputed asks equal on both sides, that is a net gain of
**at least 5.85 asks** on the ten PRs' 33, or **at most 1.95**. Asks reached per finding must be no
lower than X's. One seal a set holds X1, X2 and E1 on that set's run PRs, so X is re-judged beside E.

**Steps that run only if the reading calls for them, fixed now:**
- **E2 on the ten PRs:** only if E1's difference lies strictly between +0.05 and +0.15 on either
  matcher.
- **The three PRs not run:** only if the difference is within 0.03 of a threshold. One lost ask is
  0.026, and a brief can only lose there.
- **A route control** (a fresh unbriefed session on 30641 and 29842 through this route, about 2.6M):
  only if E1 reads `≥ +0.15`, before the ladder is built on it.

**Provisional by construction:** one briefed session a PR, one model, 39 asks.

## Result 3 (2026-10-04): with the exact conventions Claude reaches 74% of the in-census asks against 46-49% without; +0.26 and +0.28, a good direction by the rule

Stage C as pre-registered above: one briefed session (E1) on each of the ten PRs, matched blind
beside X1 and X2. `read_stage.py C1,C2 E X --impute 26755 36822 43192` prints the tables.

| per-session reach (issue recall) | X, unbriefed | E, exact section | E − X |
|---|---|---|---|
| **in-census asks, pooled (39), the rule's measure** | 0.49 / 0.46 | **0.74** / 0.74 | **+0.256 / +0.282** |
| validation (25) | 0.52 / 0.48 | 0.76 | +0.24 / +0.28 |
| post-cutoff (14) | 0.43 | 0.71 | +0.29 |
| all asks in the tables (44 of 46) | 0.48 | 0.70 / 0.73 | +0.23 / +0.25 |
| out-of-census asks on the run PRs (5) | 4/10, 6/10 | 2/5, 3/5 | 0.00 |

Two figures in a cell are matcher 1 and matcher 2.

**By the rule (`≥ +0.15` on both matchers, pooled): conventions are a good direction.** On the ten
run PRs' 33 in-census asks the briefed session reaches 23, where an unbriefed session reaches 13
(matcher 1) or 12 (matcher 2): a net gain of 10 to 11 asks against the 5.85 the rule needs.
Provisional: one briefed session a PR, one model, and a ceiling by construction.

**Beside the rule.**
- **Nothing was lost.** On both matchers, every ask an unbriefed session reached, the briefed one
  reached too. Twelve asks differ, all toward E. Nine of them no X session reached on either
  matcher: `gcongr` for a monotonicity step (30641), `simpa` for a two-step close (32875), two
  section and `variable` layout asks (30458), a docstring abbreviation (28649), `mk_iff` and a
  shared `variable` (42814), a prime replaced by a named variant (43167) and a `HasProd` sibling
  (42184).
- **It is not volume.** E filed 59 findings on the ten PRs, X 52.5 a session. Asks reached per
  finding rise from 0.29 to 0.42 / 0.44.
- **The within-session control held.** The five out-of-census asks on the run PRs did not move on
  either matcher.
- **Near misses became hits.** `partial` cells on in-census asks: 11 / 13 for X's two sessions, 1
  for E.
- **By family** (in-census, ten PRs; X per session, then E): proof 6.5 / 5.5 to 9 of 11; interface 3
  to 6 of 6; naming 0.5 to 2 of 3; derive 1 to 2 of 2; statement design 0 to 1 of 2; documentation 0
  to 1 of 2; generality 1 and 1 of 2; registration 0 and 0 of 1; **PR level 0 and 0 of 3**.
- **Both sides of the cutoff.** The gain is +0.29 on PRs created after Claude's training data and
  +0.24 / +0.28 on those inside it.
- **Against the local model.** The same sections took the local 397B from 0.034 to 0.085. The
  knowledge is usable by a reviewer that can already find where it applies.

**What the briefed reviewer still missed: 10 of 39.** Read from its `notes.md`, by me and not blind.
- **Convention weighed, condition judged unmet (6).** "No iff here has its directions used
  separately" where the maintainer asked for an alias (42814); "the Int- and Nat-specific lemmas
  are inherently specific" where the maintainer asked whether it holds in any UFD (42814); "also
  compiles as a term. That is a matter of taste, not an ask" (32875); and the three PR-level asks
  for motivation, set aside as "does not apply, since this is a generalization rather than a new
  concept" (29842, twice) and "too minor to be an ask" (41930). These are design and judgement
  calls a one-sentence convention does not carry, and brief X itself tells the reviewer not to
  file questions.
- **Right convention, neighbouring place (2).** The `grind` tag put on the lemma itself, not the
  two it rewrites with (32875, `partial`); the author's-taste convention applied to one rewording
  and not to the one the maintainer objected to (28649).
- **Convention too general to pick the comparison (1).** `left`/`right` swapped against the
  library's orientation (43167): the brief said "follow siblings' and analogues' names", and the
  session compared with local siblings.
- **Never attended (1).** "Surely this is a one-liner using `infinite_pigeonhole_card_lt`" (34091).

**And why unbriefed Claude missed what the brief recovered.** On the post-cutoff asks its notes show
local precedent used as the standard ("the name matches local siblings… the file's own convention
wins"; "same pattern as `discr_def` by the same author"), an ask seen and withheld ("Considered and
not filed: a companion `HasProd.nonneg`"), and a repeated binder never mentioned. It was looking at
the right declaration and judging it against the file, not the library.

**How it ran.**
- Ten sessions: nine on token C (09:20-10:01), 34091 on token B after its reset (11:52). Every
  assistant entry reads `claude-opus-5-5`, effort xhigh, CLI 2.1.285; every prompt was handed over
  verbatim. Audits: one flag in ten transcripts, benign (41930's session ran the project's Python by
  its absolute path to check its own JSON).
- **Cost.** A five-hour window is about 3M tokens weighted by list-price ratios (29-31k a point),
  not the 20-24M processed the record gave. The ten sessions took 97 points, one window; a briefed
  session cost 52-70% of an unbriefed one on the same PR. `batch_report.py` meters it.
- **Matching, as it ran, not as first stated.** Post-cutoff (four PRs) was matched by subagents of
  the orchestrating session, which that login's limit stopped after both had written complete files
  (33 cells each, checked by `check_matches.py`, transcripts clean; agreement 33 of 33). Validation
  (six PRs, one seal) was matched headless on token B (agreement 76 of 81). Both deviations were
  committed before the cells they touch were judged (`a53e264b`).
- **Imputed:** 26755, 36822 and 43192 enter as reached by X and by E (6 asks), from stage L's
  matching. Two out-of-census asks on PRs not run (43024, 43192) are in no table.

**Limits, stated.**
- **A ceiling, not a reviewer.** Each section was built from the PR's own maintainer asks. Its
  length hints at how many asks there are, and it tells the reviewer which conventions are in play,
  which is the hard part of the task. What a reviewer can do without that is the ladder's question.
- **Selected PRs.** The ten were chosen because X missed asks there. Four unbriefed sessions on
  three of them recovered none of the asks two had missed (0 of 18, 0 of 12), so regression to the
  mean is small, but it is not zero by proof.
- **The route differs from X's** (a headless parent, CLI 2.1.285 for 2.1.284). The out-of-census
  asks and the finding volume say the route did not change the reviewer; the route control below
  tests it directly.

**The route control: the route is X's** (`route_control.sh`; its rule was committed in `dbcec290`
before the run). An unbriefed session, XR1, with brief X byte for byte, ran on 30641 and 29842
through the briefed sessions' route on token B and was matched beside X1, X2 and E1 by two new
blind matchers (`match_R_val/`, `read_stage.py R XR X`).

| in-census asks on the two PRs (7) | X1, X2 | XR1 | E1 |
|---|---|---|---|
| per-session reach, matcher 1 / 2 | 4/14 = 0.29 / 0.29 | 2/7 = 0.29 / 0.29 | 5/7 / 4/7 |

- XR − X is 0.000 on both matchers, and XR reaches no ask that both X sessions missed. It differs
  from X on two asks, both ones X1 and X2 themselves split on.
- It files as X does: 8 findings on the two PRs against X's 7 a session (E: 10).
- By the rule fixed before it ran there is no route effect, and stage C's difference stands
  against X. Its power is small, as stated: two PRs, 7 asks.
- A cell moves between matcher instances: this seal's matcher 2 reads one of E's golfs on 30641 as
  `partial` where stage C's read it `reached` (agreement here 27 of 32 cells).
- Cost: 18 points of token B for the two sessions and 8 for the two matchers. Both audits clean.

## Stage F: the floor -- the same reviewer briefed without the asks (pre-registered 2026-10-04, before any selector or session)

The user (2026-10-04): the exact brief is *"a sort of a ceiling"*, and it cheats by looking at the
maintainers' asks. *"Without relying on the asks, what gives the reviewer the best shot at doing the
reviewing using the conventions as effectively as possible?"* This is the todo's ladder, designed
from what stage C showed. Nothing below has run.

**What is already known, without a session.**
- **A fixed common list is bounded low.** The 50 most-used census entries hold the entry behind 16
  of the 33 in-census asks on the ten PRs, and behind 4 of the 9 asks only the briefed reviewer
  reached (the top 25: 10 and 2; the top 100: 25 and 6). The gain was in the tail: `gcongr` for a
  monotonicity step is rank 174 of 438, `simpa` rank 323, docstring abbreviations 126, an alias for
  an iff 128. Unbriefed Claude already applies the head. So the todo's "common" level is not run.
- **The record's ask-free deliveries were general text to weaker reviewers:** distilled guides
  ("statute", null on gpt at N=115) and guide summaries as a directive (local-unlock C, 1 of 23).
  The plan's own ask-free design is deterministic detectors keyed to a declaration
  (`docs/plans/2026-10-03-after-structure.md` §2), which is code. A selector is the same idea with
  a model doing the detecting.

**The design: applicable.** One variable changes from stage C: who picks the entries.
- **A blind selector a PR** (`selector_rubric.md`, `build_selector_folders.py`): a `general-purpose`
  subagent, `claude-opus-5-5` at xhigh, whose folder holds the reviewer packet's own `pr.md`,
  `model.md` and `diff.patch` (byte-identical to X1's), all 438 entries as `P### sentence`, and the
  rubric. No tools on the repository, no asks. It writes at most 25 entries, each with where its
  situation occurs.
- **It selects on the situation, not on conformance.** "If the situation occurs, the convention
  applies, whether the code seems to conform or not." Stage C's unbriefed misses were the reviewer
  judging the code against its own file and passing it; a selector that filtered on "looks
  violated" would repeat that judgement and drop the same asks.
- **No frequency prior.** The rubric says a rare convention matters as much as a common one.
- **The brief** is brief X plus the section, the same lead as every level, the selected sentences
  in codebook order with no location (`briefs_applicable.json`, `cli probe packets --conventions`).
  The selector's `where` is kept and not delivered.
- **The reviewer** is session A1: the ten stage C PRs, one session each, the stage C route
  (`run_claude_batch.sh`), model, effort and CLI.
- **Matching:** one seal a set holding X1, X2, E1 and A1, so the ceiling and the unbriefed reviewer
  are re-judged beside the floor by the same two blind matchers.

**Read before any reviewer session: retrieval.** For each of the 33 in-census asks, whether an
entry behind it is in the PR's applicable brief (`build_applicable_briefs.py`). This bounds what A
can recover. If the briefs hold the entry of fewer than 11 of the 33, the reviewer sessions are not
spent: the floor is bounded by retrieval, and that is the result.

**Reading rule, fixed now.** The same measure as stage C: per-session reach on the 39 in-census
asks, pooled, each of two matchers, with 26755, 36822 and 43192 imputed as before.

| A − X, on both matchers | reading |
|---|---|
| within 0.05 of E − X | **the floor is at the ceiling**: picking conventions from the diff is enough |
| `≥ +0.15`, more than 0.05 under E − X | **the direction survives without the asks**; the gap is decomposed below |
| between +0.05 and +0.15 | partial |
| `≤ +0.05` | **the gain needed the asks' own pinpointing**: the floor is the unbriefed reviewer |

Asks reached per finding must be no lower than X's.

**Also read, fixed now.**
- **The decomposition.** For each in-census ask: was its entry in the brief (retrieval), and if it
  was, did A reach it (application), beside whether E and X did. A gap to the ceiling is then
  retrieval's or application's.
- **Dilution:** asks A misses with the entry in its brief that E reached with the exact brief.
- **Cost of the brief:** findings a PR against X's and E's, and out-of-census asks.
- **Not measured:** control PRs. An ask-free brief could be given to them; these sessions are not.

**Untried, in the order I would try them if A falls short:** the reviewer selecting for itself from
all 438 in its packet, then applying (no separate stage); the selector's `where` delivered with each
sentence; a past ask as an exemplar of each selected entry (the census holds 2,102, on other PRs);
two selectors in union; detectors in code for the head entries.

**Cost, expected:** ten selectors at about 3 points of a window each, ten reviewer sessions at
about 10 to 12, four matcher runs at about 7. Selectors run on token B's remainder now; reviewers
on token C from its 14:10 reset; whatever does not fit waits for B's 16:50 reset.

## Result 4 (2026-10-04): the floor is the unbriefed reviewer -- conventions picked from the diff move issue recall by +0.03, where the exact ones move it by +0.28

Stage F as pre-registered above. Ten blind selections, ten briefed sessions (A1), and one seal a set
holding X1, X2, E1 and A1, so the three conditions are judged together by the same two matchers.
`read_stage.py F A X --impute 26755 36822 43192` and `decompose_floor.py` print the tables.

| per-session reach (issue recall), matcher 1 / 2 | X, unbriefed | A, 25 picked from the diff | E, exact |
|---|---|---|---|
| all asks in the tables (44) | 0.45 / 0.43 | 0.48 / 0.45 | 0.70 / 0.68 |
| **in-census asks, pooled (39), the rule's measure** | 0.46 / 0.44 | **0.49 / 0.46** | 0.74 / 0.72 |
| difference from X | | **+0.026 / +0.026** | +0.282 / +0.282 |
| validation, in-census (25) | 0.48 / 0.44 | 0.48 / 0.44 | 0.76 / 0.72 |
| post-cutoff, in-census (14) | 0.43 | 0.50 | 0.71 |
| out-of-census (5) | 0.40 | 0.40 | 0.40 |

**By the rule (`≤ +0.05` on both matchers): the gain needed the asks' own pinpointing.** With this
delivery the floor is the unbriefed reviewer. The ceiling replicates under new matchers: E − X is
+0.282 on both (stage C read +0.256 and +0.282). Provisional: one selector design, one session a PR.

**Where the gain went: retrieval against application** (the 33 in-census asks on the ten PRs).

| | asks | X, a session | A | E |
|---|---|---|---|---|
| an entry behind the ask is in A's brief | 22 | 10.5 | 12 | 18 |
| it is not | 11 | 1.5 / 0.5 | 1 / 0 | 5 / 4 |

- **Retrieval kept two thirds.** The selector's 25 hold the entry of 22 of the 33 asks, and of 7 of
  the 10 asks only the exact brief reached.
- **Application lost more than retrieval did.** Of those 10 asks A reaches 2: three were lost because
  the entry was not selected, five with the entry in the brief. The same sentence is in both briefs
  for 22 asks; among one to five sentences it yields 18 of them, among 25 it yields 12, where no
  brief yields 10.5.
- **What the notes say at the five.** `gcongr` "does not apply, because `posLog` is only
  `MonotoneOn` and has no `gcongr` tag. No request", where the maintainer asked whether `gcongr`
  can do it and the exact-briefed session filed it. A merge of two steps "compiled … but every
  variant either runs past 100 columns or reads no better". Two section-layout asks and the "spell
  out `mgf`" ask were reached only as `partial`: a different change at the same place. The shared
  `variable` binder is never mentioned; its entry was 18th of 25.
- **More findings, worse aim.** A filed 82 findings on the ten PRs, against E's 59 and X's 52.5 a
  session. Asks reached per finding fell to 0.18 / 0.17, from X's 0.27 / 0.25 (E: 0.42 / 0.41), so
  the pre-registered side condition fails. On 41930, where X and E file nothing, A files four.
- **Near misses, as for X.** `partial` cells on in-census asks: A 8 / 10, X 6 to 7 a session, E 1 / 2.
- **A is not X with noise.** It reaches two asks no X session does (32875's `simpa`, 42184's
  `HasProd` sibling) and misses two that one of the two X sessions reached.
- **A shorter brief from the selector's own order would not help.** Its first 5 entries hold the
  entry of 6 asks, its first 10 of 15, all 25 of 22. The entries behind asks sit at ranks 7 to 22.

**What it means, at this altitude.**
- The exact brief delivered two things: each convention's text, and the fact that it is in play on
  this PR (a list of one to five is itself a claim that these are departed from). Stage F delivers
  the first without the second, and the gain goes with it. So most of what the ceiling measured is
  the value of knowing *which* convention the code departs from, not of having the convention
  written down.
- A reviewer handed 25 true and relevant conventions treats them as a checklist: it weighs each,
  passes the code on most, and files more elsewhere. That is the judgement unbriefed Claude already
  makes, and the selector was built not to make it for the reviewer.
- This is the todo's reading of "only exact moving": the work is in pinpointing which conventions
  apply at the reviewing point.

**Untried, and not concluded against.**
- A pinpointing pass: a stage with the reviewer's tools that outputs candidate departures, each a
  convention at a named place with its check run, which the reviewer vets. The plan's convention
  detectors (`docs/plans/2026-10-03-after-structure.md` §2), with a model doing the detecting.
- The selector's `where` delivered with each sentence (it was recorded and withheld).
- A better ranking with a far shorter brief; a past ask as an exemplar of each entry; the reviewer
  selecting for itself from all 438; a second session a PR.
- The "all" level (438 sentences) was not run: on this evidence it dilutes further.

**How it ran.**
- Selectors: token B, 43 points for ten (four each, not the three estimated), which ended B's
  window; six were cut after writing `selected.json`, and each file was checked as written.
- Sessions: six on token C (62 points), four on token B after its reset (38): 100 points, as E's 97.
  Every assistant entry reads `claude-opus-5-5`, xhigh, CLI 2.1.285.
- Matchers: headless on token B, 25 points. Agreement 102 of 108 cells on validation, 44 of 44
  post-cutoff. In all about 1.7 five-hour windows.
- Audits: one flag in ten reviewer transcripts, benign (28649's session wrote a helper in its own
  `tmp/` and ran it with the project's Python by its absolute path; nothing outside the packet was
  read). `run_stage_f.sh` held back that batch's commit and the matching's until the flag was read.

## Stage G: conventions as guarded rules, pinpointed (pre-registered 2026-10-05, before any rule, pinpointing or session)

The user (2026-10-05), looking for a design less ad hoc than a list of sentences: think of a
convention as an inference rule, with preconditions, postconditions, a scope, and what is undefined
or nondeterministic. Asked which test would say whether that framing is worth building, the answer
given was this stage, and the user's reply was *"Okay it's worth testing the probe."* Nothing below
has run.

**What the stage tests.** Stage F delivered each convention as a sentence, 25 a PR, and the
reviewer weighed each one and passed the code. The exact brief carried two things beside the text:
that the convention is in play on this PR, and, by being one of five, roughly where. A guarded rule
states both openly: a trigger that says where the convention is in play, and a check that says how
to tell a departure. If reach under that delivery comes near the exact brief's, the trigger and the
place carry the gain, and both are computed from the diff, not from the asks.

**The rule set, and its leak, stated first** (`stage_g_entries.json`, `build_stage_g_entries.py`):
52 census entries.
- **The pool: the 26 entries behind the 33 in-census asks on the ten stage C PRs.** The set is
  chosen knowing the asks, pooled over the PRs. So the stage skips retrieval over the 438: the right
  rule is always among the 52. On any one PR, two to five of the 52 are behind its asks; which of
  them fire there, and where, is decided blind.
- **26 decoys, none behind an ask on any of the 14 PRs:** the entries stage F's blind selectors
  picked on the most of the ten PRs (three on 5 PRs, four on 4, eight on 3, eleven on 2). Their
  situations occur in these PRs and the maintainers asked nothing under them, so a false fire has
  somewhere to come from.

The stage is therefore a best case for the guarded-rule delivery, given a rule set that holds the
right rule. It is not a floor, and stage F's remains the only ask-free number.

**The rules** (`rule_writer_rubric.md`, `build_rule_writer_folders.py`, `rules.json`). Two blind
writers, 26 entries each, shuffled and unmarked. A writer's folder holds each entry's sentence and
up to four of the census asks reader A filed under it, comment and code, all on census PRs
(disjoint from the probe's). Per entry it writes `applies_to`, `trigger` (a yes-or-no test on
changed code that does not judge its quality), `required`, `check_kind` (`read`, `compile`,
`lookup` or `judge`), `check` and `not_when`.

**The pinpointing pass** (`pinpoint_rubric.md`, `build_pinpoint_folders.py`, `pinpoints/`). One
blind subagent a PR. Its folder holds the reviewer packet's own `pr.md`, `model.md` and
`diff.patch` and the 52 rules in one seeded order. No tools, no asks. It goes through every rule.
For a `read` rule it lists a place only where the code departs. For the other kinds it lists every
place the trigger holds, at most three a rule, without judging the code: that takes the check, and
the check takes tools. Each item is a file, a declaration, a fact about this code and a status.

**The brief** is brief X plus a section (`probes.CANDIDATES_LEAD` and `candidate_line`, tested). An
item reads: the place, the fact, the convention's census sentence, then either "Decided by
reading: the code departs" or the rule's check, then the rule's exception if it has one. The lead
tells the reviewer to verify every item, run the check an item names, file where the code departs,
drop the rest without comment, and review the rest of the PR as the brief says.

**The reviewer** is session G1: the ten stage C PRs, one session each, in stage C's order, on
stage C's route, model, effort and CLI.

**Matching.** One seal a set holding X1, X2, E1 and G1, two blind matchers a set. A1 is left out to
save matcher cost; X and E are re-judged beside G and tie this table to stage F's.

**Read before any reviewer session** (`build_candidate_briefs.py`): for each of the 33 asks,
whether a candidate carries an entry behind it and whether it sits at the ask's place; and the
candidates a PR, from the pool and from the decoys. If an entry is delivered for fewer than 11 of
the 33, the sessions are not spent and that is the result.

**Reading rule, fixed now.** Stage C's measure: per-session reach on the 39 in-census asks, pooled,
each of two matchers, with 26755, 36822 and 43192 imputed as before.

| G − X, on both matchers | reading |
|---|---|
| within 0.05 of E − X | **guarded rules, pinpointed, recover the ceiling**: the trigger and the place carry what the asks' own pinpointing carried |
| `≥ +0.15`, more than 0.05 under E − X | **the delivery carries most of the direction**; the decomposition says where the rest went |
| between +0.05 and +0.15 | partial |
| `≤ +0.05` | **this delivery does not carry it either** |

Asks reached per finding must be no lower than X's.

**Also read, fixed now** (`decompose_stage_g.py`).
- **Application at the place.** Asks with a candidate at their place, with the entry delivered
  elsewhere, and with no candidate: how many G, E and X reach. Stage F's sentence among 25 gave 12
  of 22 and the exact brief 18 of 22; the rate at the place is this framing's own number.
- **By kind of check:** reach on asks whose rule is `read`, `compile`, `lookup` or `judge`.
- **The decoys:** candidates delivered from them a PR, and findings a PR against X's and E's.
- Out-of-census asks, which should not move.

**Limits, stated before.** The pooled rule set, above. One writer a rule, one pinpointer and one
session a PR. The pinpointer has no tools, so no check arrives already run. The rules are written
by Claude from a census Claude wrote.

**Untried after this, whatever it reads:** rules for all 438 with retrieval in front; the checks
run before delivery; decoys at the census's real ratio; a second session a PR.

**Cost and tokens.** Token B is disabled: read at 06:12, its login answers "your organization has
disabled Claude subscription access". Everything runs on token C, at 41% of its five-hour window
(resets 09:50) and 39% of its week when read. Expected, from stage F's meters: two writers about 8
points of a window, ten pinpointers about 40, ten sessions about 100, four matcher runs about 25,
so about 1.7 windows. Writers and pinpointers go in the current window; `run_stage_g.sh` runs the
sessions and the matching, meters each batch, and sleeps to the reset when a batch does not fit.
Sessions run in stage C's order, so a spent window or week leaves the most informative prefix, and
a stage cut short is reported as partial on the PRs it ran.

**Running notes (2026-10-05, written after the rules and nine pinpointings, before any reviewer session).**
- **The rules:** 52, both writers audited clean, committed as written (`rules.json`, `60209444`).
  Check kinds: of the 26 pool rules, compile 11, lookup 8, read 6, judge 1; of the 26 decoys,
  read 14, lookup 6, judge 4, compile 2.
- **The window cost about three times stage F's rate.** The writers ran at 17k weighted units a
  point of the five-hour window, the first four pinpointers at 12k, against stage F's 23-31k. Part
  of it is another session on token C (its window rose from 41% to 53% in six minutes before
  this stage spent anything); the rest is unexplained. The second batch of four ran into the
  limit: pr28649 and pr42184 finished; pr34091 wrote `candidates.json` at 10:10:55 and was cut off
  before its own check, and the file passes every check the rubric names, so it stands, as the
  census's b05 did; pr43167 wrote nothing and is rerun from a rebuilt folder after the 14:50 reset.
- **A weekly guard, added now.** At that rate the ten sessions could take most of the remaining
  week (52% at 10:15, resetting Friday 04:00), which the user's other sessions share. So
  `run_stage_g.sh` now runs one session at a time, meters each against the dearest cost seen so
  far, and starts none once the week reaches 72%. Matching runs on the PRs that finished while the
  week is under 85%. A stage cut short reads as partial on the PRs it ran, in stage C's order, as
  fixed above; both caps are environment variables.
- **Brief length, read before any session:** 13 to 74 candidates a PR on the nine done (328 in
  all, 183 from pool rules, 145 from decoys; 67 decided by reading, 261 checks). Stage F's 25
  sentences diluted; this brief is longer, but each item carries a place and a check.

## Result 5 (2026-10-06): guarded rules, pinpointed, move nothing -- the reviewer gets the right convention at the right place and decides it is not worth asking

Stage G as pre-registered above. 52 rules, ten blind pinpointings, ten briefed sessions (G1), and
one seal a set holding X1, X2, E1 and G1. `read_stage.py G G X --impute 26755 36822 43192` and
`decompose_stage_g.py` print the tables.

| per-session reach (issue recall), matcher 1 / 2 | X, unbriefed | G, pinpointed rules | E, exact |
|---|---|---|---|
| **in-census asks, pooled (39), the rule's measure** | 0.46 / 0.46 | **0.46 / 0.46** | 0.74 / 0.74 |
| difference from X | | **+0.000 / +0.000** | +0.282 / +0.282 |
| validation, in-census (25) | 0.48 | 0.48 | 0.76 |
| post-cutoff, in-census (14) | 0.43 | 0.43 | 0.71 |
| out-of-census (5) | 0.40 / 0.60 | 0.40 / 0.60 | 0.40 / 0.60 |

**By the rule (`≤ +0.05` on both matchers): this delivery does not carry the ceiling either.** G
differs from X on two asks, one each way. The ceiling replicates a third time under new matchers
(E − X = +0.282 on both). Asks reached per finding on the ten run PRs: G 0.23 / 0.25 against X 0.27 /
0.29 and E 0.42 / 0.44, so the side condition fails as stage F's did; G filed 61 findings, X 52.5 a
session, E 59. Matchers agree on 102 of 108 cells on validation and 44 of 44 post-cutoff.
Provisional: one session a PR, one writer a rule, one pinpointer a PR, and a pooled rule set.

**Retrieval was not the gap.** A candidate carried an entry behind the ask for 28 of the 33
in-census asks, at the ask's place for 21 by the mechanical test (stage F's sentences: 22 of 33,
no place). The briefs ran from 13 to 74 items a PR, 385 in all (217 from pool rules, 168 from
decoys; 78 decided by reading, 307 checks).

**Application was** (matcher 1; matcher 2 the same within one ask):

| | asks | X, a session | G | E |
|---|---|---|---|---|
| a candidate at the ask's place | 21 | 9.0 | 9 | 17 |
| the entry delivered elsewhere | 7 | 3.0 | 3 | 5 |
| no candidate | 5 | 0.0 | 0 | 1 |

Of the 10 asks only the exact brief reached, G reaches none, and 8 had a candidate at the place.

**What the notes say there.** The session verified the candidate and overrode it:
- `gcongr` on 30641's monotone step: run, "did not make progress, because `posLog` has no gcongr
  lemma. I dropped that item." The maintainer's ask was a question, "Can `gcongr` do this (or do you
  need to provide the side condition manually)?"
- `{D : ℤ}` repeated in four consecutive signatures on 42814, delivered as *departs*: "Missing
  docstrings, line-wrapping and `variable {D}` items: Mathlib does not require these, so I would
  not request them."
- The primed private helper on 43167, delivered as *departs*: "The prime on a private helper is
  acceptable, so I raised no naming ask."
- The `HasProd` sibling on 42184: "would be natural follow-ups ... I would not" ask.
- 28649's `MGFs`: the convention judged departed, and a different change filed (revert to
  lowercase rather than spell it out): `partial`, as X.
- 30458's `variable` sections: filed, as a different restructure: `partial`, as X.

**What it means, at this altitude.** Stage F delivered the text without the place; stage G
delivered the text, the place and the check; both read as X. What the exact brief carried and
neither did is the assertion: a list of one to five conventions is a claim that maintainers ask
for each of them here. Given a long list to verify, half of it decoys, with an instruction to drop
what does not depart, the reviewer applies its own bar for what a maintainer would ask, and that
bar is X's. This is the filing bar the post-carry-over plan names ("verified, withheld"), met on
Claude.

**Untried, and not concluded against.**
- **The lead, isolated:** the exact entries delivered as pinpointed candidates under stage G's
  verify-and-drop lead. At X, the lead is what removes the gain; near E, the decoys and length do.
- **An asserting lead:** the same candidates, told that maintainers raise these and to file each,
  as a question where a check fails ("can `gcongr` do this?"), unless the check refutes it.
- Rules for all 438 with retrieval in front; checks run before delivery; a second session a PR.

**How it ran.** Rules (two writers) and pinpointing (ten) on token C on 2026-10-05; two pinpointers
were cut by the five-hour limit (pr34091's file, written before the cut, stands; pr43167 reran).
Sessions one at a time from 15:01 to 01:12, three windows, each 6 to 16 points of the five-hour
window at 27k to 36k weighted units a point, as stage F; the week went from 53% to 61% for the
sessions and to 63% with the matchers. Two session audits flagged the project's Python run by
absolute path, on helper scripts in the packet's own `tmp/` and on `findings.json`; read, benign,
committed by hand (`146bf67e`).

## Stage H: which pinpointed departures would a maintainer raise? Five decisions over one record (pre-registered 2026-10-06, before any mining or decision)

The design space and why: `docs/plans/2026-10-06-convention-decision-designs.md`. The user
(2026-10-06): test several modifications at once on a few rules and PRs, with negatives, recorded
examples, and an agent nudged to retrieve examples, "so we minimize model-specific judgement and
thresholds." Nothing below has run.

**What it tests.** Stage G's reviewer had the right convention at the right place and declined it,
and maintainers asked at 9 of the 78 places the pinpointer judged departing. The missing piece is
the selection. Stage H asks which decision procedure picks the places maintainers raise, before
any reviewer session is spent on it.

**The rules** (`stage_h_rules.json`): ten, chosen knowing the probe asks, as stage G's set was:
P005, P010, P011, P018, P048, P100, P254 (each with a candidate at an ask on some probe PR and
candidates without), P040 (candidates, no ask), P084 and P126 (the decoys with the most candidates).

**The candidates** (`stage_h.py`, `probe_candidates`): stage G's pinpointed places for these rules
on the ten PRs, 149, of which 12 sit at an in-census ask filed under the same rule (8 distinct
asks, checked; the mechanical place test of stage G). That truth is never shown to a decider.

**The record, from census PRs only.**
- Positives: reader A's census asks under each rule (comment and code).
- Negatives: the same blind pinpointer, rubric and 52 rules as stage G, run on 16 val1000 PRs
  (`census_sample.json`, `build_census_sample.py`: seeded, at most 40 change targets, 3 AI-authored),
  keeping places for the ten rules; a place at a round-1 ask under its rule is a positive, the rest
  negatives.
- The rate index: census asks under the rule over the 973 val1000 PRs, divided by the places flagged
  per sample PR (plus a half) times 973.

**The designs**, each deciding raise or not for all 149 candidates:
- `judge`: the rule and the candidate's code alone (the control);
- `examples`: four asked and four not-asked examples a rule, seeded;
- `examples_rate`: as `examples`, with the rule's rate stated as the prior;
- `retrieve`: one file a rule with every asked (up to 30) and not-asked example; the decider must
  find the most similar for each candidate and cite them;
- `rate`: no model; per PR, the three candidates whose rule has the highest index.

Deciders are blind subagents, Opus 5.5 at xhigh on the headless route, two a design (PRs split in
halves), decider rubric fixed in `stage_h.py`. Order: `examples`, `judge`, `retrieve`,
`examples_rate`, so a budget-forced stop keeps the main contrast.

**Reading rule, fixed now.** Per design, on the 149 candidates: candidates raised, raised at an ask
(of 12), precision and recall. Base precision (raise all) is 12/149 = 0.08; the oracle is 1 and 1.

| design, on its decisions | reading |
|---|---|
| recall ≥ 8/12 and precision ≥ 0.35 | **strong**: carry to reviewer sessions first |
| recall ≥ 6/12 and precision ≥ 0.25 | **carry to reviewer sessions** |
| otherwise | below the bar |

**A baseline seen before this rule was fixed, stated as such.** A dry run of the scorer with all
indices equal made design `rate` fall back to the pass's own order (departs first): three a PR, 30
raised, 7 at an ask, precision 0.233, recall 0.583. The scorer reports it as `order`. A model design
that does not beat it adds nothing over the pinpointer's own ranking, whatever its reading above.

One candidate is 0.083 of recall, so two designs differing by fewer than two at-ask candidates are
not distinguished. The contrasts are read as the plan states them. Exploratory: one decider run a
design and half, ten rules chosen knowing the asks.

**Also read:** the rate per rule (flagged per PR, asked); asks the pinpointer never flagged on the
census sample (its recall there); per-PR raises; the `p` ranking of each model design.

**Limits, stated before.** The rule set is chosen knowing the asks. Negatives are round-1 silences,
so a later-round ask counts as not asked. The mechanical place test matches by declaration name and
file. Sixteen census PRs give few negatives for rare rules.

**Cost and tokens.** All on token C (B's login is disabled); at 04:18 the week stood at 64% and the
five-hour window at 51% with another session drawing on it. Expected: 16 pinpointers at 4 to 16
points of a window each, eight deciders at 5 to 15: about two windows, and about 8 to 12 points of
the week. `run_stage_h.sh` meters every batch and stops starting work once the week reaches 80%.

**Running note (2026-10-06 04:30, before any batch ran).** At the user's direction the stage runs on
the main account (`CLAUDE_CODE_OAUTH_TOKEN`; five-hour window 6%, week 55% when read, resetting
Friday 10:00), not token C. Same model, route and caps; the runner reads the login from `TOKEN_VAR`.

## What follows

The ladder's question is answered for the one ask-free delivery tried: conventions as sentences
picked from the diff do not move the reviewer, and the ceiling's gain was in the pinpointing. The
design the two results point to is a pinpointing pass (above), which is code and a prompt, not a
brief. Stage G, above, was its first test (2026-10-05): the place and the check arrived and the
reviewer overrode them. What remains untested is the decision to file, listed under Result 5.

## What closes it

The table above, per matcher and per set, here and in the todo. The Claude exact step then runs or
does not on the todo's own terms; the only way this stage stops it is by showing that most asks are
out of census, or that the machinery is wrong.
