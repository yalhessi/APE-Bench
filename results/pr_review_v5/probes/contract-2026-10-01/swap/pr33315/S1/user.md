# Pull request #33315

**Title:** doc(Data): fix file refs

**Description:**
Fix some stale documentation file refs.

**Changed files:**
  - `Mathlib/Data/Array/Defs.lean`
  - `Mathlib/Data/Complex/Basic.lean`
  - `Mathlib/Data/Fin/Tuple/NatAntidiagonal.lean`
  - `Mathlib/Data/Finset/Defs.lean`
  - `Mathlib/Data/Finsupp/MonomialOrder.lean`
  - `Mathlib/Data/List/Lex.lean`
  - `Mathlib/Data/Matrix/Mul.lean`
  - `Mathlib/Data/Nat/Init.lean`
  - `Mathlib/Data/Option/Defs.lean`
  - `Mathlib/Data/Set/Basic.lean`
  - `Mathlib/Data/Vector3.lean`

**Tools available:** read files, grep the repo (content_search), find files by name (file_search), compile your edit against the reviewed workspace (lean_verify_edit)


---

## The PR model (pass 0)

# The PR model for #33315 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: doc(Data): fix file refs
- description: Fix some stale documentation file refs.
- changed files: Mathlib/Data/Array/Defs.lean, Mathlib/Data/Complex/Basic.lean, Mathlib/Data/Fin/Tuple/NatAntidiagonal.lean, Mathlib/Data/Finset/Defs.lean, Mathlib/Data/Finsupp/MonomialOrder.lean, Mathlib/Data/List/Lex.lean, Mathlib/Data/Matrix/Mul.lean, Mathlib/Data/Nat/Init.lean, Mathlib/Data/Option/Defs.lean, Mathlib/Data/Set/Basic.lean, Mathlib/Data/Vector3.lean

## Objects

### `module_doc in Defs.lean` (module_doc, modified) [bec76eba36]
- file: `Mathlib/Data/Array/Defs.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
## Definitions on Arrays

This file contains various definitions on `Array`. It does not contain
proofs about these definitions, those are contained in other files in `Mathlib/Data/Array.lean`.
-/
```
- as the PR leaves it:
```lean
/-!
# Definitions on Arrays

This file contains various definitions on `Array`. It does not contain
proofs about these definitions.
-/
```

### `command in Basic.lean` (command, modified) [fa1c7175f2]
- file: `Mathlib/Data/Complex/Basic.lean`; changed: value_or_body:modified
- before the PR:
```lean
/-- Scalar multiplication by `R` on `ℝ` extends to `ℂ`. This is used here and in
`Mathlib/Data/Complex/Module.lean` to transfer instances from `ℝ` to `ℂ`, but is not
needed outside, so we make it scoped. -/
```
- as the PR leaves it:
```lean
/-- Scalar multiplication by `R` on `ℝ` extends to `ℂ`. This is used here and in
`Mathlib/LinearAlgebra/Complex/Module.lean` to transfer instances from `ℝ` to `ℂ`, but is not
needed outside, so we make it scoped. -/
```

### `module_doc in NatAntidiagonal.lean` (module_doc, modified) [bbbe0f6880]
- file: `Mathlib/Data/Fin/Tuple/NatAntidiagonal.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Collections of tuples of naturals with the same sum

This file generalizes `List.Nat.Antidiagonal n`, `Multiset.Nat.Antidiagonal n`, and
`Finset.Nat.Antidiagonal n` from the pair of elements `x : ℕ × ℕ` such that `n = x.1 + x.2`, to
the sequence of elements `x : Fin k → ℕ` such that `n = ∑ i, x i`.

## Main definitions

* `List.Nat.antidiagonalTuple`
* `Multiset.Nat.antidiagonalTuple`
* `Finset.Nat.antidiagonalTuple`

## Main results

* `antidiagonalTuple 2 n` is analogous to `antidiagonal n`:

  * `List.Nat.antidiagonalTuple_two`
  * `Multiset.Nat.antidiagonalTuple_two`
  * `Finset.Nat.antidiagonalTuple_two`

## Implementation notes

While we could implement this by filtering `(Fintype.PiFinset fun _ ↦ range (n + 1))` or similar,
this implementation would be much slower.

In the future, we could consider generalizing `Finset.Nat.antidiagonalTuple` further to
support finitely-supported functions, as is done with `cut` in
`archive/100-theorems-list/45_partition.lean`.
-/
```
- as the PR leaves it:
```lean
/-!
# Collections of tuples of naturals with the same sum

This file generalizes `List.Nat.Antidiagonal n`, `Multiset.Nat.Antidiagonal n`, and
`Finset.Nat.Antidiagonal n` from the pair of elements `x : ℕ × ℕ` such that `n = x.1 + x.2`, to
the sequence of elements `x : Fin k → ℕ` such that `n = ∑ i, x i`.

## Main definitions

* `List.Nat.antidiagonalTuple`
* `Multiset.Nat.antidiagonalTuple`
* `Finset.Nat.antidiagonalTuple`

## Main results

* `antidiagonalTuple 2 n` is analogous to `antidiagonal n`:

  * `List.Nat.antidiagonalTuple_two`
  * `Multiset.Nat.antidiagonalTuple_two`
  * `Finset.Nat.antidiagonalTuple_two`

## Implementation notes

While we could implement this by filtering `(Fintype.PiFinset fun _ ↦ range (n + 1))` or similar,
this implementation would be much slower.

In the future, we could consider generalizing `Finset.Nat.antidiagonalTuple` further to
support finitely-supported functions, as in `Finset.finsuppAntidiag` from
`Mathlib/Algebra/Order/Antidiag/Finsupp.lean`.
-/
```

