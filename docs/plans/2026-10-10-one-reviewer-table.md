# One reviewer table: every reviewer, every benchmark, scored once (plan, 2026-10-10)

*Revised after an adversarial review round (`docs/research/one-reviewer-table-review-2026-10.md`).
The first draft is commit `fcb61c9e`.*

**Why** (the user, 2026-10-10): the write-up's ten-PR set has DeepSeek closer to gpt than to Claude,
while on dev DeepSeek sits near Claude. *"These numbers are important and we'll be making decisions
motivated by these results ... we have to first collect the data cleanly."* The data has variance,
and the picture may not come back clean. This plan fixes how each cell is collected, before any of
them is read.

## What is wrong with the cells on disk

| defect | where | effect |
|---|---|---|
| gpt-5.5 ran brief G on the probe sets and contract v2 on dev; DeepSeek ran contract v2 on both | `probe_*_gpt55_Grc*` vs `probe_dev_gpt55_Grc_contract2_rep1` | the gpt row is not like-for-like with DeepSeek on P14 |
| the "Claude" on dev that DeepSeek sits near is the project harness (7, 7); the Claude on P14 is the X route (11, 11 on dev) | `probe_dev_opus55_contract2_claude_sub_*` vs `probe_dev_claude_X*` | two Claudes, one name |
| seven seals, each read separately | `match_{L,C,F,M,W,D,AP}_*` | the same two Claude sessions read 0.27-0.39 on the ten PRs (`read_common.py`): about ±0.06 between seals |
| reps: Claude 2, gpt 1-2, DeepSeek 3 | runs dir | the 3-rep rule is met only by DeepSeek |
| AP ran on the ten stage F PRs only | `iter_ds41_conv_*_ap_*` | no AP cell on all 14 PRs, none on dev |
| the ten PRs were chosen as those holding an ask neither Claude session reached | stage C | a subset selected on one row's misses; it is not a benchmark |
| dev runs judged on two endpoints | X1, X2, gpt rep 1 on `gpt_5_mini`; DeepSeek on `elm_gpt_5_mini` | a second scorer |
| DeepSeek's dev solo reps ran on a plain server, before `8538502a` made DSpark the default | `iter_ds41_contract2_keepthink_high_*` | AP on dev would run on a different server |

## The table

**Two benchmarks, never pooled.** Each keeps its own standard scorer, and a second, shared scorer
spans both.

| | **P14**: the conventions probe sets | **D12**: dev held-out 12 |
|---|---|---|
| PRs | 14 with asks: validation small12's 8 and post-cutoff's 6, reported per set and pooled | 12 scored; every new run covers all 15, so the 3 controls give volume |
| gold | 46 maintainer round-1 asks; 39 in census | 23 obligations; census share labelled before AP runs |
| standard scorer | two blind matchers, one seal per set holding every row's sessions | judge v9 on `elm_gpt_5_mini`, every run re-judged into one cache |
| shared scorer | (the same) | one blind-matcher seal over the 23 obligations |
| measures | per-session reach on all asks (the headline) and on in-census asks; findings a PR; yield (hits a finding) | issue recall per session; findings a PR; the same matcher measures |
| leakage | census is PR-disjoint | census is PR-disjoint; examples come from val1000 and outside_years only |

Both benchmarks are in-sample for the conventions work. The table describes; the fresh set decides
(below). Training windows are stated per row against each set's dates: Claude's cutoff is June
2026, so validation and dev fall inside it and post-cutoff outside; DeepSeek-V4.1 (released
2026-09-10) and gpt-5.5 publish none.

**Rows: one configuration each, named by model and harness.**

