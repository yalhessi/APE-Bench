# The C1 measurement understates method-expressibility: the transformation vocabulary is missing half the maintainer acts

*2026-08-05, found while starting the v5 build. This is a measurement defect, not a
pipeline defect, and it has to be fixed before checker work is prioritised — otherwise the
priorities are set by an artifact.*

## Symptom

The static census reported **C1 = 15/40** with **21/40 obligations abstaining on the
transformation classifier** (`no_transformation_rule_matched`). C1 is conjunctive — a
contract must cover both the issue class *and* the requested-transformation class — so
every abstention forces C1 false regardless of how good the methods are.

## The abstentions are not scattered; they are five whole categories

| abstained | issue class | the maintainer act, in their own words | frozen vocabulary term |
|---:|---|---|---|
| 9 | proof_simplification | "Simplify … using the requested grind setup", "Golf the proof … to a direct lambda", "Rewrite the `calc` proof so the initial line includes the goal" | **none** |
| 4 | duplicate_implementation | "Generalize … into a `Dense.ciSup'` lemma", "Factor out the repeated argument into a general reusable lemma", "replace the duplicated lemmas with `@[to_additive]`" | **none** |
| 4 | style_norm_violation | "Insert a blank line after `section auxiliaryDefs`", "Wrap/split the overly long doc comment line", "Replace the rewrite with the method call `h.map_iSup`", "Redefine … as a set comprehension" | **none** |
| 3 | documentation_gap | "Fix the docstring typo", "Complete/fix the docstring so the sentence …", "Revise the module-level documentation" | **none** |
| 1 | scope_placement | "Move the declarations … inside `namespace Complex`" | **none** |

The frozen vocabulary has five terms — `fix_target_compile`, `apply_repository_policy`,
`replace_with_repository_declaration`, `compose_wrapper_with_witnesses`,
`rename_declaration` — and **no term for editing prose, reformatting source, rewriting a
proof in place, extracting or generalising a declaration, or relocating one.**

That is why 53% of obligations abstain. It is a vocabulary gap, not a judgement about the
methods.

## Corroborated by the full corpus, not just medium

To avoid fitting a vocabulary to the cases already seen, the leading imperative verb of all
**92 judgeable non-meta interventions across the 75-PR corpus**:

```
replace 14   rename 11   refactor 7   remove 7   rewrite 6   add 6
change 4     reorder 3   fix 3       wrap 2      factor 1   move 1
redefine 1   revise 1    complete 1  golf 1      adjust 1   reconsider 2
```

`rename` (11) and `replace` (14) are the only acts the frozen vocabulary can express.
**`refactor`, `remove`, `rewrite`, `add`, `reorder`, `wrap`, `move`, `redefine`, `revise`,
`golf` — 36+ interventions, ~40% of the corpus — have no term at all**, and the pattern is
the same at corpus scale as inside medium. This is not a medium artifact.

## Proposed vocabulary extension (v2 protocol)

Derived from the corpus verb distribution above, not from which obligations would flip:

| new class | covers | corpus verbs |
|---|---|---|
| `rewrite_proof` | change a proof's tactics/structure in place, without importing a new declaration | rewrite, golf, refactor (proof), simplify |
| `extract_shared_declaration` | pull repeated content into a new reusable/generalised declaration | factor, generalize, refactor (structure) |
| `edit_documentation` | change docstring or module-doc prose | fix (docs), complete, revise |
| `reformat_source` | layout and surface form: whitespace, line length, dot-notation, ordering | wrap, reorder, insert, adjust |
| `relocate_declaration` | move a declaration into/out of a namespace, section, or file | move |
| `remove_declaration` | delete code, including policy-forbidden constructs such as new `axiom`s | remove |

## Why this matters for what gets built next

The current priority ranking — "style-norm 5 and docs 3 are the largest uncovered
families" — was derived from C1 numbers computed under the broken vocabulary. Until the
census is re-run under the extended protocol, **we do not actually know which families are
method-expressible**, and building checkers against the current ranking risks optimising
for a measurement artifact.

Concretely, several abstained obligations are near-certainly expressible once the
vocabulary exists, and three are *mechanically detectable* with perfect measured control
safety across all 16 medium PRs:

| obligation | signal | fires elsewhere in medium? |
|---|---|---|
| PR33305 "wrap the overly long doc comment line" | exactly **1** line >100 chars in the reviewed code | **no** — 0 in every other PR, including all 3 controls |
| PR33149 ×2 "remove the newly introduced axioms" | **19** targets with `declaration_kind == axiom` | **no** — 0 in every other PR |
| PR33294 "replace `Order.IsNormal.map_iSup h …` with `h.map_iSup …`" | dot-notation-eligible call sites | to be measured |

These are the highest-precision signals found anywhere in this project, and all three sit
in families the current census reports as unreachable.

## Recommended order

1. **Extend the transformation vocabulary** to the six classes above; version the
   annotation protocol (`obligation-expression-class/3`) and keep v2 frozen.
2. **Re-run the static census** under v3 of the protocol. This is judge-free and costs
   nothing, but it *does* consume a medium look under the standing rule — so run it once,
   on a frozen protocol, and treat the resulting C1/C2 as the real baseline.
3. **Then** prioritise checkers from the corrected numbers, starting with the mechanical
   lint/policy signals above, which need no norm store and no model.

## Discipline note

Extending the protocol changes C1 and must not be done to rescue misses. Two guards were
applied: the new classes are derived from the **corpus-wide verb distribution** (92
interventions across 75 PRs, including the 46 PRs never measured), and each new class
names a *maintainer act*, not an obligation. The extension should still be frozen and
reviewed before the census is re-run.
