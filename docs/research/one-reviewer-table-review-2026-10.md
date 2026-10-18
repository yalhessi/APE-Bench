# The one reviewer table: adversarial review round (2026-10-10)

The draft plan (`docs/plans/2026-10-10-one-reviewer-table.md` at `fcb61c9e`) went to two independent
reviewers before anything was spent. Both worked read-only and called no model.
- **Comparability:** what makes a cell differ for a reason other than the reviewer.
- **Decision value:** whether the table answers the user's question, and with what power.

Their reports are verbatim in `one-reviewer-table-review-2026-10/`. The user's three answers
(Claude rep 3 last in order; gpt-5.5 at three reps on both benchmarks; fresh-set builds now) came
before the reports. Where a report bears on an answer, it says so below.

## What changed in the plan

| finding | reviewer | outcome |
|---|---|---|
| The Claude row and the ape rows run in different harnesses. Opus reads 11, 11 on dev under the X route and 7, 7 under the project harness (8 after the ELM re-judge), more than the noise band. | both | **Adopted.** Two Claude rows, each labelled by harness. The project-harness row (`probe_dev_opus55_contract2_claude_sub`, three reps on disk) goes on D12 only, re-judged, at no generation cost. |
| X3 is not a third rep of X1/X2. X1/X2 ran on 2026-09-29 on CLI 2.1.284, before `5e215ffe`, with that day's CLAUDE.md in context. The label X3 already exists in `construction-demo-2026-09-29`. A dev import needs all 15 PRs. | comparability | **Adopted; it overturns the user's answer on rep 3.** New Claude sessions are a same-day condition with a fresh label, reported beside X1/X2 and never pooled with them. How to spend that budget goes back to the user. |
| Claude with AP's delivery is the cell that says whether conventions beat the best solo reviewer, not only lift DeepSeek to it. | decision value | **Offered to the user**, as a same-day pair (Claude solo and Claude + AP, one rep each on P14). It costs about what X3 would have. |
| DeepSeek's dev solo reps ran on a plain server (DSpark off, flags by hand). Since `8538502a` (2026-10-08 02:28), AP runs on the defaults. | comparability | **Adopted.** Three new dev solo reps run in the same server job as the dev AP reps. P14's solo reps (stage D, after `8538502a`) and AP reps share the defaults. |
| The rep-range rule ignores PR clustering. Reps are nearly deterministic per PR, so ranges are narrow. AP − DX is [+0.02, +0.39] by PR bootstrap, and dropping PR 34091 halves it. | decision value | **Adopted.** An ordering needs both non-overlapping rep ranges and a paired PR-cluster bootstrap on the same seal that excludes 0 on both matchers, with the leave-one-PR-out range reported. Minimum detectable differences are stated now: about 0.18 on P14 and about 5 of 23 on D12. |
| The two benchmarks differ in scorer as well as PRs, so a disagreement between them cannot be explained. | decision value | **Adopted.** Add one blind-matcher seal over D12's 23 obligations, so one scorer spans both. Judge v9 stays as D12's standard measure. |
| No decision depends on the gpt row. P14 only, and keep D12's rep 1. | decision value | **Not adopted.** The user asked for gpt beside DeepSeek and Claude, and chose three reps on both with the cost in view. All three D12 reps run new, so the D12 ape rows share one day and one tool state. |
| The comparator of `deployable-reviewer-review` §4 is DX_i ∪ DX_j, paired by rep. | decision value | **Adopted.** The derived rows DX ∪ DX and AP ∪ DX go in every cell, at no cost. |
| AP's three reps share one selector draw. | comparability | **Adopted** in the reading rule: AP's range is conditional on one pick set. |
| AP on D12 has no stated expectation, and dev's census share was never measured. | decision value | **Adopted.** Two readers label D12's 23 obligations against the codebook (about 0.1M tokens), and the expectation is stated before the run. |
| Run all 15 dev PRs, so the 3 controls give a volume reading. | decision value | **Adopted** for every new D12 run. |
| The AP tooling rewrites `context_*_ap.jsonl`, `examples_ap.json` and `context_ap.sha256` in place. `run_ds41.sh` takes no new level. The probe-PR assertion omits dev. | comparability | **Adopted.** A new level with its own files and digests. The ten PRs' rows are checked by per-row hash, and the dev PRs go into the assertion. |
| Matchers can tell the harnesses apart: Claude targets are prose, AP findings name "the convention", and `_claude` skips the 20-finding cut. | comparability | **Adopted.** Claude targets are rendered through `resolve_target`, the convention phrasing is redacted, and the cut applies. |
| A 12-session seal is larger than any matched so far: about 400 findings against D23_val's 251. | comparability | **Adopted.** One seal a set, with matcher instances batched by PR and all of a PR's sessions together. |
| X1, X2 and gpt's dev rep 1 were judged on `gpt_5_mini`; the DeepSeek reps on `elm_gpt_5_mini`. | comparability | **Adopted.** Every D12 run is re-judged on `elm_gpt_5_mini` before any reading. |
| Training windows confound cross-model comparisons. | comparability | **Adopted.** P14 is reported per set (validation and post-cutoff) as well as pooled, and each model's cutoff is stated against each set's dates. |
| Headline all asks for ordering, and report yield and added-findings yield. | decision value | **Adopted.** |
| An early stop leaves nothing readable. | decision value | **Adopted.** The free re-judges and derived rows come first, and the P14 seal does not wait on new Claude sessions. |
| The fresh set should get the paid capacity. | decision value | **Partly adopted.** The builds started at 04:31 (Slurm job 449292). Its runs follow the table. |

## Verified by the reviewers as correct

- **DeepSeek's P14 and D12 configurations match** apart from context file, PR list and concurrency;
  the dev reps share one `scaffold_config_sha256`.
- **The packets carry the same information.** Every X packet's `model.md` equals the matching ape
  context row on all four sets.
- **gpt contract v2 differs from DeepSeek's setup only in model, API and caps.**
- **The census is PR-disjoint from dev:** none of its 16 PRs is among val1000's 759, outside_window's
  300 or outside_years' 129.
- **The on-disk numbers match the record:** 11, 11; 8, 6, 9; 3; X at 0.27-0.39 across seals.