### `module_doc in Defs.lean` (module_doc, modified) [8e4cef9f10]
- file: `Mathlib/Data/Finset/Defs.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Finite sets

Terms of type `Finset α` are one way of talking about finite subsets of `α` in Mathlib.
Below, `Finset α` is defined as a structure with 2 fields:

  1. `val` is a `Multiset α` of elements;
  2. `nodup` is a proof that `val` has no duplicates.

Finsets in Lean are constructive in that they have an underlying `List` that enumerates their
elements. In particular, any function that uses the data of the underlying list cannot depend on its
ordering. This is handled on the `Multiset` level by multiset API, so in most cases one needn't
worry about it explicitly.

Finsets give a basic foundation for defining finite sums and products over types:

  1. `∑ i ∈ (s : Finset α), f i`;
  2. `∏ i ∈ (s : Finset α), f i`.

Lean refers to these operations as big operators.
More information can be found in `Mathlib/Algebra/BigOperators/Group/Finset.lean`.

Finsets are directly used to define fintypes in Lean.
A `Fintype α` instance for a type `α` consists of a universal `Finset α` containing every term of
`α`, called `univ`. See `Mathlib/Data/Fintype/Basic.lean`.

`Finset.card`, the size of a finset is defined in `Mathlib/Data/Finset/Card.lean`.
This is then used to define `Fintype.card`, the size of a type.

## File structure

This file defines the `Finset` type and the membership and subset relations between finsets.
Most constructions involving `Finset`s have been split off to their own files.

## Main definitions

* `Finset`: Defines a type for the finite subsets of `α`.
  Constructing a `Finset` requires two pieces of data: `val`, a `Multiset α` of elements,
  and `nodup`, a proof that `val` has no duplicates.
* `Finset.instMembershipFinset`: Defines membership `a ∈ (s : Finset α)`.
* `Finset.instSetLike`: Provides a coercion `s : Finset α` to `s : Set α`.
* `Finset.instCoeSortFinsetType`: Coerce `s : Finset α` to the type of all `x ∈ s`.

## Tags

finite sets, finset

-/
```
- as the PR leaves it:
```lean
/-!
# Finite sets

Terms of type `Finset α` are one way of talking about finite subsets of `α` in Mathlib.
Below, `Finset α` is defined as a structure with 2 fields:

  1. `val` is a `Multiset α` of elements;
  2. `nodup` is a proof that `val` has no duplicates.

Finsets in Lean are constructive in that they have an underlying `List` that enumerates their
elements. In particular, any function that uses the data of the underlying list cannot depend on its
ordering. This is handled on the `Multiset` level by multiset API, so in most cases one needn't
worry about it explicitly.

Finsets give a basic foundation for defining finite sums and products over types:

  1. `∑ i ∈ (s : Finset α), f i`;
  2. `∏ i ∈ (s : Finset α), f i`.

Lean refers to these operations as big operators.
More information can be found in `Mathlib/Algebra/BigOperators/Group/Finset/Basic.lean`.

Finsets are directly used to define fintypes in Lean.
A `Fintype α` instance for a type `α` consists of a universal `Finset α` containing every term of
`α`, called `univ`. See `Mathlib/Data/Fintype/Basic.lean`.

`Finset.card`, the size of a finset is defined in `Mathlib/Data/Finset/Card.lean`.
This is then used to define `Fintype.card`, the size of a type.

## File structure

This file defines the `Finset` type and the membership and subset relations between finsets.
Most constructions involving `Finset`s have been split off to their own files.

## Main definitions

* `Finset`: Defines a type for the finite subsets of `α`.
  Constructing a `Finset` requires two pieces of data: `val`, a `Multiset α` of elements,
  and `nodup`, a proof that `val` has no duplicates.
* `Finset.instMembershipFinset`: Defines membership `a ∈ (s : Finset α)`.
* `Finset.instSetLike`: Provides a coercion `s : Finset α` to `s : Set α`.
* `Finset.instCoeSortFinsetType`: Coerce `s : Finset α` to the type of all `x ∈ s`.

## Tags

finite sets, finset

-/
```

