# Principles, scope and currency: where the idea holds and where it fails (plan, 2026-10-16)

Status: pre-registered; adversarial round done (amendment 1). **Queue, set by the user 2026-10-16, both run in parallel so neither is dropped:** (1) R1, the maintainers' stated grounds (`results/pr_review_v5/probes/stated-grounds-2026-10-16/`); (2) the 5% re-examined at its source, stage H's 205 flagged places through survival-at-merge and a calibrated reading (`results/pr_review_v5/probes/stage-h-departures-2026-10-16/`). Earlier: nothing run. Written in this session from the user's
picture (2026-10-14, 10-16); the tests run in a fresh session once the round is read.

## Already answered?

Checked against `docs/questions.md` (2026-10-16):
- "Given the exact conventions behind a PR's asks, how far does each model move?": the convention
  *sentence* lifts every strong model; the ceiling is 40 of 46 asks in union. So the sentences carry
  most of what is needed, and this plan is about why a reviewer holding one still misses.
- "What does the reviewer do with a convention sentence it was given?": considered and dropped 39,
  ignored 46 of 177. The plan's claim is that it lacked the scope and the principle, not the sentence.
- "Picked without the asks, do the conventions move the reviewer?": +0.13 on the held-out, 0.00
  post-cutoff, −0.01 dev. A flat list, selected by the diff, is the baseline this plan must beat later.
- "At the ask's own place, one turn, does the model write the maintainer's change?": 25-29 of 39 with
  the sentence. Test 6 reuses that form with the sentence hidden.
- "For the asks no free-reviewer session reaches, does something in Mathlib at the base decide the
  fix?": 7 of 41 decided, 19 "the library points to it but a choice remains". Test 3 re-reads those 19
  with scope: the plan predicts the scope's established form decides most of them.
- "Asked at every changed place, does a convention's question pick out the places maintainers asked
  about?": 549 unasked pairs, "departs" at 28-30% of them. Test 4 reads those.
- "Where, by census rank, does an exact-convention delivery gain?": past rank 100; the head asks are
  stable misses. Stratify every test by rank as well as by principle.
- `docs/dead-ends.md`: "Convention detectors closed as a recall lever" (the tail), "Knowledge taken
  from the library as the decider of the fix" (7 of 41), "Linter-as-convention-oracle". None tested
  scope or the principle layer; the norm store with maturity (`research/pr-review-v5-principled-design.md`
  §D2) is the currency layer, designed and never built.

## The picture under test (the user's, condensed)

Maintainers apply a short list of rules that hold across the whole codebase (maintainability,
correctness, clarity, generality, one encompassing design per concern). Applying them means design
decisions, and these are instantiated differently in different scopes and contexts; the conventions
exist so that a decision made once is reused and two designs for one thing are not introduced. Some
instantiations are arbitrary or historical. The instantiations go in and out of style with Zulip,
automation and metaprogramming. A maintainer's decision at a place is reasoning on reconstructible
evidence, positive and negative; arbitrary taste is a small residual.

On disk already: the codebook's 438 conventions each carry one or two of 11 rationale tags
(readability 148, consistency 147, maintainability 111, discoverability 103, compactness 76,
automation 51, process 29, generality 27, correctness 19, performance 13, mathematics 9; the top five
cover 80% of uses). The tags are names, not statements. No entry carries a scope.

## Claims, tests, thresholds, and what each failure changes

Every test is stratified by principle (rationale tag) and by census rank (head: top 50; tail: the
rest), so a partial failure says *where* the idea holds. Thresholds are fixed here; a change to one is
an amendment, dated, written before the reading it affects.

### Test 1. The principles are well-defined

- **Claim.** The 11 tags can be written as operative statements (what each protects, what it forbids,
  what it yields to when two conflict) that readers apply consistently.
- **Method.** Write the statements from the tags, Mathlib's own style and naming documents and the
  conventions each tag covers. Two readers, independent, assign a primary principle to a random 100
  conventions from the statements alone (codebook tags hidden). Record agreement with each other and
  with the codebook's tag.
