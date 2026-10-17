# Adversarial review 4, part 2: does the read follow from the numbers? (2026-10-17)

**Under attack.** The read of `results/pr_review_v5/probes/attention-practice-2026-10-17/` (commits `9be22397`
to `456934f4`): claims (a) to (d), and the headline (e) told to the user, in `RESULTS.md` and the
`docs/questions.md` line. The detector rows are taken as given (another reviewer re-checks them), except where a
number below shows a problem in how a row is read.

**Read.** `PROTOCOL.md` with amendment 1, `RESULTS.md`, `detect.py`, `places.py`, `practice.py`, `outcome.py`,
`declines.py`, `score_declines.py`, `declines_labels.jsonl`, `practice.json`, `outcomes.jsonl`; stage H's
`RESULTS.md` and `census_rates.json`; stage G's `rules.json`; the census labels and events; review 3's files beside
this one; the plan with amendment 2; Mathlib's linters (`Mathlib/Tactic/Linter/`, `Mathlib/Init.lean`,
`lakefile.lean`, `scripts/`) in the clone. The 24 convention declines were read in full from the rebuilt packet
(rebuilding rewrote `declines_key.jsonl` identically).

**Computed.** Scripts in
`/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/a142d916-dd29-4521-a449-00e1db067b18/scratchpad/rev4/infer/`.
Each imports the probe's own `detect.py`, `places.py` and `outcome.py` unchanged.

| script | what it computes |
|---|---|
| `s1_step3.py` | step 3's table re-derived; census asks per departure, per rule |
| `s2_p097_any.py` | one tactic per line, "fixed" amid other changes: does the merged proof still hold a `;`? |
| `s3_declchange.py` | per rule and attention: how often the declaration changes by merge, and the departure goes given a change |
| `s4_p097_split.py` | the same "fixes": joined tactics split onto their own lines, or replaced |
| `s5_asked_fixes.py` | near-comment fixes crossed with a census ask at the departure |
| `s6_census.py` | census asks under the six rules and stage H's ten: count, askers, months |
| `s7_split.py` → `split_rows.jsonl` | step 2's practice counts re-split by new / edited / moved declaration, month, area, author |
| `s8_split_read.py` | rates by those splits; each rule's census askers in their own code |
| `s9_authors.py` | spread of the practice rate across the 30 active reviewers |
| `s10_blame.py`, `s11_blame_p341.py` | the base library's rates by the age of the line (`git blame`, all 2,279 base files) |
| `s12_suggest.py` | departing suggestion blocks: the reviewer's own layout, or the author's lines kept? |
| `s13_p097_denominator.py` | one tactic per line over tactic proofs with two or more tactics |
| `s14_rewrite_control.py` | every touched theorem near and far from a comment: changed by merge, by what it holds |
| `s15_selection.py` | census ask labels by stage G check kind; layout-like census entries |
| `s16_lemma_share.py` | `lemma` against `theorem` headers, per active reviewer |
| `s17_stageh_overlap.py` | stage H's P084 places against this probe's line-join departures on the same 16 PRs |
| `s18_intervals.py` | Wilson intervals for the small counts |

## Verdicts

| claim | verdict | in one line |
|---|---|---|
| (a) three rules "not their practice" | **weakened** | Robust for theorem docstrings and term-proof placement. Line joins rest on one author (17% without him, "mixed" by the protocol). "As the library" is wrong for two of the three. |
| (a) two rules "practice, kept at 95-99%" | **weakened** | AI-flagged PRs keep one tactic per line at 91%. Over proofs where a choice exists, humans keep it at 92%. No linter enforces either rule. `[C x]` is the language's default form. |
| (a) blank lines "mixed" | **stands** | 15-19% pooled. By author it splits: 6 of 20 reviewers keep it at 5% or less, 7 break it at 20% or more. |
| (b) "near a comment, practiced rules vanish at 32-49%" | **weakened** | Near a comment, declarations with no departure are rewritten at 56%. The contrast follows where the construct sits. Fixes in the rule's own form are asked fixes. |
| (c) the control | **stands, low power** | The amendment is well grounded. 10 of 10 has an interval of 72-100%. It validates the line-text matcher only. The 13-of-15 check covers the declaration-based matcher. |
| (d) a third of convention declines give a place fact | **stands as a count; weakened as support** | 8 of 24 (18-53%). About 16 of the 24 are commenters softening their own suggestion. 3 of the 8 facts say the change fails or is moot. |
| (e) "no rule is held by maintainers and enforced at 5%" | **weakened** | It changes the denominator. Per departure, every one of the six is asked at under 2%, the practiced rule included. |
| (e) "where they look, maintainers act on the practiced rules, mostly inside rewrites" | **falls as stated** | What the numbers show: maintainers rewrite attended code; the construct goes with the rewrite; the rule is acted on by asking, at 6% and 26% of attended departures. |

