* `ProbabilityTheory.centralMoment X p μ`: `p`th central moment of `X` with respect to measure `μ`,
  `μ[(X - μ[X])^p]`
* `ProbabilityTheory.mgf X μ t`: moment generating function of `X` with respect to measure `μ`,
  `μ[exp(t*X)]`
* `ProbabilityTheory.cgf X μ t`: cumulant generating function, logarithm of the moment generating
  function

## Main results

* `ProbabilityTheory.IndepFun.mgf_add`: if two real random variables `X` and `Y` are independent
  and their MGFs are defined at `t`, then `mgf (X + Y) μ t = mgf X μ t * mgf Y μ t`
* `ProbabilityTheory.IndepFun.cgf_add`: if two real random variables `X` and `Y` are independent
  and their CGFs are defined at `t`, then `cgf (X + Y) μ t = cgf X μ t + cgf Y μ t`
* `ProbabilityTheory.measure_ge_le_exp_cgf` and `ProbabilityTheory.measure_le_le_exp_cgf`:
  Chernoff bound on the upper (resp. lower) tail of a random variable. For `t` nonnegative such that
  the CGF exists, `ℙ(ε ≤ X) ≤ exp(- t*ε + cgf X ℙ t)`. See also
