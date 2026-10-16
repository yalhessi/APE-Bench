# Adversarial review of the six tests: validity (2026-10-16)

Reviewer: the validity reader of the adversarial round the plan asks for (`../2026-10-16-principles-scope-currency.md`,
"Guards"). Read: the plan, `docs/questions.md`, `.claude/rules/mathlib-review.md`,
`docs/research/pipeline-overfit-2026-09.md`, `probes/library-knowledge-2026-10-13/{PROTOCOL,RESULTS}.md`,
`probes/conventions-places-2026-10-09/README.md`, `probes/conventions-ladder-2026-10-08/README.md`,
stage H in `probes/conventions-ceiling-2026-10-04/README.md`, the census (`results.md`, rubrics, both
codebooks, `crossmap.json`, reader A's labels), `docs/todo/conventions-nature.md`, and
`arm-coverage-val1000-*/events.jsonl` for the cid → PR, path, month, author join. Nothing was run
that spends; every number below that is not quoted from the record was computed from those files
with a few lines of Python and can be recomputed from the paths named. Nothing else was modified.

## Numbers computed for this review (not in the record; checkable from disk)

| what | value |
|---|---|
| Codebook A: entries with two rationale tags / one | 295 / 143 of 438; 194 of the 295 have both tags among the top five |
| Reader A vs reader B rationale on the 312 cross-mapped `same` pairs | identical sets 208 (0.67); any overlap 308 (0.99, chance 0.38); first-listed tag equal 246 (0.79), **κ 0.75** (p_e 0.15) |
| Census join: principled asks with a month and path | 1,669 of 1,833; 197 are PR-level (no path); median month 2025-11; early 804 / late 865 |
| AI-authored share of asks, early half / late half | **0.036 / 0.236** |
| Area mix, early → late | Algebra 90 → 76, Analysis 87 → 143, NumberTheory — → 58, RingTheory 63 → 87 |
| Entries with ≥ 8 principled asks (reader A primary id) | **53** (41 with ≥ 10); median 13 asks; 6 have one author ≥ 50% of asks; 9 have one top-level area ≥ 50%; 5 have ≥ 2 asks per PR on average |
| Chance that two entries of a given size are "separated by top-level area" / "co-occur (share an area and a half)" | ≥ 8 asks: **0.06 / 0.94**; 6–9: 0.19 / 0.81; 3–5: 0.54 / 0.45; 2 asks: 0.87 / 0.10; 1 ask: 0.92 / 0.04 |
| Chance two entries are strictly date-separated (all of one before all of the other) | ≥ 8: 0.00; 3–5: 0.06; 2: 0.53; 1: 0.90 |
| Entries ≥ 8 whose early/late split is binomially off the global split at p < 0.05, un-clustered | **10 of 53** (2.7 expected): P103 8→0, P119 4→18, P038 1→11 (all 12 on AI PRs), P001 8→1, P172 8→1, P089 1→9, P201 1→9, P008 13→4, P014 13→4, P060 7→1 |
| Places probe: unasked-exact pairs saying `departs` | in both samples **123**, in exactly one 86, in at least one **209** of 549; 24 at the PR place |
| …by PR | 30458 42, 42814 42, 43192 30, 29842 25 = **139 of 209 (67%)**; 41930 0 of 4 |
| …by entry | P369 27, P100 24, P041 23, P086 17, P329 15, P254 14 = 120 of 209 (57%); 24 of the 28 exact entries belong to one PR |
| …under the three `process` entries (P041 motivation, P329 incidental rewrites, P185 third-party style) at declaration places | 44 of 209 (21%) |
| Library reading's 19 `library_partial` rows, by kind | naming 7, file pattern 5, tactic 4, existing declaration 2, generator 1; `findable_from_place` yes 4 / maybe 15 |
| …whose reader note already records the same-scope pattern pointing the other way or a larger competing pattern | d0045, d0038, p0010, p0012, d0006 (5); the tactic or tag absent at base v0068, d0008, d0009 (3); external style guide d0016 (1) |
| The 41 never-reached asks, by set | D12 22, P14_val 12, P14_post 7; 25 reached by nobody; 18 PRs (33066 and 33145 five each) |
| Mathlib clone | not shallow, 31,660 commits, 2021-05-09 → 2026-05-14 |
| Zulip store | 180,162 messages, synced to 2026-07-30 |

Three things hold for every test and are said once:

- **Every reader is a Claude subagent.** The census says it: two instances of one model family are an
  upper bound on agreement, not a human figure. κ thresholds set for humans are easy here.
- **The census labels are one reader's.** Reader A's `principle_id` keys tests 2–5. A and B agree at
  0.809 ask-level through the cross-map, and A marked 20.6% `unsure`. For an entry with 8 asks, about
  1.5 of them are under another entry by B's lights. Tests 2 and 5 should use the 1,483 asks whose two
  ids are a cross-mapped pair, not all 1,833.
- **Round-1 only.** The census unit is a round-1 ask. "Unraised" anywhere in this plan means
  "not raised in round 1 at this place", and later rounds exist in the PR store.

---

## Test 1. The principles are well-defined

**Confounds and circularities.**
1. The 11 tags are the census rubric's table, and each row there already *is* a one-line operative
   statement ("the library gains …"). Two readers of the same family given statements derived from
   that table will agree with each other and with the tag the same family assigned. A pass measures
   the vocabulary's reproducibility, not whether the principles are operative. The record already
   has this number without any new reading: A and B, who never saw each other's work, agree on the
   first-listed rationale of the same principle at κ 0.75 (246 of 312 cross-mapped entries).
2. "Primary principle" is undefined in the codebook: 295 of 438 entries carry two tags with no
   order, and 194 of those have both in the top five, which overlap by design (`consistency`
   co-occurs with `discoverability` 40 times and `readability` 35). The forced single label is the
   trap `mathlib-review.md` records ("a forced-choice label vocabulary hides the mechanism").
3. The statements are written by the session that holds the picture, from the conventions each tag
   covers. Writing them *from* the tagged conventions and then asking readers to re-tag those
   conventions from the statements is a round trip.

**False pass / false fail at the thresholds.** κ ≥ 0.6: a false pass is the default outcome (0.75 is
already on disk for the raw tags). "More than 20% fit no principle or several equally": a false fail
is likely for an honest reader, since 67% of entries legitimately carry two tags; the test then fails
on the taxonomy's non-exclusivity, not on the statements.

**Fix (possible on disk, no reading needed for most of it).** Drop test 1 as a gate. If a check on the
statements is wanted: readers give a ranked pair; score the top choice against the codebook's *set*
(hit if in the set) and set agreement by Jaccard; report "several equally" as a share. Add one human
spot-check of 30 entries, since every other number is one model family. Validate the statements only
by prediction, as the plan's own guard says, which means tests 3 and 6 need a *without-statement* arm
(see test 6), or the principle layer is never tested against its absence.

**Threshold.** κ 0.6 is Landis–Koch, not the record. The record's model-reader agreements are κ 0.86–0.97
on facets and 0.94 on ask labels, 0.61 for a designer labelling their own facet. Set κ ≥ 0.75 on the
top choice (what A and B already reach) and Jaccard ≥ 0.7 on the set, or do not run it.

---

## Test 2. Instantiations are scope-dependent

**Confounds and circularities.**
1. **Incompatible pairs are chosen by readers who know where the asks fall.** The codebook was built
   from asks, each entry a preferred form; an opposite form enters only if someone asked for it. The
   record holds exactly one opposite pair (A's P014 / P133 on squeezing `simp`; B's P015/P025 and
   P392). So "fewer than 10 incompatible pairs" is nearly pre-decided, and the plan's reading of it
   ("scope does no work; a flat list suffices") does not follow: the census records asks, not forms,
   so it cannot show scope-independence. The canonical scope case on record, 30458's `variable … in`
   (0 in the file, 20 of 141 files in `Algebra/Group`, 1,129 of 6,947 library-wide; the library's
   form was asked for), is one entry whose prevalence varies by scope, not a pair.
2. **Separation is a sample-size artefact.** For two entries with ≥ 8 asks each, the chance they share
   a top-level area and a half-period is 0.94 even if their asks were placed at random; for two
   entries with 3–5 asks it is 0.45; with 2 asks, 0.10. "Asks of more than half the pairs co-occur"
   is therefore decided by the sizes of the entries the readers pair, a degree of freedom the readers
   hold after seeing the labels.
3. **Reviewer × area.** Maintainers review areas. 6 of the 53 well-populated entries have one author
   behind ≥ 50% of their asks (P014 YaelDillies 7 of 17; P047 PatrickMassot 6 of 11; P122 riccardobrasca
   7 of 8 on 2 PRs; P024 grunweg 7 of 12; P185 chrisflav 6 of 10 on 4 PRs). An entry "separated by
   area" may be one reviewer's beat. The join carries `author`; the plan does not use it.
4. **Date separation at this window is not measurable for anything with asks:** 0.00 of ≥ 8-ask pairs
   are strictly date-separated by chance, and 0.90 of 1-ask pairs are. The "separated by date" branch
   fires only for sparse entries, where it means nothing.

**False pass / false fail.** False fail through clause one (< 10 pairs) and through clause two if the
pairs are populous. False pass if the pairs are sparse. Neither outcome would say anything about scope.

**Fix (all on disk).** Replace the pair construction with a per-entry statistic against a
size-matched null: for each of the 53 entries, the concentration of its asks by top-level area and by
two-level directory against 1,000 shuffles of entry labels across asks *within the same family and
part kind*; count entries beyond the 95th percentile (2.7 expected by chance). Stratify by `ai` and
report the top author's share beside each. Keep the P014/P133 pair as the one real incompatibility and
read it by hand (A: both are `rule`; P014 has 17 asks on 7 PRs, 7 from one reviewer). Where the claim
needs a denominator (is the *rate per applicable place* area-dependent), only stage H's ten rules on
16 PRs and the detectors' four conventions have one; say so rather than infer it from counts.

**Threshold.** Nothing in the record sets 10 pairs or one half. Set: ≥ 10 of 53 entries beyond the
size-matched null → scope dependence is detectable at directory grain; ≤ 3 → not detectable; between
→ reported, no verdict. "A flat list suffices" is not a reading any version of this test licenses.

---

## Test 3. The ask is the scope's established instantiation

**Confounds and circularities.**
1. **The reader knows the asked form and chooses the feature and the scope.** "Form" is undefined
   until the reader writes a predicate; two are usually available. d0022: the token `ciSup` is
   dominant library-wide (100 names), the asked name `Dense.ciSup` drops `continuous_`, which no
   count supports. d0045: by surface projection `toLinearMap_` looks established; by elaborated
   statement the corpus says `coe` 37 to 3 (`mathlib-review.md`). A reader who wants 75% picks the
   token; one who does not picks the name. The same holds for the scope level: "first scope that
   makes it dominant" is a search over four levels and the reader stops where it works.
2. **Two differently selected samples under one threshold.** The 19 rows were selected as "the
   library points to it but a choice remains", that is, where no single artifact decides; by the
   readers' own notes at least 5 of them (d0045, d0038, p0010, p0012, d0006) have the same-scope
   pattern pointing *against* the ask or a larger competing pattern, and 3 (v0068, d0008, d0009)
   name a tactic or tag absent at base, 1 (d0016) an external style guide. At most 14 of 19 can read
   "dominant in the same scope" without redefining form or scope: 74%, already under 75%. The 21
   census draws are unselected head-heavy asks and will mostly pass. Pooling them gives a number
   that depends on the mix and means nothing for either.
3. **"Dominant" has no denominator for 9 of the 19.** A tactic ask (`positivity`, `gcongr`, `grind`)
   or an attribute is not a form with a competing form to count against; `grind` is in 4–14% of
   files across the window, so it fails any dominance test anywhere, and the plan's partition then
   files a migration under "dominant nowhere: the principle alone decided", which is the currency
   case it meant to send to test 5.
4. **The record already holds the counterexamples** to the 75% claim: 33337 (`coe_` dominant, the
   ask was `toLinearMap_`), 30458 (the asked idiom at 16% of files, 0 in the file), 32875's second
   `grind` ask (0 in the file, 137 files library-wide). Three of the project's best-read asks are
   "dominant nowhere".
5. **In-sample and one reviewer:** 22 of the 41 are D12, the dev set, where one reviewer wrote 29 of
   47 asks (`pipeline-overfit-2026-09.md`). Whatever test 3 reads on them is that reviewer's practice.

**False pass / false fail.** False pass through (1): the reader's freedom in form and scope after
seeing the ask. False fail through (2)–(3): the selected-hard rows and the tactic rows with no
denominator. The 75% threshold is not met by the 19 on the record's own notes, so running them again
is a re-measurement of `library-knowledge`, with scope as the new name.

**Fix (on disk).** Split the roles: reader 1 sees the maintainer's comment and writes, before any
count, the asked predicate, the competing predicate (the PR's form) and the unit (name token, lemma
shape, tactic, layout), as a grep the second reader can run; reader 2 runs the counts at file,
directory, area, library and the 90-day window mechanically and never sees the comment; the scope
table is read by rule: dominant = asked ≥ 2 × competing with ≥ 5 instances (the library reading's
naming rule was ≥ 3 and no competitor of similar size; `naming_norm`'s established bar is 0.80 at
≥ 20). Report the 19 and the 21 separately, the 19 with no pass/fail (they were selected to be
undecided). Draw the 21 by seed from the census and commit the list before reading, with the base
commit from the PR store (`git grep` at a 2025-06..2026-03 base works in the clone; no workspace is
needed). Report D12 beside the rest.

**Threshold.** 75% comes from nowhere in the record. For the unselected 21 keep 75% (16 of 21) as the
plan's own claim. For the 19, pre-register the expectation that same-scope dominance is ≤ 50%, since
that is what their selection means; a reading above it would be the surprise.

---

## Test 4. Silence is a decision with negative evidence

**Confounds and circularities.**
1. **The sample is not silence.** Every unasked-exact pair is, by the places probe's construction, an
   (entry, place) where *that entry was asked on this PR at another place*. So 100% of test 4's
   candidates are "the maintainer raised this convention on this PR and not here". Maintainers
   routinely flag one instance and expect the author to generalise. The taxonomy has no label for
   it; it will land in `unraised` (false fail: "silence is attention") or be stretched into `history`
   or `scope_form` (false pass). The general claim about silence needs places where the convention was
   *not* asked on the PR: the probe's 836 decoy pairs (0.28 `departs`, about 234 places) are on disk and
   the plan does not use them. They are stage F's picks, a hard negative, but they are the right
   object.
2. **The pool is a model's `departs`, not a sample of plausible application.** 209 pairs (123 in both
   samples): 67% sit on four PRs (30458, 42814, 43192, 29842), 57% under six entries, and 24 of 28
   entries belong to one PR each. "Sample 40 by principle" from this pool is a sample of four PRs'
   neighbourhoods. 44 of the 209 (21%) are the three `process` entries (P041 motivation, P329
   incidental rewrites, P185 third-party style) fired at declaration segments, where `trigger_absent`
   is an artefact of asking a PR-level convention at a hunk, not a maintainer's reasoning. Those alone
   push `unraised` down by a fifth before anyone reads.
