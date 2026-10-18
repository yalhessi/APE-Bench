# Adversarial review 2: the two departures probes (2026-10-16)

Reviewer: an independent attack on the validity of
`results/pr_review_v5/probes/enforcement-at-departures-2026-10-16/` and
`results/pr_review_v5/probes/stage-h-departures-2026-10-16/`. Read in full: both PROTOCOL.md and RESULTS.md,
every script, every reading (`readings/{A,B}_{1,2}`, `{C,D}_primes`, `R1`, `R2`), `conventions_as_held.md`, the
66 stage-H packets in scratch, the reader notes in scratch (`stageh_R1/notes.txt`, `stageh_R2/len.py`), the
calibration asks' bodies (`scratchpad/bodies.json`), stage H's Result 6 and `rules.json`. Nothing that spends was
run. The scoring scripts were re-run read-only; `survival.py` was re-run once and rewrote `survival.jsonl`
byte-identically (git shows no change). My own checks are scratch scripts in
`/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/a142d916-dd29-4521-a449-00e1db067b18/scratchpad/rev2/`
(`rawfollow.py`, `rate.py`, `breaks.py`, `preexist.py`, `gone.py`, `diffplace.py`). No other file was modified.

The four headlines under attack:
- (a) for dot notation and layout rules (line breaks, `variable` lines, merging tactic steps), real departures merge unasked;
- (b) for substantive rules (use the existing API, name like siblings, drop an unneeded hypothesis), flagged places mostly already conform, so the 5% was mostly conforming code;
- (c) per real departure, maintainers ask about 10%;
- (d) the namespace-placement detector proposed the wrong namespace (97% not departures).

## Numbers computed for this review

