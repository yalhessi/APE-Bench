# One run to move the wall: let the arms say what they found

*Plan written 2026-09-23 on `develop` at `2a1f1c9`. One worktree, one judged run on the 12 held-out PRs, ≤ $20 billed. Repetitions, ablations, the arm remap and the iterative lead come only after the wall moves. To be copied verbatim to `docs/plans/2026-09-23-one-run-to-move-the-wall.md` as the first commit.*

## Context

The user named three problems after the abstention session: the generalist does the work and the specialists map poorly onto maintainers' asks; allocation is "queue the generalist, fit specialists into the remainder"; review should be iterative. All three are real (see the appendix for the measurements and the deferred designs). The user's ruling on the first draft of this plan: **cost is the constraint, and the thing to buy is one demonstration that issue recall can break through the wall it has sat behind for months.** Reps and ablations follow a breakthrough, not precede it.

**The wall.** Issue recall on the 12 held-out PRs (23 eligible obligations, judge v9, pre-gate): the three `lead` reps hit **7 / 5 / 6** (0.30 / 0.22 / 0.26), `solo` 4 / 4 / 1. Nothing in the record beats 7 of 23 on this set. On the 4-PR stage1 set, `lead` and `fanout` both hit 2 of 10.

**The one thing that ever broke it.** `forbid_abstention` on the same fanout: **2 → 5 of 10** (majority rule; 3 unanimous), 3 of the 5 new hits from `naming`, which had filed nothing unforced. It is a diagnostic, not a design: control-PR emission went 1 → 36. But it settles what the wall is made of: **the arms hold the answers and are configured to withhold them.** Four mechanisms, each verified in code this session:

1. **Compile-required.** A candidate in `correctness / proof-golf / duplication / generalization` with `proposed_edit: null` is refused (`src/ape/tasks/lean_tasks/formal_math/review/candidates.py:462-468`); the supplements say "If nothing you attempted compiled, submit nothing". ~9 of 43 gold-site abstention texts cite it. PR 33149: the arm found Mathlib's Parseval lemma and could not file "use it" without a compiling patch the maintainer never supplied either.
2. **Silence licensed, advisory undefined.** `SUBMISSION_CONTRACT` (`src/mathlib_review/agenda/render_focused.py:72-77`), appended to every specialist: "Submitting nothing is a correct and common outcome … a wrong finding costs this review far more than a silence does." `advisory` appears only as the JSON literal `"blocking|advisory"`. Gold is **91 of 113 advisory**. On 33337 the naming arm wrote "emerging (`toLinearMap_` 21 vs 7) … so I'm not requesting a rename" and, forced, produced the gold rename character for character.
3. **Per-job, not per-target.** An arm emits a roughly constant number of candidates per job; consolidated units cut generalist candidates per target 0.49 → 0.15 (`docs/todo/README.md`, "Per-target attention"). Nothing asks the arm to account for each target, and `abstention_detail` is read by nothing (`finalize.py`: 0 occurrences).
4. **The convention arms ask a narrower question than gold's label** (`style` is mostly proof-tactic rewrites and definitional form, not formatting; `naming_norm` counts prefixes). **Deferred:** fixing this means rewriting prompts from a gold-ask census, and any shape learned from the held-out gold would be in-sample on this set.

Mechanisms 1–3 are **generic contract changes**, fitted to no particular ask, so a breakthrough with them is clean. That is the demonstration.

**What does not change in this run:** the lead, the floor, the caps, the arm-specific prompts, the judge. One variable: the submission contract. **Not selection:** an unverified ask lands as `admission: diagnostic` and is never published; recall is measured pre-gate via `report buckets --audit`, and control emission (33304, 33315) is printed beside it. Bounded by `docs/dead-ends.md` "Specialists as the coverage floor" (this adds no slots) and "Publication as selection" (nothing here ranks, keeps or drops a finding).

---

## The change (one worktree, four small commits, suite green at each)