3. **Round 1 only, and gold is a lower bound.** A departure raised in round 2, or by a second
   reviewer after the episode cut, is `unraised` here. The later rounds are in the PR store.
4. **`scope_form` and `exception` are the labels a reader who holds the picture reaches for**, and
   they are judged by the same model family that wrote the picture. `unclear` is the escape valve;
   the plan does not say how `unclear` counts against the 40% line.
5. **Mixed exact entries:** the probe's exact list per PR is reader 1's entries for *all* the PR's
   asks, so a pair can be an entry whose situation never occurs at this segment (the P048 `{D : ℤ}`
   case the probe README names). The 0.28–0.30 unasked rate already includes that.

**False pass / false fail at 40% (either reader).** Both are live: (1) pushes `unraised` up, (2) and
(4) push it down. Which wins depends on the mix of PRs in the 40 and on how the reader files
"raised elsewhere". The threshold has no anchor: stage H says maintainers raise 1 in 20 to 1 in 400 of
the places a rule's situation is flagged, so if silence were attention `unraised` would read near
95% of flagged places; if reasoning, near 0. Forty percent is between and is not derived from either.

**Fix (on disk, and the primary statistic needs no opinion).** Add a mechanical label first: diff the
place between the reviewed head and the merged commit; `fixed_in_merge` if the asked form arrives
(the author generalised a sibling ask, or a later round asked), else `kept`. That is gold-free, and
it is the one number that separates "the maintainer accepted this" from "the maintainer did not get
to it". Check the merged commits of the post-cutoff PRs are fetchable: the clone's HEAD is 2026-05-14.
Then read only the `kept` places, with labels `raised_elsewhere_on_pr`, `raised_later_round`,
`trigger_absent`, `scope_form`, `exception`, `unraised`, `unclear`, non-exclusive, notes before counts.
Sample 20 from decoy `departs` and 20 from unasked-exact `departs`, seeded, capped at 4 per PR and 3
per entry, PR-level entries excluded at declaration places; commit the list before reading. Report the
two samples separately.

