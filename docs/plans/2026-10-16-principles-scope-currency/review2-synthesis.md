# Adversarial review 2: the synthesis drawn on 2026-10-16 from three probes

**Under review.** The four-bullet synthesis the user was told on 2026-10-16, from
`probes/enforcement-at-departures-2026-10-16`, `probes/stated-grounds-2026-10-16` and
`probes/stage-h-departures-2026-10-16`:

1. The "5% of applicable places" figure counted places where a rule's situation occurs. Per real
   departure, maintainers ask about 10% of the time.
2. Substantive conventions (use the API, name like siblings, drop an unneeded hypothesis) are applied:
   flagged places mostly conform. Layout and cosmetic conventions (line breaks, `variable` lines, dot
   notation, merged steps) are loosely enforced: real departures merge unasked.
3. When maintainers give a reason, it is mostly a technical fact or a general value. Taste and
   authority are about a quarter. This supports the user's picture of review as reasoning from
   evidence.
4. Design implication. For substantive conventions the reviewer's job is the check (compile, search),
   not spotting the situation. Flagging the situation floods maintainers because the code usually
   conforms. Layout departures are low-value noise.

**Read.** The three probes' `PROTOCOL.md`, `RESULTS.md`, item lists, readings and scorers.
`docs/questions.md`, `docs/dead-ends.md`, `docs/todo/README.md`, `docs/todo/conventions-nature.md`,
`docs/todo/conventions-dossiers-exams.md`, `docs/todo/review-mechanical-sweeps.md`,
`docs/research/conventions-assessment-2026-10-12.md`, `docs/research/ceiling-residual-2026-10.md`,
`docs/research/filing-decision-design-2026-10-12.md`. Stage G and stage H in
`probes/conventions-ceiling-2026-10-04/README.md`. The plan with its amendment, and the three
first-round reviews beside this file.

**Computed here.** Nothing was run that spends, and no other file was modified. Numbers marked
*(computed here)* come from four sources:
- joins of `stage-h-departures/step2_items.jsonl`, `readings/R{1,2}.jsonl` and `follow.jsonl` on
  (PR, rule, file, declaration);
- the stage G rule text in `conventions-ceiling-2026-10-04/rules.json`, and the rate index in
  `census_rates.json`;
- the census primary labels (`conventions-census-v1/reader_A/labels_b*.jsonl`), joined to
  `arm-coverage-val1000-*/events.jsonl` for PR and author;
- the PR store's `review_comments.jsonl` for the stage H PRs.

Head-versus-merged diffs of the changed places use `follow.py`'s own `apply_patch` and `blocks`, at the
round-1 head and the merge commit. `probes/x` means `results/pr_review_v5/probes/x`.

## 0. Verdicts

| bullet as told | verdict | what the evidence supports |
|---|---|---|
| 1a. The 5% counted situations | **stands** | It was 205 (declaration, rule) pairs on 82 declarations, up to nine rules on one declaration. 176 carry the pinpointer's `check` ("this rule could apply"). |
| 1b. Per real departure, about 10% | **weakened** | Of order 10%. Sampling alone gives 7-15% (13 of 48 departs, 95% interval 17-41%). The rate differs several-fold by rule: about 2% for line breaks, 27% or more for "use the API". The count of asks is too low wherever one ask covers siblings. Either way, demand is still a small subset of departures. |
| 2a. Substantive conventions are applied | **falls as worded** | Readers without Lean saw few departures where a search- or compile-checked rule could apply. That does not separate three causes: authors conforming, a trigger that fires everywhere, and readers who cannot see the departure. The readers' calibration misses fall under exactly these rules. "Applied", meaning asked or fixed, is shown for one rule (P011) on 4-5 asks. |
| 2b. Layout departures merge unasked | **stands for dot notation and line breaks; weakened for the rest** | Dot notation: calibrated 5 of 5, 0 of 32 unasked fixed on control PRs. Line breaks: 5 of 6 agreed places, mechanically checkable. `variable` lines rest on 1 agreed departure. Merged steps rest on 3, read without the compile their rule requires. |
| 3. Stated grounds support the picture | **weakened** | It holds for the 17% of asks that state a ground. Those were selected by markers that favour explanations and omit the commonest hedges. There, taste and authority are 24-29%. The picture's own layers are thin in what maintainers say: scope below the library 4.5%, currency 3%. |
| 4. Design implication | **mostly a restatement; one clause contradicted by the record** | The "flood" half restates stage H, the places test and the detectors. The "check" half restates the closer battery, the filing-decision design's first rank, stage G and the filing contract; the last two were tried. "Layout is noise" is a selection proposal, and the user ruled selection out on 2026-09-22. It also conflicts with the recall goal. |

