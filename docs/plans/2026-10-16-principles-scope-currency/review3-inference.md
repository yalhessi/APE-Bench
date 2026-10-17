# Adversarial review 3, part 2: does the step-4 read follow from its numbers? (2026-10-17)

**Under attack.** Claims (c), (d) and (e) of the step-4 read of
`results/pr_review_v5/probes/stage-h-departures-2026-10-16/` (RESULTS.md, last section), and the wording of that
section. The check rows and the audit are taken as given; no Lean was run.

**Read.** PROTOCOL.md with its step-4 amendment, RESULTS.md, `build_step2.py`, `follow.py`, `score_step4.py`,
`auditor_prompt.md`, `step3_items.jsonl`, `checks/*.jsonl`, `audit.jsonl`, `follow.jsonl`; stage G and stage H
in `conventions-ceiling-2026-10-04/README.md`, its `rules.json`, `rule_writer_rubric.md`,
`build_rule_writer_folders.py`, `stage_h.py`, `census_rates.json`, `census_sample.json`, `census_pinpoints/`;
every review, issue and review-body comment in the PR store for all 16 stage-H PRs; the census labels for
those PRs; `review2-departures.md` and `review2-synthesis.md` (not repeated here); plan test 4 and R4.

**Computed.** Scripts and outputs in
`/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/a142d916-dd29-4521-a449-00e1db067b18/scratchpad/rev3/infer/`:

| script | what it computes |
|---|---|
| `join.py` → `joined.jsonl` | items × checks × audit × step-1 outcome × note-free readers; the merge-cross table |
| `population.py` | the 199 unasked places against the 59 sampled, by rule, PR, status, AI PR, merge |
| `rate.py` | the ask rate per departure under re-weightings, ask counts and populations; cluster bootstrap over PRs |
| `census_level.py` | a cross-check from the ten rules' 259 census ask-rule pairs over 973 PRs, not from 6 asks |
| `merge_cross.py` | head against merged with `follow.py`'s own `apply_patch` and `blocks`, byte and normalised |
| `prstore.py` → `prstore*.txt` | every human comment on the 16 PRs, for reading (bodies stay in scratch) |
| `attention.py` | maintainer code comments per PR against places and sampled places |
| `writers.py`, `notwhen_rates.py` | who wrote `not_when`; ask rate per flagged place with and without it, all 52 rules |
| `p084_base.py` | base practice for P084 over Mathlib at the clone's HEAD |
| `ask_budget.py` | round-1 census asks per PR against PR size |

Everything in RESULTS.md's step-4 arithmetic reproduces: 27 of 59 (46%) and 42 of 59 (71%); 16 of 48 and 31 of
48 substantive; 6.2%, 4.1%, 8.2%, 5.4%; the merge table to the cell.

## Verdicts

| claim | verdict | one line |
|---|---|---|
| (c) ask rate per departure 4-8%, "stays near 5%, not the 10%" | **weakened** | The arithmetic is right and a census-wide cross-check agrees (3-5%). But the 6-ask interval is 2-13%, which holds 10%. Counting the asks maintainers made at these places under other census entries (12 in round 1) or in later rounds (17) gives 8-17%. The pooled rate mixes six rules with no round-1 ask with two asked at 24-100%. |
| (d) 20 of 27 literal departures reach merge unchanged; every followable asked place changed | **stands, and is stronger than stated; weak as a test sample** | All 20 are byte-identical. None of the 7 changed or gone moved toward its rule, and all 5 followable asked places were fixed as asked. None of the 20 was raised in any round. But 8 of the 20 sit on PRs with no maintainer code comment, and 7 on one PR. |
| (e) the ten rules lack `not_when`, so they encode only the positive half | **weakened; its P084 support falls** | Stage G's writers could write an exception only from the rule's sentence and four asks for it, so the gap is built in. Over 52 rules, having a `not_when` does not go with a higher ask rate (1.5% vs 1.7% per flagged place). "Changes no maintainer would want" is shown for 2 rows on one PR. Base Mathlib follows the kinds of line joins the six P084 departures rest on at 82-88%. Two alternatives the data already supports are an ask budget per PR and the round and filing of asks. |

---

## 1. The ask rate per departure (c)