Worktree: `git worktree add -b arms-speak .claude/worktrees/arms-speak develop && .claude/worktree-setup.sh .claude/worktrees/arms-speak`; `export PYTHONPATH=$PWD/src`.

Verified before designing: `verify_edits_if_present` is already implemented (`candidates.py:462-464`, both Literals, three tests at `tests/datasets/test_pr_review_v5_arm.py:339-394`); only the default is missing (`render_focused.py:218` hardcodes `verify_checkable_edits`, pinned by `tests/datasets/test_pr_review_v5_agenda.py:216-222`). An unverified checkable candidate already projects to `diagnostic` in `finalize.py::_unwarranted_findings` (245-276) and is seen by `buckets` and the judge. `render_focused.py` is also v4's renderer (`opportunities/runner.py:119`; `tests/datasets/test_pr_review_v4_focused_task.py:256` asserts refusal), so every change is a parameter whose default keeps v4 byte-identical.

| # | commit | what changes | tests |
|---|---|---|---|
| 0 | `plans: one run to move the wall` | this file to `docs/plans/`, row in `docs/plans/README.md`; status lines in `docs/todo/specialist-abstention-interventions.md` and `specialist-arm-contents.md` → "in progress, plan linked". | — |
| 1 | `contract: an ask whose fix does not compile is filed unverified by default` (renderer `focused-prompt/5`) | `render_focused.py::focused_system_prompt(..., submission_verification_policy=)` renders an `{ask_without_fix_clause}` slot in `SUBMISSION_CONTRACT` iff the policy is `verify_edits_if_present` — text lifted from `configs/v5_replay_ask_without_fix.yaml:66-78` (`closing_instruction`, written for exactly this and already saying "This is not a request to find something"); thread the parameter through `render_focused_invocation` / `render_focused_all`; `agenda.py::build_agenda(submission_verification_policy="verify_edits_if_present")` passed at :354; `runner.py::V5DatasetConfig.submission_verification_policy` (default `verify_edits_if_present`) sealed into `V5RunPlan.evaluation_settings` in `_build_plan` (1165-1172); `finalize.py:493-500` log reworded ("retained as diagnostic: the unverified ask, not a drop"). | agenda test asserts the new policy on every specialist payload and the clause iff policy; v4 focused-task test unchanged; `tests/datasets/test_prompt_contamination.py`; `test_config_strictness.py` round-trips `--set dataset.submission_verification_policy=verify_checkable_edits`; `verify_frozen verify` ok. |
| 2 | `contract: every target ends as a candidate or a labelled abstention` | `candidates.py`: `TargetAbstention{change_id, reason: AbstentionReason, detail}`; `LeanPRReviewV4CandidateData.require_target_dispositions: bool = False`; `LeanPRReviewV4CandidateResult.target_abstentions: List[Dict]` (declared — `extra="ignore"` drops undeclared fields); `submit_candidates(..., target_abstentions=[])`. Rule when the flag is on: targets covered by neither a candidate's `change_ids` nor an abstention → refuse **once**, listing them, with the mute-abstention sentence ("this is NOT a request to find something — record an entry for each"); the second press is accepted with `reason: unstated` per uncovered id (mirrors `_mute_abstentions`, :662-675). Single-target + empty candidates + whole-unit reason → the entry is synthesised. `forbid_abstention` path (:647-661) untouched. `agenda.py::_arm_payload` stamps the flag (default True, generalist included — it learns the rule from the tool description and one refusal); `runner.py` knob sealed into the plan. `schema/review.py::ArmResponse.target_abstentions: Optional[List[Dict]] = None`, `row()` → `model_dump(mode="json", exclude_unset=True)` (the `DelegationRecord.row()` argument), the three builders (`lead.py:893-904`, `runner.py:501-512`, `:565-580`) pass it explicitly. `report.py::buckets` (1085-1112) adds `target_abstention_reason/detail` for the entry at the obligation's site. | new section in `tests/datasets/test_pr_review_v5_abstention.py` (refused once naming the uncovered id; accepted second time as `unstated`; unknown id refused; single-target synthesis; flag off = old contract byte-for-byte; payload-hop test in the style of :376-395); `test_pr_review_v5_tool_schemas.py`; `test_pr_review_v5_row_models.py` → every historical `ArmResponse` row round-trips; `tests/mathlib_review/test_buckets.py`. |
| 3 | `contract: account for every target, and two strengths of ask` (renderer `/6`) | Replace `SUBMISSION_CONTRACT` lines 72-77 — rendered only when `require_target_dispositions`; the old paragraph stays for v4 — with **"## Account for every target"** (each target below is covered by a candidate naming it or by a `target_abstentions` entry with its reason and one sentence naming what you checked there; abstaining at a target is correct and is recorded, not avoided; do not add a candidate to fill a slot) and **"## Two strengths of ask"** (maintainers here ask at advisory strength far more often than blocking; `blocking` = a maintainer would hold the PR; `advisory` = you believe a maintainer would ask for it and would merge without it — a convention the repository is adopting but has not settled, an improvement the author could reasonably decline; a claim you hold at advisory strength is one you believe in: file it as advisory rather than withholding it; silence is for having no evidence, not evidence of moderate strength). `candidates.py:154` `severity` Field description carries the same two definitions — the only route to the generalist, whose prompt is frozen in the release. **`NAMING_SYSTEM` (`focused_prompts.py:361-364`): delete the sentence "Submit nothing on naming"** under `insufficient_evidence` (the tool now distinguishes `subject_unresolved` from `no_population`, `b9acfe3`; the sentence instructs silence on a tool failure) — this is a generic correction, not a shape learned from gold; `EXPECTED_SPEC_IDENTITY` moves for `naming` only, with the dated reason. | contamination; heading-placement assertion (both headings after `# Submission contract for this run` in every v5 specialist prompt, none in v4); extend `tests/mathlib_review/test_supplements_name_real_fields.py` to sweep `SUBMISSION_CONTRACT`; `test_pr_review_v5_arm_registry_consistency.py`. |
| 4 | `report: hits by arm and submit rate as printed numbers` | `report.py::_gate_report` adds `hits_by_arm` keyed on `origin_arm_id` (fallback `sources[0].spec_id`); `_abstentions` adds `filed` per arm. Needed to read *which arm* moved. | `test_buckets.py`; extend `test_pr_review_v5_abstention.py:214`. |

