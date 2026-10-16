# Adversarial review of the premise: principles, scope and currency (2026-10-16)

The plan under review: `docs/plans/2026-10-16-principles-scope-currency.md`. The brief for this review was
to attack the *picture*, not the procedure: maintainers apply a short list of invariant principles;
these are instantiated as scope-dependent conventions, reused so that one concern has one design;
instantiations drift with Zulip and automation; a maintainer's decision at a place is reconstructible
reasoning on positive and negative evidence, with taste a small residual.

Everything cited is on disk. Where a number was computed for this review it is marked *(computed
here)*; the method is stated so it can be re-run, and nothing was committed. `probes/x` means
`results/pr_review_v5/probes/x`; `research/y.md` means `docs/research/y.md`; `census/` means
`results/pr_review_v5/adjudications/conventions-census-v1/`.

**Computed here, three joins, no model calls.** (1) `census/crossmap.json` against the two codebooks'
`rationale` and `form` fields. (2) `census/reader_A/labels_b*.jsonl` joined on `cid` to
`results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/events.jsonl`, which
carries `author`, `path` and `month` for every census ask (so Tests 2 and 5 have their join, and the
author column the plan never uses). (3) The 1,833 ask bodies rebuilt with
`census/provenance/materialise_bodies.py` (spends nothing) and scanned with regular expressions for how
maintainers phrase an ask. Regex counts are provisional at the level of a sizing.

---

## 1. The strongest case, from the record, that the picture is wrong or incomplete

### 1.1 The record already says the *sentence* carries the ask, and that general rules do not

The plan's central claim is that a reviewer holding the convention sentence still misses because "it
lacked the scope and the principle, not the sentence" (plan, "Already answered?", line 2). The record
points the other way:

- **At the place, the sentence alone writes the maintainer's change for most asks.** The ladder
  (`probes/conventions-ladder-2026-10-08/README.md`, Result): told only that a maintainer asked here,
  with no convention, the model passes 5 / 6 of 39; given the sentence, 25 / 29 (judged) and 29 / 29
  (told). The sentence against no sentence gains 24 / 23 asks and loses none. The sentence *is* a
  scope-resolved instantiation (it was written from the asks), so this is the picture's three layers
  already collapsed into one line of text and working.
- **Every attempt to supply the layer above the sentence read null.** Mathlib's written guidelines
  injected: 10 against 12 of 115 and 32 against 36 (`docs/dead-ends.md`, "Community-guidelines
  injection"). A paragraph ranking the conventions over the model's judgement: routed around 85 of 177
  times, 46 held sentences ignored, 39 dropped (`probes/ask-reading-2026-10-12/readings/aggregate.md`
  §3). The same sentence offered for verification rather than asserted: +0.000
  (`probes/conventions-ceiling-2026-10-04`, stage G). The assessment's own reading is that "the
  assertion, not the content, carries guideline gains" (`research/conventions-assessment-2026-10-12.md`
  §5.4). The principle layer the plan proposes is more content, delivered in the form that has not
  moved any model.
- **What the reviewer lacked at its misses was mostly nothing.** Of the 66 asks the free reviewer
  missed, the readers coded the knowledge it needed as `none` for 34, `demand` 14, a mechanism 6, a
  direction 6, an API fact 2 (`aggregate.md` §2). In 63 of 67 residual asks every reviewer that missed
  had read, searched or compiled the object (`docs/questions.md`, "Where does a reviewer miss"). 1 of
  558 session-rows was at a place the reviewer had not read. The miss is a decision at a read place,
  with the facts in hand.

### 1.2 The reviewer already reasons from scope, and reaches the opposite conclusion

The plan says a maintainer's decision is "reconstructible reasoning on positive and negative evidence"
and Test 6 asks whether a model "derives the scope's established form". The record shows the model
doing exactly that and being wrong:

- Of 105 hand-coded rows where the free reviewer named the maintainer's concern and dropped it, the
  grounds were worth 27, a corpus plurality or tool count 22, the file's siblings 13, a check not run
  or run on its own wrong candidate 26, nothing stated 13, a guess about maintainers 6
  (`docs/questions.md`, "On what grounds does the free reviewer drop a concern"). Siblings plus
  plurality are 35 of 105: scope reasoning, done, pointing the other way from the maintainer.
