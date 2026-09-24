*Appendix to [`../pipeline-overfit-2026-09.md`](../pipeline-overfit-2026-09.md), written by a read-only sweep agent in that session and kept as it reported. Re-derived by the auditor: the 85 whitespace-only units with 714 eligible pairs and 15 required rows (B2), and the three packer-cliff hunks of 24,874 / 24,200 / 25,169 chars (B6). The scratch scripts it names (`features*.py`, `whitespace*.py`, `agenda_sizes.py`) and the plan logs were in that session's scratch directory and are not kept; every number comes from the tree's own functions over the release files named in each table.*

# Pipeline overfit review, part 3: dev-tuned knobs against the validation set's gold-free features

2026-09-24, worktree `pipeline-overfit-review` at `01ceae7`. Read-only: nothing tracked was edited, created or committed. No model was called.

**Boundary kept.**
- Test set `eval-2025-06-2026-03-v1`: nothing under it was opened.
- Validation set `val-2025-06-2026-03-v1`: only `derived/` and `input/` were read. No reviews, no gold, and nothing under `gold/`.
- Dev set: `dev-medium-0.5.0` derived/input files, plus the inventory the held-out configs use (`treatments/systematic-opportunities-v4-medium`).

**Which dev release.** The held-out configs run `dev-medium-0.5.0`: 16 PRs, 101 units, renderer `candidate-prompt/14`. The base config's default release is still `dev-medium-0.3.0` (`configs/bases/v5_generation.yaml:33`). That is the release where 33149 held 108 of 203 units.

**Method.**
- Part B is computed with the tree's own functions: `agenda.enumerate_invocations` (the eligibility rule), `components.build_components`, and `routing.plan_coverage`.
- Nothing is rendered and no exposure index is used. Exposure only moves a pair from optional to recommended, never to required, so the required counts do not depend on it.
- The required counts match `cli plan` exactly: 399 required specialist rows, 824 floor jobs, $41.20 floor on val60.
- Scratch scripts are in this directory: `features.py`, `features2.py` … `features6.py`, `whitespace*.py`, `agenda_sizes.py`. Plan logs: `plan_val60.log`, `plan_val12.log`, `plan_dev12.log`.

**Column key.**
- dev16: the whole dev release. dev-heldout12: dev16 minus smoke4.
- val60: the whole validation set. val-main50: the 50 natural-rate PRs. val-AI10: the AI stratum, from `evaluation_strata.jsonl`, `stratum == "ai"`.

---

## Part A: knob inventory

**Set-specific?**
- **S**: yes. It was fitted on a named dev PR, run or measurement.
- **P**: plausibly. Its calibration used dev-scale runs.
- **N**: no.

**What val says** (the last column) takes one of four values:
- **fine**
- **LIKELY WRONG**, with the number that says so
- **can't judge**: needs a run or gold
- **inert**: the knob does nothing

Part B holds the supporting tables. Provenance comes from comments, `git log -S` and commit bodies. Two background readers compiled the tool, lead and cap rows, and I spot-checked the load-bearing lines: the naming bars and the 3× tier, the floor exemption from `max_delegations`, the per-wave reservation, the lead prompt text, `procedure_variant`, and `pr_finding_limit`.

### A1. Packer and prompt rendering
| knob | where | value | tuned on | set? | what val says |
|---|---|---|---|---|---|
| `MAX_TARGET_CONTENT_CHARS` with the /13+ bundle packer, which charges each hunk once per unit | `release/work_units.py:21`, `:28-101`, gated at `:111` | 24,000 chars per unit | The value dates from v4 (3237679). The packer under it was re-tuned (12a3939) on 33145 (62,352 charged against 10,198 real) and 33149 (108 units to 12; its one hunk is **17,303** chars, under the budget). | value N, interaction **S** | **LIKELY WRONG.** Three new-file PRs each have one shared hunk **above** the budget: 26484 (24,874 chars), 34906 (24,200), 36637 (25,169). Every bundle therefore opens a new unit: 66 + 39 + 33 = **138 of 425 units (32%)**. At 30,000 they pack to 44 units and the set to 328 (B6). At /14 the renderer prints scoped diffs, not the hunk, so the charge is for text no prompt carries: those units' prompts have a median of 6.3–8.2k chars. |
| per-target overhead | `work_units.py:81` | +500 chars | v4 | N | fine |
| never cross a file boundary | `work_units.py:91` | — | v4 | N | fine. File sweeps are 31% of val units against 51% of dev units, so dev exercised this too. The 59-unit PR is a sweep; see A2 on whitespace. |
| a doc-comment or attribute packs with its declaration | `work_units.py:51-54` | `attached_to` | 33321 | N | fine |
| renderer /14 flags | `agenda/render_prompts.py:336-349` | scoped_diffs, checklist_once, contract_in_user_message, preserve_adjacency | `pr5_A_lead_heldout12_rel040_rep1`; the adjacency fix came from 33321 | P | can't judge. Size is not the problem: 0 prompts omit a target in either set; generalist prompts at p90 are 16.9k chars on val against 25.2k on dev. |
| diff / description / file truncation | `render_prompts.py:169` | none | — | N | fine. 0 omitted targets; no target exceeds 24k chars alone. |
| `MAX_SKELETON_ROWS` | `agenda/review_map.py:40` | 40 | 3828243, no measurement (the skeleton feature exists for 33362) | N | fine. 4 of 101 skeletons are truncated (dev: 1 of 49). |
| family members shown in a slice | `review_map.py:121` | 8 | none | N | fine. 9 of 189 families are cut (dev: 4 of 83). |
| hardwired convention questions: rename, primed name, `coe_` | `review_map.py:200-218` | 3 kinds | 33294, 33421, 33337; the `coe_` question states 33337's answer | **S** | can't judge. Model-visible dev text (see A8). |

