# Convention detectors, measured alone: dot notation first (pre-registered 2026-10-06, before the detector exists)

`docs/plans/2026-10-03-after-structure.md` §2 (conventions as detectors in the packet) and the
second half of step 3 of `docs/research/codebase-redesign-2026-10.md` (the producer seam,
`src/mathlib_review/producers/`). This file fixes what the first detector is, how it is measured
and how it is read, before it is written or run.

## Why dot notation first

The census (`results/pr_review_v5/adjudications/conventions-census-v1`, reader A, 1,833 asks on
973 validation-window PRs, disjoint from every evaluation set) files **29 asks on 13 PRs** under
P057 ("a namespaced function or lemma applied to a term of that namespace's type is written with
dot notation (`x.f`)", rank 11 of 410 entries) and 4 under P034 (leading-dot). The primed-name
conventions (P113, P211) hold 9 asks on 9 PRs between them; generated families (P201) 11 on 10.
Dot notation recurs most, and it has a shape a deterministic check can state.

## The detector, fixed here

`dot_notation`, two shapes, both over the change graph only (no model, no corpus, no gold), and
only on code the PR adds:

1. **Placement (P108 / P057).** A declaration the PR adds or renames whose conclusion asserts a
   predicate `H …` (`conventions/situations.py::predicate_head`) and whose leaf name is
   `h_of_rest`, `h` being `H`'s last component with its first letter lowered: the fact names the
   form inside the predicate's namespace, `H.of_rest`.
2. **Method call (P057).** In a line the PR adds inside a changed declaration, an application
   `N.lemma x` where `x` is an explicit binder of that declaration whose type's head has the same
   last component as `N`: the fact names the form `x.lemma`.

A fact says what the code is and what the dotted form would be. It never says a maintainer would
ask for it.

## Sets, and what each can say

| set | PRs | asks | control PRs | role |
|---|---|---|---|---|
| dev (`configs/probe_sets/dev_medium_0_3_0.yaml`) | 15 | 47 | 33304, 33315, 33438 | **in-sample**: the two dev dot-notation asks (33294, `d0038`, `d0039`) were read while choosing the convention |
| validation small12 (`val_small12.yaml`) | 11 | 30 | 26185, 32080, 34935 | out of sample; asks not read |
| post-cutoff (`postcutoff_2026_07_08_v1.yaml`) | 10 | 16 | 41271, 41280, 41314, 42238 | out of sample; asks not read |

At the census rate (33 of 1,833 asks, 1.8%) the two out-of-sample sets hold about **0.8**
dot-notation asks between them, so **recall is not read out of sample here**. What they can say
is what the section would add to a packet: its volume, its emission on clean PRs, and whether its
facts are right.

## Measures

`cli producer bench --producer dot_notation --set <set> --out <this dir>/<set>`: facts per PR,
facts on control PRs, asks located (sharing a change target with a fact). Then by hand, every
fact on every set: is the dotted form it names *valid as written* (the binder's type is in the
namespace the lemma lives in; the predicate's namespace is the one the conclusion names) -- valid,
not asked for -- and, for every located ask, is the fact the ask.

## Reading rule, fixed before the detector exists

- **In-sample check.** Both dev asks located, each with a fact that states the ask's dotted form.
  A miss is a defect, fixed before the other sets are read, and reported as such.
- **The section is packet-ready** when, on validation small12 and post-cutoff each:
  - control emission is **at most 1.0 fact per control PR** (one Opus solo pass emits about 1.0
    finding per control PR on dev; a section that says more than that about clean code is noise);
  - and, pooled over both sets, **at least half the facts are valid as written** by the hand read.
- **Too noisy** if either fails; the shape that failed is named, and the section does not enter a
  packet.
- Recall waits for a set with enough dot-notation asks: the census PRs, which need change graphs
  built (`docs/todo/README.md` gets the entry if this one passes).

## The footprint threshold (redesign step 3)

The detector lands in at most **three `src/` files, one test fixture, and no hub edit**
(`runner.py`, `cli.py`, the task bases, `schema`).

## Amendment 1 (2026-10-06, after the in-sample check, before any out-of-sample set was run)

**The in-sample check, as it came out.** On dev, 7 facts on 2 of 15 PRs, 0 on the three control
PRs. `d0038` (33294) is located with the fact that states its ask exactly
(`IsFundamentalSequence.of_isNormal`). `d0039` (33294, `rw [Order.IsNormal.map_iSup h …]` ->
`h.map_iSup`) is **missed**, and the miss is a limit of the shape, not a bug: `h` there is bound
by a `fun h =>` inside the proof, so its type is known only after elaboration, and shape 2 reads
the declaration's binders. Five other facts on 33294 state the same move (`Order.IsNormal.map_*
H` -> `H.map_*`) where `H` *is* a binder, on lines no maintainer commented on -- the asked
transformation, at its siblings. Typing proof-local names by guesswork would trade the precision
bar for one ask, so the shape stays as fixed; closing the miss needs the elaborated local context,
which is the try-it battery's (after-structure §3). Reading continues with this limit stated.

**Validity is checked by Lean where it can be.** Several `H` are typed `Ordinal.IsNormal`, not
`Order.IsNormal`, and whether `H.map_sSup` then resolves is Lean's to say. So a method-call fact
(P057) counts as *valid as written* when the one-line edit it names compiles in the PR's reviewed
workspace (`cli tool lean_verify_edit`, line mode, the line with `N.lemma x` replaced by
`x.lemma`), and as invalid when it does not. A placement fact (P108) is a rename, which a compile
cannot judge, so it is read: the predicate's namespace exists and the dotted name is not already
declared (`cli tool declaration_search`). The pooled half-valid bar is unchanged.

## Results (2026-10-06), read by the rule above

| set | PRs | facts | PRs with a fact | control PRs, facts each | asks located | exact |
|---|---|---|---|---|---|---|
| dev (in-sample) | 15 | 7 | 2 | 0, 0, 0 | 4 of 47 | 1 (`d0038`) |
| validation small12 | 11 | **0** | 0 | 0, 0, 0 | 0 of 30 | 0 |
| post-cutoff | 10 | **0** | 0 | 0, 0, 0, 0 | 0 of 16 | 0 |

**Out of sample the detector is silent.** Not for a structural reason: the two sets' change
graphs carry the same fields (103 and 43 declaration targets with added lines, 49 predicate
conclusions, 9 `_of_` names, 75 capitalised `N.lemma x` applications), and every near miss was read
and is excluded correctly -- a head that differs (`Kernel.compProd_apply_prod hs` with
`hs : MeasurableSet s`; presheaf functors and objects), an `_of_` name the PR did not introduce
(`tendsto_of_…_le'`), a stem that does not match (`Ioi_disjoint_Iio_of_le`). These 21 PRs hold
no situation of either shape.

**By the rule.** Control emission is 0 on every set (bar: at most 1.0 per control PR) -- met. The
validity bar, at least half the facts valid as written pooled over the two out-of-sample sets, is
**unmeasured**: there are no facts to judge. So the section is neither shown packet-ready nor shown
too noisy out of sample; what is shown is that it costs nothing on clean code and on 21 of 21
out-of-sample PRs says nothing.

**Validity, in sample only** (`dev_medium_0_3_0/validity.jsonl`). 5 of 7 facts are valid as written.
Four of the six method-call edits compile in the reviewed workspace, checked against a negative
control (`H.map_sSupp` fails with "the environment does not contain `Order.IsNormal.map_sSupp`").
The placement fact is the maintainer's own suggestion. The two invalid ones are one mechanism: the
binder is `H : Ordinal.IsNormal f`, and `H.lemma` resolves in `Ordinal.IsNormal` first, where a
lemma of the same name exists -- a deprecated wrapper with another signature at line 253, the
declaration being defined at line 271. Comparing only the last component of the namespace (the
shape as fixed) cannot see that; a declaration lookup of `<binder namespace>.<lemma>` could.

**The in-sample located asks, by hand.** `d0038` is the fact exactly. `d0014`-`d0016` (33098) share
the change target of the `Set.eq_empty_or_nonempty A` fact and ask other things (`by_cases!`, an
`IsCover` lemma, a `calc` indent); `d0015`'s suggestion itself keeps `Set.eq_empty_or_nonempty A`,
so at that place a maintainer wrote the long form -- the fact is valid and not wanted there.

**What it says.** Dot notation, stated deterministically, is a quiet section: one exact ask in
sample, no emission anywhere, and the asked move (`Order.IsNormal.map_* H` -> `H.map_*`) stated at
five sibling places where the maintainer commented once. It is not shown to be a lever. Recall
needs a set with enough dot-notation asks, which these three are not (about 0.8 expected out of
sample); the census PRs are (33 asks under P057 and P034). Two refinements are named by the
in-sample misses, neither tested: a declaration lookup that checks the binder's own namespace
before stating `x.lemma`, and the elaborated local context for proof-local names (`d0039`).

**Redesign step 3's footprint threshold** -- met: the detector landed in three `src/` files (the
module, its registry line, a private helper made public), one new test file, no hub edit
(`6128044d`).

## Stage 2: recall and demand on the census PRs (pre-registered 2026-10-06, before the census change graphs exist)

The three probe sets hold about 0.8 dot-notation asks out of sample, so recall was not readable
there. The census holds enough: reader A filed **49 asks under P057 (28), P108 (17) and P034 (4)**,
as primary or second label, on **28 PRs**, every one with a path and line; 9 are on AI-generated
PRs. The census PRs are val1000's (`val1000-2025-06-2026-03-v1`), disjoint from every evaluation
set. The detector was designed from the three codebook entries' statements and the two dev asks;
no census ask was read.

**Build.** The change graphs come from the val1000 structure build
(`results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/provenance/build_structure.py`)
and the round-1 bodies from `extract_draw_feedback.py`, both rebuilt with the current code. The
census is laid out as a probe set (`census_set.py`, beside this file) so `cli producer bench` reads
it unchanged: every reader-A-labelled ask is an ask, and a census PR with round-1 feedback but no
labelled ask is a control.

**Measures.**
- *Recall.* Of the 49 target asks, how many share a change target with a fact (located), and how
  many the fact states (exact, by hand: the fact names the dotted form the ask requests), by shape.
- *Demand.* Of all facts, the share that share a change target with a target ask, and with any
  labelled ask. Stage H measured every census rule raised at 5% or fewer of the places a blind
  pinpointer flagged; this is the same quantity for a deterministic flagger.
- *Volume.* Facts per PR and the share of PRs with any fact.
- *Validity.* Census PRs have no reviewed workspaces, so no compile: a seeded sample of 20 facts
  (seed `dot-notation-census-2026-10-06`) is read by hand, valid as written or not.

**Reading rule.**
- A **finder** if exact recall is at least **25%** of the 49; **narrow** at 10-25%; **not a finder**
  below 10%. Recall is reported per shape, since a shape the detector does not target (a
  proof-local hypothesis, a term that is not a binder) is a known gap, not a failure.
- **Demand** is read against stage H: above **5%** of facts at a target ask is better demanded than
  any rule stage H measured; at or below it, the detector shares stage H's limit, and a packet
  section of these facts mostly tells the reviewer about places nobody asks about.
- **Validity** at least half of the sample, as in stage 1.

## Stage 3: two more detectors (pre-registered 2026-10-06, before either is written)

The producer seam's claim is that a detector is one module and one registry line. Two more test it,
the next two conventions by census recurrence that a deterministic check can state from the
change graph alone. Both read only declarations the PR adds or renames, and both state a sibling
the graph can see; neither guesses about the library beyond the PR's changed files.

1. **`primed_names` (P113; P211 not targeted).** A declaration the PR adds or renames whose leaf
   ends in `'`, when the unprimed full name is declared in the graph (either side): the fact names
   the sibling and gives both conclusions, so the term that differs can be named. A primed name
   with no visible sibling is skipped -- whether one exists elsewhere in Mathlib is not decidable
   here, and P211 is about exactly that.
2. **`generated_twins` (P201).** Two shapes. `@[to_fun]`: the PR adds `NS.fun_X` by hand while
   `NS.X` is declared in the graph. `@[to_additive]`: the PR adds two declarations in one file whose
   leaves are a multiplicative name and its additive translation (word for word: `mul`/`add`,
   `one`/`zero`, `prod`/`sum`, `inv`/`neg`, `div`/`sub`, `pow`/`nsmul`, `zpow`/`zsmul`, `smul`/`vadd`,
   and the capitalised forms), and the multiplicative one carries no `to_additive` attribute.

In sample: dev's `6b02b611` (33421, `round_eq'` -> `round_eq_div`) and `57bcc9fd` (33117,
`@[to_fun]`) were read while choosing these conventions. Census targets: P113 6 asks on 6 PRs,
P211 3 on 3, P201 11 on 10.

**Reading rule**, the same as stages 1 and 2 for each detector: control emission at most 1.0 fact
per control PR on validation small12 and post-cutoff; at least half the facts valid as written,
by reading (every fact if there are 20 or fewer, else the seeded sample); census recall reported
per convention against its target asks, a finder at >= 25% exact, narrow at 10-25%, not a finder
below 10% -- at 9 and 11 targets these bands are coarse, and a single ask moves them; demand read
against stage H's 5%.

**Amendment 2 (before stage 3 ran).** Writing `generated_twins` showed one false-positive mode the
rule above did not name: in a ring, `map_mul` and `map_add` are both primary lemmas, not a generated
pair. The `@[to_additive]` shape skips a multiplicative declaration whose signature names a
ring-like class (`Semiring`, `Ring`, `CommRing`, `Field`, `DivisionRing`, `Algebra`, `Module`,
`NonUnitalNonAssocSemiring`), and a pair split across two files.

## Results, stages 2 and 3 (2026-10-06), read by the rules above

The census structure was rebuilt with the current code: 973 change graphs, 0 failures; 2,306
round-1 comments, the same ids as the committed events. Laid out as a probe set by `census_set.py`
(1,833 labelled asks on 642 PRs; 331 control PRs with none). Per-detector summaries, facts and
readings are under `census/`.

**Stage 2, dot notation on the census.** 217 facts on 114 of 973 PRs; 46 on the 331 control PRs
(0.14 per control PR). 22 of the 49 target asks are located (P057 17 of 29, P108 4 of 16, P034 1
of 4). Read by hand, **9 are the fact exactly**: `hϕ.clm_apply_of_inCoordinates` (v0005), `d.count`
(v0644), `Set.Infinite.of_accPt` (v1252 and its follow-up v1254), `hs.eq_iInter_nat` (v1397),
`hp.ne_zero` (v1412-v1414), `A.toLin'` (v1661). The other 13 ask something else at the same
change target -- mostly another dotted call the detector does not produce (`clm_bundle_apply`,
whose receiver is not a binder), a different namespace choice (`IsUnit.splits` against the fact's
`Splits.of_isUnit`), or something unrelated.
- **Recall: 9 of 49 exact, 18% -- a narrow finder** (band 10-25%). By shape: method call 7 of 29,
  placement 2 of 16, leading dot 0 of 4.
- **Demand: 19 of 217 facts located at a target ask, 8.8%** -- above stage H's 5%, by the
  pre-registered measure. Counted by exact match it is 8 of 217 (3.7%), within stage H's range.
- **Validity: 13 of the 20 sampled facts valid as written** (at least half: met). The seven invalid
  have three mechanisms: a call prefix in a namespace nested under the binder's type
  (`PullbackCone.IsLimit.lift ht`, `ht : IsLimit …`, whose `ht.lift` is the general `IsLimit.lift`;
  three facts) or a qualified binder type that differs from the prefix (`adj₂ : Bicategory.Adjunction`
  against `Adjunction.ofCat`) -- the in-sample failure again; a capitalised variable taken for a
  namespace (`P.lemma h`, `S.downward_closed hf`; two); and a relation-typed binder read as its
  head (`h : Fintype.card α = …`; one).

**Stage 3, primed names.** Probe sets: 7 facts, 0 on any control PR, all 7 true as stated; exact
asks 1 in sample (`round_eq'`, d0048) and **1 out of sample** (43167, p0012: "`commutator_sup_left_of_normal`
... rather than a prime"); three times a maintainer's own suggestion kept the prime (`Dense.ciSup'`,
`Dense.ciInf'`, `exists_infinite_fiber'`). Census: 101 facts on 68 PRs, 18 on 331 control PRs
(0.05 per control PR); **5 of the 9 target asks located, and all 5 are the fact exactly** (P113 4
of 6, P211 1 of 3) -- **a finder** by the band, at nine targets where one ask moves it 11 points.
Demand 5 of 101 (5.0%), at stage H's bound. The seeded sample: 20 of 20 true as stated (a fact
here asserts a sibling and two conclusions, which the graph either has or does not).
**Packet-ready by the rule**: no out-of-sample control emission, both out-of-sample facts valid.

