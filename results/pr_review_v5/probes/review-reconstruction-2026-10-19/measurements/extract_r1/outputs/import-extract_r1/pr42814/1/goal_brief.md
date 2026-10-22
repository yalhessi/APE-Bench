# Goal brief

## 1. Kind of contribution

A new definition, with new results about it.

## 2. Capability

- A notion of **fundamental discriminant** for an integer D of either sign: D ≡ 0 or 1 (mod 4), and
  D is primitive: D ≠ f²·D′ for every integer f > 1 and every integer D′ ≡ 0 or 1 (mod 4).
  The convention for D = 1 is open (see 4).
- The classical characterization: D is a fundamental discriminant if and only if either
  D ≡ 1 (mod 4) and D is squarefree, or D = 4m with m squarefree and m ≡ 2 or 3 (mod 4).

## 3. What must keep working

- The two specialisations, for every integer m: 4m + 1 is a fundamental discriminant iff it is
  squarefree; 4m is one iff m is squarefree and m ≡ 2 or 3 (mod 4).
- Two basic facts: a fundamental discriminant is nonzero, and is congruent to 0 or 1 modulo 4.
- No existing declaration is renamed, removed or restated.

## 4. Open questions

- **Is 1 a fundamental discriminant?** It meets the primitive description and the characterization
  (the case m = 0 of the first specialisation), but it is not the discriminant of a quadratic field,
  and references differ. Reading (a): admit 1, and 2-3 hold as stated. Reading (b): exclude 1, and
  the characterization and the 4m + 1 statement carry the exception D ≠ 1.
- **Which formulation is the definition.** The primitive description, the squarefree
  characterization or another equivalent condition could be primary, with the others proved.
- **Relation to quadratic fields.** One reading keeps the notion as elementary integer arithmetic;
  another ties it to discriminants of quadratic fields ℚ(√d), or proves that link, here.
- **Further scope.** Whether deciding the property for concrete integers, or writing every nonzero
  discriminant as f²·D₀ with D₀ fundamental, belongs here.
- **The base files.** The general files supplied (primes, squarefree numbers, coprimality) are ones
  the contribution touches; what it adds there, if anything, is open.

## 5. Where the requirements come from

- The description is withheld from this packet (not recoverable as it stood at review start).
- The notion: the title, which names fundamental discriminants (the current title, not verified to
  be the one at review time); and the change itself, which adds a definition of this property.
- Integers of either sign: the change itself (defined on all integers) and the term's standard meaning.
- The characterization: the change itself (its main theorem).
- The specialisations and basic facts: the change itself, which proves each.
- Nothing existing changes: the change itself only adds declarations.
