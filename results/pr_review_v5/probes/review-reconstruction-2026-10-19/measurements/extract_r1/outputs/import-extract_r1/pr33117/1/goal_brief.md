# Goal brief

## 1. Kind of contribution

A new definition, with new results about it.

## 2. Capability

Setting: functions f : 𝕜 → E as in `Mathlib/Analysis/Meromorphic/Basic.lean`, under that file's
standing assumptions on 𝕜 and E.

Provide a notion "f is meromorphic on all of 𝕜", i.e. meromorphic at every point x ∈ 𝕜, with:

- **Agreement.** f has the new property iff f is meromorphic on the whole of 𝕜 in the sense of the
  existing `MeromorphicOn`.
- **Additive closure** (E-valued): if f, g have the property, so do −f, f + g, f − g, and so does a
  finite sum ∑_{i ∈ s} G_i of such functions.
- **Multiplicative closure**, at least for scalar-valued f, g : 𝕜 → 𝕜: f · g, f / g, fⁿ (n ∈ ℕ),
  fⁿ (n ∈ ℤ) and a finite product ∏_{i ∈ s} F_i have the property.
- **Differentiation** (E-valued): if f has the property, so do f′ and the n-th iterated derivative of
  f for every n ∈ ℕ.

## 3. What must keep working

- `MeromorphicAt`, `MeromorphicOn` and every existing result in the file stay as they are; nothing
  existing is renamed, removed, deprecated or restated.
- The new notion agrees with meromorphy on all of 𝕜 in the existing sense, so a fact stated either
  way can be used in the other form.
- The scalar-valued case of each multiplicative result is covered.

## 4. Open questions

- **Scope.** Whether to also cover inverses, scalar multiplication, constants and the identity; that
  such a function is meromorphic at each point and on every subset; that analytic functions have the
  property; and whether existing statements about meromorphy on all of 𝕜 should be restated.
- **Multiplicative generality.** Whether to go beyond 𝕜-valued functions (e.g. normed-algebra-valued),
  as far as the existing pointwise results allow.
- **Finite sums and products.** Whether the hypothesis is needed for every index or only for those in
  the finite set.
- **Derivatives.** Which hypotheses on E the derivative statements need.

## 5. Where the requirements come from

- The notion and its agreement with `MeromorphicOn` on all of 𝕜: the description's single paragraph
  (verified to be the text at the start of review), which presents it as a shorthand for
  meromorphy on the whole field following a community discussion. The current title, not verified to
  be the one at review time, also announces a new notion.
- The setting: the change itself, which adds only to `Mathlib/Analysis/Meromorphic/Basic.lean`.
- The closure and derivative results, including their scalar-valued cases: the change itself; the
  description does not mention them.
- What must keep working: the change itself, which only adds declarations and modifies none.