## 1. "Not their practice" (a)

### 1.1 The 20% line and one author

The protocol reads "not their practice" when the active reviewers' rate is 20% or more. It reads "mixed" between
5% and 20%. For line joins the pooled reviewer rate is 23% (176 of 760; interval 20-26%). One author, joelriou,
holds 76 of the 176 departures and 157 of the 760 opportunities (`s9_authors.py`).

| line joins, active reviewers | departures | rate | protocol reading |
|---|---|---|---|
| all 30 | 176/760 | 23% | not their practice |
| without the largest contributor | 100/603 | 17% | **mixed** |
| per author (19 with 15 or more opportunities) | 3 keep it at ≤5%, 8 break it at ≥20%, 8 between | | |

So the "three not practice" count is decided by the threshold and one author. Without him line joins have the same
profile as blank lines, which RESULTS calls mixed:

| rule | reviewers | reviewers, top author out | other humans | AI | suggestions | base library |
|---|---|---|---|---|---|---|
| line joins | 23% | 17% | 15% | 29% | 20% | 10% |
| blank lines | 15% | 12% | 16% | 19% | unreadable | 17% |

The ⅔ clause does no work here: reviewers are above other humans for line joins. The other two readings survive the
same test. Term-proof placement is 23% without its largest contributor, and 8 of 11 reviewers break it at 20% or
more. Theorem docstrings are 85% without the largest contributor, and all 17 reviewers break them.

### 1.2 Currency: is the rule newer than the code?

**Within the window, no.** Departure rates by PR month show no trend for any rule (`s8_split_read.py`). Line joins
run 8-30% by month, theorem docstrings 72-86%, term-proof placement 22-42%. Class hypotheses jump to 9% in
2026-03, which is one PR (36910, 26 departures).

**Before the window, the library's own rate is mostly the port's.** `git blame` dates every base opportunity by the
last time its lines were touched (`s10_blame.py`, `s11_blame_p341.py`, all 2,279 base files):

| base library, last touched | line joins depart | term proof on the last line | `theorem` without docstring | `lemma` share of headers |
|---|---|---|---|---|
| up to 2023-07 (the port) | 1% (108/8,290) | 8% (355/4,343) | 87% | 1% |
| 2023-08 to 2024-06 | 12% | 18% | 85% | 33% |
| 2024-07 to 2024-12 | 12% | 14% | 83% | 36% |
| 2025 and later | 15% | 19% | 83% | 40% |

Port-era code was machine-formatted, and the port wrote every `lemma` as `theorem`. Human code written since the
port breaks line joins at 12-15% and term-proof placement at 14-19%. That is close to PR code, not far from it. So
"the library breaks it" is wrong for port code (1%, 8%), and right only for human code since. The rival "the rule
is new" fails; a weaker rival stands: line joins describe how the port's formatter laid code out. The `lemma` share
rises from 33% to 40% after the port: a slow drift that a docstring rate cannot see.

### 1.3 Scope: held in some areas, or by some authors

Pooled rates hide large spreads (`s8_split_read.py`, `s9_authors.py`; humans, moved code out, areas with 40 or more
opportunities):

| rule | lowest areas | highest areas | reviewers keeping it (≤5%) / breaking it (≥20%) |
|---|---|---|---|
| line joins | Geometry 2% (1/41), Topology 8% (14/166) | CategoryTheory 30%, AlgebraicTopology 46% | 3 / 8 of 19 |
| blank lines | Probability 0% (0/82), AlgebraicTopology 1% (1/95) | LinearAlgebra 24%, Geometry 30% | 6 / 7 of 20 |
| theorem docstrings | Combinatorics 56% | GroupTheory 96% | 0 / 17 of 17 |
| term proof on its own line | Topology 21% | RingTheory 35% | 1 / 8 of 11 |

