# Adversarial review 3, part 3: is the proposed next step the right one?

**Under attack.** Two parts of the step-4 read told to the user on 2026-10-16
(`results/pr_review_v5/probes/stage-h-departures-2026-10-16/RESULTS.md`, last section):
- **(e)** the explanation: none of the ten rules has a `not_when` condition (11 of 52 do); their literal checks
  count changes no maintainer would want; so the rules encode only the positive half of the maintainers'
  reasoning.
- **(f)** the next step: the plan's silence test (R4) on the 20 literal departures that merged unchanged. Can a
  blind reader state a reason not to ask that holds across PRs, while finding none at the asked places?

**Read.** The plan and amendment 1; the probe's `PROTOCOL.md`, `RESULTS.md`, items, checks, audit, readings and
`follow.py`; the round-1 and round-2 reviews beside this file; `docs/questions.md`, `docs/dead-ends.md`,
`docs/todo/README.md`, `docs/todo/conventions-nature.md`, `docs/todo/adjudication-rubric.md`;
`.claude/rules/mathlib-review.md`; the READMEs or RESULTS of `conventions-ceiling-2026-10-04` (stages G and H),
`conventions-places-2026-10-09`, `enforcement-at-departures-2026-10-16`, `ask-reading-2026-10-12`,
`filing-contract-2026-10-12`, `library-knowledge-2026-10-13`, `stated-grounds-2026-10-16`.

**Computed here.** No model call, no Lean, nothing spent, no tracked file changed except this one. Scripts are in
`/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/a142d916-dd29-4521-a449-00e1db067b18/scratchpad/rev3/direction/`,
each run from the worktree root with `ape/bin/python`:

| script | what it computes |
|---|---|
| `twenty.py` | rebuilds the 20 unchanged literal departures; rule, PR, `longer`, reader labels; the 7 asked places |
| `attention.py` | per place: PR author, AI flag, round-1 inline comments by anyone but the author on the PR and file |
| `decl_attention.py` | per place: a round-1 comment within 3 lines of the declaration's span at the round-1 head |
| `pr_attention_205.py` | the same at PR level over all 205 stage H places; author's own review activity |
| `later_master.py` | each of the 20 at the merge commit against the clone's HEAD (2026-05-14) |
| `leaf_collisions.py` | places whose declaration leaf names more than one header in the file (a `follow.py` defect) |
| `rider.py` | census asks under the ten rules: suggestion blocks, whitespace-only suggestions, second principles |
| `author_trust.py` | val1000 asks per 100 added lines by the author's own review activity and AI flag |
| `declines.py` | maintainer comments in any round on val1000 PRs that carry a decline phrase ("no need", "fine as is") |
| `p084_scale.py`, `p084_match.py` | every joinable two-line signature in val1000's round-1 diffs, matched to census asks |
| `maintainer_typed.py` | two-line signatures that maintainers typed themselves in suggestion blocks, and how many are joinable |

`rider.py`, `declines.py` and `maintainer_typed.py` read census bodies rebuilt by
`provenance/materialise_bodies.py` into scratch (`bodies.json`); no body is quoted beyond eight words.

---

## 0. Verdicts

| claim | verdict | the evidence, in one line |
|---|---|---|
| (e1) None of the ten rules has a `not_when`; 11 of 52 do | **stands as a count; falls as evidence** | The rule-writer rubric allowed a `not_when` only "if the sentence or the examples show one … Do not invent one", and the examples were asks only. Four of the five `judge` rules carry one, and stage H took no `judge` rule. Among the other 47, 7 do; drawing 10 with none has p = 0.16. |
| (e2) The literal checks count changes no maintainer would want (a longer `aesop`; any join within 100 characters) | **weakened** | Both `aesop` rows (K001, K062) were rewritten by merge, so neither is among the 20. In the 20, 1 of 8 candidates is longer. In the three areas round 2 measured, base Mathlib follows the join rule in 76-89% of two-line signatures, so "does not follow" is wrong. But maintainers' own typed signatures break the rule at 28% (below), so for P084 the claim holds in a stronger form than stated. |
| (e3) This fits the user's picture: the rules encode only the positive half | **weakened; not new** | The reviewer these rules were delivered to already supplies a negative half, and uses it at asked places (§1). What the record lacks is negative evidence that *discriminates*. The rules file has said since 2026-10-16 that a rule must be calibrated on fixed departures before counting anything with it; these ten never were. |
| (f) The silence test on the 20 tests the picture | **falls as specified** | 17 of the 20 have no round-1 comment within 3 lines of their declaration, and 8 sit on PRs with no inline review comment at all, so no maintainer decision is visible there. 5 of the 7 control places are one rule that appears once in the 20. The record shows readers finding reasons not to ask at real asks. "A cost" counts as negative evidence in the picture, so a reason can always be found. |
| (f) A positive result would change how reviewers are built | **falls** | It yields `not_when` clauses for the seven rules in the 20. Used to suppress filings, those clauses are selection, which the user ruled out. The general form, a reviewer that weighs negative evidence, is what the filing contract and the precedence paragraph already tested. |
| (d), as it bears on direction: 20 of 27 literal departures merge unchanged | **stands; it is mostly attention** | All 7 literal departures that changed or went did so inside a declaration that a round-1 ask rewrote, removed or covered ("similar below"), or that called a declaration an ask removed. Survival: 17 of 20 where no comment was near, 3 of 7 where one was (one-sided Fisher p = 0.05). |

