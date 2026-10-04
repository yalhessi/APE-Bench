lemma coveringNumber_two_mul_le_coveringNumber_of_subset (h : A ⊆ B) :
    coveringNumber (2 * ε) A ≤ coveringNumber ε B :=
  (coveringNumber_two_mul_le_externalCoveringNumber ε A).trans <|
    (externalCoveringNumber_mono_set h).trans (externalCoveringNumber_le_coveringNumber ε B)