**Knob → run name:** the renderer version is the identity. The run carries `_c6`. Nothing else in the config moves, so the run is paired against `pr5_A_lead_heldout12_v2_rep{1,2,3}` on `configs/pr_review_v5_medium_heldout.yaml` (release 0.3.0).

---

## The run, and the threshold fixed before spending

**Far-end assertion first (free).** `.claude/rules/mathlib-review.md`: a directive travelling in task data is asserted where it lands. Before `--execute`: a test renders the pool for one PR and asserts every specialist payload carries `submission_verification_policy == "verify_edits_if_present"` and `require_target_dispositions == True`, and every specialist system prompt contains both new headings and the ask-without-fix clause. `plan` output confirms the plan seals both knobs.

```
ape/bin/python -m src.mathlib_review.review.cli plan  --config configs/pr_review_v5_medium_heldout.yaml --run-name pr5_A_lead_heldout12_c6_rep1
ape/bin/python -m src.mathlib_review.review.cli run   --config configs/pr_review_v5_medium_heldout.yaml --run-name pr5_A_lead_heldout12_c6_rep1 --execute
ape/bin/python -m src.mathlib_review.review.cli judge --config configs/pr_review_v5_medium_heldout_judge.yaml --of pr5_A_lead_heldout12_c6_rep1 --execute
ape/bin/python -m src.mathlib_review.review.cli report routing --run pr5_A_lead_heldout12_c6_rep1          # degenerate-check first
ape/bin/python -m src.mathlib_review.review.cli report buckets --run pr5_A_lead_heldout12_c6_rep1 --audit  # gate block: pre-gate / published, control beside
ape/bin/python -m src.mathlib_review.review.cli report conditions --condition v2=pr5_A_lead_heldout12_v2_rep1,pr5_A_lead_heldout12_v2_rep2,pr5_A_lead_heldout12_v2_rep3 --condition c6=pr5_A_lead_heldout12_c6_rep1 --release inputs/pr_review_v4/releases/dev-medium-0.3.0
ape/bin/python -m src.mathlib_review.review.cli report silences --run pr5_A_lead_heldout12_c6_rep1
```

