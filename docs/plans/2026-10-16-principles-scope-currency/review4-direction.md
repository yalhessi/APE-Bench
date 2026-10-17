# Adversarial review 4, part 3: where the thread leaves the project, and what to do next

**Under attack.** The read of `results/pr_review_v5/probes/attention-practice-2026-10-17/` (`PROTOCOL.md` with
amendment 1, `RESULTS.md`; commits `9be22397` to `456934f4`), and the headline given to the user: "for these six
rules of form, no rule is held by maintainers and enforced at 5% ... where they look, maintainers act on the
practiced rules, mostly inside rewrites." This part attacks the direction. Other reviewers attack the measurements.

**Read.** The plan with amendments 1 and 2; stage H's RESULTS with the review-3 corrections; the stated-grounds,
enforcement-at-departures, library-knowledge and ask-reading probes; `docs/questions.md`, `docs/dead-ends.md`,
`docs/todo/README.md`, `docs/todo/conventions-nature.md`, `docs/todo/adjudication-rubric.md`,
`.claude/rules/mathlib-review.md`; the three review-3 files.

**Computed here.** No model call, no Lean, nothing spent, no tracked file changed except this one. Scripts in
`/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/a142d916-dd29-4521-a449-00e1db067b18/scratchpad/rev4/direction/`,
run from the worktree root with `ape/bin/python` and `PYTHONPATH=$PWD:$PWD/src`:

| script | what it computes |
|---|---|
| `rewrite_base.py` | every theorem or lemma a round-1 diff touched on merged val1000 PRs (5,618): near a round-1 comment or not, which of the six rules depart in it, whether its text changed by merge |
| `fix_given_change.py` | joins that to `outcomes.jsonl`: how often a rewritten declaration loses its departure, per rule; Fisher tests |
| `unreviewed_load.py` | departures a PR, per rule, on the 414 PRs with no round-1 comment by anyone but the author |
| `census_share.py` | census asks under the six rules, under stage G's 52 rules by check kind, and in the 93 asks of the reviewer's evaluation sets |
| `head_entries.py` | census entries with 15 or more asks: form, stage G check kind, evaluation asks under them |
| `reviewer_form_findings.py` | form findings (keyword count) by the free reviewer with and without the conventions section |
| `held_unused.py`, `demand_asks.py`, `never_reached.py` | the ask-reading rows: held-but-unused entries; asks missed for "maintainers enforce it here"; asks no condition reaches, by knowledge code |
| `currency_signal.py` | for the migrations behind never-reached asks: merged commits adding the form, and val1000 comments naming it, by month (counts only) |
| `theorem_share.py` | share of new theorem-or-lemma headers written `theorem`, by quarter (a currency check on the docstring rule) |

---

## 0. Verdicts, as they bear on direction

| claim | verdict | the number |
|---|---|---|
| (a) three rules as written are not practice; two are | **stands, for six rules that hold 1.7% of asks** | The six hold 29 of the 1,669 census asks with a principle (37 counting second labels) and 5 of the 93 asks on the reviewer's evaluation sets. Only line breaks is among the ten rules behind the 5% figure. |
| (a), the reading "maintainers' own code" as a source | **falls as a separate source** | Active reviewers' own code is within 0-11 points of other authors' and of the library for every rule, and worse on line joins (23% against 15% and 10%). Their code says nothing the library does not. |
| (b) near a comment, practiced rules' departures vanish at 32-49% | **weakened: it is the rewrite rate** | Near a round-1 comment, 57% of touched declarations change by merge whatever they contain (193 of 347 with no departure of any rule). A rewrite drops a `;` (30 of 47) and almost never adds a docstring (5 of 117). |
| (b) Q3 too few to read | **stands, and scale will not fix it** | The arms are empty by construction (§1.3). |
| (c) the control, amended | not attacked here | The amendment changes no direction. |
| (d) a third of stated declines name a place fact | **stands at its altitude; the source is exhausted** | 38 declines in all review traffic on 973 PRs. No larger n exists on val1000. |
| (e) "no rule is held and enforced at 5%" | **weakened: true of six rules of form, silent on the rules that made the 5%** | The 5% came from substantive and naming rules, whose departures are real at 33-65% of situation places and persist to merge (stage H). |
| (e) "where they look, maintainers act on the practiced rules" | **falls as stated** | The registered targeted measure is 3% for one tactic per line. Departing proofs are rewritten a little more often than others (31 of 45 against 193 of 347, one-sided p = 0.06). Blank lines (7 of 31 targeted) is the one rule with evidence of action on the rule itself. |