### `module_doc in MonomialOrder.lean` (module_doc, modified) [4dbc335ad5]
- file: `Mathlib/Data/Finsupp/MonomialOrder.lean`; changed: documentation:modified
- before the PR:
```lean
/-! # Monomial orders

## Monomial orders

A *monomial order* is well ordering relation on a type of the form `σ →₀ ℕ` which
is compatible with addition and for which `0` is the smallest element.
Since several monomial orders may have to be used simultaneously, one cannot
get them as instances.

In this formalization, they are presented as a structure `MonomialOrder` which encapsulates
`MonomialOrder.toSyn`, an additive and monotone isomorphism to a linearly ordered cancellative
additive commutative monoid.
The entry `MonomialOrder.wf` asserts that `MonomialOrder.syn` is well founded.

The terminology comes from commutative algebra and algebraic geometry, especially Gröbner bases,
where `c : σ →₀ ℕ` are exponents of monomials.

Given a monomial order `m : MonomialOrder σ`, we provide the notation
`c ≼[m] d` and `c ≺[m] d` to compare `c d : σ →₀ ℕ` with respect to `m`.
It is activated using `open scoped MonomialOrder`.

## Examples

Commutative algebra defines many monomial orders, with different usefulness ranges.
In this file, we provide the basic example of lexicographic ordering.
For the graded lexicographic ordering, see `Mathlib/Data/Finsupp/DegLex.lean`

* `MonomialOrder.lex` : the lexicographic ordering on `σ →₀ ℕ`.
For this, `σ` needs to be embedded with an ordering relation which satisfies `WellFoundedGT σ`.
(This last property is automatic when `σ` is finite).

The type synonym is `Lex (σ →₀ ℕ)` and the two lemmas `MonomialOrder.lex_le_iff`
and `MonomialOrder.lex_lt_iff` rewrite the ordering as comparisons in the type `Lex (σ →₀ ℕ)`.

## References

* [Cox, Little and O'Shea, *Ideals, varieties, and algorithms*][coxlittleoshea1997]
* [Becker and Weispfenning, *Gröbner bases*][Becker-Weispfenning1993]

## Note

In algebraic geometry, when the finitely many variables are indexed by integers,
it is customary to order them using the opposite order : `MvPolynomial.X 0 > MvPolynomial.X 1 > … `

-/
```
- as the PR leaves it:
```lean
/-! # Monomial orders

## Monomial orders

A *monomial order* is well ordering relation on a type of the form `σ →₀ ℕ` which
is compatible with addition and for which `0` is the smallest element.
Since several monomial orders may have to be used simultaneously, one cannot
get them as instances.

In this formalization, they are presented as a structure `MonomialOrder` which encapsulates
`MonomialOrder.toSyn`, an additive and monotone isomorphism to a linearly ordered cancellative
additive commutative monoid.
The entry `MonomialOrder.wf` asserts that `MonomialOrder.syn` is well founded.

The terminology comes from commutative algebra and algebraic geometry, especially Gröbner bases,
where `c : σ →₀ ℕ` are exponents of monomials.

Given a monomial order `m : MonomialOrder σ`, we provide the notation
`c ≼[m] d` and `c ≺[m] d` to compare `c d : σ →₀ ℕ` with respect to `m`.
It is activated using `open scoped MonomialOrder`.

## Examples

Commutative algebra defines many monomial orders, with different usefulness ranges.
In this file, we provide the basic example of lexicographic ordering.
For the graded lexicographic ordering, see `Mathlib/Data/Finsupp/MonomialOrder/DegLex.lean`

* `MonomialOrder.lex` : the lexicographic ordering on `σ →₀ ℕ`.
For this, `σ` needs to be embedded with an ordering relation which satisfies `WellFoundedGT σ`.
(This last property is automatic when `σ` is finite).

The type synonym is `Lex (σ →₀ ℕ)` and the two lemmas `MonomialOrder.lex_le_iff`
and `MonomialOrder.lex_lt_iff` rewrite the ordering as comparisons in the type `Lex (σ →₀ ℕ)`.

## References

* [Cox, Little and O'Shea, *Ideals, varieties, and algorithms*][coxlittleoshea1997]
* [Becker and Weispfenning, *Gröbner bases*][Becker-Weispfenning1993]

## Note

In algebraic geometry, when the finitely many variables are indexed by integers,
it is customary to order them using the opposite order : `MvPolynomial.X 0 > MvPolynomial.X 1 > … `

-/
```

