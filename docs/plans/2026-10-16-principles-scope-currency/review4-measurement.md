# Adversarial review 4, part 1: are the measurements right? (2026-10-17)

**Under attack.** The read in `results/pr_review_v5/probes/attention-practice-2026-10-17/` (`PROTOCOL.md` with
amendment 1, `RESULTS.md`; commits `9be22397` to `456934f4`): (a) step 2, own practice; (b) step 3, fixed by merge
where a reviewer looked; (c) the control and its amendment; (d) step 4, the declines; (e) the headline told to the
user.

**Read.** The protocol, results and every script in the probe (`detect.py`, `places.py`, `practice.py`,
`outcome.py`, `declines.py`, `score_declines.py`, `declines_prompt.md`), the stage G rule texts in
`conventions-ceiling-2026-10-04/rules.json`, the six commits with their timestamps, the PR store, the clone, the
roster `inputs/pull_requests/rosters/mathlib_roster_2026-09-11.txt`, and `docs/questions.md`. I did not read the
other review-4 files. I read `declines_labels.jsonl` only after writing my own labels.

**Computed here.** No model call, no Lean, nothing spent. No tracked file changed except this one. Running
`outcome.py` and `declines.py` rewrote `outcomes.jsonl` and `declines_key.jsonl`; `git status` shows both
unchanged. Scripts are in
`/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/a142d916-dd29-4521-a449-00e1db067b18/scratchpad/rev4/measure/`,
each run from the worktree root with `ape/bin/python`:

| script | what it computes |
|---|---|
| `rebuild_check.py` | the round-1 file rebuilt by `apply_patch`, against GitHub's blob hash where checkable |
| `line_check.py` | each round-1 comment's `original_line` against the last line of its own diff hunk |
| `detect_sites.py` | a copy of `detect.py` that also returns every opportunity site (counts identical) |
| `sites_build.py` → `sites.jsonl` | 44,029 sites, conforming and departing, with attention variants and fate at merge |
| `sample_detector.py` → `detector_sample.txt` | seeded samples: 16 departures and 10 conforming sites per rule |
| `denominators.py`, `base_oneline.py` | line joins with one-line signatures; one tactic per line on tactic proofs |
| `p012_neighbours.py` | what sits next to a departing command |
| `letI_bug.py`, `systematic_misses.py`, `p392_recall.py` | detector misses counted over the population |
| `step2_sensitivity.py` | step 2 at 10, 20, 50 comments and the roster; new code only; per author; PR bootstrap |
| `baseline_change.py`, `p097_line_baseline.py` | how often conforming code under the same attention changes or vanishes |
| `p097_fixed_check.py`, `p097_split.py` | every `fixed` one-tactic-per-line row: split, rewritten, or still joined |
| `sample_outcomes.py` → `outcome_sample.txt`, `show_decl.py` | 40 outcome rows hand-checked at the merge commit |
| `gone_check.py` | `gone` rows found again under another name, and whether the departure survived |
| `step3_variants.py`, `line_near.py` | step 3 with wider windows, any round, the file, and the departure's own lines |
| `control_check.py`, `import_path.py` | the 16 long lines at merge, and each file's import path to the linter |
| `my_decline_labels.jsonl`, `compare_declines.py` | my blind labels of the 87 packet items, then the comparison |

The tables in `RESULTS.md` reproduce to the cell (`outcome.py` rerun; step 2 from `practice.json`).

## Verdicts

| claim | verdict | one line |
|---|---|---|
| (a) three rules not practice, two practice at 95-99%, one mixed | **weakened** | Docstrings, term-proof placement and class binders stand. Line joins is "not their practice" only because the denominator leaves out one-line signatures, and only with one author in it. One tactic per line is "practice" only with term-mode proofs in the denominator. Blank lines is two rules. |
| (b) where they look, practiced rules vanish at 32-49%, unpracticed at 4-12% | **falls** as a statement about maintainers acting | The numbers reproduce. But tactic lines with no `;` near a comment vanish at 40%; `;` lines at 46%. Blank lines' 32% is one PR. |
| (c) control failed as registered, passes outside `Mathlib/Tactic/`, 13 of 15 asked fixed | **stands** on the facts; **weakened** as a check | The linter claim is true for all six survivors. The ten fixes are real rewraps. But the control tests only line-text matching, not the declaration matcher five rules use. The added check is 12 of 15, six from one PR. |
| (d) 38 declines; of 24 convention declines, 8 give a fact about the place | **weakened** | A second blind reading agrees on 74 of 77 declines but gives 6 of 23 place (26%). By the registered lines that reads "mixed". |
| (e) the headline | **weakened** | The dichotomy "not practice, or kept at 95-99%" comes from the denominators. Two rules sit between: kept at 83-94% by human authors, and genuinely fixed at about 9-16% where a reviewer comments. That is the user's tension, in a mild form. |

