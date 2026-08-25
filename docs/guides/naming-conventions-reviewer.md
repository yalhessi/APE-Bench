# Mathlib Naming Conventions For Reviewers

Use this file when a PR review depends on declaration naming, theorem statement naming, namespace
placement, or structural lemma naming.

Derived from the official Mathlib naming conventions guide.

## High-level naming rules

- `.lean` filenames are generally `UpperCamelCase`. Lowercase filenames are rare exceptions for
  objects that are genuinely written that way, and unusual exceptions should be discussed first.
- Theorem names and other `Prop`-valued terms use `snake_case`.
- `Prop`, `Type`, and `Sort` names such as structures, classes, and inductive types use
  `UpperCamelCase`.
- Functions are named as though they were values of their return type.
- Other `Type`-valued terms usually use `lowerCamelCase`.
- If an `UpperCamelCase` name appears inside a `snake_case` theorem name, convert it to
  `lowerCamelCase`.
- Acronyms stay grouped by case, but there are a few established exceptions such as `Ne`.
- Declaration names use American English spelling.

## Common theorem-name patterns

- Prefer descriptive names that tell the user what the conclusion looks like.
- For infix notation, the theorem name should follow the written expression. For example, the
  pattern `-a * -b` should read like `neg_mul_neg`.
- When hypotheses need to be named, use `of` separators and keep them in argument order. Think
  `conclusion_of_hyp1_of_hyp2`, not the reverse.
- Common sign/order abbreviations such as `pos`, `neg`, `nonneg`, and `nonpos` are preferred over
  more expanded forms.
- Use `left` and `right` when there are meaningful side-specific variants.
- When mentioning a namespaced definition from outside its namespace, drop the namespace if the
  result is still unambiguous; otherwise prepend the namespace back in `lowerCamelCase`.

## Order-relation naming

- Mathlib usually phrases order lemmas using `≤` and `<`, and theorem names normally follow that
  orientation with `le` and `lt`.
- Use `ge` or `gt` when the theorem name needs to signal swapped argument order, match another
  relation's order, describe the relation with arguments reversed, or emphasize the more-variable
  argument on the right.

## Dot notation and axiomatic names

- Use dots for namespaces, structure projections, auto-generated names, and hand-written names where
  projection-style notation is useful.
- Logical connectives and relations commonly expose names such as `.intro`, `.elim`, `.symm`, and
  `.trans`.
- Some lemma families are better named axiomatically than descriptively, for example `refl`,
  `symm`, `trans`, `antisymm`, `comm`, `assoc`, and cancellation lemmas.

## Structural lemma conventions

- Extensionality lemmas should typically be named `.ext`, and equivalence versions `.ext_iff`.
- Prefer injectivity lemmas whose main conclusion is `Function.Injective f`, usually named
  `f_injective`.
- Equality-form injectivity lemmas such as `f x = f y ↔ x = y` should usually be `f_inj`, or `.inj`
  in a suitable namespace. If an auto-generated one-way `.inj` already exists, the bidirectional
  version may be `.inj_iff`.
- In names like `sub_right_inj`, `left` and `right` describe the argument that changes.
- Induction principles should contain `induction`; recursion principles should contain `rec`.
  Include `on` when the value being eliminated appears before the constructors or cases.

## Predicate and class naming

- Predicates are usually prefixes, so prefer forms like `isClosed_Icc` over suffix forms.
- Important suffix families remain standard, including `_inj`, `_injective`, `_surjective`,
  `_bijective`, `_mono`, `_anti`, `_monotone`, `_antitone`, `_strictMono`, and `_strictAnti`.
- For `Prop`-valued classes, noun-like names usually start with `Is`, while adjective-like names
  may omit it when that matches normal mathematical language better.

## Variable conventions

- Universes are usually `u`, `v`, `w`.
- Generic types are usually `α`, `β`, `γ`.
- Assumptions are usually `h`, `h₁`, ...
- Generic elements are usually `x`, `y`, `z`.
- Natural numbers are usually `m`, `n`, `k`; integers are often `i`, `j`, `k`.
- Types with mathematical meaning often use conventional uppercase letters like `G`, `R`, `K`, and
  `E`.

## Expanded vs unexpanded function forms

- When both `f * g` and `fun x ↦ f x * g x` matter, unexpanded lemmas usually use the plain name
  such as `mul`, while expanded forms use a `fun_` prefix such as `fun_mul`.

## Review use

- Treat clear violations of an entrenched naming pattern as potential `library_integration_issue`
  findings when they would hurt discoverability or consistency enough to block merge.
- If the code is mathematically fine and the naming dispute is mostly about a better alternative,
  it is usually advisory and closer to `style_or_readability`.