**Threshold.** On the `kept` decoy sample: `unraised` ≥ 60% → silence is mostly attention; ≤ 20% →
mostly reconstructible; between → undecided, reported with `fixed_in_merge` beside it. The plan's
"If `scope_form` and `exception` dominate, scope resolution is the mechanism" needs its own line:
≥ 50% of `kept` places, by both readers.

---

## Test 5. Conventions go in and out of style

**Confounds and circularities.**
1. **Composition drift is larger than any convention drift the census can show.** Between the halves,
   the AI-authored share of asks goes 0.036 → 0.236, Analysis 87 → 143, Algebra 90 → 76, and the
   top-eight reviewer list changes. P038 (AI disclosure) reads 1 → 11 with all 12 on AI PRs: a
   "shift" that is entirely who submitted, and it carries a repository signal (the guidelines were
   added in the window), so it passes both clauses on its own. P119 4 → 18 on 4 → 14 PRs is the same
   kind of thing.
2. **"Shift" is undefined, and every definition decides the test.** Read as a count change, 10 of 53
   entries already differ at p < 0.05 un-clustered (2.7 expected under a uniform null, and the true
   null is wider, since asks cluster on PRs: P122's 8 asks sit on 2 PRs, P047's 11 on 4, P014's 17 on
   7 and 7 of them from one reviewer): the ≥ 5% line (3 of 53) is met trivially, a false pass. Read
   as the plan's words, "a form asked for early and asked against late", the census holds one such
   pair (P014/P133) and it is not date-separated: 1 of 53 < 5%, a false fail, while currency could
   still be real at the level the user means (a migration's *demand* at applicable places).
3. **"No repository signal before the first ask" is unfalsifiable.** Some repository artifact
   precedes any convention (`mk_iff` and `to_dual` long predate the window). Without a rule for which
   signal counts, the clause cannot fail.
4. **Left-censoring.** The census starts 2025-06; "the first ask in the new form" is the first *in the
   census*. The reviewer corpus outside the scored PRs (about 68k comments) holds earlier asks and is
   on disk.
5. **The chosen cut.** Splitting at the median date is one cut; with 8–13 asks per entry (4–7 a side)
   no binomial test has power, and a shift inside one half is invisible.

**False pass / false fail.** Both, set entirely by the definition of "shift" (point 2) and by
composition (point 1). The second clause cannot produce a fail.

**Fix (on disk).** Define a shift as a change in the *rate per applicable place*, which needs a
denominator: the entries with a countable trigger are stage H's ten rules, the detectors' four
conventions and the migration entries (`grind`, `to_dual`, `fun_prop`, `mk_iff`), about 14; count
applicable places on census PRs by base month with the stage-G pinpointer or a grep trigger, and the
ask rate at them. Use a PR-clustered permutation null, stratified by `ai` and area. Take the first
ask from the whole reviewer corpus, not the census. Date the repository signals explicitly: the
`@[deprecated]` stream (2,987 at the testbed's commit `L`; date that commit and check it covers
2026-03), the linter's landing commit (the record already has `terminalToGrind`: 2025-08-14 with
`grind` in 4.0% of files, 14.5% by 2026-05, `dead-ends.md`), the guideline change. The Zulip store
runs to 2026-07-30, so "only Zulip preceded" is checkable. This is the sub-hypothesis
`conventions-nature.md` already states ("test on the record first"); run that, not a count split.

