theorem coveringNumber_two_mul_le_externalCoveringNumber (ε : ℝ≥0) (A : Set X) :
    coveringNumber (2 * ε) A ≤ externalCoveringNumber ε A :=
  (coveringNumber_le_packingNumber _ A).trans (packingNumber_two_mul_le_externalCoveringNumber ε A)