---

## 1. Detector precision, recall, and the opportunity definition

**The rebuild and the comment lines are right.** 256 of 256 files whose round-1 head equals the PR's final head
are byte-identical to GitHub's blob. In 1,819 of 1,827 round-1 comments, `original_line` points at the line the
comment's own diff hunk ends on (`rebuild_check.py`, `line_check.py`).

**Hand-judged samples** (seed 20261017; `detector_sample.txt`). Each rule was judged by its literal check in
`rules.json`.

| rule | departures correct | conforming correct | what went wrong |
|---|---|---|---|
| line joins (P084J) | 16/16 | 10/10 | none; the join length is arithmetic |
| theorem docstrings (P341) | 16/16 literal; 13/16 with the rule's own `not_when` | 10/10 | three are edited, pre-existing theorems, which the rule exempts |
| term proof on its own line (P240) | 14/16 | 10/10 | `haveI :=` or `letI :=` inside a statement is read as the end of the signature |
| blank lines around commands (P012) | 16/16 | 10/10 | none literal; most of the 16 are a command next to a command (stacked `variable` lines, consecutive `end`s) |
| one tactic per line (P097) | 15/16 | 10/10 | a `;` inside a `conv => { … }` opened on the line above; 2 of 10 "touched proofs" are term-mode |
| class binders (P392) | 15/16 literal | 10/10 | `(_ : LinearOrder α)` is not a named binder; 7 of 16 come from one PR (36910, five-lemma binders) |

**The same misses, counted over all departures** (`letI_bug.py`, `systematic_misses.py`, `p392_recall.py`):

| miss | count | effect |
|---|---|---|
| P240: `let`/`have`/`haveI`/`letI` inside a statement ends the signature early | 11 of 294 (4%) | false departures |
| P097: `;` inside a bracket opened on an earlier line (the depth restarts at 0 on each line) | 24 of 443 (5%) | false departures by "not inside brackets" |
| P341: docstring above an attribute block longer than one continuation line | 5 of 2,029 | false departures |
| P392: `Nontrivial` and qualified classes (`Module.Finite`) not in the class list | 4 binders | missed departures |
| P097: several `\| … =>` alternatives on one line; tactic blocks in `def`/`instance` | not counted | missed departures |

Precision is high everywhere. The problems are in the denominators, below.

**The denominators are not the rules' applies-sets, and the gap differs by group.**

1. **Line joins leave out the conforming case.** The rule says "anything fitting in 100 characters stays on one
   line". A signature written on one line is the conforming case. The detector counts only two-line signatures as
   opportunities. With one-line signatures counted as conforming (`denominators.py`, `base_oneline.py`):

   | | registered (two-line only) | with one-line signatures |
   |---|---|---|
   | active reviewers | 176/760 (23%) | 176/1,068 (16.5%) |
   | other humans | 115/767 (15%) | 115/1,132 (10.2%) |
   | AI-flagged | 66/227 (29%) | 66/285 (23.2%) |
   | base library | 3,239/31,784 (10%) | 3,239/50,170 (6.5%) |

   At 16.5% the active reviewers fall below the 20% line. By the registered lines that reads **mixed**, not "not
   their practice". The ratio of one-line to two-line signatures differs by group (1.17 reviewers, 1.33 others,
   0.96 AI), so the registered rates do not compare across groups.

2. **One author carries line joins.** joelriou wrote 76 of the reviewers' 176 departures (48% of his own two-line
   signatures). Without him the registered rate is 100/603 (16.6%), also **mixed**. With one-line signatures
   counted, the median reviewer (23 with 10 or more signatures) departs at 8.9%. "The active reviewers break line
   joins more than other authors" is one person's habit.

