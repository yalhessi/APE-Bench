# Selection, not coverage — what the September runs did to the talk, and what to do next

Written 2026-09-14, after `5537128` (fanout), `fe7a8a7` (`forbid_abstention`), `9a8479f` (forced
results). It reviews `docs/ai4math-convening.md` against the evidence now on the record and names
what to retire, what to promote, and what to run. Cost estimates are billed spend.

---

## The one-line change

The talk is organised around **coverage** — enumerate the units, route a question to each, and the
findings follow (Parts III and VI). Three runs in the last week say the binding constraint is not
coverage. The arms reach the right code and hold the right answer, and the system does not submit
it. The talk's own §18 (`grind`: the model wrote the maintainer's proof, watched it compile, and
submitted something else) was presented as one narrow case in Part V. It is the mechanism, and it
now has company.

| | lead | fanout | fanout **forced** | solo |
|---|---:|---:|---:|---:|
| issue recall (4 PRs, 10 obligations) | 0.20 | 0.20 | **0.50** | 0.40 |
| location recall | — | 0.80 | **1.00** | 1.00 |
| candidates | ~ | 49 | 179 | ~ |
| specialist submit rate | 19% | 16% | 88% | — |
| control-PR (33315) findings | 3–5/rep | 1 | 36 | 0 |

Unlimited slots moved nothing (16% vs 19% submit). Removing the *right to stay silent* moved recall
2 → 5 hits, strictly dominating (3 forced-only, 0 unforced-only). The candidates the bar had been
suppressing align with gold at the **same rate** as the ones it kept (0.038 vs 0.041) — a volume
filter, not a quality filter.

---

## Retire or demote

1. **Scheduling as the coverage lever.** `routing_mode: fanout` tested the "specialists as the
   floor" design at its ceiling and it tied `lead` and lost to `solo` at 2×/job. Entry in
   `docs/dead-ends.md`. Part III currently spends its longest stretch presenting enumeration +
   routing as *the* response to Hypothesis 1; it should present it as a hypothesis that was built,
   measured, and falsified, with the cost of finding that out. Relation-based assignment grain
   (§9, §19) drops from "lands next" to "revisit only if the composition problem below turns out
   to be a grain problem."

2. **The abstention bar as a quality gate.** `already_correct` was the label on good and bad
   candidates alike. Any design that tries to make the arm's own bar smarter is working on the
   wrong end of the pipeline. Move the decision downstream.

3. **Ten single-concern specialists as the product.** Six specialist types matched nothing across
   three reps (§16); at gold sites the declines are *the right arm was never asked* (33145 wanted a
   rename; duplication/api_reuse/style were present and each correctly silent), *an evidence bar
   refused a correct instinct* (33337), and *the arm lacked knowledge* (33117, `@[to_fun]`).
   Maintainer asks are cross-concern; arms are single-concern; nothing composes the slices. Adding
   arms is not the move — composition and selection are.

4. **Keeping coordinator synthesis / dedup / publication switched off.** §19 defends this as
   deliberate ("each can discard a correct finding, measure the cost first"). The forced run makes
   the *absence* of downstream selection the thing blocking the result: 179 candidates for 5 hits,
   36 of them on a PR nobody asked anything about. Turning them on one at a time with the recall
   cost measured is no longer scheduled work; it is the next work.

5. **`model_confidence` as a falsified signal.** `merge.py:256` and `digest.py:145` both refuse it
   on three v4-era falsifications. It is nonetheless collected. See the next section — this is now
   a live question, not a closed one.

### Stale statuses in §19, to correct before the talk is given

- **Atomic coordinated patch sets** — listed as "contract drafted". Built: `registry.patch_set`,
  `family_design` carries it, `PatchEditSubmission` and `_verify_patch_set` verify all touched
  files together, refused by default for every other arm.
