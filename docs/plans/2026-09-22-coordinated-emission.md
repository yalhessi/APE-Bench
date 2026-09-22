# Where generation fails to align with maintainer obligations — and the one hole worth working on

Written 2026-09-22 in the worktree `abstention-capture`, after the user asked whether the four holes I proposed
(taxonomy, grain, shape, evidence) and a per-obligation ledger were worth building, or whether there were better
ideas. Five independent audits ran against the record and the committed artifacts, then a read-only stress-test of
the surviving design against the code; this plan is what survived. Every count is one release (`dev-medium-0.3.0`,
40 eligible obligations, 13 PRs) and is a description of that corpus, not a rate. Nothing here is selection: no
ranking, threshold, channel or gate is proposed, and the ordering rule is generator first.

## Context — what the scrutiny did to the four ideas

**The ledger already exists. Do not build it.** `src/mathlib_review/analysis/request_groups.py` (2026-09-08, plan step
10) is a hand-audited, Codex-cross-classified table of all 35 maintainer request groups over the 40 obligations, each
with `answerable_arm_ids`, `required_scope`, `required_information`, `required_output`; `obligation_capability.py`
adds a scope × capability lattice. Obligation-weighted: `required_output` single_edit 18 / **patch_set 11** / rename
8 / deletion 3; `required_information` diff 17 / repository 13 / **convention 10**. Its module docstring states the
finding this plan acts on: *"A group needing `patch_set` cannot be resolved by an arm confined to one work unit,
however well briefed."* Unacted on for two weeks.

**Taxonomy is not a hole.** 42 of 43 claims fall inside some arm's brief; the one that does not (33145 "swap the
sides of the iSup/iInf equalities") is also the release's only obligation with zero `change_ids`. No missing concern
family; all five audits agree an eleventh arm is not the fix. What diverges: (a) 8 of 43 asks are conjunctions
across two or three briefs — the shape hole below — and (b) **dispatch**: the arm whose remit covers a gold site is
*proposed* at 22 of 22 obligations and *executed* at 12 of 22, identically in all three reps; the lead prunes it at
10 ("not selected by the lead"). My todo `routing-remit-and-silence.md` says "0 of 22 without an on-concern arm";
that counted proposals including pruned ones and is wrong as a headline (W1).

**Grain (cross-unit authority) is fixed and the record is stale.** Under the shipped 0.5.0 packing 3 of 42 anchored
obligations span more than one unit, all PR 33149; 32 of 38 request groups sit wholly inside one unit; PR 33145's
six-theorem `Dense` family — the motivating example of `batching-work-units.md` — is now one unit of 12 targets.
12 of the 15 multi-declaration asks are fully visible to one arm.

**Shape is the hole: reachable and still unsayable.**
- 11 of 40 obligations need `patch_set` or `deletion` emission. Counted from every run's own responses: **60 runs,
  3,411 candidates, 0 carrying a `patch_set`** (the record's "1,660 null keys" and "5,308 candidates" count the same
  fact in other files). Held-out: 4 obligations need it, 0 ever resolved in 3 reps.
- The three obligations with the most judge issue-matches and *zero* resolution-matches in the corpus — `e83e6544`
  (rename both AND reprove via OrderDual: 20 issue / 0 resolution over 20 audits), `57bcc9fd` (import ToFun AND
  attribute 11 AND delete 13: 10/0), `bd8a8d8c` (name the pair AND derive the dual: 6/0) — are all
  coordinated-across-declarations; they alone are 36 of the corpus's 57 issue-without-resolution rows from
  never-resolved obligations.
