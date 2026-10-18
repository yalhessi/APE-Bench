import json
L=open("Schwarz_pr.lean").read().split("\n")
src="\n".join(L)
def rep(old,new):
    global src
    assert src.count(old)==1, old[:80]
    src=src.replace(old,new)
# module doc bullets
start=src.index("* `Complex.norm_deriv_le_div_of_mapsTo_ball`, `Complex.abs_deriv")
end_=src.index("## Implementation notes")
src=src[:start]+"""* `Complex.norm_dslope_le_div_of_mapsTo_ball`: if `f : ℂ → E` sends an open disk with center `c`
  and radius `R₁` to a closed ball with center `f c` and radius `R₂`, then for any `z` in the disk
  the norm of `dslope f c z` is at most the ratio `R₂ / R₁`;

* `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div`,
  `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div'`: the equality case; if moreover `E`
  is complete and strictly convex and `‖dslope f c z₀‖ = R₂ / R₁` at a point `z₀` of the disk, then
  `f` is affine on the disk;

* `Complex.norm_deriv_le_div_of_mapsTo_ball`: if `f : ℂ → E` sends an open disk with center `c`
  and a positive radius `R₁` to a closed ball with center `f c` and radius `R₂`, then the norm of
  the derivative of `f` at `c` is at most the ratio `R₂ / R₁`;

* `Complex.dist_le_div_mul_dist_of_mapsTo_ball`: if `f : ℂ → E` sends an open disk with center `c`
  and radius `R₁` to a closed ball with center `f c` and radius `R₂`, then for any `z` in the former
  disk we have `dist (f z) (f c) ≤ (R₂ / R₁) * dist z c`;

* `Complex.norm_deriv_le_one_of_mapsTo_ball`: if `f : ℂ → E` sends an open disk with center `c`
  and a positive radius `R` to the closed ball with center `f c` and the same radius, then the norm
  of the derivative of `f` at `c` is at most `1`;

* `Complex.dist_le_dist_of_mapsTo_ball_self`: if `f : ℂ → E` sends an open disk with center `c`
  and radius `R` to the closed ball with center `f c` and the same radius, then for any point `z` of
  this disk we have `dist (f z) (f c) ≤ dist z c`;

* `Complex.norm_le_norm_of_mapsTo_ball_self`: if `f : ℂ → E` sends `0` to `0` and an open disk with
  center `0` to the closed ball with center `0` and the same radius, then for any point `z` of this
  disk we have `‖f z‖ ≤ ‖z‖`.

"""+src[end_:]
# layout
rep("""open Metric Set Function Filter TopologicalSpace

open scoped Topology ComplexConjugate

variable {E""","""public section

open Metric Set Function Filter TopologicalSpace

open scoped Topology

namespace Complex

variable {E""")
rep("private theorem Complex.schwarz_aux","private theorem schwarz_aux")
rep("""@[expose] public section

namespace Complex

""","")
# schwarz_aux line 77-79
rep("mem_sphere_iff_norm.1 hz, ←","mem_sphere_iff_norm.mp hz, ←")
rep("    exact h_maps <| mem_ball.2 <| by rw [mem_sphere.1 hz]; exact hr.2","    exact h_maps <| mem_ball.mpr <| (mem_sphere.mp hz).trans_lt hr.2")
rep("  · rw [hc, norm_zero]; exact div_nonneg hR₂ hR₁.le","  · rw [hc, norm_zero]\n    exact div_nonneg hR₂ hR₁.le")
rep("""    (hd : DifferentiableOn ℂ f (ball c R₁))
    (h_maps : Set.MapsTo f (ball c R₁) (closedBall (f c) R₂))
    (h_z₀ : z₀""","""    (hd : DifferentiableOn ℂ f (ball c R₁)) (h_maps : MapsTo f (ball c R₁) (closedBall (f c) R₂))
    (h_z₀ : z₀""")
src=src.replace("Set.MapsTo","MapsTo").replace("Set.EqOn","EqOn")
rep("""/-- The **Schwarz Lemma**: if `f : ℂ → E` sends an open disk with center `c` and a positive radius
`R₁` to an open ball with center `f c` and radius `R₂`, then the norm of the derivative of
`f` at `c` is at most the ratio `R₂ / R₁`. -/""","""/-- The **Schwarz Lemma**: if `f : ℂ → E` sends an open disk with center `c` and a positive radius
`R₁` to a closed ball with center `f c` and radius `R₂`, then the norm of the derivative of
`f` at `c` is at most the ratio `R₂ / R₁`. -/""")
rep("""/-- The **Schwarz Lemma**: if `f : ℂ → ℂ` sends an open disk of positive radius to itself and the
center of this disk to itself, then the norm of the derivative of `f` at the center of
this disk is at most `1`. -/""","""/-- The **Schwarz Lemma**: if `f : ℂ → E` sends an open disk with center `c` and a positive radius
`R` to the closed ball with center `f c` and the same radius, then the norm of the derivative of `f`
at `c` is at most `1`. -/""")
rep("""/-- The **Schwarz Lemma**: if `f : ℂ → ℂ` sends an open disk to itself and the center `c` of this
disk to itself, then for any point `z` of this disk we have `dist (f z) c ≤ dist z c`. -/""","""/-- The **Schwarz Lemma**: if `f : ℂ → E` sends an open disk with center `c` and radius `R` to the
closed ball with center `f c` and the same radius, then for any point `z` of this disk we have
`dist (f z) (f c) ≤ dist z c`. -/""")
rep("""/-- The **Schwarz Lemma**: if `f : ℂ → E` sends an open disk with center `0`
to the closed ball with center `0` of the same radius,
then for any point `z` of this disk we have `‖f z‖ ≤ ‖z‖`. -/""","""/-- The **Schwarz Lemma**: if `f : ℂ → E` sends an open disk with center `0` to the closed ball with
center `0` of the same radius, then for any point `z` of this disk we have `‖f z‖ ≤ ‖z‖`. -/""")
rep("simpa [(nonempty_ball.1 ⟨z, hz⟩).ne']","simpa [(nonempty_ball.mp ⟨z, hz⟩).ne']")
open("Schwarz_revised.lean","w").write(src)
for i,l in enumerate(src.split("\n"),1):
    if len(l)>100: print("LONG",i,len(l),l)
nl=len(L)
body=src.rstrip("\n")
json.dump({"path":"Mathlib/Analysis/Complex/Schwarz.lean","line_start":1,"line_end":175,"replacement":body},open("z_all.json","w"))
