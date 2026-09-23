# Dead ends, retracted conclusions, and deliberate deferrals

The threads this project tried and stopped, with the evidence that stopped them and what would
reopen each. Read it before starting a direction; if a proposal is on this list, say so and cite
the entry. When a thread is abandoned, its entry is written *before* its branch is deleted.

Format: **what** (when) — what was tried · the evidence · why it stopped · **reopens if**.
Numbers are as measured at the time; the write-ups they come from are in `docs/research/` and
the commit bodies. `docs/PROJECT-STATUS.md` §11 lists what is planned and not started.

## Abandoned or superseded designs

- **Δ revealed-preference framing** (Jun 2026) — score reviewers against
  `diff(first_pushed_head, merged_head)`. Authors make the changes, not maintainers; Δ conflates
  author taste with maintainer judgment; maintainers deliberately under-report. Dropped as a
  framing; the snapshot and collector plumbing stayed, `review_quality_score` did not. **Reopens if:**
  never as ground truth.
- **Community-guidelines injection, "statute"** (2026-06-18) — `lean_pr_review_guidelines` appends
  distilled Mathlib guides. Null at N=115 on two models (gpt_5.4 10 vs 12 covered, gpt_5.2 32 vs 36);
  the 30-PR "re-orients toward conventions" reading did not replicate. **Reopens if:** measured as
  directive V3-only injection with three reps; a large effect is already ruled out.
- **Selection from artifact-only signals** (2026-06-19 → 06-22) — pointwise selector AUC 0.62
  overall but V2 ≈ chance (0.57); listwise ≈ same; agentic tool-using selector 0.56 on V2 while
  genuinely investigating (113 compiles, within-PR spread 76/100); crude centrality within-PR 0.55;
  diff-only legibility 0.50; workspace-grounded legibility 0.56 (real but narrow: the convoluted-proof
  slice). *Provisional* negative: the signals given do not capture which valid V2 change a maintainer
  raises. **Untried:** LLM-rated centrality within a PR, thread-plan / sibling coherence, per-reviewer
  conditioning, precedent-based selection. Do not run another selector on artifact-only information.
- **Idiom checker as the finder of missed golfs** (2026-06-22) — precise (on-target 20–39%), but
  flagged nothing on 4 of 6 target proofs: a legible non-idiomatic proof carries no internal tell.
  **Reopens if:** retrieval by *mechanism* exists (a base-commit `Mathlib/Tactic/**` docstring index;
  arms today search only identifiers lifted from the diff).
- **Snippet verification of findings** (Jun) — a self-contained `example` compiled against base
  oleans could not see PR-new declarations *and* over-counted (an isolated example compiles when the
  in-file edit would not). Replaced by in-file splicing, `lean_verify_edit`, and declaration-targeted
  edits. Part A — building changed modules for cross-file dependencies — was never built; the small
  set hit no cross-file failures. **Reopens if:** multi-file PRs need verified edits.
  **Reopened 2026-09-12.** They do, and the failure is not a missing feature but a false statement:
  the review overlay applies δ₀ to source only, `lean_verify`/`lean_verify_edit` compile against the
  base `.olean`s, so a lemma the PR renames in a sibling file is an `Unknown constant`, and
  `_attribute_errors` then tells the model *"the file does not compile as it stands"*. On the 12-PR
  held-out `lead` run, **41 of 321 arm sessions** received such an error; 16 became `broken_build`
  findings on PRs that all build, 4 of them `published`; all 10 resolvable "missing" names were
  introduced by the PR itself. The naming arm on 33337 burned 2–5 verify calls on it in 5 of 10
  reps. Filtering by identifier cannot fix it — the stale sibling cascades into `simp made no
  progress` / `unsolved goals`. **Closed 2026-09-12** on branch `verify-reviewed-state`: a *reviewed
  workspace* per episode — `workspaces/<base>+<fp>`, the base snapshot, the diff, and the changed
  modules rebuilt by a targeted `lake build` in a real copy of `.lake/build` (hardlinks are not an
  option: Lean truncates `.ilean` in place; NFSv3 has no reflink; measured 585 s copy + 67 s build on
  33337). `prebuild --reviewed` makes them, `plan` reports which episodes lack one,
  `require_reviewed_workspaces` refuses a run without them. Built for all 12 held-out PRs on
  2026-09-12 (144–997 s each, 74.9 min sequential, 34 GB; the driver is import-path length, not
  file count) and required by both held-out configs; smoke4's four PRs are not built. On 33337 the
  `Unknown constant` transcripts went 19–68 per rep → 0 (reps 11–12), phantom `broken_build` 2 → 0,
  recall unmoved. Design, scope and the hardening that followed a verification pass:
  `docs/research/reviewed-workspaces.md`. The held-out rerun is still the check that the 16
  compile claims vanish across the set.
