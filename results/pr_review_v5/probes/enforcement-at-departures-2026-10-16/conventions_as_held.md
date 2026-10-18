# The three conventions as maintainers hold them (written 2026-10-16, before any survivor is read)

Sources: Mathlib's naming page (https://leanprover-community.github.io/contribute/naming.html, read
2026-10-16), the census codebook entries, and the maintainers' own words in the census asks filed under
each entry (29 asks under P057, 17 under P108, 6 under P113, 3 under P211, 4 under P034; quoted
fragments only, bodies not committed). Each section gives the rule, its motivation in the maintainers'
words, and the scope: where it is stated or visibly not to apply. Readers use these, not the detector's
one-line shape.

## Dot notation for a call (census P057)

**Rule.** A lemma or function in namespace `T`, applied to a term whose type's head is `T`, is written
with dot notation, `x.f`, not `T.f x`. The codebook: "a namespaced function or lemma applied to a term
of that namespace's type is written with dot notation (`x.f`), not the fully qualified name".

**Motivation, in the asks.** Readability and compactness: "I feel like dot notation would look better
throughout" (on a matrix `A`, so data receivers are covered as well as hypotheses); most asks under
P057 are `suggestion` blocks rewriting a line, the dot form arriving with a golf ("If you're golfing,
I'd suggest `d.count`"). The naming page: "It is useful to use dot notation even for types which are
not inductive types."

**Scope and limits visible in the sources.** The dotted form must resolve to the same declaration (Lean
looks up `x.f` in the namespace of `x`'s type head first, so a lemma in a namespace nested under it, or a
same-named lemma in the head's namespace, makes `x.f` mean something else). Nothing in the sources
excludes term mode, tactic mode, or `simp`/`rw` lemma lists. Whether a maintainer asks for the dot form
on a line no one else is rewriting is not stated anywhere.

## Placement in the predicate's namespace (census P108)

**Rule.** The codebook: "a declaration whose main argument is a term of type `T` or a hypothesis `P x`,
or whose conclusion is `P x` *when no argument is*, is placed in `T`'s or `P`'s namespace so that it is
applied with dot notation (`h.f` or `.of_h`)". The main-argument namespace comes first; the conclusion's
namespace is the fallback.

**Motivation, in the asks.** Use through dot notation: "For dot notation?"; "then we can use dot
notation `I.rootSet` throughout below"; "if you have the expected type being `Set.Infinite _` then you
can write `.of_accPt hAccPt`". Consistency within a family: "It seems inconsistent that one lemma uses
`of_monic` while the other uses `Monic.`". A stated hesitation: "I think this name is fine, although
there might not be official policy".

**Scope and limits visible in the sources.** When a lemma has a main hypothesis (`X_of_Y`, with `Y` a
hypothesis about the main object), the rule puts it in `Y`'s namespace, not in the conclusion's; the
detector proposes the conclusion's namespace (`X.of_Y`) from the name and conclusion alone, which the
rule allows only when there is no main argument. The naming page: "Note however we do not do this for
axiomatic logical and arithmetic operations."

## Primed names (census P113, P211)

**Rule.** P113: "a lemma variant is distinguished from its siblings by naming the term of its statement
that differs, not by appending primes". P211: "a name carries a prime only to distinguish it from an
unprimed sibling that is the primary form".

**Motivation, in the asks.** Legibility of the pair: "I don't know how I'd keep straight in my mind which
one the primed/unprimed one is"; "the statement is pretty different from the version without `'`";
"the `''` version is so uninformative"; "Or docstring why prime and explain". Mathlib's naming page says
nothing about primes.

**Scope and limits visible in the sources.** P211 itself permits a prime beside a primary unprimed
sibling, so a prime is not a departure as such; the asks object where the two statements differ enough
that the prime hides how ("pretty different"), and accept an explanation in a docstring as an
alternative. The naming page's only primed name is a structure field (`map_one'`) beside its bundled
lemma, a standing Mathlib pattern.

## Primed names, revised (2026-10-16, after the first reading failed its calibration on primes)

The first version above permitted a prime beside a primary sibling and accepted a docstring as an
explanation; readers following it excluded 4 of the 6 primes maintainers had fixed. This version is
derived from the prime asks that are **not** on any calibration item (v0207, v0477, v0958, v1207, v1524,
v1552, v1935 in the window; o0202, o0840 outside it); the four asks on fixed items (v1057, v1096, v1490,
v2081) are not used, so the calibration stays held out.

**Rule.**
- A prime marks the secondary of a pair whose primary form is unprimed; maintainers assign primes that
  way on purpose ("I think you should rename `div` to `div'` and `div₀'` to `div`"). A primed name with no
  primary unprimed sibling is unprimed ("Maybe remove the prime in this one also?").
- **Where the variant differs from its sibling in something a name can say** (an extra or different
  hypothesis, a specialisation, a different function or structure, a different quantification), the
  maintainers ask for a name that says it, and a docstring does not substitute: "I know it's verbose, but
  the `''` version is so uninformative" (with a descriptive rename); a descriptive name or an
  `_of_mem_maximalIdeal` suffix in place of the prime; "Am I remembering correctly that the reason there is
  a prime here is because the unprimed version would be specialized to `n = ⊤`?".
- **A prime is accepted where it follows an established Mathlib prime pattern** whose difference is not
  naturally a word: argument order or form by analogy with `le_trans'` ("`assoc'` makes sense to me, by
  analogy with `le_trans'`"), or a name mirroring a primed component of its own statement ("`ι'_hom'` …
  I feel there should be `hom'` in the name").
- **A primed name the PR only moves or touches** is an opportunity, not a requirement: "This PR could be
  an opportunity to 'unprime' `CatCommSq.iso'`? (Or maybe in a separate PR?)".

**Attitude.** Hedged and maintainer-dependent: "I understand some Mathlib maintainers don't feel so fondly
about primed theorem names."