- **The compile-claim defect** — §11 and §13 describe the claim-to-warrant join as the open
  problem. The larger part of that story closed on 2026-09-12: reviewed workspaces
  (`docs/research/reviewed-workspaces.md`) removed the stale-sibling `Unknown constant` cascade
  that produced 16 phantom `broken_build` findings, 4 of them published. The held-out rerun that
  confirms those 16 vanish across the set is still outstanding.
- **`rejected_alternatives`** — exists in the schema and in the prompts, written to
  `arm_responses.jsonl`, and *dropped* at the candidates boundary (see below).

---

## Promote

1. **Selection over discovery becomes the spine.** §18 is no longer one PR. Forced, `naming` asked
   for `Dense.upperBounds_image` — character for character the rename gold wanted, on an obligation
   it had abstained on; `duplication` proposed the OrderDual reuse; `correctness`, pressed outside
   its own concern on 33421, landed on a real naming obligation. "The system had the answer and did
   not submit it" is the throughline, and it is the sharpest thing this project has to say:
   *verifiable correctness is not enough, and neither is discovery.*

2. **The control PR is the scoreboard, not a footnote.** §3 calls 33304/33315 "no-request cases,
   not adjudicated negative controls". Every recall number from here on has to be read against
   control emission: forced is ~12 spurious control findings per real obligation recovered. Report
   the pair everywhere.