- The verbatim rows (`aggregate.md` §4, §5): d0045 "`coe_` 48 of 124 … is right per the corpus" (the
  maintainer wanted `toLinearMap_`, 21); d0038 "`_of_isNormal` suffix seems reasonable (cf.
  `add_le_iff_of_isSuccLimit`)" (the maintainer wanted the file's namespace form); p0010 "the file's
  local convention … uses `_left`/`_right` to denote argument position … Fine" (the maintainer wanted
  the library's orientation); v0060 "the sections themselves were read as the file's convention" (the
  maintainer wanted the library idiom).
- **The direction of resolution is not consistent across asks.** *(computed here, by reading the four
  readers' `artifact` and `note` fields in `probes/library-knowledge-2026-10-13/readings/*.jsonl` for
  which scope's dominant form the maintainer asked for; single reader, provisional.)* Of the 41 asks no
  free-reviewer session reached: the asked form is the dominant form in the file or directory for 7
  (v0067, p0003, d0002, d0016, d0029, d0038, d0039), plus d0006 mixed; dominant only library-wide for
  8 (d0043, p0005, v0092, v0093, and the `ciSup` token behind d0022/23/25/27, which fixes the token
  and not the name); **the PR's form is the local precedent for 9** (v0060, v0061, v0064, d0003, d0004,
  p0010, p0012, d0018, d0045); no scope has a dominant asked form for 14 (v0068 and d0008/d0009, where
  the needed `@[gcongr]` / `@[grind]` tag did not exist at base and the ask adds it; v0091, p0004,
  v0105, d0035, d0036, d0049, d0051; and the history asks v0053, v0056, d0007, p0000); mixed 2 (p0006,
  v0090). The file beats the library in d0038 (namespace, 440 against 793 library-wide), d0029 and
  d0016; the library beats the file in v0060 (an idiom in 1,129 of 6,947 files, 0 in the file, 1 of 13 in
  the directory), p0010 and p0012; a minority or two-day-old form beats the plurality in d0045 (21
  against 48, no deprecation) and d0018 (`to_fun`, 7 uses in the library, the same file hand-writes the
  pairs). No rule of the form "narrowest wins", "widest wins" or "newest wins" fits more than about half.
  What fits all of them is: the maintainer chose the form, and scope is cited where it agrees.

### 1.3 "Taste is a small residual" is contradicted at the hardest asks and in the maintainers' own words

- **The readers' codes.** On the 41 never-reached asks, four readers under a pre-registered protocol
  coded 11 `judgement` ("the maintainer's preference or design call"), 4 `history`, 19
  `library_partial` ("a choice remains"), 7 `library` (5 on re-check)
  (`probes/library-knowledge-2026-10-13/RESULTS.md`). By the readers' own words the maintainer's
  preference decides 15 of 41 outright and the residual choice in 19 more. The plan's Test 3 would
  re-code "dominant nowhere" as "the principle alone decided: a design decision". That relabels the
  readers' `judgement` as reasoning without any measurement that distinguishes the two.
- **The maintainers mark their own asks as preferences.** In the texts behind the 41: "consider my
  suggestion optional" (v0064); "would be even nicer" (d0004); "Can `positivity` do this (untested)?"
  (v0067); "How about `round_eq_div`?" (d0048); "I suggest turning the declarations … around" (d0029);
  "maybe you can provide a `HasProd` version" (p0003); "or … or" (d0036); and on p0016 the maintainer
  concedes "there is an hesitation in mathlib" (`probes/filing-contract-2026-10-12/partial_reading.md`;
  `research/ceiling-residual-2026-10.md` §3).