---

## 1. What the thread has established

### 1.1 Measured

| finding | number | source |
|---|---|---|
| The "5% of applicable places" was not a rate per departure | Placement: 85-97% of "departures" were not departures. Stage H: the 205 places were places where a rule's situation occurs, on 82 declarations. | enforcement probe; stage H step 1 |
| An asked departure is fixed | 8 of 9 (detectors), 5 of 5 (stage H), 13 of 15 (this probe) | all three |
| Real departures persist to merge unasked | Dot notation: 2 of 113 unasked fixed. Stage H's literal departures: 23 of 27 persist. | enforcement; stage H step 4 |
| Whether code changes by merge tracks attention | Touched declarations change 57% near a round-1 comment, 19% elsewhere on reviewed PRs, 6% on PRs with no round-1 comment (`rewrite_base.py`) | this review |
| Departures change only as by-products | Near a comment, a departing declaration changes at about the rate of any declaration (table in §1.2). Stage H: every literal departure that changed sat in a declaration an ask about something else rewrote. | this review; review 3 |
| For six rules of form, maintainers' code matches everyone's | Three texts broken at 15-86% by everyone; two kept at 95-99% by everyone; reviewers within 0-11 points of others and the library | this probe, step 2 |
| Ask rate per real departure, where measured | Line joins 0.8% (3 of 369); dot notation 2-10%; stage H's ten rules 4-17%, with intervals that hold 10% | review 3; enforcement; stage H |
| When maintainers give a reason | 37% of asks state one; a technical fact or a principle leads; first-person taste is about 2% of all asks; area-level scope is under 2% of stated grounds | stated grounds |
| The negative half in maintainers' words | 38 declines in all review traffic on 973 PRs; of 24 declines of a convention, 8 name a place fact (one reader) | this probe, step 4 |

### 1.2 The rewrite base rate, which the read left out

Theorem and lemma declarations a round-1 diff touched, on merged PRs, changed or unchanged at merge
(`rewrite_base.py`, `fix_given_change.py`):

| where | any touched declaration | departs no rule | departs one tactic per line | departs theorem docstring | departs line join |
|---|---|---|---|---|---|
| within 3 lines of a round-1 comment | 348 of 613 (57%) | 193 of 347 (56%) | 31 of 45 (69%) | 117 of 211 (55%) | 17 of 28 (61%) |
| reviewed PR, not near | 443 of 2,364 (19%) | 281 of 1,483 (19%) | 18 of 83 (22%) | 130 of 686 (19%) | 17 of 100 (17%) |
| PR with no round-1 comment | 108 of 1,735 (6%) | 64 of 1,071 (6%) | 4 of 64 (6%) | 40 of 531 (8%) | 2 of 77 (3%) |

What a rewrite does to the departure, near a comment:

| rule | departures in a rewritten declaration | of those, departure gone | departures in an unchanged declaration | of those, gone (targeted) |
|---|---|---|---|---|
| one tactic per line | 47 | 30 | 18 | 2 |
| theorem docstring | 117 | 5 | 93 | 3 |
| line join | 17 | 2 | 11 | 2 |
| term proof on its own line | 9 | 1 | 12 | 0 |

So attention matters, and it acts on declarations. A maintainer's comment near a declaration is followed by its
rewrite more than half the time, whatever rule it departs. A rewrite of a proof usually drops its `;`; a rewrite of
a theorem leaves its missing docstring missing. The read's contrast between practiced and unpracticed rules near a
comment is mostly this difference between constructs. The evidence that maintainers act on one tactic per line as
such is the targeted 2 of 65 and a 13-point excess in rewrites that does not reach p = 0.05.

### 1.3 Q3 cannot be read at any scale as specified

Near-comment departures with an outcome, by arm (from `outcomes.jsonl`):

