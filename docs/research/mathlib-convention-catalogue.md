# A catalogue of Mathlib's conventions, and what it says about discovery

*2026-09-11. Built by `src/mathlib_review/conventions/catalogue.py` against the clone at
`28908c09`. Regenerate with `ape/bin/python -m src.mathlib_review.conventions.catalogue --out <path>`.*

## Why this exists

Six convention-discovery mechanisms were proposed and rejected in a single session
(`docs/dead-ends.md`: "Surface proxies for convention discovery"). Every one was fitted to the same
two or three conventions the author happened to know — `grind`, dot notation, `to_fun` — and each
failed for that reason. The missing object was a **denominator**: nothing said what a mechanism is
supposed to reach, so "this design finds conventions" could never be false.

This catalogue is that denominator. The question it makes answerable is *"mechanism X reaches N of
these"*, which is the same reachability-census discipline that returned `static_reachability_rejected`
on the v4 operators (C0 40/40, C1 15/40, C2 5/40) and saved a paid run.

## What the scan found: 112 conventions the repository states about itself

| tier | n | what it means |
|---|---:|---|
| **standard** | **23** | in `linter.mathlibStandardSet`, which the lakefile turns on globally — **binding on every contributor** |
| default_on | 17 | `defValue := true`, in no set |
| available | 28 | registered, off, in no set — a *capability*, not a convention |
| weekly | 3 | `weeklyLintSet` — run weekly, posted to Zulip, advisory |
| nightly | 4 | `nightlyRegressionSet` — **diagnostics, not conventions**: they find where `grind`/`lia` do *not* yet supersede an older tactic |
| disabled | 1 | commented out of a set, with a reason |
| **cited** | **22** | library notes cited from the code that follows them; the citation count is an adoption weight |
| uncited | 14 | library notes nobody cites |

**Enforcement is read from linter-set membership × `defValue` × the lakefile — never from option
existence.** A registered linter defaulting to `false` and belonging to no set is a proposal. That
distinction is what separates the 23 binding conventions from the 28 available capabilities, and
conflating them is how `grind`-the-tactic-exists got mistaken for `grind`-the-convention earlier.

The `nightly` tier is worth its own warning: `regressions.linarithToGrind` and its three siblings
exist to find places where `grind` **fails** to replace the older tactic. Reading membership there
as "Mathlib wants `grind`" inverts the sign.

### The binding 23

`flexible` · `hashCommand` · `oldObtain` · `privateModule` · `style.cases` · `style.cdot` ·
`style.docString` · `style.dollarSyntax` · `style.emptyLine` · `style.induction` ·
`style.lambdaSyntax` · `style.longFile` · `style.longLine` · `style.maxHeartbeats` ·
`style.missingEnd` · `style.multiGoal` · `style.openClassical` · `style.refine` · `style.setOption` ·
`style.show` · `style.whitespace` · `unusedDecidableInType` · `unusedFintypeInType`

### The most-cited design conventions

```
364  reducible non-instances          a class-defining def with an explicit argument not in the
                                      conclusion must be `@[reducible] def`, not an instance
168  lower instance priority          always-applicable instances get a lowered priority
 55  partially-applied ext lemmas     state `ext` lemmas without a full argument set
 25  category theory universes        object and morphism universes vary independently
 20  foundational algebra order theory
 18  commutative subobjects           commutativity is bundled into the class
 12  bundled maps over different rings
 11  pointwise nat action
 10  lower cancel priority
  8  implicit instance arguments      `{}` not `[]` when the instance is determined elsewhere
```

## The finding that reframes the problem

**The 23 binding conventions are already enforced by CI on every build.** A review agent that
discovers them adds nothing: the contributor's own `lake build` has already rejected the code. The
same is true of most of the `default_on` 17.

So the conventions worth discovering are, almost by definition, **the complement of what is
encodable as a linter.** This is the sharp form of the objection that killed the anti-unification
design: `simp (config := { contextual := true }) → simp +contextual` was legible precisely because
it was mechanical, and mechanical conventions get a linter or a chore PR and are then *gone*.