### `module_doc in Lex.lean` (module_doc, modified) [291ca1a337]
- file: `Mathlib/Data/List/Lex.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Lexicographic ordering of lists.

The lexicographic order on `List α` is defined by `L < M` iff
* `[] < (a :: L)` for any `a` and `L`,
* `(a :: L) < (b :: M)` where `a < b`, or
* `(a :: L) < (a :: M)` where `L < M`.

## See also

Related files are:
* `Mathlib/Data/Finset/Colex.lean`: Colexicographic order on finite sets.
* `Mathlib/Data/PSigma/Order.lean`: Lexicographic order on `Σ' i, α i`.
* `Mathlib/Data/Pi/Lex.lean`: Lexicographic order on `Πₗ i, α i`.
* `Mathlib/Data/Sigma/Order.lean`: Lexicographic order on `Σ i, α i`.
* `Mathlib/Data/Prod/Lex.lean`: Lexicographic order on `α × β`.
-/
```
- as the PR leaves it:
```lean
/-!
# Lexicographic ordering of lists.

The lexicographic order on `List α` is defined by `L < M` iff
* `[] < (a :: L)` for any `a` and `L`,
* `(a :: L) < (b :: M)` where `a < b`, or
* `(a :: L) < (a :: M)` where `L < M`.

## See also

Related files are:
* `Mathlib/Combinatorics/Colex.lean`: Colexicographic order on finite sets.
* `Mathlib/Data/PSigma/Order.lean`: Lexicographic order on `Σ' i, α i`.
* `Mathlib/Order/PiLex.lean`: Lexicographic order on `Πₗ i, α i`.
* `Mathlib/Data/Sigma/Order.lean`: Lexicographic order on `Σ i, α i`.
* `Mathlib/Data/Prod/Lex.lean`: Lexicographic order on `α × β`.
-/
```

### `module_doc in Mul.lean` (module_doc, modified) [c90b8b1ac4]
- file: `Mathlib/Data/Matrix/Mul.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Matrix multiplication

This file defines vector and matrix multiplication

## Main definitions
* `dotProduct`: the dot product between two vectors
* `Matrix.mul`: multiplication of two matrices
* `Matrix.mulVec`: multiplication of a matrix with a vector
* `Matrix.vecMul`: multiplication of a vector with a matrix
* `Matrix.vecMulVec`: multiplication of a vector with a vector to get a matrix
* `Matrix.instRing`: square matrices form a ring

## Notation

The scope `Matrix` gives the following notation:

* `⬝ᵥ` for `dotProduct`
* `*ᵥ` for `Matrix.mulVec`
* `ᵥ*` for `Matrix.vecMul`

See `Mathlib/Data/Matrix/ConjTranspose.lean` for

* `ᴴ` for `Matrix.conjTranspose`

## Implementation notes

For convenience, `Matrix m n α` is defined as `m → n → α`, as this allows elements of the matrix
to be accessed with `A i j`. However, it is not advisable to _construct_ matrices using terms of the
form `fun i j ↦ _` or even `(fun i j ↦ _ : Matrix m n α)`, as these are not recognized by Lean
as having the right type. Instead, `Matrix.of` should be used.

## TODO

Under various conditions, multiplication of infinite matrices makes sense.
These have not yet been implemented.
-/
```
- as the PR leaves it:
```lean
/-!
# Matrix multiplication

This file defines vector and matrix multiplication

## Main definitions
* `dotProduct`: the dot product between two vectors
* `Matrix.mul`: multiplication of two matrices
* `Matrix.mulVec`: multiplication of a matrix with a vector
* `Matrix.vecMul`: multiplication of a vector with a matrix
* `Matrix.vecMulVec`: multiplication of a vector with a vector to get a matrix
* `Matrix.instRing`: square matrices form a ring

## Notation

The scope `Matrix` gives the following notation:

* `⬝ᵥ` for `dotProduct`
* `*ᵥ` for `Matrix.mulVec`
* `ᵥ*` for `Matrix.vecMul`

See `Mathlib/LinearAlgebra/Matrix/ConjTranspose.lean` for

* `ᴴ` for `Matrix.conjTranspose`

## Implementation notes

For convenience, `Matrix m n α` is defined as `m → n → α`, as this allows elements of the matrix
to be accessed with `A i j`. However, it is not advisable to _construct_ matrices using terms of the
form `fun i j ↦ _` or even `(fun i j ↦ _ : Matrix m n α)`, as these are not recognized by Lean
as having the right type. Instead, `Matrix.of` should be used.

## TODO

Under various conditions, multiplication of infinite matrices makes sense.
These have not yet been implemented.
-/
```

### `command in Init.lean` (command, modified) [56f58eb178]
- file: `Mathlib/Data/Nat/Init.lean`; changed: value_or_body:modified
- before the PR:
```lean
@[expose] public section

library_note2 «foundational algebra order theory» /--
Batteries has a home-baked development of the algebraic and order-theoretic theory of `ℕ` and `ℤ`
which, in particular, is not typeclass-mediated. This is useful to set up the algebra and finiteness
libraries in mathlib (naturals and integers show up as indices/offsets in lists, cardinality in
finsets, powers in groups, ...).

