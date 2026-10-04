import json
rep = '''@[deprecated (since := "2025-12-25")]
alias IsNormal.deriv_fp := deriv_fp

theorem le_iff_deriv (H : IsNormal f) {a} : f a ≤ a ↔ ∃ o, deriv f o = a := by
  unfold deriv
  rw [← le_iff_derivFamily fun _ : Unit => H]
  exact ⟨fun h _ => h, fun h => h Unit.unit⟩

@[deprecated (since := "2025-12-25")]
alias IsNormal.le_iff_deriv := le_iff_deriv

theorem mem_range_deriv (H : IsNormal f) {a} : a ∈ Set.range (deriv f) ↔ f a = a := by
  rw [Set.mem_range, ← H.strictMono.le_apply.ge_iff_eq', le_iff_deriv H]

@[deprecated (since := "2025-12-25")]
alias IsNormal.mem_range_deriv := mem_range_deriv

@[deprecated Ordinal.mem_range_deriv (since := "2025-12-25")]
theorem IsNormal.fp_iff_deriv (H : IsNormal f) {a} : f a = a ↔ ∃ o, deriv f o = a :=
  (Ordinal.mem_range_deriv H).symm'''
print(json.dumps({"path": "Mathlib/SetTheory/Ordinal/FixedPoint.lean", "line_start": 364, "line_end": 383, "replacement": rep}))
