import json
rep = """`Finset.Nat.antidiagonalTuple` has since been generalized: `Finset.finAntidiagonal` and
`Finset.piAntidiag` in `Mathlib/Algebra/Order/Antidiag/Pi.lean` work over any commutative monoid
with antidiagonals (see `Finset.piAntidiag_univ_fin_eq_antidiagonalTuple`), and
`Finset.finsuppAntidiag` in `Mathlib/Algebra/Order/Antidiag/Finsupp.lean` is the version for
finitely supported functions."""
print(json.dumps({"path":"Mathlib/Data/Fin/Tuple/NatAntidiagonal.lean","line_start":39,"line_end":41,"replacement":rep}))
