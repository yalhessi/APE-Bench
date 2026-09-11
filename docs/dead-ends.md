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

- Recruited Mathlib annotators and the inter-annotator ceiling — not until the agent is worth their time.
- Phase-D scale-up to 150–200 PRs — affordable about three times ever; needs a stopping point first.
- Norm store (L0), generalised checkers (L1), calibration, the thesis experiment, a clean v5
  comparison — `docs/PROJECT-STATUS.md` §11.
- Cross-file verification (part A above).
- The Zulip citation benchmark (n ≈ 143 maintainer-cited threads) and a `zulip_search` query study.