- **At census scale.** *(computed here, regex over the 1,833 rebuilt bodies with code blocks
  stripped.)* 80% of asks state no ground of any kind (no reason word, no consistency reference, no
  external source, no currency word); 58% are 12 words or fewer (mean 16.8); 45% are a bare
  ` ```suggestion ` block; 33% are phrased as a question; 28% carry hedging language ("optional", "nit",
  "I think", "maybe", "nicer", "minor", "I prefer"); 24% are hedged with no reference to any norm. A
  consistency reference ("as elsewhere", "convention", "in Mathlib we") appears in 5%; an external
  source (a docs link, a PR number, Zulip, a library note) in 4% (76 asks); a currency word in 5%.
  Asks under `standard` entries are hedged more than under `rule` entries (36% against 23%) and asked
  as questions more (40% against 27%). Across the whole mathlib4 history, 709 of 104,093 reviewer
  comments (0.68%) link a norm source (`research/code-review-systems-survey-2026-09.md`:113).
  Maintainers almost never say *why*. The picture may still be right that the why is tacit; but the
  claim that the decision is "reconstructible" has no support from what maintainers write, and the
  principles in Test 1 will be the project's statements, not Mathlib's.

### 1.4 "One concern has one design, reused" is contradicted by the census and the library

- The census is not saturated: 409 and 407 principles over 1,833 asks, one new principle per ten asks
  still arriving (Good-Turing 0.099 / 0.107), 166 singletons, 370 entries in the tail (`census/results.md`
  §1-2). A library that enforced one design per concern would have a saturating list.
- Two maintainers hold opposite rules on one situation and the census keeps both: A's P014 (do not
  squeeze a `simp` before a flexible finisher, 19 asks) against P133 (squeeze it, 7 asks)
  (`census/results.md` §5). *(computed here, primary labels only: 17 and 7 asks)*: P014's asks are
  YaelDillies 7 and riccardobrasca 4, in NumberTheory 6 and Analysis 4; P133's are chrisflav 3 and
  vlad902 2, in AlgebraicGeometry 3; both
  were raised in 2025-06, 2025-08 and 2025-12. Two designs coexist in one period, and they separate by
  reviewer at least as cleanly as by area.
- The library carries two forms at scale with no deprecation between them: `coe_` 48 against
  `toLinearMap_` 21 for one coercion (d0045); root `isFoo_of_bar` 793 against namespace `Foo.of_bar` 440
  (d0038); two `calc` layouts at 130 against 481 lines (d0016's reading); `mk_iff` on 52 structures against the
  common `def` plus `_def : … ↔ … := Iff.rfl` (p0006); `homMk` in ~25 files against `mkHom` ~7 with the
  maintainer's own "hesitation" (p0016). The maintainers tolerate two designs; they ask for one at a
  place.

### 1.5 The decision is not taken "at a place"

- 17% of census asks (286 of 1,669) repeat a (PR, principle) pair already counted *(computed here)*; on
  the dev set one rename is counted four times (`docs/questions.md`, "Is the dev ask set easier"). The
  census's P100 (20 asks) is the propagation rule itself: "a variant or improvement introduced for one
  member of a family of siblings … is also provided for the other members". The maintainer comments once
  and expects the author to propagate. Silence at the sibling place is neither a decision nor
  inattention; it is economy. Test 4's category list has no code for it.
- Maintainers raise a settled convention at 1 in 20 to 1 in 400 of the places its situation is flagged;
  on 16 census PRs 6 of 205 flagged places (2.9%) sat at an ask (`probes/conventions-ceiling-2026-10-04`,
  Result 6). Demand at a place is a 5% event. If every one of those silences were a reasoned negative
  decision, maintainers would be making about twenty reasoned negative decisions per positive one; the
  places test's "many of the unasked departures may be real" and the per-place engine's 7% precision at
  0.70 asked-recall say the simpler reading is that most applicable places are not decided at all.

### 1.6 What moved the wall was the model and the harness, not a layer of knowledge

Opus over DeepSeek with identical information: +0.19 / +0.22 on the two sets, interval excluding 0; the
Claude Code harness over the project harness, same model and prompt: +0.10 and +4 obligations
(`docs/questions.md`, "Model and harness"). Every ask-free knowledge delivery off its development PRs:
+0.03, +0.000, +0.13 / 0.00 / −0.01, +0.02 to +0.09 with intervals spanning 0. Every reviewer measured
hits 0.09-0.11 asks per finding regardless of what it knows; recall follows volume
(`docs/questions.md`, "Does any reviewer aim better"). The record's own adversarial round concluded
"the levers that moved the wall were the model and the harness" (`research/filing-decision-design-2026-10-12.md`
§9, record row 20). A picture in which maintainers' decisions are reconstructible from layers the model
lacks predicts that supplying the layers moves recall; the one layer that has been supplied in every
form (the convention) moves recall only when pinned to the ask.

### 1.7 Reviewer concentration: taste is a sizeable fraction of gold on every set the tests will use

- Dev: one reviewer wrote 29 of 47 asks (2.5 effective authors against 9.3)
  (`research/pipeline-overfit-2026-09.md`). P14 *(computed here from the probes' `feedback.json`)*: 46
  asks by 12 reviewers, the top three (grunweg 8, ocfnash 7, themathqueen 5) writing 43%. The 41
  never-reached asks come from these sets.
- Census *(computed here)*: 74 reviewers; the top 10 wrote 50.5% of principled asks (j-loreaux 135,
  YaelDillies 101, erdOne 100). Of the 398 principles used, 198 were raised by exactly one reviewer (166
  of them singletons); of the 153 with three or more asks, 42 have one reviewer at 50% or more of their
  asks and 5 are single-reviewer. The head is multi-reviewer (P005: 27 reviewers; the 53 entries with
  eight or more asks have no single-reviewer entry and 6 with one reviewer at 50% or more), so taste
  does not explain the head; it is a candidate for the tail, which is where the exact-convention gain
  sits (past rank 100, `research/conventions-dossiers-review-2026-10.md` §2.2).

---

## 2. Alternative pictures that fit the same evidence, and which tests do not separate them

A test is non-discriminating if it passes under the plan's picture and under the alternative. The
plan's six tests are numbered as in the plan.

### Alternative A. The sentence is the whole instantiation; the layers above it do no work

The census entry was written from the maintainer's ask, so it already encodes the scope-resolved form
("in a conditionally complete lattice the indexed supremum is `ciSup`"). Principle, scope and currency
are the derivation of the sentence, not an addition to it, and a model holding the sentence has
everything the layers would give. Fits: the ladder (sentence 64-74%, no sentence 13%); the exact brief
(+0.26 Claude, +0.42 DeepSeek); every general-form delivery null; 34 of 66 misses lacking nothing.

- **Non-discriminating: Tests 1, 2, 3, 5.** Tags can be written and agreed (1), incompatible pairs exist
  in the codebook (2), the asked form is dominant at some scope (3), and some entries shift (5) whether or
  not the layers add anything a model can use. All four pass under A.
- **Discriminating: Test 6**, if and only if it carries a same-model reference arm with the sentence
  given (the ladder's U and A arms exist for DeepSeek; nothing exists for the strong model). Without it,
  a strong model reaching 70% says nothing about whether the principle statement did the work (see E).

### Alternative B. The decision is demand at 5%, volume-calibrated, not reconstructible from the code

Maintainers raise a convention at 1 in 20 to 1 in 400 of the places it applies; which place gets the
one ask is attention, PR size, the reviewer's time, whether the author is new, and whether it was
already said once on this PR. Every reviewer's hit rate per finding is the same 0.09-0.11; the exact
brief's gain is (share of asks whose entry was asserted) × (0.5 − solo's reach). The layers predict
*applicability*; they do not predict *demand*, which is what gold records. Fits: stage H; the places
test (0.70 at asked places, 0.30 elsewhere, 7% precision); the per-place engine (3× reach at 25×
filings); the filing contract (14 of 37 at 4.9 control findings a PR); 17% repeated pairs.

- **Non-discriminating: Tests 1, 2, 3, 5, 6.** All five are about applicability or form. Test 6 puts one
  prompt at the ask's own place, which removes the demand question by construction (the ladder already
  did this and passed at 64-74% with the sentence); its 15 non-asks are pre-selected as `scope_form`
  cases from Test 4, the explicable ones.
- **Partly discriminating: Test 4**, but as written it will pass under B. It reads the model's own
  one-turn `departs` verdicts at unasked places, where the model says `departs` at 0.30 of pairs whether
  the convention is the PR's own or a decoy (0.28). `trigger_absent` will therefore absorb the model's
  false departures and read as "reconstructible negative evidence". A `covered_by_another_ask` category
  is missing (P048's four `{D : ℤ}` signatures, one comment). For Test 4 to discriminate it needs the
  decoy departs rate as its baseline for `trigger_absent`, the sibling category, and `unraised` read
  against the 5% demand prior, not against 40%.

### Alternative C. Instantiations are per-reviewer; area separation is reviewer separation

Maintainers specialise by area and enforce their own forms there. What looks like a scope-dependent
convention is the trace of one or two reviewers' enforcement in the files they curate. Fits: P014
against P133 by reviewer; the dev set; reviewer specialisation *(computed here)*: among the 26 reviewers
with 20 or more census asks the median top-area share is 0.43, with EtienneC30 0.92 (MeasureTheory),
MichaelStollBayreuth 0.89 (Analysis), PatrickMassot 0.86 (Topology), joelriou 0.77 (CategoryTheory).

- *(computed here)* Of the 53 head entries (eight or more asks), 18 have a top-area share above the 95th
  percentile of a permutation baseline (2.7 expected by chance). Of those 18, four are PR-level process
  conventions whose "area" is `(PR-level)` by construction (P043, P100, P041, P038); nine have the top
  area carried by one to three reviewers with the leading one at 0.50-1.00 of its asks there (P057
  PatrickMassot 0.64 of 2 reviewers; P013 themathqueen 0.71; P014 riccardobrasca 0.67; P047 PatrickMassot
  0.86; P185 chrisflav 0.80; P001 0.60; P069 0.50; P122 riccardobrasca 1.00; P060 EtienneC30 1.00). Five
  remain with four or more reviewers in the top area and none above half (P005, P019, P003, P070, P108),
  and for the two largest the concentration is weak (Analysis at 0.25-0.28 against a 0.17 base). So the
  area signal that survives a reviewer control is about 5 of 53 head conventions.
- **Non-discriminating: Test 2** (it separates by area and date and never by author; area and author
  are collinear); **Test 3** (the dominant form in a curated area is the curating reviewer's past asks,
  compiled; dominance is the trace of enforcement, so finding it does not say a principle produced it);
  **Test 5** (a reviewer arriving or leaving reads as a shift in the asked form); **Tests 1 and 6**
  (a model deriving "the area's form" derives the reviewer's enforced form; passes under both).
- **Discriminating: Test 2 with author as a third separating variable** (events.jsonl carries it): a pair
  whose sides separate by author within one area and period is C; a pair whose sides each have three or
  more authors and separate by area is the plan's picture.

### Alternative D. The principles are post-hoc labels that same-family readers produce consistently

Two Claude readers wrote the rationales from merged PRs; a third matched the sentences. Consistency
between them is consistency of rationalisation, which `census/results.md` itself names as the bound
("one model family read both sides … an upper bound on what two independent humans would show").
Fits: 0.68% norm citation; 80% of asks with no stated ground; and *(computed here)* on the 312 `same`
pairs of the cross-map the readers' primary rationale tag already agrees at 0.79 (κ 0.75), any shared
tag 0.99, identical tag sets 0.67, form κ 0.81. The disagreements are the top five tags confused with
each other (discoverability↔readability 9, consistency↔discoverability 7, compactness↔readability 5),
and those five cover 80% of tag uses.

- **Non-discriminating: Test 1.** Its bar (κ 0.6) is already met by the bare tag names before any
  statement is written; passing it says the labels are stable, not that maintainers reason from them
  or that they predict anything. Its "what each yields to when two conflict" clause is the only part
  that would make a principle operative, and no test reads a conflict against it. (Also a construction
  problem: 295 of 438 entries carry two tags, so "fits several equally" above 20% is the codebook's own
  state.)
- **Non-discriminating: Test 3** ("dominant nowhere → the principle alone decided" assigns the residual
  to the principle with no independent reading; under D the same cases are the maintainer's preference,
  labelled afterwards); **Tests 2, 4, 5** (none reads a principle).
- **Partly discriminating: Test 6**, only with an ablation arm "search over the scope, no principle
  statement". Without it, a model that derives the form from the code alone passes while the principle
  did nothing, and the plan reads the pass as the principle layer working.

### Alternative E. The gap is model capability and harness; the layers are orthogonal to it

Fits: Opus +0.22 over DeepSeek with identical packets; harness +0.10; Qwen3.5 at the floor under every
prompt (`docs/dead-ends.md`); the misses at a read place with the facts in hand; the record's row 20.

- **Non-discriminating: Tests 1-5** (none involves a reviewer). **Test 6** runs the free model and one
  strong model and reports the free one "beside" the strong one. It will show a model gap. If the strong
  model passes 70% the plan reads the picture as holding; under E the strong model passes because it is
  strong, as it already reaches 0.47-0.62 unbriefed with the same tool access to the same base
  workspace. Only a same-model contrast against a sentence-given arm (and a no-principle arm, as in D)
  turns Test 6 into a test of the layers rather than of the model.

### Summary table

| alternative | passes under both (non-discriminating) | would discriminate |
|---|---|---|
| A sentence is everything | 1, 2, 3, 5 | 6 with a same-model sentence-given reference |
| B demand at 5%, volume | 1, 2, 3, 5, 6 | 4 with a decoy baseline, a sibling-coverage category, and `unraised` read against 5% |
| C reviewer taste by area | 1, 2, 3, 5, 6 | 2 with author as a separating variable |
| D post-hoc labels | 1, 2, 3, 4, 5 | 6 with a no-principle ablation arm |
| E model and harness | 1, 2, 3, 4, 5 | 6 with same-model contrasts; otherwise none |

No test in the plan as written separates the picture from all five; Tests 1, 2, 3 and 5 pass under
every alternative.

---

## 3. What would show the picture false that none of the six can catch, and tests on data already on disk

### 3.1 The maintainers' own stated grounds

None of the six reads what maintainers *say* when they do give a reason. The picture predicts that when
a ground is stated it names a scope's form ("as elsewhere in this file", "Mathlib does this"), a
currency fact ("now that `grind` …", "deprecated") or a principle ("so that it is discoverable"); the
taste alternative predicts preference and bare authority ("I prefer", "nicer", "I don't think we want").

- **Test.** The roughly 370 census asks with any stated ground *(computed here: 182 with a reason word,
  99 with a consistency reference, 76 with an external source, 87 with a currency word, overlapping)*,
  two readers blind to the codebook tags, each ask coded as: `principle` (an invariant is named),
  `scope_form` (a form at a named scope), `currency` (a newer or deprecated form, automation), `authority`
  (a Zulip decision, a maintainer's ruling, a named person), `preference` (worth, aesthetics, "I"),
  `fact` (a correctness or compile fact), `other`. Separately, for the 76 external references, whether the
  source is a form, a principle, or a decision. Falsifier: `preference` plus `authority` at or above a
  third of stated grounds, or `principle` under a tenth.
- **Data.** `census/provenance/materialise_bodies.py <out>` (ran here in under a minute, 3,622 rows,
  none missing); `census/reader_A/labels_b*.jsonl`; events.jsonl for author and path. Cost: three
  reader batches, about 600k subagent tokens; the regex sizing above costs nothing and is already
  computed.
- **Also read.** Hedge rate by entry: the picture predicts hedging where two forms coexist in the scope;
  compare the 28% hedge rate between entries that are area-concentrated (§2 C) and those spread over
  areas.

### 3.2 Author as the separating variable, before area

Test 2 cannot see Alternative C. The test above (§2 C) is a join already made: for each incompatible
pair, the author, area and month distributions of each side. Falsifier for the picture: more than half
of the pairs separate by author with overlapping areas and periods. The P014/P133 pair already does.

### 3.3 Scope resolution has no consistent direction

Test 3 records "which scope first makes the asked form dominant", reading from narrow to wide. It will
file v0060, p0010 and p0012 under "dominant only wider: a scope-resolution rule is needed, and its
level" and d0038 and d0029 under "dominant in the same scope", and read both as the picture holding.
The falsifier is that no single rule fits: record the dominant form at *every* level (file, directory,
area, library, last-90-days) for every ask and count the asks where the levels disagree and the
maintainer's choice does not follow one fixed level. *(computed here from the readers' notes, §1.2)*: 9
of 41 against the local precedent, 7-8 with it, 8 library-only, 14 nowhere, 2 mixed; file wins in some,
library in others, a two-day-old generator in one. If a re-count with `git grep` at the base commit
confirms that no level wins in 75% of the decided cases, "scope-dependent instantiation" is a
description of where the maintainer found support, not a mechanism. The same data also exposes Test 3's
circularity: dominance at the base commit is produced by the same maintainers' earlier enforcement, so
a maintainer asking for the dominant form is asking for consistency with their own past asks, which is
the picture's claim restated rather than tested; the informative cases are the 9 where they asked
against it.

### 3.4 Silence is coverage, not decision

Test 4 cannot see the propagation reading because it has no category for it. On disk:
`probes/conventions-places-2026-10-09/items.json` and `outputs.jsonl` hold the 549 unasked (convention,
place) pairs where the convention *was* raised on that PR. For each, whether the place is in the same
file as an asked place for the same entry, and whether the maintainer's one comment names siblings
("and the next three lemmas", "same here", "following the above suggestion": d0008, v0091, v0061 do).
Falsifier for "silence is a decision with negative evidence": a majority of the model's `departs` at
unasked-exact pairs sit in the same file as an asked pair under the same entry. Deterministic, no model
calls.

### 3.5 The principle without the sentence, on the same model, with the sentence as the reference

Test 6 is the only test whose outcome is not already fixed by the record, and it is confounded three
ways (A, D, E). The fix is on disk: for the free model, the ladder's F (no convention, 5 / 6), U and A
(sentence, 25-29 / 29) arms exist for 39 of the asks. Add two arms on the same 39 for the same model:
`P` (principle statement, place, no sentence, no tools) and `PS` (principle statement with tool access
to the base workspace). The picture is supported if PS lands near A and above P; Alternative A if PS
lands near F; Alternative D if PS equals a `S`-only arm (tools, no principle statement). Thresholds can
be set from the ladder's own spread: F to A is 24 asks, so a layer that recovers fewer than 8 of those
24 without the sentence is not carrying a third of what the sentence carries. $0 on the local tier;
matchers about 130k tokens as the ladder cost.

### 3.6 A gold-free read of the unasked 95%

Whether an unasked departure would have been welcome is the adjudication the record has not done
(`docs/todo/adjudication-rubric.md`). The one gold-free signal is revealed preference: did the author
or a later PR conform at the unasked `departs` places? The dossiers round split on it (R1 keep, R3
reject: it follows migrations; `research/conventions-dossiers-review-2026-10.md` §3). None of the six
touches it, and the stop rule reads `unraised` as if silence could be scored. It cannot, without this.

---

## 4. Verdict

**Supported by the record as it stands.**

- The census holds the knowledge behind what maintainers ask: 39 of 46 and 40 of 47 asks in census;
  the sentence at the place writes the change for 64-74% of in-census asks; 5 of the 6 asks nothing
  reaches are in census (`probes/conventions-ceiling-2026-10-04`; the ladder; `research/ceiling-residual-2026-10.md`).
- Currency exists, for a handful of named migrations: `grind` in 4.0% of files at 2025-08, 8.4% at
  2025-12, 14.5% at 2026-05, with review enforcement 9.1 → 22.4 mentions per thousand Aug → Dec;
  `by_cases!` 0 asks Jun-Aug and 12 in December; `to_fun` two days old at d0018's base; `toLinearMap_` at
  17% called "emerging" (`docs/dead-ends.md`, "Linter-as-convention-oracle"; `research/pr-review-v5-principled-design.md` D2).
  Its size as a share of asks is not measured; the migration entries that no ask-free reviewer reaches
  are about 4-6 of 93.
- Scope exists in some form: 18 of 53 head conventions are area-concentrated beyond chance, 5 of them
  after a reviewer control *(computed here)*; the 30458 `variable … in` case is a library idiom beating
  the file's (`docs/todo/conventions-nature.md`); 19 of 41 hard asks have the library pointing at the
  form.
- The miss is at a read place, not an unvisited one: 1 of 558 rows unattended; 63 of 67 residual asks
  had the object read, searched or compiled.

**Contradicted, or against the record as it stands.**

- "The reviewer lacked the scope and the principle, not the sentence": the sentence is what carries the
  ask (+24 / +23 over no sentence at the place), and every delivery of the layer above it in general
  form has read null (guidelines, precedence paragraph, verification form).
- "Taste is a small residual": readers coded 15 of the 41 hardest asks as preference or history and 19
  more as a choice among the library's options; maintainers hedge 28% of asks, ask 33% as questions,
  state no ground in 80%, and cite a norm in 0.68% of all review comments; two opposite rules on one
  situation coexist in the census.
- "One concern has one design, reused": the census is unsaturated with a 370-entry tail and 166
  singletons; the library carries 48 against 21, 793 against 440, 130 against 481 with no deprecation;
  "there is an hesitation in mathlib" is a maintainer's description of it.
- "A decision at a place": 17% of census asks repeat a (PR, principle) pair; P100 is the propagation rule;
  demand is 1 in 20 to 1 in 400 of applicable places.
- "Reconstructible from positive and negative evidence" in the sense that a model can do it: the model
  reconstructed from siblings and plurality in 35 of 105 drops and reached the opposite verdict; in 9
  of 41 hard asks the local precedent was the PR's form; the resolution direction is inconsistent.
- The implied prediction that supplying the layers moves recall: what moved it was the model (+0.22)
  and the harness (+0.10); knowledge deliveries off their development PRs: +0.03, +0.000, 0.00, −0.01.

**Untested, and the tests that would reach it.**

- Whether a principle statement lets a model derive the form *without* the sentence (Test 6 with the
  same-model sentence and no-principle reference arms, §3.5). This is the one genuinely new cell.
- Whether silence is reconstructible negative evidence (Test 4 with a decoy baseline, a sibling-coverage
  category, and the 5% prior, §3.4); whether unasked departures are welcome (§3.6, not reachable by any of
  the six).
- Whether scope separation survives a reviewer control (Test 2 with author, §3.2), and whether any
  resolution level wins (§3.3).
- What maintainers' stated grounds are, when they state one (§3.1): the direct measurement of
  "principle, scope-form, currency, or preference" from the source, which no test in the plan reads.
- The size of the currency layer, and whether repository signals precede asks or are their consequence
  (Test 5's "adoption in recent code" is downstream of complied-with asks, so it cannot be read as a
  precursor without a lag analysis).

**Two notes on the plan's own "Already answered?" section.** The tests are studies 2-4 of
`docs/todo/conventions-nature.md` (scope, conflict, maturity), which the plan does not cite and which
already names the author join and the P014/P133 pair as the starting points. And the plan's picture
does not stratify by AI-generated PRs, where PR-level asks are 16% against 5-6% elsewhere
(`research/pipeline-overfit-2026-09-replication.md`) and the asks ("close the PR", disclosure) are not
decisions at a place at all; the project's stated target is those PRs.

**Where the picture is most likely to hold, on this evidence.** The head: multi-reviewer, multi-area
conventions (P005, P019, P011, P018, P004) with a sentence that already carries them, where the
instantiation is global and no scope layer is needed. Where it is least likely to hold: the tail past
rank 100, where the exact-convention gain lives, 42 of the 153 entries with three or more asks are
half one reviewer's, and the readers' codes say preference. The plan's stratification by rank is the right instrument; its
thresholds should be read expecting the split to fall there, and a pass in the head should not be
reported as the picture holding.