- **Specialists as the coverage floor** (2026-09-14) — *"the generalist is the floor and the
  specialists get pruned; force the specialists to be the floor instead"*. Tested at its ceiling
  rather than by tuning: `routing_mode: fanout` on 4 held-out PRs gives every specialist every
  eligible slot with no lead and no pruning — 140 specialist jobs, 173 total, $14.72 billed. It
  recovered **2 of 10 obligations, exactly what `lead` recovered on the same PRs, against `solo`'s
  4**, at `gold_alignment_rate` 0.041 (2 of 49 candidates). The mechanism is the point: the
  specialist submit-rate was **16%, against lead's 19%** — unlimited slots did not raise output,
  and **104 of 136 abstentions were `already_correct`**. `correctness` filed nothing in 11 jobs and
  `family_design` nothing in 11, the two arms that were the strongest candidates for being starved.
  Silence is a judgement about the code, not a scheduling artifact, so more slots buy more
  abstentions. Two corrections fell out: fanout costs **$0.085/job against lead's $0.040** (arms are
  top-level tasks, so they lose the nesting/caching benefit and all spend lands in the `lead` bucket
  with `nested_billed: 0.0`), making the full 12-PR fanout ~$111 rather than the $70.45 the agenda
  projects; and fanout is *not* a precision disaster — it emitted 1 candidate on the control, not
  the pile predicted. **Reopens if:** the reason arms decline changes. Reading the abstention details
  at gold sites, the declines are three different things and only one is a bar problem: the right arm
  was never asked (33145 wanted a *rename* and the arms present were duplication/api_reuse/style,
  each correctly reporting nothing in its own concern), an evidence bar refused a correct instinct
  (33337 `naming` considered the exact rename and `naming_norm` returned `insufficient_evidence` —
  that obligation was never hit by any condition), or the arm lacked knowledge (33117 `family_design`
  judged the family balanced; the ask was to use `@[to_fun]`, which it does not know about). Only the
  second is scheduling-adjacent, and it is a threshold question, not a floor question.
  **Amended 2026-09-14, same day:** the conclusion stands -- more slots do not help -- but the
  cause stated above was wrong. Re-running the identical 4 PRs with `forbid_abstention` (arms
  refused an empty submission) took **issue recall 0.20 -> 0.50 and location 0.80 -> 1.00**,
  strictly dominating: 3 forced-only hits, 0 unforced-only. The arms were not short of findings,
  they were withholding them -- forced, `naming` produced `Dense.upperBounds_image`, character
  for character the rename gold asked for, on an obligation it had abstained on. And the bar was read as
  a *volume filter, not a quality filter*, on the ground that the suppressed candidates align
  with gold at the same rate as the kept ones (marginal 5 aligned / 130 extra = 0.038, against
  0.041 unforced). The cost is why this is still not a design: control emission went 1 -> 36
  findings on a PR where maintainers asked for nothing, about 12 spurious control findings per
  real obligation recovered.
  **Retracted 2026-09-22, the quality half only.** 0.038 is *five candidates*. Fisher exact on
  2/49 against 5/130 gives p = 1.0, which is no power rather than equivalence; the marginal
  Wilson interval spans 0.4x to 2.1x the kept rate, and on the adjudicated denominator (only 31
  of 49 and 65 of 179 candidates were ever paired) the marginal is 2.3x *better*, while under
  judge unanimity it inverts to 0.015. The subtraction also assumes the forced run nests the
  unforced one, and they share 3 of 48 (pr, claim) keys. The honest statement is **no evidence
  either way about the bar's discrimination**, from one unreplicated pair of runs on 4 PRs. The
  volume and recall halves stand (49 -> 179 candidates, 2 -> 5 obligations on majority, 2 -> 3
  under unanimity). Two clauses attached to it were also wrong: `model_confidence` is *not*
  missing -- it is populated on 907 of 907 lead candidates and 179 of 179 forced ones, and is
  absent only from the *finding* schema and from solo runs -- and its within-PR AUC is
  0.485 / 0.485 / 0.514, so the ranking signal is captured and does not rank.
  **And the lever is not only the bar.** Re-scoring the three held-out reps found the admission
  gate discarding 71-83% of the gold obligations the run had already found (7/5/6 hit -> 2/1/1
  published), on the axis of whether a collector can warrant the claim's family rather than
  whether the claim is right: `docs/research/the-admission-gate-2026-09.md`. **Reopens if:** a
  second `forbid_abstention` rep exists, or the forced run is re-judged under unanimity -- both
  free of new generation spend, neither done.
