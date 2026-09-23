# Plan — enumerate the work maintainers do, and measure the ceiling of doing all of it

*Written 2026-09-23 in the worktree `work-enumeration`, after the user asked to step back from the
abstention thread: specialists map poorly onto maintainer work, the generalist is queued first and the
specialists fitted around it, and review should be iterative. Approved as written below; the
corrections section at the foot was added after approval, from an exploration that reported late.*

Thread: **work-enumeration**. Scope agreed 2026-09-23: enumeration + unbudgeted ceiling in this
thread; the belief-updating scheduler is designed here on paper and built in the next thread only if
the ceiling is high. The enumeration is derived from the PR store **outside** the evaluation PRs; the
generalist is **not** in the ceiling condition (existing solo / lead runs are the baselines);
**≤ $25 per gpt_5.2 rep** of the ceiling, which forces question-batched jobs.

## Context

The system's useful output comes from the generalist: 64 of 71 held-out hits, 1,168 findings / 168
matches against the ten specialists' 434 / 25. `solo` (one generalist, no lead) reaches issue
recall 0.40 on the 4-PR set where `lead` and `fanout` reach 0.20. Forcing the specialists to return
something (`forbid_abstention`) took the same arms to 0.50 — three of the five forced-only hits from
`naming`, which files nothing unforced. So the specialists are not short of judgement; they are
aimed at the wrong questions, allowed to stay silent, and scheduled as a remainder around a
mandatory generalist wave.

And the failure is *what is asked*, not *where the system looks*: on the held-out 12
(`3a3bf72`, three reps each of lead and solo), **91% of obligations are located and 57% correctly
asked**; of the 10 obligations nothing hit, **8 were located and wrongly asked**, 2 never located.
Solo owns naming, scope and generalization — judgements that need the whole file — while lead owns
what a specialist can warrant by compiling. A design that asks each maintainer question at every
place it applies is aimed at exactly that gap.

The last session worked the abstention *mechanisms* one arm at a time (labels, replays, the advisory
contract) and did not change what the system asks. This plan steps back to the user's framing:

1. The specialists do not map onto maintainer work. → Derive the work from what maintainers ask.
2. Allocation is "generalist first, specialists in the remainder". → One queue of questions.
3. Review should be iterative: verdicts update beliefs and queue deeper questions. → Designed
   here, built only after (1) and (2) show the question set can reach the asks at all.

The load-bearing hypothesis is the user's: **if we enumerate all the work involved in reviewing and
do all of it, ignoring budget, we recall most issues.** This thread tests exactly that, on data the
enumeration was not fit to.

## What the record already settles, and where this plan sits against it

- **`dead-ends.md`, "Specialists as the coverage floor" (fanout).** Superficially the same
  experiment. It ran the *current ten arms* with abstention allowed: 2 of 10 obligations, submit rate
  16%. Its reopen condition is *"the reason arms decline changes"*. This plan changes both what is
  asked (a question list derived from maintainer comments, not ten concern briefs) and whether an arm
  may decline (every question returns a verdict per target — forcing, made structural). The forced
  twin of that run (0.50) is the direct comparison.
- **"Community-guidelines injection, statute".** Null at N=115: rules appended to one reviewer's
  prompt. Different mechanism from one forced-verdict job per question; the ceiling tests attention
  allocation, not prompt content. Say so in the write-up.
- **"Facet-keyed review join".** Facets fit 4–8% of asks; *reviewers ask about a pattern in the code,
  not the declaration's shape.* The enumeration is keyed by the **question** and its applicability
  predicate over code patterns, never by declaration-shape facets.
- **"Oracle-site instantiate pipeline".** Worklists built from gold shrank the search toward gold and
  made every number an oracle diagnostic. Hence the corpus source and a gold-independence test on the
  enumeration (below).
- **"Selection from artifact-only signals" / "Publication as selection" / rule in
  `.claude/rules/mathlib-review.md`.** Nothing here changes what is published. All recall is reported
  as the pair *found (pre-gate) / published*, with control emission beside it. The *budgeted*
  scheduler (next thread) needs a prior over "which (question, target) needs scrutiny", and a prior
  from artifacts alone is exactly the selector that measured at chance; the design below therefore
  drives priority from **returned verdicts**, not from artifact features — and says so.