### A2. Eligibility: subject kinds, lifecycles, roster
| knob | where | value | tuned on | set? | what val says |
|---|---|---|---|---|---|
| `DECLARATION_KINDS` | `agenda/focused_specs.py:42-44` | 6 kinds | v4 | N | fine |
| `_BOTH_LIFECYCLES`, applied to **all** ten arms | `agenda/arms.py:89`, applied at `:122` and `:154` | added + modified | smoke4 gold: all 22 gold targets in 33066/33098 are `added` (43e9d88) | **S** | **LIKELY WRONG in part.** proof_golf/idiom are eligible on 212 units, against 90 under the v4 modified-only rule (2.4×). On the AI stratum it is **52 against 2**. The widening also reaches duplication and generality, whose own remits say "a *new* declaration" (`registry.py:154`, `:157`): 333 units against 174 under their v4 added-only rule. The comment justifies the widening only for the proof arms. |
| `removed`, `renamed` and `moved` never eligible | `arms.py:89`, `focused_specs.py:65` | — | v4, never examined | N (unexamined) | **LIKELY WRONG.** Val has 92 removed declarations in 14 PRs; dev has 13 in 4. No specialist is eligible on any of them. 36 have no trace on any `+` line, and only 3 have a `deprecated` alias on the same line. The inventory never emits `renamed`: a rename arrives as removed + added, and 23 of the 92 are re-added under the same short name. |
| no substantive-change filter on `modified` | inventory lifecycle, consumed by `applies_to` at `focused_specs.py:64-74` | any byte change counts | never needed: **0 of 124** dev modified declarations are whitespace-only | **S** by absence | **LIKELY WRONG.** **120 of 344** val modified declarations (35%) are whitespace-only: 81 in 26718 (a `commandStart` linter extension) and 38 in 33716 (spacing). **85 units (20%)** hold nothing else, and they carry **714 eligible specialist pairs**, 85 floor jobs and 15 required rows. 21 of these declarations count as proof-modified, so golf and idiom are eligible there. |
| `component="proof"` filter for golf/idiom | `focused_specs.py:156`, `:168` | proof delta added/modified | v4 | N | fine, apart from the whitespace case above |
| docs `extra_subject_kinds` | `agenda/registry.py:122`, `:189` | module_doc, doc_comment (plus declarations) | 33305, 33321 (0370e5b) | P | fine as eligibility (383 units) |
| style `PLACEMENT_KINDS` | `registry.py:125`, `:206` | + namespace_or_section, command, import, attribute | 33362 | P | fine as eligibility. namespace_or_section is 14.5% of val records against 9.1% of dev. |
| `expected_concerns` (style+scope, correctness+scope, family_design dup+gen) | `registry.py:205`, `:218`, `:225` | — | 33362 | S | can't judge (not an admission rule) |
| roster: ten arms; lean five | `registry.py:130-231`; `configs/pr_review_v5_contract_fanout4_lean.yaml` | 10 / 5 | The lean roster was chosen on fanout4 gold; the file says "do not carry this roster to another PR set". | **S** (lean) | can't judge. On val the lean roster leaves **92 units (21.6%)** with no eligible arm, against 41.6% on dev (its own comment: 22 of 33 on fanout4). It costs less coverage here, but it was selected on scored gold. |
| per-arm context grants | `registry.py:139-229` | e.g. naming gets naming_norm, declaration_search, precedent_search, zulip_search | smoke4 rep13 (33337), rung 0 on 33098, family_design's 50 of 63 calls | P | can't judge |
| `procedure_variant` (the proof_profile grant) | `focused_prompts.py:768-783` | `baseline` in every config | rung ladder on 33098 | S | inert: proof_profile is never granted |

