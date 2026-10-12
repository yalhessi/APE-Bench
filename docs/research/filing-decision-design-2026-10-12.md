# The filing decision: knowledge as authority, not as facts. A general design from the per-ask reading of P14 and D12 (2026-10-12; draft for adversarial review)

**Status** — the first draft (§0–§8) was put through an adversarial round on 2026-10-12 (four
reviewers: the record, the reading's mechanics, generality and falsifiability, and an advocate for a
different design; `filing-decision-design-2026-10-12/`). **§9–§12 are what survived it.** The draft is
kept verbatim above so the next session does not re-derive it. Written from one reading programme
(`results/pr_review_v5/probes/ask-reading-2026-10-12/`, six readers, one per batch, counts provisional),
the one reviewer table (`docs/research/beating-solo-2026-10.md`) and the record. Nothing built, nothing
run. Branch `ask-reading`.

**The request** (the user, 2026-10-12): *"We need to review every ask in P14 and D12 with the DeepSeek
and DeepSeek + AP runs to try and understand better what goes wrong. We are hypothesizing here about
many directions, and some of them are clearly an improvement over the solo reviewer but the
difference they will deliver on actual PRs is minimal (say 1-2 asks). This is partially because we keep
coming up with designs that are far far too narrow in their nature. We jump into investigating
deterministic detectors although it's clear many asks don't have deterministic asks. We need to take
in these runs, the discussion above, and come up with a clear general design that encapsulates as much
as possible. This isn't a design that has too many pieces that apply narrowly, but a design that
clearly navigates knowledge and judgement."*

## 0. The answer in one paragraph

The free reviewer does not miss asks for want of attention (1 of 558 session-rows was at a place it
had not read) and only rarely for want of a fact about the code or the library (15 of the 66 asks it
misses need a mechanism, a direction, an analogue or a construction it did not have). It misses them
at the **filing decision**: at a place it has read, it either never asks the maintainer's question,
because its audit runs its own checklist, or it asks it, often writes the maintainer's exact change
down, and then clears the concern on a ground that is the wrong authority: its own guess about
maintainers, the worth of the change, the file's siblings, the corpus plurality, a tool's threshold,
the brief's form rules, or a check that failed on its own wrong variant. Delivered conventions move it
only where a sentence's example matches the hunk's shape and is asserted as what maintainers ask; they
narrow it, redirect it, or read as endorsement elsewhere. So the general design is not another source
of facts. It is **an explicit authority order for the filing decision, attached to an explicit
question set**: a check that decides outranks the library's current practice (newest form wins over
the file and the plurality), which outranks maintainers' asserted demand, which outranks the
reviewer's own judgement; a failed check on the reviewer's candidate turns the finding into a
question rather than clearing it; and worth, guesses, siblings, pluralities and form rules are not
grounds to clear anything. Every narrow design in the record is one authority or one question of this
structure. What the design cannot settle is volume: it converts dropped concerns into filings, and
how many of those are welcome is unmeasured (demand is at most 5% of applicable places). That
measurement, not another detector, is the next step.

## 1. What the reading found

93 asks on 26 PRs (D12: 47; P14: 46), six DeepSeek-V4.1-Flash sessions each: DX (solo) ×3 and AP (solo
plus about 25 conventions picked from the diff, each with two maintainer comments and a precedence
paragraph) ×3. Outcomes from the one reviewer table's two blind matchers; the reading adds, per
session, the behaviour at the ask's place in the session's own words, the knowledge the miss needed and
where it lives, and what an AP session did with a held convention. Codes in `PROTOCOL.md`, fixed before
any reader ran.

**1.1 Where the miss happens** (session-rows; `aggregate.md` §1):

| | rows | reached | partial | right concern, dropped | checked, read as conforming | attended, concluded fine | asked something else | not attended |
|---|---|---|---|---|---|---|---|---|
| DX | 279 | 95 | 19 | **64** | 17 | **65** | 17 | 1 |
| AP | 279 | 112 | 32 | 41 | 18 | 37 | 39 | 0 |

