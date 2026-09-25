# PR #30650: notes for the whole-PR reviewer

1. **Wanted?** Yes. Before this PR, `addRelatedDecl` handed `info.value!` to each generator, so every derived `_assoc`/`_apply`/`_app` lemma copied the source proof and the kernel re-checked it. About 2.8k attribute lines in Mathlib are affected, so the saving is real. There is no existing helper this duplicates. `higher_order` (Mathlib/Tactic/HigherOrder.lean:78,85) already refers to the source by `.const`. No finding.

2. **Every hunk an improvement?** Yes. Every hunk is either the signature change or follows from it: the callback loses `type`, `mkExpectedTypeHint` is dropped because `inferType` of the constant already gives the stated type, and `elementwise_of%` is adjusted to the new `elementwiseExpr` signature. None is stylistic or unrelated. No finding.

3. **One thing?** Yes. One helper plus its only three callers (mlgrep `addRelatedDecl`: Elementwise, Reassoc, ToApp), and the title names exactly those three attributes. No finding.

4. **Description?** Empty. It gives no mechanism, no `!bench` numbers for a `perf` PR, and no note of the changed public meta signatures (`addRelatedDecl`'s `construct`, `elementwiseExpr`). There is nothing to check for AI disclosure, and nothing suggests AI was used, so no separate finding on that. No linked discussion or dependencies, and none looks needed. One finding (advisory).

5. **Finishes the job?** Only partly. The same redundant type argument survives as `reassocExpr`/`reassocExpr'`'s `type?`, which every Mathlib caller now sets to `none` (Reassoc.lean:112,123,141,155), and the `addRelatedDecl` docstring (AddRelatedDecl.lean:20,33-36) still describes the old callback. I looked for other generators that copy a source proof into a new declaration (the `addDecl`/`addAndCompile` sites in Mathlib/Tactic, `simps`, `mk_iff`, `higher_order`, `to_additive`): none needs this change, since `to_additive` must translate the value anyway. The existing tests in MathlibTest/CategoryTheory/{Reassoc,Elementwise,ToApp}.lean cover the generated statements, which this PR leaves unchanged. Two findings (advisory).

6. **Right place?** Yes. The helper stays in Mathlib/Util and the attribute code stays in Mathlib/Tactic/CategoryTheory. No finding.
