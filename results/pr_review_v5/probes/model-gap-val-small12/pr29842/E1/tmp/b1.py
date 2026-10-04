import json
rep = '''theorem UniqueDiffWithinAt.mono (h : UniqueDiffWithinAt 𝕜 s x) (st : s ⊆ t) :
    UniqueDiffWithinAt 𝕜 t x :=
  ⟨h.1.mono <| Submodule.span_mono <| tangentConeAt_mono st, closure_mono st h.2⟩

#check @UniqueDiffWithinAt.mono

variable [ContinuousAdd E] [ContinuousSMul 𝕜 E]

theorem UniqueDiffWithinAt.mono_nhds (h : UniqueDiffWithinAt 𝕜 s x) (st : 𝓝[s] x ≤ 𝓝[t] x) :
    UniqueDiffWithinAt 𝕜 t x := by
  simp only [uniqueDiffWithinAt_iff] at *
  rw [mem_closure_iff_nhdsWithin_neBot] at h ⊢
  exact ⟨h.1.mono <| Submodule.span_mono <| tangentConeAt_mono_nhds st, h.2.mono st⟩'''
print(json.dumps({"path":"Mathlib/Analysis/Calculus/TangentCone.lean","line_start":433,"line_end":443,"replacement":rep}))
