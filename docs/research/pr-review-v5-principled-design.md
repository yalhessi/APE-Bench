# A principled design for reaching maintainer issues and fixes

*Written 2026-08-05, after pausing checker generalization. Consolidates every roadblock
measured across v2/v3/v4 and proposes the design changes that follow from them. Targets
all three scales: the 3-PR dev set, the 16-PR medium set, and the 57-PR set used in
earlier iterations.*

---

## 1. The reframe: we have been building for 29% of the corpus

The single most important number in this document. Across the 75-PR intervention corpus
there are **92 judgeable non-meta maintainer interventions**, and they partition cleanly by
what kind of knowledge is needed to produce them:

| problem class | count | share | what it takes | methods today |
|---|---:|---:|---|---|
| **Convention** — style, naming, docs | **65** | **71%** | know what the repository's convention *is* | naming only (16 of 65) |
| **Repository knowledge** — duplication, generalization | 15 | 16% | know what already *exists* | canonical_api, wrapper |
| **Local judgment** — proof-golf, correctness, scope | 12 | 13% | understand *this* proof | none (holistic only) |

Every systematic operator built during v4 — `canonical_api_search`, `wrapper_composition` —
serves the 16% class. `naming_contrast` serves a quarter of the 71% class. **Style (37
interventions) and docs (12) have no method at all**, and together they are 53% of the
corpus.

This is corroborated inside medium, where the census found 12 obligations that no method
expresses: style-norm 5, docs 3, correctness 2, scope 1, generalization 1.

The C2 = 5/40 wall is therefore not primarily an implementation-breadth problem. It is a
**portfolio** problem: the registry was grown from whatever the development PR happened to
contain, and the development PR is not representative of the corpus.

---

## 2. Roadblocks, with the evidence for each

### R1. Coverage vs selection is not one wall — it depends on pool size

From the 115-anchored-gold miss decomposition:

| pool | recall | located-miss (selection) | untouched (coverage) |
|---|---:|---:|---:|
| single holistic run (gpt_5.4) | 10% | 13% of misses | **87% of misses** |
| single holistic run (gpt_5.2) | 31% | 51% | 49% |
| grand union of 6 runs | 47% | **64%** | 36% |

The often-quoted "81% of gold sits at a predicted location" is a property of the *grand
union*, not of any deployable system. **For one run, coverage is the dominant wall; only
after flooding does selection become dominant.** A design must therefore say which regime
it is operating in, and cannot borrow the union's framing to justify a selection lever.

### R2. Selection is at chance exactly where the problems are hardest

Selector AUC by stratum: **0.574 on golf/duplication/generality (≈ chance)** versus 0.66 on
conventions. Giving the selector tools moved it 0.586 → 0.563 — nothing. Self-confidence
has now been falsified as a ranking signal three separate times, and precision stayed flat
(9% → 12%) across confidence thresholds.

**Consequence:** any design that generates broadly and then ranks is relying on a signal
that does not exist for the semantic classes. Ranking can be used for conventions; it
cannot be the mechanism for golf/duplication.

### R3. Norm-establishing asks are structurally invisible to frequency rules — *new*

Measured this session on the real snapshots:

- PR 33337's maintainer asks for the `toLinearMap_` convention. At that base snapshot
  `toLinearMap_` holds **17%** (21 of 121 declarations) and the `→ₗ` coercion is dominated
  by `coe_` at **39%**.
- Phase 6 was deferred because `grind` had **2 temporally-eligible mentions in an
  8,161-event ledger**.

The maintainer is *establishing* a convention, not enforcing one. A population-frequency
rule cannot fire without arguing against the current majority, and lowering thresholds to
17% would fire on any minority spelling and destroy control safety (currently 0 candidates
on all three control PRs).

**This bites hardest in the 71% class.** Conventions are exactly the thing that evolves.

### R4. Shape rules recover the issue but not the resolution

The generalized naming rule identifies PR 33145's issue correctly (prefix should be
`upperBounds`, not `continuous`) but proposes `upperBounds_upperBounds` where gold asks for
`upperBounds_image`. Choosing the *rest* of a name requires knowing what the lemma says,
not just what it is about.

This matches the historical pattern: apply-all reached **69–72% issue** but only **42–47%
resolution**; of genuinely identified problems just over half got the right fix.

### R5. Maintainer asks are indexical; model asks are generic

The divergent-judgment audit of 65 same-site/same-family pairs the judge scored as
different found: wrong-specific-aspect ~22, **reviewer-plan/cluster coherence ~15**
(maintainers repeat one ask across siblings — "Same below"), knowledge-frontier ~9,
taste-direction inversion ~5, grain ~5, terse ~3.

Two design-relevant items there: **cluster coherence** is a property of the review *as a
whole*, not of any single site; and **taste-direction inversion** (model prefers
explicit-verbose, maintainers prefer tight-canonical) is a systematic bias, not noise.

### R6. Gold does not exist at the scale we want to evaluate