### 1.1 Is the 59-place sample representative of the 199?

`build_step2.py` drew from the 145 *located* unasked places on merged PRs, at most 8 per rule, then 60 at
random. Steps 3 and 4 kept 59 open places on **11 PRs and 37 declarations**. RESULTS says 14 PRs; the other
three PRs carry only calibration places.

| stratum | 199 unasked | 59 sampled | effect on the rate (strict / as written) |
|---|---|---|---|
| reported | | | 6.2% / 4.1% |
| re-weighted to the 199's rule mix (sampling ran 0.28 of located places for P100, P126, P254 to 0.83 for P048) | | | 6.5% / 4.4% |
| re-weighted by PR (PRs with sampled places only) | | | 5.9% / 3.9% |
| on AI-authored PRs (30244, 36430, 37341) | 32 (16%) | 3 (5%) | excluded: 7.2% / 4.8% |
| on PRs not merged in the clone (30244, 28926 closed; 37190 merged after HEAD) | 41 | 0 | closed ones excluded: 7.0% / 4.6% |
| unlocated by `follow.py` (docstrings, `variable` commands, sections) | 13 | 0 | never sampled |
| on the 5 PRs with no sampled place (37190, 30244, 28678, 28926, 30652) | 49 | 0 | `d` imputed |
| on PRs with no maintainer code comment (26301, 27054, 36430, 36577, 37052, 37341) | 55 (28%) | 23 (39%) | excluded: 7.3% / 4.8% |
| on the 5 PRs with five or more maintainer code comments (32598, 37190, 28678, 30244, 30652) | 57 (29%) | 5 (8%) | can't be re-weighted: four of them have no sampled place |

The sample over-represents lightly reviewed PRs and under-represents the reviewed ones. Every re-weighting the
data allows moves the rate by at most one point. **What moves it is the numerator.**

### 1.2 How many of the 205 places were actually asked?