**Stage 3, generated twins.** The `@[to_additive]` shape is **0 of 29 valid** across every set (8
on the probe sets, 21 on the census): lexical coincidences of `one`/`zero` and `mul`/`add` --
evaluation lemmas (`epow_zero` beside `epow_one`), sums and products of meromorphic functions,
ordinal arithmetic, modules (`SModEq`); amendment 2's ring-like filter matched whole words only
and missed `NontriviallyNormedField`. The `@[to_fun]` shape is 11 of 11 valid and exactly the
ask in sample (33117, d0018), and fires on no census or out-of-sample PR. Census recall 0 of 11.
**Too noisy, by the rule; the failing shape is `@[to_additive]`.** The census's P201 asks are
mostly a missing attribute on a lemma with no hand-written twin (as 43167's p0011, "Missing
`@[to_additive]` here"), which neither shape can see.

## Stage 4: refinements named by the misses (pre-registered 2026-10-06, before either is written)

**`dot_notation/2`** adds three conditions to the method-call shape, one per invalid mechanism the
stage-2 sample showed, and changes nothing else:
- *R1, qualified binder.* When the binder's type head is written qualified (`Bicategory.Adjunction`,
  `Ordinal.IsNormal`), the call prefix must be exactly that head; `x.lemma` resolves in the binder's
  own namespace first. (An unqualified binder head keeps the last-component match: the dev facts on
  `H : IsNormal …` compile. The `PullbackCone.IsLimit` case, unqualified `IsLimit`, is not reachable
  without the environment and stays.)