---

## 1. Already answered? What (e) and (f) restate

| what (e) or (f) proposes | already on disk | what it found |
|---|---|---|
| Rules need an exception (`not_when`) half | Stage G's rubric had the field: 11 of 52 rules carry one, and items were delivered with "the rule's exception if it has one" (`conventions-ceiling-2026-10-04/README.md`, stage G). | +0.000 (Result 5). |
| | `docs/todo/conventions-nature.md` (2026-09-29), the working definition: a convention has a scope, a rationale, a form, "a maturity … and its exceptions". | Open todo; the plan's amendment already notes the plan restated it. |
| | `enforcement-at-departures` RESULTS: "a convention has to be stated with its precedence rules and the maintainers' actual line … checked against what they fixed". The same lesson is in `.claude/rules/mathlib-review.md` (2026-10-16): "a statement that fails that check measures us, not them". | Placement: 85-97% of "departures" were construct error. Primes: two written versions failed calibration (2 and 4 of 6). |
| A reader states a reason not to ask at unasked departures | Enforcement probe, amendments 2-3: readers label survivors `excluded` with categorical grounds ("a docstring explains", "a minor variant", "the file's own precedent"). | The same grounds excluded 4 of 6 primes that maintainers had fixed, twice. The reason-finder fired at real asks. |
| …while finding none at asked places | Stage H Result 6: deciders given four asked and four not-asked examples a rule (and `retrieve`, every example). | Raised 0 of 12 at-ask candidates. AUC 0.56-0.64. Their reasons at the asked places were "a plausible nit, not commonly enforced", "the standard pattern". |
| | Free reviewer, 105 drops at asked places (`docs/questions.md`, "On what grounds does the free reviewer drop a concern"). | Worth or taste 27, plurality or tool count 22, the file's siblings 13. These are the cost and scope-form kinds (f) would find at the 20. |
| | Stage G session notes at the 10 asks only the exact brief reached. | Verified and overrode 8: "Mathlib does not require these". The reviewer wrote its own `not_when`. |
| | `library-knowledge-2026-10-13`. | In 9 of 41 hard asks the local precedent was the PR's form and the maintainer asked against it. |
| A reviewer that may drop only on a stated, checked reason | Filing contract, design G (`docs/dead-ends.md`, 2026-10-13). | 14 of 37 against a line of 16; 4.9 findings a control PR. Closed. |
| | The precedence paragraph, which lists the reasons that do not count (`docs/questions.md`, "Does a paragraph ranking the conventions"). | +0.20 / +0.18 on its own PRs; −0.04 / −0.01 off them. |
| The silence reading itself | Plan amendment 1, R4: 20 decoy `kept` places and 20 unasked-exact, with 10 asked pairs as calibration. Read only if misfiles are under 15%. | Not run. (f) swaps R4's decoy half for the 20 and its 10-pair calibration for 7 places. |
| Signals that might pick the asked places | Stage H Result 6, "untried": the reviewer, the PR's own theme, file-local regularity, adjudication of the unasked departures. | Still untried. (f) skips this list. |

**Verdict on novelty.** (e) restates the enforcement probe's design lesson and the rules-file entry from the same
day, and the field stage G already had. (f) is R4 with a smaller, rule-mismatched calibration and without the
decoy half that round 1 asked for. The *control* half of (f) has been measured four times (stage H deciders,
free-reviewer drops, primes calibration, stage G). Each time, a fluent reader found reasons not to ask at places
maintainers asked. Never measured: whether a *fixed, checkable* set of exception predicates discriminates asked
from unasked departures. §4 puts that in reach.

