# Naming evidence from the statement, not from the leading token

**Status** — open, 2026-09-24, **for a fresh session** (its own thread and worktree: a redesign of the
naming arm's evidence tool; the prefix-scoping fix `adcc7ba` is the last change to the current tool)
**Cost** — design, build and the first measurement are free (no model calls); a judged check on the
release's naming golds is ~$1 through `cli bench`
**Motivating example** — `naming_norm` answers one question: across declarations about the same subject,
which *leading* token wins (`naming_norm.py:122`, `leaf.split("_", 1)[0]`). The user's reframing,
2026-09-24: naming is about identifying the critical parts of the object being named and the relations
between objects, and a name can need revising in many ways that touch neither a prefix nor a suffix. The
record agrees on both counts.

- **The release's rename asks are about the statement's parts, and the maintainers say so.** 33337's gold
  renames `coe_starProjection_eq_isComplProjection` to `toLinearMap_...` "to reflect that the statement is
  about `.toLinearMap`", so the justification is the statement, not prevalence (the tool's 21-of-121 count
  was a weak stand-in for it). 33145 renames `Dense.continuous_upperBounds` to `Dense.upperBounds_image`, whose
  conclusion is `upperBounds (f '' S) = upperBounds (range f)`: `continuous` names a hypothesis, `image`
  names `f '' S`. 33294 moves `isFundamentalSequence_of_isNormal` to `IsFundamentalSequence.of_isNormal`
  (dot notation on the conclusion's head). 33421 renames `round_eq'` to `round_eq_div` (a prime replaced
  by a word; the statement not yet read). Of these five, a leading-token census can express only the 33337
  pair. Five asks in one release are a description, not a rate.
- **Mathlib's own renames are mostly not prefix edits.** Crude census, 2026-09-24: 2,856
  `@[deprecated] alias old := new` pairs in the local tree (`data/code_execute/repos/mathlib4/source`,
  `28908c09b5`, 2026-05-14), leaves split on `_` only, enclosing namespaces unresolved:

  | edit | share | example |
  |---|---|---|
  | several tokens changed | 23.6% | `Congruence.compLeft -> HomRel.comp_left` |
  | namespace move, same leaf | 22.1% | `Quotient.CompClosure -> HomRel.CompClosure` |
  | first token substituted | 20.7% | `linearProjOfIsCompl -> projectionOnto` (most are one-token def names) |
  | tokens only added or removed | 12.0% | `IsIdempotentElem.eq_isCompl_projection -> ...eq_projection` |
  | last token substituted | 8.1% | `surjective_comp_linearProjOfIsCompl -> surjective_comp_projectionOnto` |
  | interior token substituted | 6.1% | `coe_linearProjOfIsCompl_apply -> coe_projectionOnto_apply` |
  | enclosing namespace only | 3.5% | `upperCentralSeriesStep` |
  | reordered | 2.5% | `IsCompl.projection_range -> range_projection` |
  | moved between namespace and leaf | 1.4% | `lex_lt_iff_of_unique -> Lex.lt_iff_of_unique` |

  The rows show the user's point directly: one concept rename (`linearProjOfIsCompl` -> `projectionOnto`)
  surfaces as a first, interior or last token substitution depending on where that concept sits in each
  lemma's statement. Position is incidental; the unit being renamed is a *part*. Caveats: camelCase is not
  split, cascades count once per alias, defs are included, and deprecations are post-hoc migrations rather
  than review asks, so this is the distribution of what Mathlib renames and not of what reviewers ask.

## The hypothesis

A Mathlib name is mostly a *function of the statement*: tokens name the conclusion's constituents in
order (concepts such as `encard` or `toLinearMap`, relations such as `eq`, `le` or `iff`), `_of_` introduces
hypotheses, the namespace names the conclusion's head for dot notation, and `'` or `_left` / `_right` mark
variants of a sibling. A rename ask is then a claim of one of two kinds, and each has its own evidence:

1. **Parts.** Align the name's tokens with the statement's constituents: a token that names no
   constituent (`continuous`, `'`), a constituent that no token names (`image`, `div`?), a constituent named
   by a different word than the corpus uses for it (`coe` where the statement writes `.toLinearMap`), or a
   namespace that is not the conclusion's head.
2. **Relations.** Find the declarations related to this one: structural analogues (the same statement shape
   up to one constituent), the file's siblings, and the other names of the same concept. Check whether this
   name maps onto theirs the way theirs map onto each other (`floor_X : ceil_X :: round_X : ?`).

The current tool is the degenerate case of (1): one token, at one position, for one subject. D2's maturity
idea (`docs/research/pr-review-v5-principled-design.md` §D2, never built) carries over unchanged: every
claim comes with counts, and a mapping 20 of 22 analogues follow is a different act from one 3 of 5 follow.
The tool returns an aligned diff with counts. It never returns a verdict about "naming", and the arm judges.

## What to settle first (free)

1. **Substrate.** This needs statements as structure: head constants and constituents, not text.
   `conclusion_subject` parses text and already misreads coercion ascriptions (see the test module's
   `REAL_CONCLUSIONS`). Find what is already on disk or cheap to get per base snapshot: elaborated types
   from the built workspaces, `declaration_search`, or a shape-search index over one environment (Loogle-style;
   check whether it runs offline before assuming it). Whatever it is has to be gated at the retrieval cutoff
   like every other corpus tool.
2. **The symbol-to-word map** comes from the corpus, never from a hand list: for each head constant, the
   tokens that co-occur with it in the names of declarations whose statements contain it. That map is also
   the evidence the 33337 ask cites.
3. **A gold-free testbed**, pre-registered before it is scored. The 2,856 deprecated renames plus matched
   never-renamed controls. The question is whether the aligned diff localises the renamed part and points at
   the new token more often than the leading-token census, and how often it flags a control. Split by date
   against every PR in any evaluation set: a deprecation after an episode's retrieval cutoff is not evidence
   for that episode, and one made by the PR under review is its gold.
4. **Then the judged check.** `cli bench --arm naming` at the five release asks plus their negatives, with
   the threshold stated before the run.

## What would close it

- **Closed negative** if the testbed shows the aligned diff localises renames no better than the prefix
  census. Before recording that, list the untried designs: another substrate, relations without parts, and
  camelCase-aware tokens.
- **Built but not the lever** if the testbed moves and the five release asks do not. At the two misses
  benched on 2026-09-24 the arm saw the right site and declined, so richer evidence may not change what it
  files. On the dev set this reaches at most the two non-prefix asks: the lever survey's in-sample ceiling
  is 2 for every specialist lever. Its value is out of sample and depends on how much naming gold
  `eval-set-selection.md`'s set carries.

Related: `specialist-arm-contents.md` (the prefix-only and 0.80-bar defects, the 2026-09-24 bench),
`docs/dead-ends.md` "B1 naming generalisation" (a subject-general *prefix* rule failed its reach gate on
2026-08-05; this is a different evidence shape, not a reopening of that rule), and `.claude/rules/mathlib-review.md`
on `naming_norm` counting prefixes only.