- **Data.** `results/pr_review_v5/adjudications/conventions-census-v1/reader_A/codebook.json`;
  Mathlib `docs/` at a recent snapshot.
- **Fails if.** Reader-reader agreement under κ 0.6, or more than 20% of conventions fit no principle
  or several equally.
- **Then.** Revise the statements or the set before any test that depends on them; if no revision
  reaches the bar, the principle layer is not a usable artifact and tests 3, 4, 6 run on conventions
  alone.

### Test 2. Instantiations are scope-dependent

- **Claim.** One principle is instantiated in incompatible forms in different areas of the library,
  and the asks respect the area.
- **Method.** From the codebook, list pairs of conventions that instantiate the same principle in
  incompatible forms (by hand, two readers; expect a few dozen pairs). Join every census ask to its
  convention, its file path (top-level Mathlib area and the directory below it) and its date. For each
  pair: are its asks separated by area, by date, or neither (co-occurring in one area and period)?
- **Data.** The census labels (cid → principle id) joined to the round-1 comment rows (cid → PR, path,
  date) of the 1,000-PR validation set; the codebook.
- **Fails if.** Fewer than 10 incompatible pairs exist (scope does no work; a flat list suffices), or
  the asks of more than half the pairs co-occur within one area and period (two designs coexist and
  maintainers accept both).
- **Then.** The co-occurring share is the historical residual, measured. Separation by date and not
  area moves the pair to the currency layer (test 5). Separation below the directory level says scope
  must be resolved finer than a directory (namespace or file).

### Test 3. The ask is the scope's established instantiation

- **Claim.** At the base commit, the form the maintainer asked for is the dominant form in the ask's
  own scope; where it is not, it is dominant in a wider scope or in newer code, and only rarely nowhere.
- **Method.** 40 asks: the 19 the library reading coded "points to, a choice remains", plus 21 drawn
  by principle and rank from the census. For each, at the base commit, count the asked form against
  the PR's form in the same directory, the wider area, and the library (git grep, commands recorded),
  and in code changed in the last 90 days before the base. Record which scope first makes the asked
  form dominant, or none.
- **Data.** `probes/library-knowledge-2026-10-13/readings/*.jsonl`; the census; the Mathlib history.
- **Fails if.** The asked form is dominant in the same scope for under 75% of asks.
- **Then.** The partition says what to change: dominant only wider (a scope-resolution rule is
  needed, and its level); dominant only in recent code (currency decides, test 5); dominant nowhere
  (the principle alone decided: a design decision; its share is how often the reviewer must reason
  from the principle with no precedent).

### Test 4. Silence is a decision with negative evidence

- **Claim.** Where a convention plausibly applied and the maintainer raised nothing, the reason is
  reconstructible: the trigger did not hold, the PR already follows the scope's form, a stated
  exception applies, or the answer is in the PR's history; and "a real departure nobody raised" is a
  small residual.
- **Method.** From the per-place probe's 549 unasked (convention, place) pairs, take those the model
  called "departs" (about 150); sample 40 by principle. Two readers, independent, each assign one of:
  `trigger_absent`, `scope_form` (the PR's form is the scope's established one), `exception` (stated
  in the convention, a library note or the file), `history` (needs the discussion), `unraised` (a
  real departure the maintainer did not raise), `unclear`; with the evidence and commands.
- **Data.** `probes/conventions-places-2026-10-09/items.json`, `outputs.jsonl`; the base commits.
- **Fails if.** `unraised` at 40% or more (either reader).
- **Then.** Silence is attention, not reasoning: gold is a loose lower bound and negative decisions
  cannot be read from it; only stated exceptions count as negative evidence, and the reviewer's
  precision cannot be judged against silence. If `scope_form` and `exception` dominate, negative
  evidence is reconstructible and scope resolution is the mechanism.

### Test 5. Conventions go in and out of style

- **Claim.** Some instantiations change over the census window, and the change is visible in the
  repository (deprecations, adoption in recent code, new automation) before or as the asks change.