Without joelriou, line joins still run from 8% (Topology) to 22-24% (CategoryTheory, LinearAlgebra). Area and
author are collinear (the plan's earlier finding), so this cannot say which. But the pooled "not their practice"
cannot separate "nobody's practice" from "the practice of some authors or areas". For line joins and blank lines the
data on disk favour the second.

Theorem docstrings show the same thing through the rule's other half. The rule says: give a `theorem` a docstring,
or use `lemma`. Reviewers' `lemma` share runs from 4% (4 of 88) to 99% (299 of 302) (`s16_lemma_share.py`). An
author who keeps the rule writes `lemma`, which is not an opportunity. So the per-opportunity rate is drawn mostly
from the authors who do not keep it. The only census asker under P341 (two asks, one PR) writes `lemma` for 49 of
his 50 headers.

The askers keep two other rules more than others do (moved code out): one tactic per line 2% (10/555) against 5%;
blank lines 6% (7/123) against 15%. For line joins the askers without joelriou sit at 16%, as other humans do.

### 1.4 New code against rewritten code; writing against reviewing

| humans, moved code out | new declarations | edited declarations | moved |
|---|---|---|---|
| line joins | 20% (274/1,372) | 11% (10/87) | 10% |
| one tactic per line (per proof) | 6% | 2% | 2% |
| theorem docstrings | 77% | 84% | 87% |
| term proof on its own line | 28% | 28% | 6% |

Line joins depart most in new code, and reviewers' new code is at 25%. Edited code keeps older layout.

**"A practice they apply at review but not when writing" is not supported.** Active reviewers' suggestion blocks
leave 20 of 87 two-line signatures joinable (23%), from 9 different reviewers. In 19 of the 20 the two lines are not
among the lines the suggestion replaces, so the layout is the reviewer's own (`s12_suggest.py`). For term-proof
placement it is 6 of 30. Copilot is counted as a suggestion author (the bot filter matches "bot", not "Copilot");
it adds one departure.

**Verdict (a).** Weakened. Two of the three readings are robust to the threshold, the author, the month and the
area: theorem docstrings and term-proof placement. Line joins are at the line. "As much as the library" holds only
against the library's human code since the port.

## 2. "Practice, kept at 95-99%"

**No linter enforces any of the six.** Mathlib's standard set (`Mathlib/Init.lean`) and text linters
(`Mathlib/Tactic/Linter/TextBased.lean`) were read. The `;` linter flags only a space *before* a semicolon.
`emptyLine` flags blank lines *inside* a command, not around it. `whitespace` tolerates line breaks in a signature.
`docString` checks a docstring's form, not its presence. So (a) and (b) are not reading a linter's output.

**The denominators flatter the two practiced rules.**
- One tactic per line is counted per touched proof. That includes term proofs and one-tactic proofs, where no
  choice exists. Over human tactic proofs with two or more tactics, 242 of 2,875 depart: **8.4%**
  (`s13_p097_denominator.py`). By the protocol's 5% line that reads mixed, not practice. AI-flagged PRs depart at
  9% per touched proof. So "kept at 95-99% by every kind of author" fails both ways.
- Class hypotheses: the denominator is named class binders plus every bracketed group in the signature. So the 1%
  is the share of class arguments written as `(h : C x)` instead of `[C x]`. `[C x]` is how Lean makes a class
  argument inferable at call sites. A 1% rate cannot separate a maintainers' norm from how Lean is written. Of the
  57 departures, 26 are on one PR; 27 are `Mono`, `Epi` or `IsIso` in category theory (the two sets overlap); 5 name a
  topology or uniformity, where a named binder is usual.

**Verdict.** Weakened. The two rules are near-universal, but this does not show that maintainers hold them. They are
the language's ordinary form, kept at 92-99% unasked.

## 3. What the six rules select for, and how far (e) can travel

The six were picked because a script can check them. That selects layout and binder form, with exact triggers and
cheap fixes. It also selects rules maintainers rarely ask for (`s6_census.py`, `s15_selection.py`):

| | census ask labels (of 2,045) | census rank of each rule (of 410 asked) |
|---|---|---|
| the six | 37 (1.8%) | 21, 69, 71, 207, 237, 395 |
| stage H's ten | 259 (12.7%) | 2, 4, 7, 17, 19, 21, 22, 38, 41, 91 |

Three of the six were asked once or twice in 973 PRs: theorem docstrings (2 asks, one maintainer, one PR),
term-proof placement (2) and class hypotheses (1). For these, "not their practice" restates what the census
already said.

**Where (e) can travel.** A keyword pass over the 438 census entries finds about a dozen of the same kind: spacing
(P059, 33 asks), line breaks (P084, 20), indentation (P069, P128, P137), blank lines (P012, P217), the six. They carry
about 90 labels, near 5% of census asks. Stage G's 52 rules carry 572 of 2,045; their "read" kind 139.

**What (e) says nothing about.** The substantive rules: use the API, a finishing tactic, name like the siblings,
drop a hypothesis. That is 8 of stage H's ten and most of the census head (28 of the top 50 are not even stage G
rules). It also says nothing about docstring content, about later review rounds, or about AI-authored PRs. Their
step-3 outcomes are pooled, not reported.

