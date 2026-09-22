# Specialist silences: review of the abstention interventions, and the revised plan

Written 2026-09-21 against `develop` at `51a70f9`, reviewing `docs/todo/specialist-abstention-interventions.md`
and the diagnostic it rests on (`docs/research/decision-replay-gold-abstentions-2026-09.md`). Every claim below was
checked against the tree and the committed run artifacts today; the counts marked *provisional* are one reader's
pass over the 45 recorded abstention texts joined to gold and want the second pass that step 0 makes reproducible.

## Context — what the review found

The diagnostic is sound: 41 of 45 gold-site specialist silences reproduce under re-decision, so re-rolling the
decision buys at most 4. The *interventions* built on it need revising in five places.

**1. The population is mostly the wrong arm, correctly silent.** Joining the 45 sessions to the gold asks
(`report buckets` cells × `gold/judgments.jsonl` `concern_labels`, through `CONCERN_ALIASES`): 43 of the 45 appear
as silent cells at 22 counted obligations, and only **11 of 43** sit at an obligation whose concern label is in the
arm's `expected_concerns`. The other 32 are `duplication` at a rename, `naming` at a "factor out a lemma", four arms
at a docstring ask. Those are correct silences; the miss there is routing (was an on-concern arm scheduled at that
site at all), which is a different thread and is bounded by the fanout dead-end. The headline "41/45 stable" is
true and mostly means this. *Provisional:* gold's concern labels are themselves noisy (33145's "generalize into
`Dense.ciSup'`" is labelled `duplication`), so 11 is a lower bound and a hand read is needed — step 0.

**2. The dominant on-concern blocker is not in the todo's list.** Reading the 43 texts, about **9** cite a compiling
edit they could not produce or that the contract refused: "no verified replacement compiles" (33149 duplication,
on the Parseval ask), "although the edit compiles, the submission validator requires statement changes to be
provided via declaration_name+new_declaration" (33145 generality), "cannot submit a verified proposed edit" (33321
style), "a verification-backed patch would require a coordinated multi-declaration rename" (33321 family_design),
"could not produce a verified in-file edit" (33421 correctness), "verification fails due to missing pointwise
HMul" (33117 generality), two proof_idiom sessions on 33145. This is a **contract rule, not a misreading**:
`candidates.py:420-424` refuses any candidate in a checkable family (`correctness, proof-golf, duplication,
generalization`) with `proposed_edit: null` — "candidates require a structured proposed_edit under the
verification-backed residual policy" — and the supplements say "report ONLY verified edits", "Do not propose
generalizations you could not get to compile", "If nothing you attempted compiled, submit nothing". The
maintainer's ask on 33149 was exactly "replace the axiomatized Parseval with the existing one"; the arm found the
existing lemma and was not allowed to say so without a compiling patch the maintainer never supplied either.
Non-checkable arms (`style`) are not refused but read the shared contract sentence "Verify every edit with
lean_verify_edit before submitting it" the same way. Call this mechanism **fix_required**.

**3. Mechanism 1's example is not in the population, and its recall cost is unproven.** The 33149 `correctness`
session that saw the axioms (`wu:1c5956b9…#correctness`) is from the four-session case study, not the 45; its unit
carried no required gold change. The two "remove the axioms" obligations were **COVERED** in this rep (the `docs`
arm hit them). Among the 45, no text describes a defect it saw outside its unit. The retention half is real and
cheap — `abstention_detail` is written to `arm_responses.jsonl` and **read by nothing** (`finalize.py` has zero
occurrences of `abstention`; `report._abstentions` counts reasons and discards detail) — but the observation
*channel* has, today, zero motivating sites in the gold-site population. Defer it behind step 0.