| scale | PRs with v4 gold | obligations |
|---|---:|---:|
| dev (small) | 2 gold + 1 control | 22 included |
| medium | 13 gold + 3 control | 40 included |
| **57-PR set** | **13** | — |

The 57-PR set has **v3-schema** gold only: 113 interventions over 75 PRs. Migrating to v4
obligations needs the scope-migration and atomicity-decomposition steps, which are
human-gated (medium's 13 PRs required 9 decomposition decisions: 7 split, 2 accept-atomic).
Medium gold is also still 31/33 `migration_proposal` — only 2 judgments are
curator-confirmed.

**Nothing can be reported at 57-PR scale until this is paid for.**

### R7. Metric hygiene — largely fixed, with one residue

Under the v8 rubric the judge now measures **0/18 split pairs and a 100% self-agreement
ceiling** (v7.1: 4/18 and 90.1%), and ambiguity is a first-class reported category. The
residue: at n = 8 one flipped verdict is still 12.5%, so **small denominators cannot carry
effect-size claims** regardless of judge quality. Phase 9's resolution-recall advantage
(0.67 obligations) is inside that band; its reproducibility, control-safety and cost
findings are not, because they are judge-free.

---

## 3. Design modifications

### D1. Route by problem class, not by method

Replace the flat method registry with three arms whose *evidence sources and success
criteria genuinely differ*:

| arm | serves | evidence | reachability criterion |
|---|---|---|---|
| **Convention** | style, naming, docs (71%) | norm store (§D2) + snapshot population | a norm exists at the required maturity |
| **Repository** | duplication, generalization (16%) | declaration index, retrieval, applicability compile | a candidate declaration exists and the composed edit compiles |
| **Judgment** | golf, correctness, scope (13%) | the reviewed code itself | none — this is the holistic arm's residual |

This is not a renaming of the current design. It changes what "coverage" means: today C2
asks *does an implementation accept this shape?*; under D1 the convention arm asks *does the
repository have an opinion here, and how mature is it?* — a question about the corpus, not
about our code.

### D2. A norm store with maturity, and the honesty to abstain

The core new component, and the one that unblocks the 71% class.

```
NormRecord:
  subject / scope        what the norm is about
  statement              the convention, as a checkable predicate
  maturity               established | emerging | contested | superseded | absent
  prevalence             measured share in the snapshot, with counts
  as_of                  snapshot date (temporally gated)
  evidence_refs          the declarations / lint rules / discussions counted
  coverage_verdict       sufficient | insufficient_evidence
```

Three properties matter:

1. **Maturity is measured, not assumed.** `established` = the dominant-prefix test the
   naming rule already implements (≥20 support, ≥80% share). `emerging` = a minority
   convention with a *rising* trend or an external declaration (lint rule, style-guide
   diff, `@[deprecated]`). This is what makes PR 33337 expressible: `toLinearMap_` at 17%
   is `emerging`, not `absent`.
2. **Emerging norms do not license the same act.** An `established` norm justifies a
   blocking rename request; an `emerging` one justifies an advisory suggestion at most.
   The maturity feeds `speech_act`/`blocking_force`, which the gold schema already carries.
   This is how we get reach without paying for it in control-PR false positives.
3. **The store declares its own coverage.** Below an evidence threshold it emits
   `insufficient_evidence` and provisions nothing. Phase 6's failure then becomes a
   *published measurement* ("`grind` has 2 eligible mentions") rather than a silent gap.

Sources, cheapest first: in-tree prevalence and trend across snapshots (free, already
implemented in `naming_norm.scan_population`); dated repo artifacts — lint rules,
`@[deprecated]`, style-guide diffs, mass-migration PRs (cheap, high-precision); recency-
weighted precedent mining over the event ledger (already built in v2's corpus tooling);
Zulip (only source that *precedes* in-repo adoption; gated).

### D3. Style and docs checkers — the missing 53%

Both were expected to be tractable *because* they are conventions. One was; the other was
falsified by measurement — see below and `audits/convention-class-reach.md`.

- **`style_norm`**: the corpus is the specification. Mine per-construct conventions from the
  snapshot (binder style, `calc` alignment, `simp only` vs `simp`, case-split idiom) the
  same way `naming_norm` mines prefixes. The existing population-scan machinery generalizes
  directly — the scan already visits every declaration.
- **`docs_gap`**: ~~largely structural~~ **FALSIFIED 2026-08-05**
  (`audits/convention-class-reach.md`). Measured on the snapshot: only **8%** of Mathlib
  theorems/lemmas carry a docstring and 67% of defs — so "a public declaration with no
  docstring" is not a convention, and a rule enforcing it would fire on 92% of new lemmas.
  The corpus's missing-docstring asks are *selective editorial judgements*, which a blanket
  rule cannot reproduce without flooding. Do not build this as specified.

### D4. Separate issue-identification from fix-construction

R4 says shape rules find the issue and miss the name. Stop pretending one operator does
both:

- The deterministic arm emits an **issue** with its warrant (population counts, retrieval
  score, missing-docstring fact). This is what it is good at, and it is reproducible.
- **Fix construction is a separate, model-backed step** conditioned on that warrant plus
  the reviewed code. It is allowed to be stochastic because it is scored separately
  (`resolution_match`), and its failures no longer destroy the issue-level result.

This matches the two-level rubric the judge already implements, and it explains the
historical 69–72% issue / 42–47% resolution split as a *pipeline* property rather than a
model deficiency.

### D5. Review-level coherence as a first-class pass

R5's cluster-coherence finding (~15 of 65 divergences) is invisible to a per-site
architecture: maintainers make one decision and apply it across siblings. Add a
**propagation pass** after per-site generation: given an accepted issue on target X and the
PR-relation graph (already built — `pr_relations.py` computes `changed_siblings`,
`name_family`), propose the same issue on siblings that share the shape, and *suppress*
per-site duplicates in favour of one clustered finding. This changes both recall (siblings
the per-site pass missed) and precision (fewer near-duplicate findings).

### D6. Make the scale explicit in every claim

Adopt as a reporting rule, not a nice-to-have:

- Every recall figure at n < 20 is printed with its one-flip increment inline
  (`33.3% (±12.5pp per flipped verdict, n=8)`).
- **Effect-size claims are only made where a flip is < 3pp** — i.e. n ≳ 34, which means
  medium (40 obligations) or larger. Tier-small is for *mechanism* questions with
  judge-free endpoints: does routing partition cleanly, do control PRs stay silent, are
  accepted opportunities reproducible, does C2 move.
- The judge-free quantities (C2 coverage, control candidates, candidate volume,
  reproducibility, cost) are the preferred decision variables everywhere, because they are
  immune to R7 entirely.

---

## 4. Scaling to medium and the 57

The gold gap (R6) is the binding constraint and is *human*, not computational.

**Step 1 — finish medium's gold (small).** 31 of 33 judgments are still
`migration_proposal`. Confirm them and the 21 pending-C1 annotations in one sitting. This
is already the R1b item on the roadmap and it gates the single medium census look.

**Step 2 — migrate the 46-PR unseen slice (the real cost).** Run the existing
`migrate_interventions` → `judgment_graph` → `stabilize_judgments` chain over the remaining
interventions. Extrapolating medium's rate (13 gold PRs → 9 decomposition decisions),
expect **~30–35 decomposition decisions plus scope-migration review** for the rest. This is
one to two focused sittings, and it is the only thing standing between us and a 57-PR
number.

**Step 3 — build episodes/change graphs/workspaces for the slice.** Mechanical, but needs
Lean builds for each new base commit (the medium tier needed 7). Budget this as compute,
not attention.

**Step 4 — report at the right scale.** Once 57-PR gold exists: the convention arm's
reachability can be measured *offline and judge-free* over ~65 convention interventions —
a denominator where a single judge flip is 1.5pp. That is the first setting in this
project where an effect size is actually measurable.

---

## 5. Sequencing

Ordered by (evidence value) / (cost), with the gate each step must pass.

| # | Step | Cost | Gate |
|---|---|---|---|
| 1 | **`docs_gap` checker** — structural, no norm needed | small, no API | control PRs silent; C2 rises on ≥2 PRs outside dev |
| 2 | **Norm store v1** — in-tree prevalence + trend + dated artifacts; publishes coverage | medium, no API | ≥1 norm at each maturity level, with counts; `grind` and `toLinearMap_` both correctly typed `emerging`/`insufficient` |
| 3 | **`style_norm` checker** on established norms only | medium, no API | control PRs silent; measured reach over the 37 style interventions |
| 4 | **Medium gold completion** (R1b) | human sitting | decisions set equals the flagged set |
| 5 | **Single medium census look** — frozen implementations | 1 medium look, no API | the pre-registered ≥3/≥2/≥2 reachability gate |
| 6 | **57-PR gold migration** | 1–2 human sittings + Lean builds | atomicity gate; provenance recorded |
| 7 | **Fix-construction arm** (D4) split out and scored separately | API, tier-small | issue-level result unchanged; resolution measured independently |
| 8 | **Propagation pass** (D5) | API, tier-small | duplicate findings fall; sibling recall rises |
| 9 | **Emerging-norm arm** — advisory only | API, tier-small | control PRs still silent at advisory force |

Steps 1–3 and 5 are judge-free and therefore immune to the noise floor. Steps 1–3 cost no
API budget at all, which is the argument for doing them before anything paid.

---

## 6. What this design does *not* claim

- It does not claim the 71% convention class is *easy* — only that it is where the corpus
  actually is, that it is measurable offline, and that it is currently unserved.
- It does not claim norm mining reaches norm-establishing asks by itself. It claims those
  asks become *expressible and countable* (as `emerging`), which is the precondition for
  ever reaching them, and that acting on them requires a weaker speech act.
- It does not revive selection-by-ranking for the semantic classes: R2 falsified that, and
  nothing here depends on it.
- It does not re-score any historical result. v8 numbers compare to v8 numbers; the
  Phase 9 record stands as measured, with its resolution-recall line demoted to
  within-noise.
