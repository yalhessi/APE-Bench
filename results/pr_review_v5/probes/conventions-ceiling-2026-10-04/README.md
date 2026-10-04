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

## The Claude stage is ready and has not started

`cli probe packets --set <set> --sessions E1 E2 --prs <ask PRs> --scratch <dir> --conventions
briefs_exact.json --codebook <reader A's codebook>` writes brief X with the section at its end;
`briefs_exact.json` is the same file stage L read. The machinery from labels to reading has now run
end to end. The step is 28 reviewer sessions and four matcher runs, the todo's 1.5 subscription
windows, and it waits for the user.

## What closes it

The table above, per matcher and per set, here and in the todo. The Claude exact step then runs or
does not on the todo's own terms; the only way this stage stops it is by showing that most asks are
out of census, or that the machinery is wrong.