**Cost:** the three baseline reps billed $13.83 / $12.75 / $13.75. Commit 2 adds one refusal round-trip on jobs that omit dispositions, so expect ~$14–17 billed plus the judge (its per-run cost is not in any manifest; budget $1–3). **≤ $20 total.** Preflight prices it and stops without `--execute`. Every knob is on by default, so the resume rule cannot silently resume a v2 run under the new name: the renderer version differs.

**Cheaper alternative if $20 is too much:** the same contract under `routing_mode: fanout` on the four stage1 PRs (33145, 33315, 33337, 33421) via `--set`, run name `pr5_F_fanout_stage1_c6_rep1`, ≈ $6–9 billed, paired against the unforced (2 of 10, control 1) and forced (5 of 10, control 36) runs on disk. n = 10, so one obligation is 10pp; the 12-PR run is the credible one.

**Breakthrough, stated before the run:**

| endpoint | the wall | breakthrough |
|---|---|---|
| pre-gate obligations hit (`buckets.gate.obligations_hit_pre_gate`, majority rule, quoted with the rule) | 7 / 5 / 6 of 23; never above 7 | **≥ 10 of 23** — three flips clear of the best rep |
| pre-gate control emission on 33304 + 33315 (`gate.control_findings`) | 3 / 4 / 5 per rep; forced showed 36 on one control | **≤ 8 combined** — a design, not the forcing diagnostic |
| `hits_by_arm` | generalist 22 / 22 / 20 matches, specialists ≤ 4 per rep | at least one specialist hit an obligation no rep's specialist ever hit |

Between 8 and 9 hits: *moved, not through* — report it as such, and fund exactly one more rep (~$16) before saying anything. Below 8: the contract was not the mechanism; write the entry in `docs/dead-ends.md` with the untried designs enumerated — whole-task replay at `--cut turn=1`, merge-base file access for `correctness`/`duplication`, the census-driven prompt remap, the iterative lead — and stop. Above the emission line with recall through: the middle ground does not exist at this contract text; record the pair, do not call it a breakthrough.

**Read the inputs before touching the prompt again.** Whatever the number, the first read is `report silences` and the per-target `abstention_detail`: for every gold obligation still silent, what did the on-concern arm write at that target? That sentence, not the count, decides the next change.

---

## After the wall moves (not funded here)

