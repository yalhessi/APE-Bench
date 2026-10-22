# Goal brief

## 1. Kind of contribution

A new definition, and new results about it.

## 2. Capability

The notion of a **fundamental discriminant**, for an integer D of either sign. For D ≠ 1 it is the
classical notion: D ≡ 0 or 1 (mod 4), and D is not f²·E for any integer f ≥ 2 and integer
E ≡ 0 or 1 (mod 4). Whether D = 1 counts is open (section 4).

Results about it:

- every fundamental discriminant is nonzero and ≡ 0 or 1 (mod 4);
- the classical characterization: for D ≠ 1, D is a fundamental discriminant if and only if either
  D is 4 times a squarefree integer that is ≡ 2 or 3 (mod 4), or D is squarefree and ≡ 1 (mod 4).

Squarefree has its usual meaning on ℤ: no square of a prime divides the integer.

## 3. What must keep working

- Two special cases of the characterization, each available on its own: (a) an integer D ≡ 1
  (mod 4), D ≠ 1, is a fundamental discriminant iff it is squarefree; (b) a multiple of 4 is a
  fundamental discriminant iff its quotient by 4 is squarefree and ≡ 2 or 3 (mod 4).
- The change only adds: existing declarations in the base files keep their statements.

## 4. Open questions

- **D = 1.** Two readings; this brief takes neither. (i) 1 counts, as the discriminant of ℚ
  itself: the characterization and (a) then hold at D = 1 too. (ii) 1 does not count, so that the
  notion coincides with the set of quadratic-field discriminants: the characterization and (a)
  then hold for D ≠ 1 only.
- Which equivalent description (the one in section 2, the characterization, or another) serves as
  the definition.
- Whether the special cases are about an integer assumed to lie in the residue class, or about the
  expressions 4m + 1 and 4m for arbitrary m.
- Whether to link the notion to quadratic fields or number-field discriminants, or to treat it with
  integer arithmetic alone. The inputs require neither such a link nor results beyond sections 2-3.
- The base files are `Mathlib/Data/Nat/Prime/Basic.lean`, `Mathlib/Data/Nat/Squarefree.lean`
  and `Mathlib/RingTheory/Coprime/Basic.lean`; which general supporting facts, if any, belong
  there is open.

## 5. Where the requirements come from

The description is withheld from this packet; no requirement comes from it.

- The notion: the title, "fundamental discriminants" (the current title, not verified to be the one
  at review time), and the change itself, which introduces it for all integers.
- Nonvanishing, the residue mod 4, the characterization, and special cases (a) and (b): the change
  itself, which proves each.
- Existing declarations unchanged: the change itself, which removes or alters no existing line.