**Threshold.** Replace "under 5% shift" with: ≥ 3 of the ~14 countable entries show a monotone
rate change at p < 0.05 under the clustered null → currency is a layer worth sizing; 0 → not at this
window. Replace clause two with: in ≥ half the shifts a dated repository signal precedes the first
corpus ask; the signal kinds are listed before reading.

---

## Test 6. A model can execute the reasoning, given the layers

**Confounds and circularities.**
1. **Memory.** The strong model is Opus 5.5 (cutoff June 2026): 34 of the 41 never-reached asks are
   in-window (D12 22, P14_val 12), merged before that cutoff. At a pinpointed place with the question
   "what is the established form here", the merged name or proof is the answer and may be recalled
   (the post-cutoff probe showed in-window *review* reach was not mainly memory, 0.79–1.07, but that
   was whole-PR review, not a form question at the place). The free model is not clean either: the
   ladder README records that the census merges predate DeepSeek-V4.1's release (2026-09-10), and
   reads only between-arm differences for that reason. An absolute 70% is not readable on either.
2. **No control for the principle.** The claim is that the principle statement plus search derives the
   form "without the convention sentence", but no arm runs search without the statement, and none
   runs the sentence on the same prompt for the strong model. A pass is attributed to the principle
   layer when it may be the tool access (the ladder was one turn, no tools). The ladder's two
   anchors exist for DeepSeek only: place and "a maintainer asked here" 5 of 39; the sentence 25–29
   of 39.
