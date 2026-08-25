# How far mechanical rules reach into the convention class

*2026-08-05. The convention class (style, naming, docs) is 71% of the corpus — 65 of 92
judgeable interventions — so it is where reach matters most. This records what is and is
not mechanically reachable, measured against the real snapshot before anything was built.
Two of the three candidate rules were falsified by that measurement.*

## The discipline

Before encoding a convention as a checker, measure whether Mathlib actually follows it.
This is the same rule that governs `naming_norm`: a rename is proposed only when the
snapshot shows ≥20 supporting declarations at ≥80% share. A "convention" the corpus does
not follow is not a convention, and a rule enforcing it would fire on the majority of the
codebase.

## Result 1 — "add a docstring" is NOT a Mathlib convention (falsified)

Sampled 1,200 files / 35,670 declarations from PR 33098's base snapshot:

| declaration kind | documented | share |
|---|---:|---:|
| theorems / lemmas | 1,943 / 25,304 | **8%** |
| defs / structures / classes | 3,537 / 5,293 | 67% |
| overall | 6,112 / 35,670 | 17% |

**A missing-docstring rule for lemmas would fire on 92% of new declarations.** Even for
definitions, 67% is a weak majority — well below the ≥80% bar that qualifies a naming
prefix as `established`, and it means one definition in three legitimately has no
docstring.

This falsifies the plan's own claim that `docs_gap` is "largely structural … the cheapest
unclaimed reach". It is structural, but the structure does not support a rule. The corpus's
missing-docstring asks (PR 33232, PR 33156) are *selective* maintainer judgements about
which declarations deserve documentation, not applications of a blanket rule — and a
blanket rule cannot reproduce a selective judgement without flooding.

## Result 2 — medium's docs obligations are not mechanically detectable anyway

All three:

| PR | ask | detectable? |
|---|---|---|
| 33066 | "Fix the docstring typo: 'An **isometry** linear equivalence' → 'An **isometric** linear equivalence'" | grammatical agreement — needs linguistic knowledge, not structure |
| 33321 | "Complete/fix the docstring so the sentence …" | semantic |
| 33321 | "Revise the module-level documentation to account for the ordered coefficient set" | semantic |

Corpus-wide, roughly 6 of 12 docs interventions have a structural shape (missing docstring,
stale symbol reference, capitalization), but per Result 1 the largest of those shapes is
not rule-supported.

## Result 3 — section/variable layout is not recoverable from the change graph

PR 33066's ask ("insert a blank line after `section auxiliaryDefs` and move the following
`variable`") requires knowing that two elements are *adjacent*. In the change graph the
`section` and the `variable` are separate targets, and their reviewed line spans are hunk
level — fourteen targets in that file share line 686 — so adjacency cannot be established.
Detecting this needs a file-level view the current representation does not provide.

## What the convention class *does* support

| rule | status | evidence |
|---|---|---|
| subject-conditioned naming prefix | **built** (`naming_norm`) | 237 subjects in the snapshot have a strong prefix norm; reaches PR 33145 (27/27, 25/25) |
| line length | **built** (`lint_norm.line_length`) | Mathlib enforces a 100-char limit; fires on exactly PR 33305's line, 0 elsewhere in 16 PRs |
| forbidden constructs (`axiom`, `sorry`) | **built** (`repository_policy`) | policy, not taste; fires on exactly PR 33149's 19 axioms |
| dot-notation preference | **deferred** | needs the type of the argument to know whether `Namespace.f h` could be `h.f`; that type is not lexically available, and measuring the convention's prevalence needs the same information |
| docstring presence | **rejected** | Result 1 |
| section/variable layout | **deferred** | Result 3 |

## The honest read

**The convention class is not uniformly mechanically reachable.** It splits into three very
different regimes:

1. **Strong, measurable, subject-conditioned conventions** — naming prefixes. The corpus
   has a real opinion (237 strong subjects), and prevalence mining works. This is where
   generalisation pays.
2. **Explicit repository policy** — line length, forbidden constructs. Not conventions at
   all but rules, with perfect precision and no norm mining needed. Already exhausted:
   these two were the reachable cases in medium.
3. **Selective editorial judgement** — most docs asks, and style asks about a *specific*
   proof's shape. The corpus provides no prevalence signal because the maintainer is
   exercising taste about one site, not applying a rule. **No amount of mechanical
   coverage reaches these.**

Regime 3 is larger than regime 1 in this corpus. That is the real structural finding, and
it means the convention class's 71% share should not be read as 71% mechanically reachable.

## Consequences

- **Do not build `docs_gap` as specified in the v5 design.** Result 1 falsifies its
  premise; the design document should be corrected rather than executed.
- **Regime 3 is the holistic arm's territory**, and its share of the corpus is a much
  better argument for the routed hybrid than the earlier "conventions are 71%" framing was.
- **Dot-notation remains the one deferred item with real value** — it is a genuine
  Mathlib-wide convention — but it needs type information, which means either the Lean
  toolchain or a type-aware index. That is a materially bigger build than any checker so
  far, and it should be costed before being committed to.
- The reachability gate stays cleared on the strength of regimes 1 and 2; nothing here
  changes that, but it does bound how much further mechanical reach is available.