- **Publication as selection** (2026-09-22) — re-scoring the three held-out reps found the
  admission gate discarding 71-83% of the gold obligations the run had already found (7/5/6 hit →
  2/1/1 published), filtering on whether a collector can warrant the claim's *family* rather than on
  whether the claim is right, with a leave-one-PR-out family rule reaching 6 of 7 at zero control
  emission. Proposed as "the publication rule", which is **selection under another name** — the
  fifth derivation of a thread `selection-signal.md` already says is kept "so the next session does
  not re-derive it a fourth time", and the rationalisation that got past the standing refusal was
  "families, not findings". **The user's ruling, same day:** *"Talking about publishing is talking
  about selection. We currently don't have a good enough reviewer to start talking about selection.
  The specialist arms clearly perform much better when they can't abstain, so I don't want to
  consider anything related to selection at the moment."* The ordering is generator first. **The
  measurement is kept** — it is a real correction to every pre-gate recall number in the record, and
  `report buckets --audit` prints the pair — and the *change* is `docs/todo/publication-rule.md`,
  parked. **Reopens if:** the generator is good enough that what to show becomes the binding
  question, which is a judgement the user makes, not a number this report can produce.
- **Precedent priming, Mode A** (2026-07-06/07) — delivery worked (47% of primed findings echo an
  injected precedent), transfer failed: 13 vs 11 covered on 41 shared PRs; the first-20 win was noise.
  **Reopens if:** run under the noise-floor protocol with a different use of the precedent (recognition
  mode, ranking), not as prompt priming.
- **Flag-rate priors, Mode B / Stage 3** — demoted: unconditioned similarity flag-propensity was dead
  per the site-discrimination test (AUC 0.53) — a test later found to have been computed on leaked
  delta sites. **Reopens if:** concern-conditioned variants with an anti-precedent corpus (Stage 0b:
  full PR diffs, uncommented hunks).
- **Oracle-site instantiate pipeline: decide, apply-all, facet battery** (2026-07-07 → 07-11) —
  worklists were built from `gold.delta_total`, the *post-review* revision: 106/202 hunks were the
  author's eventual fix, the search space shrank ~2× toward gold. Every instantiate number (T1 99%,
  issue 40–43% and 69–72%) is an oracle diagnostic, not a deployable result. Fixed by taking sites
  from `input.diff` only (`test_worklist_gold_independence`); the leak-free reruns were never run
  because v4 superseded the line.
- **v3 intervention benchmark, judge v7/v7.1, `evaluate_d2`/v6** — superseded by v4 (sealed
  obligations, v8 judge). Frozen untouched for historical comparability; v7.1 lives in
  `legacy_pipeline` for provenance and its 55 cached verdicts are not re-scored.
- **Static reachability census, Phase 10** (2026-07-18) — C2 reachable 5/40 obligations, all in the
  dev PR 33098; 0/26 outside it → `static_reachability_rejected`; the paid smoke and 3-rep run were
  skipped per the gate. **Reopens if:** a new implementation-registry version with its own
  pre-registration and census; the largest uncovered families are style_norm (5) and docs_gap (3).
- **B1 naming generalisation** (2026-08-05) — a subject-general naming rule reaches 2 further
  obligations through one implementation; fails the ≥3-obligations-and-≥2-implementations gate.
  **Reopens if:** paired with a second family (a coercion-ascription extension adds a third).
- **Budget tiers** (retired Sep 2026) — existed only to vary the orchestrator-wide `sample_max_cost`,
  so each tier needed its own nested orchestrator. `ExecutionLimits` is per task; `TIER_MULTIPLIERS`
  survives only as the lead's vocabulary for asking for a budget.