3. **The 30 asks are the hardest and partly non-derivable by the record's own reading.** Of the 41,
   11 are `judgement` and 4 `history` (`library-knowledge`), so at most 26 (63%) are derivable from
   the code at all; "the never-reached ones first" at a 70% bar is a false fail built in, unless
   "first" lets the session choose which 30, which is the opposite problem.
4. **The 15 non-asks are selected by test 4's readers** as `scope_form`, and they come from a pool
   where the sentence-form already said `departs` at every one. The 70% `conforms` bar is then a test
   of whether the new form flips the old verdict, which is fine, but a model that says `conforms`
   everywhere passes this half; the two halves must be read as one discrimination, not two marginals
   (the places probe's lesson: the rate is the reading).
5. **Readers who know the ask judge "derived the asked form"**; the plan says blind, and the matcher
   harness exists; use it, and show matchers the derived form only, never the verdict.

**False pass / false fail.** False pass through memory (1) and through attributing search to the
principle (2); false fail through the sample (3). At 70% on never-reached asks, the false fail is the
expected outcome.

**Fix.** Paired arms on the same asks and places, both models: (a) place and search only, no principle
and no sentence; (b) the sentence, no search (the ladder's U, re-run so the strong model has it); (c)
the principle statement with search; (d) sentence with search. Use all 26 non-judgement, non-history
asks of the 41, plus 4 seeded from the 21 census draws; report the 7 post-cutoff asks separately and
in-window beside them, as the memory split. Non-asks: 8 from test 4's `scope_form` and 7 from the
decoy `kept` set. Blind matchers on the derived form; the verdicts read as a 2 × 2 per arm. This is the
only test that spends: about 45 prompts × 4 arms × 2 models with tool access is agentic sessions, not
single calls; on the primary subscription it is the user's call, as `CLAUDE.md` says.

**Threshold.** Relative, not absolute: (c) within 2 asks of (b) on the same asks, and (c) − (a) ≥ 8 of
30, for the strong model; and (c)'s `conforms` rate on non-asks minus its `conforms` rate on asks ≥ 0.4.
The 70% absolute was set near the free model's sentence rate at the place on the 39 *average* probe
asks; it has no reading on never-reached ones.

---

## Redundant with results already in `docs/questions.md` (or computable from disk now)

- **Test 1** is answered, as far as it can be, by the codebooks: A vs B first-tag κ 0.75 on 312
  entries, computed above in a minute. Not a questions.md line, but no reading is needed to get it.
- **Test 2's "fewer than 10 incompatible pairs"** is already known: one opposite pair in A, two in B
  (`conventions-nature.md`, study 3 start). The scope join is study 2 of that todo, planned and not
  run; test 2 is that study with a weaker statistic.
- **Test 3's 19 rows** repeat the `library-knowledge` reading with scope as the name; the readers'
  notes already place ≥ 5 of 19 against same-scope dominance, and the record holds three canonical
  "dominant nowhere" asks (33337, 30458, 32875's second `grind`). Only the 21 unselected draws are new.
- **Test 4** overlaps the open adjudication (`docs/todo/adjudication-rubric.md`) and stage H's
  measurement that the places probe's own README already flags ("an unasked-exact `departs` may be a
  real departure that nobody asked about"). The reason-labelling is new; the sample is the wrong one.
- **Test 5** is the `conventions-nature.md` study-4 sub-hypothesis (demand at applicable places for
  migration entries), already specified more sharply than here.
- **Test 6** overlaps the ladder (sentence at the place 25–29 of 39; place only 5 of 39, free model),
  stage G ("verified the right convention at the right place and overrode it") and the
  verification-offer result (+0.00 to +0.03). The principle-for-sentence substitution and tool access
  at the place are new; without arms (a) and (b) they cannot be read.

## The stop rule and the order

- **The rule is inconsistent with the tests' own fail lines.** Test 3 fails under 75% but the stop
  rule fires under 50%; test 6 runs "only if 3 and 4 hold". A test 3 reading of 60% both fails test 3
  and clears the stop rule, and nothing says whether test 6 runs. That band is where a session that
  wants to continue will land.
- **It is a conjunction over two readings made by the same readers in one programme** ("tests 1, 3, 4:
  one reading programme, shared evidence vocabulary"). A reader who has coded test 4's rows as
  `scope_form` has a stake in test 3's same-scope count. Separate the readers for 3 and 4.
- **The samples are chosen by the session**: "21 drawn by principle and rank", "sample 40 by
  principle", "30 asks (the never-reached ones first)". None is a seeded draw committed before
  reading, which is what the places and ladder probes did (`blinding_SEALED.json`). Any of the three
  can move its test across its line.
- **Order can game it:** tests 2 and 5 run first and, as written, both pass by construction (test 2
  through sparse pairs, test 5 through composition), after which "scope and currency are real
  layers" frames the reading of 3 and 4. Run the mechanical statistics (fixed-in-merge for 4; the
  scope table for 3) before any opinion label, and write the sample lists for 3, 4 and 6 into the
  plan directory in the same commit as the amendments.
- **Stratification is nominal.** 11 rationale tags × 2 rank bands is 22 cells over 40 rows; the top-50
  entries hold 57% of reader A's rows. One or two rows per cell is not a stratum; report by tag and by
  rank only as marginals, and say so in the plan now rather than in the reading.

## What to amend before anything runs, in order of how much it changes the answer

1. Test 4: the sample (decoys, caps, PR-level entries out) and the gold-free `fixed_in_merge` statistic.
2. Test 6: arms (a) and (b), the memory split, the relative thresholds, all 26 derivable asks.
3. Test 3: split roles (predicate writer / counter), the two samples reported apart, "dominant" defined.
4. Test 5: the rate-per-applicable-place definition on the ~14 countable entries, the clustered null.
5. Test 2: the size-matched null per entry; retire the pair count and the "flat list suffices" reading.
6. Test 1: retire as a gate; keep the ranked-pair check only if a human reads 30.
7. One stop rule with one set of lines, seeded sample lists committed first, different readers for 3 and 4.