- Not a judge artifact: P(resolution | issue) is 0.79 overall and uniform multi-site asks resolve (`64e1164f` 16/39;
  33149's 19-site axiom obligations 163/165). The discriminator is heterogeneity of transformation, not site count.
  Not a schema ban either: 189 of 5,308 candidates carry more than one `change_id`.
- **Five mechanisms**, each independently sufficient, verified against the code: (1) `patch_set` granted to one arm
  of ten, `family_design` — 182 responses across every committed run, 0 candidates; (2) `_patch_set_workspace`
  does `Path(self.target_workspace)` on a `WorkspaceInfo` (`ape/tasks/base.py:205`; every other consumer uses
  `.path`, e.g. `review/base.py:318`) → `TypeError` on first real use; (3) **new, unrecorded:** `patchset.apply`
  applies a declaration-mode edit by `text.replace(declaration_name, new_declaration, 1)` (`patchset.py:160-167`),
  not by the declaration splice the single-edit path uses (`review/base.py:336-354`), so even past (2) it rewrites
  the first occurrence of the name — possibly a docstring — and compiles garbage; a test pins the substring
  semantics; (4) the `SUBMISSION_CONTRACT` JSON template omits the field under "This supersedes any field list
  above", so `family_design`'s own prose about it (`focused_prompts.py:553-562`) is overridden 2,400 chars later;
  (5) `patch_set` is recorded in `arm_responses.jsonl` and dropped at `candidates_from_response`, so the judge never
  sees the edit. Also verified: patch sets are **file-confined, not anchor-confined** (`patchset.validate`,
  `arm.py:137-150`), which the 2026-09-08 plan flagged as the precondition for widening the grant.
- Nothing in `dead-ends.md` covers it. `batching-work-units.md` names it open and asks "authority, judging, or
  emission?" — the audit answers **emission**.

**Two honesty notes on the count.** The 11 obligations are **6 maintainer comments**; two (both PR 33098) expand to 7
obligations, so outside 33098 the shape is 4 of ~26. And the ledger *under-counts* the shape it was built to count:
it has `e83e6544` as `rename`, dropping the `OrderDual` conjunct; an independent hand pass and the ledger agree on
only 3 coordinated groups, union 9. A second classification pass comes first (W1).

**Evidence (convention) is the second hole, disjoint from the first: 21 of 40 in the two gaps together.** On
held-out, **7 of 24 obligations rest on evidence no granted tool can produce**; 6 of the 7 are warranted by a
*statement about the library*, and 5 of the 7 are census questions of a shape `naming_norm` does not compute —
name *form* (suffix, prime, namespace move: 2), dual-pair completeness (1), statement orientation (1), mechanism
availability (1). Not a corpus gap: 58 review comments ask for dot notation and 10 to avoid a prime, Zulip has
threads titled for both, and `@[to_fun]`'s docstring at 33117's base states the ask. Not an asking gap: 33294's arm
issued "dot notation naming convention rename" six times and got 244 one-line messages over 134 threads back. Not a
broken operator: `naming_norm` warranted 3 of the 4 obligations a census *could* warrant. Missing: **census operators
of more shapes** in `naming_norm`'s form, and a retrieval unit for stated norms that returns a norm rather than a
scatter. §D2 of `pr-review-v5-principled-design.md`, never built. (Where audits disagreed on precedent supply —
"182/182 non-empty" against "0 of 306 distinct hits mention either convention" — the one that read the hits is right.)

**Verdict on the four ideas.** Ledger: exists; reuse it and re-audit its coordinated column. Taxonomy: not a hole; the
dispatch count is a correction. Grain: fixed. **Shape: the one to work on.** Evidence: real, second, larger design.

**Why shape before dispatch.** Dispatch's ceiling has a measurement: fanout gave every arm every slot and recovered
2 of 10, exactly what `lead` did (`dead-ends.md`, "Specialists as the coverage floor"). And W0 below says it directly
on the subset that can be checked for free: at the 3 pruned obligations the unpruned run covers, the pruned arms ran
and filed nothing, 7 cells of 7. Shape's ceiling is **unmeasured** because the channel crashes on first call — 0 of
3,411 is not evidence a working channel was offered and declined. The two holes overlap on 2 of the 4 held-out
`patch_set` obligations, so they compound rather than substitute.

## The work

### W0 — the dispatch discriminator (done as far as it is free)
The audit proposed reading `pr5_F_fanout_heldout12_v2_rep1`; that run is **aborted** on disk — sealed plan, pool and
agenda, no `arm_responses.jsonl` — exactly as `operational-floor.md` records. The only unpruned run with responses is
`pr5_F_fanout_stage1_rep1` (PRs 33145, 33337, 33421, 33315), covering 3 of the 10 pruned obligations. Read directly
from its `arm_responses.jsonl`: **every on-concern arm the lead prunes in the A reps ran to `success` unpruned and
submitted nothing — 7 of 7 arm-cells.**

| obligation | pruned on-concern arms | unpruned, in fanout |
|---|---|---|
| 33421 `38e722` factor out the repeated `Tendsto (2·)` argument | api_reuse, duplication, family_design | 3 ran, 3 abstained |
| 33145 `7fef91` provide `Dense.ciInf'` by duality | api_reuse, duplication, family_design | 3 ran, 3 abstained |
| 33145 `e8e028` `by_cases` refactor of the `ciSup` proof | style | 1 ran, abstained |

No remit floor. Caveats: 3 of 10, one rep, one release — and all three are coordinated design asks, i.e. the shape
hole, so this subset was the one most likely to come out this way. The other 7 need a run and are not free.

### W1 — corrections to the record and one reader defect (docs + one test; no spend)
- `routing-remit-and-silence.md`: headline → proposed 22/22, **executed 12/22**, all three reps; W0's result; fanout
  bounds un-pruning; a remit floor is not this plan's work.
- `batching-work-units.md`: motivating example stale (33145 one unit; 3/42 span, all 33149); item 1 done; "authority,
  judging, or emission" → emission; add mechanisms (3) substring `apply` and anchor confinement to item 2.
- `dead-ends.md`, deferred-by-choice: **Track 1.C's second half and the oracle ladder.** The 2026-09-08 plan proposed
  extending `patch_set` to the proof arms after grouping; grouping landed (`12a3939`), the extension did not; Track 1
  was replaced by the oracle ladder, whose own self-critique found it rested on one PR (33098; 2 of 35 groups). Neither
  is recorded anywhere. **Reopens:** now, as W2, under the same plan's correction (`:1376`, anchor confinement first).
- **Re-audit `request_groups.py`'s coordinated column**: fold `obligation_capability.py`'s axis in, no third table
  (`test_pr_review_v4_no_duplicate_helpers.py` pins the count downward), disagreements per row as the module already
  does for Codex. Gold-derived, evaluation-only, `test_none_of_this_reaches_a_prompt` unchanged. Decides whether W2's
  population is 11 or nearer 4.
- **`buckets` misreads fanout runs.** Fanout arms are top-level tasks, so every `delegations.jsonl` row has
  `status: None`; `_cell_state` (`report.py:929-943`) reads that as "ran and did not come back" → every obligation
  `UNTOUCHED`, printed beside `judge=hit` on both hits of `pr5_F_fanout_stage1_rep1`. Fix: refuse a run whose
  delegation rows carry no status, or read status through `arm_responses.jsonl` (all 173 rows `success`); pin with a
  test on that run that the coarse bucket never contradicts the judge. Same class as the rules-file trap "a closed
  vocabulary silently filters".
- Release drift noted: four audits measured 0.3.0 (the A reps' release), one 0.5.0; numbers travel with their release.
- Not counted as progress: `issue_recall_reachable` keys on judgment-level `concern_labels` and flips 14 of 40 verdicts;
  a measurement repair for `judge-and-measurement.md`, done separately.

### W2 — coordinated emission: six small commits, each with the suite green
Picks up `batching-work-units.md` item 2 and Track 1.C's second half, under the anchor-confinement correction. Every
new or rewritten test **constructs the real `ReviewArmData` / `ReviewArmTask` / `WorkspaceInfo`**: the existing
`patch_set` tests build the task with `__new__` and a `SimpleNamespace` (`test_pr_review_v5_patchset.py:155-200`;
`test_pr_review_v5_accounting_paths.py:20-33` assigns a *string* to `target_workspace`), which is the fake the rules
file warns stayed green while the code it covered was not, and is why (2) and (3) survived.

1. **`_patch_set_workspace` reads `.path`.** `candidates.py:399-403` → `self.target_workspace.path if
   self.target_workspace else None`, the idiom at `review/base.py:318`. Rewrite the accounting-paths test with a real
   `WorkspaceInfo(name=..., path=tmp_path, commit_hash=..., repo_url=...)`.
2. **One declaration splice for both edit paths.** Factor `review/base.py:336-354`'s declaration-mode body into a
   public `splice_declaration(src, name, new) -> (Optional[str], error)` (public: `test_package_boundaries.py` pins
   private cross-boundary imports); `_edited_file_code` calls it; `patchset.apply` / `verify` take the splice as a
   callable (module stays workspace-free) and `_verify_patch_set` passes it. Tests: the two that pin substring
   semantics move to the real splice; add "declaration mode replaces the whole declaration, not the first occurrence"
   with a docstring mentioning the name earlier; add "empty `new_declaration` deletes the declaration" (`deletion` is 3
   of the 11 shapes; `PatchEdit.mode()` already permits it).
3. **Anchor confinement.** `PatchEditSubmission` (`candidates.py:99-108`) gains `change_id: Optional[str]` defaulting
   to the candidate's `primary_change_id` — optional so the recorded tool schema stays replayable (see W3); make it
   subclass `ProposedEditSubmission`, which is byte-identical today. `PatchEdit` gains the field; a pure
   `anchor_problems(patch, *, change_ids, paths_by_change, subjects_by_change)` beside `validate` refuses an anchor
   outside the candidate's `change_ids`, a path that is not that anchor's file (the rule `normalize_candidate_edit`
   already applies at `:225-230`), and a declaration-mode edit whose name resolves to a unit target the candidate did
   not claim. Span edits keep file confinement (an import line has no declaration anchor; say so). Called from
   `_patch_set_error` after the `change_ids` suffix normalisation. Tests: three refusals plus an end-to-end
   `submit_candidates` refusal on the pattern of `test_pr_review_v4_focused_task.py`.
4. **The grant, by a gold-free rule that two tests will state.** `registry.py`: `patch_set=True` such that
   `patch_set_arms() == checkable_arms()` — *a coordinated patch's only warrant is one compile of every touched
   file, so the grant is exactly the arms whose claims a compile can settle*: `correctness`, `duplication`,
   `generality`, `proof_golf`, `proof_idiom`, `api_reuse`, and `family_design` as today. The evidence that this is
   the right set goes in the commit body, not the code: the `answerable_arm_ids` of the 6 `patch_set` and 3
   `deletion` groups union to exactly the checkable set; `family_design` has 182 responses and 0 candidates.
   `api_reuse` is inert until routing sends it (0 invocations ever) — the grant is harmless there and the rule stays
   clean; not the `migration_consistency` case, since it has a spec and prompt. Rewrite
   `test_a_patch_set_arm_is_one_whose_scope_is_a_group` (`== {"family_design"}`) and
   `test_only_the_structural_arms_may_carry_a_patch_set` to state the new rule; their premise — "granting it broadly
   turns a bounded capability into a licence to rewrite whatever the arm was shown" — is what step 3 removes, and
   every arm now holds units of up to 12 targets. `test_every_patch_set_arm_is_a_registered_spec` holds.
5. **The contract says `patch_set`, to granted arms only.** `render_focused.py:52-99`: `{patch_set_field}` in the
   JSON template and `{patch_set_clause}` after "State the change, not the impression", filled when
   `spec.spec_id in patch_set_arms()`, else `""` — ungranted arms' prompts stay byte-identical. Move the "Coordinated
   fixes" paragraph out of `FAMILY_DESIGN_SYSTEM` into the clause verbatim (already proven leak-free); add one
   sentence each for the `change_id` anchor and `new_declaration: ""` deletion. Do **not** lift wording from
   `request_groups.py` `why` strings or `obligation_capability.CLASSIFICATION` — `test_none_of_this_reaches_a_prompt`
   compares against them. Give `CandidateSubmission.patch_set` a `Field(description=...)`. Bump
   `FOCUSED_RENDERER_VERSION` to `focused-prompt/4`. Extend
   `test_the_v4_submission_contract_supersedes_the_v2_field_list` to assert `"patch_set"` after the contract start for
   granted specs and absent for `naming`/`docs`/`style`. Also run `tests/mathlib_review/test_supplements_name_real_fields.py`
   (it exists there, not under `tests/datasets/`): it asserts no supplement names a field absent from
   `CandidateSubmission` and that every rung routes a discarded compiling edit to `rejected_alternatives` — the moved
   "Coordinated fixes" paragraph and the new `change_id` wording must satisfy it.
6. **Deferred until one emission is observed — let the judge see the patch.** Pairing already reaches a multi-site
   finding: the `anchor` tier pairs on candidate `change_ids` ∩ gold `change_ids` (`judge/runner.py:230,245`;
   `finding_from_candidate` carries all of them), so `issue_match` is scorable today. `resolution_match` is not,
   because the judge renders only `proposed_edit.new_declaration` (`runner.py:199-206`) and `patch_set` is dropped at
   `candidates_from_response`. Cost when done: `patch_set` on `CandidateClaim` (outside the identity payload, like
   `concern_tags`), `ReviewFinding`, `ReviewIssue`; thread through `merge.py`, `digest.py`, the judge rendering.
   `ReviewFinding` is sealed over its whole dump, so every *re-finalized* `finding_id` changes; committed
   `findings.jsonl` are not rewritten, no test pins a hex id, and the judge cache keys on `candidate_source_sha256`.
   `ReviewIssue.aggregation: per_pattern` needs **no** change — collapsing N findings into one issue is the digest's
   job and selection-adjacent; a coordinated candidate is one finding with the union `change_ids`.

`verify_frozen verify` after 3, 5 and 6. Not pulled in: `batching-work-units.md` items 4 (authority) and 5
(exact-closure cap) — unnecessary for the 12 asks now inside one unit; the 3 cross-unit asks (33149's 19/19/22-unit
deletions) stay out of reach and the write-up says so.

### W3 — measure it
- **Free, no model:** the unit tests above; a local dry run of `submit_candidates` with a hand-written 33145 patch set
  against a built reviewed workspace, checking a `lean_compile_patchset` verification artifact lands.
- **Replay can test part of it, with two caveats stated.** `--cut turn=1` reruns a recorded session from its prompt
  with *today's* tool implementation, so steps 1–4 are exercised; the recorded `submit_candidates` schema already
  lists `patch_set` (it is on `CandidateSubmission`), so the model was shown the field in every recording and only
  the prompt omitted it — a `prompt_replacements` condition inserting step 5's clause reproduces the contract on old
  prefixes. Caveat one: step 3's `change_id` makes today's schema differ → `tool_drift` recorded, the model sees the
  old schema, edits default to the primary anchor. Caveat two: `turn=1` re-samples the investigation, so it is a cheap
  rep on selected sessions, not a decision replay; it costs model spend, no judge. Select the units holding `e83e6544`,
  `57bcc9fd`, `bd8a8d8c` by `invocation_ids`. **Timing is the user's call:** a replay pins the model of the run it
  replays, so this is runnable only before the provider switch; after it, only a rep.
- **The rep: ordinary, unforced, three of them**, on the held-out set under `focused-prompt/4`. Forcing is ruled out as
  a design; it is kept only as the fallback that separates "won't use the channel" from "can't", on two PRs, if the
  unforced reps emit zero patch sets and the user wants that distinction.
- **Pre-registered reading, readable from `arm_responses.jsonl` before any judge:** (i) any candidate carrying a
  `patch_set` — 0 of 3,411 is the baseline, one is a result; (ii) `lean_compile_patchset` artifacts; (iii) at the
  units of `e83e6544` / `57bcc9fd` / `bd8a8d8c`, did the granted arm emit one; (iv) control-PR emission in the 0–1 band —
  a patch must compile in every touched file, a higher bar than one edit; (v) whether only PR 33098 moves — 7 of the
  11 are two comments on it. Then the judge, with step 6 built if (i) is non-zero: does `resolution_match` leave 0.

### Falsifiers, stated before spending
- Granted arms, with the clause provably in their prompt (`prompt_sha256` at `/4`) and the field in their schema,
  emit **zero** patch sets in three unforced reps. Then the schema was never the constraint — the arm can already
  voice these asks in prose (issue_match 20/10/6) and declines to build them — and the `abstention_detail` at those
  cells says whether it is knowledge (33117's `to_fun`) or bar. The most likely falsifier, and why the reps are
  unforced.
- They emit compiling patch sets and `resolution_match` stays 0. Then the loss is judging or design;
  `batching-work-units.md`'s question resolves against this plan and step 6 is the next thing.
- W1's re-audit shrinks the coordinated population to 3–4. Then the hole is real but single digits, and the convention
  hole (7 of 24, structurally broader) becomes the better per-unit-work bet.
- Only PR 33098 moves. Then the result is about one PR and is reported as one.

### W4 — the convention hole (design, after W3 is read)
Census operators of more shapes — name form, counterpart completeness, statement orientation, mechanism
availability — in `naming_norm`'s form (declaration or proof in; counted population over the base snapshot with a
verdict out; `repository_measurement` tier), and a retrieval unit for stated norms that returns a norm. §D2, never
built. `dead-ends.md` "Linter-as-convention-oracle" and "Precedent priming, Mode A" constrain the sources: one
corroborating source among ≥ 2, never the oracle. Not designed here; W3 says whether the arms *use* a new capability
before a second one is built.

## What must not be done
- No ranking, keep-rule, threshold, channel or gate over existing findings — `dead-ends.md` "Publication as selection".
- **No joining two existing candidates into one `ReviewIssue` after the fact** (`digest.py` `per_pattern`, `merge.py`
  keyed on `requested_change`): that composes what a maintainer sees out of what was already produced. The
  generator-side form — one candidate carrying the whole ask — is what W2 builds.
- No un-pruning wholesale and no forcing as a design — "Specialists as the coverage floor".
- No new per-obligation ledger; no routing keyed on gold labels; no eleventh arm; no prompt iteration on the silent
  arms (they asked the right question and got the wrong unit back).
- No `patch_set` grant to an arm with no spec or prompt (`plans/STATUS.md`, the `migration_consistency` lesson); no
  second confinement path — anchor confinement extends `normalize_candidate_edit`'s rule.
- Convention sources belong to W4, not W2.

## Risks
- **Statement gate skipped on the patch path**: `_verify_candidate_submission` verifies a `patch_set` before the
  checkable-family checks, bypassing `_statement_gate_error`, so a `proof_simplification` patch could move a
  statement unnoticed. Step 3's anchors make a per-edit gate possible; record as a follow-up, do not widen the series.
- **Cross-file patches cannot verify**: `patchset.verify` compiles each file against unpatched `.olean`s, so 33337's
  two-file rename pair stays unreachable; units are one file anyway.
- **Fallback workspaces**: `verify` runs in `target_workspace.path`; a run that fell back to the source-only overlay
  hits the `Unknown constant` cascade the rules file records. `plan` says which.
- **Control emission**: six arms gain a rewrite capability; bounded by `MAX_PATCH_EDITS=32`, single-file units, the
  compile of every touched file, and an untouched abstention contract. Read `silent_pr_emission` per rep against the
  0–1 range, never as a rate.

## Verification
- `ape/bin/python -m pytest tests -q` green at every commit; `ape/bin/python -m
  src.mathlib_review.release.verify_frozen verify` ok after W2.3, W2.5, W2.6.
- The grant reaches the task and nothing else does: `patch_set_arms()` lists the checkable set; after `cli plan`,
  `"patch_set"` is in every granted arm's rendered system prompt and in no other's — an ungranted arm's
  `rendered_system_prompt` byte-identical to `develop`'s. `test_every_patch_set_arm_is_a_registered_spec` and
  `test_none_of_this_reaches_a_prompt` green.
- Anchor confinement refuses an edit whose declaration the candidate did not claim, with a message naming the anchor.
- Declaration-mode patch edits splice the declaration, not the first occurrence of its name; deletion works.
- `patchset.verify` against a built reviewed workspace produces a `lean_compile_patchset` artifact on a hand-written
  33145 patch set (host-local, as the focused-task test does).
- `buckets` on `pr5_F_fanout_stage1_rep1` refuses or agrees with the judge on both hit obligations.
- W3's reading is the list above; nothing in it is computed after seeing the run.