## 4. The 5% itself

The user's figure is stage H's: census asks per flagged place for ten rules, 0.26-4.8% (`census_rates.json`). Only
one of the six is among those ten: P084, line breaks. This probe checks one sub-case of it, two-line signature
joins. On the 16 stage H PRs the probe finds 10 line-join departures. 8 of them are at stage H P084 places, and
stage H flagged 23 P084 places there (`s17_stageh_overlap.py`). Over 973 PRs, 3 line-join departures carry a census ask under P084,
which has 20 asks in all.

RESULTS never computes the figure the user asked about for its own rules. Computed (`s1_step3.py`):

| rule | census asks per departure | targeted fix by merge | any change by merge |
|---|---|---|---|
| line joins | 3/357 (0.8%) | 2/243 | 10/243 |
| one tactic per line (practice) | 5/443 (1.1%) | 3/239 (1.3%) | 46/239 (19%) |
| theorem docstrings | 1/2,029 (0.05%) | 8/1,337 | 20/1,337 |
| blank lines | 8/419 (1.9%) | 10/248 | 16/248 |
| term proof on its own line | 1/294 (0.3%) | 5/210 | 9/210 |
| class hypotheses (practice) | 0/57 | 0/19 | 0/19 |

Every one of the six is asked at under one departure in fifty: less than the ten rules per flagged place. For the
practiced rule, 81% of departures reach merge, and 1.3% are fixed in the rule's own form. The probe measured
something else, and it is useful: departures per opportunity. For two rules few departures exist, so few asks are
needed. But "the tension does not appear here" holds only per opportunity. Per departure, the one-in-a-hundred is
right there, for the practiced rule too.

## 5. Steps 3 and 4 as support for the user's picture

### 5.1 "Where they look" is "where the declaration gets rewritten"

`near` means a round-1 comment within 3 lines of the declaration. Near a comment, most declarations are rewritten by
merge, whatever they hold (`s14_rewrite_control.py`):

| touched theorems on merged PRs | near a comment: changed by merge | far: changed |
|---|---|---|
| holding no departure | 56% (193/347) | 14% |
| holding a one-tactic-per-line departure | 69% (31/45) | 15% |
| holding a line-join departure | 61% (17/28) | 11% |

So most of the near/far gap (49% against 5-10%) is the rewrite rate. A rewrite removes a construct inside a proof,
and rarely one in a signature or header (`s3_declchange.py`). Given that the declaration changed, the departure is
gone for one tactic per line at 64%, line joins 10%, term-proof placement 11%, theorem docstrings 4%. The split
between "practiced" and "not practiced" rules coincides with this split between proof and signature. The two cannot
be told apart here.

**What the 32 one-tactic-per-line "fixes" near a comment are** (`s2_p097_any.py`, `s4_p097_split.py`):
- In 26, a tactic of the joined line is no longer in the merged proof. The proof was replaced.
- In 6, the joined tactics now stand on their own lines (2 targeted). That is the rule applied: 6 of 65, 9%
  (interval 4-19%).
