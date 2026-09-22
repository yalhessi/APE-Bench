# Open todos — the hypotheses worth spending on next

The register of work this project has decided is worth doing and has not done. It sits beside the
other three records and answers a question none of them answers:

| Record | Answers |
|---|---|
| `docs/PROJECT-STATUS.md` | what exists |
| `docs/plans/STATUS.md` | what a plan asked for, and whether it got built |
| `docs/dead-ends.md` | what was tried and stopped, and what would reopen it |
| **`docs/todo/`** | **what is open, why we believe it is worth doing, and what would close it** |

## The rule that makes this file worth keeping

**Every todo carries the motivating example that made us interested in it** — a measured result, a
named PR, a run path, a line of code. A todo with no motivating example is a wish, and wishes are
how this project has previously spent money on the wrong thing. If you cannot name the observation
that made the item interesting, it does not go in.

A todo is *not* a plan. Plans live in `docs/plans/<date>-*.md` and are kept verbatim. A todo is the
one-screen case for doing the work at all; when a todo grows a design, it gets a plan and this entry
links to it.

## How to use it

- **Before proposing a direction:** read this index and `docs/dead-ends.md`. If the direction is
  already here, pick it up rather than restating it; if it is in `dead-ends.md`, say so and cite the
  entry.
- **When a session surfaces a new hypothesis it will not pursue:** write it here before the session
  ends. Compaction drops what only exists in conversation, and this project has re-derived the same
  idea in three separate sessions.
- **When a todo is closed:** move it to `docs/dead-ends.md` if it was tried and stopped, or strike it
  here with the commit that closed it. Do not silently delete an entry — the reason it was open is
  part of the record.
- **One file per todo** in this directory, named `<area>-<slug>.md`; this file is the index and is
  the only place the list lives.

## Entry format

```markdown
# <title>

**Status** — open / in progress / blocked on <what>
**Cost** — an estimate in dollars of billed spend, or "no spend"
**Motivating example** — the measurement, PR, or line of code that made this interesting
**What would close it** — the concrete check, not a direction of travel
**Evidence** — file:line, run paths, commit hashes
**Risk** — what makes this possibly not worth doing
```

---

## The list

Written 2026-09-14 from an evidence sweep over the tree and the committed run artifacts. Every claim
below was gathered by one pass and then re-measured by an adversarial second pass; where the two
disagreed, the entry carries the corrected number and says what was refuted. Nothing here is costed
above "one rep" without a measurement behind it.

