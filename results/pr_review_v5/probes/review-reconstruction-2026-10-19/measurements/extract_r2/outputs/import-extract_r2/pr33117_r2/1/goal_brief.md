# Goal brief

## 1. Kind of contribution

A new definition, and new results about it.

## 2. Capability

For functions f : 𝕜 → E in the setting of `Mathlib/Analysis/Meromorphic/Basic.lean`, provide a notion
"f is meromorphic on the whole of 𝕜", with:

- **(a) Agreement.** f has the new property if and only if `MeromorphicOn f` holds on all of 𝕜.
- **(b) Additive closure** (E-valued functions). If f and g have the property, so do −f, f + g and f − g;
  a finite sum ∑_{i ∈ I} f_i of functions that have the property also has it.
- **(c) Multiplicative closure**, at least for 𝕜-valued functions. If f and g have the property, so do
  f · g, f / g, fⁿ for every n ∈ ℕ and every n ∈ ℤ; a finite product ∏_{i ∈ I} f_i of functions that
  have the property also has it.
- **(d) Derivatives**, at least when E is complete. If f has the property, so do its derivative f′ and
  every iterated derivative f⁽ⁿ⁾, n ∈ ℕ.

## 3. What must keep working

- `MeromorphicAt`, `MeromorphicOn` and the existing results about them keep holding.
- Each case in (a)–(d), at least at the generality stated there.

## 4. Open questions

- **Defining form.** The description presents the notion as a short name for meromorphy on the whole
  space in the existing set-wise sense. One reading: define it literally that way. Another: define it in
  some other equivalent way and prove (a). Which, and which of the two forms is preferred when both
  appear, is not settled.
- **Codomain of (c).** Whether products, quotients and powers should hold for more general codomains
  than 𝕜.
- **Hypotheses of (d).** Whether completeness of E is needed.
- **Scope.** Which further results about the new notion belong in this contribution beyond (a)–(d).
  Also whether existing Mathlib statements phrased as meromorphy on all of 𝕜 should be restated in
  terms of the new notion, or left as they are. Both are open.

## 5. Where the requirements come from

- The notion: the description's first paragraph, and the title (the current one, not verified to be the
  one at review time). The second paragraph only links a Zulip discussion not in the inputs.
- (a): the first paragraph of the description; the change itself also proves this equivalence.
- (b), (c), (d) and their minimum generality: the change itself, which proves each case listed; the
  description does not mention them.
- Section 3: the description's first paragraph presupposes the existing set-wise notion and its results;
  the second point is the change itself.
- The description is present and verified to be the text at the start of review.