Less basic uses of `ℕ` and `ℤ` should however use the typeclass-mediated development.

The relevant files are:
* `Mathlib/Data/Nat/Basic.lean` for the continuation of the home-baked development on `ℕ`
* `Mathlib/Data/Int/Init.lean` for the continuation of the home-baked development on `ℤ`
* `Mathlib/Algebra/Group/Nat.lean` for the monoid instances on `ℕ`
* `Mathlib/Algebra/Group/Int.lean` for the group instance on `ℤ`
* `Mathlib/Algebra/Ring/Nat.lean` for the semiring instance on `ℕ`
* `Mathlib/Algebra/Ring/Int.lean` for the ring instance on `ℤ`
* `Mathlib/Algebra/Order/Group/Nat.lean` for the ordered monoid instance on `ℕ`
* `Mathlib/Algebra/Order/Group/Int.lean` for the ordered group instance on `ℤ`
* `Mathlib/Algebra/Order/Ring/Nat.lean` for the ordered semiring instance on `ℕ`
* `Mathlib/Algebra/Order/Ring/Int.lean` for the ordered ring instance on `ℤ`
-/

/- We don't want to import the algebraic hierarchy in this file. -/
assert_not_exists Monoid
```
- as the PR leaves it:
```lean
@[expose] public section

library_note2 «foundational algebra order theory» /--
Batteries has a home-baked development of the algebraic and order-theoretic theory of `ℕ` and `ℤ`
which, in particular, is not typeclass-mediated. This is useful to set up the algebra and finiteness
libraries in mathlib (naturals and integers show up as indices/offsets in lists, cardinality in
finsets, powers in groups, ...).

Less basic uses of `ℕ` and `ℤ` should however use the typeclass-mediated development.

The relevant files are:
* `Mathlib/Data/Nat/Basic.lean` for the continuation of the home-baked development on `ℕ`
* `Mathlib/Data/Int/Init.lean` for the continuation of the home-baked development on `ℤ`
* `Mathlib/Algebra/Group/Nat/Defs.lean` for the monoid instances on `ℕ`
* `Mathlib/Algebra/Group/Int/Defs.lean` for the group instance on `ℤ`
* `Mathlib/Algebra/Ring/Nat.lean` for the semiring instance on `ℕ`
* `Mathlib/Algebra/Ring/Int/Defs.lean` for the ring instance on `ℤ`
* `Mathlib/Algebra/Order/Group/Nat.lean` for the ordered monoid instance on `ℕ`
* `Mathlib/Algebra/Order/Group/Int.lean` for the ordered group instance on `ℤ`
* `Mathlib/Algebra/Order/Ring/Nat.lean` for the ordered semiring instance on `ℕ`
* `Mathlib/Algebra/Order/Ring/Int.lean` for the ordered ring instance on `ℤ`
-/

/- We don't want to import the algebraic hierarchy in this file. -/
assert_not_exists Monoid
```

### `module_doc in Defs.lean` (module_doc, modified) [c7eff15b67]
- file: `Mathlib/Data/Option/Defs.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Extra definitions on `Option`

This file defines more operations involving `Option α`. Lemmas about them are located in other
files under `Mathlib/Data/Option.lean`.
Other basic operations on `Option` are defined in the core library.
-/
```
- as the PR leaves it:
```lean
/-!
# Extra definitions on `Option`

This file defines more operations involving `Option α`. Lemmas about them are located in other
files under `Mathlib/Data/Option/`.
Other basic operations on `Option` are defined in the core library.
-/
```

### `module_doc in Basic.lean` (module_doc, modified) [fe3f595e6f]
- file: `Mathlib/Data/Set/Basic.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Basic properties of sets

Sets in Lean are homogeneous; all their elements have the same type. Sets whose elements
have type `X` are thus defined as `Set X := X → Prop`. Note that this function need not
be decidable. The definition is in the module `Mathlib/Data/Set/Defs.lean`.

This file provides some basic definitions related to sets and functions not present in the
definitions file, as well as extra lemmas for functions defined in the definitions file and
`Mathlib/Data/Set/Operations.lean` (empty set, univ, union, intersection, insert, singleton and
powerset).

Note that a set is a term, not a type. There is a coercion from `Set α` to `Type*` sending
`s` to the corresponding subtype `↥s`.

See also the file `SetTheory/ZFC.lean`, which contains an encoding of ZFC set theory in Lean.

## Main definitions

Notation used here:

-  `f : α → β` is a function,

-  `s : Set α` and `s₁ s₂ : Set α` are subsets of `α`

-  `t : Set β` is a subset of `β`.

Definitions in the file:

* `Nonempty s : Prop` : the predicate `s ≠ ∅`. Note that this is the preferred way to express the
  fact that `s` has an element (see the Implementation Notes).

* `inclusion s₁ s₂ : ↥s₁ → ↥s₂` : the map `↥s₁ → ↥s₂` induced by an inclusion `s₁ ⊆ s₂`.