Of DX's 184 non-reached rows, 81 (44%) are the reviewer naming or checking the maintainer's own concern
and clearing it; 65 (35%) are the place read through the reviewer's own checklist with the ask's
question never arising; 17 asked a different question there. AP moves rows from "concluded fine" to
"asked something else" and to "partial" (a narrower change than the ask), and halves the dropped ones.

**1.2 What the miss needed** (per ask with a miss, DX; §2):

| none | demand | mechanism | direction | api | construction | pr_context | unclear |
|---|---|---|---|---|---|---|---|
| 34 | 14 | 6 | 6 | 2 | 1 | 2 | 1 |

A fact about the code or the library the sessions lacked: 15 of 66 (`mechanism` `to_fun`, `grind
[def]`, `mk_iff`, `variable … in`, a structure's own `mk`; `direction` `coe_` → `toLinearMap_`,
hand-written twins → generators, `def`-with-`∧` → `@[mk_iff] structure`, "tag, don't re-prove" for
`grind`; `api` an analogue; `construction` what a proof uses of a constant). A fact about maintainers,
that they enforce this here: 14. Nothing lacking: 34. The AP section changed no knowledge column in
any batch; the readers' phrase for what it changed is "what counts as asked-for".

**1.3 The grounds on which a named concern was cleared** (§4, §5, verbatim; classified by keyword, 105 K
rows and 35 V rows, overlapping categories): worth / minor / marginal / taste 27; a guess about
maintainers ("maintainer wouldn't reject", "probability … maybe 0.35. Skip it") 22; the corpus
plurality or a tool's count ("`coe_` 48 of 124 … is the plurality ✓", "naming_norm … unresolved, so
unmeasured") 14 + 8; the file's siblings ("consistent with the file", "the file's established style.
Fine.") 9 + 4; a check that failed on the reviewer's own candidate read as "cannot be done" 6 + 5; the
brief's form ("the brief says not questions", "must be about the reviewed code") 4; an outside
authority (Zulip, Wikipedia, a precedent read as endorsement) 1 + 9; the PR's own framing (its profile
says "slower, so revert") 2 + 1. **63 of the 105 dropped rows, on 32 distinct asks, rest on a ground
the design below rules inadmissible**; 21 of the 35 checked-as-conforming rows rest on a failed check
or an authority ranked below the library's current practice.

**1.4 The conventions section** (§3): held at 177 AP rows; used and reached 87; held and considered
then dropped 39 (20 of them the `K` grounds above); held and ignored at the place 45. On the asks it
held, AP beat DX at 14, lost at 4, tied at 41. The gains are where the sentence's example matched the
hunk's shape and the sentence was read as demand (v0106–v0108 0→3 of 3, v0029 0→3, d0032 0→3,
v0062/v0063 0→2); the losses are where a sentence narrowed the change (d0015), redirected attention to a
neighbouring convention (d0005, the d0022 group), or, satisfied at the place, read as endorsement of the
very name the maintainer asked to change (p0012, p0008). By family: interface asks (F2) 0→11 of 24, the
one family the section moves; statement and API design (F6) 0 and 0 of 18, with every held sentence
ignored; naming (F8) 22 and 19 of 60, where a count-backed check reaches reliably (`encard_` 84 of 88)
and a plurality licenses the old form.

**1.5 The 24 asks no ask-free session on these sets reaches** (any model): by knowledge, none 7,
direction 5, mechanism 4, demand 3, pr_context 2, construction 1, api 1, unclear 1; by family, naming 5,
statement and API design 4, proof 4, PR-level 3, two each of derive-don't-restate, generality and
registration. At those very asks the sessions' behaviour was: dropped 44 rows, asked something else 34,
concluded fine 29, checked 24, partial 13. Even where nobody reaches, the concern was named and dropped
more often than it went unasked.

