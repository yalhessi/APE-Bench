import json
rep = '''/-!
# Schwarz lemma

In this file we prove several versions of the Schwarz lemma.

* `Complex.norm_deriv_le_div_of_mapsTo_ball`: if `f : ℂ → E` sends an open disk with center `c`
  and a positive radius `R₁` to a closed ball with center `f c` and radius `R₂`, then the norm of
  the derivative of `f` at `c` is at most the ratio `R₂ / R₁`;

* `Complex.dist_le_div_mul_dist_of_mapsTo_ball`: if `f : ℂ → E` sends an open disk with center `c`
  and radius `R₁` to a closed disk with center `f c` and radius `R₂`, then for any `z` in the former
  disk we have `dist (f z) (f c) ≤ (R₂ / R₁) * dist z c`;

* `Complex.norm_deriv_le_one_of_mapsTo_ball`: if `f : ℂ → E` sends an open disk with center `c`
  and a positive radius `R` to the closed ball with center `f c` and the same radius,
  then the norm of the derivative of `f` at `c` is at most `1`;

* `Complex.dist_le_dist_of_mapsTo_ball_self`: if `f : ℂ → E` sends an open disk with center `c`
  and radius `R` to the closed ball with center `f c` and the same radius,
  then for any point `z` of this disk we have `dist (f z) (f c) ≤ dist z c`;

* `Complex.norm_le_norm_of_mapsTo_ball_self`: if `f : ℂ → E` sends `0` to `0` and an open disk
  with center `0` to the closed ball with center `0` and the same radius, then for any point `z`
  of this disk we have `‖f z‖ ≤ ‖z‖`.

## Implementation notes

We prove some versions of the Schwarz lemma for a map `f : ℂ → E` taking values in any normed space
over complex numbers.

## TODO

* Prove that any diffeomorphism of the unit disk to itself is a Möbius map.

## Tags

Schwarz lemma
-/
'''
print(json.dumps({"path":"Mathlib/Analysis/Complex/Schwarz.lean","line_start":11,"line_end":48,"replacement":rep}))
