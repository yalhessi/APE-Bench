# The 5% at its source: results

## Step 1: stage H's places followed to merge (`follow.py`, `follow.jsonl`)

| | n | unchanged | changed | gone | unlocated | no merge in clone | changed or gone, of located |
|---|---|---|---|---|---|---|---|
| asked places (validity) | 6 | 0 | 1 | 3 | 1 | 1 | **4 of 4** |
| unasked places | 199 | 100 | 23 | 22 | 13 | 41 | **45 of 145 = 31%** |
| baseline: other declarations the round-1 diff touched | 14 | 11 | 3 | 0 | 0 | 0 | 3 of 14 = 21% |

By rule, unasked, changed or gone: P005 46%, P011 43%, P254 41%, P040 36%, P048 33%, P084 33%, P126 24%,
P018 20%, P100 19%, P010 18%. By the pinpointer's status: `check` 31%, `departs` 33%.

**Read by the rule.** Validity passes: every asked place on a merged PR was changed or removed. The unasked
places against the baseline read "within 10 points" (31% against 21%), but **the baseline cannot bear the
reading**: the pinpointer flagged most of the declarations each PR touched (on PR 31081's new file, 3 of 3),
so only 14 unflagged touched declarations exist on the 13 merged PRs. What step 1 does establish: **100 of
the 145 located unasked places (69%) reach merge byte-for-byte unchanged**, and no rule has a majority of its
places changed. Whether those 100 are conforming code, places outside the rule, or departures nobody asked
about is step 2's question; "gone" includes renames and moves, so the 31% is an upper bound on fixes.

## Step 2: how many flagged places are departures at all (`score_step2.py`, `readings/R1.jsonl`, `R2.jsonl`)

Two readers, independent, on 60 seeded unasked places and the 6 asked places as blind calibration. Calibration:
R1 4 of 6 (fails the 5-of-6 bar), R2 5 of 6 (passes); both missed the same asked place (H055, P011, read as
conforming). By the pre-registered fallback the headline is read on the items both agree on (59 of 66).

| | departs | conforms | excluded | needs a compile or search | unclear | departs of decided |
|---|---|---|---|---|---|---|
| R1 | 14 | 32 | 7 | 5 | 2 | 26% |
| R2 | 16 | 32 | 4 | 5 | 3 | 31% |
| **both agree** | 13 | 31 | 4 | 4 | 2 | **27%** |

**By the rule: mixed** (27%, just over the 25% line; the 60% line is far). The estimated ask rate per real
departure is 6 / (6 + 0.27 × 199) = **about 10%**, three to four times the 2.9% computed per flagged place.

**By kind of rule the reading is not mixed** (both readers pooled; small per-rule n):

| rules | departs of decided | what it says |
|---|---|---|
| decided by a search (P011 use the existing API, P100 give the siblings the same variant, P126 spell it as the file does, P254 name it like its siblings) | 15% (7 of 46) | flagged places mostly conform |
| decided by a compile (P005 a finishing tactic closes it, P010 drop an unneeded hypothesis, P018 merge consecutive steps, P040 write the block as a term) | 24% (9 of 37), 10 more need a compile | mostly conform where a reader can tell |
| decided by reading the layout (P084 line breaks, P048 shared arguments as `variable`) | 64% (14 of 22) | mostly real departures nobody asked about |

Per rule, the substantive ones read almost all conforming: P010 0 of 10, P254 0 of 16, P011 1 of 6, P100 2 of 12,
P040 2 of 12. The cosmetic ones read mostly departing: P084 10 of 12, P018 6 of 10.

**What it says, with the departures probe beside it.** The "5% of applicable places" was computed over places
where a rule's *situation* occurs. For the substantive rules most such places already do what the rule asks,
so the 5% was mostly conforming code in the denominator, as the user suspected. For the layout rules (line
breaks, `variable` lines, merging steps) the flagged places are mostly real departures and they pass to merge
unasked (step 1: 69% unchanged), as dot notation did. Even counted per real departure, maintainers ask at
about 10%, not 100%; the substantive rules have too few departures in the sample to say how much higher their
own rate is.

Limits: 60 places on 13 PRs; two readers of one model family, one below the calibration bar; 10 compile-rule
places could not be settled without running Lean; rules chosen knowing the probe asks (stage H's own limit).

## Corrections after the adversarial review (2026-10-16; `review2-departures.md`, `review2-synthesis.md` beside the plan)

**A framing leak in step 2's packets.** Each packet showed "what the blind pass noted here", the pinpointer's
note. Every departure both readers agreed on (13 of 13) was one the note had already named; where the note was
neutral they agreed on none (0 of 26). The pinpointer's status was `departs` on the two layout rules only, so the
substantive/layout split may echo the earlier pass rather than measure the code. It also coincides with the
rules' check kind (read, search, compile), which decides both what the pinpointer marked and what a reader
without Lean can verify.

**What changes.**
- **(b) "substantive rules mostly conform": weakened.** On the substantive rules 17 of 29 `conforms` rest on
  something checked, 4 on not finding anything and 7 on "reads no better"; the departure share runs 12-49% by how
  those count. It holds for naming like siblings (P254) and unneeded hypotheses (P010, though the rebuild its
  check needs was not run); it is unsupported for "use the existing API" (P011): H008 was a real departure,
  asked ("similar below") and fixed, and the shared calibration miss H055's asked lemma existed at base.
- **(c) "about 10% per departure": falls as a single number.** The interval is 3.6-23%; the census missed two
  asks (8, not 6); per rule it runs from about 65% (P011) to about 5% (line breaks); 21 places are on an
  AI-generated PR closed unmerged.
- **(a) layout departures merge unasked: weakened** to dot notation and line breaks; line-break "departures"
  break stage G's own rule, which base Mathlib breaks in 11-24% of two-line signatures; `variable` rests on one
  agreed item, merged steps on three uncompiled low-confidence ones.
- **Stands:** the 205 are places where a rule's situation occurs (82 declarations, some under nine rules), not
  departures, so the 2.9% was never a rate per departure.

## Step 3: the same places without the pinpointer's note (`score_step3.py`, `readings/S1.jsonl`, `S2.jsonl`)

Two new readers, the same 66 places, the note removed and nothing else changed. Calibration (7 asked places,
H008 added): **6 of 7 for both readers**, 4 of 4 where the note had named the fix and 2 of 3 where it was neutral
(step 2: 1 of 4 reader labels there). Agreement 53 of 66.

**1. Did departures track the note?** Departs among decided labels on the 59 open places, by the note the place
had in step 2:

| note | with the note (step 2) | without (step 3) | step 3, both agree |
|---|---|---|---|
| named a fix or a contrast (24) | 54% | 68% | 81% (13 of 16) |
| hedged (13) | 9% | 12% | 10% |
| neutral (22) | 3% | 16% | 17% (3 of 18) |

By the pre-registered lines, **neither**: neutral places rose to 16% (the line for "the notes suppressed
departures" was 20%), and the readers, unaided, found departures at most of the places the pinpointer had named
(68%). So the note was mostly informative, the pinpointer's notes were largely right about where departures are,
and it suppressed some departures where it was silent.

**2. Does the rule-kind split survive?** Yes, and it widens: layout rules 86% departing (P084 92%, P048 80%)
against substantive rules 25% (pooled), a 61-point gap (step 2: 45). Per substantive rule: drop an unneeded
hypothesis (P010) 0 of 9, a term instead of a short block (P040) 17%, name like the siblings (P254) 19%, give the
siblings the same variant (P100) 25%, spell as the file does (P126) 31%, a finishing tactic (P005) 36%, merge
steps (P018) 36%, use the existing API (P011) 2 of 4.

**What changes in the read.** The framing leak is measured and small: removing the note did not create the
split. The remaining confound is the one the review named second: substantive rules are decided by a compile or
a search, which these readers could only partly do (no Lean), so "conforms" there is still a reader's judgement;
running each rule's own check at the places is the measurement that would settle it. Within that limit:
substantive rules' flagged places mostly conform (about three quarters), layout rules' mostly depart.

## Step 4: each rule's own check, run with tools (`score_step4.py`, `checks/*.jsonl`, `audit.jsonl`)

All 14 reviewed workspaces built; one checker agent a PR ran each rule's check at its places (248 tool calls,
none undecided). After 7 PRs, two rows showed the checkers generalising a check beyond its wording, so an
audit was pre-registered (PROTOCOL.md, step 4 amendment): one auditor, blind to readers, notes, asked flags and
scores, marked each row against the rule's literal check. It found 50 `literal`, 15 `looser`, 1 `incomplete`.

**Calibration passes under both readings: 6 of 7 asked places depart.** The miss, K023 (use the existing API),
searched the base only; the audit marks it `incomplete`.

**The pre-registered line depends on the reading.** Share of note-free reader `conforms` on open substantive
places where the check finds `departs`:

| reading | S1 | S2 | pooled | by the line |
|---|---|---|---|---|
| strict (audited `looser` counts as conforms) | 8 of 35 | 6 of 29 | **22%** (14 of 64) | mixed |
| the checkers' verdicts as written | 19 of 35 | 13 of 29 | **50%** (32 of 64) | readers were largely not checking |

The rows that decide it are the 15 `looser` ones: all six "merge consecutive steps" (P018) departures use a
combining form the check does not list (`simpa ... using`, `rintro`, a rewrite replacing `simp` or `aesop`); five
of seven "a term for a short block" (P040) departures leave the check's "reads no worse" unsettled; and four
single rows (K016, K026, K027, K030) rest on a contested reference spelling or a one-line gain. In the other
direction, under the strict reading 7 reader `departs` labels meet a check `conforms`; under the checkers'
reading none do.

**Departure share, open places** (layout: 11 of 11 under both readings):

| rule | strict | as written | reader S1 | reader S2 |
|---|---|---|---|---|
| P005 a finishing tactic closes it | 7/7 | 7/7 | 2/6 | 2/5 |
| P010 drop an unneeded hypothesis | 0/5 | 0/5 | 0/5 | 0/4 |
| P011 use the existing API | 1/2 | 2/2 | 1/2 | 1/2 |
| P018 merge consecutive steps | 0/6 | 6/6 | 1/6 | 3/5 |
| P040 a term for a short block | 2/7 | 7/7 | 1/6 | 1/6 |
| P100 give the siblings the same variant | 4/6 | 4/6 | 1/6 | 2/6 |
| P126 spell it as the file does | 2/7 | 3/7 | 2/6 | 2/7 |
| P254 name it like its siblings | 0/8 | 2/8 | 2/8 | 1/8 |
| **substantive, pooled** | **33%** | **65%** | 22% | 28% |

Descriptive, changing no verdict: 10 of 48 departing candidates are longer than the code they replace, 4 of
them among `literal` rows (K001 and K062: the one finishing call that compiled is a hinted `aesop` twice the
length of the proof).

**Exploratory, not pre-registered: what happened to the places by merge** (step 1's outcome joined per place):

| | n | unchanged | changed | gone | not followed |
|---|---|---|---|---|---|
| asked (calibration) | 7 | 0 | 2 | 3 | 2 |
| open, departs by the literal check | 27 | **20** | 5 | 2 | 0 |
| open, departs only under a looser reading | 15 | 9 | 5 | 1 | 0 |
| open, conforms by the check | 17 | 15 | 0 | 2 | 0 |

"Changed" may be an unrelated edit to the declaration, so these are upper bounds on fixes.

**What it says about the 5%.** *Superseded by the corrections after review 3, below; kept as it was told.*
- Step 2-3's explanation, that the 5% was mostly conforming code in the denominator, **holds only for the
  substantive rules, and only under the strict reading** (33% depart, against the readers' 22-28%); under the
  checkers' reading they depart at 65%. **Over all ten rules it does not hold:** the layout places all depart,
  so under the strict reading 46% of the 59 open places depart (27), under the checkers' 71% (42). The ask
  rate per departure is then 6.2% or 4.1% by step 2's formula, 8.2% or 5.4% with the census's two missed
  asks. Either way it stays near 5%, not the 10% step 2 estimated.
- So, read literally, these ten rules are broken at about half the places their situation occurs, and three
  quarters of those breaks reach merge unchanged. If the rules as written were the maintainers' rules, the
  user's objection would stand: a library is not kept coherent by rules enforced one time in twenty.
- **What the record does show is that the rules as written carry no exceptions.** None of the ten has a
  `not_when` condition (11 of all 52 rules have one). Their literal checks count changes no maintainer would
  want: P005 counts a longer `aesop` call; P084 counts every line join that fits in 100 characters, which base
  Mathlib does not follow (step 2 corrections). On the user's picture, maintainers decide on positive *and*
  negative evidence, and the rules as written encode only the positive half. That is a hypothesis this step
  makes sharp, not one it tests: the 20 literal departures that merged unchanged are the sample on which it
  can be tested. The test is whether a blind reader, given the place and the code around it, can state a
  reason not to ask that holds across PRs, while not finding one at the asked places. That is the plan's
  silence test (R4), now with verified departures instead of the decoy places it planned to read.

Limits: 59 open places on 14 PRs, 2 to 8 per rule; one checker a place and one auditor, all of one model
family; at most six candidate edits a place, so a `conforms` on a compile rule is "none of six compiled";
searches at the base, not recent master (K023); the merge cross is exploratory and "changed" is not "fixed".

## Corrections after adversarial review 3 (2026-10-17; `review3-measurement.md`, `review3-inference.md`, `review3-direction.md` beside the plan)

Three reviewers: one re-ran 28 compiles with negative controls, the searches and the line measurements, and
re-audited every departure before reading the audit; one re-derived the arithmetic, the merge cross and every
comment on the 16 PRs; one read the record for closed work and ran the cheapest tests on disk.

**The rows reproduce.** Every literal departure re-runs, except K002 and K041 (a missing `IsMeagre` sUnion or
biUnion lemma counted as a sibling's variant), which the re-audit calls contested. The re-audit agrees with the
audit on 44 of 48 departures: it also calls K015 and K053 literal, since P018's `required` text names
`simpa ... using`. All step-4 arithmetic reproduces exactly.

**What changes.**
- **Calibration, 6 of 7: the count stands; the miss is misdescribed.** K023's asked fix is one step,
  `update_eq_self`, a lemma at the base, and it compiles. The check looked for a replacement of the whole
  declaration. The audit's "recent master not searched" is wrong. Calibration only tests that the check finds
  known departures (5 of the 7 are P011); it cannot catch a check that over-calls.
- **The pre-registered line can fall in any region.** Strict 22% (14 of 64) has a per-place interval of 11-37%;
  with K015 and K053 literal it is 23%; without the four literal departures whose fix is longer than the code it is
  11%. P040's "reads no worse" rows decide more of it (8 cells) than P018's merges (5). And the two labels answer
  different questions: a reader says whether a maintainer would ask, the check whether the literal check passes.
  Of the 14 strict cells, 9 are readers predicting the check wrongly and 5 are a different reading or a judgement.
- **"Stays near 5%, not the 10%" falls.** The intervals hold 10%: with 8 asks the strict rate is 6.3-11.9%; over
  PRs, 2.3-12.6% strict and 1.6-7.9% as written. The census counts only round-1 asks filed under the same entry,
  and on these 16 PRs it caught 6 of the 12 round-1 asks at the places. Counting the other 6 and five later-round
  asks the rate is 8-17% (3.5-34%). Census-wide, over 973 PRs, it is 3-5%. Six of the ten rules had no round-1
  ask on these PRs; P011 runs 24-38%. The open places sit on 11 PRs (37 declarations), not 14, and the five
  most-reviewed PRs hold 57 of the 199 unasked places but 5 of the 59 sampled.
- **"Broken at about half the places" is half selection.** The pinpointer listed P048 and P084 places only where
  the code departs, so their 11 of 11 is how the places were picked. The substantive rules' checks find a
  departure at 33-65% of the places their situation occurs.
- **The merge cross is stronger than stated.** 23 of 27 literal departures are still there at merge, 20 byte for
  byte; K012, K013 and K024 changed elsewhere in the declaration and kept the departure. None moved toward its own
  rule: the four that went were removed by asks under other rules. All five followable asked places were fixed as
  asked. No departure was fixed elsewhere in the PR.
- **Survival is mostly attention.** 17 of the 20 unchanged had no round-1 comment within 3 lines of the
  declaration, and 8 sit on PRs with no inline review at all. Departures survived at 17 of 20 where no comment was
  near and 3 of 7 where one was (one-sided p = 0.05). Round-1 asks a PR grow 2.5 times as PR size grows 15 times:
  an ask budget alone accounts for a rate this low.
- **The "no exceptions" explanation falls as evidence.** Stage G's writers saw only asks for a convention, so they
  could not write a `not_when` from their inputs; drawing ten rules without one has p = 0.16. Rules that have one
  are asked no more often (1.5% against 1.7% a flagged place). "Changes no maintainer would want" rests on K001 and
  K062, both rewritten by merge; among the 20, one of eight candidates is longer.
- **The line-break claim was wrong, and the truth is sharper.** Base Mathlib follows P084's joins in 76-89% of
  two-line signatures. But maintainers' own round-1 suggestion blocks leave 21 of 76 two-line signatures (28%)
  joinable, and PR code 21% (369 of 1,791). So P084 as written is broader than what maintainers themselves write:
  the rule text departs, not the maintainers.
- **The silence test on the 20 is dropped as specified.** No maintainer decision is visible at 17 of them; the
  control is mostly another rule (5 of 7 asked places are P011, which appears once in the 20); 7 control places
  cannot meet the plan's 15% misfile bar; and the picture counts a cost as a reason, so a fluent reader always
  finds one. A positive result would add exception clauses to seven rules, which is selection, and the general
  form (a reviewer that weighs reasons not to ask) was tried as the filing contract.

**The read, at the altitude the reviews leave.** By the rules' own checks, substantive situations depart at a
third to two thirds of places; the departures persist to merge; the asked ones are fixed as asked. The low rate
is what the census counts (round-1, same-entry asks, about half of the asks at these places) and what maintainers
look at (departures survive where no maintainer commented), not evidence that a rule fails where it was weighed.
At least one rule as written (line breaks) is broader than maintainers' own code. Whether maintainers weigh
negative evidence at places they did look at is untested. Provisional: 59 places, one model family checking.

**Next, ranked by the direction review** (deterministic first, no model):
1. Separate attention and the PR's ask budget from evidence at the place, at scale, on rules a script can check.
   A first cut on P084 over 973 PRs: 369 departures, 3 asked; 2 of 31 asked where another ask sits at the same
   signature, 1 of 338 where none does. The 29 attended-but-unasked places are where silence is a decision.
2. Check each rule against code maintainers write themselves (suggestion blocks), as done above for P084.
3. Read the 77 comments in which maintainers decline something ("no need", "fine as is"): the only written record
   of the negative half.

**Defects recorded.** `follow.py` follows a declaration by its last name component, so `IsMeagre.union` can match
`IsGδ.union` in the same file; no number moves here. A checker or the auditor could have read commit messages, the
results tree or the clone; nothing blocked it, and the derivations that differ from the merged code argue against
copying. The 20 unchanged departures are 18 distinct omissions (two pairs double-count).
