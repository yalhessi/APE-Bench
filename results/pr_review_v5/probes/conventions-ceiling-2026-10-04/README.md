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

## Result 6 (2026-10-06): no decision design picks the places maintainers raise -- every rule is raised at 5% or less of its flagged places, and a model's guess is barely above chance

Stage H as pre-registered above, on the main account, 04:30 to 05:30: 16 census pinpointers and eight
deciders, every transcript audited clean; the week went from 55% to 59%. `stage_h.py score` prints
the table.

**The record.** On the 16 census PRs the same pinpointer flagged 205 places for the ten rules (12.8
a PR), 6 of them at a round-1 ask (2.9%). The rate index (census asks per flagged place) runs from
P005's 0.048 to P254's 0.0026: maintainers raise between one in 20 and one in 400 of the places a
rule's situation is flagged. An 18x spread, all at or under 5%.

**By the rule: every design is below the bar.**

| design | raised | at an ask (of 12) | asks (of 8) | precision | recall |
|---|---|---|---|---|---|
| all (stage G) | 149 | 12 | 8 | 0.081 | 1.000 |
| order (the pass's own, three a PR; seen before the rule) | 30 | 7 | 5 | 0.233 | 0.583 |
| `judge` | 2 | 0 | 0 | 0 | 0 |
| `examples` | 2 | 0 | 0 | 0 | 0 |
| `examples_rate` | 2 | 0 | 0 | 0 | 0 |
| `retrieve` | 5 | 0 | 0 | 0 | 0 |
| `rate` | 30 | 2 | 2 | 0.067 | 0.167 |

**Also read, as pre-registered: the probability ranking**, which does not depend on the deciders'
threshold.

| design | AUC of p | three a PR by p: at an ask (asks) | mean p, asked / not |
|---|---|---|---|
| order | 0.558 | 7 (5) | |
| `examples` | 0.641 | 7 (6) | 0.091 / 0.083 |
| `retrieve` | 0.591 | 7 (6) | 0.105 / 0.101 |
| `examples_rate` | 0.585 | 6 (5) | 0.049 / 0.044 |
| `judge` | 0.563 | 5 (4) | 0.100 / 0.108 |
| `rate` | 0.602 | 2 (2) | |

- **The deciders learned the base rate, not the selection.** Told that most flagged places are never
  raised, they put p near 0.05-0.10 everywhere, which is about the true 0.08, and separated asked
  from not asked hardly at all. Ranked three a PR, `examples` and `retrieve` tie the pass's own order
  on candidates (7 of 12) and cover one ask more (6 of 8): within the two-candidate noise.
- **The rate ranks the wrong rules first here.** P005, P011 and P018 have the highest index; on these
  PRs maintainers asked as much under P048, P254 and P100.
- **Their reasons at the 12 are the reviewer's.** "In a golf PR reviewers usually accept the golf as
  is" (32875, where the maintainer asked for a further `simpa`); "a plausible nit, not commonly
  enforced" (42814's `{D : ℤ}`); "the standard pattern" (43167's `_left`/`_right`). `retrieve` cited
  closer not-asked examples for most of them.
- **Raises at an ask under another rule:** one, `retrieve`'s P048 on 30458 at the `variable` asks
  filed under P369. The "restore the old proof" raises on 30458 are not at its old-proof asks.

**What it means, at this altitude.** Given the convention, the code at the place, and asked and
not-asked examples, a model's guess at which places maintainers raise is barely above chance
(AUC 0.56-0.64). That is where the record's artifact-only selectors stood (AUC 0.62,
`docs/dead-ends.md`, "Selection from artifact-only signals"), now replicated with the convention
and its demand side in hand. Exploratory: one decider run a design, 12 positives, rules chosen
knowing the asks.

