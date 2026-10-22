# Goal brief

## Kind of contribution
A new mathematical notion and results, together with reusable elementary arithmetic results, documentation, and import integration.

## Capability
Provide a mathematical account of fundamental discriminants among the integers: the admissible integers are congruent to 0 or 1 modulo 4; when the integer is divisible by 4, writing it as 4d, require d to be neither divisible by 4 nor congruent to 1 modulo 4; and no square of an odd prime divides the integer. Give the equivalent squarefree classification: either the integer is congruent to 1 modulo 4 and squarefree, or it is divisible by 4 and its quotient by 4 is squarefree and congruent to 2 or 3 modulo 4. Also supply the arithmetic facts used in this development: integer squarefreeness can be tested by excluding divisibility by prime squares; a property of all natural primes can be checked at 2 and at odd primes; odd elements are coprime to 2; and coprimality gives the corresponding divisibility cancellation for a product. The supporting results concern the existing natural-prime material in `Mathlib/Data/Nat/Prime/Basic.lean`, squarefree material in `Mathlib/Data/Nat/Squarefree.lean`, and coprime material in `Mathlib/RingTheory/Coprime/Basic.lean`. Integrate the contribution into the library's umbrella import.

## What must keep working
Retain the stated specializations: an integer of the form 4m+1 is fundamental exactly when it is squarefree, and 4m is fundamental exactly when m is squarefree and congruent to 2 or 3 modulo 4. The basic consequences that a fundamental discriminant is nonzero and is congruent to 0 or 1 modulo 4 are also part of the supplied results.

## Open questions
The inputs do not establish whether a formal connection with quadratic fields is part of the requested deliverable or only motivation, nor whether the supporting arithmetic facts are intended as standalone library API or merely as support for the main classification. The description is absent from the packet, so it cannot resolve these scope questions.

## Where the requirements come from
The definition and squarefree classification, including the two special families and the nonzero and congruence consequences, come from the added mathematical statements in the diff. The prime, squarefree, oddness, and coprimality facts, and umbrella-import integration, likewise come from additions in the diff. The current title identifies fundamental discriminants as the topic, but it is not verified to be the title at review time. The description is absent from this packet; its review-start content is withheld and unavailable.