3. **One tactic per line counts term proofs.** 27% of the touched theorem and lemma bodies contain no `by`. A
   term proof cannot hold a tactic. On bodies with `by`: reviewers 121/1,966 (6.2%), others 146/1,960 (7.4%),
   AI 47/397 (11.8%). By the registered 5% line that reads **mixed**. Even on the registered numbers, AI-flagged
   PRs keep it at 91%, not "95-99%".

4. **Blank lines around commands is two rules.** 375 of the 419 departures (89%) are a command next to another
   command: stacked `variable` lines, `end A` over `end B`, `section` over `variable` (`p012_neighbours.py`). A
   command next to a declaration, docstring or comment departs at 2% in every group (20/1,327; 19/1,087; 5/263).
   That half is practice. The command-to-command half is not.

5. **Docstrings: the exemption arithmetic is wrong.** `RESULTS.md` says that without edited or moved theorems,
   1,448 of 2,583 new theorem headers (56%) lack a docstring. The 2,583 still includes the dropped theorems. With
   both numerator and denominator restricted to new code it is 1,448 of 1,903 (76%): reviewers 86%, others 74%,
   AI 69%. The reading does not change. Reviewers' theorems are edited ones twice as often (38% against 17%).

## 2. The merge outcome

**The squash-merge match is right.** All 500 matched commit subjects equal the PR title after the bors prefix. No
PR number is matched by two commits. 71 PRs with departures closed unmerged.

**Labels, hand-checked** (`outcome_sample.txt`; 2 rows of each status for each declaration rule and P012, 40
rows). Every label matches its operational definition. Of the 10 `gone` rows, 8 are absent from the file at merge,
1 was renamed and 1 command was edited. `ambiguous` was a name repeated in another namespace. But the `fixed` label does not always mean fixed:

| rule | `fixed` rows | the departure is really fixed | what else |
|---|---|---|---|
| line joins | 10 | 6 (2 targeted, 4 joined while names shortened, PR 25886) | 4 false: `@[simp]` added to the header line pushes the join past 100 (3 rows), or a proof term appended to the second line (1) |
| one tactic per line | 46 | 9 split onto separate lines (`p097_split.py`, a heuristic) | 28 vanished inside rewrites; 9 still hold the `;` in an edited line (`persists` needs the exact line text) |

**"Targeted" is too strict, and "any change" is too loose.** Of the 8 near-comment `;` lines that were genuinely
split, only 2 are targeted. The other 6 sat in declarations that also changed in other ways. Master-wide renames
merged into the PR (`omega` to `cutsat`, `Fin.lt_iff_val_lt_val` to `Fin.lt_def`, seen in the sample) break the
targeted test the same way. "Any change" counts rewrites and false fixes. The measure the question needs is "the rule now holds at the same construct". For one tactic per line I
approximated it. Near a comment: **8 of 65 (12%)**. Elsewhere: 1 of 174.

**What `gone` hides** (`gone_check.py`). The declaration was searched for under another name in every file the PR
touched.

| rule | `gone`, not moved | found renamed | departure survives the rename | departure gone after the rename | no similar declaration |
|---|---|---|---|---|---|
| docstrings | 183 | 124 | 113 | 11 | 59 |
| one tactic per line | 88 | 22 | 13 | 9 | 66 |
| line joins | 38 | 19 | 6 | 13 (9 now on one line; 4 still broken, a longer name pushing the join past 100) | 19 |

`gone` hides few docstring fixes (at most 11). For line joins, renames hide 9 genuine joins (4 near, 5 far). The genuine near fix rate for line joins lies between 3 of 33 and 7 of 44 (9-16%).

**The baseline that step 3 lacks** (`baseline_change.py`, `p097_line_baseline.py`). Under the same attention,
how often does conforming code change?

| one tactic per line | `;` lines | other added tactic lines |
|---|---|---|
| comment within 3 lines of the declaration: line vanished by merge | 30/65 (46%) | 1,533/3,872 (40%) |
| comment within 3 lines of the line itself | 22/36 (61%) | 879/1,923 (46%) |
| no comment near the declaration | 13/174 (7%) | 1,161/10,950 (11%) |