- *R2, a variable is not a namespace.* The prefix's first component is neither a binder name of the
  declaration nor a single capital letter (`P.lemma h`, `S.downward_closed hf`).
- *R3, a relation is not a receiver.* A binder whose type is a relation (`conclusion_head` not
  `other`: `h : Fintype.card α = …`) is not a receiver.

Since the three were read off the stage-2 sample, they are tested on a **holdout**: a fresh seeded
sample of 20 census facts of `/2`, none of them in the stage-2 sample (seed
`dot-notation-census-2026-10-06-holdout`). **Bars:** at least **15 of 20** valid as written (stage 2's
sample was 13 of 20); of the 9 exact census asks, at most **one** lost; and the dev compile outcomes
reported for the facts that remain (in sample: R1 is expected to drop all three `Ordinal.IsNormal`
facts, two invalid and one valid).

**`generated_twins/2`** retires the `@[to_additive]` shape, wrong on 29 of 29 facts. Nothing is
tuned: the `@[to_fun]` shape is unchanged, and its facts must be identical.

## Results, stage 4 (2026-10-06), read by its rule

**`dot_notation/2`.** Census: 217 -> 190 facts, 114 -> 103 PRs with a fact, control-PR facts
46 -> 35 (0.11 per control PR). **All 9 exact census asks are still located** (bar: at most one
lost). Dev: 7 -> 4 facts; R1 dropped the three `Ordinal.IsNormal` facts (the two that failed to
compile and the one that compiled), and the four left are all valid (three compile, one is the
maintainer's own suggestion). Validation small12 and post-cutoff: still 0.
**Holdout: 19 of 20 valid as written** (`census/dot_notation_v2/holdout.json`; bar 15; stage 2's
sample was 13 of 20). The one invalid fact is a parsing defect, not a convention error:
`Finset.range F.card` was matched as `Finset.range F`, because the argument pattern stops before a
projection. Two placement facts drop a qualifier from a dotted predicate (`s.Nonempty`, whose
namespace is `Set.Nonempty`, stated as `Nonempty.of_…`; stage 2's `F.HasPointwiseLeftDerivedFunctor`
likewise) and are counted valid, as stage 2 counted them, with the imprecision named here.
**Passed on all three bars.** Three of the holdout facts are on PRs that add a toy
`MyNewProofs.lean` (36912, 36914, 36915) -- valid, and a reminder that the census carries such PRs.

**`generated_twins/2`.** The `@[to_fun]` facts are identical (11 on dev, 0 elsewhere); the
`@[to_additive]` shape is gone.

**`dot_notation/3` (2026-10-06, after the holdout).** Fixes the parsing defect the holdout found:
an argument followed by a projection (`Finset.range F.card`, `X.lemma h.1`) is not the receiver.
Census: 188 -> 180 distinct facts (9 removed, 1 added -- a call a projection occurrence had
shadowed), control-PR facts 35 -> 33; dev unchanged (four facts); validation and post-cutoff still 0.

**A correction to stage 2's exact count: 9 -> 8 of 49 (16%, still narrow).** One removed fact
was the one credited as `v0005`'s exact match. Read at its own line it was wrong: line 430 is
`ContinuousWithinAt.clm_apply_of_inCoordinates hϕ.2 hv hϕ.1`, whose receiver is `hϕ.2`, and the
fact named `hϕ`. Its text matched `v0005`'s ask (at line 387, where there was no fact) by
coincidence of the misparse. `v0006`, the ask at line 430, asks for `hϕ.2.clm_apply_of_inCoordinates`,
which a binder-typed shape cannot state. Under `/3` neither is stated, and 8 of 49 are exact.

## Stage 5: does a section that states the exact ask make a reviewer file it? (pre-registered 2026-10-06, before the set is built)

Stages 1-4 measured the facts. This stage measures a reviewer reading them, at the one place the
answer is cheapest to read: PRs where a packet-ready detector states, word for word, what a
maintainer asked. **The record predicts a null.** The ceiling probe's stage G handed a reviewer the
right convention at the right place with a check, and the reviewer verified it and overrode it
(+0.000). This stage tests whether a deterministic fact about the code fares differently.

**Set** (census PRs, val1000, disjoint from every evaluation set):
- *Stratum A, asked*: every PR where a packet-ready detector's fact is exactly a reader-A ask, by
  the stage 2-4 hand reads -- `dot_notation/3`: 28484 (v0644), 31961 (v1252, v1254), 32674 (v1397),
  32715 (v1412-v1414), 34241 (v1661); `primed_names`: 30645 (v1057), 31007 (v1096), 32992 (v1490),
  35807 (v1935), 36355 (v2081). **10 PRs, 13 asks.**
- *Stratum B, unasked*: 6 PRs in the seeded order (seed `census-detectors-stage5`) of census PRs
  where a packet-ready fact fires and no labelled ask shares a change target with any fact.
- A PR whose reviewed workspace does not build is replaced from its stratum's seeded order (B) or
  dropped and reported (A).

The release is cut from the sealed val1000 draw restricted to these PRs, by the same writer the
evaluation releases use (`frame.write_evaluation_release`), into `inputs/probes/census-detectors-v1/`.

**Conditions** -- the frozen solo baseline harness (Opus 5.5 under Claude Code, contract v2, the
hygiene tools), one rep each, differing only in `context_file`:
- *S0*: each PR's pass-0 PR model, as every probe set has it;
- *S1*: the same, followed by the `primed_names` and `dot_notation/3` sections.

**Reading, by hand (no judge).** For each of the 13 stratum-A asks: is there a finding at its place
asking for its change, in S0 and in S1? For every section fact without an ask (stratum B, and
stratum A's other facts): is there a finding that repeats it, in S0 and in S1?
- The section **moves the reviewer** if S1 files at least **4 more** of the 13 asks than S0;
  **no effect** at a difference of 1 or less; between, a second rep decides.
- **Emission:** S1's findings that repeat an unasked fact, against S0's, per stratum-B PR. More than
  1.0 more per PR than S0 makes the section a volume lever, whatever it does to the asks.

## Stage 6: a missing generator attribute (pre-registered 2026-10-06, before the detector is written)

Stage 3 found most census P201 asks are a missing attribute on a lemma with no hand-written twin
(43167's p0011, "Missing `@[to_additive]` here"), which no twin shape can see. **`missing_attribute`**
states that fact from the file alone: a declaration the PR adds that carries none of a generator
attribute -- `to_additive`, `to_dual` -- while **at least 3 of the file's other declarations, and at
least half of them**, carry it (graph entities of the same path, either side). The fact names the
attribute and the count. An additive-named declaration (`add`, `zero`, `sum`, `neg`, `sub`, `nsmul`,
`vadd` among its leaf words) is skipped for `to_additive`, since it is what the attribute generates.

Measured as stages 1-3: probe sets (dev in sample only in that 43167's ask was read in stage 3;
validation small12 and post-cutoff otherwise unread for this shape) and the census, P201's 11 asks.
**Bars:** control emission at most 1.0 per control PR on validation small12 and post-cutoff; at least
half the facts valid as written, by reading (all if 20 or fewer, else a seeded sample of 20, seed
`missing-attribute-2026-10-06`) -- valid meaning the attribute would apply to the declaration as
stated; census recall in the stage-2 bands.

## Results, stage 6 (2026-10-06), read by its rule

| set | facts | PRs with a fact | control-PR facts | asks located |
|---|---|---|---|---|
| dev | 0 | 0 | 0 | -- |
| validation small12 | 0 | 0 | 0 | -- |
| post-cutoff | 3 | 1 (43167) | 0 | p0010-p0012 |
| census | 19 | 10 | 0 on 331 | 0 of 11 P201 targets |

On 43167 the three facts are the three places of one ask exactly -- p0011, "Missing `@[to_additive]`
here, on line 357, and on the private lemma" (`commutator_sup_left` at 337, `commutator_sup_right`
at 357, the private `commutator_sup_left'` at 326) -- but that ask motivated the detector, so it is
in sample. **Census validity: 8 of 19**, under the half bar: **too noisy, by the rule.** The eleven
invalid have two mechanisms, both visible in the code:
- *the declaration is itself the additive form* (8): `AddZero`, `NegAntiClass`, `HasMemOrNegMem`,
  `instNatSMul`, `instIntSMul`, and `AddSubmonoid.IsSpanning`, `AddSubmonoid.IsPointed`,
  `AddSubgroup.IsSubnormal` -- the additive-word skip read `_`-separated leaf words only, not
  camelCase parts or the namespace;
- *a parsing defect* (3): `@[to_dual] lemma succ_max` and `@[to_additive] lemma closure_pow_le` carry the
  attribute on the keyword's own line, and the attribute block was read only when the keyword
  started a line.
The 8 valid are `isSMulRegular_iff` (three files) and the `genLTOne_*` lemmas (two PRs). Census
recall 0 of 11: the census's P201 asks sit elsewhere than these facts.

## Stage 6b: the two fixes, on a holdout (pre-registered 2026-10-06, before either is written)

**`missing_attribute/2`**: the attribute block is read up to the first declaration keyword wherever
it sits (comments and strings masked), and the additive skip reads every word of the full name --
`.`- and `_`-separated, then camelCase parts (`AddSubmonoid`, `NegAntiClass`) -- not the leaf's
`_` words alone. Nothing else changes. Since both were read off the census facts, the measurement
is a **holdout**: every `/2` fact on the 60-PR validation release
(`inputs/pr_review_v4/releases/val-2025-06-2026-03-v1`, change graphs only, no asks read), by hand,
seeded sample of 20 if more (seed `missing-attribute-2-holdout`). **Bar:** at least half valid as
written. The census count under `/2` is reported, in sample.

## Results, stage 6b (2026-10-06)

**Holdout: no facts.** `missing_attribute/2` states nothing on any of the 60 validation-release PRs,
so the validity bar is **unmeasured** -- there is nothing to judge, as with dot notation's
out-of-sample sets in stage 1. In sample: the census falls from 19 facts to 8, and the 8 left are
exactly the 8 read valid in stage 6 (`isSMulRegular_iff` in three files, the `genLTOne_*` lemmas on
26591 and 26846); 43167's three facts stand. **What it shows:** a precise but nearly silent section
-- 8 facts on 3 of 973 census PRs, none on a control PR, none at any of the census's 11 P201 asks.
It is not shown to be a lever, and on this evidence it rarely has anything to say.

**Stage 5, ready and not run (2026-10-06).** The workspaces are built: 14 base snapshots (two
existed), restored, then 16 of 16 reviewed workspaces (`stage5/build.log`; 11:45-16:29 after a
first launch died on the home-directory quota, `stage5/build_*_attempt1.*`). `cli plan` preflights
both conditions clean with the login exported: 16 of 16 workspaces prebuilt, both plans seal (S0
agenda `6a9532d20371`, S1 `c3f0e42ed4b4`, 702 prompt hashes each). The run is not launched: the two
Pro subscription accounts now refuse Claude Code, so it would spend the user's primary quota
(about two five-hour windows; seven_day at 67% that day), which is the user's call. Commands:
`ape/bin/python -m src.mathlib_review.review.cli run --config configs/pr_review_v5_census_detectors_v1_opus55_hygiene_claude_sub.yaml --run-name probe_census_detectors_s0_rep1 --execute`,
then the `_hygiene_sections_` config as `probe_census_detectors_s1_rep1`.

## Stage 5 on gpt-5.5, with S2 (amendment, pre-registered 2026-10-07, before any session)

**The user (2026-10-07):** *"Okay let's run with GPT"* -- after the two Pro subscription accounts
began refusing Claude Code and the primary account's week stood at 67%. **What changes is the
reviewer**, and nothing about the set, the sections or the reading rule: Opus 5.5 under Claude Code
becomes `elm_gpt_5.5` under APE-Agent in **stage W's condition** (branch `generation-suppression`,
`results/pr_review_v5/probes/generation-suppression-2026-10-06/run_wide.sh`): high effort, reasoning
carried, summaries on, brief G, the five context tools, `filing_bar: request`, $20 and 24M tokens a
session. It is the condition in which the disposition paragraph moved gpt-5.5's in-census reach 0.43 to
0.62 out of sample. So this measures whether the sections move **gpt-5.5**, not Opus; the Claude
configs stay as the stage first written, built and unrun. GPT is the more informative reader for S1
in any case: 11 of its 23 in-census misses in the conventions probe were never considered at the
place (`conventions-ceiling-2026-10-04/cross_model.md`), the gap a section naming the place targets.

**Conditions**, one run each, differing in `context_file` alone:
- **S0**: each PR's pass-0 model (`stage5/model_context_s0.jsonl`, as built for the Claude stage);
- **S1**: S0 then the `primed_names` and `dot_notation/3` sections (`stage5/model_context_s1.jsonl`);
- **S2**: S1 then one closing section, the plan `2026-10-06-generation-without-suppression.md`'s C1 in
  the form stage W measured (`probes.CONVENTIONS_DISPOSITION` on that branch), worded for places
  rather than conventions, titled "Dispositions for the places above", text fixed now:

  > Give every place listed in the sections above a disposition, and say in your submission's
  > `message` which you gave and on what ground. `departs`: file the change its section describes,
  > as a finding at that place. `conforms`: only if a check you ran, or a line of the code you quote,
  > shows the required form already holds there. What Mathlib usually requires, accepts or enforces,
  > how minor the change is, and whether a maintainer would insist on it are not grounds for either
  > disposition. For these places this replaces the brief's instruction to emit only what you would
  > actually request.

**Order.** A smoke first: S2's configuration on `elm_qwen_3.5` (priced 0) on 30645 and 28484 --
the sessions start, the sections reach the prompt, a submission lands; not read for any result. Then
S0 and S1 together. S2 runs only if S1 files fewer than 10 of the 13 asks (the plan's skip rule: from
10, S2 cannot gain 4).

**Reading, by hand and blind to condition.** Round 1, S0 against S1: per PR, the two sessions'
findings under labels shuffled by a seeded permutation (seed `stage5-gpt-round1`), the key written
to disk before reading and opened after every mark. Round 2, if S2 runs: S1 against S2 the same way
(seed `stage5-gpt-round2`), so S1 is marked twice and the two marks give my own agreement. Marks as
stage 5 first said: per stratum-A ask, a finding at its place asking for its change; per unasked
section fact, a finding that repeats it.

**Rules**, each a difference between successive conditions on the 13 asks:
- S1 - S0 **>= 4**: the sections move gpt-5.5; **<= 1**: no effect; between: a second rep decides.
- S2 - S1, the same bands: the disposition is a lever on detector facts, or not.
- **Emission gate**, as first written: stratum-B findings repeating an unasked fact, more than 1.0 more
  a stratum-B PR than the condition before makes that step a volume lever, whatever it does to the asks.
- **Also read (S2)**: the dispositions in `message`; places marked `departs` and not filed; `conforms`
  with no check or quote (the plan's C3). Sessions stopped by a cap are reported, not dropped.

**Cost.** Stage W billed $15.61 for 13 sessions, about $1.20 a session: 32-48 sessions is about
$40-60 at list price, from the ELM key (GBP 458 left on 2026-10-07). The $20 session cap binds a
session; the run caps are set to fit 16 of them, a ceiling, not a forecast.

**Smoke (2026-10-07 05:12-05:17), passed.** `iter_elmqwen35_census_detectors_s2_smoke`: both sessions
started and submitted (28484: 29 turns, 0.75M tokens; 30645: 32 turns, 1.42M), no retries, $0.00.
Each prompt holds its PR model, its own detector section (28484 dot notation, 30645 primed names)
and the disposition section. `probes._solo` loads the run's findings with their targets, so
`cli probe match-inputs` can blind it. Not read for any result. S0 and S1 launched at 05:21,
both answered by ELM's Responses endpoint in their first minute with no retries.

One change to the reading, made before any GPT session ended: the labels come from `cli probe seal`,
a fresh draw from `secrets` written to disk before reading, rather than a permutation from a seed I
named. The seeded one would have let me recompute the key.

**Interruptions (2026-10-07).** S0 and S1 died with the Claude Code process that launched them at
05:40, 7 of 16 sessions each done; relaunched detached with `--resume` at 05:46, and stopped again by
me at 05:49 on a misread cost: the log's `cost=` is nominal ($65.44 for S0's seven), the bill is
`billed_cost` ($13.15, $1.88 a session against stage W's $1.17-1.23; these sessions run 30 turns and
1.8M tokens against about 18 and 0.8M). Resumed at 05:52, 7 kept and 4 started in each. The
sessions in flight at each stop were lost and rerun from the start; none of them had submitted. Cost
re-estimated: S0 and S1 about $60 billed, S2 about $30 more, which waits for the user's word.
