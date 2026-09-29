/-- The **Schwarz Lemma**: if `f : ℂ → E` satisfies `f 0 = 0` and sends an open disk with center `0`
to the closed ball with center `0` of the same radius,
then for any point `z` of this disk we have `‖f z‖ ≤ ‖z‖`. -/
theorem norm_le_norm_of_mapsTo_ball_self (hd : DifferentiableOn ℂ f (ball 0 R))
    (h_maps : MapsTo f (ball 0 R) (closedBall 0 R)) (h₀ : f 0 = 0) (hz : ‖z‖ < R) :
    ‖f z‖ ≤ ‖z‖ := by
  simpa [h₀] using dist_le_dist_of_mapsTo_ball_self hd (by rwa [h₀]) (mem_ball_zero_iff.mpr hz)