| rule | new | edited | file conforms (≤ 10%) | file departs (≥ 50%) | targeted fixes |
|---|---|---|---|---|---|
| line joins | 32 | 1 | 8 | 1 | 2 of 33 |
| one tactic per line | 65 | 0 | 35 | 0 | 2 of 65 |
| theorem docstring | 188 | 22 | 2 | 146 | 4 of 210 |
| blank lines | 31 | 0 | 4 | 1 | 7 of 31 |
| term proof placement | 21 | 0 | 2 | 1 | 0 of 21 |
| class hypotheses | 4 | 0 | 1 | 0 | 0 of 4 |

- Four of the six detectors fire only where the header line itself was added, so an edited declaration enters
  only when its header was rewritten.
- For the two practiced rules, files that break them at half their opportunities barely exist: 8 of 239
  one-tactic departures, 0 of 19 class-binder departures, over all attention levels.
- The outcome has almost no variance to explain: targeted fixes run 0-6%, except blank lines.
- The store holds round-1 diffs for 4,110 PRs, about four times val1000. Four times an empty arm is still empty.

### 1.4 Inferred, not measured

- **"The low rate measures our rule texts."** Shown for namespace placement, line joins, theorem docstrings and
  term-proof placement. Not true for dot notation. **Unknown for the head of the census**: a finishing tactic
  (56 asks), names built from the statement (54), use the existing API (37), merge steps (37). These are where
  the 5% was measured, and no practice rate exists for any of them.
- **"Silence is attention."** Strongly suggested: survival tracks a 3-line attention proxy, at 5,618
  declarations. But the proxy is not reading. A maintainer can read a file and comment only at one place.
- **"Maintainers decide at attended places on evidence at the place."** Untested. Q3 is unreadable. The declines
  are 24 comments read by one reader, exactly at the line.
- **Scope and currency as layers.** Scope is weak in what maintainers say (area under 2% of stated grounds).
  Currency is untested beyond `grind` adoption, and §3.1 below is the first cut at it.

### 1.5 In plain words

Maintainers ask about few of the places a convention seems to apply for two measured reasons. First, many of
our convention texts are broader than what anyone, maintainers included, writes. Second, departures that are
real are fixed when a maintainer happens to rewrite the code around them, and mostly nowhere else. Whether
maintainers, having seen a real departure, leave it on evidence at the place is still open. The record holds
too little written negative reasoning to settle it. For the conventions that carry most asks, we do not yet
know whether the text is the practice.

---

## 2. What it means for the reviewer

| proposal | what the thread says | already on record? | verdict |
|---|---|---|---|
| Drop or restate rule texts that maintainers' own code breaks (docstrings for theorems, line joins, term placement) | Applied literally on the 414 PRs with no round-1 comment, the six texts would file 2.5 form findings a PR. 1.83 of those (docstrings 1.44) are departures of texts nobody keeps; 0.34 are of the practiced rules (`unreviewed_load.py`). The control-PR bar is 2.0. The line-join sentence is in 12 of 26 conventions sections, the docstring sentence in 7. With the section, the free reviewer's dev output holds about 51 form findings of 322, against 4 of 203 without (keyword count). | Not done. The rules file (2026-10-16) already says to calibrate a text before counting with it. | **Do it, folded into the next delivery change.** Recall stake: at most 1 of 93 asks. It removes volume, not misses. |
| Keep the practiced rules, stated as strict | Class hypotheses as `[C x]` (99% kept): its three asks on one evaluation PR were reached in 0 of 3 sessions without the section and 3 of 3 with it. | Matches "the sentence carries most of what is needed" (ceiling probe). | **Keep.** Practiced rules are rare departures, so strictness costs little volume. |
| Build convention texts from maintainers' own code | For rules of form their code equals the library's, so it adds nothing. The line maintainers hold, where one exists, is in their asks and fixes. With 0-20 asks a rule, a derived line cannot be validated: primes failed with 9 asks, twice. | The library as decider is closed (`dead-ends.md`, 7 of 41). It **reopens if** paired with a record of maintainers' preference. Asks, fixes and recent adoption are such records. | **Only for entries with 30 or more asks**, which are substantive and need Lean or elaboration (§3.2). |
| Tell the reviewer each convention's standing (practice rate, recent adoption) | Supplies the "maintainers enforce it here" belief. That belief was what was missing for 14 of 66 missed asks (DX) and 7 (AP). | A blanket version failed: the precedence paragraph read +0.20 / +0.18 on its own PRs and −0.04 / −0.01 off them; "offered for verification" moved +0.00 to +0.03. | **Untried only as a measured, per-convention currency field.** At risk of being the precedence paragraph with numbers. Test it only where §3.1's premise holds. |
| Let gold's silence count against a finding | Silence at a departure of a text nobody keeps is agreement. Silence at a practiced-rule departure is attention, but those are 0.34 a quiet PR. | Recall already ignores silence. The control-PR bar is the only place it counts. | **No change.** For form findings the bar is right. For substantive findings it is untested (§3.4). |

