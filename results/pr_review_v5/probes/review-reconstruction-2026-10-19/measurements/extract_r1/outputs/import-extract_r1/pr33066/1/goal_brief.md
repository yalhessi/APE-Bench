# Goal brief

## 1. Kind of contribution

- A new definition (a construction on existing objects).
- New results.
- Other: accompanying updates to module-level documentation of existing files.

## 2. Capability

𝕜 is ℝ or ℂ; V, W, H, K are Hilbert spaces over 𝕜. B(V), the bounded operators on V, is a
⋆-algebra over 𝕜 with the adjoint as star.

(a) For a surjective linear isometry U : H → K, conjugation x ↦ U x U⁻¹ is a ⋆-algebra isomorphism
B(H) → B(K), available as a construction from U.

(b) Every ⋆-algebra isomorphism f : B(V) → B(W) is conjugation by some surjective linear isometry
U : V → W: f(x) = U x U⁻¹ for all x. This is the ⋆-counterpart of the existing
`AlgEquiv.eq_linearEquivConjAlgEquiv` (algebra isomorphisms are conjugation by a linear isomorphism)
and `ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv` (continuous algebra
isomorphisms are conjugation by a continuous linear isomorphism), so the three kinds of isomorphism
are characterized alike.

(c) Such ⋆-isomorphisms preserve and reflect the operator order (x ≤ y when y − x is positive):
x ≤ y if and only if f(x) ≤ f(y).

## 3. What must keep working

- The two existing characterizations named in (b), and every declaration already in the changed
  files, keep their statements and names.
- (b) holds with no nontriviality assumption on V or W, zero spaces included.

## 4. Open questions

- **Continuity.** ⋆-isomorphisms of these operator algebras are automatically continuous, but
  proving that is further work. Reading 1: (b) and (c) for every ⋆-isomorphism. Reading 2: (b) and
  (c) for ⋆-isomorphisms assumed continuous, the general case left for later. The inputs do not
  decide.
- How (c) is packaged for users, and for which maps, is not settled.
- Whether constructions needed along the way become public API in existing files or stay local to
  the proof.

## 5. Where the requirements come from

- 2(b): the title (the current title, not verified to be the one at review time), which says
  ⋆-algebra isomorphisms between algebras of continuous endomorphisms are isometrically inner, and
  the description's first paragraph, which presents it as the ⋆-counterpart of the two named results.
- 2(a), 2(c): the change itself, which adds this construction and this order statement; neither title
  nor description mentions (c).
- 3: the change itself, which modifies no existing declaration and states (b) without a
  nontriviality hypothesis.
- Documentation (1): the change itself, which revises module overviews of the existing files on the
  algebraic and continuous versions.
- The description is present and verified as the text at the start of review; its other paragraphs
  concern the proof and dependencies.