- **`docs/todo/specialist-arm-contents.md`, `routing-remit-and-silence.md`,
  `specialist-abstention-interventions.md`.** Their measured defects (naming_norm prefix-only,
  api_reuse never runs, golf/idiom overlap, style asks the wrong thing, family_design files nothing,
  37 of 58 gold-site silences off-remit) are *symptoms* this plan addresses at the root. Each gets a
  pointer to this thread rather than being worked arm by arm.
- **D1 in `pr-review-v5-principled-design.md`** (route by problem class: convention / repository /
  judgment) — the one prior re-decomposition, never built, and three classes is coarser than the
  work maintainers do. Cited as precedent, not adopted.

## The design

### A review question is the unit of work, not a concern brief

An **enumerated question** is one thing a maintainer checks, stated generically enough to apply to
any PR and specifically enough that a verdict is decidable — e.g. *"Does an existing declaration
already state this, or something it follows from in one step?"*, *"Does this name follow the naming
convention for its subject and head symbol — prefix, suffix, and namespace/dot-notation?"*, *"Is a
hypothesis unused, or a typeclass stronger than the proof needs?"*. Each entry carries:

| field | what it is |
|---|---|
| `question_id`, `text` | the generic question; the prompt renders it verbatim |
| `applies_to` | a **deterministic** predicate over the agenda's change graph (added/modified decl, decl kind, proof present, file-level, PR-level, name/attribute patterns) — never a gold field |
| `grain` | declaration / family (siblings) / file / PR — so a file-level defect has a legal anchor |
| `evidence` | which tool answers the question, as guidance rendered into the prompt — **not** a grant: every `q:*` arm holds the generalist's full grant (`arms.py:201-231`), because the ceiling must not starve a question of a tool (the `docs` arm told a linter settles a check it cannot run; `family_design` without `declaration_search`), and one grant is one place for the closed-vocabulary trap to bite instead of forty |
| `provenance` | corpus support: n comments, example `comment_id`s, date range — all pre-cutoff, none from a scored PR |
| `concern_family`, `issue_kind` | drawn from the existing closed `Literal`s in `CandidateSubmission` (`candidates.py:132-150`) so finalize, the gate and the judge need no change; never a new spelling (`documentation`/`docs` is the precedent) |

The list lives as **data** — `inputs/review_questions/<version>/questions.json` plus its build
manifest (not under a frozen root). Each entry registers as its own arm id `q:<question_id>`,
expanded from the list by **one** function beside `ARM_DEFINITIONS` in
`src/mathlib_review/agenda/registry.py`, with **one** shared prompt template in
`src/ape/tasks/lean_tasks/formal_math/review/focused_prompts.py` that renders the question text. It
has to be one arm id per question because invocation ids are `wu:<unit>#<arm>` (`agenda.py`), so one
parameterised arm would collide across questions. It also means per-arm reports, benches,
`arm_sha256_by_id` and prompt hashes all become per-question for free. The rule "adding an arm is
exactly two edits" becomes "adding a question is one list entry"; that change goes into
`.claude/rules/mathlib-review.md` in the same commit.

`applies_to` extends the mechanism that already exists — `FocusedAgentSpec.applies_to` and
`schedule_focused` (`src/mathlib_review/agenda/focused_specs.py:64-74, 226-279`), with lifecycle and
subject-kind filters in `arms.py:89` — rather than a second predicate language. Grains beyond the
current file-confined work unit (family, file, PR) come from the components that already exist in
`src/mathlib_review/agenda/components.py:266-390`.

### Every target gets a verdict — forcing, made structural