### A3. Components and routing
| knob | where | value | tuned on | set? | what val says |
|---|---|---|---|---|---|
| `_INTENT_GRAIN` keyword substrings over title + description | `agenda/components.py:48-57` | golf, simplif, rename, deprecat, migrat, generalis/z, dedup | 33285 | P | Precision is about 4 in 5 on both sets. On val, 17 of 60 PRs match; 3 matches are clearly false (29339: "linter for deprecations"; 34906: "further golfs with Claude and Codex"; 36784: "I don't think it makes sense to add deprecations") and 37352 is borderline. On dev, 33066's "Please feel free to golf!" is the same kind. The new harm: the 34906 false match lands on a **39-unit AI PR**, which then asks **70 uncapped required golf/idiom rows**. No negation handling. |
| `_stem` hypothesis families (namespace + leading token) | `components.py:113-132` | — | 33145 | P | fine. 85 of 189 families (45%) are hypotheses, against 41 of 83 (49%) on dev. |
| file grain needs at least 2 changes | `components.py:341` | 2 | none | N | fine. 100 file components give 95 required style rows. |
| introduction trigger | `components.py:316` | base empty and reviewed non-empty | 33149; heldout12, where correctness was never required | N | fine as a trigger (397 introductions) |
| `_GRAIN_REQUIREMENTS` | `agenda/routing.py:39-67` | migration→naming; family→family_design+naming; file→style; site→docs; introduction→duplication+correctness | 388 of 554 proposals had become mandatory | P | Same shape on both sets: required rows are 11.4% of the val pool and 14.9% of dev's. **api_reuse is never required: 0 of 333 eligible units.** It could only be required through a `dedup` intent, and no val PR has one. |
| `_ONCE_PER_PR` | `routing.py:78-81` | docs/site; family_design/family; duplication and correctness/introduction | 33304/33315 (17 of 27 docs jobs), heldout12 family_design (24 jobs, 1 candidate), 33149 | **S** | Introduction: one PR holds **49** units with a new declaration (the AI maximum is 30; the dev maximum is 12, 33149), and it gets one required duplication job. Docs: 21 PRs change a module doc and 34 change a doc-comment (213 records); docs is required on 18. |
| `MAX_REQUIRED_SPECIALISTS_PER_PR` | `routing.py:97` | 10 | 33149's $10.05 floor | P | Binds on 12 of 60 val PRs (dev: 4 of 16); uncapped demand is 489 rows against 399. Slots fill in `(work_unit_id, arm_id)` order (`routing.py:170`), which is hash order, so the first units take all 10. 26484 gets required specialists on **6 of 66 units**, 34906 on **3 of 39**. |
| `MAX_INTENT_REQUIRED_PER_PR` | `routing.py:87` | 12 | 33285 | S | inert: every intent claim also spends one of the 10 slots |
| `DEFAULT_CENTRAL_RANK` | `routing.py:102` | 3 | none | — | inert: `agenda.py:295` passes empty census rows |
| centrality ≥2; exposure floor 5 | `routing.py:248`; `exposure.py:66` (a literal copy at `routing.py:229`) | 2 / 5 modules | "calibrated against the heldout set" | S | low stakes. Together they move 38 of 3,485 val pairs from optional to recommended (plan with the index against my run without it). |
| census `_WEIGHTS`, `_INTENT_KEYWORDS`, `_CHAIN_STEPS`, `_LONG_PROOF_LINES` | `agenda/census.py:78`, `:55`, `:107`, `:96` | 1–100 / 9 stems / 3 / 12 | "read off the two proofs 33285's maintainer asked to golf"; the docstring says "not calibrated" | **S** | can't judge. It matters more on val: the census orders the lead's 15-row view, and **7 val PRs exceed 15 units** (dev: 0). |

### A4. Lead and delegation
| knob | where | value | tuned on | set? | what val says |
|---|---|---|---|---|---|
| `max_delegations` | `configs/bases/v5_generation.yaml:68`; `review/lead.py:554`; the floor is exempt (`lead.py:304-315`) | 25 per PR, flat | 8c80a2d; heldout11 rep2 used at most 6 | **S** | **LIKELY WRONG for the tail.** Eligible-but-not-required pairs per PR: median 13 on val, 20 on dev, so fine at the median. But the maximum is **469** (26484) against 120 on dev, and **5 PRs have more than 25 units**. |
| `per_pr_cost_cap` (discretionary only) | `v5_generation.yaml:67`; enforced `lead.py:571-579` | $1.50, about 5 standard jobs reserved per wave | Was $2.00 on smoke4, then $1.50 for heldout12 with no measurement (8c80a2d). Never bound on dev (maximum $0.80). | P | The same pattern: a flat allowance against a pool that spans two orders of magnitude on val. |
| `lead_cost_cap` | `v5_generation.yaml:66` | $1.00 | smoke4 rep5: 5× the $0.200 maximum, sized to "a 184-proposal agenda" | P | **LIKELY WRONG on 6 val PRs** with more than 184 proposals: 649 (26718), 575 (26484), 357, 321, 231, 227. The dev maximum is 143. A lead stopped by a cap appears to lose its PR's arm output: in lead mode the runner collects `arm_responses` from the lead's result (`runner.py:541-542`). That is a code reading, not tested. |
| `lead_token_cap` | `v5_generation.yaml:100` | 1.2M | the 1.2M-tokens-per-$ calibration; dev lead maximum 207k | P | same six PRs |
| `read_agenda` top / `AGENDA_PAGE` | `lead.py:419` / `:207` | 15 rows / 40 | "9 of 11 leads saw 5 of 56 units" | P | 7 val PRs have more than 15 units. On 26484 the first page shows 15 of 66. |
| `max_rounds` / "two waves" | `review/coordination.py:53`; `review/prompts.py:96-98` | 2, not enforced | "what every run so far did" | P | can't judge |
| lead prompt quotes a dev statistic | `review/prompts.py:59-64` | "7% … three specialist arms were never invoked" | heldout11 rep2 | **S** (model-visible) | can't judge (part 2's scope) |
| `max_turns` | `v5_generation.yaml:19` | 40, lead and arms alike | v4 | N for arms, P for the lead | can't judge. On 26484 the lead must read about 76 floor summaries. |
| `max_concurrency` / nested concurrency | `v5_generation.yaml:20`; `src/ape/orchestration/subtasks.py:42` | 4 | memory pressure | N | wall time only: 26484's 76-job floor is about 19 batches |

