# The written guidance checked against (fetched 2026-09-26)

Pages, via WebFetch, summarised to their design rules; the in-tree notes by `grep -Rh "^library_note"`
on the 34091 base workspace (33 notes; `Note [lower instance priority]` cited 286 times,
`custom simps projection` 100, `forgetful inheritance` 26, `range copy pattern` 12, the rest under 12).

- **Style guide** https://leanprover-community.github.io/contribute/style.html — explicit types;
  hypotheses left of the colon; no conjunction or disjunction hypotheses; no conjunction conclusions;
  existential hypotheses become explicit arguments, results using choice become definitions;
  `to_additive`/`to_dual` over hand-written variants; `where` syntax; definitions semireducible unless
  there is a reason; **normal forms**: settle on a standard form and register simp lemmas towards it;
  deprecation.
- **PR review guide** https://leanprover-community.github.io/contribute/pr-review.html — docstrings;
  `#find_home`; duplication check with `apply?`/`exact?` ("possibly in a more general form with a
  different name"); imports; split files over 1000 lines; **long proofs split into supporting lemmas
  or definitions**; better tactics, golf without sacrificing readability; a different proof structure
  using existing lemmas; definitions avoid dependent types; attributes `simp`/`ext`/`gcongr`;
  rewrite lemmas so users need not pass through defeq; **convenient constructors for a new type**;
  **new definitions come with lemmas** (even just `@[simps]`); generality for known future needs;
  new morphisms bundled with `FunLike`, new subobjects bundled with `SetLike`; instance diamonds;
  `Type*`.
- **Values** https://leanprover-community.github.io/contribute/values.html — **general definitions**;
  **weak hypotheses, strong conclusions**; modular lemmas; **API for new definitions**; right file;
  readable proofs; naming; performance; no diamonds; automation annotations.
- **Naming** https://leanprover-community.github.io/contribute/naming.html — `ext` lemmas; injectivity
  lemmas also as an iff (`f_inj`); `≤`/`<` over `≥`/`>`; `_apply`/`map_`; `₀` for groups with zero.
- **Library notes** (in tree): bundled maps over different rings; category theory universes; change
  elaboration strategy with `by apply`; comp_of_eq lemmas; continuity lemma statement; continuous
  functional calculus; custom simps projection; decidable arguments; decidable namespace; design
  choices about smooth algebraic structures; fact non-instances; forgetful inheritance; foundational
  algebra order theory; hom simp lemma priority; implicit instance arguments; instance argument
  order; lower cancel priority; lower instance priority; Manifold type tags; no_index around
  OfNat.ofNat; non-Archimedean non-instances; norm_num lemma function equality; operator precedence
  of big operators; out-param inheritance; partially-applied ext lemmas; pointwise nat action; range
  copy pattern; RCLike instance; reducible non-instances; SetLike Aesop ruleset; slow-failing
  instance priority; specialised high priority simp lemma; the algebraic hierarchy.