| Todo | The motivating result | Cost |
|---|---|---|
| ~~[Specialist abstention interventions](specialist-abstention-interventions.md)~~ *(opened and **closed unfunded** 2026-09-21)* | Replayed 3x at the decision turn, **41 of 45** specialist silences at required-gold sites are identical every time ($1.97). Step 0 — free — then labelled all **58** silent gold-site sessions against the ask each was silent about, with an adversarial second reader: **37** are an arm correctly quiet about somebody else's concern, **17** are the right arm declining on stated grounds, and the three mechanisms the interventions were costed against total **four sessions** — advisory-suppressed **0**, cross-unit **0**, `naming_norm` evidence gaps **2**, compiling-edit-rule **1** (one session, one PR). Nothing was spent; the conditions are built and priced if the population ever justifies them. Residue: judgement, not plumbing. | closed, $0 |
| ~~[The publication rule](publication-rule.md)~~ *(written and **parked** 2026-09-22: it is selection, and the generator comes first)* | The admission gate discards **71-83%** of the gold obligations the run already found -- 7/5/6 hit, **2/1/1** published over three held-out reps -- because it filters on whether a collector can warrant the claim's *family*, not on whether the claim is right. 21 of rep1's 24 suppressed hit-findings say exactly that. The families that hit are not the families that publish (`correctness` 161/39/**2**, `naming` 66/10/**0** against `generalization` 15/**0**/6), and the generalist holds **64 of 71** hits at 2.8% publication. All 12 control findings are `documentation` and `style`, the two families that never hit, so a leave-one-PR-out family rule takes obligations published **2 -> 6 of 7** with control emission still **0**. | measured free; change is code + 1 rep |
| [Routing: remit and silence](routing-remit-and-silence.md) *(new 2026-09-21)* | The agenda sent an arm whose remit covers the ask to **22 of 22** counted gold obligations -- and four or five whose remit does not. Of **76** silent cells at gold sites, **13** are an arm declining inside its own remit and **53** are an arm correctly quiet about somebody else's concern; 9 of 20 obligations with a silence have no on-concern arm among the silent ones at all. So "41 of 45 silences reproduce" is mostly a fact about which arms were asked, not about arms withholding. The off-concern silent jobs billed $1.93 against $0.39 -- the price of the breadth, not a waste figure, because nothing yet values what those jobs filed elsewhere. | free to measure |
| [Stage chaining](pipeline-stage-chaining.md) *(new 2026-09-21)* | A v5 experiment is four processes chained by a hand-typed run name, and `judge --of` exists because three free-form paths once scored **rep1's findings under rep2's name**. Replay is the third stage to re-implement "find the previous stage's artifacts": selecting its 45 diagnostic sessions took an untested scratch join across four files. Same defect one level down, measured this week: task-data keys were **dropped between orchestrator and worker**, so `execution_limits` never bound (arms ran at $1.00, not $0.30) and a replay silently ran as a fresh task. | code |
| [Decision-turn replay](replay-decision-turn.md) *(built; diagnostic run 2026-09-21, one condition left)* | Forcing only the submit decision took issue recall **0.20 → 0.50** on identical PRs, and abstaining arms investigate as much as filing ones (**median 6.0 vs 7.0** tool calls) — yet every decision-stage change is tested with a full **$7.26 / ~38 min** rep that re-samples the investigation too. Resume each recorded session at its `submit_candidates` turn with one thing swapped. OCR settled its filter fix this way: 455 recorded calls replayed, precision **36% → 88%**. | code + replay turns |
| [Work-unit batching](batching-work-units.md) *(grouping landed and measured; authority, `patch_set` open)* | PR 33145's six-theorem family is split across 4 work units by a **sha256 sort and a double-counted 24,000-char budget** — the packer charges one 5,196-char hunk 12 times when the renderer prints it once. Repacking on real content: **203 units → 92**. 41 of 62 families span >1 unit; 22 of 32 required family-grain jobs hold part of their family. `patch_set` has never been submitted in **1,660 recorded candidates** and would raise TypeError on first use. | code + 1 rerun |
| [Specialist arm contents](specialist-arm-contents.md) | **Seven** of ten specialists match nothing, for three different reasons — `style` 126 findings / 0 published / 0 matches; `family_design` 26 invocations / 0 candidates; `api_reuse` 107 proposals / **0 mandatory rows** / 0 invocations. `naming_norm`'s `established` bar needs ratio ≥ 0.80 while 33337's gold prefix is **21 of 121**. `docs` is told a linter settles a check that is not in the toolset. | mostly re-scoring |
| ~~[Lead prompt cost](lead-prompt-cost.md)~~ *(closed 2026-09-15)* | `### Exact changed fragments` is **43.6%** of rendered prompt characters and **61.8%** of prompt spend, and **95.5% of it is a verbatim re-send**. PR 33149 is **48% of the run's billed cost**: one 17,303-char hunk shipped to 120 jobs that each review one 163-char declaration. Target-scoping it removes 89.9% of the section and **16% of lead spend**. | code + 1 rep |
| [The judge and the denominators](judge-and-measurement.md) | The judge has only ever paired at `anchor` — **705 of 705 pairs, no other tier ever emitted** — so an ask anchored one change away is never shown to it. The active v9 rubric splits its own vote on **76 of 705** pairs, against a v8 result of 0/18 that does not carry forward. PR 33149 is **68.9%** of condition A's findings. | no spend |
| [Evidence tiers and traces](evidence-tiers-and-traces.md) | `repository_measurement` is declared in the schema and **produced by no v5 code path**, so "27 of 27 lemmas use this prefix" serialises exactly like a guess. Two collectors can only ever return `inconclusive`. `proof_profile` writes **no trace row at all** while gating condition C's leak audit. | no spend |
| [Selection signal](selection-signal.md) | **Refuted in its absolute form**, which is what the 2026-09-14 plan proposed: at 10× the data — 907 candidates, 71 hit-candidates — within-PR AUC is **0.486 / 0.485 / 0.516**. The forced-run frontier is one PR (drop 33145 → AUC 0.511). Kept because the **relative within-PR** form is recorded as working and was never tested here. **New 2026-09-15:** cross-rep agreement separates within PR — findings in both other reps hit at **0.70 / 0.29** vs **0.18 / 0.07** in neither (33149 excluded), AUC **0.71 / 0.63**; few obligations, in-sample. | no spend |
| [Pipeline streaming](pipeline-streaming.md) *(added 2026-09-21)* | `cli pipeline` starts a downstream stage when the one it reads has **closed**, because `finalize` writes one `findings.jsonl` for the whole run -- there is no moment when one PR's findings exist and another's do not. A rep is **~38 min** of which **9.5 min is finalization after the last arm line prints**, and one PR (33149) is **48% of billed cost**, so judging the other eleven early would overlap most of the judge with most of the run. The judge's resume is a content hash, so the final aggregate would be free. | code |
| [Adjudication rubric](adjudication-rubric.md) *(added 2026-09-21)* | The socket is built and empty: `cli adjudicate` keys **259 unadjudicated findings over 214 keys** on one held-out rep and carries labels across runs, but nothing labels them. The hard part is the rubric -- `valid_not_an_ask` is the verdict a correct/wrong split destroys, and Atlassian's result says truth is not the question: a factual-grounding judge did almost nothing there while a value gate moved **15-20pp**. | ~30 human labels + one cheap run |
| [Parked corpora](parked-corpora.md) | A **30,297-row** A→B ledger whose only importer is a test, with a clean `grind` curve countable in it. The Zulip benchmark's 45% unresolved rate is **exhaustively** two build parameters. The precedent gate's 49%/56% was measured on embeddings the bench builds itself, **never on the shipped index**. | no spend |
| [Record corrections](record-corrections.md) | Three `dead-ends.md` clauses assert mechanisms the artifacts contradict — including the 33145 decline, where `naming` **did** run at the gold site and filed both renames. Every conclusion survives; the causes do not. | no spend |
| [Framework defects](framework-defects-2026-09.md) *(added 2026-09-21)* | Four defects in `src/ape/` found while adopting the subtask contract, each beside code that was being changed anyway. `judge_mode` has **never** reached either nested judge — it is set as `task_config` on the scaffold config and `create_task_from_data` reads only `task_config_overrides`, so both judges have always run on their defaults. `theorem_proving` omits a **required** result field, so every termination raises inside a `try` that logs a warning. `TaskOutcome.resumable` is computed against the orchestrator's cap, not the child's own. And a task whose samples all failed is written a synthesised result, against the plan rule that says never to. | no spend |
| [Operational floor](operational-floor.md) | An **aborted** fanout run sits untracked under a resumable name with a sealed plan — a resume would seal onto a retired design at ~$111. The acceptance report fails on **one unexplained row**. `cli trajectory` returns **0 arm invocations** for all three `rel050` reps: the index holds absolute paths into a deleted worktree. | no spend |
| [Wall clock — the whole run process](wall-clock-arm-runtime.md) | A run is **~38 min** but `run_manifest.json` records **27.1** — it times the orchestrator only, missing **89 s** of agenda build and **9.5 min** of finalization that runs *after* the last line prints. The same full-tree Python scan is written **twice in two modules**: `content_search` (**26–30%** of arm time) and `repository_search` (dominates the tail), at **32.7 s / 5.4 s** where `grep` takes **0.28 s**. Startup is **97% `exposure._scan`**, run **14×** at 8.5 s, **12.3 M `json.loads`**, on immutable snapshots it never caches to disk. The evidence chain is a **serial loop over 268 candidates** on 64 cores. Concurrency can't be raised first: `content_search` throughput is **flat 0.39→0.69/s**, degrading **2.7 s → 25.0 s** from 6 to 16 arms. *Correction: `record_turn` is **7%**, not the 21% first claimed — median write 0.0 s; the 68% byte amplification is real but third-order.* | code + 1 rep |
| [Billed as the only spend number](cost-accounting-billed-only.md) | Across 52 v5 manifests the field named `total_cost` sums to **$283.53** against a true billed **$84.23**, at a per-run ratio of **2.06×–3.38×** — so **69 of 820 run pairs (8.4%) are ordered differently by nominal than by billed**. Nominal is still what the live progress line labels `Cost:`, what `Already spent:` prints beside a billed cap, and what reaches `report["cost"]` and `score["cost"]`. | no spend |