---

## 1. Does each claim follow from its numbers?

### 1.1 Bullet 1: from 2.9% per flagged place to about 10% per departure

**The first half stands, and is stronger than told.** Stage H's 205 "applicable places" are 205
(declaration, rule) pairs on **82 declarations**. 39 declarations carry one rule; 15 carry five to
nine *(computed here, `follow.jsonl`)*. On 35140 the pinpointer flagged `Functor.isTerminal` and
`isInitial` under seven rules each; on 26301 and 37190 one declaration each carries nine. Step 1 already
said the pinpointer "flagged most of the declarations each PR touched"
(`stage-h-departures/RESULTS.md`). So the 2.9% was asks per (touched declaration × rule that could
conceivably apply). It was never a demand rate at places where a convention is relevant.

**The second half is one estimate with wide error, and it pools unlike things.**
- **Sampling.** 13 of 48 decided agreed items depart, 27%, with a Wilson 95% interval of 17-41%. That
  interval maps to 7-15% per departure, before any reader error *(computed here)*.
- **Calibration.**
  - Reader R1 missed 2 of 6 asked places, below the pre-registered 5 of 6. R2 met the bar exactly.
  - Both misses are under P011 ("derive it from existing API").
  - The amended plan set a stricter bar for reading silence: "read only if the calibration misfiles
    under 15% of real asks" (R4, plan amendment 1). Neither reader meets it: 33% and 17%.
  - No negative calibration set was read (places known to conform), so the false-`departs` rate is
    unmeasured. The record puts it near 0.28-0.30 for a model's one-turn verdict
    (`docs/questions.md`, "Asked at every changed place").
- **One rule carries the asks.** Four of the six asked places are P011; the others are one P010 and
  one P084 (line breaks). Per kind of check *(computed here, the scorer's pooled shares against the
  unasked population of each kind)*:

  | kind | departures per decided label | asks per departure |
  |---|---|---|
  | lookup | 15% | about 20%, entirely P011's 4 asks |
  | compile | 24% | about 6% |
  | layout read | 64% | about 5% |

  P100, P126 and P254 have no ask on their 91 flagged places. Per rule, dividing the census rate index
  (`census_rates.json`, asks over 973 PRs) by the departs share gives about 1.6-1.7% for P084 and
  P126, about 7% for P018 and P048, 14% for P040 and 27% for P011. The pooled 10% is an average over
  a several-fold spread.
- **The ask count misses sibling and neighbouring asks.** Two of the six asked comments on stage H's
  PRs cover more than their own line. On 35140, dagurtomas's suggestion for `isTerminal` ends
  "similar below". On 37190, IvanRenison's line-break ask says "The same for the other lemma"
  (`data/pull_requests/pr/{35140,37190}/review_comments.jsonl`). The probe counts the place below,
  `isInitial` under P011 (item H008), as unasked. The merged code is exactly the suggested
  `evaluationJointlyReflectsColimits` proof *(computed here, head versus merge)*. On 32598,
  kbuzzard's "I don't think this conforms to the naming convention -- are there any other uses of
  `Dep`" was filed under census entry P220 ("ad hoc suffixes such as `Dep` are not used"). The P254
  places on the same `Dep` declarations ("name it like its siblings") therefore count as unasked.
  The census already records the general pattern: 17% of asks repeat a (PR, principle) pair
  (`review-premise.md` §1.5).

**What survives.** Demand is a small subset of real departures: about one in ten, varying by rule.
That keeps the assessment's point that strict application is a volume lever
(`research/conventions-assessment-2026-10-12.md` §5.3), with the denominator corrected.

### 1.2 Bullet 2: the substantive/layout split is the instrument's split

