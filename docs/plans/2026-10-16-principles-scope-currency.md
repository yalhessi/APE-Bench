# Principles, scope and currency: where the idea holds and where it fails (plan, 2026-10-16)

Status: pre-registered, adversarial round pending, nothing run. Written in this session from the user's
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
