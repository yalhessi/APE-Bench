# PR Review v4 benchmark tiers — small / medium / large

*Status: v0.1 proposal. Created 2026-07-17.*
*Machine-readable manifest: `inputs/pr_review_v4/benchmarks/tiers-v1.json`.*
*Companion: `pr-review-v4-systematic-opportunity-pipeline-design.md` (§6.5 development/holdout
discipline; the temporal holdout is separate from and unaffected by these tiers).*

## 1. Purpose and usage discipline

Three nested evaluation scales with explicit contamination status and look budgets:

| tier | PRs | role | look budget |
|---|---|---|---|
| **small (dev)** | 3 | per-phase operator smokes, plumbing gates, unlimited iteration | unlimited |
| **medium (treatment)** | 16 | pre-registered treatment comparisons (3-rep arms), method census | pre-registered runs only; miss analyses allowed |
| **large (confirmation)** | 57 | confirm treatment-level claims at scale; per-family CIs | ≤3 total uses over the project; pre-registered, frozen configs only |

Rules:

1. Results iterate freely on small; medium runs require a written pre-registration (arms, gates,
   thresholds) before execution; large runs additionally require a passed medium gate.
2. All three tiers are **development-contaminated to different degrees** (small: fully; medium:
   selection used gold statistics; large: used across the whole project history). None of them is
   the temporal holdout. Generalization claims for publication still require the frozen temporal
   holdout of the pipeline design §6.5.
3. Nesting: dev ∩ large = {33098}; medium ⊃ pilot-9; medium-gold ⊂ large. When large runs, report
   **(a)** the full-57 aggregate and **(b)** the *unseen slice* — large minus every dev/medium
   gold PR (~44 PRs) — which is the number that carries generalization weight.
4. Controls are first-class members of every tier and count toward its look budget.

## 2. Small tier (unchanged)

`33057` (compile-sensitive intervention), `33098` (multi-obligation proof/naming development PR,
14 obligations), `33438` (substantive control). This is the existing stable smoke; it remains the
only tier where prompts and operators may be iterated against results.

## 3. Medium tier (new): pilot-9 + 7 gap-filling PRs

Composition: the nine 0.9.0 pilot PRs (episodes, change graphs, migrated gold already exist)
plus seven PRs selected **from the 57** to repair the concern-distribution gaps that the pilot-6
gold leaves open (measured from `interventions_v5`, judgeable non-meta):

| family | corpus total | covered by pilot-6 | after additions |
|---|---|---|---|
| style | 37 | 6 | well covered |
| naming | 16 | **1** | ~5 |
| duplication | 13 | 3 | ~6 |
| docs | 12 | **1** | ~3 |
| correctness | 4 | **0** | 2 |
| scope | 4 | **0** | 1–2 |
| proof-golf | 4 | 1 | 3 |
| generalization | 2 | 1 | 1 |

### 3.1 The seven additions, with selection rationale

| PR | ivs (concerns) | sites | outcome mix | why it's here |
|---|---|---|---|---|
| **33149** | 3 (correctness ×2, dup) | 1 | dropped/unknown | the only correctness-rich PR (no-axioms policy; "Mathlib already has Parseval"). Tests `baseline_failure`/policy routing and dup discovery. Sole source of the correctness family. |
| **33362** | 1 (scope) | 5 | adopted | namespace-placement ask ("move into `namespace Complex`") — the scope family's cleanest adopted case. |
| **33145** | 5 (dup ×3, style ×2) | 1 | mostly adopted | the dualization multi-anchor family (one judgment across sibling lemmas) — THE test for PR relations, sibling propagation, and Phase-8 synthesis retention. |
| **33337** | 2 (naming ×2) | 4 | adopted | `toLinearMap_` prefix renames — naming_contrast generalization beyond the `encard` motivating case (my review issue 5: operators need non-motivating cases). |
| **33321** | 3 (docs ×2, style) | 10 | dropped-heavy | docs family + a dropped-rich PR — calibrates worthiness policies against asks maintainers made but authors ignored. |
| **33294** | 2 (naming, style) | **51** | adopted | the size stress test: batching, context assembly, big-PR economics. Largest change surface in the corpus. |
| **33285** | 2 (proof-golf ×2) | 11 | adopted/partial | knowledge-frontier golf outside 33098 — the Phase-6 historical-transformation store needs test cases that didn't motivate it. |

### 3.2 Medium tier totals