### Reading order

The four no-spend measurement items — judge pairing tier, judge noise, the 33149 denominator, and
the evidence tiers — change what every recall number in the record *means*, and all four are cheaper
than any run. Anything scheduled before they land will be read against denominators that are known
to be wrong in a known direction.

[Billed as the only spend number](cost-accounting-billed-only.md) is the same argument on the cost
axis: until it lands, a cost figure in the record does not say which currency it is in, and the two
currencies do not even rank the same runs in the same order.

### Added 2026-09-15, from the batching comparison

- **Adjudicating findings that are not maintainer obligations.** ~90% of what the system emits is
  off-gold, and gold is a lower bound, so `gold_alignment_rate` is not precision and nothing in the
  evaluation says whether those findings are useful or noise. *Motivating result:* the batching
  comparison moved alignment 0.069–0.091 → 0.181–0.202 and control emission 2/3/4 → 0/0/1, and
  neither can be read as better output. This is now the largest gap in the evaluation.
  *Design precedent (2026-09-15):* AACR-Bench labels model-found comments correct **and incorrect**
  (1,505 / 640) and folds them into gold; a stable finding key lets one label serve every rep that
  reproduces it. See `docs/research/open-code-review-comparison-2026-09.md` §1.
- **Per-target attention under consolidated units.** Packing 203 work units into 92 cut generalist
  candidates per target from **0.494 to 0.154**; the generalist emits a roughly constant number per
  *job*, not per target. *Motivating result:* 33321's docstring had a dedicated job in 0.3.0 and
  caught the typo; in 0.5.0 it is one of ten-plus targets and the job filed about a different
  declaration. Untried: a cap on targets per unit, or telling the generalist its target count, or
  requiring a per-target disposition (candidate or abstention label per `change_id`) in
  `submit_candidates` — OCR's "every file reviewed or skipped with a reason".