- In 6 of the 32, the merged declaration still holds a `;` departure. The outcome follows the line's text, so
  editing the line counts as a fix.

**Fixes in the rule's own form are asked fixes** (`s5_asked_fixes.py`):

| near a comment | asked: targeted fix | unasked: targeted fix | unasked: any change |
|---|---|---|---|
| one tactic per line | 1 of 4 (3 more changed) | 1/61 | 28/61 |
| blank lines | 6 of 8 | 1/23 | 4/23 |
| line joins | 2 of 2 | 0/31 | 2/31 |

Blank lines' "32% near" is mostly six census asks. So the evidence supports this: maintainers act on a rule by
asking. They ask at 4 of 65 attended one-tactic-per-line departures (6%) and 8 of 31 attended blank-line departures
(26%). An asked departure is fixed (13 of 15). An unasked one is rewritten away or left. "Act on the practiced
rules, mostly inside rewrites" credits the rule with the rewrite.

### 5.2 The control

The amendment is well documented and the reason is right: the linter does not run upstream of itself. Three limits:
- 10 of 10 has a Wilson interval of 72-100%. It cannot exclude a matcher that misses one fix in four.
- The long-line control follows a line by its text. The five declaration rules follow a declaration by its name and
  run the detector again. The control does not test that path.
- The added check does test it for asked departures: 13 of 15 fixed (62-96%), 7 of them on declaration rules.

### 5.3 Step 4: rival readings of "a third give a fact about the place"

I read the 24 convention declines in full (one reader, me). Whose proposal is declined:

| the declined change was | n | of which `place` |
|---|---|---|
| the commenter's own suggestion or idea (golf, generalise, a pattern, a move) | 16 | 5 |
| another reviewer's or a bot's request | 6 | 3 |
| the author's own style change (asked to revert) | 1 | 0 |
| unclear | 1 | 0 |

Rival readings, each with the items that carry it:
1. **Self-hedging, not a decision about a departure.** Most declines soften the commenter's own optional suggestion.
   No convention was broken in the PR's code; the reviewer offered an improvement and made it optional.
2. **The convention does not apply.** Three of the eight `place` facts say the suggested change fails or is moot:
   the tactic hit a side condition; the lemma's generality is wrong anyway; an edge case was tested. That is a
   trigger absent, not evidence that a scope-dependent convention yields.
3. **The category is broad.** `place` includes performance, technical limits and consistency. The user's picture
   names the file's practice, a scope or currency. Of the 8, about three fit that closely: the library already
   diverges and the convention is undecided; the folder already names the topic; a construct used only once.
4. **Selection by phrase.** Declines phrased without the list's phrases are not counted. The direction is unknown.
5. **n and one reader.** 8 of 24 has an interval of 18-53%, which holds both registered lines. One label decides
   it. RESULTS says so; the questions line does not.

The closest analogue of the picture's negative half is a maintainer leaving *another person's* convention request
on a fact about the place. That is 3 of 6, on six comments over 973 PRs.

## 6. Over-claims, sentence by sentence

**RESULTS, step 2 read.**
- "broken by the maintainers' own code as often as by anyone's ... and by the library itself": the library breaks
  line joins at 10% and term-proof placement at 16%; port code at 1% and 8% (§1.2).
- "(the active reviewers break line joins *more* than other authors)": one author's effect; 17% against 15% without
  him (§1.1).
- "Two are held everywhere, at 95-99%, by every kind of author": AI-flagged PRs 91%; per multi-tactic proof 92%
  (§2).
- "None is a rule the maintainers' code keeps while PR code breaks it": true pooled. By author, 3 of 19 reviewers
  keep line joins and 6 of 20 keep blank lines (§1.3).

**RESULTS, step 3.**
- "Attention matters only for the rules that are practice": confounded with where the construct sits; near-comment
  rewrite rate 56% (§5.1).
- "For the three rules that are not practice, they vanish at 4-12% near a comment, barely above the rest": line
  joins near 12% against 3% far is four times. Both are small.
- "The outcome tracks real asks": supported, 13 of 15.

**RESULTS, step 4.** "The facts given are of the kind the user's picture names": two of the five listed (a side
condition defeats the tactic; the lemma is in the wrong generality anyway) are facts about the suggestion, not about
the place (§5.3).