- **16 PRs**: 13 gold-bearing (33048? no — see exclusions), i.e. pilot gold-6 {33057, 33066,
  33098, 33117, 33305, 33421} + additions {33149, 33362, 33145, 33337, 33321, 33294, 33285};
  3 controls {33304, 33315, 33438}.
- **Obligations**: 23 (pilot) + est. 15–20 after decomposition of the additions' 18 interventions
  → **~40 atomic obligations**, spread across all 8 families, sizes 1–51 sites, and adopted /
  partially_adopted / dropped / unknown outcomes.
- Control ratio 3/16; optionally +1–2 family-specific controls later (e.g. a PR whose names
  already follow convention, for naming pressure) drawn from the non-gold records.

### 3.3 Notable exclusions and why

- `33048` (4 ivs): strong PR, but its `FiniteElement` asks overlap heavily with families already
  covered and its gold had lingering compile issues in earlier eras; revisit for large only.
- `33267`/`33268` (style micro-asks): high volume of terse formatting nits with unknown outcomes —
  poor signal-to-review-cost for the medium tier; they remain in large.
- `33111`, `33203`, `33419`, `33400` (naming): covered by 33337 + 33294; adding all naming PRs
  would over-rotate medium toward one family.

## 4. Large tier: the 57 gold-bearing PRs

The full historical eval set (`ALL_57` in `site_worklist.py`), scored under v4 gold once migrated.
Use is rationed (≤3 over the project) and gated on a passed medium pre-registration. Report both
full-57 and the unseen ~44-PR slice (§1.3).

## 5. Prerequisites (status 2026-07-17: medium release BUILT)

**Medium is built**: `inputs/pr_review_v4/releases/dev-medium-0.1.0` (release `0.1.0-medium`,
built from `dev-judgment-stable-0.9.0` via `pilot.py --cases medium`). 16 PRs, 225 work units,
33 judgments / 43 obligations across 13 gold PRs; 30 included views (+2 excluded_not_judgeable,
1 unresolved_scope). Validated: the 74 pilot work-unit prompts are byte-identical to
`dev-pilot-0.9.0`, and no gold obligation text appears in any generation artifact. Run config:
`configs/pr_review_v4_medium.yaml`.

Gold-quality parity note: the additions' 19 judgments are 18× `migration_proposal` /16×
`presumed_atomic` — the **same** standard the 0.9.0 pilot ran at (13/14 migration_proposal).
Remaining steps before first pre-registered use:

- **Lean builds (user compute)**: 7 new base commits (one per addition PR); builder input at
  `data/pr_review_v4/medium_base_commits.jsonl` (14 rows incl. the 7 pilot bases already built).
- **Curation sitting (optional but recommended)**: digest at
  `inputs/pr_review_v4/curation/medium_additions_digest.md` (19 items; 2 flagged:
  `pr33149_i04` not_judgeable, `pr33145_i05` unresolved_scope — both already excluded from
  views). Confirmations land as a decisions v2 → stable-0.10.0 → dev-medium-0.2.0 rebuild.
- Large: same per-PR work ×48 plus decomposition review of ~70 interventions. Do NOT start this
  until the medium tier has justified it (a treatment that beats its medium gate).

## 6. What medium unlocks immediately

1. **The method-coverage census** (systematic-pipeline review, issue 1): classify all ~40 medium
   obligations by which registry method could in principle recover them — before building
   Phases 5–8, so the registry grows toward the corpus distribution (style/docs operators!) rather
   than toward 33098.
2. **Non-motivating operator cases** (issue 5): naming_contrast on 33337/33294, canonical-API/
   wrapper on 33145/33285, policy path on 33149 — each operator gets real cases it wasn't built
   from, before the Phase-9 integrated smoke.
3. **Worthiness calibration data** (issue 3): 33321/33149's dropped-heavy gold gives the
   deterministic policy table its first negative-side calibration.
4. A Phase-10 pilot set that is no longer 33098-dominated: today 14 of 23 pilot obligations are
   one PR; medium dilutes that to ~14 of ~40.

## 7. Open questions

1. Add 1–2 family-specific controls to medium now or after the census?
2. Should 33098's 14 obligations be down-weighted (per-PR capped reporting) so medium aggregates
   aren't 33098-driven? Proposal: always report per-PR alongside pooled.
3. Decomposition review cadence: one sitting for all 7 additions, or per-phase as operators need
   their cases?
