# Goal brief

## 1. Kind of contribution

- A new definition: the conjugation in 2(a).
- New results: 2(b) and 2(c).

## 2. Capability

Setting: V and W are Hilbert spaces over a common scalar field (see 4), possibly different; B(V),
B(W) are their algebras of continuous linear operators, with the adjoint as ⋆. A *unitary from V
onto W* is a linear bijection V → W preserving inner products.

(a) For a unitary U from V onto W, the map A ↦ UAU⁻¹ is a ⋆-algebra isomorphism B(V) → B(W), and
is available as such.

(b) A ⋆-algebra isomorphism f : B(V) → B(W) (which ones: see 4) is implemented by a unitary: for
some unitary U from V onto W, f sends each A to UAU⁻¹. This is the ⋆-algebra counterpart of the
existing `AlgEquiv.eq_linearEquivConjAlgEquiv` (algebra isomorphisms are implemented by linear isomorphisms) and
`ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv` (continuous algebra
isomorphisms by continuous linear isomorphisms).

(c) A ⋆-algebra isomorphism f : B(V) → B(W), of the same kind as in (b), preserves and reflects the
existing operator order (A ≤ B when B − A is positive): A ≤ B if and only if f(A) ≤ f(B).

## 3. What must keep working

- The two existing results named in (b), and the other existing results in the changed files, keep
  their statements; (b) sits beside the two, not in place of them.
- (b) covers the case in which V or W is the zero space.

## 4. Open questions

- Which isomorphisms (b) and (c) cover. The title states the result for star-algebra equivalences
  with no further hypothesis; the description presents it as the counterpart of the two results
  above, the second of which assumes continuity. Two readings fit: (i) every ⋆-algebra isomorphism
  B(V) → B(W); (ii) those that also satisfy a continuity hypothesis. The inputs do not say which,
  nor, under (ii), the form of the hypothesis.
- The scalar field: the inputs name none; the base defines the adjoint on B(V) over ℝ and over ℂ.
- Whether (c) belongs in this contribution; it comes from the change alone.

## 5. Where the requirements come from

- Kind and 2(a): the change itself, which adds a definition; the title's "isometrically inner"
  (current title, not verified to be the one at review time).
- 2(b): the same title, and the description's first paragraph, which names the two counterparts.
- Setting: the title's "star-algebra equivalences between continuous endomorphisms"; two spaces from
  the description's first paragraph, via the continuous counterpart.
- 2(c): the change itself; neither title nor description mentions it.
- 3: the description's first paragraph and the change itself, which alters no existing statement
  and assumes neither space nonzero.
- The description is verified to be the text at the start of review; its other paragraphs concern
  the proof and the PRs it depends on, and give no requirement.