**RESULTS, "What it says about the 5%".**
- "no rule is held by maintainers and enforced at 5%": per departure every rule is asked at under 2% (§4).
- "their own code, their suggestions and the library break it at 10-86%": suggestions are unreadable for theorem
  docstrings; the 10% is the library keeping line joins at 90%.
- "the code already keeps it at 95-99% whoever writes it": 91-92% (§2).
- "The one mixed rule (blank lines) is broken at 15-19% by everyone": by area 0-30%, by reviewer 0% to 62% (§1.3).
- "The tension the user named ... does not appear here": per opportunity only (§4).
- "Where they look, maintainers do act on the rules that are practice": they rewrite; they act on the rule by asking
  (§5.1).
- "When maintainers say why they leave something": mostly they make their own suggestion optional (§5.3).

**`docs/questions.md`.** "as much as other authors and the library"; "every kind of code keeps them at 95-99%";
"Near a comment, departures of the practiced rules vanish at 32-49%"; "No rule is held by maintainers and enforced
at 5%": each as above. "Practiced rules" there includes blank lines, which step 2 calls mixed.

**Labels.** "Maintainers" in (e) means 30 logins with 20 or more round-1 comments. RESULTS's limits say so; the
headline and the questions line do not.

## Not checked

- The detectors and the outcome matcher (the other reviewer's brief).
- My reading of the 24 declines is one reader, of one model family, as the probe's was.
- `git blame` dates the last touch, not the first writing. A port line reformatted later counts as later.
- The "split onto lines" test compares each `;` segment, with `·` removed, against whole merged lines. A segment
  edited in passing counts as replaced, so 6 of 65 is a lower bound on the rule applied.
- The layout-like census entries were found by keyword and read by title only.
- Lean was not run.

## Corrections

1. RESULTS step 2, "Three of the six rules, as stage G wrote them, are broken by the maintainers' own code as often
   as by anyone's (the active reviewers break line joins *more* than other authors), and by the library itself." →
   "Two of the six rules as stage G wrote them, theorem docstrings and term proofs on their own line, are broken by
   the active reviewers' own code as often as by anyone's (86% and 26%; 85% and 23% without the largest contributor),
   and by the library's human-written code since the port (83% and 14-19%). Line joins sit at the line: 23% pooled,
   17% without one author who holds 76 of the 176 departures, which the protocol reads as mixed; 3 of 19 reviewers
   keep it at 5% or less, 8 break it at 20% or more. Port-era library code keeps line joins at 99%."
2. RESULTS step 2 table, line joins' reading "not their practice" → "not their practice (mixed without one author:
   17%)".
3. RESULTS step 2, "Two are held everywhere, at 95-99%, by every kind of author." → "Two are kept at 95-99% per
   opportunity by human authors and 91-100% on AI-flagged PRs. Over tactic proofs with two or more tactics, one
   tactic per line is kept at 92%. No Mathlib linter enforces either. Class hypotheses as `[C x]` is Lean's ordinary
   form."
4. RESULTS step 3, "Attention matters only for the rules that are practice. ... barely above the rest." → "Near a
   comment, declarations are rewritten by merge at 56% even when they hold no departure (14% elsewhere). A departure
   inside a proof goes with the rewrite (one tactic per line: 64% of changed declarations); one in a signature or
   header rarely does (4-11%). So the near/far contrast follows where the construct sits as much as whether the rule
   is practice. Fixes in the rule's own form are asked fixes: unasked attended departures were fixed that way at 1
   of 61 (one tactic per line), 1 of 23 (blank lines) and 0 of 31 (line joins)."
5. RESULTS step 3, after "30 of those 32 went with other changes to the same proof (23 declarations on 21 PRs)" →
   add "In 26 of the 32 a tactic of the joined line is no longer in the merged proof; in 6 the tactics were split
   onto their own lines (9% of 65); 6 of the 32 merged declarations still hold a `;`."
6. RESULTS step 4, "The facts given are of the kind the user's picture names: ..." → "About 16 of the 24 decline
   the commenter's own optional suggestion, and 6 another reviewer's or a bot's request (a second reading, also one
   reader). Of the 8 place facts, 3 say the suggestion fails or is moot; 3 are on another person's request: the
   library already diverges, the folder names the topic, a single use. The interval on 8 of 24 is 18-53%."