- **Method.** For each convention with at least 8 dated asks, test for a shift in the asked form
  across 2025-06 to 2026-03 (split at the median date; a form asked for early and asked against late,
  or appearing only after a date). Cross each shift with the deprecation stream and the introduction
  commit of the automation it names. For each shift, record whether a repository signal preceded the
  first ask in the new form, or only Zulip did.
- **Data.** The census with dates; `results/pr_review_v5/naming_testbed/` (2,987 deprecations); the
  Mathlib log; the Zulip store.
- **Fails if.** Under 5% of eligible conventions shift (currency is not worth a layer). Or shifts
  exist and none has a repository signal before the first ask (the signal is Zulip only).
- **Then.** Sizes the currency layer; says whether the norm store's maturity can be measured from the
  snapshot, as designed, or needs a Zulip reader.

### Test 6. A model can execute the reasoning, given the layers

- **Claim.** Given the principle statement, the place, and search over the scope's code at the base,
  a model derives the scope's established form and judges the PR against it, without the convention
  sentence.
- **Method.** 30 asks (the never-reached ones first) and 15 non-asks of type `scope_form` from test
  4. One prompt each, the convention hidden, for the free model and one strong model, with tool
  access to the base workspace. Read blind against the ask (two readers): derived the asked form /
  derived another form / found no form; and on non-asks, said conforms / departs.
- **Fails if.** Under 70% derive the asked form, or under 70% say conforms on the non-asks, for the
  strong model (the free model is reported beside it).
- **Then.** Which step failed, per case: could not find the scope's form (tooling or search), found
  it and overrode it (needs harness enforcement), resolved the wrong scope (the rule from test 3), or
  needed a fact outside the code (currency or history).

## Order, cost, stop rules

1. Tests 2 and 5: computations over the census, about a day, few model calls. They decide whether
   scope and currency are real layers before any reading.
2. Tests 1, 3, 4: one reading programme, shared evidence vocabulary, two readers per batch, about
   half a day and under a million tokens.
3. Test 6: only if 3 and 4 hold; the only test that queries a reviewer model (free tier, plus one
   strong model for about 45 prompts).

No paid review run, no harness code, no training. **Stop rule:** if test 4 puts `unraised` at 40% or
more and test 3 puts the same-scope form under 50%, the idea in this form is not viable; write what
the residual was made of and stop. Partial failures by principle are the result, not a reason to
widen thresholds.

## Guards

- The principle statements are validated by whether they predict (tests 1, 3, 6), never by how they
  read; they are written before test 3's reading and not revised during it.
- Every reading has two independent readers and a re-check sample by the session; disagreements are
  reported, not averaged.
- The adversarial round attacks the picture first (what would show it false that these tests miss)
  and the tests second (confounds: gold as a lower bound, census labelling bias, scope defined after
  seeing the ask, dates), before anything runs.
- A line goes into `docs/questions.md` for each test as its result lands.

## Amendment 1 (2026-10-16, after the adversarial round; nothing has run)

Three independent reviews, in `2026-10-16-principles-scope-currency/`: `review-premise.md` (the picture),
`review-validity.md` (each test's confounds), `review-feasibility.md` (data, cost, whether outcomes
discriminate). Each computed new numbers from disk; none spent.

### What the round found

**A miss in "Already answered?".** `docs/todo/conventions-nature.md` (2026-09-29) states this picture in
the user's own words and plans its studies 2-4 (scope, conflict, maturity), naming the author join and
the P014/P133 pair as starting points. This plan is those studies with weaker statistics. The index
lists results, not open todos; the check must read `docs/todo/README.md` too.

**Parts of the picture the record already contradicts, with numbers.**
- *Taste a small residual:* readers coded 15 of the 41 hardest asks preference or history and 19 more a
  choice; maintainers hedge 28% of census asks, ask 33% as questions, state no ground in 80%, cite a norm
  in 0.68% of all comments; two opposite rules on one situation coexist (P014 17 asks, P133 7), separated
  by reviewer, not by area or period.