## Implementation notes

* `s.Nonempty` is to be preferred to `s ≠ ∅` or `∃ x, x ∈ s`. It has the advantage that
  the `s.Nonempty` dot notation can be used.

* For `s : Set α`, do not use `Subtype s`. Instead use `↥s` or `(s : Type*)` or `s`.

## Tags

set, sets, subset, subsets, union, intersection, insert, singleton, powerset
-/
```
- as the PR leaves it:
```lean
/-!
# Basic properties of sets

Sets in Lean are homogeneous; all their elements have the same type. Sets whose elements
have type `X` are thus defined as `Set X := X → Prop`. Note that this function need not
be decidable. The definition is in the module `Mathlib/Data/Set/Defs.lean`.

This file provides some basic definitions related to sets and functions not present in the
definitions file, as well as extra lemmas for functions defined in the definitions file and
`Mathlib/Data/Set/Operations.lean` (empty set, univ, union, intersection, insert, singleton and
powerset).

Note that a set is a term, not a type. There is a coercion from `Set α` to `Type*` sending
`s` to the corresponding subtype `↥s`.

See also the directory `Mathlib/SetTheory/ZFC/`, which contains an encoding of ZFC set theory in
Lean.

## Main definitions

Notation used here:

-  `f : α → β` is a function,

-  `s : Set α` and `s₁ s₂ : Set α` are subsets of `α`

-  `t : Set β` is a subset of `β`.

Definitions in the file:

* `Nonempty s : Prop` : the predicate `s ≠ ∅`. Note that this is the preferred way to express the
  fact that `s` has an element (see the Implementation Notes).

* `inclusion s₁ s₂ : ↥s₁ → ↥s₂` : the map `↥s₁ → ↥s₂` induced by an inclusion `s₁ ⊆ s₂`.

## Implementation notes

* `s.Nonempty` is to be preferred to `s ≠ ∅` or `∃ x, x ∈ s`. It has the advantage that
  the `s.Nonempty` dot notation can be used.

* For `s : Set α`, do not use `Subtype s`. Instead use `↥s` or `(s : Type*)` or `s`.

## Tags

set, sets, subset, subsets, union, intersection, insert, singleton, powerset
-/
```

### `Vector3.unexpandNil` (def, modified) [0f5d0b223a]
- file: `Mathlib/Data/Vector3.lean`; changed: documentation:modified
- before the PR:
```lean
@[app_unexpander Vector3.nil] meta def unexpandNil : Lean.PrettyPrinter.Unexpander
  | `($(_)) => `([])

-- this is copied from `src/Init/NotationExtra.lean`
```
- as the PR leaves it:
```lean
@[app_unexpander Vector3.nil] meta def unexpandNil : Lean.PrettyPrinter.Unexpander
  | `($(_)) => `([])

-- this is copied from `Init/NotationExtra.lean` (Lean core)
```

### `command in Vector3.lean` (command, modified) [19163a8d05]
- file: `Mathlib/Data/Vector3.lean`; changed: value_or_body:modified
- before the PR:
```lean
scoped macro_rules | `([$l,*]) => `(expand_foldr% (h t => cons h t) nil [$(.ofElems l),*])

-- this is copied from `src/Init/NotationExtra.lean`
```
- as the PR leaves it:
```lean
scoped macro_rules | `([$l,*]) => `(expand_foldr% (h t => cons h t) nil [$(.ofElems l),*])

-- this is copied from `Init/NotationExtra.lean` (Lean core)
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- none found by the change graph

## Relations between changed declarations

- none

---

## The diff