**The one reviewer-side gap this thread points at.** Of the 93 asks on the evaluation sets, 24 are reached by none
of the seven conditions in `asks_all.tsv`. Neither model nor harness has moved them. By the ask-reading's knowledge
code, 9 of the 24 are a mechanism or a newer form (`never_reached.py`):
- four are the `grind` roll-out on two PRs;
- the others are `to_fun`, `mk_iff`, the `toLinearMap` naming, an autoparam constructor, and a sibling's form.

The selector picked the entry for one of the nine: the `toLinearMap` naming, which all three sessions considered
and dropped. Seven had no entry in the section, and one is outside the census. At the `grind` asks the sessions
named the concern and dropped it. This is the currency layer, R5 in the plan, and it is the only item in the thread
aimed at the never-reached core.

---

## 3. Ranked next steps

Ranked by expected progress per session day toward issue recall. "Ceiling" is the most the item could add on the
93 evaluation asks if everything went right.

| rank | work | question or change | cheapest first test on disk | stops it | cost | ceiling |
|---|---|---|---|---|---|---|
| 1 | **Currency at the never-reached asks** (R5, reframed for the reviewer) | Did a dated repository or review signal for the asked form precede each never-reached mechanism or newer-form ask? If so, does an ask-free "recently adopted here" digest let the reviewer file it? | For the 9 asks (then library-knowledge's 19 "points to, a choice remains"): adoption of the asked form in merged commits over the 90 days before base, against the 90 before; earlier census asks naming it (signal PR ≠ ask PR, a day earlier). First cut done (§3.1). | Fewer than 5 of 9 have a preceding signal; or, one turn at each place on the free model, the digest yields the asked change at fewer than 3 of 9 | Half a day deterministic. Then about an hour of free-model serving on `first` for the one-turn test, and 4 PRs × 2 reps of sessions only if it passes | 9 of 93, clustered on about 7 PRs; census-wide, the entries naming `grind`, generators or such tags hold about 2% of asks |
| 2 | **Practice and line for the compile-checkable head conventions**, a finishing tactic first (56 asks), then drop a hypothesis (18), a term for a short block (21) | Answers the user's question for the rules the 5% came from: is the text the practice, and if not, what line do the asks draw? | A fixed closer battery (`simp`, `grind`, `omega`, `positivity`, `fun_prop`, `norm_num`, `rfl`, `aesop`) at a seeded 60 multi-step closing blocks in active reviewers' merged code and 60 in other code, on stage H's built workspaces. No agent. | Maintainers' code departs at 5% or less (then the 5% is attention, and the reviewer should apply it strictly). At 20% or more, derive a line on half the asks and test on the other half; stop if no line separates asked blocks from maintainers' own departures by 2x. | 1-2 session days; Lean CPU hours (`lake env lean`, about 10 s a check); no tokens | 14 evaluation asks sit under compile rules, 5 of them overlapping rank 1; census 207 asks (11%) |
| 3 | **Restate or drop the three unpracticed form texts in the delivered section**; mark the practiced ones strict | Removes volume the thread shows is unwanted | Done: §2's counts | — | An edit; measured only inside the next delivery run | ≤ 1 of 93 |
| 4 | **Decompose control-PR volume with the rules' own checks** (the adjudication todo's `valid_not_an_ask` boundary, for checkable findings) | Says whether the volume bar on the high-reach designs (the all-session union at 0.63-0.68, the per-place engine at 0.55) measures noise or unattended truth | The form findings among design G's and the four-pass union's control-PR output, classified by the six detectors and step 2's practice. Deterministic for those. | Form findings on control PRs mostly at unpracticed texts: the bar holds for them, and stop | Half a day for form findings; substantive ones need rank 2's checks | None on recall. It changes how volume designs are read, and may never be reported as precision (`.claude/rules/mathlib-review.md`) |
| 5 | **Q3, redesigned** | Do place facts predict which attended departures are left? | Only where asks exist: dot notation (24 asks) and line breaks (14-20). Asked against attended unasked places, predicates fixed first (review 3, §2.5). | Fewer than 20 attended departures per arm | 1 day | About 0 |
| 6 | **Declines over the whole PR store** | Firms up the negative half in maintainers' words | A phrase scan over the 32,851 PRs' comments, then one reader | — | 1 day plus a reader run | 0 |