- *One concern, one design:* the library carries two forms at scale with no deprecation between them (48
  against 21, 793 against 440, 130 against 481); the census is unsaturated (one new principle per ten
  asks, 166 singletons). Maintainers tolerate two designs and ask for one at a place.
- *Scope decides:* 18 of 53 head conventions are area-concentrated beyond chance, about 5 after a
  reviewer control; area and reviewer are collinear (74 reviewers, top five 31%). In 9 of the 41 hard
  asks the local precedent was the PR's form and the maintainer asked against it; no rule (narrowest,
  widest or newest wins) fits more than about half.
- *A decision at a place:* 17% of asks repeat a (PR, principle) pair; P100 is the propagation rule;
  maintainers raise a settled convention at 1 in 20 to 1 in 400 of the places it applies. Most
  applicable places are not decided at all.
- *The reviewer lacked the layers, not the sentence:* the sentence at the place writes the change for
  64-74% of in-census asks and is itself the scope-resolved instantiation; every general-form delivery
  above it read null; what moved recall was the model (+0.22) and the harness (+0.10).

**Parts supported:** the census holds the knowledge (39 of 46, 40 of 47 asks); currency is real for a
few migrations (`grind` 4.0% → 14.5% of files, enforcement 9.1 → 22.4 per thousand); misses are at read
places (1 of 558 unattended).

**The strongest rival picture:** demand at about 5% of applicable places, calibrated by volume and
attention, not reconstructible from the code. Every reviewer hits 0.09-0.11 asks per finding whatever it
knows. Under it, knowledge layers predict applicability and not which place gets the ask. Tests 1, 2, 3,
5 as written pass under this rival and under four others; only a controlled test 6 and a fixed test 4
separate them.

**Validity.** Test 4's pool is not silence (every pair is a convention raised elsewhere on the same PR;
67% on four PRs; 21% PR-level entries fired at hunks). Test 2's co-occurrence is 94% expected by chance
for large entries. Test 5's "shift" is undefined and tracks composition (AI-authored share of asks 3.6%
→ 23.6% across the halves). Test 1's bar is pre-met (readers' tags agree at κ 0.75). Test 6 lacks a
no-principle arm and a sentence arm, and 34 of its 41 asks are in the strong model's training window.
The stop rule's lines disagree with the tests' fail lines, and no sample list was seeded.

**Feasibility.** The census joins (cid → PR, path, author, month, for every ask; day dates by one script).
Three data claims were wrong: the deprecation list is not stored (rebuild from `since :=` over two
snapshots); the "departs" pool is 123-209 pairs on 27 entries and 13 PRs, so stratifying by principle is
not possible; the 19 partial rows are single-reader. Readings cost 20-25k tokens an ask: the original
battery is 8-9M reader tokens over five or six session days, not "under a million".

### The battery, revised

Retired: test 1 as a gate; test 2's pair count; test 5's count split; test 3's margin; test 4's sample;
test 6 without controls. Replaced by:

- **R1. The maintainers' stated grounds** (new; the direct measurement). The about 370 census asks that
  state any ground, bodies rebuilt by `census/provenance/materialise_bodies.py`, two readers blind to the
  codebook, coded `principle` / `scope_form` / `currency` / `authority` / `preference` / `fact` / `other`;
  the 76 external references coded form / principle / decision. **Falsifier:** `preference` plus
  `authority` at or above a third, or `principle` under a tenth. About 600k tokens.
- **R2. Scope with author as the separating variable** (test 2 fixed; deterministic). For the
  area-concentrated entries and the incompatible pairs, the author, area and month distribution of each
  side; a side counts only with 3 or more asks. **Falsifier:** more than half the separations are by
  author within one area and period. Entries whose text already holds both forms under an "or" clause
  are counted and reported.
- **R3. Scope resolution has no consistent direction** (test 3 fixed). For every countable ask among the
  41 plus 21 seeded census draws (list committed first), one reader writes the grep predicates for the
  asked and the PR's form blind to which is asked; another counts them at the base commit at file,
  directory, area, library, and last-90-days; dominance needs 5 or more occurrences; the 2×2 (scope ×
  library) is the result, with the dev rows apart. **Falsifier of the scope layer:** no single level wins in
  75% of decided cases. The cases where the maintainer asked against the local precedent are reported by
  name.