---

## 2. Does the silence test separate the picture from its rivals?

### 2.1 Who was looking at the 20

| stage H places (step 4) | n | on a PR with no round-1 inline comment by anyone but the author | no round-1 comment within 3 lines of the declaration | changed or gone by merge |
|---|---|---|---|---|
| asked (calibration) | 7 | 0 | 1, plus 1 not locatable* | 5 of 5 followable |
| open literal departures, changed or gone | 7 | 0 | 3** | 7 |
| **open literal departures, unchanged (the 20)** | **20** | **8** | **17** | 0 |
| open looser departures | 15 | 4 | 12 | 6 |
| open conforms | 17 | 11 | 15 | 2 |

\* K010 (`isInitial`) was covered by the "similar below" ask on `isTerminal`; K056 is a `variable` command.
\*\* K013 and K062 (`isInitial`) went with that same "similar below" rewrite. K024 calls
`exists_of_basis_kaehlerDifferential`, which an ask's restructuring removed.

What this says:
- **No literal departure in the sample changed except as a by-product of an ask about something else.** That
  matches the enforcement probe's finding for dot notation ("the only route … is an ask"). Here the route is
  an ask that rewrites the declaration.
- **17 of the 20 are places no round-1 comment came near.** Eight are on four PRs with no inline review comment
  at all (26301, 27054, 36430, 36577). On those, the record shows an approval or "bors merge" and nothing at the
  place. The picture reads that silence as a decision; inattention reads it the same way. Nothing in the record
  tells them apart at these places.
- **The three attended ones are not silence in the plan's sense.**
  - K043 (33879, P100: give the primed variant to the siblings). The maintainer commented *at that
    declaration*, under census P154 (do not add a mere restatement), asking whether it was "an accidental
    duplication". That is the opposite direction to P100's check. It is the one case in the 27 where a
    maintainer's reasoning at a surviving departure is on record. It reads as two census conventions in
    conflict, not as an exception missing from P100.
  - K002 and K004 (26979) sit within 3 lines of grunweg's ask on the next lemma. The same reviewer wrote "But I
    like this change" on the section. That is attention, and a positive verdict nearby.
- **Who wrote the PRs.** 11 of the 20 are on PRs whose author is an active reviewer: joelriou 7 (55 round-1
  review comments on other val1000 PRs), JovanGerb 2 (40), kim-em 1 (32), chrisflav 1 (57). Across val1000,
  human PRs by such authors draw 1.97 asks per 100 added lines, against 3.11 for authors who never review; 60%
  of their PRs draw any ask, against 70% (`author_trust.py`). That PR-level driver is not evidence at the place.
- **The AI-generated PRs, the project's target, are absent.** One of the 20 (K048) is on an AI-flagged PR, and
  that departure was created by removing `private`. #36567 restored `private` three days later, and the joined
  line is then 105 characters, so at HEAD the departure no longer exists.

### 2.2 What each rival predicts, and what (f) would see