A question job returns one disposition **per applicable target**: `issue` (the ask, optional fix,
`severity: blocking|advisory`), `no_issue` (with the reason and what was checked), or
`cannot_determine` (with what evidence was missing). There is no empty submission. This is the
per-target disposition already in `docs/todo/README.md` ("OCR's *every file reviewed or skipped
with a reason*"), and it keeps what forcing bought (the arm must answer the question it was given)
without forcing a finding — `no_issue` is a legal verdict, which is what should keep the control PR
from going 1 → 36. The `no_issue` / `cannot_determine` rows are also the belief state the next
thread's scheduler consumes; today `abstention_detail` is read by nothing.

### The question template: two rules

- **No exclusion list and no licence for silence.** Today's briefs open "That is your only job —
  ignore proof length, generality, …" and close "a naming check that finds nothing is a normal and
  correct outcome" (`focused_prompts.py:344-378`) — the restraint that forcing removed, and the one
  Bugbot reports had to be replaced by "aggressive" prompts. The template states the question, lists
  the targets, and asks for a verdict on each; the per-target schema, not prose, is what keeps it
  honest.
- **No corpus examples in the prompt.** The comments that motivated a question stay in its
  `provenance`, for the user's read. Showing them to the arm is precedent priming, which
  `dead-ends.md` ("Precedent priming, Mode A") measured as delivered but not transferred, and it
  would add a second variable to the ceiling.

### The ceiling condition

All (question, unit) pairs whose `applies_to` selects at least one target, batched so **one job
answers one question over all its applicable targets in a unit**. It is `routing_mode: fanout`
(`agenda.py:435`, the whole pool, no lead) with `generalist_floor: false` and only `q:*` arms in the
pool — **no new routing mode**, since `routing_mode` is a closed `Literal` in three places in
`src/mathlib_review/schema/review.py`. No lead, no pruning, no generalist, no mandatory first wave.
Same PRs as `pr5_F_fanout_stage1_rep1` and its forced twin so the comparison is direct; `solo` and
`lead` on the same PRs are the other baselines.

The ceiling sets `submission_verification_policy: verify_edits_if_present` (`7eef7af`). Otherwise
`candidates.py:420-424` refuses any `issue` in a checkable family (correctness, proof-golf,
duplication, generalization) that has no compiling edit. That rule was the largest in-remit
blocker in the silence read, and it would silence the 33149 Parseval ask again. Edits that are
supplied are still compiled; an ask without one lands as `diagnostic`, and found recall counts it.

`generalist_floor: false` refuses a run in which any unit has no eligible arm
(`runner.py:763-791`). A unit no question applies to is an **enumeration gap** — a result, not an
error — so `plan` lists such units, and the refusal is satisfied by an explicit allow-list sealed
into the run plan rather than weakened. Their count is reported beside recall.

**The $25 billed cap has to bind, not be estimated.** In `fanout`, `per_pr_cost_cap` and
`max_delegations` are not enforced and `run_total_cost_cap` is a *preflight* check that prices the
pool at `cost_hint` $0.05/job while each job actually runs under `standard_budget_cap` ($0.30)
(`runner.py:968-1044, 1487`). Fanout billed **$0.029/job** ($5.07 / 173), so $25 is ~850 jobs
expected — but the worst case is jobs × per-job cap. Phase 2 makes the existing preflight honest
for arm modes: `runner.py`'s budget check (`:985-1044`, which already refuses with `BudgetTooSmall`
under `enforce`) prices a `fanout`/`rules` pool as **jobs × the per-job `billed_cost_limit`** and
its token twin. One check, the existing one — not a second limiter. The per-job cap is set at
≥ 2× the median job's measured cost (tokens from the Qwen shakeout, converted at the calibrated
1.2M processed tokens per billed dollar) so ordinary jobs do not pause; if jobs × that cap exceeds
$25, batching coarsens (question × file instead of question × unit), and only then are the
lowest-support questions dropped — each drop listed in the run plan. The cap is never raised
without asking. Rough size: the four PRs (33145, 33315 control, 33337, 33421) are **33 work units
/ 81 targets** in the fanout agenda; ~40 questions at ~40% applicability is ~530 question × unit
jobs, ~$42 worst case at a $0.08 cap — so expect question × file batching (~240 jobs, ~$19 worst
case, ~$7 expected at fanout's $0.029/job).

### Why the ceiling comes before the scheduler

With every (question, target) verdict recorded, a budgeted policy is a *subset and an order* over
jobs that already ran independently. Recall-at-budget for any priority rule can be computed
**offline, for nothing**, from the ceiling's artifacts — so the ceiling run is also the simulator for
problem 3. What it cannot price is follow-up questions (they are not in the ceiling), which is what
the next thread builds.

## Phases

Each phase ends in a commit on the topic branch; free phases gate paid ones, and every gate is
written into the plan copy in `docs/plans/` **before** the phase it gates runs.

### Phase 0 — worktree, and the two free reads that size problem 1 (no spend)

Other sessions share the main tree, so first:
`git worktree add -b work-enumeration .claude/worktrees/work-enumeration develop && .claude/worktree-setup.sh .claude/worktrees/work-enumeration`,
then `export PYTHONPATH=$PWD/src` in that shell. Copy this plan verbatim to
`docs/plans/2026-09-23-work-enumeration.md` as the first commit.

**0a. What the generalist answers.** For every counted gold obligation hit in the committed
held-out runs (`pr5_A_lead_heldout12_v2_rep{1,2,3}`, `pr5_B_solo_ape_heldout12_v2_rep{1,2,3}`, and
the four-PR `pr5_F_fanout_stage1_rep1` / `pr5_F_fanout_forced_stage1_rep1`), record which arm hit
it and restate the hit as *the question it answered*. Read through `report buckets` and the judge
audits, never by hand-parsing JSONL. The table says whether the generalist's lead is breadth
(it asks questions no brief asks) or something the specialists' framing blocks.

**0b. Do the current briefs ask the maintainer's question?** For each counted obligation, does any
current arm's *brief text* (not its `expected_concerns` label) ask the question gold answers?
Non-exclusive labels, notes read before counts (the 2026-09-23 lesson in
`.claude/rules/mathlib-review.md`). This is the baseline number the enumeration must beat.

### Phase 1 — the enumeration, from the PR store (a few dollars of labelling)

1. **Sample.** Top-level comments from `data/pull_requests/projections/corpus/reviewer_view.jsonl`
   (104,093 rows; scored PRs already excluded by `scored_pr_numbers`), `created_at` before the
   earliest `agenda/cutoffs.py::cutoffs_by_episode` over the evaluation episodes, stratified by
   month and reviewer so a few prolific reviewers do not define the list. ~1,500 to label plus a
   disjoint ~500 held back for saturation. Seeded, written with its manifest. The held-out runs'
   `context_trace.jsonl` shows cutoffs of 2025-12-20 → 2025-12-31; before 2025-12-20 the corpus has
   ~68k reviewer comments (~56k top-level), so the pool is not the constraint. The gate date is
   computed over **every** scored episode in the release, not read off one trace.
2. **Label.** Each comment → {is it a request; the generic question it answers; target grain;
   evidence needed}. A registered non-agentic task on the `judgment.py` pattern (content-hash
   `global_index`, so resume is the cache), run through `TaskOrchestrator`, `gpt_5_mini`. The
   request filter reuses the rubric text of `src/datasets/pr_review_v2/actionability.py`, not its
   hand-rolled cache. The v2 caches (`data/pr_review_v2/cache/concern_classify`, 1,886 single-family
   labels; `ask_distill`, 524 specific asks) are read as a cross-check only: one family per comment
   is the forced-choice vocabulary the 2026-09-23 lesson warns against, and a distilled ask is
   specific to its PR where a question must be generic. Entry point: one new verb on the one
   pipeline CLI, `ape/bin/python -m src.mathlib_review.review.cli questions <sample|label|build>`,
   which spends nothing without `--execute`, requires `--run-name`, and runs the task from its own
   top-level orchestrator the way `src/mathlib_review/judge/runner.py` runs the judgment task
   (the task's docstring calls it `judge_runner.py`, which no longer exists). The task class lives
   under `src/ape/tasks/lean_tasks/formal_math/review/` (a task outside that tree cannot import
   `ape.tasks.base` without a cycle).
3. **Consolidate** the free-text questions into the list (expected 30–60 entries), with the user
   reading the list before it is frozen.
4. **Saturation and coverage.** New-question discovery curve over the labelled sample, and the
   share of the held-back 500 that map to an existing entry. The user's hypothesis needs "all the
   work"; this is the evidence the list is close to all of it.
5. **`applies_to` predicates**, deterministic over the agenda's change graph, with a test that they
   read no gold field (the `test_worklist_gold_independence` pattern).
6. **Gate (free, pre-registered).** The list and its predicates are **frozen, with their digest
   committed, before** gold is looked at; any change after that is a new version, reported as such.
   Then, against counted gold, with the same reader rubric as 0b (model reader plus an adversarial
   second reader, non-exclusive labels): the share of obligations for which an entry asks the
   question *and* its predicate selects the gold target must be ≥ 80% and strictly above 0b's
   current-brief number. Fails → stop, write the dead-end with the untried designs, spend nothing on
   the ceiling.

### Phase 2 — the question arm and the enumerated mode (code, no spend)

Small commits, in this order:

1. **Registry expansion** — the one function that turns `questions.json` into `q:<id>` arm
   definitions beside `ARM_DEFINITIONS` (`src/mathlib_review/agenda/registry.py:130-231`), the shared
   template in `focused_prompts.py`, and the generalist's grant on every `q:*` arm. The question-list
   digest goes into the run plan (a knob that changes what a run does is in the plan).
2. **Applicability and batching** — `applies_to` through `FocusedAgentSpec.applies_to` /
   `schedule_focused`; proposals at the entry's grain, batched per (question, unit) or per
   (question, file) as priced; enumeration gaps listed by `plan` and allow-listed in the seal.
   Work units are file-confined (`schema/identity.py:327-352`) and invocation ids are unit-keyed, so
   a PR-grain question has no unit today. Either a PR-level unit is added through the existing
   unit builder (`src/mathlib_review/release/work_units.py`), or those questions run at file grain
   with the limitation recorded. Decide this when the list shows how many PR-grain questions there
   are, not before.
3. **Per-target verdict** — for `q:*` arms, `submit_candidates` (`candidates.py:596-759`) requires a
   disposition for every applicable `change_id` in the job, reusing the existing press loop
   (`_FORCED_SUBMISSION_ATTEMPTS`, `:53-66`) for a missing one; `issue` rows go through
   `CandidateSubmission` unchanged, `no_issue` / `cannot_determine` rows through one new typed row
   model beside `ArmResponse` in `schema/review.py` (a ledger row has one constructor). Run
   `tests/datasets/test_pr_review_v5_row_models.py` before touching either model.
4. **Finalize** — `issue` verdicts become candidates as today; verdict rows are written to their own
   artifact registered in `run_state.RUN_ARTIFACTS`, so the scheduler thread reads them through
   `StageInput`.
5. **Preflight honesty** — the arm-mode worst case as jobs × per-job cap (see the ceiling section).

Exercise the capability once by hand before any run (the `patch_set` lesson) and assert the grant
reaches the task (`tests/datasets/test_context_tool_grants_survive.py` pattern). Every step keeps
`tests/datasets/test_package_boundaries.py` and `test_pr_review_v4_no_duplicate_helpers.py` at or
below their pinned counts.

### Phase 3 — Qwen shakeout (free, iteration tier; not for the record)

A thin `configs/pr_review_v5_questions_ceiling_qwen.yaml` extending the gpt_5.2 ceiling config
(the `pr_review_v5_smoke4_qwen.yaml` pattern: `elm_qwen_3.5`, `reasoning_effort: none`, the token
block, so the two cannot drift). On one PR, then the four: every applicable target gets a verdict,
tool calls succeed (`repaired_argument_count` watched — `docs/todo/elm-tool-schema-enforcement.md`),
the schema conforms, and measured tokens per job set the gpt_5.2 per-job cap. Then `cli plan` on the
gpt_5.2 config must show ≤ $25 worst case. If it does not, re-batch; the cap is not raised without
asking.

### Phase 4 — the ceiling, gpt_5.2, three reps (≤ $75)

Same four PRs as the fanout pair. Report mean / union / stable over three reps, majority and
unanimous judge rules both, found and published as a pair, control emission (33315) beside it, and
billed cost. Every miss is attributed to one stage, gold-light and in this order: **no entry asks
it** → **predicate missed the target** → **the job answered `no_issue` / `cannot_determine`** (read
the reason) → **judge did not match**. That decomposition is the deliverable as much as the recall
number: it says which layer to fix next.

Outcome bands, fixed now, against the same four PRs' baselines (lead 0.20, fanout 0.20, solo 0.40,
forced fanout 0.50 — the last one unreplicated): mean found recall **≥ 0.6** → the hypothesis holds
at this n, and the scheduler thread starts; **0.4–0.6** → read the miss decomposition before
anything else; **< 0.4** → record the negative with the untried designs enumerated. Ten
obligations: one obligation is 10pp, so no band edge is read off a single rep. **Control guard:**
pre-gate findings on 33315 are read beside recall (lead 3–5/rep, fanout 1, forced 36). A recall
gain that arrives with control emission in forced's range is forcing by another name and does not
by itself support the enumeration hypothesis.

### Phase 5 — the scheduler, on paper and offline (free)

From the ceiling's artifacts, compute recall-vs-jobs curves for candidate orderings — random, corpus
base-rate prior per question, verdict-driven (an `issue` on a target raises its siblings; a
`cannot_determine` re-asks with more evidence), and the oracle order as the upper bound. Then write
`docs/plans/<date>-belief-scheduler.md`: the belief state as the coordinator-owned blackboard that
`coordination.py` already names, the follow-up question graph, and which refused
`CoordinationPolicy` values it implements (`max_rounds > 2`, `parent_view: full`,
`max_redispatches_per_pair`, `sibling_view: blackboard`). The base-rate curve is the
artifact-only-prior dead end measured again on new data and is labelled as such.

## Risks, stated before anything runs

- **Ten obligations.** The four-PR set is small, and a single rep moves recall by 10pp per
  obligation. Three reps and the outcome bands are the defence. The held-out-11 extension is the
  follow-up that would make this a rate.
- **It may be forcing by another name.** A per-target verdict removes silence. If the gain arrives
  with forced-level control emission, the control guard says so, and the enumeration gets no credit.
- **Machine labels define the list.** The question list is built from `gpt_5_mini` labels. The
  user's read before freezing and the saturation curve are the checks on it; the held-back 500 is
  the check on overfitting to the labelled sample.
- **Grain.** Batching one question over many targets is the per-target-attention problem that
  consolidated units already showed (0.494 → 0.154 generalist candidates per target). Requiring a
  verdict on every target is the counter, and verdicts-per-target is reported so that the dilution
  is visible if it happens.
- **Negative results stay provisional.** A miss is attributed by stage before anything is concluded,
  and the untried designs are listed: file grain for the whole-file judgements solo owns, follow-up
  questions, and evidence tools a question needed but did not have.

## Verification

- **Suite green at every commit:** `ape/bin/python -m pytest tests -q -n auto --dist loadfile`
  (targeted files without the xdist flags), and
  `ape/bin/python -m src.mathlib_review.release.verify_frozen verify` prints `ok` — nothing here
  writes under the frozen roots.
- **Gold independence, as tests:** the sample manifest contains no scored PR and no comment dated
  at or after the earliest evaluation cutoff; `applies_to` reads no gold field (pattern of
  `tests/datasets/test_worklist_gold_independence.py`); the `q:*` payloads carry no gold
  (`tests/datasets/test_pr_review_v5_agenda.py::test_the_agenda_mentions_no_gold` covers them once
  they are in the agenda); `tests/datasets/test_pr_review_v5_arm_registry_consistency.py` extended to
  the generated arms.
- **Capability reaches the task, before any spend:** the grant one-liner
  (`ape/bin/python -c "from src.mathlib_review.agenda.arms import _grant_for; print(_grant_for('<arm>'))"`),
  one hand-exercised question job on a real reviewed workspace, and `arm_pool.jsonl`'s
  `task_data` read after the Qwen shakeout.
- **Preflight prices the rep:** `ape/bin/python -m src.mathlib_review.review.cli plan --config <ceiling cfg> --run-name <name>`
  shows ≤ $25 billed per gpt_5.2 rep and a job count; Qwen runs carry the token block.
- **End to end:** `cli run … --execute`, `cli judge --config <judge cfg> --of <run> --execute`,
  `cli report buckets --run <run> --audit` (found / published / control), `cli report routing`
  degenerate check read first.

## Bookkeeping

- **Record corrections found while planning:** `dead-ends.md` "Specialists as the coverage floor"
  says fanout cost "$14.72 billed"; the manifest says **$5.07 billed / $14.72 nominal** (forced twin
  $9.35 / $31.64). Fix in the Phase 0 commit, and add an "Reopened <date>, under its own condition"
  note to that entry pointing here.
- **Todo pointers**, one line each, in the Phase 0 commit: `specialist-abstention-interventions.md`,
  `specialist-arm-contents.md`, `routing-remit-and-silence.md` — this thread addresses their symptoms
  at the root; their free items stay open but are not prerequisites.
- **Hypotheses surfaced and not pursued here** go into `docs/todo/` before the session ends: the
  belief scheduler (with the Phase 5 curves as its motivating result), follow-up question graphs,
  and extending the ceiling to the held-out set without 33149 (`configs/pr_review_v5_heldout11.yaml`,
  ~2× the obligations of the four-PR set; priced by `cli plan`, not assumed to fit $25).
- **Commit at every phase boundary** by explicit path, `<area>: <what, and why it is right>`,
  measurements in the body. Never touch the other sessions' uncommitted files in the main tree.

## Corrections, 2026-09-23 (after approval; the body above is kept verbatim)

From the generalist-vs-specialist exploration, which reported after the plan was approved. Each was
re-derived from committed artifacts by a read-only join that reproduces the spine doc's §5 table.

1. **The four-PR baselines mix a union with means.** `solo`'s 0.40 is the **union of three reps**
   (per rep 1, 3, 0 hits of 10 → mean 0.13); `lead` is 2, 2, 2 → mean 0.20, union 0.20; `fanout`
   (0.20) and `forced` (0.50; 0.30 unanimous) are single reps. Phase 4 compares **mean to mean and
   union to union**: lead 0.20 / 0.20, solo 0.13 / 0.40, fanout 0.20 (n=1), forced 0.50 (n=1). The
   outcome bands stay on the ceiling's mean; its union is reported against solo's 0.40.
2. **The generalist works under a different contract, not only a different remit.** It runs with
   `submission_verification_policy: none` (`schema/identity.py:369-371`, confirmed in
   `arm_pool.jsonl`) and is told to "examine every target across all concern families … there is no
   quota" (`render_prompts.py:13-18`). Specialists run with `verify_checkable_edits` and a contract
   ending "a wrong finding costs this review far more than a silence does"
   (`render_focused.py:72-77`), and are also sent `FACET_CHECKLIST_ONCE` ("apply every item to every
   review target"), which contradicts their one-concern system prompt. The ceiling's
   `verify_edits_if_present` sits between the two: a supplied edit is compiled, and an ask without
   one is still filed. That difference from the generalist baseline is stated in the write-up.
3. **The lead's discretionary allocation has produced nothing.** Over six held-out reps, the 235
   specialist jobs the lead *chose* (waves 1 or 2, briefed or not) produced **0** gold matches. All
   21 specialist matches came from rule-mandated, briefless wave-1 jobs, which never saw the
   generalist's output. A second wave opened on 1–4 of 12 PRs per rep. This is the measured form of
   problem 2, and the motivating result for the scheduler todo.
4. **No arm is shown the PR diff; solo is** (`review_map.py:5-6`; `base.py:230-239`). The ceiling
   keeps the arms' view unchanged so the comparison with fanout is one-variable; a diff-bearing view
   is a listed untried design.
5. **More record corrections for `record-corrections.md`:** the spine doc's solo "$1.90 billed" is
   nominal (billed $0.74–0.84/rep); its claim that solo uses "the same prompts and the same
   submission contract" contradicts `solo.py`; its obligation prefix `7fef9136` should be `7fef913e`.
   The untracked `docs/ai4math-convening.md` §8 says the reviewer sees the complete PR diff, which the
   code contradicts. That file belongs to another session and is not edited here.