- **Facet-keyed review join** (2026-09-11) — facets fit 4–8% of maintainer requests; reviewers ask
  about a pattern in the code, not the declaration's shape. Adopted instead: the A→B ledger from
  ```suggestion blocks. Do not rebuild a facet-keyed join.
- **Standalone corpus collectors** — the `/pulls/comments` listing route (HTTP 500 for mathlib4)
  and a search-API stage (30 req/min, separate bucket) both died; the per-PR route worked and was then
  superseded entirely by the PR store (`src/datasets/pull_requests`).
- **Moving the shared review task base into `src/mathlib_review/`** — `ape/tasks/__init__.py`
  imports every task package eagerly, so a `BaseLeanTask` subclass outside that tree cannot import
  `ape.tasks.base` without a cycle. Do not retry.
- **Deleting `src/datasets/pr_review_v2`** — nine frozen manifests pin its roster file by path and
  hash (see `.claude/rules/pull-requests.md`). **Deleting dead code as a route to the collapse** —
  reachability over ~56k lines found exactly one unreachable module; the generations had to be
  consolidated, not pruned.
- **`lean_retrieve` in the review path** — silently returned empty (no per-commit index; the build is
  a heavy LLM-annotation job). Removed from the default toolset; the dense precedent index serves
  instead. **Reopens if:** a per-commit index is built for the base commits in use.
- **Linter-as-convention-oracle** (2026-09-11) — read Mathlib's own `tacticAnalysis` linters
  (`terminalToGrind`, `tryAtEachStepGrindSuggestions`) as a dated, gold-free statement of the
  convention at a base commit, on the argument that "the linter present at base *is* the convention
  at base". It is not. `terminalToGrind` landed 2025-08-14 (`609d272edf`) with `grind` in **4.0 %**
  of Mathlib files and is unchanged while adoption reached 8.4 % (2025-12) and **14.5 % (2026-05)**,
  and review enforcement went 9.1 → 22.4 mentions per thousand Aug → Dec. A linter is a step
  function and a convention is a ramp: it dates *availability*, not the convention. It also answers
  "where **can** X be used", and the can/does gap is the quantity that moves — a high-recall
  generator aimed at a pipeline whose measured bottleneck is **selection, not generation**
  (81 % of missed gold already had a candidate at the line). In the life-stage vector a linter is a
  `stated` source only, which the census spec already said (`suggestion_round` … "never read as
  adopting") and the ≥2-independent-components rule already forbids briefing alone. Raised by the
  user more than once before being written down, which is why it was re-derived from the plan's own
  outcome table. **Reopens if:** used as one corroborating source among ≥ 2 — its `descr` / "How to
  fix this?" text remains the right `stated` extractor — never as the oracle, and never to date a
  convention.
- **Surface proxies for convention discovery** (2026-09-11) — five designs proposed in one session,
  all rejected for one reason: each substituted a statistic *about* code for the semantic question.
  Linter firing ("can `grind` close this goal"); marginal drift in per-declaration features ("how
  often does this token appear"); the A→B ledger from review ("what did a reviewer correct");
  recurring migration targets in commit titles ("what did someone name a PR" — and Mathlib
  squash-merges, so 14,730/14,730 commits are PR titles, the same tier-0 data, not a new substrate);
  author breadth ("how many people did it" — `grind` is 232 commits from 19 authors with 69 % by one,
  `gcongr` 88 from 22 with 28 % by one). The user's ruling on the last: one author running a
  migration does not make `grind` not a convention — it makes commit titles a weak signal, and the
  weakness is of the signal, not a property of the phenomenon. Two further errors made while arguing
  for these: measurements ungated (a `to_dual` example that was 85 % post-eval data, withdrawn), and
  a circular validation ("every target with n ≥ 6 is a genuine convention" was recognition of names
  already known, not a measurement). **The constraint that survives:** evidence must carry what the
  code was *for* and how it was *expressed*, together. Only a modified declaration has both — the
  statement pins the purpose, the before/after pins the form; review corrections are a small late
  sample of that shape, and the authored version is the modified declarations across the merged PR
  diffs (tier 2, not titles). **Reopens if:** a proxy is used as one corroborating source beside a
  semantic one, never as the discovery mechanism.
- **`mergeready_v1` prompt** — approved on compile-exit; more tools produced *fewer* findings under
  it (69 → 3 → 2). The binding constraint was the framing, not tools; `acceptability_v2` is default.
- **Sibling-propagation post-processor** — superseded by the intervention gold unit.
- **`pr_shared` promotion (severing v4 tasks → v2 base → v1 core)** — the entry point transitively
  needs 17 methods / ~409 lines of workspace-overlay code in `src/ape/`, not the 86 first estimated.
  **Reopens if:** archiving the v1/v2 tasks becomes the goal.

## Retracted conclusions — do not re-derive

- *"Holistic dominates; stop decomposing"* (2026-06-18) — retracted twice. The location metric
  over-counted; then at N=115 the composed checkers added 11 disjoint hits (V2 4× holistic) — for a
  conservative model. With gpt_5.2 composed is near-redundant. The two architectures are
  complementary and the split is threshold-dependent.
- *"Holistic under-reaches V2 (1/13 ≈ 8%)"* — a path-normalisation bug plus claim-strictness; true
  coverage was ~60% on 30 PRs. The whole first decomposition effort chased a metric artifact.
- *"V2 selection is irreducibly inseparable"* — over-claim; the correct statement is the narrow one
  above. The user pushed back on this framing explicitly (2026-06-20).
- *"The gen checker is redundant with golf"* — two stacked artifacts: a golf-curated small set with
  no generality gold, and an old gen prompt that golfed proofs. Orthogonal concerns are never
  inherently redundant.
- *"The generalist arm dominates on quality"* (v5 rep2) — a volume artifact: 0.08 vs 0.09 hits per
  candidate; the generalist emits 2.0 candidates per run against 0.5. Specialists are silent, not worse.
- *"`by_cases!` is a refactor, not a convention reviewers request"* — an artifact of the August 2025
  corpus cutoff: 0 in Jun–Aug, 12 in December. A component measured on a truncated source gives a
  confident *wrong* life stage, not a missing one.
- *"The `lean_verify` defect under-counted recall"* — it made recall unreliable in both directions.
- *"Reviewer recall is 40%"* — omitted the PR-author rule; it is 33% recall / 62% precision.
- *"Arms are competent locally but structurally cannot reach design"* — not supported: `report scope`
  shows design recall ≥ local in every audited run with hits (small n).
- *Single-run deltas at n ≈ 6–23* — noise. Same-design pairs swung ±5–7 covered; the judge splits
  its own vote on ~11% of pairs. Three reps is a floor.
- *Phase-C numbers (~70%)* — leak-inflated; never shown externally.

## Deferred by choice (not dead)

- **Track 1.C's second half, and the oracle ladder that replaced it** (2026-09-08 → 2026-09-22) —
  `docs/plans/2026-09-08-review-digestion-and-oracle-ladder.md` §5(i) found that "multi-declaration
  edits exist and are unreachable" and proposed Track 1.C: group sibling declarations into one work
  unit **and** extend `patch_set=True` to `proof_idiom`/`proof_golf`. The grouping half landed
  (`12a3939`, 225 → 121 units). The grant half was never built: Track 1 was replaced by the oracle
  ladder, whose own self-critique in the same document then found it rested on "one PR, one
  obligation family, two arms" (33098; **2 of 35 request groups exercised, 7 of 40 obligations**).
  Neither the dropped track nor the ladder's outcome was recorded here, in `PROJECT-STATUS.md`, in
  `plans/STATUS.md` or in the todo index — `batching-work-units.md`'s status line ("authority,
  `patch_set` … still open") was the only trace, so this is unfinished rather than abandoned.
  **Reopened 2026-09-22** as `docs/plans/2026-09-22-coordinated-emission.md`, under the same plan's
  own correction (`:1376`, **[verified]**): patch sets are file-confined, not anchor-confined, and
  every edit must carry an anchor validated against the investigation's targets *before* the grant
  widens. Two further defects found on reopening and not known in 2026-09: `patchset.apply` splices
  a declaration by substring replacement of its name, and `_patch_set_workspace` calls
  `Path(WorkspaceInfo)`.


- Recruited Mathlib annotators and the inter-annotator ceiling — not until the agent is worth their time.
- Phase-D scale-up to 150–200 PRs — affordable about three times ever; needs a stopping point first.
- Norm store (L0), generalised checkers (L1), calibration, the thesis experiment, a clean v5
  comparison — `docs/PROJECT-STATUS.md` §11.
- Cross-file verification (part A above).
- The Zulip citation benchmark (n ≈ 143 maintainer-cited threads) and a `zulip_search` query study.
