lemma coveringNumber_subset_le (h : A ⊆ B) :
    coveringNumber ε A ≤ coveringNumber (ε / 2) B := by
  calc coveringNumber ε A
    _ = coveringNumber (2 * (ε / 2)) A := by rw [mul_div_cancel₀ _ two_ne_zero]
    _ ≤ externalCoveringNumber (ε / 2) A := coveringNumber_two_mul_le_externalCoveringNumber _ A
    _ ≤ externalCoveringNumber (ε / 2) B := externalCoveringNumber_mono_set h
    _ ≤ coveringNumber (ε / 2) B := externalCoveringNumber_le_coveringNumber _ B
