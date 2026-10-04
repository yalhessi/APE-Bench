import json
rep = '''* `ProbabilityTheory.IndepFun.mgf_add`: if two real random variables `X` and `Y` are independent
  and their mgfs are defined at `t`, then `mgf (X + Y) μ t = mgf X μ t * mgf Y μ t`
* `ProbabilityTheory.IndepFun.cgf_add`: if two real random variables `X` and `Y` are independent
  and their cgfs are defined at `t`, then `cgf (X + Y) μ t = cgf X μ t + cgf Y μ t`'''
print(json.dumps({"path":"Mathlib/Probability/Moments/Basic.lean","line_start":24,"line_end":27,"replacement":rep}))
rep2 = '''* `ProbabilityTheory.centralMoment X p μ`: `p`th central moment of `X` with respect to measure `μ`,'''
print(json.dumps({"path":"Mathlib/Probability/Moments/Basic.lean","line_start":15,"line_end":15,"replacement":rep2}))
rep3 = '''  `a ≤ X ≤ b` almost everywhere is at most `((b - a) / 2) ^ 2`.'''
print(json.dumps({"path":"Mathlib/Probability/Moments/Variance.lean","line_start":34,"line_end":34,"replacement":rep3}))
rep4 = '''  U_N(a, b) = \\sum_{i = 1}^N \\mathbf{1}_{\\{\\tau_i < N\\}},
$$
where $\\tau_i$ is the $i$-th upper crossing time `upperCrossingTime a b f N i`, $U_N(a, b)$ is
measurable as each $\\{\\tau_i < N\\}$ is a measurable set since $\\tau_i$ is a stopping time.'''
print(json.dumps({"path":"Mathlib/Probability/Martingale/Upcrossing.lean","line_start":703,"line_end":706,"replacement":rep4}))
