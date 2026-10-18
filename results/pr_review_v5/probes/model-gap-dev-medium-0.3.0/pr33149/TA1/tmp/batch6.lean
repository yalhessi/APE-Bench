-- H1. fourier_ortho_integral from `orthonormal_fourier`
example (n m : ℤ) :
    ∫ x : UnitAddCircle, fourier n x * star (fourier m x) = if n = m then 1 else 0 := by
  have h := orthonormal_iff_ite.mp (orthonormal_fourier (T := 1)) m n
  rw [MeasureTheory.ContinuousMap.inner_toLp] at h
  rw [AddCircle.volume_eq_smul_haarAddCircle, ENNReal.ofReal_one, one_smul]
  simp_rw [mul_comm (fourier n _)]
  convert h using 2
  exact propext eq_comm

example (n m : ℤ) :
    ∫ x : UnitAddCircle, fourier n x * star (fourier m x) = if n = m then 1 else 0 := by
  have h := orthonormal_iff_ite.mp (orthonormal_fourier (T := 1)) m n
  rw [MeasureTheory.ContinuousMap.inner_toLp] at h
  rw [AddCircle.volume_eq_smul_haarAddCircle, ENNReal.ofReal_one, one_smul]
  simpa [mul_comm, eq_comm] using h