1. Two more reps of `_c6` (~$32) → mean / union / stable against the v2 reps.
2. **The generalist hypothesis** (user's: specialists are strict improvements; drop the generalist when the rest works). Baseline against it: today the generalist is the *sole* finder of 4 / 3 / 5 of the hit obligations per rep, all inside a specialist's remit (`correctness` filed 0 on both axiom obligations; `docs` 0 matches on the typo). One rep with `--set dataset.generalist_floor=false` (every unit on 0.3.0 has ≥ 1 specialist proposal; preflight's `assert_coverage_is_reachable` checks). "Drop it" is supported only if the specialist-only condition recovers ≥ the with-generalist mean with control emission no worse.
3. **Arm remap from a gold-ask census** (mechanism 4): `report ask-census` over the 65 non-held-out PRs of `dev-judgment-stable-0.9.0` (style 34, naming 16, docs 14 — the three non-checkable arms are 66% of asks); one table per family, one row per ask *shape*, with a gap column for shapes no arm asks — which is the generalist's remaining job; then rewrite `STYLE_SYSTEM` / `NAMING_SYSTEM` / `DOCS_SYSTEM` from the shapes (two edits per arm; `test_prompt_contamination.py` forbids quoting claims). Evaluated cleanly only on a fresh generation release — a release-build thread.
4. **The iterative lead** — see the appendix.

---

## Appendix — deferred designs, kept so they are not re-derived (→ `docs/todo/lead-iterative-queue.md` on commit 0)

**Allocation, measured.** The floor (generalist on every unit + ≤ 10 rule-required specialists per PR) is exempt from `per_pr_cost_cap: 1.50`; the lead's discretion is that remainder — **3–5 jobs per PR regardless of size** (33149 with a 120-job floor got 3; 33305 with 13 got 5), 34–38 `proposed` + 0–5 `agent_added` per rep, ~1,090 pruned as "not selected by the lead". 3 of 12 leads opened a second wave. `JobOutcome.summary()` omits `abstention`; 4 of 10 arms are described to the lead; `max_rounds` is enforced nowhere. **And allocation is not what binds:** fanout = lead = 0.20 on the same PRs; where the lead's pruned on-concern arms ran under fanout they filed nothing 7 of 7. So the loop is built only after the arms speak.

**The design (one thread, ~8 commits, measured at ~$18–25/rep):** (i) one per-PR budget `base + scale × Σ cost_hint(mandatory)` — the agenda's 0.05/job hint tracks actual floor spend closely (33149: hint $5.85, actual $5.08–6.10), so it is priceable at preflight with no new estimator; the floor is charged but never refused, preflight refuses a PR that cannot afford one standard job after its floor; (ii) `parent_view: full` — `JobOutcome.summary(view=)` carrying `abstention`, `target_abstentions` and the context-tool verdict (`naming_norm`'s trace rows record `result_ids` but not the verdict word — one key), collapsing silent jobs when a wave exceeds 40, plus a `read_results` tool; (iii) `max_redispatches_per_pair: 1` with a brief required and `invocation_id@n` (`base_invocation_id` stripped in `trace.reconcile`, `journal.replay`, `review/candidates.py:420`, `report.py:78`, `replay.py:433`; `payload["task_id"] += "__r{n}"` for the `spec_by_task_id` collision), `max_rounds` enforced; (iv) **sibling follow-ups as a deterministic rule** consuming outcomes — candidate on X + `changed_siblings`/`name_family` edge X–Y + unrun pool pair (unit(Y), same arm) → queued with a question-shaped brief, prepended to the next wave exactly as the floor is, `disposition: propagated`, lead may skip by id, `submit_routing` refuses while affordable follow-ups are queued (the trigger is mechanical and the measured lead prunes what it does not reach); (v) `LEAD_SYSTEM` edits — delete the "authority is subtractive and it is real" block (contradicts `apply_lead_synthesis: False`), the "7% of available specialist jobs" complaint, the `cheap` contradiction; replace "Two waves beat one" with the loop; render all ten arms from `registry.ARM_DEFINITIONS` + a hand-kept `ARM_STRENGTHS`; (vi) `report routing` adds waves per lead, discretionary share, redispatches, brief rate, `hits_by_wave` (needs `investigation_id` populated on candidate rows — it is `None` today) and degenerate checks printed first (`one_wave`, `redispatch_all`, `follow_ups_declined`, `budget_idle`). **The selection line:** wave returns drive which pair runs next and what brief it carries; nothing ranks, keeps or drops a finding.

---

## Verification

- `ape/bin/python -m pytest tests -q -n auto --dist loadfile` green at every commit; `ape/bin/python -m src.mathlib_review.release.verify_frozen verify` prints ok after commits 1 and 3 (no frozen hash may move; the policy Literal already exists).
- Far-end assertion test (above) green before `--execute`; `plan` output shows both knobs in the sealed plan.
- `tests/datasets/test_prompt_contamination.py` after every contract or prompt edit; `test_package_boundaries.py` and `test_pr_review_v4_no_duplicate_helpers.py` counts unchanged (no new module, no new helper outside `candidates.py` / `render_focused.py` / `report.py`).
- `report routing` degenerate block read before the recall number; the gate block quoted as the pair (pre-gate / published), never one of them; every recall figure at n = 23 printed with its one-flip increment (±4.3pp).
- Record: results commit (artifacts + audit + numbers in the body); `docs/research/` write-up at the altitude one rep supports — *provisional until replicated*; `plans/STATUS.md` (W4 default, W5 as contract, D4 built); todo status lines; `dead-ends.md` only if the reading rule fails.

---

## Halted before the paid run, 2026-09-23 (the plan above is kept as approved)

Commits 0–4 landed on `arms-speak` with the suite green at each (2271 passed, `verify_frozen` ok),
and the preflight for `pr5_A_lead_heldout12_c6_rep1` passed at zero spend: 12 of 12 reviewed
workspaces, worst case $32.10 against the $35.00 cap. The run was **not** launched.

**Why.** At launch time another session was already running the same experiment on branch
`work-enumeration` (`.claude/worktrees/work-enumeration`, plan
`docs/plans/2026-09-23-work-enumeration.md` on that branch, 18 commits not on `develop`): a
per-target verdict contract (`target_verdicts`: `issue` / `no_issue` / `cannot_determine` per
target) plus `verify_edits_if_present`, as tool-only changes with the rendered prompts untouched,
measured by fanout on the four stage1 PRs with no generalist against a matched control on current
code, three reps each at ~$5/rep. Its treatment rep `pr5_V2_verdicts_fanout4_rep1` was mid-run.
This plan never saw it because the reading was of `develop`; the two branches touch the same six
source files and each adds its own per-target field, so merging both would leave two
implementations of one concept. Which survives is the user's call.

**What this branch has that the other does not**, for that decision:

- contract *text*: the ask-without-fix clause in the prompt, "Account for every target", and
  "Two strengths of ask", which removes "a wrong finding costs this review far more than a
  silence does" and defines `advisory` (also in the `severity` field description, the one route to
  the generalist). The other branch left the rendered prompts untouched on purpose.
