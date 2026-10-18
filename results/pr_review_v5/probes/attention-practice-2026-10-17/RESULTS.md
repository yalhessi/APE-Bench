# Is a rule the maintainers' own practice, and do they fix it where they look? Results (2026-10-17)

Protocol: `PROTOCOL.md` (pre-registered before any outcome), with amendment 1 (the control, post hoc). Scripts:
`places.py` (step 1), `practice.py` (step 2, `practice.json`), `outcome.py` (step 3, `outcomes.jsonl`),
`declines.py` and `score_declines.py` (step 4, `declines_labels.jsonl`, one reader). 3,628 departures on 571 of the
973 val1000 PRs; 3,040 on the 500 PRs merged in the clone.

## Step 2: is the rule their practice? (`practice.py`)

Departures per opportunity, by who wrote the code:

| rule | active reviewers' own PRs | other humans | AI-flagged PRs | reviewers' suggestion blocks | base library | reading |
|---|---|---|---|---|---|---|
| line joins (P084J) | **23%** (176/760) | 15% | 29% | 20% (22/108) | 10% | not their practice |
| theorem docstrings (P341) | **86%** (706/817) | 75% | 74% | unreadable | 85% | not their practice |
| term proof on its own line (P240) | **26%** (137/522) | 29% | 28% | 22% (8/36) | 16% | not their practice |
| blank lines around commands (P012) | **15%** (196/1,327) | 16% | 19% | unreadable | 17% | mixed |
| one tactic per line (P097, per proof) | **4%** (121/2,699) | 5% | 9% | 3% (34/1,240) | 5% | their practice |
| class hypotheses as `[C x]` (P392) | **1%** (19/2,352) | 2% | 0% | 0% (0/230) | 1% | their practice |

Suggestion fragments cannot show a docstring above them or a command's neighbours, so those two cells are
unreadable (decided before running). 581 of the 2,029 docstring departures sit in edited or moved theorems, which
that rule exempts; dropping all of them from the count still leaves 1,448 of 2,583 new theorem headers (56%)
without a docstring.

**Read.** Three of the six rules, as stage G wrote them, are broken by the maintainers' own code as often as by
anyone's (the active reviewers break line joins *more* than other authors), and by the library itself. Two are
held everywhere, at 95-99%, by every kind of author. None is a rule the maintainers' code keeps while PR code
breaks it.

## Step 3: fixed by merge where they look? (`outcome.py`)

**Control (amendment 1, post hoc).** As registered it failed: 10 of 16 long lines fixed. The six survivors sit in
the long-line linter's own upstream files (`Mathlib/Tactic/`), where the linter does not run, and are present at
merge at 104-113 characters. Outside `Mathlib/Tactic/`: **10 of 10**. The added check: of the 15 departures with a
census ask under the same rule within a line, **13 were fixed by merge**. The outcome tracks real asks.

**Fixed by merge**, moved code left out. The registered measure is a *targeted* fix (the declaration otherwise
unchanged); fixes amid other changes are shown beside it, descriptive:

| rule | near a round-1 comment: targeted | near: any change | PR reviewed, not near: any | PR not reviewed in round 1: any | reading (registered) |
|---|---|---|---|---|---|
| line joins | 2/33 (6%) | 4/33 (12%) | 6/126 (5%) | 0/84 | left where seen |
| theorem docstrings | 4/210 (2%) | 8/210 (4%) | 12/659 (2%) | 0/468 | left where seen |
| term proof on its own line | 0/21 | 1/21 (5%) | 8/135 (6%) | 0/54 | left where seen |
| blank lines around commands | 7/31 (23%) | 10/31 (32%) | 6/134 (4%) | 0/83 | mixed |
| one tactic per line | 2/65 (3%) | **32/65 (49%)** | 10/100 (10%) | 4/74 (5%) | left where seen (targeted) |
| class hypotheses | 0/4 | 0/4 | 0/7 | 0/8 | too few |

