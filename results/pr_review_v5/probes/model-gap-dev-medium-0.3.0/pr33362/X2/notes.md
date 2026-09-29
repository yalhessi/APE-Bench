# Review notes: PR #33362 (weaken assumptions in the Schwarz lemma)

I read `pr.md`, `model.md` and `diff.patch`, and the whole of
`target/Mathlib/Analysis/Complex/Schwarz.lean` as the PR leaves it (`file_read`). With no edit
applied, `lean_verify_edit` reports that the file as the PR leaves it compiles, with no errors or
warnings. I searched `target/` for every changed lemma name. None of them is used outside this
file; the only other mentions are `docs/overview.yaml` (`norm_le_norm_of_mapsTo_ball_self`) and
`scripts/nolints_prime_decls.txt` (the primed affine lemma). So the signature changes break no
downstream code.

## Object by object

- **`Complex.schwarz_aux`**: the hypothesis is weakened to `closedBall`, and the proof's closing
  step is adapted with `← mem_closedBall_iff_norm`, which is correct. The lemma is now `private`
  and has moved above `@[expose] public section` / `namespace Complex`, with a fully qualified
  name. That reordering is unnecessary: a verified alternative keeps the header order and puts
  `private theorem schwarz_aux` inside the namespace (finding 8). Making it private removes no
  downstream use.
- **`Complex.norm_dslope_le_div_of_mapsTo_ball`**: `hR₂` is now `0 ≤ R₂` via `nonempty_closedBall`,
  the now-unneeded `hg₀` is dropped, and `mapsTo_ball` becomes `mapsTo_closedBall`. All correct and
  minimal. I looked for a golf that avoids the `dslope f c z = 0` case split. `exists_dual_vector'`
  would need `[Nontrivial E]`, which is a loss of generality, so I made no request. The docstring
  is fine.
- **`affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div`** and **`...'`**: only the hypothesis is
  weakened. The `by_cases h : z = c` branch was removed and the file compiles without it, which is
  a valid golf. `Set.MapsTo` / `Set.EqOn` are over-qualified, since `Set` is open, but that
  predates the PR, so I did not raise it.
- **`norm_deriv_le_div_of_mapsTo_ball`**: the statement is fine, but the docstring still says
  "open ball" (finding 3).
- **`dist_le_div_mul_dist_of_mapsTo_ball`**: the statement and docstring were both updated
  consistently. Nothing to request.
- **`norm_deriv_le_one_of_mapsTo_ball`**: generalized to `ℂ → E` and `closedBall (f c) R`, with
  `hc` dropped. The proof is fine; the docstring is stale (finding 2).
- **`dist_le_dist_of_mapsTo_ball_self`**: generalized the same way, and the conclusion is now
  `dist (f z) (f c)`. The `simpa` proof is fine. The docstring is stale and gives the wrong
  conclusion (finding 1).
- **`norm_le_norm_of_mapsTo_ball_self`**: now for `ℂ → E` with a closed ball; the proof is fine.
  The new docstring omits `f 0 = 0`, which the statement needs (finding 4).
- **Module doc**: the PR's own new text for the last bullets describes `ℂ → ℂ` fixed-point versions
  and `dist (f z) c` (finding 5). It also keeps the nonexistent `abs_deriv_*` names;
  `declaration_search` found 0 declarations of either (finding 6). Removing the TODO "strict unless
  affine" is justified, because the `affine_of_...` lemmas already prove the equality case.
- **`open scoped ... ComplexConjugate`**: unused, since `conj` appears nowhere in the file.
  Removing it compiles (finding 7).
- **`variable` line** (adds `R`, drops the `{f : ℂ → ℂ}` section): this is what makes the
  "same radius" lemmas work for any codomain, as the PR description says. Correct.

## Considered and not raised

- The `_self` suffix on `dist_le_dist_of_mapsTo_ball_self` and `norm_le_norm_of_mapsTo_ball_self`
  is less apt now that the codomain is `E`, because the map no longer sends a ball to *itself*.
  A rename would need deprecated aliases, and I have no evidence that a maintainer would ask for
  one, so I did not raise it.
- The statement changes to `norm_deriv_le_one_of_mapsTo_ball` and
  `dist_le_dist_of_mapsTo_ball_self` break downstream callers, but there are none in Mathlib.
  Signature generalizations like these are not normally deprecated.
- `precedent_search` on the `dist_le_dist` lemma returned nothing applicable.

## Verification

Every proposed edit was checked with `lean_verify_edit` and succeeded with no errors or warnings:
- removing `ComplexConjugate`;
- the header restructure with `private theorem schwarz_aux` inside the namespace;
- the docstring rewrites for lines 134-165;
- the `norm_le_norm` docstring;
- the module-doc bullets for lines 16-34.

Every proposed line is at most 100 characters.