- the naming prompt's `insufficient_evidence` bullet no longer instructs silence on
  `subject_unresolved` (spec identity `naming` → `1f4b176a45a4`). The other branch's pilot read
  recorded that `cannot_determine` was never chosen even where `naming_norm` returned
  `subject_unresolved` — the same symptom, left unchanged there.
- `report buckets --audit`'s `hits_by_arm` with `sole_finder`, and `report retrieval`'s `filing`
  rate per arm — measurement only, independent of either contract.
- the measurement design: `lead` on all twelve held-out PRs with the generalist in, against the
  three v2 reps, rather than fanout on four without it.

**A defect this branch shares and the other fixed** (`451eaa8` there): under
`verify_edits_if_present` a refused edit is still answered "Fix the edit or omit the candidate"
(`candidates.py`), so an arm can spend its budget repairing a patch it could have filed as an
unverified ask — it cost the other branch's pilot a real `correctness` duplicate on 33421. Fix
before any run from this branch.

**Reopens as:** either the run above, after that fix, if the user keeps this contract; or the
three distinct pieces ported onto whichever contract survives.

**Unification checklist, added 2026-09-23.** Before `git worktree remove .claude/worktrees/work-enumeration`
(or this worktree), copy each run directory's `arm_pool.jsonl` into the main checkout's matching
`results/pr_review_v5/runs/<run>/`: it is gitignored, so committing the run directories brings the
tracked artifacts across and the removal silently deletes the pool -- which is how all three `rel050`
reps lost theirs (`docs/todo/operational-floor.md` §5). The fanout runs write no
`execution_index.jsonl`, so their trajectories survive the removal; their pools do not.

**Census vs window, added 2026-09-23.** The deferred ask-census ("After the wall moves", item 3) over the
65 non-held-out gold PRs includes all 46 PRs of the unseen window (`docs/todo/eval-unseen-window.md`).
They can be census input or the window, not both. The advisory section's motivation ("91 of 113") is
55% those PRs' judgments; the sentence holds on the held-out 12 alone (19 of 24 judgments advisory).