| picture or rival | what it says about the 20 | what (f) would observe | does (f) separate it? |
|---|---|---|---|
| The user's picture: a decision on positive and negative evidence | a reason exists at each place, and is absent at asks | a reason at most of the 20 | — |
| Attention and load | nobody weighed 17 of the 20 | a fluent reader still writes a reason; the record says readers do at real asks | **no**: same output |
| One ask covers many places | silence where a sibling ask applies | 0 of the 20 share a rule with an ask on their PR; the 7 literal departures that changed sat in declarations an ask covered | already excluded for these 20, without reading |
| PR-scope norms (not this PR's job; trusted author) | reasons about the PR, not the place | "a follow-up would add the `sUnion` version" — and a later PR did add `isMeagre_biUnion` (#33308, 2026-01-09) | **no**: (f)'s "reason that holds across PRs" accepts it |
| The rules are over-broad paraphrases | the "departure" is not one by the maintainers' line | a reason at every place of an over-broad rule, and at its asks too | **no**: by construction a `not_when` *is* a narrower paraphrase. §4 shows this is measurable without a reader for P084. |

(f) passes under every row whenever the reader is fluent. It fails only through its control, and a control
failure would be blamed on the reader, not the picture.

### 2.3 Can the test fail?

- **The picture counts "a cost" as negative evidence** (auto-memory, 2026-10-14: "an exception, a deliberate
  local deviation, a cost"). "The gain is too small for a review round" fits every unasked nit. It also fits the
  20 census asks under P084, which maintainers did raise. A test cannot fail if the cost is not fixed as an
  observable *before* reading (for example a character difference, or the number of asks already on the PR).
- **Maintainers almost never state the negative half.** In any round on val1000 PRs, 66 of 4,399 inline review
  comments and 11 of 1,355 issue comments by anyone but the author carry a decline phrase ("no need", "fine as
  is", "either is fine", "up to you"; `declines.py`). In round 1 it is 5 of 473 comments that are not asks.
  There is no gold to check a reconstructed reason against, except those 77 comments.

### 2.4 Size, and the control

| rule | in the 20 | asked places in (f)'s control (7) | census asks under the rule on val1000 (reader A; primary, or second where the primary is outside the ten) |
|---|---|---|---|
| P005 finishing tactic | 3 | 0 | 59 |
| P011 existing API | 1 | **5** | 46 |
| P040 term for a short block | 2 | 0 | 22 |
| P048 `variable` | 4 | 0 | 11 |
| P084 line breaks | 4 | 1 | 20 |
| P100 siblings' variant | 4 | 0 | 22 |
| P126 file's spelling | 2 | 0 | 11 |
| P010 unneeded hypothesis | 0 | 1 | 18 |

- **The control is another rule.** Five of seven asked places are P011, which appears once in the 20. No asked
  place exists for P005, P040, P048, P100 or P126. A reason like "a layout nit" would be tested against "use the
  existing API".
- **The control cannot meet R4's own bar.** Even 0 misfiles in 7 leaves a 95% upper bound of 35% (Wilson), so it
  cannot show a rationalisation rate under 15%. That needs about 20 asked places with none misfiled (upper bound
  16%), per rule group. The census holds 11-59 a rule.
- **The sample is seven PRs.** 33879 holds 7 of the 20 and 16 declarations carry the 20 rows. At 10 of 20 the
  Wilson interval is 30-70%; with PR clustering it is wider. The record's noise floor (±12pp at n≈8 for one
  judge) comes on top. Readers of one family count as one reader (`.claude/rules/mathlib-review.md`).

### 2.5 What a falsifiable version needs

1. **Read only where a decision is visible.** Use departures in declarations a maintainer commented on in that
   round, or on PRs small enough that every line was read. Report the unattended ones apart.
2. **Fix the reasons before reading.** Use a closed set of exception predicates, taken from material other than
   the places read: the 77 stated declines, the 11 existing `not_when`, Mathlib's style documents. Each
   predicate must name something checkable at the base, such as a grep count, a character difference, "the line
   was moved, not written by the PR", or the file's own rate. A script or a second blind agent evaluates it.
3. **Use matched positives at size.** Take the census asks under the same rules (the table above), packaged
   exactly as the departures are: the declaration at the round-1 head, the base commit, no comment. Mix them in
   blind.
4. **Add a shuffle control.** A reason written for place A is tested at another place under the same rule. A
   generic reason transfers; a reason drawn from the place does not.
5. **Use two model families.** The local DeepSeek is free.
6. **Pre-register the falsifier.** The picture's place-level negative half is not supported for a rule group if
   the predicates fire at the matched asks at two thirds or more of their rate at the unasked departures. It is
   supported if the gap is 0.3 or more and the rate at asks is 15% or less.

---

## 3. Is it general?

- **A positive result explains seven rules.** The rules present in the 20 hold about 191 census asks under
  primary or second label, about 10% of 1,833. A `not_when` clause for each is the kind of fix "appropriate to a
  small number of asks" that the user asked not to deploy (auto-memory, 2026-10-13).
- **The general form already exists, and it errs.** "Weigh negative evidence before asking" is what the free
  reviewer does now: concluded fine at 65 of 279 session-rows, and named-then-dropped 64. Stage G's reviewer
  supplied its own exceptions at asked places. A design gains only if its exceptions *discriminate* better than
  the reviewer's own, and nothing on record measures that.
- **The direction runs against the goal.** The goal is issue recall (2026-10-07). A negative half removes
  filings. It raises recall only by replacing the reviewer's broad self-made exceptions with narrower true ones.
  Ceiling: the 37 asks the free reviewer named and dropped. The conventions-list reviewer already reaches 15 of
  them, and the filing contract, which refused the reviewer's grounds wholesale, reached 14. That is at most
  about 22 of 93 asks, and only where the dropped ground was a false exception.
- **Used to decide what to file, a `not_when` is selection,** refused since 2026-09-22 ("Any proposal about
  which findings reach a maintainer is selection").
- **What would be general.** A small set of cross-rule kinds of negative evidence (the file's own rate,
  PR-written versus moved code, a contrary convention, as at K043), each measurable for any convention, with its
  discrimination measured on the large labelled set. That is what the falsifiable version in §2.5 would produce.
  The 20 do not.

---

## 4. Untried designs that could explain or remove the gap, ranked by what they would change

| rank | design | cheapest test on disk | what it would change |
|---|---|---|---|
| 1 | **Attention, rewrite and PR budget against place-level negative evidence, at scale, on rules a script can check** (P084 joins, P057 dot notation) | Deterministic. Val1000 round-1 diffs (`compares/` on disk); census asks by path and line; the enforcement probe's `survival.jsonl`/`scope.jsonl`. **First cut run here** (`p084_scale.py`, `p084_match.py`): 1,791 added two-line signatures, 369 joinable (21%) on 155 PRs; P084 asked at 3 (0.8%). Where another census ask sits at the same signature: 2 of 31 (6.5%). Where none does: 1 of 338. Then add PR asks, size, author, AI, and the file's own rate as covariates. | If a place-level predicate (the file's rate, moved versus written) separates asked from unasked beyond PR-level and rewrite variables (pre-register a within-stratum rate ratio of 2 or more), the negative half is real for that rule and a reading has a predicate to test. If not, silence is attention and economy, and (f) would read rationalisations. Here attention lifts P084's rate about twentyfold and still leaves 29 of 31 attended departures unasked: those 29 are where silence is a decision. |
| 2 | **Check each rule against what maintainers themselves write** (the over-broad-paraphrase rival, and the rules file's own instruction) | Suggestion blocks (856 of 1,917 census asks carry one). **Run here for P084** (`maintainer_typed.py`): of 76 two-line signatures maintainers typed in round-1 suggestions, **21 (28%) are joinable**. PR code: 21%. Base library: 11-24% (round 2). | P084 as written ("break only when over 100") is not the maintainers' rule for signatures: they write the "departure" themselves. No silence reading is needed to see that. For the other read and lookup rules the same check is a script. For compile rules, run stage H's checker on a random sample of base declarations (Lean compute, no spend). The rules are rewritten "as held" before any departure share or silence reading, as placement needed. |
| 3 | **The maintainers' stated declines** | 77 comments in any round on val1000 PRs (66 inline, 11 issue) with a decline phrase (`declines.py`). Read by hand, about an hour, or by one reader; code the convention declined and the ground. | The only gold-anchored record of the negative half. It supplies §2.5's codebook. If the grounds are mostly "up to you" or "not worth it", the negative half is economy, not place evidence. |
| 4 | **The silence reading where silence can be read** ((f) done properly) | Attended verified departures: the 29 P084 signatures from rank 1, and the 18 P057 dot-notation survivors on 10 PRs that sit on a change target with an ask (`survival.jsonl`). Matched positives: the census asks under P084 (20) and P057 (49). The §2.5 controls. About 120 places × 2 readers; 3-5M reader tokens at the record's 20-25k a reading, fewer where a script checks the predicates; one family free. | The direct test of (e), on n large enough to read and at places where a decision is visible. |
| 5 | **Revealed preference later in the library** | Script, minutes. **Run here for the 20** (`later_master.py`): 13 identical at HEAD. `isMeagre_biUnion` (the P100 gap at K002/K041) was added by a later PR, #33308. A later generalisation replaced `aesop` by `simp` in K014's proof. K048 dissolved when `private` was restored. Extend to the enforcement probe's 111 survivors. | A gold-free lower bound on "wanted but not asked in this PR", which is the PR-scope rival. |
| 6 | **Author trust and the PR's ask budget** | `author_trust.py`, extended: asks per PR against PR size (does it saturate?), and per-departure rate by author's review activity. | Measures how much of the 5% is a PR-level budget rather than a judgement at the place. The first cut gives a factor of about 0.63 for reviewer-authors. |
| 7 | **Per-reviewer instantiation** | One join, done here: the ten rules are multi-reviewer (P084: 20 asks by 15 reviewers). The eight reviewers on the 20's PRs raise these ten rules in 1 to 18 of their 33-115 census asks each (jcommelin 1 of 41, erdOne 18 of 109). | Low promise for these rules. Listed so it is not re-derived. |
| 8 | **A person adjudicates** | The user reads the 3 attended survivors and a sample of rank 1's 29: "would you want this if a reviewer proposed it?" The adjudication socket exists (`docs/todo/adjudication-rubric.md`). | Tests (e2)'s "no maintainer would want" without a model's rationalisation. |
| 9 | **Currency** (R5, already planned) | As planned. | Orthogonal to these 20. |

**What I would run first: ranks 1 and 2 together, then 3.** They are deterministic, need no model and take
about a day. They reach hundreds of departures for P084 and P057, against 20 on seven PRs. They are the only
designs here that can fail the picture's place-level claim. Rank 2 also carries out the project's own rule:
calibrate a rule on what maintainers do before counting departures with it. Its first cut already shows P084 is
broader than practice. Run (f) only in the form of rank 4, only for rule groups where rank 1 shows a place-level
predicate with signal, and with rank 3's codebook. I would not run (f) as specified.

---

## 5. Smaller findings

- **A defect in `follow.py`.** `blocks()` keys declarations by leaf name and keeps the first, so for
  `IsMeagre.union` (K002, K004, K053) it followed `IsGδ.union` at line 124, not `IsMeagre.union` at line 232
  (`leaf_collisions.py`). Re-checked by full name, `IsMeagre.union` is also unchanged by merge, so no step-1 or
  step-4 number moves. The method can still misfire on any leaf that collides; resolving by full name fixes it.
- **The `aesop` example is not in the sample.** K001 and K062 were rewritten by merge. Of the 20, only K004
  (P040) has a longer candidate, and the auditor judged its "reads no worse" settled by an in-file precedent.
- **Two of the 20 are not stable departures.** K048 vanished when `private` came back (#36567). K002 and K041's
  missing family member was partly supplied later (#33308), with `sUnion` still absent.
- **P084's rule text in the codebook** says a line is broken "when, and only when" it exceeds 100. Maintainers'
  own suggestions break 28% of the two-line signatures they type that would fit.

---

## Corrections

1. RESULTS.md, step 4, "What it says about the 5%", third bullet: "P084 counts every line join that fits in 100
   characters, which base Mathlib does not follow (step 2 corrections)." **Should read:** "P084 counts every line
   join that fits in 100 characters. Base Mathlib leaves 11-24% of two-line signatures joinable in the three areas measured, PR code 21%
   (369 of 1,791 on val1000), and maintainers' own suggestion blocks 28% (21 of 76). As written, the rule is
   broader than the maintainers' practice."
2. Same bullet: "Their literal checks count changes no maintainer would want: P005 counts a longer `aesop` call".
   **Add:** "Neither `aesop` row (K001, K062) is among the 20 unchanged departures: both were rewritten by
   merge. Of the 20, 1 of 8 candidates is longer."
3. Same bullet: "None of the ten has a `not_when` condition (11 of all 52 rules have one)." **Add:** "The rule
   writers were told to write one only where the asks showed one, and saw no unasked places. Four of the five
   `judge` rules have one; stage H took none of them. Among the others, 0 of 10 has p = 0.16."
4. Same bullet: "the 20 literal departures that merged unchanged are the sample on which it can be tested … That
   is the plan's silence test (R4), now with verified departures instead of the decoy places it planned to
   read." **Should read:** "17 of the 20 had no round-1 comment within 3 lines of their declaration, and 8 sit on
   PRs with no inline review comment. Every literal departure that changed did so inside, or by calling, a
   declaration that an ask about something else rewrote or removed. At most three of the 20 show a maintainer at the place, and at
   one (K043) the maintainer's comment there argues the opposite way under another convention. A silence test
   needs places where a decision is visible, matched asked places under the same rules (the 7 calibration places
   are 5 P011), and reasons fixed before reading. It is not run on these 20."
5. Exploratory table: "open, departs by the literal check | 27 | 20 unchanged". **Add a row split:** within 3
   lines of a round-1 comment, 3 of 7 unchanged; not near one, 17 of 20.
6. `docs/questions.md`, the stage H line: "none of the ten rules states when it does not apply". **Add:** "by
   construction: the rules were written from asks alone."
7. `follow.py`: `blocks()` keys by leaf and keeps the first header, so a leaf that collides (here `union`)
   follows the wrong declaration. No number moves on this probe; record the defect, or resolve by full name.