**4. Mechanism 2's only example is decision-limited, and the licence already exists in the prompt.** The 33337
naming session filed the gold rename 3/3 in the diagnostic (2/5 in the case study). And `NAMING_SYSTEM`
(`focused_prompts.py:363-368`) already says "`emerging` — … Say so as an ADVISORY suggestion"; the
`naming_norm` description says "(advisory at most)" and its rendered line says "Advisory at most -- say it is the
emerging spelling, not the rule". So the todo's condition 2 as written — "tell the arm that emerging warrants an
advisory candidate" — restates text the arm already holds. What the arm does *not* hold: the `SUBMISSION_CONTRACT`
appended last (`render_focused.py:52-99`) mentions advisory only as the JSON literal `"blocking|advisory"`, and
closes the abstention paragraph with "a wrong finding costs this review far more than a silence does". Gold, by
contrast, marks **17 of 22** counted obligations `blocking_force: advisory`: the advisory tier is where most of the
asks live. Condition B stays, redesigned as a contract-and-schema change, and **gated** on step 0 finding ≥ 3
advisory-suppressed cells (today's count: 1).

**5. The tool-work step cannot be tested the way the todo prices it.** A replay at `--cut turn=1` resumes from
the *recorded* system prompt, user prompt and tool list (`conversation.py:470-507`, `:638-690` bypassed;
`_replay_tool_definitions` shows the recorded set, a newly registered tool lands in `registered_not_shown`). It
exercises today's *implementation* of an already-granted tool, never a new tool or a changed prompt. So "merge-base
file access" is a rep, not a $5.82 replay; a `naming_norm` behaviour fix (subject resolution, prefix-only
population) *can* be replayed at turn=1 on the 11 naming sessions. Also: no condition but `null` exists yet;
`PromptReplacement` requires the substring **exactly once**, so a condition spanning arms with different prompts
is refused unless it edits only the shared contract text or uses `closing_instruction`.

Two smaller corrections. The "$2.60 per condition" omits the guard population: the 45-session selector contains
no control PR, so no replay so far could measure the one thing the todo names as the guard (control-PR emission).
`v2_rep1` has **7** specialist abstentions on the controls 33304/33315 (5 + 2); replaying them is ~$0.35 and is
the paired precision proxy. And the diagnostic found 17/45 abstention *labels* swap under replay, so step 0 must
label from the detail texts, not the reason enum; the replayed texts survive only in
`.claude/worktrees/decision-replay/.ape/runs/…` (135 session files, present today) — `replay_outcomes.jsonl`
does not carry `abstention_detail`.

Checked against `docs/dead-ends.md`: not on it. Forcing and "be less conservative" nudges stay out (the 41/45
argument and the 1 → 36 control emission). Condition A removes a *refusal* and says so; it does not ask for
findings, and its output lands in the `diagnostic` admission the gate already keeps out of `published`.

## The revised interventions, in order

| # | What | Motivating count (provisional) | Gate to run | Cost |
|---|---|---|---|---|
| 0 | **Step 0 as an instrument, not a hand read**: `report silences` joins gold ask, concern, blocking force, arm remit, recorded detail, refusals and replay stability per silent cell; labels go in a store the report reads back | 43 cells, 22 obligations | none | $0 |
| A | **`ask_without_fix`**: a checkable-family candidate may be filed with `proposed_edit: null`; it lands as `diagnostic`, unpublished, judged pre-publication | ~9 of 43 texts cite a compiling-edit requirement; 5 obligations, 4 PRs | step 0 confirms ≥ 3 `fix_required` cells | ~$3.30 + ~$1 null top-up |
| B | **`advisory_licensed`**: contract sentence + `severity` schema description say an emerging/minority verdict warrants an advisory candidate; silence is for `insufficient_evidence` | 1 cell today; 17/22 gold asks are advisory | step 0 finds ≥ 3 `advisory_suppressed` | ~$3.30 |
| C | Out-of-scope observation channel (todo's #1) | 0 cells in the 45; 1 in the case study | step 0 finds ≥ 3 `cross_unit` | deferred |
| D | Routing: on-concern arm never scheduled at the site | 32/43 cells off-concern | separate thread; measured by 0, written as a todo | $0 here |
| E | Tool behaviour: `naming_norm` prefix-only population and subject-resolution zero branch | 33421 suffix rename; 596/834 zero-branch calls | step 0 `evidence_gap:naming_norm` ≥ 3; testable at `--cut turn=1` | priced by preflight |

Every paid condition runs on **`gold-site-abstentions` (58 sessions) plus the new `control-abstentions` (7)**,
paired with `null` on the same prefixes (45 already on disk; top up the 13 + 7). Conversions are hand-read
against the gold `claim` from the step-0 sheet; the replay → finalize → judge path stays unbuilt and the write-up
says so.

## Implementation

Worktree: `git worktree add -b specialist-silences .claude/worktrees/specialist-silences develop &&
.claude/worktree-setup.sh .claude/worktrees/specialist-silences`; `export PYTHONPATH=$PWD/src`. Three other
sessions share the main tree; nothing here touches their uncommitted files. One commit per step, suite green,
`verify_frozen verify` after W4.

### W0 — register the plan and correct the record (docs only)
- Copy this file verbatim to `docs/plans/2026-09-21-specialist-silences.md`; add it to `docs/plans/README.md`.
- `docs/todo/specialist-abstention-interventions.md`: status → *in progress, plan linked*; add a "Corrections
  2026-09-21" block with points 1–5 above (mechanism-1 example not in the 45; naming prompt already licenses
  advisory; `turn=1` cannot test a new tool or prompt; no control sessions in any replay yet; fix_required
  missing). `docs/todo/README.md` row: one-line amendment.