### A5. Budgets and token twins
| knob | where | value | tuned on | set? | what val says |
|---|---|---|---|---|---|
| `standard_budget_cap` (cheap ×0.5, deep ×2) | `v5_generation.yaml:62` | $0.30 per job | smoke4 rep5, maximum $0.117 | N | fine. Units are size-bounded, and val units are smaller (mean 3.2 targets per unit against 5.0). |
| `COST_HINT_PER_WORK_UNIT` | `agenda/arms.py:59` | $0.05 | smoke4 rep5 median $0.046 | P | fine (smaller units) |
| `TOKEN_HINT_PER_WORK_UNIT` | `arms.py:73` | 60,000 | 2,857 attempts over 9 runs | N | fine |
| `run_total_cost_cap` / token twin | base `v5_generation.yaml:76`, `:105`; val `:29-30`; small12 `:29-30` | $10 base; val $135 / 162M; small12 $25 / 30M | restated per set from `plan` | N | fine. Val worst case $131.20 ≤ $135 and 157.4M ≤ 162M; small12 $24.05 ≤ $25 (B5). |
| token-twin ratio | `v5_generation.yaml:99-105` | 360k / 1.2M / 1.8M / 1.8M / 12M | 1.2M processed tokens per $ over 16 dev v5 runs (6fe2995) | P | can't judge. The issue is general, not set-specific: cache-heavy sessions run 2–3M tokens per $, so the token cap binds first (the fanout4 base re-scaled to 3.5M). |
| fanout4 base | `configs/bases/v5_verdicts_fanout4.yaml:22-27` | $0.17 per job, 600k | fanout4 per-job cost | S | do not carry to val |
| `solo_cost_cap` | `configs/bases/v5_solo.yaml:28` | $1.50 | matched to dev lead cost per PR ($0.77–0.78) | S | can't judge. Val's PR-size tail is wider (max 66 units against 15). |

### A6. Verification, finalization, abstention, findings budget
| knob | where | value | tuned on | set? | what val says |
|---|---|---|---|---|---|
| `submission_verification_policy` | `review/runner.py:240`; `agenda/render_focused.py:314` | None: specialists run `verify_checkable_edits`, the generalist `none` | 33149; about 9 of 43 gold-site abstentions on held-out | S | can't judge |
| checkable arms | `registry.py:240` | 6 compile-gated | registry | N | — |
| `apply_lead_synthesis` | `runner.py:166` | False | pr5_smoke4_rep9: 2 of 6 hits were only in claims the lead removed | S (4 PRs) | can't judge |
| conflict suppression | `review/merge.py:326-363` | disagreeing equal-warrant claims are demoted | heldout11 | N | can't judge |
| `pr_finding_limit` | `runner.py:124`; `merge.py:48`; `review/digest.py:231` | 20 issues per PR, flat | v4 (4fe717d) | N | plausibly binds on val: **7 PRs have more than 15 units**, dev has none. Dev measured roughly 0.7–1.3 generalist candidates per job. |
| `forbid_abstention` / `_FORCED_SUBMISSION_ATTEMPTS` | `runner.py:222`; `review/candidates.py:60` | False / 3 | fanout on 4 held-out PRs (fe7a8a7); the 3 is unmeasured | P | can't judge |
| mute abstention is refused once | `candidates.py:816-830` | 1 | none | N | can't judge |
| `target_verdicts` presses | `runner.py:230`; `candidates.py:676-685` | off; 3 | work-enumeration plan | N | can't judge |
| arm `finding_budget` | `review/arm.py:76` | 20 | — | — | inert: nothing on the v5 path reads it |
| solo `finding_budget` | `review/solo.py:132` | 20 per PR | matches the lead's ceiling | N | same as `pr_finding_limit` |

### A7. Evidence tools
Unless noted, the tools live in `src/ape/tasks/lean_tasks/formal_math/review/context_tools.py` (abbreviated `ct`).