Any proposed discovery mechanism should therefore be scored on the complement, not on the
catalogue as a whole. A mechanism that recovers the 23 standard linters has recovered the part
that needed no mechanism.

## The catalogue's bias, stated so it is not rediscovered

Everything above is extractable **because someone already encoded or wrote it down**. That is the
easy end by construction. The conventions that matter for review are disproportionately those with
no linter, no note, and no prose anywhere — the record's own sweep found that most of the 35
dev-set request groups are taught by *exemplars only*, and that the one statement-form group has no
in-repo prose source at all.

Rows carry `source`, so extracted and hand-observed entries can never be silently pooled.

## Hand-observed conventions: the part that matters, and is not yet done

**Status: 12 sketched of a 50-target. This section is the actual work and it is incomplete.**
Each entry needs a conforming example with a path, a non-conforming one where findable, and the two
assessment columns. Provenance is marked because several come from the project record rather than
from a fresh read, and the record's dev-set analysis is burned as evaluation data.

| # | convention | category | linter? | note? | provenance |
|---|---|---|---|---|---|
| H1 | state a lemma at the weakest typeclass that suffices | generality | no | no | record: 355 review comments, 123 directive |
| H2 | subject-prefixed names (`encard_foo`, not `card_foo`, for `Set.encard`) | naming | no | no | measured: 87/91 direct-subject decls |
| H3 | dot notation for `of`-lemmas concluding a predicate | naming | no | no | measured: 13.7% of 9,862 in-class; 224 review comments |
| H4 | don't reprove what exists (`zero_lt_two`, not a reproof) | api_reuse | no | no | commit subjects |
| H5 | `@[to_additive]` on multiplicative lemmas rather than a hand-written additive twin | api_family | partial (`existingAttributeWarning`) | no | 78 commit subjects |
| H6 | state lemmas in `simp`-normal form | statement_form | no | no | `simp`-nf linter exists but is not in the standard set |
| H7 | put the goal on the `calc` header | proof_style | no | no | record: dev-set group |
| H8 | term mode when the proof is short | proof_style | no | no | record: dev-set group |
| H9 | factor a repeated argument into a lemma | api_design | no | no | record: dev-set group |
| H10 | deprecate with `@[deprecated (since := …)]` + `alias`, never a bare delete | deprecation | no | no | 4,335 invertible pairs, 87.5% machine-generated |
| H11 | prefer the API over the definition | api_reuse | no | no | commit subjects |
| H12 | set-builder form for set-valued statements | statement_form | no | no | record: dev-set group, **no in-repo prose source** |

Sources not yet mined, each of which should add entries: the deprecation ledger's structural
classes (primed→unprimed 183:26, flat→dot 45, gains-`Is` 119); `@[simps]` / `@[to_dual]` /
`@[fun_prop]` attribute-usage patterns; the Zulip store (180k messages); and reading the code,
which is the only source for the exemplar-taught majority.

## The reachability census this is for

To be filled once the hand-observed section reaches its target. For each candidate mechanism, the
fraction of the catalogue it can reach — **reported separately for the encoded and hand-observed
halves**, since a mechanism scoring well on the encoded half has told us nothing.

| mechanism | encoded (112) | hand-observed | notes |
|---|---|---|---|
| executable linter | 40 by construction | ? | reaches exactly what is already enforced |
| syntactic anti-unification / edit mining | ? | ? | expected high on style, ~0 on library notes |
| contrast search (`naming_contrast`) | ? | ? | proven on H2; hardcoded to one subject |
| semantics-aware AU / goal states | ? | ? | unbuilt; the open question |
| prose extraction | 112 by construction | ~0 | trivially reaches what is written down |

The two columns are the point. A mechanism is interesting only in the second.

## Verification

```
ape/bin/python -m src.mathlib_review.conventions.catalogue --out <path>
```

Records `workspace_revision` so a catalogue can be tied to the snapshot it was read from, and
reports `linter_options_without_a_readable_docstring` (18 at `28908c09`) rather than silently
dropping them.
