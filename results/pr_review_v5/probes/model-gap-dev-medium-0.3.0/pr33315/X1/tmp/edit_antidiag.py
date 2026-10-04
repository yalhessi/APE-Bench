import json
rep = """`Finset.Nat.antidiagonalTuple` is generalized by `Finset.finAntidiagonal` and `Finset.piAntidiag`
in `Mathlib/Algebra/Order/Antidiag/Pi.lean` (see `Finset.piAntidiag_univ_fin_eq_antidiagonalTuple`),
and to finitely-supported functions by `Finset.finsuppAntidiag` in
`Mathlib/Algebra/Order/Antidiag/Finsupp.lean`.

## TODO

Deduplicate `Finset.Nat.antidiagonalTuple` with `Finset.finAntidiagonal`."""
print(json.dumps({"path":"Mathlib/Data/Fin/Tuple/NatAntidiagonal.lean","line_start":39,"line_end":41,"replacement":rep}))