Half of the commented `;` lines vanish because half of all commented tactic lines vanish. The excess specific to
the `;` is 6-15 points, about 5-8 lines. That matches the 8 genuine splits. The same holds for declarations: a
commented declaration changes by merge at 35-80% whether or not it departs (line joins 61% against 61%, one
tactic per line 69% against 57%).

**The contrast between rules is a contrast of location.** A `;` line sits in a proof, and commented proofs get
rewritten. Docstrings, two-line signatures and term-proof placement sit in the header, which a proof rewrite
leaves alone. So 49% against 4-12% compares where the departure sits, not whether the rule is practice.

**Blank lines near a comment is one PR.** 7 of the 10 near fixes, and all 7 targeted ones, are in PR 25908. Six
of them carry a census ask. The 31 near rows come from 18 PRs.

## 3. Attention

**What the proxy counts.** Round-1 inline comments: 1,872. Later rounds: 2,527, more than half of all inline
review comments. 2,256 of the later ones have a compare for their own commit. I rebuilt each such file and
mapped the comment to the declaration name or command it sits on.

**Step 3 under other proxies** (`step3_variants.py`; registered measure targeted, beside any change):

| rule | near, registered: targeted / any | within 10 lines | within 25 lines | any round, within 3 | far, registered: any |
|---|---|---|---|---|---|
| line joins | 2/33, 4/33 | 2/45, 6/45 | 2/59, 8/59 | 2/43, 7/43 | 6/210 |
| docstrings | 4/210, 8/210 | 6/288, 11/288 | 8/378, 14/378 | 5/278, 10/278 | 12/1,127 |
| term proof | 0/21, 1/21 | 0/38, 2/38 | 0/71, 3/71 | 0/32, 1/32 | 8/189 |
| blank lines | 7/31 (1 PR), 10/31 | 8/75, 11/75 | 8/103, 12/103 | 7/45, 11/45 | 6/217 |
| one tactic per line | 2/65, 32/65 | 2/72, 34/72 | 2/87, 35/87 | 2/77, 33/77 | 14/174 |

Every targeted reading holds except blank lines. That one drops from 23% ("mixed") to 11% ("left where seen") at
10 lines, and it is one PR at every window. The any-change rate for one tactic per line falls from 49% to 40-43%
as the window widens.

**The span is generous for long proofs.** For one tactic per line, only 36 of the 65 "near" departures have the
comment within 3 lines of the `;` line itself. A comment anywhere in a 147-line proof counts (`line_near.py`).

**"Not reviewed in round 1" is not "unseen".** Of the 152 PRs behind that column, 99 have a review event by
someone else (approval or review), 101 have conversation comments by others, and 19 have later inline comments.
The 0% fix rate there means maintainers approved without asking.

## 4. The control and its amendment

**The amendment's facts hold** (`control_check.py`, `import_path.py`, reading header imports only):
- At each of the four merge commits, `TacticAnalysis/Declarations.lean` does not reach `Mathlib.Tactic.Linter.Style`
  through its imports (7-9 modules in its closure). `DirectoryDependency.lean` imports only `Lean.Message`.
- The text-based linter (`Linter/TextBased.lean`) has no line-length check. So nothing in CI lints those lines.
- All ten fixed lines are re-wrapped in place: eight docstring lines, one `simp_rw` argument list, and one
  deprecated alias with its attribute moved to the line above. No file or declaration was deleted. The ten come
  from 7 PRs.

**What the control cannot show.** LONG is matched by line text. Line joins, docstrings, term proofs, one tactic
per line and class binders are matched by declaration name; blank lines by command text. The control therefore
validates neither the name matcher nor the meaning of `fixed`, which section 2 shows is the weak part. The added
check is the only test of the name matcher. Its 13 of 15 is 12 of 15: the one-tactic-per-line row in PR 34374
still holds its `;`. Six of the 15 come from PR 25908, so the check spans 7 PRs.

