# PR #33145: feat: supremum of a continuous function on a dense set is equal to the supremum on the univ

## Description

This PR adds the following theorems:

1. `Dense.continuous_upperBounds` : If `α` is a preordered set with ClosedIicTopology, `f : γ → α` is a continuous functions, and `S` is a dense subset of `γ`. Then the upper bounds of `f '' S` is equal to the upper bounds of `range f`.
2. `Dense.continuous_sup` : If`α` is a conditionally complete lattice and `f` is bounded above, then `⨆ i, f i = ⨆ s : S, f s`.
3. `Dense.continuous_sup'`: If `α` is a conditionally complete linear order, then `⨆ i, f i = ⨆ s : S, f s`.

Some of the codes in this PR are created by @plp127 and @j-loreaux . See also the zulip discussion: [#Is there code for X? > Continuous function reaches its supremum on a dense set](https://leanprover.zulipchat.com/#narrow/channel/217875-Is-there-code-for-X.3F/topic/Continuous.20function.20reaches.20its.20supremum.20on.20a.20dense.20set/with/556965307).

## Changed files

- `Mathlib/Topology/Order/IsLUB.lean`