**1.6 Recurring observations of the readers** (each from a named ask): file-consistency is the wrong
ground once the library has moved past the file (d0018, d0003, d0004, d0008/9, p0006); a plurality tool
licenses the old form, and the evidence threshold is set by the tool, not the rule (d0045, d0022–27,
d0038); every session answered the maintainer's question itself and, holding the answer, filed nothing
(p0000, p0005, v0105); the brief's "not questions" closes the only form some asks take (p0000, p0005,
v0068, v0092: the gold holds questions whose answer is "no"); a satisfied convention at the place
licenses the miss (p0012, p0008); delivery moves pattern- and policy-shaped asks, judgement-shaped ones
need a per-declaration question with its own check (D12c); audits run axis by axis and never ask what
shape a caller would want (p0004, p0016, d0051, F6 throughout); the finding budget is a ground ("I'm
already at 7"; "filing a marginal finding dilutes precision").

## 2. The diagnosis

The reviewer makes two decisions at every place and conflates them: **what could be asked here** and
**whether it is asked for**. It answers the first with its own checklist (duplicate, name, proof,
binders, placement), which never contains "what shape would a caller want", "is there a mechanism that
produces this shape", "what does the proof use of this constant", "what is the library's current form
for this". It answers the second with the wrong authorities. "The model lacks knowledge" is true in a
specific sense: it lacks the knowledge *of what outranks what*. The exact-conventions brief
(+0.26) works because it substitutes one authority ("maintainers ask for this") for the model's prior at
a matching shape; it is not supplying facts about the code, which the model mostly has. Stage G
(+0.000) fails because a rule plus a check leaves the authority order where it was: the reviewer checks,
confirms the departure, and clears it on its prior. The disposition paragraph (S2) moves asks and passes
every unasked departure through because it removes one inadmissible ground without ranking the others.

## 3. The design

### 3.1 The unit

A review is a set of **(object, question)** cells, as D1's ledger already is: declaration, family, file
and PR objects; the question set of §3.3. Every cell ends in a **disposition** with its **authority** and
its **evidence**. Silence is not a disposition.

### 3.2 The authority order for the filing decision

At each cell, the reviewer files unless an authority of *higher* rank than the one raising the concern
says the code conforms. Ranked:

1. **A check that decides.** A compile, a linter, a count against a threshold the *rule* states (not the
   tool's default), a try-it. A passing check clears the cell. **A check that fails on the reviewer's own
   candidate does not clear it**: it changes the finding's form to a question with the evidence ("`gcongr`
   does not fire on `MonotoneOn`; is the side condition needed?"), because the maintainers' asks include
   questions whose answer is no (v0068, v0092, v0105, p0005, p0000).
2. **The library's current practice, with direction.** The newest form wins: a dated deprecation
   (old → new), a migration, a mechanism whose docstring is newer than the file, an analogue's shape
   where the library has settled one. **The file's siblings and the corpus plurality are evidence of
   the older form, never grounds to clear.** Where they are the only ground, the finding is "this file
   follows the older form; the library now does X", with the dated evidence.
3. **Maintainers' demand, asserted.** A census convention with its asks, stated as what maintainers ask
   for, outranks the reviewer's prior about maintainers. Its limits are stated with it: demand is a
   licence to file, not a prediction that this maintainer will; a convention *satisfied* at a place
   says nothing about the neighbouring name or form (negative guard); a sentence whose example does
   not match the hunk's shape is carried one step by the reviewer or filed as a question, not dropped.
4. **The reviewer's own judgement**, where 1–3 are silent. Its output is a finding or a question with
   its reasons, never silence.

**Inadmissible grounds for clearing a cell**, each with its count in the reading: the reviewer's
estimate of what a maintainer would request (22 rows); worth, minority, marginality or taste (27);
the file's siblings or house style (13); the corpus plurality or a tool's count below a threshold the
rule did not set (22); a form rule of the brief ("not questions", "concrete requests only") (4); the PR's
own framing of its change (3); a finding budget. These are selection, and selection is downstream (the
2026-09-22 ruling); a cell cleared on one of them is a cell the reviewer has decided for the maintainer.

### 3.3 The question set

The questions are the maintainers', at the maintainers' grain (the family vocabulary: proof, statement
and API design, interface, naming, registration, redundancy, generality, derive-don't-restate,
documentation, formatting, PR level, correctness), and the set is written so that it *contains the
questions the audit never asks*:

| question | the authority it is answered by | the knowledge source attached |
|---|---|---|
| does a check settle this (compiles, lints, counts)? | 1 | the standard linter set; try-it; counts with stated thresholds |
| is there a mechanism that produces this shape? | 1 (apply it, compile) then 2 | the tactic and attribute catalogue at base, with dates and adoption (`to_fun` at 2 files, `grind [def]`, `mk_iff`, `variable … in`) |
| what is the library's current form for this, and is the file's older? | 2 | the deprecation stream (old → new, dated); recent migrations; the newest sibling, not the nearest |
| what shape would a caller want; what does the analogous API provide? | 2 then 4 | analogue retrieval by role (`review-design-comparison.md`); the family's twin pattern |
| what does the proof use of this constant or hypothesis (generality)? | 1 (compile the generalisation) | the closer battery's constructions |
| do maintainers ask for this here? | 3 | the census with examples, asserted; with the negative guard |
| what does this file now cost its importers; what must the description state? | 2 / 4 | the import graph; the PR node |

### 3.4 Knowledge enters as authority, not as injected facts

Each source is attached to the rank at which it may decide, which is what the record's experiments
lacked: the same sentence delivered as "a convention, with a check" (rank 1 and 2 evidence without a
rank 3 assertion) moved nothing; delivered as "maintainers ask for this" (rank 3) it moved. A plurality
count delivered without its rank acted as rank 1 and licensed the old form. A sibling delivered as
context acted as rank 2 and endorsed the stale pattern. The design makes the rank explicit on every
piece of evidence the reviewer sees and on every disposition it writes.

### 3.5 The output contract

Per cell: disposition (`file` / `question` / `conforms`), authority rank, evidence (a check's output, a
dated form, a convention with its asks, or the reviewer's reasons), and a confidence label. Questions
are legal findings. Nothing is withheld on worth; the volume is reported, and a confidence label is
carried for the selection stage downstream, never used as a filter here.

## 4. Every design in the record is an instance

| design | what it is in this structure | what it lacked |
|---|---|---|
| convention detectors; the static pass; the closer battery | rank-1 checks for particular questions | they decide 10 of 93 asks' questions (mechanism/construction); the rest are rank 2–4 |
| the exact-conventions brief (+0.26) | rank-3 evidence for the PR's own asks | a ceiling: it knows the asks |
| AP (+0.20 on the ten PRs, 0 to −0.04 off them) | rank-3 evidence for a selector's picks, with the rank asserted | no negative guard; sentences matched by shape; narrowing |
| stage G (+0.000) | rank-1 checks without a rank-3 assertion | the authority order |
| the disposition paragraph S2 | one inadmissible ground removed | the others, and the rank |
| the dossiers and exams | richer rank-3 evidence | the reading says understanding was not the bottleneck; authority was |
| D1 `structured` (verdict per cell, silence illegal) | the unit and the contract | the authority order and the question set's missing questions |
| the critic D2 | a second reviewer over the same cells | a disagreement without an authority to appeal to |
| the naming census tool | a rank-1 count used as the rule's threshold | the rule's threshold; direction |
| analogue retrieval (E), the mechanism catalogue, the deprecation stream | sources for rank-2 questions | never attached to a question; two of the three never built |

What the structure says to stop building: detectors for the long tail (the census's 399 conventions,
the top 50 half of asks) as the route to recall; prompt variants that remove one dropping ground at a
time; sources delivered without a rank.

## 5. What the design predicts on the reading, and what it costs

- **Dropped concerns**: 63 of the 105 `K` rows (32 asks) rest on inadmissible grounds and would be
  filed; 34 of the 105 are on asks some other session reached, where the filing is the ask. On the 24
  never-reached asks, 44 rows named the concern and dropped it.
- **Cleared by a failed or wrong check or by a lower authority**: 21 of 35 `V` rows become questions or
  "older form" findings under rule 1 and rule 2.
- **Concluded fine**: 102 `C` rows, of which 16 are statement-and-API-design and 16 interface asks,
  where the question set is what is missing; the rest need the right question at a read place
  (layout rules, orientation, cost of an import).
- **The section's ignored rows** (45) become dispositions under §3.1, which the record measures as a
  volume lever: S2 took asks from 1 to 5 of 13 and unasked facts from 0.50 to 2.17 a PR.
- **The cost is volume**, and it is the open question: demand is at most 5% of applicable places
  (stage H); the design files what the reviewer would otherwise clear on worth or a guess. Whether those
  filings are welcome is unmeasured; the record's ruling is that selection comes after a generator that
  reaches, and gold is a lower bound. A reviewer under this design on the two control PRs of each set is
  the first number to read.
- **What it does not reach**: the 15 asks that need a fact the sources do not yet hold (an unbuilt
  catalogue, a direction no stream records, an analogue retrieval that does not exist), PR history
  outside the packet, and asks the gold itself misstates (v0105, v0053/v0056 counted twice, the 33145
  rename counted four times).

## 6. What would test it, before anything else

One condition, on the free reviewer, on the same packets, pre-registered before it runs: **R** = the
D1 cell contract + the authority order of §3.2 as the filing rule, the inadmissible grounds named, the
question set of §3.3 with the AP section as its rank-3 evidence and a negative guard, questions legal.
No new source is built for the first run; the rank-2 questions are asked of what the packet and tools
already hold. Against DX and AP, three reps, both sets, judged by the same matchers.

Rules, stated now: on the 24 never-reached asks, R reaches **≥ 6**; on the asks the reading marks `K`
on inadmissible grounds (32), R reaches **≥ 16**; findings per PR reported, with the two control PRs'
counts beside them, no cap; a re-read of a seeded sample of 40 R dispositions by the protocol's codes,
to see whether the inadmissible grounds fell. Below the bars, the design is written to `dead-ends.md`
with the untried sources (the mechanism catalogue, the deprecation stream, analogue retrieval) as its
reopen conditions.

## 7. Limits

One reader per batch; codes by keyword for §1.3 and §5, with a third of the `K` rows unclassified; the
matchers' outcomes are the table's and inherit its noise; the two sets are in-sample for every design in
the record, and P14's ten PRs are where AP was read; the design was written by the session that ran
the reading. The adversarial round should press on: whether this is forcing plus conventions plus
"questions allowed", each already tried; whether the authority order is a prompt that the free model
will follow where it ignored the precedence paragraph; whether volume makes it a pass-through like S2;
whether the rank-2 sources exist; and whether the 24 never-reached asks are reachable by any contract on
this model (gpt-5.5 and Qwen say contracts do not move weak models).

## 8. Defects the reading found in the measurement, to fix apart from the design

- The gold holds questions whose answer is "no" or whose change was never made (v0068, v0105): a
  reviewer that files only verified changes cannot match them; the matcher needs a question form.
- One design ask counted twice (v0053/v0056) and one rename counted four times (d0022–d0027).
- The brief's "do not raise questions" clause, the finding cap, and the naming tool's plurality without
  a direction are three harness features the reading records as grounds for misses.
- The readers shared one scratchpad and overwrote each other's helpers; nothing was lost, but each
  reader should get its own.

## 9. What the adversarial round did to the draft (2026-10-12)

Four reviews, each in `filing-decision-design-2026-10-12/`: `review-record.md` (21 verdicts),
`review-mechanics.md` (re-coding and re-counting from the transcripts), `review-generality.md`,
`alternative-design.md`. Consolidated:

| element of the draft | verdict | the evidence |
|---|---|---|
| The reading's numbers (§1.1–1.4) | **stand**, with slips: held-and-ignored is 46, not 45; §1.5's family list sums to 22 | recomputed from the jsonl by two reviewers |
| "A guess about maintainers" as a ground (22 rows) | **wrong: 6 rows.** The word `maintainer` marks 22; in 16 the reviewer *predicts the ask correctly* and drops it on the brief, on worth, or on nothing | mechanics §2, hand-coded 105 rows |
| The inadmissible-ground count (63 rows, 32 asks) | **64 rows on 37 asks**; and **41 rows state no listed ground**: 15 wrong technical justifications without a check, 13 unstated, 8 "convention satisfied", 6 correct refutations (v0105) | mechanics §2 |
| "The section changed no knowledge column" | **false**: 11 asks change DX→AP; `demand` has three meanings across readers; "15 need a fact" is 9–17 | mechanics §4 |
| The 24 never-reached asks | **24 only with Opus+AP as ask-free on `match_D12`**; 29 without TA; 32 on the assessment's seals; five D12 asks flip between matcher passes | mechanics §3 |
| Inter-reader agreement | 25 of 30 (K 9/10, C 5/8, V 5/6, O 6/6); the five disagreements on three undefined boundaries; one batch's K share is a reader effect, so §1.1's 81/65 split is reader-dependent at the tens | mechanics §1 |
| §0, §3.4: "an explicit authority order, which the record's experiments lacked" | **already exists, as prose**: `CONVENTIONS_PRECEDENCE` (`src/mathlib_review/analysis/probes.py:442-456`), stages D and AP, is ranks 1, 3, 4, the question rule and five of the seven inadmissible grounds, verbatim. With the PR's own asks +0.197/+0.179; off them −0.04 / −0.01 | record row 1; `one-reviewer-table-2026-10-10/README.md:185` |
| "The free model will follow the order" | **not shown**: under that paragraph 46 held sentences ignored, 39 dropped (20 on the grounds it names: "probability 0.35. Skip it", "overly pedantic"); DP filed no question in 131 findings; S2 wrote `conforms` on excluded grounds at 2 of 8 misses. Every record result that moved filings was structural (forced abstention 0.20→0.50; `target_verdicts` 112/112; D1 stable 6→8; S2 1→5 of 13); every rule about grounds read null (F +0.03, G +0.000) | record rows 6–7; alternative §2.5 |
| Rule 1, "a failed check becomes a question" | **the record's named untried item, set aside on volume**; narrowed there to `ask_author` (the check failed for want of a piece the author could add). **It cannot score**: judge v9 marks a question false (`judge/protocol.py:65`); the matcher has no question form. D1 records the inverse for *changes*: a tool-contradicted change is refuted, not filed | record rows 2, 10; `2026-10-06-generation-without-suppression.md:142,197` |
| Rank 1, "a check that decides" | **conflicts with the linter-as-oracle dead end** as stated: a passing linter dates availability, not a convention; the census bar swept 0.80→0.20 moved nothing | record rows 4, 12 |
| Rank 2, "the library's current practice with direction" | **amend**: siblings and plurality are already inadmissible under the paragraph; the direction sources (deprecation stream, mechanism catalogue, dated forms) **do not exist**; the 21:7 instance is a cited correction (`.claude/rules/mathlib-review.md`) | record rows 3, 11 |
| §3.3 "one structure" | **seven sources, five unbuilt**; §4 assigns ranks to past designs by outcome | generality §1 |
| §4 instances | S2 removes three grounds, not one; detectors decide 7, not 10; D1 did not "lack the order", it is the instance rule 1 reverses | record rows 8–10 |
| §5–§6 volume | **understated by an order of magnitude**: a regex over 156 transcripts' reasoning finds the grounds a median of 60 (DX) / 53 (AP) times a session; 20–30 named-and-dropped concerns against 3.8–6.2 filed and 3.6 asks a PR; expected 15–40 findings a PR; the record's pass-throughs sit there (stage G "all" 149/12 at 0.081; the places engine 68 at 7%; S2 13 of 14 unasked). "No cap" misreads the 2026-09-22 ruling, which every plan since read as "measure the gate, do not design one"; AP's yield guard and D1's ≤ 2.0 control guard are the record's standard | generality §3; record rows 16–18 |
| §6 as a test | **tests R against AP, not the order against its absence**; in-sample; no statistic; the matcher cost (~0.6M subscription tokens a seal) unstated; the 40-disposition re-read measures phrasing | generality §4; record row 16 |
| §0 "every narrow design is one authority or one question" | **over-claimed**: the levers that moved the wall were the model and the harness | record row 20 |
| The negative guard; the direction lesson for AI PRs; §8's gold defects | **stand** | generality §7; alternative §3 |

**Where the diagnosis lands after the corrections.** The reviewer names the maintainer's concern at
most of its misses and clears it; but the clearing is less "a guess that maintainers would not ask"
(6 rows) than worth (27), a plurality or a tool's count (22), the file's siblings (13), a check it did
not run or ran on the wrong candidate (15 + 11), and **nothing stated at all (13)**. Prose about grounds
cannot reach an unstated ground. What reached this model's filings in the record was always a change
in what the submission *may contain*. That is the alternative's point, and the generality review's,
and the record review's, arrived at separately.

## 10. The design that survives

Not an authority order the reviewer is told. **A submission contract the harness enforces, and a
boundary.** Four clauses, each one already measured in part:

1. **`conforms` is refusable.** A cell may be closed as conforming only with one of three evidence
   types the harness can see: a tool-call id (a check the harness ran, whose output is attached), a
   quoted line of the reviewed code that already has the required form, or a cited convention id
   whose example the reviewer matched. Anything else at a cell is a candidate. A submission with a bare
   `conforms` is handed back (D1's hand-back mechanism, `structured.py`, already does this for missing
   cells). This is S2's rule generalised from the detector list to every cell and made refusable
   rather than stated. It covers, by construction, the 15 wrong justifications stated without a check,
   the 13 unstated grounds, the 11 failed-check clearances and the 27 worth-grounds: none is an
   evidence type. Siblings and pluralities are not evidence types either, which is all the "direction"
   rule needs to say at the contract.
2. **The negative guard.** A cited convention clears only the cell that names it (p0012, p0008: a
   satisfied prime rule was used to clear the name the maintainer asked to change).
3. **`ask_author` is a legal disposition**, in the generation plan's narrowed form: the check could
   not be run, or it failed for want of a piece the author could add; it carries the check's output.
   Not "questions legal everywhere" (60 failed checks on one PR). This needs the measurement fixed
   first (§12): the judge and the matchers have no question form, and five gold asks take it.
4. **The boundary.** Stage 1, the reviewer, may not withhold: every cell ends as `conforms` (with
   evidence), a candidate (with typed evidence: `check`, `form`, `convention`, `construction`,
   `analogue`, `own`; and `would_clear_on`, the ground on which it would have left it out), or
   `ask_author`. Its candidate set is stored per sample. Stage 2 is a policy over the stored set,
   replayable without a reviewer run; the draft's authority order is its first policy, and it is
   selection, named as such and ordered after the generator as the 2026-09-22 ruling requires. The
   generator is measured by what it *names* (the matchers over All(G)); the policy by what it keeps.

**The question set** stays as the knowledge-side change, as D1's concern axis extended by the
questions the audit never asks (what shape a caller wants; is there a mechanism for this shape; what
the proof uses of a constant; the library's current form; what the file costs its importers), declared
as a `knob()` on the structured task (record row 21). Its sources are *later work*, listed with what
each would reach: the mechanism catalogue and the deprecation stream (direction, 6–9 asks), analogue
retrieval (2), constructions (1), none of them built.

**What is dropped from the draft**: the rank numbers as a prompt device; "a check decides" as an
authority over conventions (a check decides the question the check was written for: compiles, the
lint's own rule, a count against a threshold the rule states; never a convention's demand); "no cap"
and "nothing withheld on worth" (stage 1 withholds nothing; stage 2 keeps the record's two guards);
the 40-disposition phrasing re-read; the claim that every record design is an instance.

**Volume, sized now.** Stage 1 on a control PR: 10–20 candidates (the alternative's lexicon prior over
33304/33315/33438), against 0–1 findings today. Stage 2's first policy, if it keeps what the draft's
order keeps, publishes at the per-place engine's rate unless the guards bind. The guards are
pre-registered as failure conditions of the *published* set: asks reached per published finding no
lower than solo's (AP's yield guard), and ≤ 2.0 published findings a control PR (D1's). Whether the
unasked candidates are welcome is the adjudication the record has not done; stage 1's `would_clear_on`
tallies, over ask PRs and controls alike, are its first corpus.

## 11. The experiment, revised (pre-registered here; nothing run)

Conditions, the free reviewer, the same 26 PRs and packets, three reps, one seal, the table's two blind
matchers, with a question form added to the matcher rubric before the seal:

- **G** — stage 1: the D1 cell contract with the extended question axis, `conforms` refusable, the
  negative guard, `ask_author` legal, the AP section as `convention` evidence. No withholding. Stored.
- **All(G)** — every candidate published: the ceiling of what G named. Offline.
- **A(G)** — the draft's authority order as a policy over G's stored candidates, one adjudicator call a
  PR (mechanical for `check` and `form`; a model read for `convention` and `own`). Offline.
- **R** — the draft's in-line condition (the order stated to the reviewer), *only if* bar 1 passes:
  the prompt-versus-contract contrast.

The never-reached core is fixed as the assessment's definition (Opus+AP excluded, the table's seals):
**32 asks**; the inadmissible-`K` set as the mechanics review's hand coding: **37 asks**.

Bars:
1. **Does a reviewer that may not withhold still name?** All(G) reaches ≥ 24 of the 37 and ≥ 8 of the
   32, on the union of three reps, both matchers. Below 16 of 37 the contract suppresses naming and the
   design is written to `dead-ends.md`.
2. **Does the policy keep the reach?** A(G) keeps ≥ 80% of All(G)'s reached asks while its published set
   meets both guards on the control PRs and on yield. Failing the guards with the reach kept is the
   places test again, and is reported as that.
3. **Prompt or contract**, if R runs: A(G) − R ≥ 4 of the 37 on both matchers, paired by rep, says the
   boundary is needed; |A(G) − R| ≤ 2 says the in-line order suffices and the boundary is dropped.
4. Side readings: All(G) − A(G), the first measurement of the order as a policy; `would_clear_on` by
   ground over every candidate, the adjudication rubric's first corpus; a re-read of 30 G cells by the
   protocol's codes for the C3 counts (delivered or derived departures not filed; `conforms` without
   evidence; compiled edits with no finding).

Cost: G is three DeepSeek runs of 26 PRs on the local tier, about 35 min each, $0; All(G) and A(G) are
offline. The seal and the matchers are the cost, about 0.5–1M subscription tokens on the primary
account; R adds three runs and another seal. The build is the D1 subclass of
`.claude/rules/mathlib-review.md` (three edits) plus the refusable `conforms` and the stored candidate
set: small, native. Everything is in-sample; the fresh 40-PR set is the deciding set after.

## 12. Decisions for the user, and what is settled without one

- **Settled by the round**: the authority order is not a prompt; the knowledge the reviewer lacks is
  rarely a fact about the code; the misses are named concerns cleared on grounds a contract can refuse
  and prose cannot; volume is the cost and is bounded by numbers already on disk.
- **Yours**: whether to spend the seal-and-matcher tokens on G (and R); whether the question form goes
  into the matcher rubric now (it changes what every future seal can score, so it is a boundary, not a
  patch); whether stage 2 being selection, named as such, is acceptable under the ruling's ordering
  (generator first, measured uncapped) — the alternative argues it is, the draft tried to avoid the
  word.
- **To fix regardless**: §8's gold defects; the matcher's question form; a per-reader scratchpad.
