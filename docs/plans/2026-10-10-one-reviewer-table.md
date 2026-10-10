# One reviewer table: every reviewer, every benchmark, scored once (plan, 2026-10-10)

**Why** (the user, 2026-10-10): the write-up's ten-PR set has DeepSeek closer to gpt than to Claude,
while on dev DeepSeek sits near Claude. *"These numbers are important and we'll be making decisions
motivated by these results ... we have to first collect the data cleanly."* The data has variance,
and the picture may not come back clean. This plan fixes how each cell is collected, before any of
them is read.

## What is wrong with the cells on disk

| defect | where | effect |
|---|---|---|
| gpt-5.5 ran brief G on the probe sets and contract v2 on dev; DeepSeek ran contract v2 on both | `probe_*_gpt55_Grc*` vs `probe_dev_gpt55_Grc_contract2_rep1` | the gpt row is not like-for-like with DeepSeek on either benchmark |
| seven seals, each read separately | `match_{L,C,F,M,W,D,AP}_*` | the same two Claude sessions read 0.27-0.39 on the ten PRs (`read_common.py`): about ±0.06 between seals |
| reps: Claude 2, gpt 1-2, DeepSeek 3 | runs dir | the 3-rep rule is met only by DeepSeek |
| AP ran on the ten stage F PRs only | `iter_ds41_conv_*_ap_*` | no AP cell on all 14 PRs, none on dev |
| the ten PRs were chosen as those holding an ask neither Claude session reached | stage C | a subset selected on one row's misses; it is not a benchmark |
| dev runs judged on either side of the 2026-10-06 judge move (to be checked per run) | Claude X1/X2 (2026-10-01) vs later runs | the move forked the cache; 73 of 76 verdicts agree, but it is a second scorer |

## The table

**Two benchmarks, each with its own scorer, never pooled:**

| | **P14**: the conventions probe sets | **D12**: dev held-out 12 |
|---|---|---|
| PRs | 14 with asks: validation small12's 8 and post-cutoff's 6 | 12 scored, of the release's 15 |
| gold | 46 maintainer round-1 asks; 39 in census | 23 obligations |
| scorer | two blind matchers, **one seal per set holding every row's sessions** | judge v9 on `elm_gpt_5_mini`, every run in the same judge cache |
| measures | per-session reach, all asks and in-census asks; findings a PR | issue recall per session; findings a PR |
| leakage | census is PR-disjoint (README "Sets") | census is PR-disjoint: 0 of the 15 dev PRs among val1000's 759; examples come from val1000 and outside_years only |

Both are in-sample for the conventions work: designs were developed watching P14, and dev is
development material under the 2026-09-24 ruling. The table describes, and the fresh set decides
(below).

**Rows: four reviewers, one configuration each, the same on both benchmarks.**

| row | configuration | P14 now | D12 now | to collect |
|---|---|---|---|---|
| **Claude Opus 5.5, solo** | brief X, a `general-purpose` subagent, `claude-opus-5-5`, effort xhigh (the X route) | X1, X2 | X1, X2 (11, 11) | X3 on both: 14 + 12 sessions |
| **gpt-5.5, solo** | contract v2 under `ape_agent` (brief G2, user prompt v2), `elm_gpt_5.5`, Responses with reasoning carry-over | none at contract v2 | 1 rep on the OpenAI endpoint (3 of 23) | 3 reps on both, all on ELM |
| **DeepSeek-V4.1-Flash, solo** | contract v2, keepthink, effort high, self-hosted | 3 reps (`iter_ds41_conv_*_base`) | 3 reps (`iter_ds41_contract2_keepthink_high`) | nothing |
| **DeepSeek + AP** (deployable) | stage F's blind Opus selector, 25 picks a PR from the diff, delivered with two census examples and the precedence paragraph | 3 reps on 10 of the 14 PRs | none | selectors and 3 reps on P14's other 4 PRs; selectors and 3 reps on D12 |

Not in the table, and why:
- **Qwen:** the floor tier (`docs/dead-ends.md`).
- **The ceiling rows (E, DE, DP, GE, GD):** they are diagnostic and need the asks. They keep their own
  seals, in a separate table.
- **The ten-PR subset:** it was selected on Claude's misses.
- **Claude and gpt with AP:** a design question, not a fill.
- **The no-ask controls:** volume reads from findings a PR on the ask PRs.

## Order, so an early stop still reports

| step | what | resource | expected |
|---|---|---|---|
| 0 | this plan committed; configs; run names | none | |
| 1 | 16 blind selectors (P14's 4, D12's 12), stage F's rubric and route | Claude | about 3 points of a five-hour window each: half a window |
| 2 | gpt-5.5 contract v2, three reps, P14's 14 PRs and D12's 12 | ELM | billed about $1.0 a PR on validation, $1.3 on dev: about $90 (about £70 of £397 left) |
| 3 | DeepSeek AP, three reps, P14's 4 PRs and D12's 12 | `first`, 8 GPUs | one server session, 2-3 hours; waits for the 8 GPUs another user holds until 18:00-23:00 today at the latest |
| 4 | Claude X3, P14's 14 and D12's 12, the X route | Claude | about 10 points a session: 2.6 windows. The step to cut first: X1 and X2 agree on 37 of 39 in-census asks |
| 5 | P14: one seal a set holding X1-3, GPT1-3, DX1-3, AP1-3 (12 sessions a PR), two fresh matchers each; D12: `cli judge` on all twelve runs, Claude's re-judged | Claude, ELM | about 1M tokens; a few pounds |
| 6 | read, and replace the table in `docs/research/beating-solo-2026-10.md` | none | |

Run names: `probe_{val_small12,postcutoff,dev}_elmgpt55_contract2_rep<n>`;
`iter_ds41_conv_{val,post}_ap4_rep<n>`; `iter_ds41_dev_ap_rep<n>`; Claude X3 as `probe_dev_claude_X3`,
with the probe sets' X3 beside X1 and X2. The extended AP context keeps the ten PRs' bytes, checked
against `context_ap.sha256`.

## Reading rule, fixed before any cell is collected

- **Each benchmark is read only once all its cells are scored.**
- **Every cell reports:** the three reps' values, the mean, the union, the stable count, and findings a
  PR.
- **An ordering between two rows is claimed only when their rep ranges do not overlap.** Overlapping
  rows are reported as indistinguishable on that benchmark.
- **Noise bands, stated now:** about ±0.06 between seals, though one seal per set removes that term;
  about ±2 of 23 on D12 (the judge's ~90% self-agreement).
- **The questions the table answers, without deciding them:**
  - Where does DeepSeek sit between gpt-5.5 and Claude on each benchmark?
  - Does that position agree across the two?
  - Does AP move DeepSeek on all 14 PRs and on dev, as it did on the ten?
- **If the benchmarks disagree, report the disagreement.** Do not choose between them.

## After the table: the fresh set decides

40 validation-window PRs no design has touched (75 asks on 34; 6 no-ask controls). 39 of their 40
workspaces have never been built, because none of these PRs has been run: about 6-7 hours of CPU and
110 GB (disk: 2.4 TB free). The builds are CPU only and can run beside steps 1-5. The decision test
there is DeepSeek AP against DeepSeek solo, three reps, by `deployable-reviewer-review-2026-10.md`
§4, with one Claude rep as a reference if the week allows.
