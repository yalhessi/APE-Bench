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