The census counts a place as asked only if a **round-1** ask filed under the **same census entry** sits at it
(stage H's limits, README: "a later-round ask counts as not asked"). I read every comment on the 16 PRs:

| step | asks at the places | what they are |
|---|---|---|
| census, as used | 6 | |
| + review 2's compressed asks | 8 | "similar below" (35140 `isInitial`, P011); "The same for the other lemma" (37190, P084) |
| + round-1 asks filed under another census entry, on the place's own subject | **12** | 32598 `subsingletonEquivDep` P254: the `Dep` naming ask ("conforms to the naming convention", filed P220). 28678 `WellFoundedLT.ulift` P254: "define it in the ULift namespace" (filed P164/P213), applied at merge. 33879 `mk₂` P126: "`@[reducible]` instead of `abbrev`?" (filed P351), applied. 32598 K065 P005: v1378's `update_eq_self` replaces exactly K065's manual goal, applied |
| + later rounds, clear cases | **17** | 35140 `variable` line P126 (robin-carlier's suggestion makes `[Category* D]` match `[Category* C]`); 37190 P254 on both lemmas (j-loreaux's renames); 37190 P126 on both (j-loreaux's suggestions respell `Finset.card` as `#`) |
| + later rounds, arguable | about 25 | 28678 P040 (`by apply` replaced by a term after "Not sure why `by apply`"); 37190 P005, P011, P018 and P040 at the two proofs j-loreaux rewrote; 30652's unasked P010 instance (the asked `variable` block "applies to 1 instance only") |

The stated method gives 6. Counting what maintainers raised at these places, by the place's own rule, gives at
least 12 in round 1 and 17 in all.

### 1.3 The rate, as an interval

Cluster bootstrap over the 16 PRs, with asks, unasked places and the departure share resampled together
(`rate.py`, 20,000 draws):

| asks | strict reading | as written |
|---|---|---|
| 6 (as told) | 6.2% (95%: 2.3-12.6%) | 4.1% (1.6-7.9%) |
| 8 | 8.2% (2.9-16.1%) | 5.4% (2.0-10.1%) |
| 12, round 1 | 12.2% (5.2-25.1%) | 8.1% (3.5-15.2%) |
| 17, any round | 16.8% (6.1-33.8%) | 11.3% (4.2-22.0%) |
| 17, without AI, closed and no-comment PRs | 23.4% | 16.0% |

The strict reading also depends on how the auditor read open lists. It read P005's tactic list and P126's
construct list as examples (K001, K062 `aesop`; K054 colon placement; K060 parentheses), but P018's list as
closed, though P018's own `required` names `simpa ... using`. Reading all lists as closed moves the strict share
to 39%; reading all as open moves it to 56%. That is 5.1-7.2% at 6 asks.

**The point for (c).** RESULTS calls the rate "near 5%, not the 10% step 2 estimated". With 6 asks the interval
contains 10%. With 8 asks the strict point is 8%. So the step-2 and step-4 estimates are not shown to differ.

### 1.4 What supports "near 5%"

A census-level cross-check that does not rest on 6 asks (`census_level.py`). It takes the ten rules' census asks
over the 973 PRs and divides them by the departures expected over those PRs: places flagged per census PR,
times the step-4 departure share of each rule. Round-1, same-entry asks run **4.8% (strict) and 3.1% (as
written) per departure**. RESULTS could cite it.

It shares two limits with the 6:
- it counts round 1 only;
- it counts filing under the same entry, which on these 16 PRs caught 6 of the 12 round-1 asks at the places.

### 1.5 The pooled number is a mixture

Per rule, from the 6 asks and the checks' departure shares (`rate.py`):
- **No round-1 ask on these 16 PRs at all:** P005, P018, P040, P048, P100, P126, P254. That is 0% per departure,
  on 20, 0-15, 4-15, 6, 17, 10-15 and 0-8 estimated departures.
- **P011:** 24-38%.
- **P010:** 1 ask against 0 estimated unasked departures (the check found 0 of 5).
- **P084:** 4%.

With 17 asks, P126 rises to 24-32% and P254 to 37% or more. "One in twenty" therefore describes no rule. It
describes the pool.

**Verdict (c): weakened.** The formula is applied correctly, and on the census's own definition a 3-8% rate is
supported. "Stays near 5%, not the 10%" is not: the intervals overlap. Counting the asks maintainers made at these
places, by other filings or in later rounds, the rate is 8-17% (interval 3.5-34%). The sample under-represents
the reviewed PRs where those asks were made.

---

## 2. The merge cross (d)

### 2.1 Unchanged and changed, re-derived

`merge_cross.py` uses `follow.py`'s `apply_patch` and `blocks` and also compares raw blocks:
- **All 20 "unchanged" literal departures are byte-identical** from the declaration line to the next top-level
  line.
- **Fixes elsewhere were checked at the merge commit:**
  - P100 K002 and K041: no `IsMeagre` biUnion or sUnion at merge.
  - P100 K017: `Functor.map_hom_inv_id_app` still has no `to_dual`.
  - P100 K043: `homMk₃_app_two` still uses `⟨2, by valid⟩`.
  - P126 K054: the colon still starts line 238.
  - P126 K060: `(D R S)` is still parenthesised.
  - P084 K059: the attribute is still broken over two lines.

  None was fixed elsewhere.

**The 7 changed or gone.** None moved toward its own rule.

| item | rule | what changed |
|---|---|---|
| K001, K062 | P005 | the uniqueness goal disappeared with the asked P011 rewrite |
| K012 | P048 | `{F : C ⥤ D}` is still repeated; only the body changed |
| K013 | P084 | the break before `IsInitial F :=` is kept by the maintainer's own suggestion |
| K024 | P005 | `map_inj` and `hbij` are unchanged; the edit is erdOne's generalisation |
| K044 | P084 | declaration removed by a generalisation ask (census P004) |
| K065 | P005 | goal replaced by `update_eq_self`, the round-1 ask v1378 |

So 23 of 27 literal departures reach merge with the departure intact: the 20 plus K012, K013 and K024. The
other 4 were removed by asks under other rules: K001 and K062 by the asked P011 rewrite, K044 by a
generalisation ask, and K065 by the asked lemma at the same goal.

**The 5 followable asked places were all fixed as asked:**
- K010 and K050 became the suggested `evaluationJointlyReflects…` proofs;
- K023 was renamed, and `update_eq_self` was applied;
- K034 is now a nameless `ULift` instance by `InvImage.wf`;
- K057 was removed.

### 2.2 Were any of the 20 raised somewhere?

**0 of 20**, in any round, on any line, including general comments. One, K043 (P100,
`homMk₂_app_two'`), had a maintainer comment on the same declaration about another thing: "accidental
duplication or do we need both" (chrisflav). The author gave a `dsimp` reason, and the maintainer accepted it.

Where the 20 sit, from `attention.py`:

| PR | maintainer code comments | of the 20 |
|---|---|---|
| 33879 | 2 | 7 |
| 26979 | 4 | 4 |
| 31081 | 2 | 1 |
| 26301, 27054, 36430, 36577 | **0** | **8** |

**Verdict (d): stands as a description, and is stronger than stated.** RESULTS says "three quarters"; the
number is 23 of 27 with the departure intact, and the other 4 went with asks under other rules. As **the sample for the silence test** it is weak:
- 8 of the 20 are on PRs where no maintainer commented on any code, so their silence is not a decision about
  the place;
- 7 of the remaining 12 are on one PR.

Plan R4 already has `raised_later_round` and `raised_elsewhere_on_pr`. For these 20 both are 0. For the
population they are not (§1.2).

---

## 3. The explanation (e)

### 3.1 "None of the ten has `not_when`" is a product of how stage G wrote rules

`rule_writer_rubric.md` limits `not_when` to a case "if the sentence or the examples show one … Do not
invent one". The examples were up to four census asks *for* the convention. No writer saw a place where
maintainers declined. So every stage-G rule encodes only the positive half by construction, with or without a
`not_when`.

`not_when` is not a writer artefact (`writers.py`): writer 1 filled 6 of 26 and writer 2 filled 5 of 26. Its
pattern is this:
- it sits on 4 of the 5 `judge` rules, and stage H's ten include none;
- 7 of the 11 are decoys.

Ten rules with none of the 11 is a 7% draw from all 52 and a 16% draw from the 47 non-judge rules.

### 3.2 The cheapest test on disk

The test is the ask rate per flagged place, for all 52 rules, computed exactly as stage H computed
`census_rates.json`. The script reproduces the ten published indices. It takes census asks over 973 PRs and the
blind pinpointer's flags on the same 16 census PRs (`notwhen_rates.py`):

| | rules | asks | flags | pooled ask rate per flag | median index |
|---|---|---|---|---|---|
| with `not_when` | 11 | 98 | 105 | **1.53%** | 0.0172 |
| without | 41 | 474 | 453 | **1.72%** | 0.0143 |

The medians differ with a one-sided permutation p of 0.35. A rule whose writer saw an exception is not asked any
more often per place where it fires. This does not refute the hypothesis, because stage G's exceptions came from
asks and not from declined places. It does mean the absence of `not_when` is not evidence for it.

### 3.3 "P084 counts every line join that fits in 100, which base Mathlib does not follow": falls for its own rows

The cited source (step 2's corrections: base breaks 11-24% of two-line signatures) shows base mostly *does*
follow the whole-line join. I measured three readings over the whole of Mathlib at the clone's HEAD
(`p084_base.py`; 242,023 top-level signatures):

| reading of P084 | base signatures that depart |
|---|---|
| whole join: signature fits in 100 but is broken | **11.7%** of signatures that fit (9-16% by area) |
| binder fill: next line's leading binder fits on the line above (not after `:`) | **17-18%** of multi-line signatures |
| word fill (the check read word by word): any next leading binder **or word** fits | **72-83%** of multi-line signatures |

Base Mathlib does not follow the word-level reading: it keeps the statement on its own line after the colon.
One maintainer stated that exception on 37190: "maximally use whitespace" but "keep the conclusion … on a
single line". That is a real negative half, stated by a maintainer, and it supports (e) for word-level fill.

But **none of the six P084 literal departures rests on word-level signature fill**:
- whole join: K009, K013, K059, K063;
- leading binder: K044, K048.

Those are the forms base follows at 82-88%. For these six, "base does not follow" is false. They are
departures from majority practice that went unasked, four of them on PRs with no code comment.

### 3.4 "Changes no maintainer would want": how many rows?

- **P005:** shown for 2 of 7 literal rows (K001 and K062: one PR, one proof shape, both replaced anyway by the
  asked rewrite). Of the others:
  - four are shorter one-call replacements (K003 is 55 against 98 characters), the shape P005's 60 census
    asks request;
  - one, K065, is a goal the maintainer asked to shorten in round 1.
- **P040:** K004 is longer by 8 characters.
- **Overall:** 4 of the 17 literal departing rows with a candidate are longer. The six P084 rows are the forms
  base follows (§3.3).

So it is shown for 2-3 rows. It is not shown for "their literal checks" in general.

### 3.5 Other explanations of a persistent ~5%, and what the data on disk separates

| explanation | evidence on disk | separable now? |
|---|---|---|
| **Ask budget per PR.** Reviewers write a few asks whatever the departures | Census round-1 asks per PR: 1.18 in the smallest size quartile (median 3 targets), 2.96 in the largest (median 46): 15× the targets, 2.5× the asks. 34% of PRs get none. The ten rules alone give 6-9 departures per PR (12.8 flags × 0.46-0.71) against 1.9 asks per PR on all ~440 entries, 14% of them on these ten. That arithmetic alone yields about 3-5% | **Yes, at PR level** (`ask_budget.py`). It predicts the 5% with or without exceptions; it does not say *which* places get the few asks |
| **Round 1 and census filing** | 6 → 12 (same round, other entry) → 17 (later rounds) | **Yes**, done here (§1.2) |
| **One ask covers several places** | 2 of the 6 asked comments cover a second place | Yes (review 2) |
| **No review at all** | 6 of 16 PRs, 55 of 199 places, 8 of the 20: no maintainer code comment | Yes |
| **Local precedent**: the PR writes what its file writes | K008 and K011: the file's older lemmas repeat the same binders. `questions.md` (enforcement probe): where the file has a practice, it uses the departure form in 85% | Measurable per place at base; not done |
| **PR scope** (chores) | K048 (36430 removes `private`, freeing 8 characters), K017 and K059 (36577, a `to_dual` refactor) | Partly, from titles and the diff |
| **AI-authored PRs** | 3 of 16; excluding them moves 6.2% to 7.2% | Yes; small |
| **Decoy selection** (P084, P126) | excluding them gives 7.8% / 4.6% | Yes; small |
| **The check over-broad / stage G's paraphrase** | P005 hinted `aesop` (2 rows); P084 word fill (72-83% of base, but no sampled row rests on it); the audit's open-list calls | Partly |
| **Missing negative evidence (RESULTS' hypothesis)** | the maintainer-stated P084 exception; K043's accepted reason | Only by the silence test |

**Verdict (e): weakened.** As a hypothesis to test it remains reasonable. The evidence RESULTS gives for it does
not hold:
- the missing `not_when` is built in by stage G's rubric;
- having one does not predict asks;
- the P084 citation is contradicted for the six rows;
- "no maintainer would want" rests on two rows.

The ask budget explains the size of the rate from data already on disk. The negative-evidence hypothesis can
still explain *which* places get the few asks. RESULTS should name both.

---

## 4. Wording, line by line (step-4 section)

| sentence | problem |
|---|---|
| "10 of 48 departing candidates are longer" | 17 of the 48 departing rows have no candidate (`longer` null). It is 10 of 31 |
| "'Changed' may be an unrelated edit … upper bounds on fixes" | True. The measured answer is 0 of 5 changed toward the rule; RESULTS can say it |
| "Either way it stays near 5%, not the 10% step 2 estimated" | The intervals overlap. It holds only for round-1, same-entry asks (§1.3-1.4) |
| "these ten rules are broken at about half the places their situation occurs" | For P048 and P084 the pinpointer lists a place *only where the code departs*, so 11 of 11 is the selection, not a finding. The eight other rules' places are trigger places, at 33-65% departing. "Broken" overstates "a literal check finds a candidate" |
| "three quarters of those breaks reach merge unchanged" | Understated: 23 of 27 reach merge with the departure intact; the other 4 went with asks under other rules |
| "a library is not kept coherent by rules enforced one time in twenty" | "Enforced" is used to mean "asked in round 1 under the same entry". Authors conform unasked at 35-67% of substantive places, and base follows the counted line-break forms at 82-88%. A rhetorical inference with no measurement behind it |
| "What the record does show is that the rules as written carry no exceptions" | The record shows that stage G's writers had no way to write one (§3.1) |
| "P084 counts every line join that fits in 100 characters, which base Mathlib does not follow" | Contradicted for the six departures counted (§3.3); the cited 11-24% shows base mostly follows it |
| "the 20 literal departures … are the sample on which it can be tested" | 8 are on PRs with no code review (§2.2) |
| "now with verified departures" | Verified by the literal checks this paragraph says over-count. "Departures by the literal check" is accurate |
| "Limits: 59 open places on 14 PRs" | 11 PRs, 37 declarations |

## Not checked

- Whether the 37190 later-round suggestions were applied as written; they count as asks either way.
- Whether the census's other 1,800 asks show the same 2-to-1 under-filing (§1.4). The 16 PRs suggest the
  census-level rate may be low by up to that factor for naming and spelling rules.
- Docstring line-fill in base Mathlib (K013, K044 also rest partly on docstrings).
- `p084_base.py` reads signatures up to the first `:=`, `where` or `|`, over at most 12 lines. It skips a
  binder default `:= by …` and attributes, and counts Unicode code points as characters.

## Corrections

1. "Either way it stays near 5%, not the 10% step 2 estimated." → "On round-1 asks filed under the same census
   entry it is 4-8%, with intervals over PRs of 2.3-12.6% (strict) and 1.6-7.9% (as written) that contain step
   2's 10%; a census-wide check over 973 PRs gives 3-5%. Counting the four further round-1 asks at these places
   filed under other entries (12) and five later-round asks (17), it is 8-17% (3.5-34%). Six of the ten rules
   had no round-1 ask on these PRs; P010 and P011 carry the asks."
2. "these ten rules are broken at about half the places their situation occurs" → "the eight substantive rules'
   checks find a departure at 33-65% of the places their trigger fires; the two read rules' places are
   departures by construction, so the pooled 46-71% is not a rate over situations."
3. "and three quarters of those breaks reach merge unchanged" → "and 23 of the 27 reach merge with the departure
   intact (20 byte-identical, 3 inside rewritten declarations); the other 4 went with asks under other rules,
   none changed toward its own rule".
4. "If the rules as written were the maintainers' rules, the user's objection would stand: a library is not kept
   coherent by rules enforced one time in twenty." → delete, or "One round-1 ask in 6-25 departures is not the
   enforcement rate: authors conform unasked at 35-67% of substantive places."
5. "What the record does show is that the rules as written carry no exceptions. None of the ten has a `not_when`
   condition (11 of all 52 rules have one)." → "None of the ten has a `not_when`. Stage G's writers could write
   one only from the sentence and four asks for the convention, and over all 52 rules having one does not go
   with a higher ask rate per flagged place (1.5% against 1.7%)."
6. "P005 counts a longer `aesop` call; P084 counts every line join that fits in 100 characters, which base
   Mathlib does not follow (step 2 corrections)." → "P005 counts a hinted `aesop` twice the proof's length (2 of
   7 P005 departures, one PR). P084 read word by word counts the break after a signature's colon, which Mathlib
   keeps in 72-83% of multi-line signatures. But the six P084 departures here are whole-line joins or binder
   fills, which base Mathlib follows in 82-88% of signatures."
7. "the 20 literal departures that merged unchanged are the sample on which it can be tested" → "… 12 of them on
   PRs where a maintainer commented on code (7 on one PR); 8 sit on PRs with no code review, where silence is
   not a decision. None of the 20 was raised in any round."
8. "now with verified departures" → "now with departures by the rules' literal checks".
9. Add: "The ask budget explains the size: round-1 asks per PR grow 2.5× while PR size grows 15×, and the ten
   rules alone give 6-9 departures a PR against 1.9 asks a PR on all entries. The negative-evidence hypothesis
   would explain which places get those asks."
10. "10 of 48 departing candidates are longer" → "10 of the 31 departing rows with a candidate are longer".
11. "Limits: 59 open places on 14 PRs" → "59 open places on 11 PRs (37 declarations)". Add to the limits: "asks
    are round-1 and same-entry; the sample holds 5 of the 57 unasked places on the five most-reviewed PRs".