**What it does not show, and the untried designs.**
- **Whether the unasked departures are unwelcome.** The truth is round-1 asks, a lower bound. If a
  maintainer would accept most of the 78 departures the pass decided by reading, the gap is in the
  evaluation, not in the selection. Untried: adjudicate a sample of them ("would a maintainer accept
  this if proposed?"), the socket `docs/todo/adjudication-rubric.md` describes.
- **Signals outside the convention and the hunk:** the reviewer (one maintainer wrote 30 of dev's
  52 round-1 comments); the PR's own theme (on a golf PR the maintainer asked for more golf, and the
  deciders inferred the opposite); file-local regularity (42184's ask: "as this seems to be the
  convention in this file").
- More rules, more census PRs and a second decider run; scope by area and era.

## Stage D: DeepSeek-V4.1-Flash -- stage L replicated, and the conventions given precedence over the reviewer's judgement (pre-registered 2026-10-08, before any session)

The user (2026-10-08): DeepSeek is *"a good opportunity to replicate those results and try one
alternate design of how conventions get used: models still don't seem to understand how we want them
to use conventions, and that the examples of conventions should count as stronger evidence than their
internal judgement."* The self-hosted DeepSeek-V4.1-Flash reaches 8, 6, 9 of 23 on the dev held-out 12
with its thinking kept (Opus 5.5: 7, 7), free on `first` (`../local-ds41-2026-10-06/`). Nothing below
has run.

**Two questions, one gate.**
1. **Replication: does a strong local model carry the ceiling?** DE against DX, as stage L read LE
   against LB. The record: Qwen3.5-397B +0.05 (stage L), gpt-5.5 +0.22 (stage M), Claude +0.26 / +0.28
   (stage C).
2. **The alternate design: do the conventions, with maintainers' asks for them, move the reviewer
   further when they are stated to outrank its own judgement of the code?** DP against DE.

**Sets: stage L's two, unchanged.** Validation small12 (30 asks on 8 PRs, 3 controls) and post-cutoff
(16 asks on 6 PRs, 4 controls); 39 in-census asks (25 and 14), stage L's labels and exact briefs.
DeepSeek-V4.1 was released 2026-09-10 and its training cutoff is not public, so the validation PRs,
and perhaps the post-cutoff ones, may be in its training data. Only differences between conditions
are read; all three share the same memory.

**Conditions.** Model `local_deepseek_v4.1_flash`, `reasoning_effort: high`, each turn's thinking kept
(the dev keepthink condition), contract v2 under `ape_agent`. The configs
`configs/pr_review_v5_{val_small12,probe_2026_07_08_v1}_local_ds41_contract2.yaml` are each set's
gpt_5.2 contract-v2 config (stage L's base) with the model lines of
`configs/pr_review_v5_dev_medium_local_ds41_contract2.yaml`. The server is `serve_ds41.sbatch` with its
defaults (the patched nightly, DSpark, a 1M context). A condition differs from another only in its
context file.

| label | the reviewer reads | PRs | reps | run name |
|---|---|---|---|---|
| DX | the PR model (`context_<set>_base.jsonl`, stage L's file) | all 11 and 10 | 3 | `iter_ds41_conv_<val\|post>_base_rep<n>` |
| DE | the PR model, then the exact section (`context_<set>_exact.jsonl`, stage L's) | the 8 and 6 with asks | 3 | `iter_ds41_conv_<val\|post>_exact_rep<n>` |
| DP | the PR model, then the exact section with examples and the precedence paragraph (`context_<set>_prec.jsonl`) | the 8 and 6 with asks | 3 | `iter_ds41_conv_<val\|post>_prec_rep<n>` |

`build_context.py base` and `exact` rebuild stage L's two files byte for byte (checked 2026-10-08).
`cli plan` passes for all 18 runs (`run_ds41.sh <set> <level> <rep> plan`, the gate's own arguments;
2026-10-08: reviewed workspaces 11 of 11, 10 of 10, 8 of 8 and 6 of 6, token budget 16.08M a PR).

### The alternate design: P, the conventions and their examples over the reviewer's judgement

**The text.** DP's section is DE's lead and sentences byte for byte, with up to two examples beneath
each sentence and this paragraph after the list (`probes.CONVENTIONS_PRECEDENCE`):

> Under each convention are up to two comments in which a maintainer asked for it on another PR, each
> with the code it was on. Take the conventions and these examples as the standard for this review:
> they show what maintainers ask for, and they outrank your own judgement of this code. Where the
> changed code is in a situation like an example's, file the change its convention calls for, as a
> finding at that place. None of these is a reason to leave it out: that the code is correct, clear or
> idiomatic as it stands; that the change is minor or a matter of taste; that this file, its author or
> its neighbours do it differently; that Mathlib does not require it or a maintainer might not insist
> on it; that the convention's wording does not quite fit, where the code is like an example's. Where
> you cannot make or check the change, file it as a question to the author that names the convention
> and the change. Leave a place unfiled only where a line of the code you quote, or a check you ran,
> shows it already has the form the convention calls for. In your submission's `message`, list each
> convention with the places you filed and any place you left, with that line or check. For these
> conventions this replaces the brief's instructions to emit only what you would actually request and
> not to raise questions.

An example reads "Example n, asked on another PR at `<file>`. The maintainer's comment:" with the
comment quoted, then "The code it was on:" and the hunk (`probes.exemplified`).

**The examples, chosen mechanically and not read against the probe asks.** For each of the 28 entries
in the exact briefs: reader A's census asks filed under it (primary label) on val1000 and
outside_years PRs, in stage G's seeded order (`stage-g-2026-10-05`), first two. These are the first
two of the four each stage G rule writer saw for the entry, cut as stage G cut them (comment to 900
characters, the hunk's last 800). 25 entries have two, P315 and P401 one, P392 none (it reads as its
sentence). None is on a probe PR (asserted). The rule was fixed before any example was read; one
PR's section (32875) was then printed to check the rendering, and nothing was changed after.
`examples_prec.json` records them by id. Census bodies are
never committed, so the two `context_*_prec.jsonl` files are not: `build_context.py prec <bodies>`
rebuilds them from `materialise_bodies.py`'s output, byte for byte (twice, 2026-10-08), and
`context_prec.sha256` holds their digests, which `run_ds41.sh` and the gate refuse to run without.
The section is 2.8k to 12.6k characters a PR against DE's 0.5k to 1.2k, so length is part of the
design.

**How it differs from DE:** the examples and the closing paragraph. Nothing else in the run differs.

**How it differs from the disposition paragraph** (`probes.CONVENTIONS_DISPOSITION`, branch
`generation-suppression`, cherry-picked here as `a1ff423f`; stage W moved gpt-5.5 by +0.189 with it):

| | disposition paragraph (stage W) | precedence (DP) |
|---|---|---|
| examples | none | up to two maintainers' asks a convention |
| grounds it rules out | what Mathlib usually requires, accepts or enforces; minorness; whether a maintainer would insist | those, and the reviewer's view of the code: correct, clear or idiomatic as it stands; a matter of taste; the file's, author's or neighbours' practice; the wording not quite fitting |
| where a convention applies | "each place in the changed code where its situation occurs": the reviewer's call | "a situation like an example's": the examples decide |
| precedence | implied (`conforms` needs a check or a quoted line) | stated: "they outrank your own judgement of this code" |
| a change it cannot make or check | not covered (`departs` or `conforms` only) | a question to the author naming the convention and the change |
| leaving a place | `conforms`: a check or a quoted line shows the required form | the same |
| the filing bar | stage W also moved gpt-5.5 to `filing_bar: request` | contract v2 has no merge-bar clauses; nothing changed |

**Why this design and not the disposition paragraph as it stands.**
- **The user's direction names the examples,** and asks that they count for more than the model's own
  judgement. The disposition paragraph has no examples and leaves the merits of the code to the
  reviewer.
- **What the exact brief leaves missed is mostly the reviewer's judgement of the code, not its guess
  about maintainers.**
  - Claude E1's ten misses (Result 3): six conventions weighed and the condition judged unmet ("a
    matter of taste, not an ask"; "inherently specific"; three motivation asks set aside as "a
    generalization rather than a new concept" or "too minor"); two right conventions at a
    neighbouring place; one comparison too general to pick; one never attended.
  - Qwen LE (Result 2): "`gcongr` doesn't apply here as verified"; a convention quoted as one the PR
    already follows.
  - Stage G (Result 5): "Mathlib does not require these", and "the prime on a private helper is
    acceptable".
  - The disposition paragraph's grounds reach "too minor" and "Mathlib does not require". The rest are
    judgements of the code or of the convention's fit, which DP reaches and it does not.
- **Examples are the record's untried delivery,** listed after stage L ("exemplars"), stage F ("a past
  ask as an exemplar of each entry") and in the todo's low-ceiling list. For the neighbouring-place
  misses and the comparison too general to pick (43167's `left`/`right`), an example of the change
  asked for is what was missing.
- **What the choice costs.** DP bundles the examples, the precedence and a longer section, so a gain
  does not say which carried it. The ablations are the disposition paragraph on DeepSeek and DP
  without its examples, run only if DP moves. A null does not separate them either: it says this
  bundle did not move this model.

### Reading rule, fixed before any session runs

**The measure** is stage L's: per-session reach on the 39 in-census asks (`reached` cells; `partial`
is not reached), on each of two blind matchers, pooled over the two sets and reported per set. Three
reps make 117 cells a condition. `read_stage.py D <treated> <control>` prints it.

**1. DE − DX, the replication** (the todo's thresholds, as stage L):

| DE − DX, both matchers, pooled | reading |
|---|---|
| **≥ +0.15** | **DeepSeek carries the ceiling**, as Claude and gpt-5.5 did: the exact conventions move a strong local model. |
| **≤ +0.05** | **it does not**, as Qwen did not: a stated convention does not become the ask on this model. |
| between | inconclusive at this size: read the transcripts before saying more. |

Side condition (the todo's): asks reached per finding under DE no lower than under DX.

**2. DP − DE, the alternate design:**

| DP − DE, both matchers, pooled | reading |
|---|---|
| **≥ +0.10** (12 cells of 117, about four asks a rep) | **the conventions given precedence, with examples, move the reviewer beyond the exact brief.** |
| **≤ +0.03** (3 cells or fewer) | **they do not.** |
| between, or the matchers disagree | inconclusive: read the reasoning at the asks that differ. |

**Volume guard** (stage W's): DP's findings a PR on the 14 ask PRs, mean over reps, more than 3.0
above DE's makes it a volume effect, whatever the reach. DP − DX is reported beside it.

One ask moving in every rep is 3 cells, 0.026.

**Also read, not in the rule:**
- mean, union and stable reach per condition (asks reached in any rep, in all three), per set;
- the out-of-census asks (7), the within-session control, minding stage L's lesson that one sharing a
  hunk with an in-census ask is not a control;
- findings a PR and asks reached a finding per condition; DX's findings on the 7 control PRs;
- `partial` cells per condition;
- at every in-census ask whose reach differs by two reps or more between DP and DE, and at DP's
  misses: what the kept reasoning (`reasoning_content`) says at the ask's place, sorted as
  `cross_model.md` sorted GE1's misses: weighed and dropped (on what ground), filed as another change,
  or never considered;
- whether DP's `message` lists the places it left with a quoted line or a check, as the paragraph asks;
- DP findings that are questions, and how many matched asks are among them;
- DP findings whose place is not in this PR's diff (an example's code restated);
- sessions that ended without a submission.

### Matching (after the gate)

One seal a set on the PRs with asks, holding Claude's X1 and X2 (the anchors, as in stage L), DX1-3,
DE1-3 and DP1-3: 11 sessions a PR (`sources_D_<set>.json`, written now). Then as stage L: `cli probe
seal`, `cli probe match-inputs` with the sources, two blind matchers a set as subagents under the
harness's rubric (labels shuffled per PR, condition cues redacted), `cli probe audit`, `cli probe
unblind` into `match_D_<set>/unblinded.json`, `read_stage.py D DE DX` and `read_stage.py D DP DE`.

### The gate, and what it costs

`run_stage_d_gate.sh`, one Slurm job on `first` (120 GB, no GPU; the cluster refuses a CPU count):
- starts the server with `sbatch serve_ds41.sbatch` and waits for it, stopping on a traceback;
- runs `probe_correct.py` and `probe_carry.py`, and stops and releases the node if either fails;
- runs the 18 runs rep-major (rep 1 of every condition and set first, so a gate cut short leaves
  whole reps), three at a time (at most 29 sessions: one 15-session rep peaked at 34% of the KV cache);
- starts no run with under 60 minutes left on the server's 8 hours; when the runs in flight finish
  it releases the server and starts another, at most three in all; an interrupted run resumes and a
  complete one is skipped;
- stops on a run that keeps retrying, and releases the node at the end.

Progress: `/research/projects/proofedit/ya475/localmodel/logs/ds41_conv_gate.status`; each run's log
is `cli_iter_ds41_conv_<set>_<level>_rep<n>.log` beside it.

**Cost.** GPU time on `first` only: 147 sessions. A 15-session dev rep took 34.5 minutes with DSpark,
so about 3 to 5 hours of server time. Matching is four subagent matcher runs; stage L's took 87k to
185k tokens each at 8 sessions a PR, so about 150k to 250k each at 11. No reader runs and no paid API
call. On 2026-10-08 gg676's jobs held 3 to 5 of `first`'s 8 GPUs with 8 to 12 hours to run, so the
server waits for the node.

**Limits, stated before.** One model, three reps, 39 asks. The exact brief is a ceiling by
construction (built from the asks), and DP carries the same leak plus census examples from PRs
disjoint from the probe sets. The comparisons are within one seal; against Claude's published X
figures they are not.

**Running note (2026-10-08 03:15, after the pre-registration was committed, before any session).**
- **Submitted:** gate job 434256 (running, waiting for its server) and the server it submitted, job
  434257, pending on Resources. gg676's `mp_meas` (434156) holds one of `first`'s GPUs under a 12-hour
  limit from about 02:17, so the server can start by 14:17 at the latest. Another session's 7-GPU
  pipeline-parallel test of the same server (434255, "TP1 x PP7") ran from 03:12 and was cancelled at
  03:15:08, before this gate was submitted.
- **Do not edit `run_stage_d_gate.sh` until the status file reads "finished".** Bash reads it as it
  runs; a comment edit made after submission was reverted to the submitted bytes (7f6070f5) at once,
  while the gate slept inside `start_server`. Its usage line still shows `-c 12`, which the cluster
  refuses; it was submitted without `-c`.
- **What is left, in order** (nothing below has run): when the status file reads "stage D gate
  finished", commit each run's `results/pr_review_v5/runs/iter_ds41_conv_*` by path; per set, `cli
  probe seal --set <set yaml> --sessions X1 X2 DX1 DX2 DX3 DE1 DE2 DE3 DP1 DP2 DP3 --out
  blinding_D_<set>_SEALED.json` (the PRs with asks, by default), then `cli probe match-inputs` with
  `sources_D_<set>.json` into a scratch folder outside every packet, as `run_stage_m.sh` lines 80-81;
  two blind matchers a set as subagents; `audit_batch.py` on their transcripts; `cli probe unblind`
  into `match_D_<set>/unblinded.json`; `read_stage.py D DE DX` and `read_stage.py D DP DE`; then the
  also-reads above and Result 7 here and in the todo.

### Interim look at rep 1 (2026-10-08 05:30, at the user's request, before any rep-1 cell was matched)

The user (05:25): *"We should judge the runs that finished, before we waste time replicating the same
negative result."* **This is a deviation from the pre-registration,** which reads three reps under
one seal a set. Rep 1 of every condition finished at 05:21:50 (DX1, DE1, DP1 on both sets: 49
sessions, none failed). Reps 2 and 3 are running under the same gate and are left alone.

**The procedure is the pre-registered one, on rep 1 only.** One seal a set over Claude's X1 and X2
with DX1, DE1 and DP1 (`blinding_D1_<set>_SEALED.json`), two blind matchers a set as subagents under
the harness's rubric, the audit, then `cli probe unblind` into `match_D1_<set>/`. `read_stage.py D1`
reads it.

**What one rep can support, and what it cannot.**
- It can show a direction, and what the sessions did at each ask: their reasoning at the misses.
- It cannot give a reading by the rule:
  - one rep is 39 in-census cells a condition, so one ask is 0.026;
  - the semantic judge's self-agreement puts one obligation at n≈8 near ±12 points (CLAUDE.md);
  - DeepSeek moved 6 to 9 of 23 rep to rep on the dev set.
- So the thresholds above are not applied to rep 1 as a verdict. The rule stays the three-rep one,
  and every rep-1 figure here is provisional.
- **Whether to stop the gate after this look is the user's decision.** This session does not stop,
  edit or restart the gate or its server.

**How the full reading adds reps 2 and 3 without re-matching rep 1.** It needs a second seal a set
over X1, X2, DX2-3, DE2-3 and DP2-3 (`D23`), read together as `read_stage.py D1,D23`.
- Within each seal, every condition is judged by the same two matchers. So each rep's differences
  stay within one seal, though the three reps are no longer under one.
- X1 and X2 sit in both seals as the anchors. Their cells in the two rounds measure how far one
  matcher pair drifts from the other.
- `read_stage.py` merged rounds by replacing a whole ask's row, which suits rounds on disjoint PRs
  (stage C). It now merges rows by session, so two rounds on the same asks add up.
- Re-matching all 11 sessions a PR under one seal, as pre-registered, would instead cost four more
  matcher runs at 11 sessions a PR, on top of the four run now.

### Interim result (rep 1), provisional: not a null -- the exact section moves DeepSeek by +0.23, and precedence with examples by a further +0.15 to +0.18

Rep 1 alone, matched as recorded above. All four matcher transcripts audit clean (41 tool calls, none
flagged), and the prompts were handed over verbatim. The matchers agree on 149 of 150 cells
(validation) and 80 of 80 (post-cutoff). Matcher tokens: 128k, 131k, 87k and 87k, about 0.43M in
all, on the primary subscription. `read_stage.py D1 DE DX` and `read_stage.py D1 DP DE` print the
tables.

| per-session reach, in-census asks, matcher 1 / 2 | DX1 | DE1 | DP1 | Claude X (X1, X2), same seal |
|---|---|---|---|---|
| validation (25) | 0.20 | 0.44 | 0.64 / 0.60 | 0.48 |
| post-cutoff (14) | 0.21 | 0.43 | 0.57 | 0.43 |
| **pooled (39)** | **0.21** (8/39) | **0.44** (17/39) | **0.62 / 0.59** (24 / 23 of 39) | 0.46 |
| out-of-census (7), the control | 4/7 | 5/7 | 6/7 | 7/14 |
| findings a PR, the 14 ask PRs | 2.64 | 3.14 | 3.29 | 4.86 |
| asks reached a finding, all asks | 0.32 | 0.50 | 0.65 / 0.63 | 0.32 |

- **DE1 − DX1 = +0.231 on both matchers** (9 in-census asks gained, none lost). The rule's
  three-rep bar for "DeepSeek carries the ceiling" is +0.15. Gained: 28649 v0030 (spell out `mgf`),
  32875 v0094 and v0095 (`simpa`), 34091 v0106-v0108 (instance-implicit class hypotheses), 43167
  p0012 (`_of_normal` rather than a prime), 43192 p0014 and p0015 (`by cat_disch` defaults).
- **DP1 − DE1 = +0.179 / +0.154**, a net gain of 7 / 6 asks. The rule's three-rep bar is +0.10.
  - Gained (both matchers unless marked): 28649 v0029 ("please revert" a wording change); 30458
    v0060 and v0061 (no sections, collect the common `variable`s); 30458 v0062 and v0063 ("does the
    old proof not work?"); 32875 v0090 (the `grind` tag; matcher 1 only); 41930 p0000 (why the old
    names are bad, a PR-level motivation ask); 42814 p0006 (`mk_iff`); 42814 p0007 (one `variable
    {D : ℤ}`).
  - Lost: 30641 v0066 (prove the `≤` version directly) and 43192 p0014 (`cat_disch` default on `mk`).
  - p0007 is the ask stage G's Claude session verified and dropped ("Mathlib does not require
    these"). p0000 is one of the three PR-level motivation asks Claude E1 set aside as "too minor".
- **The volume guard is far from binding.** DP1 files 0.14 findings a PR more than DE1, against the
  +3.0 guard, and its asks reached a finding rise (0.50 to 0.65 / 0.63).
- **The control moved, and both moves are tied to the brief.** DE1 gained 28649 v0031 ("I'm not
  sure about this one"), which shares the docstring hunk with the in-census v0030, as in stage L.
  DP1 gained 30641 v0065 (`h₂a` → `ha`), which it filed under the brief's variable-naming entry
  (P105). So the out-of-census asks are not a clean control here either.
- **Against Claude.** DE1 reaches about what unbriefed Claude does in the same seal (0.44 against
  0.46), and DP1 more (0.62 / 0.59). Stage C's briefed Claude (0.74) was matched under another seal
  and is not compared here.
- **DP1's messages follow the paragraph's form.** Each lists the conventions with the places filed
  and the places left, with the check or line. Twice the reasoning still weighs maintainer
  insistence: "would a maintainer ask? ... maybe 50% likelihood" (30641, filed), and "not a change I
  would insist on" (43192, an unused `open`, not an ask).

**What DP1's sessions show at the 16 in-census asks it still misses** (15 on matcher 1; read by me
from each session's reasoning and submission `message`, not blind):

| how it was missed | asks | what the session says |
|---|---|---|
| **a check failed, and the place was left rather than filed as a question** (the paragraph asks for a question) | 4: 30641 v0068, 32875 v0092, 32875 v0093, 43192 p0014 | v0068: "the code does NOT use gcongr, but gcongr doesn't work here (verified), so the code is fine". v0092: "`simpa only [pi_pi, this] using …` does not elaborate", and a different change filed there. v0093: tested `exact … h` without the `simp`, "a type mismatch, so the `at h` simplification is not redundant". p0014: "`by cat_disch` cannot discharge them here … so requiring them is correct" (DE1 filed it). |
| **weighed on the merits, and the code judged conforming or necessary** | 5: 30641 v0064, 34091 v0105, 42814 p0005, 43167 p0010, 43192 p0016 | v0105: "the extra case split … is necessary". p0005: "its ℤ-specific content is used … not an instance of the general" lemma. p0010: "`_left`/`_right` is the first/second argument here exactly as in `commutator_le_left`" (local siblings, as Claude E1 did). p0016: `homMk` ~25 files against `mkHom` ~7, "NOT a clear naming violation". v0064: "everything else uses the area's letters" (the maintainer called it optional). |
| **the right convention filed, in another form or place** (`partial`) | 3 on matcher 2 (2 on matcher 1): 29842 v0053 and v0056, 32875 v0090 | A motivation finding at the module docstring ("the PR's description is empty"), where the maintainer asked about #24163 and the downstream plan. The `grind` tag put on `mem_map_equiv` itself. |
| **considered against the wrong comparison** | 1: 42184 p0003 | "`HasProd.nonneg` does not exist, but neither does the additive twin" (the ask is the `HasProd` sibling in this file). |
| **the convention swept, never at the ask's place** | 3: 30641 v0066, 30641 v0067, 42814 p0004 | The direct-lemma check at `this.le`, not at `rw [not_le] at h₂a` (DE1 and DX1 reached v0066). `positivity` used for other arguments, with `simp [Finset.sum_nonneg …]` kept. The alias check on the file's other iffs, not `forall_prime_iff_two_and_odd`. |

**What it means, at this altitude (one rep).**
- The pick-up's fear, that this would replicate the negative, does not hold on rep 1.
  - DeepSeek behaves like the strong reviewers (Claude +0.26 / +0.28, gpt-5.5 +0.22), not like
    Qwen (+0.05).
  - Stating the conventions' precedence, with examples, moved it further, both ways counted.
  - Both differences clear their three-rep bars on one rep, by two to three asks.
- The mechanism reads as intended where it worked: the asks gained include the ones on record as
  verified and dropped.
- Where it did not work, the leading cause is new.
  - A failed check is still read as the code conforming, though the paragraph says to file a
    question where the change cannot be made.
  - The merits judgements the paragraph rules out still decide five asks.
- One rep cannot carry a verdict. Per-ask stability (mean / union / stable) needs reps 2 and 3.

## Result 7 (2026-10-08): three reps -- DeepSeek carries the ceiling (+0.22 / +0.25), and precedence with examples moves it a further +0.20 / +0.18, with no volume effect

**How it was matched.** Reps 2-3 were matched as the interim look's procedure fixed: a second seal a
set, `D23`, over X1, X2, DX2-3, DE2-3 and DP2-3 (`blinding_D23_<set>_SEALED.json`, committed before any
cell was judged, `c39eb332`); `cli probe match-inputs` with `sources_D_<set>.json`; no condition cue
in any reviewer file. Four blind matchers ran, two a set, as subagents of the session that wrote this
(Opus 5.5, CLI 2.1.292), each handed its generated prompt verbatim (checked against the transcripts).
- Matcher tokens: 181k, 176k, 127k and 127k, about 0.61M in all, on the primary subscription.
- `check_matches.py` passed all four.
- `cli probe audit` on each transcript: 51 tool calls, 0 flagged. `audit_batch.py` reads a headless
  parent's stream, so its inner audit was run on each transcript directly.
- Matcher agreement, reached against not: 233 of 240 cells (validation) and 128 of 128 (post-cutoff).
  Over both seals, 382 of 390 and 208 of 208.
- **The anchors across the two seals:** X1 and X2's cells agree between D1 and D23 on 92 of 92
  (matcher 1) and 88 of 92 (matcher 2). On matcher 1 they reach 36 of 78 in-census cells in both
  rounds; on matcher 2, 36 against 32. So the two matcher pairs read alike, and reps under different
  seals can be pooled.

**The reading.** `read_stage.py D1,D23 DE DX` and `read_stage.py D1,D23 DP DE`: three reps, 117
in-census cells a condition.

| per-session reach, in-census asks, matcher 1 / 2 | DX | DE | DP | Claude X (D23 seal) |
|---|---|---|---|---|
| validation (25) | 0.21 / 0.19 | 0.44 / 0.45 | 0.67 / 0.65 | 0.48 / 0.40 |
| post-cutoff (14) | 0.24 | 0.45 | 0.60 | 0.43 |
| **pooled (39)** | **0.22 / 0.21** | **0.44 / 0.45** | **0.64 / 0.63** | 0.46 / 0.41 |
| asks reached a rep, mean (of 39) | 8.7 / 8.0 | 17.3 / 17.7 | 25.0 / 24.7 | |
| union over three reps | 11 / 9 | 22 / 23 | 29 / 29 | |
| stable, all three reps | 7 / 7 | 13 / 13 | 19 / 19 | |
| `partial` cells, in-census | 7 / 7 | 10 / 8 | 4 / 5 | |
| out-of-census (7 asks, 21 cells), the control | 13 | 14 | 15 | |
| findings a PR, the 14 ask PRs (`session_stats`) | 2.62 | 2.86 | 3.48 | |
| asks reached a finding, all asks | 0.36 / 0.34 | 0.55 / 0.56 | 0.62 / 0.61 | 0.32 / 0.29 |

- **1. DE − DX = +0.222 / +0.248: DeepSeek carries the ceiling** (rule: ≥ +0.15 on both matchers).
  The side condition holds: asks reached a finding rise from 0.36 to 0.55.
  - The ceiling has now replicated on Claude (+0.26 / +0.28), gpt-5.5 (+0.22) and DeepSeek, and failed
    on Qwen3.5 (+0.05).
- **2. DP − DE = +0.197 / +0.179: the conventions given precedence, with examples, move the reviewer
  beyond the exact brief** (rule: ≥ +0.10 on both matchers).
- **The volume guard is far from binding.** DP files 0.62 findings a PR more than DE, against the
  +3.0 guard, and its asks reached a finding rise.
- **DP − DX = +0.419 / +0.427.**
- **Rep 1 held.** Each rep's reach is within three asks of the others: DP 24, 27, 24 and DE 17, 17, 18
  on matcher 1.
  - Rep 1's interim DP − DE (+0.179 / +0.154) sits a little below the three-rep figure.
  - The control moved by one cell in each comparison.

**Where the gain sits, by the census rank of the ask's entry** (cells reached over three reps, matcher
1; matcher 2 within two cells; ranks as `docs/research/conventions-dossiers-review-2026-10/factsheet.txt`):

| entry rank | asks | cells | DX | DE | DP |
|---|---|---|---|---|---|
| 1-10 | 8 | 24 | 4 | 7 | 9 |
| 11-50 | 10 | 30 | 9 | 12 | 21 |
| 51-100 | 5 | 15 | 9 | 10 | 11 |
| > 100 | 16 | 48 | 4 | 23 | 34 |

DP's gain over DE is +2 cells on the head and +9 on ranks 11-50; the exact sentences' gain over DX is
largest in the tail (+19 cells).

**At the asks that differ by two reps or more** (DP − DE, sessions reaching of three, both matchers):
- 28649 v0029 ("please revert" a wording change): 3 against 1.
- 30458 v0062 and v0063 ("does the old proof not work?"): 3 against 0.
- 30641 v0068 (`gcongr`, rep 1's leading "check failed" miss): 2 against 0.
- 41930 p0000 (a PR-level motivation ask): 2 against 0.
- 42814 p0007 (`variable {D : ℤ}`, stage G's verified-and-dropped case): 3 against 1.
- 32875 v0090 (the `grind` tag): 2 and 1 against 0.

The one loss is 43192 p0014 (the `cat_disch` default), 2 against 3.

**DP's stable misses: 10 of 39, reached in no rep on matcher 1.**
- In the head 10 there are five:
  - v0067: `positivity`;
  - v0092 and v0093: the merged `simpa` forms;
  - v0105: a one-line proof from `infinite_pigeonhole_card_lt`;
  - p0005: generalise to a UFD.
- Outside the head there are five:
  - v0053 (rank 23): motivation tied to #24163;
  - v0064 (rank 64): the area's variable letters, which the maintainer called optional;
  - p0004 (past 100): an `alias` for an iff;
  - p0010 (past 100): `_left`/`_right` against the library's orientation;
  - p0016 (past 100): `homMk` against `mkHom`.

Rep 1's reasoning sorted these as search and execution, merits judgements and wrong comparisons (the
interim table above). v0068 is no longer a miss, so rep 1's "check failed" class was partly noise.

**Also read, mechanically.**
- **DP filed no finding in question form,** over 131 anchored findings on the ask PRs. The paragraph
  asks for a question where the change cannot be made or checked.
- **One DP finding cites another PR, an example or precedence.** Whether the examples steer the
  reasoning is not read here.
- Sessions without a submission: none (147 of 147 ok, `ds41_conv_gate.status`).
- The reasoning at the asks that differ, and at DP's 10 stable misses, is not read beyond rep 1's
  interim reading.

**What it means, at this altitude.** Three reps of one local model, 39 asks, a ceiling by
construction.
- **The pre-registered answers are both yes.**
  - A strong local model carries the exact conventions as Claude and gpt-5.5 did.
  - Telling it that maintainers' examples outrank its own judgement of the code moves it by another
    seven to eight asks of 39 a rep, without filing much more.
- **The bundle is not separated.** DP carries the examples, the precedence paragraph and a longer
  section (2.8k to 12.6k characters a PR, against DE's 0.5k to 1.2k). The ablations named before the run are now called for: the disposition
  paragraph on DeepSeek, and DP without its examples.
- **Like DE, DP is built from the asks.** Whether any of it survives choosing the conventions without
  them is untested. It is the convention-dossiers thread's next question
  (`docs/research/conventions-dossiers-review-2026-10.md` §6, on branch `conventions-dossiers`).

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

## Stage AP: the conventions chosen without the asks, delivered as DP delivers them (pre-registered 2026-10-09, before any session)

The user (2026-10-09): *"Clearly, choosing conventions without the asks is the most important question
to address at this point."* Later the same day, asked to pick the next run: *"You can pick... I want to
have a clearer picture of how to improve on the solo reviewer to get a better deployable reviewer. I
still believe sticking to the conventions is a good direction."*

**Why this stage.**
- **DP moved DeepSeek +0.20 over the exact sentences** (Result 7). But DP was built from the asks.
- **Every ask-free delivery so far moved nothing:** stage F +0.03 and stage G +0.00, both on Claude
  and without the precedence paragraph.
- **AP is the untried combination:** the ask-free picks, delivered with DP's examples and precedence,
  on DeepSeek. It is the simplest deployable form of "stick to the conventions", a section in the solo
  reviewer's context, and the third adversarial round named it the engine's cheaper rival
  (`docs/research/deployable-reviewer-review-2026-10.md`).

**Its gap to the ceiling.** It sits between DP and DX by construction. It keeps the selector's
retrieval (the right entry is in the 25 for 22 of these PRs' 33 in-census asks), and it pays for the
section's length.

**The design.**
- **The PRs:** the ten stage C PRs with stage F's picks: validation 28649, 29842, 30458, 30641,
  32875, 34091; post-cutoff 41930, 42184, 42814, 43167. They hold 33 in-census asks.
- **The section:** stage F's blind Opus picks (`briefs_applicable.json`, 25 a PR, 142 distinct
  entries), delivered exactly as DP's section.
  - DP's lead and the sentences in codebook order.
  - Up to two census asks beneath each sentence, by DP's mechanical rule (`examples_ap.json`): reader
    A's census asks filed under the entry, on val1000 and outside_years PRs, in stage G's seeded order,
    first two, none on a probe PR (asserted). 111 entries have two, 30 one, 1 none.
  - `probes.CONVENTIONS_PRECEDENCE` after the list.
  - `build_context.py ap <bodies>` builds it. The two context files carry census bodies and are not
    committed; `context_ap.sha256` holds their digests, and `run_ds41.sh` refuses any other bytes.
  - `prec`'s rebuild stays byte-identical (checked 2026-10-09).
  - The section is 47k-66k characters a PR against DP's 6k-37k, so length is part of the design, as
    for DP.
- **The model and runs:** as DX, DE and DP: DeepSeek-V4.1-Flash, keepthink, reasoning high, contract
  v2, the stage D configs. Three reps, `iter_ds41_conv_<val|post>_ap_rep<n>`.
- **Preflight:** `cli plan` passes for both sets, with reviewed workspaces 6 of 6 and 4 of 4.
- **The gate:** `run_stage_ap_gate.sh`, one Slurm job.

**Matching.**
- **One seal a set,** on these ten PRs, over X1, X2, DX1-3 and AP1-3: eight sessions a PR, as D23.
  DX is matched again under the same seal as AP, so the comparison stays within one seal.
- **The procedure:** two blind matchers a set as subagents, `cli probe audit`, `cli probe unblind`
  into `match_AP_<set>/`.
- **The reading:** per-session reach on the in-census asks, pooled over three reps, read with
  `read_stage.py AP AP DX`.

**Reading rule, fixed before any session.**

| AP − DX, pooled in-census reach, both matchers | reading |
|---|---|
| **≥ +0.10** (10 cells of 99, about three asks a rep) | **the conventions, chosen without the asks and delivered with precedence, beat solo DeepSeek.** The first ask-free convention delivery to move a reviewer |
| **≤ +0.05** | **they do not.** Stage F's result holds on DeepSeek with precedence: the gain needed the asks' own choice of conventions |
| between, or the matchers disagree | inconclusive; read the reasoning at the asks that differ |

- **Volume guard:** AP's findings a PR are at most DX's + 3.0, and asks reached a finding are no lower
  than DX's. If AP fails either, it is a volume effect whatever its reach.

**Also read:**
- **AP_i ∪ DX_i against DX_i ∪ DX_j**, paired by rep, under the same seal. This is the round's
  comparator: does AP add over solo run twice?
- **AP against DP's cells** on these PRs (DP's own seals): how much of DP's gain survives choosing
  without the asks. They are different seals, so this is not a reading.
- **The split by whether the ask's entry is in AP's picks** (22 asks) or not (11).
- **Findings a PR, and asks reached a finding.**
- **Partial cells.**
- **The out-of-census asks** on these PRs.

One ask moving in every rep is 3 cells, 0.030.

**Limits, stated before.**
- One model, three reps, 33 in-census asks.
- The picks were made by Opus, not by the reviewer's own model.
- These PRs were chosen in stage C because Claude X missed asks there, and every stage since used
  them, so they are in-sample.
- A positive here is a direction, to be checked on a fresh set (the round's validation remainder)
  before any claim.

**Cost.**
- **Generation:** GPU on `first` only. 30 sessions at once, about 1-1.5 hours plus 12 minutes to
  serve. $0.
- **Matching:** four matcher runs, about 0.4-0.6M tokens on the primary subscription. Its week reset
  at 10:00 on 2026-10-09.

## Result AP (2026-10-09): the conventions chosen without the asks move DeepSeek +0.18 on both matchers; the yield guard misses by 0.014

**How it ran.**
- **The runs:** six, 30 sessions, none failed (gate 443397, 11:56 to 12:38; `23028b47`).
- **The seal:** one a set on the ten PRs, committed before any judging (`f189c546`).
- **The matchers:** four blind matchers, subagents with the generated prompts verbatim.
  - `check_matches.py` passed all four.
  - Audit: 9-13 tool calls each, 0 flagged.
  - Agreement on reached-or-not: 216 of 216 and 88 of 88.
  - Tokens: 164k, 168k, 105k and 106k.
- **The reading:** `read_stage.py AP AP DX`.

| in-census reach (33 asks, 99 cells), matcher 1 / 2 | DX (solo DeepSeek) | **AP** | Claude X (same seal) |
|---|---|---|---|
| validation (22) | 0.11 / 0.11 | 0.36 / 0.36 | 0.41 |
| post-cutoff (11) | 0.27 / 0.27 | 0.30 / 0.30 | 0.27 |
| **pooled** | **0.16 / 0.16** | **0.34 / 0.34** | 0.36 |
| all asks (38, 114 cells) | 0.22 | 0.38 | 0.39 |
| findings a session-PR | 2.70 | 4.87 | 5.25 |
| asks reached a finding | 0.309 | 0.295 | 0.286 |

**By the rule.**
- **Reach: AP − DX = +0.182 on both matchers,** against the +0.10 bar.
- **The volume guard:**
  - findings a PR rise by 2.17, inside the +3.0 guard;
  - **asks reached a finding fall from 0.309 to 0.295.** The rule required them no lower, so read as
    written it labels the gain a volume effect. The miss is 0.014, about two asks of 146 findings.

**Also read, as pre-registered.**
- **The added findings hit asks at near solo's rate.** AP gains 18 cells for 65 more findings, 0.28
  a finding, against DX's own 0.31. Stage F's 25 sentences fell to 0.18 against 0.27, and the
  detectors under the disposition filed 13 of 14 unasked facts.
- **Against solo run twice,** paired by rep: AP_i ∪ DX_i reaches **0.364**, against DX_i ∪ DX_j
  **0.192**, on both matchers.
- **The split by selection:**

  | | asks | AP | DX |
  |---|---|---|---|
  | the ask's entry among the picks | 22 | **0.50** | 0.20 |
  | not among them | 11 | 0.03 | 0.09 |

- **Union over three reps:** AP 15, DX 7 of 33. Stable in all three reps: AP 7, DX 4.
- **Against DP on these asks** (stage D's seals, not a reading): DP reaches 0.61, so AP keeps about
  40% of DP's gain over DX with ask-free selection.
- **Asks gained, in every rep or most:**
  - 28649 v0029 ("please revert");
  - 30458 v0062 and v0063 (the old proof);
  - 34091 v0106-v0108 (instance-implicit classes);
  - 32875 v0094 and v0095 (`simpa`);
  - 42814 p0007 (`variable`).
- **Ask lost:** 30641 v0066, which DX reaches 3 of 3 and AP 1 of 3.
- **The out-of-census asks did not move:** 9 of 15 cells for both.

**What it means, at this altitude** (one model, three reps, 33 asks, in-sample PRs, Opus-made picks).
- **This is the first ask-free convention delivery in the record to move a reviewer by the rule's
  reach bar.** DeepSeek given 25 conventions picked from the diff, each with two maintainers' asks
  and the precedence paragraph, reaches what unbriefed Claude Opus reaches on these PRs, at fewer
  findings.
- **Its gain sits on the asks whose convention the selector picked.** So selection quality is now
  the lever: the picks held the entry for 22 of 33.
- **The guard's narrow miss is reported as a miss.** Whether the extra 2.2 findings a PR are welcome
  is the open adjudication.
- **Before any claim:** a fresh set, and the picks made by the reviewer's own model.