| what | value |
|---|---|
| Stage H, pinpointer status by rule | P048 and P084 (the two `read` rules): 29 of 29 places `departs`; the other eight rules: 176 of 176 `check`. In the step-2 sample: 11 of 11 and 49 of 49 |
| Step-2 open items whose blind-pass note asserts a departure (names a concrete alternative, a contrasting precedent, or a measured line length) / hedges ("possibly", "may") / is neutral | 26 / 7 / 27 (my coding, listed under attack 3) |
| Both-agree `departs` by note type | asserted **13 of 22 decided**; hedged **0 of 6**; neutral **0 of 20**. Pooled reader labels: 29/51, 0/12, 1/42 |
| …asserted notes only, by rule kind | read rules 6 of 9 (67%); all other rules 7 of 13 (54%) |
| Calibration by note type | the 4 asked places whose note names the fix (H009, H023, H048, H049): 8 of 8 reader labels `departs`; the 2 whose note states only the trigger (H055, H066): **1 of 4** |
| Substantive `conforms` (P005 P010 P011 P040 P100 P126 P254), both agree, by what the label rests on | verified by me at base 6, positive finding stated 11, absence of evidence 4, judgement ("reads no better", "not shorter") 7, contested 1 (of 29) |
| Substantive departure share, both agree | reported 4/34 = 12%; with H008 (verified below) 5/35 = 14%; positive-or-verified conforms only 5/23 = 22%; absence counted as departure 9/35 = 26%; absence, judgement and contested counted as departure 17/35 = **49%** |
| Confidence of `departs` on the read rules (both readers) | high 0, medium 5, low 9. P018 `departs`: low 6 of 6 |
| `needs_tools` by check kind (both readers) | compile 10 (8 of them P005); lookup **0 of 92** |
| Spot-checks of substantive `conforms` at base (12 open labels + 1 calibration) | 7 verified, 2 plausible, 1 contested, **2 contradicted**, plus the calibration miss contradicted |
| Census asks that cover more than their mapped place | v1838 "similar below" (covers `isInitial`, H008, counted unasked); v2242 "The same for the other lemma" (covers 37190's second P084 place, counted unasked): **8 asked places, not 6** |
| Places on PRs with no merge in the clone | 41: PR 30244 21 ("chore(Algebra): misc. generalizations by LLM", closed unmerged 2025-10-16), 37190 17 (merged by Bors after the clone's HEAD), 28926 4 (closed unmerged) |
| Ask rate per departure, per rule (pooled reader labels) | P011 4 / (4 + 0.17 × 13) = **65%** (71% with the "similar below" ask); P084 1 / (1 + 0.83 × 22) = **5%** (10% with "the other lemma"); P010 1 ask, 0 estimated unasked departures |
| …by group | substantive 5 asks against ~24 estimated unasked departures = 17%; layout (P084 P048 P018) 1 against ~30 = 3% |
| Pooled rate, interval | cluster bootstrap over the 16 PRs (20,000 resamples, both-agree labels): median 10%, **95% 3.6% to 23%**; d 14% to 36%. Wilson on 13/48 alone: rate 6.9% to 15.4% |
| Pooled rate under the corrections | 8 asks: 13%; d = 0.37 (absence counted as departure): 7.6%; d = 0.53 (pessimistic): 5.4% |
| `follow.py` without whitespace normalisation | all 100 `unchanged` places are byte-identical blocks too; normalisation hid no layout fix |
| Layout places changed or gone by merge | 8; every one changed by another rewrite (the asked P011 rewrite at 35140 and deletion at 26979, the rename at 32598, a proof rewrite at 31081); **none toward its layout rule** |
| Base Mathlib, two-line signatures broken after `:` whose joined line fits in 100 | CategoryTheory/Limits 112 of 1,018 (11%); RingTheory/Smooth 5 of 30 (17%); ComposableArrows 4 of 17 (24%) |
| Located unasked places on P100 / P126, where a fix may not touch the flagged block | 46 of 145 |
| `survival.py` `declared_in_tree` | `git grep -E` rejects `(?:` and `(?!` ("Invalid preceding regular expression", exit 128); returns False even for `add_comm`. With `-P`: 2 unasked P113 "gone" facts are declared in another file at merge (moved, so survived) |
| Enforcement survivors not introduced by the PR | 21 of 111 unasked survivors already in the same file at base (P057 5/24 calls, P108 8/43, P113 8/44); up to 12 more have the leaf declared elsewhere at base (leaf-only, noisy; 4 checked by hand are real moves) |
| P108 both-agree exclusions (33), by what the place is | 19 already in the namespace of their main argument or hypothesis; 8 not introduced by the PR; 6 root- or general-namespace (2 with only instance hypotheses) |

---

## 1. The check-kind confound

**The claim.** RESULTS splits by check kind: search rules 15% departs, compile rules 24%, read rules 64%.

**The confound is larger than the one the brief names.** Check kind coincides exactly with the pinpointer's own
verdict: every place on the two read rules carries `departs` (29 of 29), every other place `check` (176 of 176). And
the packets show the pinpointer's note ("What the blind pass noted here"). On read rules the note states a measured
departure ("though the joined line is 81 characters"); on the others it mostly describes the situation ("whether
both are needed for every `n` is to be checked"). **Every one of the 13 both-agree `departs` sits at a place whose
note already asserted it.** At the 27 places with a neutral note, the readers found no departure both agreed on
(0 of 20 decided); at 7 hedged notes, none (0 of 6). Holding the note fixed, rule kind matters little: asserted notes
give 67% departs on read rules and 54% on the rest. In this design the split by rule kind cannot be separated from
the note's wording.

**Did the readers default to `conforms` where they could not verify?** Partly, and in specific places.
- **Search rules other than P011: no.** Of each reader's 18 search-rule `conforms` (P011 included), 14 (R1) and 15
  (R2) cite a found sibling, a file count or a generated name. I checked six at the base commit and all hold: H015 and H041 (no `IsMeagre` biUnion,
  sUnion or left/right union sibling exists at d61d5bb; only `mono`, `inter`, `iUnion`), H029 (`basisCotangent_apply`
  and `basisCotangentAway_apply` exist), H026 (`isEmptyEquiv_apply_tprod`, `tmulEquivDep` exist), H053
  (`Functor.isZero (hF : ∀ X, IsZero (F.obj X)) : IsZero F` at ZeroObjects.lean:140), H039 (ComposableArrows primes
  argument-form variants at base: `obj'`, `map'`, `app'`, `naturality'`).
- **P011, use the existing API: yes, and the checkable cases fail.** Three open places. H008 R1 `conforms` ("the
  `evaluationJointlyReflectsLimits` route would not be shorter"): the maintainer's round-1 suggestion on the twin
  `isTerminal` is exactly that route and ends "similar below", and the merged `isInitial` is
  `refine evaluationJointlyReflectsColimits _ …`. H019 holds (no ComposableArrows `IsIso` API at 23a3f86). H004 rests
  on a judgement (R2 found `SubmersivePresentation.isStandardSmoothOfRelativeDimension`; using it is about the same
  length; merged unchanged). On the calibration H055 both readers said "no base API yields it"; the ask was
  `update_eq_self i₀ f` for an inner `have`, a lemma at Logic/Function/Basic.lean:546 at the base. R2 searched for
  `update_eq_const` on H016 and missed it.
- **Compile rules: mixed.** P010's ten `conforms` give mathematical reasons the hypothesis is used; I checked H002's
  (`rank_subsingleton : Module.rank R M = 1` over a trivial ring, so `[Nontrivial S]` is needed). Two of them
  (H040, H051) are places where the hypothesis *is* the statement (`[IsEmpty n]` in a lemma about empty matrices),
  so the rule barely applies. P005's two `conforms` (H034, H035) are predictions that "no finisher plausibly" closes
  the goal, never compiled. P040's ten `conforms` are "a term would read worse", the rule's own escape, with no
  compile.
- **No honest abstention on search rules.** `needs_tools` appears 10 times on compile rules and 0 of 92 times on
  search rules. The readers had `git grep`, so every search question got a verdict, though "is there a combination of
  library lemmas that yields this" is not something grep settles. The label text makes `conforms` the default for a
  prediction: "`conforms` (… or its check would fail)".
- **One more contradiction, by the rule's own letter.** H010 (P100, `+to_dual` on the `hom_inv_id_app` family):
  R2 found `Iso.map_hom_inv_id_app` and `map_inv_hom_id_app` (Functor/Category.lean:199, 204) without `to_dual` and
  labelled `conforms` because they are "outside this file-scoped PR". P100's check says "in the file and library".
  H038 (`domain_sSup`) is contested: the file has 8 `X_domain` names against 4 `domain_X`, and the nearest sibling
  `domain_sup` supports the PR.

**Re-estimate.** Both-agree substantive places: 4 departs, 29 conforms, 1 excluded. By what each `conforms` rests
on, the departure share runs from 12% (as reported) through 22% (only positive or verified `conforms` kept) and
26% (absence counted as departure, H008 added) to 49% (absence, judgement and the contested one counted as
departure). The first spot-check sample was not random (I chose search and absence cases), but 3 of 13 checked
`conforms` labels were contradicted.

**Changes a headline?** (b) weakens. It holds where `conforms` rests on something checkable: naming (P254, 7 of 8
both-agree `conforms` cite a matching sibling or a generated name) and unneeded hypotheses (P010). For P011 it is not
supported (3 places, one a departure the maintainer asked about). For P005 and P040 it rests on predictions without a
compile. The split between layout and substantive rules is not shown to be about rule kind at all (see attack 3).

**Smallest fix.** Re-read the same 66 items with the "What the blind pass noted here" line removed, by two new
readers, and report labels by note type and rule. Pre-state: if the substantive departure share stays at or under
25% without the note, (b) stands on the reading; if it moves toward the read rules' rate, the split was the note.
Separately, add the per-label basis table above to RESULTS.

## 2. Calibration

**Stage H.** Six asked places; R1 4 of 6 (fails), R2 5 of 6. The bar tests less than it seems. Four of the six notes
name the fix: H023 "although the PR's generalised isMeagre_iUnion yields the ℕ case directly"; H048 "pulling back
along `ULift.down` (InvImage …) may give it directly"; H009 "so it may now be unneeded"; H049 "would fit within 100".
On those, 8 of 8 labels are `departs`: a reader that only confirms the note passes. On the two whose note states only
the trigger, 1 of 4. That 1-in-4 is the measured sensitivity on the kind of place where 34 of the 49 substantive open
items sit (neutral or hedged note). Four labels cannot pin it (exact 95% interval 0.6% to 81%), so `conforms` at a
neutral-note place means "the reader found no departure", with a sensitivity that is unmeasured and may be low.
Calibration also tests only one rule properly: 4 of 6 asked places are P011, one P010, one P084.

**The shared miss, H055.** The ask (v1378, ocfnash) is "this can be: `have h : … := update_eq_self i₀ f`", a
one-line sub-step inside a 20-line construction. Both readers judged the declaration as a whole, as the note framed
it ("Built by hand with `LinearEquiv.ofLinear` … for an equivalence about notions with library API"), and both said
no base API yields the dependent equivalence. Two things follow. P011 asks often land on a step, not on the
declaration, and the readers did not search at that grain, so P011 `conforms` is an upper bound on conformity. And
the two readers' errors are correlated (same model family, same packet), so restricting to the 59 items both agree on
keeps shared errors rather than removing them. Of the 6 open disagreements, 4 have one `departs`; dropping them
lowers d.

**Enforcement probe.** Both readers pass at exactly 9 of 13, but per convention: P057 5 of 5 (exact 95% lower bound on
sensitivity 0.55), P108 2 of 2 (lower bound 0.22), P113 2 of 6 (fails). And one of the two P108 items is not blind:
`conventions_as_held.md` quotes I044's own ask ("if you have the expected type being `Set.Infinite _` then you can
write `.of_accPt hAccPt`"), and reader B wrote "Packet's own ask endorses .of_accPt". So the 97% for P108 rests on
**one** blind calibration item, and no calibration item exercises the ground used for 58 exclusions (main-hypothesis
namespace). Calibration measures sensitivity only, which is the right risk for (b) and (d), since both are claims
that places are not departures. On P108 it has no power.

**Changes a headline?** (b) and (d) weaken: neither has calibration that could have caught over-calling `conforms` or
`excluded` on its main ground.

**Smallest fix.** Report calibration by note type (stage H) and per convention (enforcement) in RESULTS. Strike I044
from P108's calibration count, or rewrite the P108 section of `conventions_as_held.md` without that quote. Record the
lesson where it binds: a reading packet that carries a detector's or pinpointer's verdict measures agreement with
that verdict, and a convention text that quotes a calibration item's ask unblinds it.

## 3. Framing

Wording in the packets that leans:

**Toward `departs` on layout rules.**
- The note gives a measured violation: "though the joined line is 81 characters" (H037), "the joined line is 93
  characters, within the 100 limit" (H031).
- P084's check is mechanical with no exception: "Departure: … could take its next line's leading binder, argument or
  word, or all of it, within 100 characters". So the readers labelled the letter against local practice: H037 R1
  "breaking before the type is a category-theory habit, but the rule as stated asks to join"; H014 R1 "though the base
  file breaks after the colon"; H046 R2 "though a docstring on its own line inside to_dual is common". Three of the five
  both-agree P084 departures carry such a note. Confidence: 9 of 14 read-rule `departs` are `low`, none `high`.
- P018's departures go beyond the rule's own list of combinations (concatenated `rw`, `rwa`, `by_contra!`, merged
  `calc`). H006 proposes `rintro` (R2: "though not one the rule names") and H062 `simpa`, not compiled; all six P018
  `departs` labels are `low`.

**Toward `conforms` on substantive rules.**
- The notes are neutral or "to be checked".
- The checks carry subjective bars the readers used: P011 "such a derivation exists **and is shorter**" (H008 R1:
  "would not be shorter", contradicted by the merge); P040 "if it compiles **and reads no worse**" (all ten P040
  `conforms` are "reads worse").
- The label text: "`conforms` (… or its check would fail)".
- The example asks for P011 are whole-proof replacements ("use `Subgroup.isCyclic_zpowers`", "use directly
  `continuousWithinAt_toIcoDiv_Ici`"), which cues a declaration-level search; the miss was a sub-step.
- Readers narrowed a substantive rule where they had applied the layout rule's letter: H010 (above).

**In the enforcement probe.** `conventions_as_held.md`, written by the session holding the hypothesis, tells readers
before they read that the detector's construct is wrong: "the detector proposes the conclusion's namespace (`X.of_Y`)
from the name and conclusion alone, which the rule allows only when there is no main argument". The first prime
section supplied the exclusions the readers then used ("a prime is not a departure as such"; "accept an explanation in
a docstring"), and it failed calibration. For P057 the text removes exclusion grounds instead ("Nothing in the sources
excludes term mode, tactic mode, or `simp`/`rw` lemma lists"). The construct-error split across conventions (P057 20%,
P108 97%, P113 83%) follows what the text licensed. For P108 the exclusions are mostly checkable facts (attack 6), so
wording is not the main driver there. For primes it was, as amendment 3 showed: the verdict moved 83% to 52% when the
text changed.

**Who wrote what.** The stage-H rules are stage G's text, not written for this probe, and that is a point in their
favour. The asymmetry is that P108 got an "as held" rewrite that narrowed it, while P084 ("breaks fill lines", a
sentence of ours) got none. Base Mathlib breaks a signature after `:` though the joined line would fit in 11% to 24%
of two-line signatures (112 instances in CategoryTheory/Limits alone). At 35140 the maintainer's own suggestion
(v1838) rewrote the line after `IsTerminal F :=` and kept the break before it. The one P084 ask in the record (v2242)
objects to one short binder per line, a narrower complaint than our sentence.

**Changes a headline?** (a) weakens for line breaks: these are departures from stage G's sentence, and nothing tested
whether maintainers hold that sentence; the only maintainer edit at such a place kept the "departure". (b) weakens as
in attack 1.

**Smallest fix.** The note-free re-read (attack 1). Before calling line-break places real departures, write P084 as
held from its census asks, as was done for P108, and re-read the 6 P084 items against it. Put the base-practice count
beside it in RESULTS.

## 4. Survival

**Is survival informative for (b)?** No, by construction. A conforming place merges unchanged. A departure nobody
asked about also merges unchanged: the enforcement probe measured that at 98% for dot notation and primes. So "69%
unchanged" is predicted by both readings and supports neither. RESULTS says as much for step 1. But its closing
paragraph uses "(step 1: 69% unchanged)" as support for "the layout rules' places are real departures and pass to
merge unasked". The informative cells are the few changed places:
- **Changed or gone by merge, by both-agree label:** `conforms` 9 of 31; `departs` 3 of 13; disagreements 3 of 6.
- **`departs` places:** none of them changed toward its rule.
- **`conforms` places:** none changed toward its own rule, except H008 (R1 `conforms`, changed to the API the
  maintainer asked for). The others changed with the asked P011 rewrite at 35140 or the rename at 32598.
- **Layout places:** of the 8 that changed or went, none changed toward the layout rule.

**What `follow.py` can and cannot see.**
- **Whitespace normalisation is harmless.** Re-run without it, all 100 `unchanged` blocks are byte-identical, so no
  layout fix was hidden.
- **The validity check covers only P011** (3 gone, 1 changed; the one asked P010 place is unlocated, the P084 one is
  on an unmerged PR). The method has not shown it can see a layout, naming or sibling fix.
- **For P100 and P126 a fix need not touch the flagged block.** A P100 fix adds the sibling's variant elsewhere; a P126
  fix may respell the file's other occurrences instead. That is 46 of the 145 located unasked places, where
  `unchanged` does not mean "not fixed".
- **"Gone" mixes fixes and renames:** `isMeagre_iUnionNat` deleted (the asked fix); `subsingletonEquivDep` renamed to
  `subsingletonEquiv` once the non-dependent version was replaced; `exists_of_basis_kaehlerDifferential` inlined. So
  31% is an upper bound on fixes, as RESULTS says.
- **The baseline of 14 cannot be read**, as RESULTS says.

**Enforcement survival.** It survives the attack, with two defects worth fixing.
- **`declared_in_tree` never matches** (ERE rejects `(?:`), so a declaration moved to another file reads `gone`.
  With a working search, at most 2 unasked rows move from gone to survived (`nhdsSetWithin_univ'`,
  `nhdsSetWithin_empty'`), which strengthens survival.
- **19% of unasked survivors were in the same file at base**, and up to 30% if moves are counted; I checked
  `min_def'`, `max_def'` (moved from Order/Basic.lean), `isAlgebraic_adjoin_simple_X'` and `irreducible_minpolyX'`
  (in Luroth.lean at base). The detector's "`X'` is new" is wrong for these. On names the PR did introduce, unasked
  fixes are still 2 of about 92.

**Changes a headline?** No headline rests on survival, but the closing sentence of stage-H RESULTS borrows it for (a).

**Smallest fix.** In stage-H RESULTS:
- state that survival does not separate conforming places from unasked departures;
- report P100 and P126 apart;
- say the method's validity was shown on P011 proof rewrites only.

In `survival.py`, switch `declared_in_tree` to `git grep -P`, add a test that it finds a known declaration, and re-run
(deterministic, about 15 s).

## 5. The arithmetic

**Is 6 / (6 + d × 199) the right estimator?** It has these problems, from largest to smallest.

1. **It pools rules whose rates differ by an order of magnitude.** The asks sit on three rules (P011 4, P084 1, P010
   1). With per-rule d from the readers' own labels:
   - P011 (use the existing API): **65%** of departures asked.
   - P084 (line breaks): **5%**.
   - Substantive rules together: 17%. Layout rules together: 3%.

   The 10% is a volume-weighted mixture dominated by line breaks (22 × 0.83 ≈ 18 estimated unasked departures),
   spellings (P126, ~11) and step-merging (P018, ~9), none of which has a substantive ask. RESULTS concedes that "the
   substantive rules have too few departures in the sample to say how much higher their own rate is". On these
   labels, P011's rate is most of the departures.
2. **The numerator is short by two.** "similar below" (v1838) and "The same for the other lemma" (v2242) are round-1
   asks that name a second flagged place. With 8 asks the pooled rate is 13%, P011 71% and P084 10%.
3. **d comes from both-agree labels**, which drop 4 open disagreements containing a `departs`. It is also sensitive to
   the basis of `conforms` (attack 1): d from 0.27 to 0.53 moves the pooled rate from 10% to 5.4%.
4. **d is drawn from 145 located places on merged PRs and applied to 199.** That includes 21 places on PR 30244, an
   AI-generated PR ("misc. generalizations by LLM") closed unmerged. Silence on a PR maintainers closed is not
   evidence about enforcement, and the project's own rule is that AI-generated PRs are labelled and filterable.
   Restricting to the other PRs (174 unasked places) gives 11.3%.
5. **The sample is capped at 8 a rule**, not proportional, and sits on 37 declarations in 11 PRs (one declaration,
   `isInitial`, carries 5 items). The pooled d is unweighted. Weighting by rule population gives the same 10%, by
   coincidence of P084's weight.

**Interval.** Cluster bootstrap over the 16 PRs: 95% from **3.6% to 23%**, median 10%. Binomial on d alone (Wilson):
6.9% to 15.4%. The ±12pp floor the project uses for one obligation at n of about 8 applies here too: one ask more or
less on P011 moves that rule's rate by about 10 points.

**Changes a headline?** (c) as a single number does not hold. On the readers' labels the defensible statement is per
rule group: maintainers ask at most "use the existing API" departures in this sample (on the order of two in three,
from 4 or 5 asks), and at about 1 in 20 to 1 in 10 of line-break departures by our sentence. The pooled 10% has an
interval of 4% to 23% and moves to 5% to 13% under the corrections above.

**Smallest fix.**
- Report the estimator per rule group, with the cluster-bootstrap interval.
- Count the two compressed asks.
- Label or exclude PR 30244 in `follow.jsonl` and its tables.
- Write the estimator into `score_step2.py` so it is not hand-computed.

## 6. The placement claim (d) and the primes result

**Placement.** I re-read all 34 P108 items' notes and checked five against the base.
- **19 of the 33 both-agree exclusions** are lemmas that already sit in the namespace of their main argument or
  hypothesis, for example `Functor.isIso_of_isLeftDerivedFunctor_of_inverts` beside the base dual
  `isIso_of_isRightDerivedFunctor_of_inverts` (PointwiseRightDerived.lean:179), or
  `TStructure.isLE_of_isZero` beside `isLE_of_iso`. The detector reads only the leaf `X_of_Y` and ignores the
  enclosing namespace, so these are not departures under any reading. This is the part of (d) that holds.
- **8 were not introduced by the PR:** pre-existing, uncommented, given an attribute, or untouched hunk context.
  That is a defect in the detector's "new", not a wrong namespace.
- **6 are root- or general-namespace lemmas.** Two take only instance hypotheses (`epi_of_effectiveEpi`,
  `nonempty_of_isProbabilityMeasure`), a defensible exclusion. Four (I020 `effectiveEpi_of_kernelPair`, I034
  `free_of_colorable`, I063 `isEmpty_of_commSq_sigmaι_of_ne`, I068 `isCyclic_of_injective_ringHom`) take an
  explicit main hypothesis and follow a root-named library family.
  - That is the shape of I044, `infinite_of_accPt`: root-named, a main hypothesis `AccPt x (𝓟 S)`, and a library
    leaning root (reader B counted `Set.infinite_of_*` 12 against `Infinite.of_*` 2). The maintainer asked for the
    *conclusion* namespace, which is the detector's proposal.
  - I034 departs even from the convention as held: base Coloring.lean:440 has
    `protected theorem Colorable.cliqueFree (hc : G.Colorable n)`, so the held rule puts the lemma at
    `Colorable.free`. Reader B wrote that and still labelled it excluded, because the detector's suggested fix was
    wrong. A wrong fix was read as no departure.
- **Range.** Counting those four as departures gives 29 of 34 not departures, **85%** against the reported 97%.

**Primes.** RESULTS calls primes not readable by this method, and that stands. My checks confirm the re-read's
`not_introduced` ground is factually right for the 4 I checked: the names existed at base and the PR moved them. But
that ground is the one the calibration contradicts: Q003, `integral_countable'`, was moved and the maintainer asked to
unprime it. Moving the 5 items both readers excluded on that ground to `departure` takes construct error from 52% to
29%. Neither figure should be cited.

**Dot notation (part of (a)).** It survives every attack I tried:
- 12 to 13 of 16 departures, with positive checks in the notes (dotted form resolves to the same lemma; base dotted
  counts such as 222 to 1 for `.ae_eq_mk`);
- calibration 5 of 5, with no calibration ask quoted in the text;
- 0 of 32 unasked calls fixed on control PRs.

**Changes a headline?** (d) stands in direction and weakens in explanation and size. The 97% becomes 85% to 97%.
"Proposed the wrong namespace" explains about 19 of the 34. Most of the rest is "the PR did not introduce the name".
For root-named lemmas the reading is unsettled, and the one fixed case of that shape went the detector's way.

**Smallest fix.** In enforcement RESULTS:
- report the 19 / 8 / 6 split;
- note that I044 was quoted in the convention text and is the shape of the 4 contested exclusions;
- give P108's blind calibration as 1 item.

## Defects found in the code

| file | defect | effect |
|---|---|---|
| `enforcement-at-departures-2026-10-16/survival.py` `declared_in_tree` | `git grep -E` with `(?:` and `(?!`: an invalid ERE, so the function always returns False | moved declarations read `gone`; `moved` is never assigned; ≤ 2 unasked rows affected, in the direction of more survival |
| the census mapping used by both probes | an ask's "similar below" or "the same for the other lemma" is mapped to one place | the asked count is 8, not 6 |
| detector facts (P108, P113) | "is new" holds for names the PR only moved or touched | 21 to 33 of 111 unasked survivors were not introduced by the PR |
| `follow.py` reporting | 30244 (AI-generated, unmerged) is folded into `no_merge_commit` and into the 199 | the denominator carries 21 places from a PR maintainers closed |
| `build_step2.py` packets | the pinpointer's verdict (note) is in the packet | step 2 measures agreement with the note at least as much as departures |

## Smallest fixes on disk, in order of how much they change the answer

1. **Note-free re-read of step 2.** Same 66 items, packets without the blind-pass line, two new readers. Report by
   note type and rule against a threshold stated first (substantive departs ≤ 25% keeps (b)). This is the only fix
   that separates rule kind from wording.
2. **The arithmetic per rule group**, with 8 asks, PR 30244 labelled, and the cluster-bootstrap interval, written into
   `score_step2.py`. Replaces (c).
3. **The basis table for substantive `conforms`** (verified, positive, absence, judgement) and the 12% to 49% range,
   in stage-H RESULTS.
4. **P084 as held**, written from its census asks before calling line-break places real departures, with the
   base-practice count (11% to 24%) and the 35140 suggestion beside it.
5. **Enforcement RESULTS (d):** the 19 / 8 / 6 split, I044's quote and shape, P108 calibration as 1 blind item.
6. **`survival.py`:** `-P` in `declared_in_tree`, a test that it finds a known declaration, re-run.
7. **Optional, the structural fix for attack 1:** compile the 10 `needs_tools` places, the 6 P018 `departs` and the
   P005 and P040 `conforms` with `ape.toolkits.execute.lean` on the base workspaces. Readers without a compiler
   produced both the unverified `departs` (P018) and the unverified `conforms` (P005, P040).

Lessons to record (not written here; this review modifies no other file):
- a reading packet that carries a detector's verdict measures agreement with it;
- a convention text that quotes a calibration item's ask unblinds that item;
- a wrong suggested fix is not evidence that a place conforms;
- "similar below" asks cover more than one place.

## Verdict per headline

- **(a) Dot notation and layout rules: real departures merge unasked.**
  - *Stands for dot notation.*
  - *Weakened for layout:* line breaks that our sentence calls departures merge unasked (5 both-agree places; 0
    changed toward the rule). Nothing tested that maintainers hold that sentence. Base Mathlib contains the same shape
    in 11% to 24% of two-line signatures, the maintainer who rewrote one such declaration kept the break, and 9 of 14
    such labels are low confidence.
  - "`variable` lines" rests on 1 both-agree item, and "merging tactic steps" on 3 uncompiled, low-confidence items;
    neither supports "mostly".
- **(b) Substantive rules: flagged places mostly already conform.**
  - *Weakened to:* holds on checkable grounds for naming-like rules (P254) and unneeded hypotheses (P010).
  - Not supported for "use the existing API" (P011): 3 places, one a departure the maintainer asked about and the
    merge fixed. The readers missed 3 of 8 known P011 departure labels, 3 of 4 where the note did not name the fix.
  - Rests on uncompiled predictions for P005 and P040.
  - Across substantive rules the departure share is 12% to 49% depending on what a `conforms` rests on.
  - In this design every departure the readers agreed on was one the blind pass had already named, so "conforms"
    largely means "the note did not name a departure".
- **(c) Per real departure, maintainers ask about 10%.**
  - *Falls as a single number.* 95% interval 4% to 23%; 13% with the two compressed asks; 5% to 8% under the
    pessimistic substantive reading.
  - Per rule group, on the readers' own labels: about two in three for P011, about 1 in 20 to 1 in 10 for line
    breaks. Report it per group.
- **(d) Placement: the detector proposed the wrong namespace, 97% not departures.**
  - *Stands in direction, weakened in size and reason:* 85% to 97% not departures.
  - About 19 of 34 because the lemma already sits in its main argument's namespace; 8 because the PR did not
    introduce the name; 6 root-named, unsettled.
  - The one fixed case of that last shape went the detector's way, and its ask was quoted in the convention text, so
    P108's blind calibration is a single item.
- **Primes:** "not readable by this method" stands. Neither 52% nor 83% should be cited.