### 3.1 Rank 1, first cut (`currency_signal.py`, `currency_signal.txt`)

| form | merged commits adding it, by month | val1000 comments naming it (askers) | ask PR created | reading |
|---|---|---|---|---|
| `grind` attribute | 2025-07 10, 08 12, 09 21, 10 14, 11 20, 12 24 | Jul 5 (4), Aug 8 (4), Nov 6 (3), Dec 6 (3) | 32875: 2025-12-14; 33098: 2025-12-19 | signal precedes by about five months (4 asks) |
| `to_fun` | first in 2025-12 (7) | one, 2026-01 | 33117: 2025-12-20 | concurrent, not preceding (1 ask) |
| `mk_iff` | 2-13 a month through 2025 | 3 in ten months | 42814: 2026-08-16 | an old mechanism, not a migration (1 ask) |

The comment count matches any mention of `grind`, not only tag asks, so it is an upper bound. Four of the
nine pass a crude form of the test. All four are one migration on two PRs, so the effective n is about three.
The next step is the remaining five, then the one-turn test.

**Fences.** "Linter-as-convention-oracle" and "Surface proxies for convention discovery" (`dead-ends.md`) rule
out an adoption count as the discoverer of a convention. Both reopen only when the count corroborates a semantic
source. Here that source is the census entry for the same migration (tag `@[grind =]`, generator attributes),
which the selector did not pick. The design is the norm store's maturity field (`pr-review-v5-principled-design.md`
§D2, designed, never built) and `conventions-nature.md` study 4's sub-hypothesis. It is not on the dead-end list.

### 3.2 Rank 2, why a battery and not an agent

Stage H's checker spent 248 tool calls on 59 places. A practice rate needs about 120 blocks a rule, so an agent
checker would cost millions of tokens. For a finishing tactic and an unneeded hypothesis, the check is
mechanical: try the closers, or delete the binder and recompile. The battery is the closer probe of 2026-09-26
and the open `review-mechanical-sweeps.md` todo, used to measure practice before it is used to file. If a line
is found, using it to filter what a sweep files is close to selection, and the user should rule on it first.

### 3.3 What I would do first, and why

**Rank 1's first test, then rank 2's battery in parallel.** Rank 1 takes half a day, costs nothing and can fail
quickly. It is also the only item aimed at asks that no model or harness reaches. Rank 2 needs no tokens, and it
is the measurement that answers the user's question for the rules the 5% was computed on. A finishing tactic
also covers two of rank 1's `grind` asks. Rank 3 waits for the next delivery change. Ranks 4-6 go no further
until rank 1 or 2 gives them a reason.

### 3.4 What each would change if it succeeded

- **Rank 1:** a currency field on the conventions the reviewer receives, computed ask-free from merged code
  and earlier asks. It is the first general element in this thread that adds knowledge the reviewer provably
  lacked.
- **Rank 2:** the census's top entry gets a measured line, or a measured "this is a preference applied where
  seen". Either way the reviewer is told the truth about its most-asked convention, and the same battery serves
  the other compile rules.
- **Rank 4:** whether the 2.0 bar should keep discounting the designs that reach 0.55-0.68.

---

## 4. What to stop doing

- **Probes of the 5% on rules of form.** The six hold 1.7% of asks, and the answer is in: such a rule is either
  kept by authors or not a rule anyone keeps.
- **Reading silence or declines for the negative half on val1000.** Attention dominates survival at 5,618
  declarations, and 38 written declines are all there are.
- **Q3 as specified, at any scale.** Its arms are empty by construction.
- **Reading "gone by merge" as action on a rule** without the rewrite base rate beside it. The base rate near a
  comment is 57%.