| knob | where | value | tuned on | set? | what val says |
|---|---|---|---|---|---|
| naming_norm `MIN_SUPPORT` / `MIN_SUPPORT_RATIO` / `MAX_CONFLICT_RATIO` | `evidence/operators/naming_norm.py:55-57` | 20 / 0.80 / 0.05 | Ported from the frozen `encard` operator (`naming_contrast.py:24-26`, `SUBJECT = "Set.encard"`), calibrated on 87 of 91. `encard` renames are 33098's gold. 33337's 21 of 121 cannot pass. | **S** | The tool reaches few theorems on either set (B7). The `established` tier fires on **3 of 560** val theorems (dev: 6 of 248) and on 0 of 74 AI theorems. |
| naming_norm `emerging` tier | `ct:711-712` | support ≥20 and ≥3× the runner-up | 33337: 21 against 7, exactly 3.0× (19ef236, 4d655e8) | **S** | **22 of the 25 val rename verdicts** come from this tier (dev: 3 of 9). Val's naming evidence therefore rests on a margin set at exactly one dev case. Precision can't be judged without gold. |
| `leaf_prefix` (first `_` token only) | `naming_norm.py:122-125` | — | `card_`→`encard_` (33098) | **S** | 57% of val theorems (dev: 58%) get no high-confidence subject, so the tool is silent on most of them on both sets. The live `naming-from-statement` and `arm-naming-bar` branches redesign this. |
| naming_norm display | `ct:719`, `:768` | shows 6 counts, returns 8 | none | N | fine |
| proof_profile limits and trend thresholds | `ct:499-563`; `declaration_table.py:251`, `:348` | 8/20 tactics; 0.5% / 2× / 1pt | 33098's `grind` (0222433) | S | inert (never granted) |
| precedent_search k / cap / similarity floor | `ct:209`, `ct:35`; `precedent_index.py:435-468` | 5 / 8 / none | 43e9d88; e86498d (five queries, one of them 33337's) | N | can't judge |
| declaration_search | `ct:335`, `:354` | 5 / 8 files | 43e9d88 | N | fine |
| zulip_search | `ct:35`, `:126`, `:136` | 8 hits / 12 messages / 400-char snippet | 43e9d88; 9bf474e | N | fine |
| result cap on every context tool | `ct:36` | 6,000 chars | 43e9d88 | N | fine |
| lean_verify_edit | `review/base.py:490`, `:380`, `:689` | 20 messages / 50 baseline / concurrency 3 | v2 | N | fine |
| content_search | `src/ape/toolkits/file_system/tools.py:172-192` | 20 / 10 per file / 5 s | upstream APE | N | fine |

### A8. Model-visible dev strings the knob readers found in passing (part 2's scope; listed, not audited)
- `focused_prompts.py:381-382`: 33337's counts (121 / 21 / 7).
- `focused_prompts.py:350`: `encard_le_encard`, 33098's subject.
- `ct:617`: `coe_starProjection_eq_x`, 33337's renamed declaration.
- `ct:180`: "e.g. `toLinearMap`".
- `ct:484-488`: describes 33098's `grind` curve (inert).
- `review_map.py:213-218`: the coercion question states 33337's answer.
- `base.py:481`: `Subgroup.closure_pow_le`, 33401's gold target.
- `registry.py:142-143` and `focused_prompts.py:106`: name `grind`.
- `focused_prompts.py:109`, `:533-536`: the `OrderDual` dual, which is 33145's shape.
- `prompts.py:59-64`: heldout11's "7%".

---

## Part B: what the validation set's gold-free features say

### B1. Size and shape
| feature | dev16 | dev-heldout12 | val60 | val-main50 | val-AI10 | val-small12 |
|---|---|---|---|---|---|---|
| PRs / work units / targets | 16 / 101 / 508 | 12 / 92 / 432 | 60 / 425 / 1348 | 50 / 326 / 1049 | 10 / 99 / 299 | 12 / 43 / 214 |
| units per PR, med / mean / p90 / max | 5.5 / 6.3 / 13 / 15 | 8 / 7.7 / 13 / 15 | 3 / 7.1 / 21 / **66** | 2.5 / 6.5 / 10 / 66 | 3.5 / 9.9 / 34 / 39 | 3 / 3.6 / 7 / 7 |
| largest PRs (units) | 33421: 15, 33294: 13 | same | **26484: 66, 26718: 59** | same | 34906: 39, 36637: 33 | 28649: 7, 30714: 7 |
| largest PR's share of units | 14.9% | 16.3% | 15.5% | 20.2% | **39.4%** | 16.3% |
| PRs with 1 unit / >8 units / >25 units | 4 / 6 / 0 | 2 / 6 / 0 | **19 / 8 / 5** | 17 / 6 / 3 | 2 / 2 / 2 | 2 / 0 / 0 |
| PRs over 15 units (the lead's page, finding limit) | 0 | 0 | **7** | 5 | 2 | 0 |
| targets per unit, med / mean / p90 / max | 1 / 5.0 / 12 / 30 | 1 / 4.7 / 12 / 30 | 1 / 3.2 / 9 / 31 | 1 / 3.2 / 10 / 31 | 2 / 3.0 / 6 / 22 | 1 / 5.0 / 13 / 31 |
| files per PR, med / mean / max | 3 / 5.3 / 15 | 6.5 / 6.5 / 15 | 2 / 4.8 / **59** | 2 / 5.1 / 59 | 2.5 / 3.1 / 7 | 3 / 3.6 / 7 |
| diff `+` lines per PR, med / max | 67.5 / 469 | 67.5 / 469 | 47.5 / 507 | 40.5 / 473 | 73 / 507 | 40.5 / 129 |
| diff `−` lines per PR, med / max | 10.5 / 182 | 13.5 / 182 | 6 / 193 | 10 / 193 | **0** / 39 | 16 / 66 |
| diff chars per PR, med / max | 9.8k / 46.2k | 10.4k / 46.2k | 6.2k / 47.8k | 6.1k / 47.8k | 6.9k / 27.1k | 6.5k / 7.8k |
| units in file-sweep PRs (≥10 units, ≤2 per file) | 52 (51%) | — | 131 (31%) | — | 0 | — |
| generalist prompt chars, med / p90 / max | 9.4k / 25.2k / 30.9k | 9.1k / 24.9k / 30.9k | 9.0k / 16.9k / 31.9k | 9.2k / 18.2k / 31.9k | 8.0k / 15.9k / 22.6k | 8.7k / 22.3k / 30.0k |
| prompts that omit a target | 0 | 0 | 0 | 0 | 0 | 0 |

The two large PRs have **different** causes, and the /13–/14 packer targets neither:
- **26484 (66 units, 4 files)** is the packer cliff in B6: 63 units in one new file.
- **26718 (59 units, 59 files)** is a linter-driven whitespace sweep: one unit per file, and 81 whitespace-only declarations (B2).

small12 contains **no PR over 8 units**, by construction, so it cannot exercise any size-dependent knob.

### B2. Kinds, lifecycle, meta code
| feature | dev16 | val60 | val-main50 | val-AI10 | val-small12 |
|---|---|---|---|---|---|
| subject kinds (% of inventory) | theorem 51.4, doc_comment 11.6, module_doc 9.6, namespace_or_section 9.1, definition 6.9, attribute 5.1, import 3.3, command 1.2, other decl 1.8 | theorem 47.3, doc_comment 15.8, namespace_or_section 14.5, definition 8.1, **instance 4.8**, module_doc 3.7, command 1.6, structure_or_class 1.4, import 1.2, attribute 1.0, **non_lean 0.3**, unknown 0.1 | theorem 52.9, doc_comment 13.3, namespace_or_section 12.3, definition 7.2, instance 5.7, module_doc 3.1 | theorem 27.4, **doc_comment 24.4, namespace_or_section 22.1**, definition 11.0, module_doc 6.0 | theorem 48.1, namespace_or_section 19.6, doc_comment 12.1, module_doc 7.0 |
| lifecycle (%) | added 58.9, modified 37.4, removed 3.7 | added 55.4, modified 36.5, **removed 8.1** | added 46.9, modified 43.5, removed 9.6 | **added 85.3**, modified 12.0, removed 2.7 | added 45.3, modified 43.0, removed 11.7 |
| `renamed` / `moved` lifecycle | 0 / 0 (never emitted) | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| declarations: added / modified / removed | 168 / 124 / 13 | 397 / 344 / **92** | 284 / 340 / 84 | 113 / 4 / 8 | 57 / 46 / 23 |
| removed declarations: moved (same name re-added) / name recurs on a `+` line / `deprecated` on the same line / no trace | 4 / 5 / 1 / 3 | 23 / 30 / 3 / **36** | — | — | — |
| **whitespace-only modified declarations** | **0 of 124** | **120 of 344 (35%)**: 26718 81, 33716 38, 32440 1 | 120 | 0 | — |
| units whose declarations are all whitespace-only | 0 | **85 (20%)**, with 714 eligible specialist pairs | — | — | — |
| declarations with a proof added/modified (modified-lifecycle / added) | 204 (92 / 112) | 420 (131 / 289) | 346 (128 / 218) | 74 (**3** / 71) | 67 (21 / 46) |
| changed files on meta paths (Tactic, Linter, Util, MathlibTest, scripts, docs, non-.lean) | 1.2% | **8.4%** | 6.2% | **25.8%** | 4.7% |
| PRs mostly meta (>50% of files) | 0 | 4 (26484, 29339, 32440, 32668) | 2 | 2 | 0 |
| targets in Tactic/Linter/MathlibTest/scripts | **0** | **90** | 52 | 38 | 0 |
| units wholly on meta paths (declaration arms eligible) | 1 (0) | 26 (14) | 18 (11) | 8 (3) | — |
| target parse_status (semantic / structural / unparsed) | 491 / 17 / 0 | 1326 / 20 / 2 | 1035 / 13 / 1 | 291 / 7 / 1 | 212 / 2 / 0 |

### B3. Eligibility per arm under the tree's rule
Cells are units / sites. Renderable is in parentheses: the subject-kind filter only.

| arm | dev16 | dev-heldout12 | val60 | val-main50 | val-AI10 | val-small12 |
|---|---|---|---|---|---|---|
| api_reuse, correctness, duplication, family_design, generality, naming (identical) | 59/292 (59) | 51/245 (51) | 333/741 (335) | 270/624 (271) | 63/117 (64) | 27/103 (27) |
| proof_golf, proof_idiom | 50/204 (59) | 42/164 (51) | 212/420 (335) | 160/346 (271) | 52/74 (64) | 23/67 (27) |
| docs | 86/398 | 77/340 | 383/991 | 303/783 | 80/208 | 41/143 |
| style | 101/489 | 92/413 | 418/1233 | 322/944 | 96/289 | 43/189 |
| proof_golf units: v5 rule / v4 modified-only rule | 50 / 27 | — | **212 / 90** | 160 / 88 | **52 / 2** | — |
| duplication/generality units: v5 / v4 added-only | 59 / 35 | — | **333 / 174** | 270 / 112 | 63 / 62 | — |
| units with no specialist eligible | 0 | 0 | 7 (1.6%) (`plan`: 6) | 4 | 3 | 0 |
| units with no lean-5 arm eligible | 42 (41.6%) | 41 (44.6%) | 92 (21.6%) | 56 (17.2%) | 36 (36.4%) | 16 (37.2%) |
| units with only style/docs eligible | 42 (41.6%) | 41 (44.6%) | 85 (20.0%) | 52 (16.0%) | 33 (33.3%) | 16 (37.2%) |
| inventory records no arm is eligible for | 19 (3.7%), all removed | 19 | **115 (8.5%)**: removed 109, non_lean 4, unknown 2 | 105 (removed 101) | 10 (removed 8) | 25 |

### B4. What routing would schedule
| arm | dev16 required | dev-heldout12 (`plan`) | val60 (`plan`) | val-main50 | val-AI10 | val-small12 (`plan`) |
|---|---|---|---|---|---|---|
| generalist (floor) | 101 | 92 | 425 | 326 | 99 | 43 |
| naming | 29 | 23 | 96 | 78 | 18 | 13 |
| style | 19 | 16 | 95 | 77 | 18 | 18 |
| family_design | 13 | 9 | 50 | 42 | 8 | 9 |
| duplication | 9 | 6 | 46 | 37 | 9 | 8 |
| correctness | 9 | 6 | 46 | 37 | 9 | 8 |
| generality | 2 | 2 | 19 | 14 | 5 | 7 |
| docs | 8 | 6 | 18 | 12 | 6 | 6 |
| proof_golf | 5 | 3 | 15 | 13 | 2 | 5 |
| proof_idiom | 4 | 3 | 14 | 12 | 2 | 4 |
| **api_reuse** | **0** | **0** | **0** | 0 | 0 | 0 |
| required specialist rows: capped / uncapped | 98 / 135 | 74 | 399 / 489 | 322 / 349 | 77 / **140** | 78 |
| required per PR, med / max; PRs at the cap of 10 | 6 / 10; 4 | 6 / 10; 3 | 6.5 / 10; **12** | 6 / 10; 8 | 8 / 10; 4 | 6 / 10; 2 |
| required rows by grain | family 42, file 19, intro 18, intent 11, site 8 | family 32, file 16, intro 12, intent 8, site 6 | family 144, file 95, intro 92, intent 48, site 18, migration 2 | — | family 26, file 18, intro 18, intent 9, site 6 | family 22, file 18, intent 16, intro 16, site 6 |
| eligible-but-not-required pairs per PR, med / p90 / max (discretionary: 5 standard jobs per wave, 25 in all) | 20 / 90 / 120 | 29 / 100 / 120 | 13 / 90 / **469** | 13 / 71 / 469 | 11.5 / 190 / 294 | 12.5 / 32 / 60 |
| proposals the lead sees per PR, med / max; PRs over 184 | 31 / 143; 0 | — | 22 / **649**; **6** | 22 / 649; 4 | 25 / 357; 2 | — |
| PRs matching an intent keyword | 5 of 16 | 4 of 12 | 17 of 60 | 13 of 50 | 4 of 10 | 4 of 12 |
| units in PRs >8 units that get any required specialist | 33421: 3/15, 33294: 4/13, 33149: 4/12 | — | **26484: 6/66, 26718: 6/59, 34906: 3/39**, 36637: 6/33, 33716: 6/30 | — | — | — |

The val intent matches, read from titles and descriptions only (one reader, not adjudicated):

- **golf:** 28576 (true), 32875 (true), 36645 (true), 34906 (**false**: "further golfs with Claude and Codex").
- **simplif:** 28922 (true).
- **generaliz / generalis:** 27557, 29842, 30108, 30458, 34091 and 30173 (all true); 37352 (**borderline**: "I had to generalise and clean it up").
- **deprecat:** 27124 (true), 35636 (true), 29339 (**false**: a linter for deprecations), 36784 (**false**: "I don't think it makes sense to add deprecations").
- **rename:** 34790 (true).

### B5. `cli plan` (free dry run)
| config | units | floor | discretionary | worst case vs cap | tokens | result |
|---|---|---|---|---|---|---|
| `pr_review_v5_val_2025_06_2026_03_v1.yaml` | 425 | $41.20 (824 jobs) | $90.00 (60 × $1.50) | $131.20 ≤ $135 fits | 49.44M + 108M = 157.44M ≤ 162M fits | **refused** at the reviewed-workspace check: 60 of 60 not prebuilt, and `require_reviewed_workspaces: true`. The agenda and budget report printed first; fanout would be $195.50, rules $182.65. |
| `…_small12.yaml` | 43 | $6.05 (121 jobs) | $18.00 | $24.05 ≤ $25 fits | 7.26M + 21.6M = 28.86M ≤ 30M fits | **refused**: 12 of 12 reviewed workspaces not prebuilt |
| `pr_review_v5_medium_heldout_v5release.yaml` (dev, 12 PRs) | 92 | $8.30 (166 jobs) | $18.00 | $26.30 ≤ $35 fits | 31.56M ≤ 42M fits | ok. 12 of 12 workspaces prebuilt; the plan seals 669 prompt hashes. |

Every plan also warns that no `OPENAI_API_KEY` is set in this shell. That is expected for a dry run.

The three cliff PRs account for 168 floor jobs (138 generalist + 30 required), which is **$8.40 of the $41.20 floor**.

### B6. The packer cliff, simulated (scratch copy of `_pack_bundles`, constant patched in memory)
| budget | val total units | 26484 | 34906 | 36637 | dev total | 33149 |
|---|---|---|---|---|---|---|
| 24,000 (current) | 425 | 66 | 39 | 33 | 101 | 12 |
| 26,000 | 419 | 64 | 36 | 33 | 98 | 9 |
| 30,000 | **328** | **17** | **13** | **14** | 94 | 6 |

Each cliff PR has one hunk shared by almost every target: 76 of 79, 57 of 62 and 49 of 50. Each hunk is larger than the budget, so the first bundle charged to any new unit overflows it. On dev the largest shared hunk is 33149's 17,303 chars, under the budget, so the defect never showed. The number is not really the fix: the renderer no longer prints that hunk (scoped diffs), so the charge itself is wrong.

### B7. naming_norm's verdict on added/modified theorems
This applies the `ct:705-713` logic against one cached snapshot index, `data/code_execute/norms/36a2b22f…` (not each PR's own base), to the first theorem in each target.

| verdict | dev16 (248) | val60 (560) | val-main50 (486) | val-AI10 (74) |
|---|---|---|---|---|
| no high-confidence subject or no population | 58.1% | 57.3% | 54.7% | 74.3% |
| population exists, no bar met | 16.5% | 17.5% | 16.5% | 24.3% |
| name already follows the dominant prefix | 21.8% | 20.7% | 23.7% | 1.4% |
| **established** rename | 6 (2.4%) | **3 (0.5%)** | 3 | 0 |
| **emerging** rename (3× tier) | 3 (1.2%) | **22 (3.9%)** | 22 | 0 |

Mathlib-wide in the same index: 545 subjects have at least 20 members, and 231 of them clear 0.80. Of the 116 theorems concluding about `toLinearMap`, 20 start with `toLinearMap_`.

---

## Knobs most likely to be dev-fitted, ranked

Ranked by the strength of the validation number and the size of what it moves. None of this is a quality result: every item says what the pipeline *would schedule*. Whether it matters needs gold or a run.

1. **Packer budget with /13 hunk-once charging** (`work_units.py:21`, `:63-98`). It was tuned on 33149's 17,303-char hunk, just under 24,000. On val, three new-file PRs with one 24,200–25,169-char hunk pack one bundle per unit: **138 of 425 units (32%)**, which is $8.40 of the $41.20 floor. At 30,000 they become 44 units and the set 328. The charge is for text the /14 renderer never prints.

2. **No substantive-change filter on `modified`** (eligibility via the inventory lifecycle). Dev had **0 of 124** whitespace-only modified declarations. Val has **120 of 344 (35%)**, and **85 units (20%)** consist only of them. Those units carry 714 eligible specialist pairs and 85 floor jobs on a linter sweep (26718, 59 units) and a spacing sweep (33716). This is why the 59-unit PR exists, and the packer fix does not touch it.

3. **Flat per-PR lead allowances**: `max_delegations` 25, `per_pr_cost_cap` $1.50, `lead_cost_cap` $1.00 sized to "a 184-proposal agenda", `read_agenda` 15 rows. The dev maximum is 143 proposals and 120 discretionary pairs. On val, **6 PRs exceed 184 proposals (max 649)**, discretionary pairs reach **469**, **5 PRs exceed 25 units** and 7 exceed 15. A lead that pauses on its cap appears to lose the PR's whole output. The median val PR is well served, so this is a tail problem.

4. **`_BOTH_LIFECYCLES` and the `{added, modified}` gate** (`arms.py:89`). The widening came from smoke4 gold (33066/33098). On val, golf/idiom are eligible on 212 units against 90 under the v4 rule, and **52 against 2 on the AI stratum**. Duplication/generality are eligible on 333 units against 174, contradicting their "new declaration" remit. Meanwhile **92 removed declarations** (dev: 13), 36 without any trace on a `+` line, have no eligible specialist, so a deprecation ask has no owner.

5. **The `_ONCE_PER_PR` introduction rule, and filling the cap of 10 in hash order** (`routing.py:78-81`, `:97`, `:170`). This was set on 33149's 56 introductions. On val one PR holds **49** units with a new declaration and gets one required duplication and correctness job. The cap binds on **12 of 60** PRs, and on the big ones it lands on 6 of 66 units (26484) and 3 of 39 (34906). `MAX_INTENT_REQUIRED_PER_PR` (12) is dead.

6. **naming_norm bars** (`naming_norm.py:55-57`, `ct:711-712`). The 0.80 / 20 / 0.05 bars come from the `encard` population (33098); the 3× tier sits exactly at 33337's 21 against 7. On val, `established` fires on **3 of 560** theorems and the dev-calibrated `emerging` tier carries **22 of 25** rename verdicts (dev: 3 of 9). The AI stratum gets 0 of 74. Coordinate with `naming-from-statement` and `arm-naming-bar` before touching it.

7. **Intent keywords** (`components.py:48-57`). Precision is about 4 in 5 on both sets, so this is not worse on val per se. But val adds negation (36784) and authoring history (34906, 37352), and the 34906 false match puts **70 uncapped required golf/idiom rows** on a 39-unit AI PR.

8. **Meta and Tactic code was never in dev.** Val has **90 targets** in Tactic/Linter/MathlibTest/scripts (dev: 0) and 26 units wholly on meta paths, 14 of them with the declaration arms eligible. The AI stratum is 25.8% meta by file. Every arm prompt and naming_norm population was tuned on library mathematics. This can't be judged without a run, but nothing about it has been seen.

9. **`pr_finding_limit` of 20 per PR** (`merge.py:48`). It was never near binding on dev (max 15 units). **7 val PRs exceed 15 units.** Plausible, unmeasured.

10. **docs required only on module-doc sites, once per PR** (`routing.py:59`, `:78-81`). This was set against the doc-heavy dev controls 33304/33315. On val, 34 PRs change a doc-comment (213 records) but docs is required on 18. That is only an observation until gold says whether the asks are there.

**Fine on the validation features:**
- `standard_budget_cap` and the cost/token hints: val units are smaller.
- The run-total caps: restated per set, and they fit.
- `MAX_SKELETON_ROWS` and family truncation.
- Prompt sizes: nothing is omitted.
- The `_stem` families.
- The file-grain threshold.

**Inert:**
- `DEFAULT_CENTRAL_RANK`
- `MAX_INTENT_REQUIRED_PER_PR`
- the proof_profile grant and thresholds
- arm `finding_budget`

**Smaller notes:**
- Neither val config can reach `--execute` today: all 60 reviewed workspaces are unbuilt, and the plan refuses on them. Everything above was reached through the plan's report and the tree's functions directly.
- small12 excludes PRs over 8 units, so items 1, 3, 5 and 9 can be tested only on the full 60.
- The val release manifest records `"split": "test"`. That looks like a label carried over from the test-set build; check it before anything gates on `split`.
