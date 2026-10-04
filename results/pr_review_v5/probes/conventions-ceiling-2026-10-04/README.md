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

## What closes it

The table above, per matcher and per set, here and in the todo. The Claude exact step then runs or
does not on the todo's own terms; the only way this stage stops it is by showing that most asks are
out of census, or that the machinery is wrong.