- **The reading of "one tactic per line" depends on the measure.** Half of its departures near a comment are gone
  by merge, but 30 of those 32 went with other changes to the same proof (23 declarations on 21 PRs). By the
  registered, targeted measure it is "left where seen"; by any change it sits at the 50% line.
- **Attention matters only for the rules that are practice.** Near a comment, departures of the two rules that are
  practice or mixed vanish at 32-49% against 0-10% elsewhere. For the three rules that are not practice, they
  vanish at 4-12% near a comment, barely above the rest.
- **Place predicates (Q3) could not be read.** Near a comment, the new-against-edited and file-practice arms
  held under 10 departures each for every rule. On all departures, fixes are so rare (1-3%) that the ratios rest
  on single digits.

## Step 4: what maintainers say when they decline (`score_declines.py`, one reader)

Calibration: 9 of 10 census asks read as not declines (passes). Of the 77 comments with a decline phrase, 38 are
declines (most "no need to…" comments ask to remove something). Of the 24 declines of a convention:

| ground | n |
|---|---|
| a fact about this code or library (`place`) | 8 |
| indifference (up to you, either is fine) | 6 |
| economy (not worth the churn) | 3 |
| a later or separate PR | 3 |
| authority (ignore the bot) | 1 |
| none given | 3 |

**By the registered line, place evidence at 33% (8 of 24) is exactly at the third:** "maintainers state evidence at
the place when they decline". One label decides it, the reader is one model family, and n is 24. The facts given are
of the kind the user's picture names: the library already diverges on this naming, the construct is used only once,
the lemma is in the wrong generality anyway, a side condition defeats the suggested tactic, the folder already
names the topic. Over all review traffic on 973 PRs the phrase list finds 38 such declines; declines phrased otherwise are not
counted.

## What it says about the 5%

*Superseded by the corrections after review 4, below; kept as it was told.*


- **For these six rules of form, no rule is held by maintainers and enforced at 5%.** Either the rule as written is
  not their practice (three rules: their own code, their suggestions and the library break it at 10-86%), or the
  code already keeps it at 95-99% whoever writes it (two rules). The one mixed rule (blank lines) is broken at
  15-19% by everyone. The tension the user named, rules applied one time in twenty, does not appear here. Where a
  rule is practice, the code holds it because authors write it that way; asks are rarely needed.
- **Where they look, maintainers do act on the rules that are practice**, though mostly inside broader rewrites
  (one tactic per line: 49% gone near a comment against 5-10% elsewhere; blank lines 32% against 0-4%), and not on
  the rules that are not (4-12%).
- **When maintainers say why they leave something, a third of the time it is a fact about the place**, at the
  registered line, on 24 comments.
- **Not shown:** whether evidence at the place predicts which attended departures are left (Q3 was too small),
  and anything about the substantive rules (use the existing API, name like the siblings, drop a hypothesis),
  which no script checks.

Limits: six rules of form; round-1 attention only; "active reviewer" is a count threshold (30 logins); the control
was amended after it failed; the targeted measure undercounts fixes made inside rewrites; one reader for step 4.

## Corrections after adversarial review 4 (2026-10-17; `review4-measurement.md`, `review4-inference.md`, `review4-direction.md` beside the plan)

Three reviewers re-checked the detectors (precision 14-16 of 16 per rule), hand-checked merge outcomes, relabelled
the declines blind, and recomputed the readings with other denominators, thresholds and windows. Every number above
reproduces; several readings do not survive.

**What changes.**
- **The headline switched measures and falls as worded.** "No rule is held by maintainers and enforced at 5%"
  compared departures per opportunity. Per departure, every one of the six rules is asked at under 2%, the practiced
  ones included: one tactic per line at 5 of 443, with 81% of its departures reaching merge. The tension the user
  named appears here in a mild form: rules that are practice are kept by authors, and their few departures go
  mostly unasked, even where a maintainer looks.
