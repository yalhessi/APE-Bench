# Corrections the record needs — each verified against the artifacts it cites

**Status** — open; all are docs edits
**Cost** — none
**Rule** — these touch `docs/dead-ends.md`, which is the user's own register. Amend, never silently
rewrite, and keep each entry's conclusion separate from its stated cause: in every case below the
conclusion survives and the mechanism does not.

## In `docs/dead-ends.md`

**The 33145 clause of "Specialists as the coverage floor".** The entry says the decline there was
"the right arm was never asked … the arms present were duplication/api_reuse/style, each correctly
reporting nothing in its own concern". In the very run it cites (`pr5_F_fanout_stage1_rep1`, 173
jobs, 44 arm sessions on 33145) the `naming` arm ran on all four units and at
`wu:1031e8acbe2db1ea15d6a50e` returned `status=success` with two candidates — renames of
`Dense.continuous_upperBounds` and `Dense.continuous_lowerBounds` — both `admission=published`. The
judge scored both `issue_match=False` because each addressed only half the coordinated ask. So that
decline was **not** a routing failure and not an abstention; it was resolution scope. The entry's
conclusion (more slots do not help) is untouched.

**The 33337 clause of the same entry.** It says `naming_norm` returned `insufficient_evidence` and
that the obligation "was never hit by any condition". Both are false. The verdict was **`emerging`**
— the arm abstained `below_my_bar` with the detail "the third was only emerging (`toLinearMap_` 21 vs
`coe_` 7), so I'm not requesting renames" — and the obligation has been issue-matched **31 times
across 38 audits**, three of them by the naming arm itself. The true version is a *stronger* case for
the entry's own point: in the same work unit the generalist received the **byte-identical**
`naming_norm` trace row and did make the ask, and it was gold-matched. Identical evidence, different
bar, opposite outcome. The genuinely never-hit obligation is a different one and should be named.

**The fanout cost figures.** "Fanout costs $0.085/job against lead's $0.040 (arms are top-level
tasks, so they lose the nesting/caching benefit)". Those are **nominal against billed**: $0.085 =
$14.724 nominal / 173 jobs, $0.040 = $12.786 *nested_billed* / 321. The same manifest records
fanout's billed at $5.066 = **$0.0293/job**. Restricted to the same four PRs, lead is $0.0837/job
nominal and $0.0318 billed — so per job fanout is +1.7% nominal and **−7.9% billed**. The stated
mechanism is also backwards: fanout's cache hit rate is **80.2% against lead's 71.2%**. Quote both
figures side by side and drop the caching clause. The entry's conclusion is unaffected — it rests on
recall, not cost.

**Judge noise.** Add the n=705 v9 measurement (76 split pairs, 10.8%, 89.2% ceiling) beside the
existing ~11% line, and note that `judge-v8/VERDICT.md`'s 0/18 result does not carry forward to
anything currently scored.

**A new entry.** Record the 2026-09-14 absolute-confidence-threshold measurement as the fourth
falsification, so it is not re-derived a third time — and record explicitly that the *within-PR
relative* form remains open, because the sentence in `phase-c-corrected-history.md:45-46` that closes
the absolute form says the relative form works.

## In `docs/plans/2026-09-14-selection-over-coverage.md` and commit `5691ade`

- Confidence spread is **0.12–0.92**, not 0.22–0.90.
- `rejected_alternatives` is unrequested, not dropped: 2 non-empty of 1,528 across 54 runs. Step 1's
  pinning test would have passed on an always-empty list. Remove it from the "fifth serialization
  drop" framing.
- Step 2's frontier and Step 3's $35–60 out-of-sample run are answered already and should be struck:
  within-PR AUC 0.486/0.485/0.516 on 907 candidates.
- The `pr5_F_fanout_heldout12_v2_rep1` directory is **not** "plan-only" as Step 0 describes it. It
  holds a sealed `run_plan.json` (agenda_sha256 `e5d0bc40…`, `routing_mode: fanout`, git_commit
  `3a3bf72`, tree dirty), a 14 MB `arm_pool.jsonl` and 156 `context_trace` rows — an **aborted run**.
  A resume under that name would seal onto a design `dead-ends.md` has retired, at ~$111 nominal.
- "Selection over discovery as the spine" needs its regime stated: it holds in the flooded forced
  condition and not on the held-out 12, where coverage loss and selection loss are within one
  obligation of each other in every rep.

## In `docs/research/`

- `pr-review-next-iteration-roadmap.md` R0 row: v9 is active, not v8.
- `ab-heldout12-obligation-spine.md` §6: re-report with and without PR 33149, which is 68.9% of
  condition A's findings and 85.4% of its blocking demands.
- The "arms cannot reach design" retraction: add the six-run numbers, the design-vs-local location
  split, and the condition qualifier (holds for lead, fails twice for solo).

## In the code comments

`merge.py:256` and `digest.py:145` say `model_confidence` was "falsified three times as a ranking
signal" with no citation. The three are `phase-c-corrected-history.md:45-46`,
`pr-review-v5-principled-design.md:58`, and `pr-review-v4-evidence-pipeline-design.md:768`. Add the
pointers, and note that what was falsified is the **absolute** form.