| row | configuration | P14 | D12 | to collect |
|---|---|---|---|---|
| **Opus 5.5, X route** | brief X as a Claude Code `general-purpose` subagent, effort xhigh, CLI 2.1.284, 2026-09-29 (the project's CLAUDE.md was in its context) | X1, X2 | X1, X2 | re-judge D12 only; reported at 2 reps, with their 37-of-39 agreement |
| **Opus 5.5, project harness** | contract v2 on the subscription route (`claude_sub`) | none | 3 reps on disk | re-judge only |
| **gpt-5.5** | contract v2 under `ape_agent`, `elm_gpt_5.5`, Responses with carry-over (both lines stated), effort high | none at contract v2 | 1 old rep (OpenAI endpoint) | 3 new reps on each |
| **DeepSeek-V4.1-Flash** | contract v2, keepthink, effort high, server defaults since `8538502a` | 3 reps (stage D) | 3 old reps, plain server | 3 new D12 reps, in the AP server job |
| **DeepSeek + AP** (deployable) | stage F's blind Opus selector, 25 picks a PR from the diff, two census examples each, the precedence paragraph | 3 reps on 10 of the 14 PRs | none | selectors and 3 reps on P14's other 4 PRs and on D12's 15 |
| derived | DX_i ∪ DX_j and AP_i ∪ DX_i, paired by rep (`deployable-reviewer-review` §4's comparator) | from the above | from the above | nothing |
| *optional, the user's call:* **Opus 5.5 today, solo and + AP** | the X route, a fresh label, one rep each, same day | | | 28 sessions on P14 |

Not in the table:
- **Qwen:** the floor tier.
- **The ceiling rows (E, DE, DP, GE, GD):** they need the asks, and they keep their own seals in a
  separate table.
- **The ten-PR subset:** it was selected on Claude's misses.

## Order, so an early stop still reports

| step | what | resource | expected |
|---|---|---|---|
| 0 | the fresh set's reviewed workspaces (Slurm job 449292, started 04:31) | CPU | 39 builds, about 12 minutes each |
| 1 | re-judge every D12 run on disk on `elm_gpt_5_mini`; derived rows; the PR-cluster bootstrap in `read_common.py` | ELM, pennies | a first D12 reading of the rows on disk |
| 2 | D12 census share: two readers assign the 23 obligations to the codebook; the expected AP effect written here | Claude, about 0.1M tokens | |
| 3 | 19 blind selectors (P14's 4, D12's 15), stage F's rubric and route; the new AP level (own files, per-row check of the ten, dev PRs in the leak assertion) | Claude | about 3 points of a five-hour window each: 0.6 of a window |
| 4 | gpt-5.5 contract v2, 3 reps, P14's 14 and D12's 15 | ELM | billed about $1.0 a PR on validation and $1.3 on dev: about $100 (about £80 of the £397 left) |
| 5 | DeepSeek AP on P14's 4 PRs, 3 reps; DeepSeek solo and AP on D12's 15, 3 reps each | `first`, 8 GPUs and 900 GB | one server job, 3-4 hours; the GPUs are held by another user's jobs until 18:00-23:00 today, with more queued |
| 6 | P14: one seal a set (X1, X2, GPT1-3, DX1-3, AP1-3; 11 sessions a PR), matcher inputs fixed (Claude targets through `resolve_target`, convention phrasing redacted, the 20-finding cut), matcher instances batched by PR; D12: judge v9 on the new runs, and one matcher seal over the 23 obligations | Claude, ELM | about 1.5M tokens; a few pounds |
| 7 | the optional same-day Claude pair, if chosen | Claude | about 2.8 windows |
| 8 | read; replace the table in `docs/research/beating-solo-2026-10.md` | none | |

## Reading rule, fixed before any cell is collected

- **Each benchmark is read once its cells are scored.** Step 1's reading of the rows on disk is
  labelled provisional.
- **Every cell reports:** the reps' values, the mean, the union, the stable count, findings a PR,
  and yield.
- **An ordering between two rows needs two things on the same seal:**
  - their rep ranges do not overlap;
  - a paired PR-cluster bootstrap (10,000 draws over PRs) excludes 0 on both matchers.

  The leave-one-PR-out range is reported beside it. Rows that fail either test are reported as
  indistinguishable on that benchmark.
- **Minimum detectable differences, stated now:** about 0.18 of reach on P14 and about 5 of 23 on
  D12. A smaller true difference, such as DeepSeek against gpt on P14 if it stays near one ask, will
  read as indistinguishable by construction.
- **AP's range is conditional on one selector draw.**
- **The questions the table answers, without deciding them:**
  - Where does DeepSeek sit between gpt-5.5 and each Claude harness, on each benchmark and each scorer?
  - Does that agree across benchmarks once the scorer is shared?
  - Does AP move DeepSeek, against both DX and DX ∪ DX, on all 14 PRs, per set, and on dev?
- **If the benchmarks disagree under the shared scorer, report the disagreement.** Do not choose
  between them.

## After the table: the fresh set decides

40 validation-window PRs no design has touched (75 asks on 34; 6 no-ask controls). Their reviewed
workspaces were never built, because none of these PRs has been run. They are building now (step 0).
The decision test there is DeepSeek AP against DeepSeek solo, three reps, by
`deployable-reviewer-review-2026-10.md` §4, with one Claude rep as a reference if the week allows.
It tests overfitting to the PRs designs were developed on. It does not test the
validation/post-cutoff split, because the fresh set is all validation-window.