- **R4. Silence** (test 4 fixed). First a gold-free statistic over all unasked and decoy "departs" places:
  diff the place between the reviewed head and the merged commit; `fixed_in_merge` or `kept`. Then read
  only `kept` places: 20 seeded from the 836 decoy pairs and 20 from the unasked-exact pairs (caps 4 a PR,
  3 an entry, PR-level entries excluded at declaration places), with 10 of the 33 asked "departs" pairs
  mixed in unlabelled as the readers' calibration; labels non-exclusive: `raised_elsewhere_on_pr`,
  `raised_later_round`, `trigger_absent`, `scope_form`, `exception`, `unraised`, `unclear`, with `raised_later`
  and `fixed_anyway` computed from the PR store, not read. **Read only if** the calibration misfiles under
  15% of real asks. **Thresholds on the decoy `kept` sample:** `unraised` ≥ 60% → silence is mostly
  attention; ≤ 20% → mostly reconstructible; `scope_form` + `exception` ≥ 50% by both readers → scope is
  the mechanism.
- **R5. Currency as rate per applicable place** (test 5 fixed; the `conventions-nature` study 4
  sub-hypothesis). The about 14 countable entries (stage H's rules, the detectors' four, `grind`,
  `to_dual`, `fun_prop`, `mk_iff`): applicable places on census PRs by base month, the ask rate at them,
  a PR-clustered permutation null stratified by AI-authorship and area; first ask taken from the whole
  reviewer corpus; repository signals listed and dated before reading (deprecation stream rebuilt, linter
  landing commits, guideline changes), Zulip thread dates beside them, signal PR ≠ ask PR and at least a
  day earlier. **Thresholds:** ≥ 3 of 14 show a monotone rate change at p < 0.05 → a layer worth sizing;
  0 → not at this window; in ≥ half the shifts a repository signal precedes the first ask → measurable
  from snapshots.
- **R6. The principle without the sentence, same model, controlled** (test 6 fixed; the only new cell and
  the only spend). Paired arms on the same asks and places, both models: (a) place and search, no
  principle, no sentence; (b) the sentence, no search; (c) the principle statement with search; (d) the
  sentence with search. The 26 derivable asks of the 41 (judgement and history excluded) plus 4 seeded
  draws; the 7 post-cutoff asks reported apart from the in-window ones as the memory split. Non-asks: 8
  `scope_form` from R4 and 7 decoy `kept`, plus asked "departs" pairs as decoys whose right answer is
  departs. Blind matchers see the derived form only. **Thresholds, relative:** (c) within 2 asks of (b)
  and (c) − (a) ≥ 8 of 30 for the strong model; (c)'s conforms rate on non-asks minus on asks ≥ 0.4. Agentic
  sessions with tools: about 45 prompts × 4 arms × 2 models; free tier for one, the subscription for the
  other, the user's call.

**Stratification** is by rank (head: top 50; tail) and by AI-authored PR as marginals only; 11 tags × 2
bands over 40 rows is not a stratum. R1's principle statements, if any are written, are written before R3
and R6 and not revised during them.

### Order, cost, one stop rule

1. R2 and R4's `fixed_in_merge` statistic: deterministic, a day, no reader.
2. R1: about 600k tokens, the direct test of the picture.
3. R3 and R4's reading, with different readers for each: about 2.5M tokens.
4. R5: a day of computation plus the rebuilt deprecation stream.
5. R6 only if R3's informative cell and R4's `scope_form` + `exception` line both hold.

About 4-5M reader tokens before R6, three or four session days. **Stop rule, one line:** if R1 reads
`preference` + `authority` at a third or more *and* R4 reads `unraised` at 60% or more on the decoy
sample, the picture in its strong form is false on this record and R6 does not run; what is written up is
the split by rank and by AI-authorship, since the round predicts the picture holds in the head and fails
in the tail.