**What was on screen before the amendment.** The committed `outcome.py` (`c8d286d5`) printed the status counts
for every rule (fixed, persists, gone, ambiguous) before the control line. It also wrote `outcomes.jsonl` with
every row before returning. The amendment commit (13:16:54) came after that run, and the rerun wrote
`outcomes.jsonl` at 13:17:05. So "no other step-3 number had been read" is true only of the attention-split
numbers. The amendment did not touch the Q2 or Q3 code, so the risk is small. But the protocol's "nothing else is
read" was not enforced by the script.

## 5. Active reviewers and the AI flag

**The stand-in is fair.** 28 of the 30 active reviewers are on the roster of the admin, maintainers and reviewers
teams. The two who are not (kckennylau, vihdzp) carry 175 of the reviewers' 706 docstring departures. 39 PRs by
active reviewers are AI-flagged and go to the AI group.

**The readings by definition** (`step2_sensitivity.py`; reviewers' rate with a 95% bootstrap over PRs):

| rule | 10 comments | 20 (registered) | 50 comments | roster | new code only (20) |
|---|---|---|---|---|---|
| line joins | 22% not practice | 23% [18-28%] not practice | 26% not practice | 22% not practice | 25% not practice |
| docstrings | 86% not practice | 86% [82-90%] not practice | 87% not practice | 85% not practice | 86% not practice |
| term proof | 26% not practice | 26% [20-33%] not practice | 30% not practice | 25% not practice | 28% not practice |
| blank lines | 16% mixed | 15% [10-20%] mixed | 16% mixed | 13% mixed | 14% mixed |
| one tactic per line | 4% practice | 4% [3-6%] practice | 6% **mixed** | 5% practice | 6% **mixed** |
| class binders | 1% practice | 1% [0-2%] practice | 1% practice | 1% practice | 1% practice |

The threshold and the roster move little. The line-joins interval holds 20%. One tactic per line sits on the 5%
line. The denominators in section 1 move more than any of these choices.

**Concentration.** Per-author rates spread widely: line joins 0-58%, blank lines 0-80%, docstrings 20-100%. The
pooled reviewer rate is a few prolific authors' habits. Line joins is one author (section 1).

## 6. The decline reading

I rebuilt the packet (`declines_key.jsonl` unchanged) and labelled all 87 items blind, by `declines_prompt.md`,
before opening `declines_labels.jsonl`. I am the same model family as the first reader, so this is not an
independent family.

| | first reader | mine |
|---|---|---|
| calibration asks marked not a decline | 9/10 | 10/10 |
| phrase matches read as declines | 38/77 | 35/77 |
| agreement on decline | 74/77 | |
| declines of a convention | 24 | 23 |
| ground `place` | 8 (33%) | 6 (26%) |
| `economy` + `indifference` | 9 (38%) | 11 (48%) |
| registered reading | evidence at the place (at the line) | **mixed** |

Where we differ:
- D036 and D087: the first reader coded `place`. I coded `indifference`: each ends with an explicit "up to you"
  or "feel free to ignore". Each also names a technical fact (an edge case that causes no issue; defeq abuse).
  Both readings are defensible, and the reading turns on them.
- D044: the first reader coded a convention decline (`scope`). I read it as a request to move an instance back.
- D053 and D061: the first reader coded content declines. I read both as asks with one optional sub-point.

"Exactly a third" does not survive a second reading: 6 to 8 of 23 to 24, either side of the line. About half of
the convention declines (12 of my 23) are reviewers marking their own suggestion optional. They are not
maintainers leaving a departure they saw. The frame therefore says little about the negative half the protocol
asked about.

---

## Corrections

1. `RESULTS.md`, step 2 table, line joins row: "**23%** (176/760) | 15% | 29% | 20% (22/108) | 10% | not their
   practice" → add a note that the denominator leaves out one-line signatures. With them: reviewers 16.5%, others
   10.2%, AI 23.2%, base 6.5%; reading **mixed**. Without one author, even the registered denominator reads mixed
   (16.6%).
2. `RESULTS.md`, step 2 table, one tactic per line row: add that on proofs containing `by` the rates are 6.2%,
   7.4% and 11.8%; reading **mixed** by the 5% line.
3. `RESULTS.md`, step 2 table, blank lines row: add that 89% of its departures are a command next to a command,
   and a command next to a declaration departs at 2% in every group.
4. `RESULTS.md`: "dropping all of them from the count still leaves 1,448 of 2,583 new theorem headers (56%)" →
   "1,448 of 1,903 new theorem headers (76%)".
5. `RESULTS.md`: "the active reviewers break line joins *more* than other authors" → "one active reviewer
   accounts for 76 of the 176; without him reviewers and others break line joins alike".
6. `RESULTS.md`: "Two are held everywhere, at 95-99%, by every kind of author." → "Class binders are held at
   98-100% by everyone; one tactic per line at 88-94% on tactic proofs, 91% in AI-flagged PRs even by the
   registered count."
7. `RESULTS.md`, step 3: "Attention matters only for the rules that are practice. Near a comment, departures of
   the two rules that are practice or mixed vanish at 32-49% against 0-10% elsewhere." → "Near a comment, a `;`
   line vanishes at 46%, and a tactic line without `;` at 40%. The excess is about 8 genuine splits of 65 (12%,
   against 1 of 174 elsewhere). Blank lines' 32% is one PR (25908; 7 of 10 fixes). The gap to the header rules
   reflects where the departure sits, proof or header, not whether the rule is practice."
8. `RESULTS.md`, step 3 bullet: "Half of its departures near a comment are gone by merge, but 30 of those 32 went
   with other changes" → add "and 2 of the 32 still hold the `;`; conforming tactic lines under the same attention
   vanish at 40%".
9. `RESULTS.md`, step 3 table: "line joins … near: any change 4/33 (12%)" → mark that 1 of the 4 is `@[simp]`
   added to the header. Of the 10 `fixed` line-join rows, 4 are not joins.
10. `RESULTS.md`, control: "of the 15 departures with a census ask under the same rule within a line, **13 were
    fixed by merge**" → "12 of 15 (one `fixed` still holds its `;`), on 7 PRs, 6 of them in one PR".
11. `RESULTS.md`, amendment narrative and `PROTOCOL.md` amendment 1: "No other step-3 number had been read" → "The
    per-rule status counts (all attention pooled) were printed before the control line; nothing split by
    attention was read".
12. `RESULTS.md`, step 4: "**By the registered line, place evidence at 33% (8 of 24) is exactly at the third**" →
    "at the line on one reading (8 of 24) and below it on a second blind reading (6 of 23, mixed); about half are
    reviewers marking their own suggestion optional".
13. `RESULTS.md`, "What it says about the 5%", first bullet: "Either the rule as written is not their practice
    (three rules …), or the code already keeps it at 95-99% whoever writes it (two rules)" and "The tension the user
    named, rules applied one time in twenty, does not appear here." → "Docstrings and term-proof placement are not
    practice. Class binders, and blank lines between a command and a declaration, are kept at 98%. Line joins and
    one tactic per line are kept at 83-94% by human authors (77-88% in AI-flagged PRs), and where a reviewer
    comments, their departures are genuinely fixed at about 9-16% and 12%. For those two the tension appears in a
    mild form."
14. `RESULTS.md`, second bullet: "Where they look, maintainers do act on the rules that are practice, though mostly
    inside broader rewrites" → "Where they look, the code is rewritten at the same rate whether or not it departs;
    the departure-specific effect is about 8 of 65 for one tactic per line and one PR for blank lines".
15. `docs/questions.md`, the attention-practice entry: replace "three as written are not the maintainers'
    practice (their own code breaks line joins at 23% …)" with "two" (docstrings 86%, term proofs 26%). Replace
    "two are practice and every kind of code keeps them at 95-99%" with corrections 1-3 and 6. Replace "Near a
    comment, departures of the practiced rules vanish at 32-49% (mostly inside rewrites …)" with correction 7. Replace
    "Of 24 stated declines of a convention, 8 give a fact about the place (one reader, at the registered third)"
    with correction 12. Replace "No rule is held by maintainers and enforced at 5%" with correction 13.
16. `docs/questions.md`, the stage-H entry: "line breaks as written are broader than maintainers' own suggestions
    (28% of their two-line signatures joinable)" → the denominator is two-line signatures only, as in correction 1;
    that comparison needs one-line signatures before it supports "broader".