- Commit: `docs: specialist silences -- the population is mostly off-concern, and the on-concern blocker is the compiled-edit rule`.

### W1 — `report silences`: the step-0 sheet, and a store for its labels
- `src/mathlib_review/analysis/report.py::buckets` (946-1154): the judgments loop (1031-1044) already holds the
  judgment row; carry `claim`, `concern_labels`, `blocking_force`, `speech_act`, `required` onto each obligation
  row. Per cell add `abstention_detail` (from `responses[...]["abstention"]["detail"]`, silent cells only),
  `on_concern` (arm's `ARM_DEFINITIONS[...].expected_concerns` ∩ judgment `concern_labels`, both mapped through
  `analysis/benches.CONCERN_ALIASES`), and `recorded_refusals` (from the source `arm_responses` is not enough —
  take it from the replay run's `recorded.decision.refusals` when `--replay` is given). Per obligation add
  `on_concern_arm_scheduled: bool` over *all* cells (the routing measurement for D).
- `_replay_stability` → `_replay_annotations(replay_run)`: per invocation `{stable, replay_reasons,
  replay_details}`; details read from `replay_outcomes.jsonl` when the row carries them (W2 makes new runs do
  so). For the committed 45-run the field is absent; the report says `replay_details: null` rather than reading
  worktree session files.
- New `report silences --run SRC --replay REP`: flattens `buckets` to one row per (obligation, silent cell) with
  the fields above plus `silence_label` from the store. JSON like every other report. CLI: `cli.py` report
  subcommand table (`:224-229` pattern).
- `SilenceLabel` in `src/mathlib_review/schema/scoring.py` beside `AdjudicationLabel`: `schema_version:
  "silence-label1"`, `key = f"{invocation_id}|{obligation_id}"` (recurs across reps: `invocation_id` is
  `work_unit_id#arm` and units are release-derived), `pr_number`, `arm_id`, `label: Literal["off_concern",
  "fix_required", "advisory_suppressed", "cross_unit", "evidence_gap", "knowledge_gap", "disagreement",
  "decision_noise"]`, `evidence_gap_tool: Optional[str]`, `note: str`, `labelled_by` (`human:<name>` |
  `task:<id>`), `labelled_at`, `from_run`, `replay_run`. Store `paths.ADJUDICATIONS / "silence_labels.jsonl"`,
  append-only; `judge/adjudicate.py` gains `ingest_silences` sharing the human-prefix refusal (factor
  `_assert_human` out of `ingest`) and `resolve_silences` (latest human row wins, `contested` reported); `cli
  adjudicate --silences <file>`. Same rule as `AdjudicationLabel`: a label orders and explains, never enters
  recall.
- Tests: extend `tests/mathlib_review/test_buckets.py` (gold fields and `on_concern` on cells; detail present
  on silent cells only; `on_concern_arm_scheduled`); new `tests/mathlib_review/test_silence_labels.py` (round
  trip, human-only ingest, latest-wins, label surfaces on its cell in `report silences`).
  `tests/datasets/test_pr_review_v5_row_models.py` must stay green (no row model changes).
- Commit: `analysis: report silences -- each gold-site silence beside its ask, its arm's remit and its label`.
- **Then do step 0**: run `report silences --run pr5_A_lead_heldout12_v2_rep1 --replay
  pr5_replay_null_first_submit_candidates_goldabstain45_v2_rep1`, label the 58 cells by hand from the detail
  texts (consult the worktree session files for the 4 unstable sessions), ingest, commit the store file and the
  counts into the todo. This decides the gates for A, B, C, E.

### W2 — retention gaps found on the way (tiny)
- `src/mathlib_review/review/replay.py::submission_summary` (54-74) keeps `abstention_detail`; `collect_outcomes`
  rows carry it under `decision.first`. Test in `tests/mathlib_review/test_decision_replay.py`.
- `src/mathlib_review/schema/review.py:259` comment on `ArmResponse.abstention` says `finalize` reads it; it does
  not. Correct the comment (no behaviour change).
- Commit: `replay: outcome rows keep the abstention text, which is the evidence the label is not`.

### W3 — the guard population: `control-abstentions` selector
- `src/mathlib_review/review/replay.py:134-135` `selector` Literal gains `"control-abstentions"`;
  `select_invocations` (253-323): reviewed PRs with no `proposed_atomic` obligation in the run's release
  (`StageInput.release / "gold/judgments.jsonl"`), specialist `arm_responses` rows with `abstention` set;
  provenance `gold_derived: True`, `control_pr_numbers`, same "gold does not reach a prompt" note. `cli.py`
  `--select` choices. Test beside the selector tests (`test_decision_replay.py:537-632`): on the fixture run it
  picks the control PRs' abstaining specialists and nothing else; refuses when the release has no controls.
- Commit: `replay: a control-abstentions selector, so a condition's conversions are read against the PRs where maintainers asked for nothing`.

### W4 — Condition A: `ask_without_fix`
- Policy value `"verify_edits_if_present"` in both Literals (`src/mathlib_review/schema/identity.py:369`,
  `src/ape/tasks/lean_tasks/formal_math/review/candidates.py:35`). In `_verify_candidate_submission`
  (`candidates.py:405-424`): the `checkable and edit is None` refusal applies only under
  `verify_checkable_edits`; under the new value an edit is compiled when present, and a checkable candidate with
  none is accepted with no artifact, which `finalize._unwarranted_findings` (244-278) already projects as
  `admission="diagnostic"` (confirm the arm path reaches it; pin with a test). `_statement_gate_error` is
  skipped when there is no edit. "Coordination is a refusable policy": implemented before accepted.
- Far-end assertion (rule: a directive travelling in task data is asserted where it lands):
  `conversation.py:490-505` writes `session_replay.json`; add `task_data_seen: {k: getattr(task.data, k, None)}`
  for each `task_data_overrides` key, and `collect_outcomes` copies it onto the outcome row. A replay whose
  override did not arrive is then visible in the report, as `replayed_from_prefix` already is.
- Condition config `configs/v5_replay_ask_without_fix.yaml` (`extends: v5_replay.yaml`):
  `condition.name: ask_without_fix`; `task_data_overrides: {submission_verification_policy:
  verify_edits_if_present}`; `closing_instruction` — one contract amendment, uniform across arms: a candidate in
  this check may be filed with `proposed_edit: null` when the fix could not be made to compile; state the
  transformation in `requested_change` and what was tried and what the compiler said in `suggested_fix`; it is
  recorded as unverified and is not published; it is not a silence; nothing here asks for a finding you do not
  believe in. (A `prompt_replacements` version would need per-arm conditions because the "ONLY verified edits"
  sentences differ per supplement — the shipped form is a prompt change tested by a rep, not by a second replay.)
  If the recorded `proposed_edit` description asserts it is required, add a `tool_schema_edits.descriptions`
  entry at `properties/candidates/items`. `tests/datasets/test_config_strictness.py` covers the new YAML.
- Tests: `tests/datasets/test_pr_review_v5_abstention.py` / `test_pr_review_v5_arm.py` pattern — under the new
  policy a duplication candidate without an edit is accepted; with a failing edit still refused; under
  `verify_checkable_edits` still refused (pin the old behaviour); `task_data_seen` lands in the record
  (`tests/ape/test_session_replay.py`).
- Commit: `contract: an ask whose fix does not compile may be filed unverified -- it lands as diagnostic, not as silence`.

### W5 — Condition B: `advisory_licensed` (only if step 0 gates it in)
- `configs/v5_replay_advisory_licensed.yaml`: `prompt_replacements` (node `system`, exactly once in every arm's
  recorded prompt because `SUBMISSION_CONTRACT` is shared) on "Never add a candidate you do not believe in to
  avoid abstaining; a wrong finding costs this review far more than a silence does." → the same sentence plus:
  a candidate you hold at advisory strength is one you believe in — file it with `severity: advisory`; silence
  is for `insufficient_evidence`. `tool_schema_edits` at `submit_candidates` `properties/candidates/items`,
  `descriptions.severity`: blocking = a maintainer would hold the PR; advisory = supported at emerging or
  minority strength, filed rather than withheld. No code. Test: the two `old` strings occur exactly once in each
  of the ten arms' rendered prompts on the fixture pool (guards against a renderer bump silently refusing it).
- Commit: `replay: advisory_licensed condition -- the contract, not the arm prompt, says what advisory is for`.

### W6 — running and reading
```
R="ape/bin/python -m src.mathlib_review.review.cli"
# null top-up on the sessions without one (preflight, then --execute)
$R replay --config configs/v5_replay.yaml --of pr5_A_lead_heldout12_v2_rep1 --select gold-site-abstentions \
   --run-name pr5_replay_null_first_submit_candidates_goldsite58_v2_rep1
$R replay --config configs/v5_replay.yaml --of pr5_A_lead_heldout12_v2_rep1 --select control-abstentions \
   --run-name pr5_replay_null_first_submit_candidates_control_v2_rep1
# condition A, same two populations, same window
$R replay --config configs/v5_replay_ask_without_fix.yaml --of pr5_A_lead_heldout12_v2_rep1 \
   --select gold-site-abstentions --run-name pr5_replay_ask_without_fix_first_submit_candidates_goldsite58_v2_rep1
$R replay --config configs/v5_replay_ask_without_fix.yaml --of pr5_A_lead_heldout12_v2_rep1 \
   --select control-abstentions --run-name pr5_replay_ask_without_fix_first_submit_candidates_control_v2_rep1
$R report replay --run <condition run> --against <null run>        # paired, sign test
$R report silences --run pr5_A_lead_heldout12_v2_rep1 --replay <condition run>
```
Preflight prices each before `--execute`; the orchestrator resumes on the same name (the 45 already-null
sessions are re-run under the 58 name only if the preflight says the cache makes it cheaper than juggling two
nulls — otherwise pass the 13 missing ids via `dataset.invocation_ids`, which always narrows).

Reading rule, fixed before spending: A is funded for a rep if ≥ 3 sessions labelled `fix_required` file a
candidate whose `requested_change` a hand read matches the gold `claim`, **and** control conversions stay within
the historical 0–1 — read as pre-publication events, since the new candidates are `diagnostic`. Every converted
candidate's `finding_key` and verdict go into the write-up table; the ones at gold sites are also entered in the
`AdjudicationLabel` store as `correct_ask`/`wrong`, so a later rep that reproduces them is pre-labelled.

### W7 — write-up and record
- `docs/research/specialist-silences-2026-09.md`: the step-0 split (per label, per arm, per PR), the
  condition results per session, controls, what is untried. Report at the altitude the evidence supports: one
  source rep, in-sample selection, submission-level plus hand read, no judge.
- `docs/todo/`: new `routing-on-concern-coverage.md` (D) carrying the `on_concern_arm_scheduled` numbers from
  step 0 and the fanout dead-end as its bound; C and E updated with their step-0 counts; the abstention todo
  closed or narrowed with the commit that did it. `docs/dead-ends.md` entry only if A or B fails on the reading
  rule, with what would reopen it.

## Verification
- `ape/bin/python -m pytest tests -q` green at every commit; `ape/bin/python -m
  src.mathlib_review.release.verify_frozen verify` prints ok after W4 (policy Literal lives in
  `schema/identity.py`, which sealed prompts reference — confirm no frozen hash moves; if it does, the value goes
  on the task model only and the identity Literal is untouched).
- Before any `--execute`: `assert the capability reaches the task` — for W4, `session_replay.json.task_data_seen`
  on a one-sample dry replay of one session shows `verify_edits_if_present`; for W3, the preflight lists exactly
  7 control sessions for `v2_rep1`.
- `report replay` refuses any stray sample (`replayed_from_prefix`), so a re-run cannot pass as a replay.
- `tests/datasets/test_package_boundaries.py` and `test_pr_review_v4_no_duplicate_helpers.py` counts unchanged or
  lower: W1 adds no module, W3–W4 add no helper outside `replay.py`/`candidates.py`/`adjudicate.py`.

## Out of scope, said plainly
- Feeding replayed candidates through finalize and the judge (replay todo step 6). Hand read instead; ≤ 10
  conversions expected.
- A full rep with the shipped contract text: the outcome of A decides whether to buy it (~$7.26).
- Routing changes for the 32 off-concern silences (D): measured here, decided elsewhere.
- Any new tool (merge-base view, `patch_set` fix): not testable by replay; not in this plan's spend.
