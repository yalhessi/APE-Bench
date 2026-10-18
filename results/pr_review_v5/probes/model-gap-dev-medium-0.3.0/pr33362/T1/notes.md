# Review notes: PR #33362 (weaken assumptions in Schwarz lemma)

## What I did
- Read `brief.md`, `pr.md`, `model.md`, `diff.patch`. Read the whole of `target/Mathlib/Analysis/Complex/Schwarz.lean` as the PR leaves it with `file_read`.
- `lean_verify_edit` with no edit: the file compiles as the PR leaves it, with no errors or warnings.
- `content_search` for every changed lemma name over `target/Mathlib`: none of them is used outside this file, so the signature changes (removing `hc`, `ball` → `closedBall`, the new `dist (f z) (f c)` conclusion) break nothing in Mathlib.
- `declaration_search` for `Complex.abs_deriv_le_div_of_mapsTo_ball` and `Complex.abs_deriv_le_one_of_mapsTo_ball`: neither exists, so the module-doc references are dangling.
- Verified every proposed edit with `lean_verify_edit`. All of them compile:
  - dropping `ComplexConjugate`;
  - the corrected module bullets;
  - the corrected declaration docstrings (lines 134-169);
  - the alternative layout that keeps `private theorem schwarz_aux` inside `@[expose] public section` / `namespace Complex`.
- `precedent_search` on `dist_le_dist_of_mapsTo_ball_self`. The hits were about unrelated files (CircleMap, MeanValue, Residue) and gave no relevant ask.
- Checked the `@[expose] public section` convention in `Analysis/Complex`: all 56 files use it, so I make no ask to drop `@[expose]`.

## Object by object
- **Module docstring** (finding 1). It names two non-existent `abs_*` lemmas, and the rewritten bullets keep `f : ℂ → ℂ` and a fixed-point hypothesis the PR removed. The `dist_le_dist` bullet has the wrong conclusion (`dist (f z) c`). The `norm_le_norm` bullet is stale (`to itself`, `abs`). Removing the TODO is fine: the affine equality-case lemmas already cover it.
- **`open scoped Topology ComplexConjugate`** (finding 6). `ComplexConjugate` is unused, and the file compiles without it.
- **`variable` line**. Adding `R` and merging the two variable blocks into one with `f : ℂ → E` is what generalises the same-radius lemmas. No issue.
- **`Complex.schwarz_aux`**. The `ball` → `closedBall` change and the proof change (`← mem_closedBall_iff_norm`, direct `h_maps`) are fine. Making it private is fine for an auxiliary lemma: no uses elsewhere. Advisory finding 7: moving it, and the `@[expose] public section` / `namespace Complex` openers, around the header is unnecessary, and keeping it in place as `private` compiles.
- **`Complex.norm_dslope_le_div_of_mapsTo_ball`**. The new `hR₂ : 0 ≤ R₂` via `nonempty_closedBall`, the dropped `hg₀`, and `mapsTo_closedBall` are all correct and simpler. No ask.
- **`Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div` and its primed version**. The hypothesis is weakened, and the removed `by_cases h : z = c` was unnecessary (the file compiles). They still spell `Set.MapsTo` while the siblings use `MapsTo` under `open Set`. That spelling predates the PR, so I make no ask. The primed lemma has no docstring, which also predates the PR, and theorems need none. No finding.
- **`Complex.norm_deriv_le_div_of_mapsTo_ball`**. The statement is fine. Its docstring still says "open ball" (finding 4).
- **`Complex.dist_le_div_mul_dist_of_mapsTo_ball`**. The statement and docstring are both updated consistently. No ask.
- **`Complex.norm_deriv_le_one_of_mapsTo_ball`**. The statement is generalised correctly to `E` with `closedBall (f c) R`. Its docstring is stale (finding 3).
- **`Complex.dist_le_dist_of_mapsTo_ball_self`**. The statement is generalised, and the one-line `simpa` proof is fine. Its docstring is stale: it gives the old conclusion and the old hypotheses (finding 2). I considered whether `_self` still fits the name now that the codomain is `closedBall (f c) R`. A rename would be churn for little gain, so I make no ask.
- **`Complex.norm_le_norm_of_mapsTo_ball_self`**. The statement and the `simpa [h₀]` proof are fine. The new docstring omits `f 0 = 0`, without which the claim is false (finding 5). Taking `hz : ‖z‖ < R` rather than `z ∈ ball 0 R` predates the PR, so I make no ask.

## Families checked with nothing to add
- Generalization: the hypotheses are already the weakest natural ones (an open domain ball, a closed codomain ball, `DifferentiableOn`). Every lemma is now stated for `f : ℂ → E`.
- Duplication: the same-radius lemmas are thin corollaries of the `R₂ / R₁` versions, which is the intended API. Nothing in the base duplicates them.
- Proof golf: the PR's proofs are already short. I found no canonical replacement worth asking for.