```diff
diff --git a/Mathlib/Data/Array/Defs.lean b/Mathlib/Data/Array/Defs.lean
--- a/Mathlib/Data/Array/Defs.lean
+++ b/Mathlib/Data/Array/Defs.lean
@@ -7,10 +7,10 @@ module
 
 public import Mathlib.Init
 /-!
-## Definitions on Arrays
+# Definitions on Arrays
 
 This file contains various definitions on `Array`. It does not contain
-proofs about these definitions, those are contained in other files in `Mathlib/Data/Array.lean`.
+proofs about these definitions.
 -/
 
 @[expose] public section
diff --git a/Mathlib/Data/Complex/Basic.lean b/Mathlib/Data/Complex/Basic.lean
--- a/Mathlib/Data/Complex/Basic.lean
+++ b/Mathlib/Data/Complex/Basic.lean
@@ -291,7 +291,7 @@ namespace SMul
 -- instance made scoped to avoid situations like instance synthesis
 -- of `SMul ℂ ℂ` trying to proceed via `SMul ℂ ℝ`.
 /-- Scalar multiplication by `R` on `ℝ` extends to `ℂ`. This is used here and in
-`Mathlib/Data/Complex/Module.lean` to transfer instances from `ℝ` to `ℂ`, but is not
+`Mathlib/LinearAlgebra/Complex/Module.lean` to transfer instances from `ℝ` to `ℂ`, but is not
 needed outside, so we make it scoped. -/
 scoped instance instSMulRealComplex {R : Type*} [SMul R ℝ] : SMul R ℂ where
   smul r x := ⟨r • x.re - 0 * x.im, r • x.im + 0 * x.re⟩
diff --git a/Mathlib/Data/Fin/Tuple/NatAntidiagonal.lean b/Mathlib/Data/Fin/Tuple/NatAntidiagonal.lean
--- a/Mathlib/Data/Fin/Tuple/NatAntidiagonal.lean
+++ b/Mathlib/Data/Fin/Tuple/NatAntidiagonal.lean
@@ -37,8 +37,8 @@ While we could implement this by filtering `(Fintype.PiFinset fun _ ↦ range (n
 this implementation would be much slower.
 
 In the future, we could consider generalizing `Finset.Nat.antidiagonalTuple` further to
-support finitely-supported functions, as is done with `cut` in
-`archive/100-theorems-list/45_partition.lean`.
+support finitely-supported functions, as in `Finset.finsuppAntidiag` from
+`Mathlib/Algebra/Order/Antidiag/Finsupp.lean`.
 -/
 
 @[expose] public section
diff --git a/Mathlib/Data/Finset/Defs.lean b/Mathlib/Data/Finset/Defs.lean
--- a/Mathlib/Data/Finset/Defs.lean
+++ b/Mathlib/Data/Finset/Defs.lean
@@ -31,7 +31,7 @@ Finsets give a basic foundation for defining finite sums and products over types
   2. `∏ i ∈ (s : Finset α), f i`.
 
 Lean refers to these operations as big operators.
-More information can be found in `Mathlib/Algebra/BigOperators/Group/Finset.lean`.
+More information can be found in `Mathlib/Algebra/BigOperators/Group/Finset/Basic.lean`.
 
 Finsets are directly used to define fintypes in Lean.
 A `Fintype α` instance for a type `α` consists of a universal `Finset α` containing every term of
diff --git a/Mathlib/Data/Finsupp/MonomialOrder.lean b/Mathlib/Data/Finsupp/MonomialOrder.lean
--- a/Mathlib/Data/Finsupp/MonomialOrder.lean
+++ b/Mathlib/Data/Finsupp/MonomialOrder.lean
@@ -34,7 +34,7 @@ It is activated using `open scoped MonomialOrder`.
 
 Commutative algebra defines many monomial orders, with different usefulness ranges.
 In this file, we provide the basic example of lexicographic ordering.
-For the graded lexicographic ordering, see `Mathlib/Data/Finsupp/DegLex.lean`
+For the graded lexicographic ordering, see `Mathlib/Data/Finsupp/MonomialOrder/DegLex.lean`
 
 * `MonomialOrder.lex` : the lexicographic ordering on `σ →₀ ℕ`.
 For this, `σ` needs to be embedded with an ordering relation which satisfies `WellFoundedGT σ`.
diff --git a/Mathlib/Data/List/Lex.lean b/Mathlib/Data/List/Lex.lean
--- a/Mathlib/Data/List/Lex.lean
+++ b/Mathlib/Data/List/Lex.lean
@@ -20,9 +20,9 @@ The lexicographic order on `List α` is defined by `L < M` iff
 ## See also
 
 Related files are:
-* `Mathlib/Data/Finset/Colex.lean`: Colexicographic order on finite sets.
+* `Mathlib/Combinatorics/Colex.lean`: Colexicographic order on finite sets.
 * `Mathlib/Data/PSigma/Order.lean`: Lexicographic order on `Σ' i, α i`.
-* `Mathlib/Data/Pi/Lex.lean`: Lexicographic order on `Πₗ i, α i`.
+* `Mathlib/Order/PiLex.lean`: Lexicographic order on `Πₗ i, α i`.
 * `Mathlib/Data/Sigma/Order.lean`: Lexicographic order on `Σ i, α i`.
 * `Mathlib/Data/Prod/Lex.lean`: Lexicographic order on `α × β`.
 -/
diff --git a/Mathlib/Data/Matrix/Mul.lean b/Mathlib/Data/Matrix/Mul.lean
--- a/Mathlib/Data/Matrix/Mul.lean
+++ b/Mathlib/Data/Matrix/Mul.lean
@@ -32,7 +32,7 @@ The scope `Matrix` gives the following notation:
 * `*ᵥ` for `Matrix.mulVec`
 * `ᵥ*` for `Matrix.vecMul`
 
-See `Mathlib/Data/Matrix/ConjTranspose.lean` for
+See `Mathlib/LinearAlgebra/Matrix/ConjTranspose.lean` for
 
 * `ᴴ` for `Matrix.conjTranspose`
 
diff --git a/Mathlib/Data/Nat/Init.lean b/Mathlib/Data/Nat/Init.lean
--- a/Mathlib/Data/Nat/Init.lean
+++ b/Mathlib/Data/Nat/Init.lean
@@ -46,10 +46,10 @@ Less basic uses of `ℕ` and `ℤ` should however use the typeclass-mediated dev
 The relevant files are:
 * `Mathlib/Data/Nat/Basic.lean` for the continuation of the home-baked development on `ℕ`
 * `Mathlib/Data/Int/Init.lean` for the continuation of the home-baked development on `ℤ`
-* `Mathlib/Algebra/Group/Nat.lean` for the monoid instances on `ℕ`
-* `Mathlib/Algebra/Group/Int.lean` for the group instance on `ℤ`
+* `Mathlib/Algebra/Group/Nat/Defs.lean` for the monoid instances on `ℕ`
+* `Mathlib/Algebra/Group/Int/Defs.lean` for the group instance on `ℤ`
 * `Mathlib/Algebra/Ring/Nat.lean` for the semiring instance on `ℕ`
-* `Mathlib/Algebra/Ring/Int.lean` for the ring instance on `ℤ`
+* `Mathlib/Algebra/Ring/Int/Defs.lean` for the ring instance on `ℤ`
 * `Mathlib/Algebra/Order/Group/Nat.lean` for the ordered monoid instance on `ℕ`
 * `Mathlib/Algebra/Order/Group/Int.lean` for the ordered group instance on `ℤ`
 * `Mathlib/Algebra/Order/Ring/Nat.lean` for the ordered semiring instance on `ℕ`
diff --git a/Mathlib/Data/Option/Defs.lean b/Mathlib/Data/Option/Defs.lean
--- a/Mathlib/Data/Option/Defs.lean
+++ b/Mathlib/Data/Option/Defs.lean
@@ -13,7 +13,7 @@ public import Batteries.Tactic.Alias
 # Extra definitions on `Option`
 
 This file defines more operations involving `Option α`. Lemmas about them are located in other
-files under `Mathlib/Data/Option.lean`.
+files under `Mathlib/Data/Option/`.
 Other basic operations on `Option` are defined in the core library.
 -/
 
diff --git a/Mathlib/Data/Set/Basic.lean b/Mathlib/Data/Set/Basic.lean
--- a/Mathlib/Data/Set/Basic.lean
+++ b/Mathlib/Data/Set/Basic.lean
@@ -25,7 +25,8 @@ powerset).
 Note that a set is a term, not a type. There is a coercion from `Set α` to `Type*` sending
 `s` to the corresponding subtype `↥s`.
 
-See also the file `SetTheory/ZFC.lean`, which contains an encoding of ZFC set theory in Lean.
+See also the directory `Mathlib/SetTheory/ZFC/`, which contains an encoding of ZFC set theory in
+Lean.
 
 ## Main definitions
 
diff --git a/Mathlib/Data/Vector3.lean b/Mathlib/Data/Vector3.lean
--- a/Mathlib/Data/Vector3.lean
+++ b/Mathlib/Data/Vector3.lean
@@ -52,12 +52,12 @@ open Lean
 
 scoped macro_rules | `([$l,*]) => `(expand_foldr% (h t => cons h t) nil [$(.ofElems l),*])
 
--- this is copied from `src/Init/NotationExtra.lean`
+-- this is copied from `Init/NotationExtra.lean` (Lean core)
 /-- Unexpander for `Vector3.nil` -/
 @[app_unexpander Vector3.nil] meta def unexpandNil : Lean.PrettyPrinter.Unexpander
   | `($(_)) => `([])
 
--- this is copied from `src/Init/NotationExtra.lean`
+-- this is copied from `Init/NotationExtra.lean` (Lean core)
 /-- Unexpander for `Vector3.cons` -/
 @[app_unexpander Vector3.cons] meta def unexpandCons : Lean.PrettyPrinter.Unexpander
   | `($(_) $x [])      => `([$x])

```

---

When you have reviewed the PR as the brief asks, call `submit_findings`. For each finding, give:

- `path` and `line_start` -- where in the reviewed file the problem is, so the finding can be located. Give the line of the declaration your claim is about.
- `claim` -- name the declaration and say what is wrong with it.
- `suggested_fix` -- what to do instead.
- `severity` -- `blocking` if the change is needed for correctness or policy; `advisory` for every other change you would request. Advisory findings count in full.

Also give `notes`: your account of the review, with an entry for every changed declaration in the PR model (declarations of one family may share an entry). In each entry, say what you checked for that declaration under each concern that applies to it -- its proof, its statement and how general it is, whether the library already has it, its name, its docstring, its attributes and placement -- and close it with what you concluded, "nothing to ask" included.

Finish by calling `submit_findings` once. If there is nothing to ask, call it with an empty `findings` list and your `notes`.