### Added 2026-09-15, from the open-code-review comparison

`docs/research/open-code-review-comparison-2026-09.md` has the mechanism and risk for each.

- **Replay the decision turn, not the job** — promoted to its own entry,
  [replay-decision-turn.md](replay-decision-turn.md). Enables the field-order item below.

- **Reason fields before verdict fields in tool schemas.** *Motivating result:* under
  `forbid_abstention`, `already_correct` labelled suppressed candidates aligning with gold at the
  kept rate (0.038 vs 0.041), and `model_confidence` — the last field — was null on every forced
  finding; `abstention_reason` is emitted before `abstention_detail`. OCR found by session replay
  that an id field ahead of its analysis field could not be retracted. One arm on `bench`, 3 reps.
  **Contested:** ByteDance's BitsAI-CR measured the opposite for its filter — conclusion-first
  77.1% vs reasoning-first 65.8% precision (fine-tuned model, first-token scoring). Test both orders.
- **"Was it acted on" to order the adjudication queue — never to score.** *Motivating result:*
  Atlassian's reviewer matches a human comment only 4% of the time yet 38.7% of its comments are
  resolved, so alignment understates usefulness ~10×; our off-gold ~90% is unadjudicated. Mark
  findings whose target changed the way they ask between reviewed and merged head, and label those
  first. Bounded by `dead-ends.md`'s Δ entry ("never as ground truth").
- **Verbatim-quote anchoring, re-filed deterministically.** *Motivating result:* 705 of 705 judge
  pairs are at `anchor`, so an ask one change away is never judged. An optional `quoted_code`
  resolved against every PR fragment gives a gold-free `resolved_change_id`. No spend to measure
  how many existing candidates would move, if arms are asked to quote.
- **`plan` writes the dispatch pool to scratch.** *Motivating result:* the `naming_norm` run
  ($1.11, 33337 rep14) lost to a tool that never reached the arm, which `plan` cannot show.