- **Step 2: two rules are robustly not practice, not three.** Theorem docstrings (86% in active reviewers' own code,
  85% without the largest contributor) and term proofs on their own line (26%) hold under every cut. Line joins is
  **mixed**: counting the conforming one-line signatures in the denominator, active reviewers break it at 16.5%,
  others 10.2%, the library 6.5%; and one author carries 76 of the 176 departures. One tactic per line is **mixed**
  on tactic proofs (6.2%, 7.4%, AI-flagged 11.8%); term-mode proofs were 27% of its denominator. Class hypotheses as
  `[C x]` stand (98-100% kept), but that is Lean's ordinary form for an inferable argument, so it separates nothing.
  Blank lines around commands is two rules: 89% of its departures are a command next to another command; a command
  next to a declaration departs at 2% in every group. No Mathlib linter enforces any of the six.
- **"Maintainers' own code" is no separate source for rules of form.** It sits within 0-11 points of other authors'
  code and the library's for all six. "As much as the library" is wrong for line joins and term-proof placement:
  code untouched since the port departs at 1% and 8%, human code since then at 12-15% and 14-19%.
- **Step 3: "where they look, maintainers act on the practiced rules" falls.** Near a round-1 comment, 57% of all
  touched theorems and lemmas change by merge whatever they contain (56% of those with no departure; 19% elsewhere
  on reviewed PRs, 6% on unreviewed ones). A rewrite drops a `;` line 30 of 47 times and adds a docstring 5 of 117
  times, so the contrast between rules is where the construct sits (proof against header), not the rule. Action on
  the rule itself: one tactic per line split onto lines at 8 of 65 near a comment (1 of 174 elsewhere); blank lines
  7 of 31, mostly one PR (25908); line joins 9-16% counting joins hidden by renames. Fixes in the rule's own form are
  asked fixes: unasked attended departures were fixed that way 1 of 61, 1 of 23 and 0 of 31 times.
- **The control stands on the facts, with less reach.** The six survivors' files are outside the linter's import
  closure; the ten fixes are real rewraps. But the control tests matching by line text only. The added check is
  **12 of 15**, not 13 (one "fixed" row still holds its `;`), on 7 PRs, six in one. Amendment 1's "no other step-3
  number had been read" is not literally true: the per-rule status counts printed before the control line; nothing
  split by attention was read.
- **Q3 cannot be read at any scale here.** The arms are empty by construction: four detectors fire only where the
  header was added (edited arms 0-1), and files that break a practiced rule at 50% or more barely exist (8 of 239,
  0 of 19).
- **Step 4 falls below the line on a second reading.** A blind relabel finds 6 of 23 convention declines grounded in a
  fact about the place (26%, mixed), against 8 of 24 (interval 18-53%). About half of the 24 are a reviewer marking
  their own suggestion optional; only about 3 are a maintainer leaving another person's convention request on a fact
  about the place. Both readers are one model family.
- **Smaller.** "1,448 of 2,583 (56%)" is 1,448 of 1,903 (76%): the denominator still held the dropped theorems. Of
  the 10 line-join "fixes", 4 are not joins (an added `@[simp]` pushes the join past 100).
- **Reach.** The six rules carry 29 of 1,669 census asks with a principle (1.7%) and 5 of the 93 asks on the
  reviewer's evaluation sets. Only line breaks is among the ten rules behind the 5% figure, which came mostly from
  substantive and naming rules this probe does not reach.

**The read, at the altitude the reviews leave.** For six rules of form: two rule texts are broader than anyone's
practice; the rest are kept by authors at 83-99% without asks; departures of every rule are asked at under 2% and
mostly reach merge; where a maintainer comments, code is rewritten about half the time whatever it holds, and action
on the rule itself is uncommon (one tactic per line 12%, line joins 9-16%, blank lines 23% mostly from one PR). Maintainers rarely write why they leave something (35-38 declines found by
phrase in all review traffic). Nothing here measures the substantive conventions that carry most asks.