3. **Calibration** (`PROJECT-STATUS.md` §11, "move the flag/no-flag threshold to the maintainer's,
   *during* review rather than as a wasteful post-filter") moves from planned-not-started to the
   main line. It is the item the newest evidence nominates by name.

4. **The convention brief's purpose shifts.** §20 argues briefs are how the reviewer *learns* what
   the community prefers now. 33337 says something narrower and better attested: `naming` already
   considered the exact rename and `naming_norm` returned `insufficient_evidence`, and no condition
   in any run ever hit that obligation. The brief is not there to supply the idea; it is there to
   supply the **warrant that lets a correct idea clear the bar**. That also closes §13's missing
   `repository_measurement` tier. Same work, a more defensible claim.

5. **The 12-PR set is burned, and a fresh window is now collectable.** §15 already says the set is a
   development set from here. The uncommitted PR-store work extends the store to 2026-08-31 with
   Dec 2025–Jan 2026 read at tier 2 (1,399 PRs, 2,863 compares) — so "a fresh held-out window, used
   once" has an input for the first time. `acceptance_report.json` currently says `passed: false`.

---

## The plan

### Step 0 — land what is on the floor · no spend

Nine uncommitted files spanning two threads. Commit the PR-store extension by explicit path, and
resolve `acceptance_report.json` `passed: false`: 441 `association_changed_upstream` and **1
`unexplained`** shared-row mismatch, plus one field mismatch on comment 2203417174 (`line`,
`commit_id`). One unexplained row is either a collector bug or an upstream edit; it has to be named
before the store backs a held-out window. The `pr5_F_fanout_heldout12_v2_rep1` tree is plan-only
(agenda + run_plan, no tasks) — commit it as a preflight artifact or delete it, but do not leave a
half-named run directory where a resume can find it.

### Step 1 — stop dropping the two fields that answer the question · no spend

`model_confidence` is written by every arm, survives to `candidates_discovered.jsonl` (179/179
floats, spread 0.22–0.90), and is **absent** from `findings.jsonl` and `issues.jsonl`.
`rejected_alternatives` is written to `arm_responses.jsonl` and dropped at `candidates.py:374`,
which reads `model_confidence` and not it. That makes 9a8479f's "`model_confidence` is null on
every forced finding" true at the layer it was read and wrong about the pipeline: the signal is
captured and then thrown away.

This is the **fifth** instance of this repo's most expensive bug — `documentation`/`docs`,
the retrieval-gate `Literal`, `CONTEXT_TOOLS`/`naming_norm`, `result_content`/`content`. Carry both
fields through candidates → findings → issues, surface them in `report`, and pin the hop with a
test in the style of `fe7a8a7`'s.

Keep the refusal in `merge.py` and `digest.py` — *ranking* the published text by confidence is
still falsified. Carrying the number is not ranking by it.

### Step 2 — measure the selection frontier on runs already paid for · no spend

Join confidence to gold alignment across every recorded run, not just the forced one. On
`pr5_F_fanout_forced_stage1_rep1` (join by `(pr_number, claim)`, 179/179 matched):

| threshold | candidates kept | gold hits | control 33315 |
|---|---:|---:|---:|
| none | 179 | 7 | 36 |
| ≥ 0.4 | 89 | 5 | 9 |
| ≥ 0.6 | 67 | 5 | 3 |
| ≥ 0.8 | 14 | 3 | 1 |

Six of the seven aligned findings sit at or above the median (0.38). A 0.6 cut keeps forced recall
at 5 hits — still 2.5× unforced — and takes control emission 36 → 3, against unforced's 1.

**This threshold is fitted post hoc on seven hits from one repetition of four PRs, and is not a
result.** It is the reason to run Step 3 rather than a substitute for it. The deliverable of Step 2
is the frontier plot across all runs and an answer to one question: does a monotone relationship
between confidence and gold alignment survive outside the run the cut was chosen on?

### Step 3 — forced + gated, out of sample · ~$35–60

If Step 2 shows separation: freeze the threshold from the 4-PR runs, then run `forbid_abstention`
with the gate on PRs it was **not** fitted on — the remaining eight held-out PRs, one rep, plus one
rep at the same setting on the original four for a paired read. Endpoints, both reported: issue
recall, and control emission per real obligation recovered. Three reps only if rep 1 clears the
unforced baseline; single-run deltas at this n are noise and this project has retracted conclusions
for less.

If Step 2 shows no separation outside the fitted run, do not run this. Go to Step 4 and record the
negative in `dead-ends.md` with the untried designs enumerated: an evidence-tier prior instead of a
self-report, a cross-arm agreement count, a per-concern threshold, an LLM selector reading the
candidate against the control.

### Step 4 — give the naming bar something to clear · ~$15 + build

33337 is the best-attested blocked hit in the corpus: the arm had the exact rename, `naming_norm`
said `insufficient_evidence`, and no condition ever recovered it. Two changes, in order:

1. Promote a population count into `repository_measurement` so the count the arm already retrieves
   serialises as a warrant rather than a `model_assertion` (this is §13's missing tier and §20's
   first deliverable, and it is the same code path).
2. Make `naming_norm`'s `insufficient_evidence` a *reportable* outcome rather than a silent veto —
   the arm should be able to submit with the weakness stated, which is exactly what
   `forbid_abstention` demonstrated it can do.

Then re-run 33337 alone, three reps, against its 10 existing reps. That obligation has never been
hit; hitting it is a clean, cheap signal.

### Step 5 — the composition problem · design only, this month

Maintainer asks are cross-concern and arms are single-concern. `patch_set` is built and
`family_design` holds it, but nothing merges two arms' slices of one ask into one submission. Write
the design against the three 33145-style cases before writing code — and check it against the
retracted conclusion *"arms are competent locally but structurally cannot reach design"*, which the
record does **not** support.

### Step 6 — the fresh window, used once · deferred until 1–5 land

Requires Step 0's gold audit, a frozen selection gate, and a stated stopping point. Not before.

---

## What would falsify the reframe

- Confidence separation does not survive outside the fitted run → selection is still the lever, but
  self-report is not the signal; Step 3 becomes an LLM-selector question.
- The forced-only hits turn out to be judge noise at n=7 → the whole forced result is one rep and
  the judge splits its own vote on ~11% of pairs; a second rep of the *unforced* config is the
  cheap control, and it should be run before Step 3 if Step 2 is equivocal.
- A gated forced run beats neither `solo` recall nor `solo` control burden → the scaffold's case
  rests on repeatability alone (§15: 5 same-issue and 3 strict-fix matches in all three reps,
  against 0 for solo), and the talk should say so plainly.
