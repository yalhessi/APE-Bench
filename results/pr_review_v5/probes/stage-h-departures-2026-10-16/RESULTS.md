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