- **"Maintainers' own code" as a source distinct from the library** for rules of form.
- **New probes in this thread without a stated recall ceiling.** The auto-memory rule (2026-10-07) is written for
  paid runs, and these probes spent nothing. But the three since 2026-10-16 measured rules holding about 2-12% of
  asks (dot notation, primes and placement; stage H's ten; these six), and none says what it would change for
  recall.

---

## Corrections

1. `RESULTS.md`, Step 3, bullet: "**Attention matters only for the rules that are practice.** Near a comment,
   departures of the two rules that are practice or mixed vanish at 32-49% against 0-10% elsewhere. For the three
   rules that are not practice, they vanish at 4-12% near a comment, barely above the rest."
   **Should read:** "Near a round-1 comment, 57% of all touched theorem and lemma declarations are rewritten by
   merge, whatever they contain (193 of 347 that depart no rule). Elsewhere on reviewed PRs the rate is 19%, and
   6% on PRs with no round-1 comment. A rewrite drops a `;` (30 of 47) and almost never adds a missing docstring
   (5 of 117). So the gap between rules near a comment is mostly what a rewrite does to each construct. The
   departing proofs were rewritten slightly more often (31 of 45, one-sided p = 0.06). The targeted measure is
   the one that speaks to the rule: 3% for one tactic per line, 23% for blank lines."
2. `RESULTS.md`, "What it says about the 5%", second bullet: "**Where they look, maintainers do act on the rules
   that are practice**, though mostly inside broader rewrites (...), and not on the rules that are not (4-12%)."
   **Should read:** "Where they comment, maintainers' comments are followed by rewrites of the code near them
   (57% of touched declarations), and departures go when the rewrite removes them. Action on a rule itself shows
   only for blank lines around commands (7 of 31 fixed with the neighbourhood unchanged); for one tactic per line
   it is 2 of 65."
3. `RESULTS.md`, "What it says about the 5%", first bullet: "The tension the user named, rules applied one time
   in twenty, does not appear here." **Add:** "These six rules hold 29 of the 1,669 census asks with a principle
   (1.7%) and 5 of the 93 asks on the reviewer's evaluation sets. Only line breaks is among the ten rules behind
   the 5% figure. That figure came from substantive and naming rules, whose departures stage H found real at a
   third to two thirds of situation places and persisting to merge, and this probe does not reach them."
4. `RESULTS.md`, Step 2, "**Read.**", last sentence: "None is a rule the maintainers' code keeps while PR code
   breaks it." **Add:** "Maintainers' own code is within 0-11 points of other authors' and the library's for
   every rule, and further from the rule on line joins (23% against 15% and 10%). So for rules of form their code
   is no separate source of the line they hold; where one exists, it is in their asks and fixes."
5. `RESULTS.md`, Step 3, "**Place predicates (Q3) could not be read.**" **Add:** "The arms are thin by
   construction, not only by n. Four detectors fire only where the header line was added, so edited declarations
   are few (near a comment: 1 for line joins, 0 for one tactic per line). Files that break a practiced rule at
   half their opportunities barely exist (8 of 239 one-tactic departures; 0 of 19 class-binder departures). The
   targeted outcome runs 0-6% except blank lines. The 4,110 PRs with a stored diff would not fill the arms."
6. `RESULTS.md`, Limits: "Limits: six rules of form; ..." **Add:** "they hold 1.7% of census asks; 'gone by
   merge' near a comment is read against a 57% rewrite rate for any touched declaration (review 4)."
7. `docs/questions.md`, the attention-practice line: "Near a comment, departures of the practiced rules vanish at
   32-49% (mostly inside rewrites; 3% as a targeted fix) against 0-10% elsewhere. No rule is held by maintainers
   and enforced at 5%." **Should read:** "Near a comment, 57% of touched declarations are rewritten by merge
   whatever they contain, and departures go with the rewrite when it removes the construct (a `;` 30 of 47 times,
   a missing docstring 5 of 117). Targeted fixes are 3% for one tactic per line and 23% for blank lines. For these
   six rules (1.7% of census asks; only line breaks is among the ten behind the 5%), no rule is held by maintainers
   and enforced at 5%; the substantive rules are not measured."
8. `docs/questions.md`, same line: "three as written are not the maintainers' practice (their own code breaks
   ...)". **Add:** "maintainers' own code matches other authors' and the library's within 0-11 points for all six."

Also, outside the two files named: the plan's amendment 2 conditions R4 on "rules where this probe finds attended
departures left and a predicate". No predicate was readable, so by its own condition R4 does not run. The plan
should say so.