**It was not pre-registered, and the labels drift.** Step 2's protocol fixed only one by-kind
report, `needs_tools` "by rule and check kind (compile, lookup, read)". The departs-by-kind table, and
the reading of kind as "substantive versus layout", came after scoring. The labels then move between
tellings:
- the commit body (`df1a64ee`) and `docs/questions.md` line 84 list "merged steps" (P018) among the
  layout rules at "64%". In the scorer P018 is a compile rule (6 of 10), and the 64% is P084 plus P048;
- the commit lists P010 ("drop an unneeded hypothesis") among the "search-decided substantive rules".
  Its stated check is "Delete the hypothesis … and rebuild. Departure: it still compiles"
  (`rules.json`);
- P126 ("spell it as the file does": `have`/`haveI`, `=>`/`↦`) is cosmetic but sits in the "search"
  group;
- dot notation enters the layout group from another probe with other readers.

**The split is the pinpointer's status, and status is the rule's check kind.** *(Computed here.)*
- The pinpointer marked `departs` at all 29 places of the two read-kind rules (P084 23, P048 6) and
  `check` at every place of the other eight.
- The step 2 readers had git and no Lean. They confirmed `departs` where the departure is visible by
  reading.
- They mostly wrote `conforms` where the rule's own check is a compile or a library search they did
  not run:
  - P010: 5 of 5 places `conforms`, 0 `needs_tools` ("[IsEmpty n] is essential"; "CommRing is needed
    for det");
  - P040: 5 of 6 agreed `conforms` on "reads no better";
  - in the other direction, P018 was labelled `departs` on the assumption that the merged call
    compiles ("intro … cases k merges into rintro", low confidence).

So the contrast is between departures a reader can see and departures that need a tool. It is
confounded with substantive versus layout by construction.

**On agreed items the substantive side is two departures.** *(Computed here.)* For P005, P010, P011,
P040, P100 and P254 together: 2 departures of 28 decided agreed items, 2 to 7 per rule. For P084,
P048, P018 and P126: 11 of 20. The synthesis names three examples:
- "Name like siblings" (P254): 7 of 7 agreed `conforms`, with no calibration item. P254 has **4
  census asks (rank 107)**, a tail convention.
- "Use the API" (P011): 2 open places agreed `conforms` after H008 drops out as a disagreement. This
  is the rule where the readers' calibration failed (below).
- "Drop an unneeded hypothesis" (P010): 5 of 5 `conforms`, read without the rebuild the rule
  prescribes.

**The readers miss real departures under exactly these rules.**
- H055 (32598, asked under P011). The maintainer's ask was a one-line lemma for an inner step ("this
  can be: `have h … := update_eq_self i₀ f`", census v1378). Both readers wrote `conforms` at the
  level of the whole equivalence: "no base API yields the dependent equivalence".
- H066 (35140, asked). R1 wrote `conforms`; R2 found `evaluationJointlyReflectsLimits`.
- H008, its sibling below, was covered by the "similar below" ask and fixed by merge. R1 wrote
  `conforms` and R2 `departs`, so the both-agree headline drops the one open P011 place that was a
  real, enforced departure.
- H026 (32598, P254, `subsingletonEquivDep_apply_tprod`). Both readers wrote `conforms` (R2: high),
  citing the sibling `tmulEquivDep`. Two maintainers asked to drop `Dep` (P220), and every `Dep`
  declaration is gone at merge.

This is the record's own failure mode for naming: a local precedent licenses the PR's form, and the
maintainer asks against it. That held in 9 of 41 hard asks (`review-premise.md` §1.2) and in 13 of
105 drops (`docs/questions.md`, "On what grounds does the free reviewer drop a concern").

**The readings do not predict what changed by merge.** *(Computed here.)*
- 9 of 31 agreed-`conforms` places changed or went by merge (29%), against 3 of 13 agreed-`departs`
  (23%).
- All nine are on 35140 and 32598, where a substantive ask rewrote or removed the declaration.
- None of the 13 agreed departures changed under its own rule. The three that changed went with the
  same rewrites, or with a removal.

So layout departures are untouched by merge, which supports 2b. One substantive ask, meanwhile, moves
five to seven "places" at once, which is the accounting problem of 1.1.

**The enforcement probe does not reach substantive conventions.** Its three conventions are dot
notation, namespace placement and primed names. Placement's result, 97% not departures, is construct
error in the detector's sentence, not conformance under enforcement. Primes were unreadable: both
written versions failed calibration (2 of 6, then 4 of 6). The first reading had both readers exclude
4 of 6 asked-and-fixed primed names. That is the same instrument, one day earlier, mislabelling
maintainer-fixed naming departures as fine. By its own pre-registered rule 2, "applied" meant
departures fixed by merge at 70% or more. The outcome was 2%.

**2b, layout, on its own evidence.**
- **Dot notation is the best-founded result of the three probes.** Survival is deterministic:
  unasked calls fixed 2 of 113, 0 of 32 on control PRs. Calibration was 5 of 5; 12-13 of 16 read
  survivors are departures, on 13 PRs.
- **Line breaks (P084).** 5 of 6 agreed places, on a rule decided by measuring line length, and 1 ask
  in 23 flags.
- **`variable` lines (P048).** One agreed departure. Pooled 4 of 10, with 6 `excluded` (R1 4, R2 2).
- **Merged steps (P018).** 3 agreed departures, labelled without compiling.
- **Selection of the rules.** P084 and P126 were stage G's *decoys*, "the decoys with the most
  candidates" (`conventions-ceiling-2026-10-04/README.md`, stage H). They were chosen because the
  pinpointer fires on them most and no probe ask was behind them. "Layout departures merge unasked"
  is partly how they were picked.

### 1.3 Bullet 3: stated grounds

The pre-registered rule reads "supported" on both readers and on agreed items. Four limits move it
from "supports the user's picture" to a narrower statement.

- **Selection favours explanations and under-samples hedges.** *(Computed here, from
  `selected.jsonl`.)* Of the 318 asks, the markers fired as follows:

  | marker | asks |
  |---|---|
  | reason | 154 |
  | external | 87 |
  | preference | 47 |
  | currency | 43 |
  | consistency | 30 |

  The preference pattern (`select.py`) has "I prefer", "personally", "nicer", "cleaner", "more
  readable", "ugly". It omits "nit", "optional", "maybe", "I think" and "minor". Those carry the
  premise review's 28% hedge rate, and 24% of census asks are hedged with no norm reference
  (`review-premise.md` §1.3). A reason word ("because", "since") selects for explanation, which is
  factual by its nature. Fact is the largest class, 78 agreed, and about 23 of those are "it already
  exists / duplicate / derivable" *(keyword count on the notes, rough)*. Those restate a reuse ask
  as its own reason.
- **Readability in the first person was coded as a principle.** Of the 47 preference-marked asks,
  each reader coded 13 `principle`, mostly readability. The notes:
  - "'hard for me to read'";
  - "'I prefer it' no catch-all";
  - "'not sure if this is more readable'; … grind 'opaque to me'".

  Recode those 13 and preference plus authority is 29%, and the "picture" kinds are 68%
  *(computed here)*. Both still fall on the rule's "supported" side, by 4 points and 1 point.
- **The picture's own layers are small in what maintainers say.** Scope grounds, by reader A's
  scope field on agreed items: library 17, file 7, area 4. So a scope below the library is 11 of 246
  (4.5%), and "Mathlib does X" is a global form, not a scope-dependent one. Currency is 7 (3%).
  Principles are named in 53 distinct free-text forms over 67 agreed items. Generality and
  readability recur; nothing here shows a *short* list.
- **The falsifier was one-sided.** "Fact" counts toward support. A taste-and-authority rival is a
  claim about *convention* decisions. It predicts nothing about "this does not compile" or "`simp`
  cannot do this", so a third of the support is neutral between the pictures.

**What it supports.** When a maintainer writes a reason, 17% of the time, it is a fact or a general
value about three times as often as taste or authority. It says nothing about the 83% with no stated
ground. In that 83%, readers coded 15 of the 41 hardest asks preference or history, and 19 more a
choice among the library's options (`probes/library-knowledge-2026-10-13`).

### 1.4 Every reading in the three probes sits at or under its calibration bar

| probe | readers | calibration | bar |
|---|---|---|---|
| enforcement, all three conventions | A, B | 9 of 13 each | met exactly |
| enforcement, primes re-read | C, D | 4 of 6 each | failed (5 of 6) |
| stage H step 2 | R1, R2 | 4 of 6, 5 of 6 | R1 failed, R2 met exactly |
| stated grounds | A, B | none (agreement 295 of 318) | — |

All eight readers are one model family (the RESULTS' own limit). The stage H calibration has six
items on three rules (P011 four, P010 one, P084 one). Seven of the ten rules were read with no
calibration item at all, P254 included, and every calibration failure is on a substantive or naming
rule.

---

## 2. Is "substantive conventions are applied" the only reading?

There are four readings of "few departures at flagged substantive places", and each has evidence on
disk.

| reading | evidence for | evidence against |
|---|---|---|
| **(a) maintainers enforce them** | P011 is asked at 4 of 17 flagged places on 4 PRs (plus H008 by "similar below"), with few unasked departures by the readers: 48-65% per departure if the readers are right *(computed here)*. Asked departures are fixed: 4 of 4 asked places changed or gone (stage H step 1); 8 of 9 (enforcement). | No other substantive rule has more than one ask: P010 1 of 18, P040, P100, P254 and P005 0 of 92. The enforcement probe's own definition of "applied" (fixed by merge ≥ 70%) read 2%. "Fixed when asked" shows compliance, not that departures get asked. |
| **(b) authors already conform** | The library conforms at 0.94 and 0.91 where naming can be counted (`docs/questions.md`, "Can naming asks be read off the corpus?"). Placement as held: 97% of the detector's flags are not departures. | It cannot be separated from (a): conformance at base is the product of earlier enforcement (`review-premise.md` §3.3). |
| **(c) the trigger flags the situation everywhere** | 205 places on 82 declarations, up to nine rules on one. P010 fires on any side condition or typeclass, P254 on any declaration with a sibling, P100 on any family member. Most hypotheses are needed and most names follow siblings, so most flags conform almost by definition. | — |
| **(d) the readers cannot see the departure** | The calibration misses are all substantive or naming: H055, H066 and, in the enforcement probe, 4 of 6 asked primes excluded. H008 and H026 were read as conforming at places maintainers asked about and fixed. P010 and P040 were read as conforming without their compile. The ladder: told only that a maintainer asked at the place, the model writes the change for 5 of 39; with the sentence, 25-29 (`docs/questions.md`). | The readers did say `departs` at known asked places 4-5 of 6, so sensitivity is not zero. |

**What the record already favours.** (c) is structural and certain. (d) is measured wherever it can
be: the stage H calibration, the primes calibration, and the reviewers' own behaviour.
- In 63 of 67 residual misses every reviewer that missed had read, searched or compiled the object.
  "Attempted and concluded fine" is 60% (`docs/questions.md`, "Where does a reviewer miss").
- The free reviewer "checked and read as conforming" 17 rows and "concluded fine" 65
  (`probes/ask-reading-2026-10-12`).

The step 2 readers are that reviewer's judgement, given the rule and no tools. (b) is plausible for
most code and is not separable from (a) on this design. (a) has one rule's evidence, 4-5 asks.

The synthesis's wording picks (a). The record supports "most flagged substantive places conform by
the reader's lights, under triggers that fire on nearly every declaration, with a reader that misses
some real departures". A design would read that very differently.

---

## 3. Tension with the record

The record says reviewers miss substantive asks that maintainers raise:
- statement and API design is 14% of census asks, and 0 of 18 were reached even with the sentence
  held, every held sentence ignored (`docs/questions.md`, "What does the reviewer do with a
  convention sentence");
- naming is 9.7% of census asks and 29% of dev;
- the never-reached kinds are naming judgement, statement design, proof try-its, library mechanisms
  and PR-level asks, each at most about 0.08 of a set (`docs/questions.md`, "Who reaches what").

If flagged substantive places mostly conform, the asks come from four places, and the record has each
of them.

1. **From the rare departure, which a reviewer must tell apart from many conforming places.** A
   reviewer whose prior is "this conforms" is right at about 85-93% of flagged substantive places, and
   wrong exactly at the asks. That explains "concluded fine" as a base-rate behaviour, not ignorance.
   The design question is then discrimination at a low base rate, and step 2's readers show the same
   miss.
2. **From conventions the probes did not measure.** Their 13 conventions hold 272 of 1,833 primary
   census asks, 14.8% *(computed here)*. The substantive heads the reviewers miss are absent:
   - P019, a name built from the statement's declarations: 54 asks, rank 2;
   - P004, extract the general core: 40 asks, rank 3;
   - P007, use the library-named predicate: 37 asks, rank 4;
   - P063, generalise from a concrete type: 25 asks, rank 9.

   p0005, "does this hold in any UFD", is P063. Every reviewer reached that place and judged it on
   its merits (`research/ceiling-residual-2026-10.md` §2).
3. **From asks that land at "unasked" places by propagation or a neighbouring entry.** 35140's
   "similar below", 37190's "the same for the other lemma", and 32598's `Dep` naming ask filed under
   P220 at P254's places.
4. **From places the reader calls conforming and the maintainer does not.** H026 (siblings as
   licence), H055 (the whole construction checked, the step missed). This is the record's "the local
   precedent was the PR's form" (9 of 41) and "a plurality or tool count" (22 of 105 drops).

Read with these four, there is no contradiction, but the synthesis's emphasis is inverted. For
substantive conventions, "the code usually conforms" is not reassurance: it is why the reviewer
concludes "fine" and misses the rare ask. Mostly-conforming code is the condition under which the
reviewer fails. It does not show that the conventions are applied.

---

## 4. Is the design implication new?

No, except for one number. Each clause has a lineage on disk.

| clause | already measured or tried | what was learned |
|---|---|---|
| "The reviewer's job is the check (compile, search)" | **Closer battery** (2026-09-26): 8 of 15 targeted misses produced verbatim by fixed procedures; `exact?` missed an in-file duplicate. Its todo, `review-mechanical-sweeps.md`, is **open and bounded**, with a pre-registered blind run (at least 15 of 38 misses hit, at most 8 firings a PR) that has **never run**. | Checks find mechanical asks *when aimed by the ask*; the blind yield is the unmeasured quantity. |
| | **Residual mechanisms** (2026-09-30): "decidable by one compile never run" 28%; 63 of 67 misses had the object read, searched or compiled; "concluded fine" 60%; "verified and withheld" 3%. | The reviewer usually does check; the miss is the conclusion. |
| | **Facet brief / complement** (2026-09-25): compile access makes findings verified, not more numerous (26 / 25 → 29 / 26). **Construction demo** (2026-09-29): briefed to construct, Claude was unchanged (it already constructs); gpt-5.2 compiled three times as much and reach fell 0.12 → 0.06. | More checking does not raise recall by itself. |
| | **Stage G** (2026-10-05): each rule with a trigger and a check, delivered at the place (307 checks), gave **+0.000**. "`gcongr` … did not make progress … I dropped that item", where the maintainer's ask was the question "Can `gcongr` do this?". | A failed check on the reviewer's own variant turns a real ask into silence. Questions whose answer is "no" are asks (v0068, v0092, v0105, p0005, p0000). |
| | **Ceiling residual** (2026-10-09): execution misses v0092 and v0093, "a failed check read as conforming". **Filing-decision design** (2026-10-12) §3.2: rank 1 "a check that decides … a check that fails on the reviewer's own candidate does not clear it". **The free reviewer's drops**: 26 of 105 rest on a check not run or run on the wrong candidate; 21 of 35 checked-as-conforming rows on a failed check or a lower authority. | The design that follows from "the job is the check" was written, with the failure mode named. |
| | **Filing contract G** (2026-10-13, `docs/dead-ends.md`): `conforms` only with a verified quote or a re-run check. 14 of 37 against a line of 16; 0 of 32 never-reached; 4.9 findings a control PR. | Making the check the condition for silence filed the topic, not the maintainer's change. Closed. |
| | **Assessment §7 option C** (2026-10-12): a closer battery as facts; ceiling about 0.065 of a set; "the hand sweep went 0 of 3, so the linters must be shown to fire on these six first". | The recall ceiling of the check route on these sets is small and stated. |
| "Flagging the situation floods maintainers" | Stage H Result 6 ("apply strictly" is a volume lever); the places test (68 filings a PR, 25x solo's volume for 3x its reach); the detectors with the disposition paragraph (13 of 14 unasked facts filed); the filing contract (4.9 a control PR). | Known. No design on record files situations. The flood measured is from filing *departures*, and the probes say 90% of real departures go unasked too. |
| "Layout departures are low-value noise" | `docs/dead-ends.md`, "Convention detectors as a recall lever": dot notation's ceiling is 2.9% of asks, and it reopens "if precision becomes the goal". "Publication as selection" (the user, 2026-09-22): "I don't want to consider anything related to selection at the moment". `docs/questions.md`: "Any proposal about which findings reach a maintainer is selection, refused until the generator is better." | Calling a class of real departures noise and not filing them is a selection rule, already ruled out. |

**Two parts of the implication run against the record's numbers.**
- **"Low-value" by precision.** The per-departure ask rate for these conventions (about 10% pooled;
  about 7% for dot notation, 4 exactly-asked calls among roughly 60 real departures in 75 facts) is
  the same as every reviewer's hit rate per finding, 0.09-0.11 (`docs/questions.md`, "Does any
  reviewer aim better"). A reviewer that filed only true layout departures would be no less precise
  against round-1 gold than any reviewer measured.
- **"Low-value" by recall.** The goal is issue recall (auto-memory, 2026-10-07). The layout and
  cosmetic conventions in these probes hold 96 of 1,833 primary census asks (5.2%), and two of them
  are head conventions: P018, merged steps, 37 asks, rank 6; P057, dot notation, 24, rank 11.
  Formatting is 12% of census asks (`docs/questions.md`, "How much of the dev gold is one reviewer's
  taste").

**What is new.** One number: under rules whose check is a search or a compile, departures are rare
among the places a broad trigger flags (by the readers' lights, about 7-15%). That gives the base rate
for a check-first design. A check run at every flagged place mostly returns "conforms", which bounds
its volume, and helps only where the check *decides* (compiles, exact lookup) rather than informing a
judgement that then defaults to "fine". It does not show that checking finds the asks. The readers ran
no check, and the record's reviewers who did check drew the wrong conclusion from it.

---

## 5. What the synthesis leaves out that a design would need

- **The 83% with no stated ground.** 45% of census asks are a bare ` ```suggestion ` block, 33% are
  questions, 28% are hedged (`review-premise.md` §1.3). Questions matter most for the implication:
  maintainers ask "can X do this?" where the answer is no. A check-first reviewer that stays silent
  on a failed check loses them, as stage G did.
- **The tail.** The three probes cover 13 conventions holding 14.8% of primary census asks. The
  check-type five (P005, P010, P011, P018, P040) hold 9.2%, about the "execution-checkable leaders
  hold 7%" of the detectors entry. The census has 399 conventions, the top 50 holding half and 286
  with three asks or fewer.
- **Statement and API design, generality and the naming heads.** None of P004, P063, P019 or P007 was
  measured. P254, the naming rule the synthesis cites, has 4 asks.
- **PR-level asks.** 6% of asks, 16% on AI-generated PRs (`research/pipeline-overfit-2026-09-replication.md`).
- **AI-authored PRs, the stated target.**
  - Stage H's sample holds 3 of 16, and 21 of their 32 flagged places sit on PRs with no merge commit.
  - Step 2 read 3 places on them, and none came out an agreed `departs` or `conforms` *(computed
    here)*.
  - The enforcement probe has no AI split. Its arbiter, the merge, does not exist when an AI PR closes
    unmerged.
  - Stated grounds: 56 AI-authored asks, authority 15% against 6%.

  No bullet says anything about the population the project is for.
- **One ask, many places.** Two of the six asked comments on stage H's PRs cover a sibling, one ask
  sits under a neighbouring entry, and one substantive rewrite moved up to seven (declaration, rule)
  pairs. Per-place accounting splits a maintainer's single decision.
- **Who reviews.** One reviewer wrote 29 of dev's 47 asks, and "enforced where noticed" depends on who
  is noticing (`review-premise.md` §1.7).
- **Rounds and the merge.** Asks are round 1 and fixes are judged at merge. `docs/dead-ends.md`
  ("Δ revealed-preference framing") rules the merge diff out as ground truth because authors make the
  changes. "Merged unchanged" therefore reads as "not fixed", never as "unwanted".
- **A recall ceiling for the implied design.** None is stated. On the table's sets, the try-it class
  no ask-free session reaches is 6 asks (0.065 a set) and library mechanisms 3 (0.03)
  (`research/conventions-assessment-2026-10-12.md` §6). One reader labelled 31 of 38 misses
  "findable" by sweeps (`review-mechanical-sweeps.md`), an upper bound never tested blind.
- **The plan's other half.** R4 (silence, with a decoy baseline and calibration under 15% misfiles)
  has not run, so only one half of amendment 1's two-part stop rule is measured.

---

## 6. Verdict per bullet, restated, and what the probes license

**Bullet 1 — first half stands; second half weakened.** "The 2.9% was asks per (touched declaration,
rule that could apply). Per real departure, as two same-family readers judge it, round-1 asks are of
order 10% (7-15% from sampling alone), from about 2% for line breaks to over a quarter for 'use the
API', undercounted where one ask covers siblings. Demand remains a small subset of departures."

**Bullet 2 — the substantive half falls as worded; the layout half stands narrowly.** "At places where
a search- or compile-checked rule could apply, readers without Lean saw few departures. The rules'
triggers fire on nearly every declaration, and the readers missed real departures under exactly these
rules, so this does not show the conventions are applied. Only P011 shows asks at a high rate per
departure, on 4-5 asks. Dot notation and line-break departures do reach merge unasked (calibrated,
deterministic survival). `variable` lines and merged steps rest on one and three readings." The
substantive/layout split should be reported as what it is: departures a reader can see against
departures that need a tool.

**Bullet 3 — weakened.** "When a maintainer states a reason (17% of asks, selected by markers that
favour explanations), it is a fact or a general value about three times as often as taste or
authority (24%; 29% if first-person readability counts as taste). Scope below the library (4.5%) and
currency (3%) are small in what they say. Nothing here reads the 83% that state no reason."

**Bullet 4 — a restatement, with one clause the record contradicts.** "Flood" restates stage H and the
places test. "The job is the check" restates the closer battery, the filing-decision design's rank 1,
stage G (+0.000) and the filing contract (closed), whose lesson is that reviewers already check and
fail on the conclusion. "Layout is noise" is selection, ruled out on 2026-09-22. It also fits neither
the per-departure rate, which equals current reviewer precision, nor the recall goal.

**What the three probes license.**

1. **Corrections to the record, before anything is built on these lines.** In `docs/questions.md`
   line 84 and the stage H result:
   - P018 is a compile rule and does not belong in the 64%;
   - P010's check is a compile;
   - the kind split is the pinpointer's status split;
   - H008 was asked ("similar below") and fixed;
   - H026 was read as conforming against a maintainer's explicit naming objection;
   - the 60 open places sit on 11 PRs, not 13.
2. **One measurement that turns bullet 2 into a measurement, with no model calls.** Run each rule's
   *own stated check* at stage H's compile-kind places on the merged PRs: P005 a finishing tactic,
   P010 delete the hypothesis, P018 merge the calls, P040 a term. Run an exact library search at
   P011's places.
   - It needs reviewed workspaces for those PRs: 144-997 s and about 2.8 GB each
     (`docs/questions.md`, "Why reviewed workspaces"), CPU only.
   - Pre-register first:
     - if the compile-confirmed departure share is 15 points or more above the readers' (24%
       compile, 15% lookup), "substantive flagged places mostly conform" falls;
     - within 10 points, it stands as a statement about the code, not about enforcement.
   - It also settles the 10 `needs_tools` labels.
3. **The test of "the reviewer's job is the check" already exists and is pre-registered: the
   mechanical-sweeps blind run.** That is seven procedures over every object of the 23 PRs of both
   sets, with a close rule of at least 15 of 38 misses at no more than 8 firings a PR
   (`docs/todo/review-mechanical-sweeps.md`). It is CPU and Lean time, no model. Its ceiling on the
   sets is the try-it class (0.065 a set) plus part of library mechanisms (0.03). Run it before any
   check-first reviewer design. If it misses its line, the check route goes to `docs/dead-ends.md`
   with these probes' base rate attached.
4. **Any further reading of silence** uses a negative calibration set (places known to conform) beside
   the asked ones, and the amended plan's bar (misfiles under 15%).

**Not licensed.** A check-first reviewer run: stage G and the filing contract measured that mechanism,
and nothing here changes the reason they failed. Suppressing layout departures, which is selection.
Reporting "substantive conventions are applied" outside the project.