7. RESULTS, "For these six rules of form, no rule is held by maintainers and enforced at 5%." → "For these six
   rules of form, no rule is enforced by asks: census asks sit at 0-1.9% of each rule's departures, the practiced
   one-tactic-per-line rule included (5 of 443), and 81% of its departures reach merge. The rules differ in how many
   departures exist: two are kept unasked by nearly everyone at 92-99%; two are kept by nobody; line joins and blank
   lines are kept by some authors and areas and broken by others, 15-20% overall."
8. RESULTS, "Either the rule as written is not their practice (three rules: their own code, their suggestions and
   the library break it at 10-86%)" → "Either the rule as written is not their practice (two rules robustly, line
   joins at the line: their own code breaks them at 23-86%, the library's post-port code at 12-85%)".
9. RESULTS, "The one mixed rule (blank lines) is broken at 15-19% by everyone." → "The mixed rule (blank lines) is
   broken at 15-19% pooled, but 0-1% in Probability and AlgebraicTopology and 30% in Geometry; 6 of 20 reviewers keep
   it at 5% or less."
10. RESULTS, "The tension the user named, rules applied one time in twenty, does not appear here." → "Per
    opportunity the tension does not appear: two rules are kept by habit and two by nobody. Per departure it does:
    none of the six is asked at more than one departure in fifty. These six carry 37 of 2,045 census ask labels;
    the ten rules behind the 5% figure share only line breaks with them."
11. RESULTS, "Where they look, maintainers do act on the rules that are practice, though mostly inside broader
    rewrites (one tactic per line: 49% gone near a comment against 5-10% elsewhere; blank lines 32% against 0-4%),
    and not on the rules that are not (4-12%)." → "Where they look, maintainers rewrite about half of the
    declarations by merge, whatever the declarations hold, and departures inside proofs go with the rewrite. They
    act on a rule itself by asking: 4 of 65 attended one-tactic-per-line departures and 8 of 31 attended blank-line
    departures carry a census ask, and 13 of 15 asked departures were fixed."
12. RESULTS, "When maintainers say why they leave something, a third of the time it is a fact about the place, at
    the registered line, on 24 comments." → "When a commenter calls a convention change optional, a third of the
    time (8 of 24; 18-53%; one reader) the reason is a fact about the code. Most of the 24 soften the commenter's own
    suggestion, and 3 of the 8 facts say the suggestion fails or is moot."
13. RESULTS, "Limits:" → add "the reviewers' line-join rate rests on one author; the six rules carry 1.8% of census
    ask labels; near/far is confounded with where the construct sits; 'maintainers' are 30 logins by a count".
14. `docs/questions.md`, "(their own code breaks line joins at 23%, theorem docstrings at 86%, term-proof placement
    at 26%, as much as other authors and the library)" → "(their own code breaks theorem docstrings at 86% and
    term-proof placement at 26%, as much as other authors and the library's post-port code; line joins at 23%,
    17% without one author, at the protocol's line)".
15. `docs/questions.md`, "two are practice and every kind of code keeps them at 95-99% (one tactic per line, class
    hypotheses as instance arguments)" → "two are kept unasked at 92-99% (one tactic per line, class hypotheses as
    instance arguments), yet asked at 1.1% and 0% of their departures".
16. `docs/questions.md`, "Near a comment, departures of the practiced rules vanish at 32-49% (mostly inside
    rewrites; 3% as a targeted fix) against 0-10% elsewhere." → "Near a comment, declarations are rewritten by merge
    at 56% whatever they hold; departures inside proofs go with the rewrite (one tactic per line: 49% gone, 9% split
    onto lines, 3% targeted); fixes in the rule's own form are asked fixes."
17. `docs/questions.md`, "No rule is held by maintainers and enforced at 5%." → "None of the six is enforced by
    asks: census asks sit at 0-1.9% of each rule's departures."
18. `docs/questions.md`, "Of 24 stated declines of a convention, 8 give a fact about the place (one reader, at the
    registered third)." → "... (one reader, at the registered third, interval 18-53%; most of the 24 soften the
    commenter's own suggestion)".
