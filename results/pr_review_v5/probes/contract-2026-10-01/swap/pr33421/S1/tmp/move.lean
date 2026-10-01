variable [IsStrictOrderedRing α]

section ContinuousAdd

variable [OrderClosedTopology α] [ContinuousAdd α]

theorem tendsto_round_nhdsGE_pure (x : α) : Tendsto round (𝓝[≥] x) (pure (round x)) := by
  rw [funext round_eq']
  have : Tendsto (2 * ·) (𝓝[≥] x) (𝓝[≥] (2 * x)) := by
    simp only [two_mul]
    refine (tendsto_id.add tendsto_id).inf (tendsto_principal_principal.2 ?_)
    exact fun a ha ↦ add_le_add ha ha
  exact (tendsto_pure_pure (fun n ↦ (n + 1) / 2) _).comp <|
    (tendsto_floor_right_pure_floor (2 * x)).comp this

theorem tendsto_round_nhdsLT_pure_half_ceil (x : α) :
    Tendsto round (𝓝[<] x) (pure (⌈2 * x⌉ / 2)) := by
  rw [funext round_eq', tendsto_pure]
  have : Tendsto (2 * ·) (𝓝[<] x) (𝓝[<] (2 * x)) := by
    simp only [two_mul]
    refine (tendsto_id.add tendsto_id).inf (tendsto_principal_principal.2 ?_)
    exact fun a ha ↦ add_lt_add ha ha
  filter_upwards [tendsto_pure.mp ((tendsto_floor_left_pure_ceil_sub_one (2 * x)).comp this)]
    using by simp +contextual

theorem continuousAt_round {x : α} (hx : 2 * fract x ≠ 1) : ContinuousAt round x := by
  rw [continuousAt_iff_continuous_left'_right']
  refine ⟨(tendsto_round_nhdsLT_pure_half_ceil x).mono_right (pure_le_nhds_iff.mpr ?_),
    (tendsto_round_nhdsGE_pure x).mono_left ?_ |>.mono_right (pure_le_nhds _)⟩
  · rw [round_eq_half_ceil_two_mul hx]
  · gcongr
    apply Ioi_subset_Ici_self

theorem continuousOn_round : ContinuousOn round {x : α | 2 * fract x ≠ 1} :=
  fun _x hx ↦ (continuousAt_round hx).continuousWithinAt

end ContinuousAdd
