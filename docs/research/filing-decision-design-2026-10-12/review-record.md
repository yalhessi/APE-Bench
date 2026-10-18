# Adversarial review of `filing-decision-design-2026-10-12.md` — lens: the project's record

Reviewer: record lens (one of four). Worktree `ask-reading`, commit `de7425b6`, 2026-10-12. Written
incrementally; a section marked `(pending)` was not reached. No model spend, no git state change.
`[verified]` = read in the cited file, run artifact or computed from the committed data;
`[inferred]` = my reading of the evidence, stated nowhere in the record. Line numbers are those of
the files at `de7425b6` (`develop` at `19bd1fd8` for the shared docs).

## Verdict table

| # | claim or element of the draft | verdict | evidence |
|---|---|---|---|
| 1 | §0, §3.4: the general design is "an explicit authority order", which "the record's experiments lacked" | **already-exists** for ranks 1, 3, 4 and most of the inadmissible grounds | `src/mathlib_review/analysis/probes.py:442-456` `CONVENTIONS_PRECEDENCE` (stage D's DP and stage AP): conventions and maintainers' examples "outrank your own judgement of this code"; ruled out as grounds: "correct, clear or idiomatic as it stands", "minor or a matter of taste", "**this file, its author or its neighbours do it differently**", "Mathlib does not require it or a maintainer might not insist", "wording does not quite fit"; "where you cannot make or check the change, file it as a question"; "leave a place unfiled only where a line you quote, or a check you ran, shows it already has the form". That is the draft's rank 1 (check clears), rank 3 (asserted demand), rank 4 (own judgement last), the failed-check-to-question rule, and five of the seven inadmissible grounds. It ran three reps on DeepSeek with the asks (DP, `conventions-ceiling-2026-10-04/README.md:1191-1300`) and three reps without (AP, `:1399-1461`); AP read null on every fresh cell (`one-reviewer-table-2026-10-10/README.md:185`: P14's other four −0.04, D12 −0.01). [verified] |
| 2 | §3.2 rule 1: a check that fails on the reviewer's own candidate becomes a question, not a clearance | **already-exists, as the record's named untried item; and once set aside** | Untried list of stage G, `conventions-ceiling-2026-10-04/README.md:721-722`: "**An asserting lead:** the same candidates, told that maintainers raise these and to file each, as a question where a check fails". DP's paragraph already asks for it and "**DP filed no finding in question form,** over 131 anchored findings" (`:1279`). "Questions legal everywhere" was set aside by the adversarial round of the generation plan: "42814 alone carried about 60 check items; every failed check admits 'a variant might work'. Narrowed to `ask_author`" (`docs/plans/2026-10-06-generation-without-suppression.md:197`). And a question cannot score: judge v9 "A defense, **question**, risk, or no-change conclusion is false" (`src/mathlib_review/judge/protocol.py:65`); the blind matchers' rubric has no question form (`construction-demo-2026-09-29/matcher_rubric.md`, grep `question`: 0). The draft's §8 names the rubric gap but §6 does not make it a precondition. [verified] |
| 3 | §3.2 rule 2: the library's current practice with direction outranks siblings and plurality | **amend** — siblings are already inadmissible under DP/AP (row 1); the "direction" source does not exist; the motivating instance is contested by the record | No deprecation stream, mechanism catalogue or dated-form index is built (the idiom-checker dead end's reopen condition is exactly "retrieval by *mechanism* ... a base-commit `Mathlib/Tactic/**` docstring index", `docs/dead-ends.md:29-33`; still unbuilt). On d0045/d0046 the record says the corpus does not carry the direction: "The elaborated corpus names 33337's coercion `coe`, not `toLinearMap` ... 37 times and `toLinearMap` 3 ... **Do not cite 21:7 as corpus support for it**" (`.claude/rules/mathlib-review.md:296-304`). The "newest form" there is the maintainer's own asks and a three-day-old review, i.e. rank 3 (demand), not rank 2. [verified] |
| 4 | §3.2 rule 1 / §3.3: "a linter", "a count against a threshold the rule states" are the top authority and a passing check clears the cell | **conflicts** with two conventions dead ends | `docs/dead-ends.md:197-212` (linter-as-convention-oracle): a linter "dates *availability*, not the convention", answers "where **can** X be used", is a `stated` source only, "never as the oracle"; `:213-231` (surface proxies): "each substituted a statistic *about* code for the semantic question"; `:286-295`: `naming_norm`'s bar swept 0.80 → 0.20 changed no verdict — the threshold was never what bound. [verified] |
| 5 | §3.1 "silence is not a disposition", the (object, question) cell | **already-exists**; acknowledged in §4 | D1: `structured.py:6` "Silence is not a verdict", `:247`; `target_verdicts` (`candidates.py`, dead-ends `:131`); plan `2026-10-02-review-designs.md:73`. [verified] |
| 6 | §2, §6 premise: a contract on the filing decision moves the free reviewer | **over-claimed** (see Q3) | D1 on gpt_5.2: 2, 2 against the carried baseline's 2-3, "98% of cells `no_issue` with reasons; the unit of decision does not bind" (`docs/plans/2026-10-03-after-structure.md:18`). D1 on Opus 10, 10 against 9, 9, 7, read as consistency, not a frontier (`:21-30`). Unified contract 3/10 vs 2/10 under a bar of 5 (`dead-ends.md:131-150`). `forbid_abstention` 0.20 → 0.50: one rep, 4 PRs, control 1 → 36 (`:81-90`). DP +0.20 with the asks given; AP null off its discovery sample. [verified] |
| 7 | §2: "Stage G (+0.000) fails because a rule plus a check leaves the authority order where it was" | **amend**: relabels the record's own reading, without citing it | Result 5 (`README.md:660-724`): what E carried and G did not is "the assertion: a list of one to five conventions is a claim that maintainers ask for each of them here. Given a long list to verify, half of it decoys, with an instruction to drop what does not depart, the reviewer applies its own bar". The dossiers round: "**The assertion carried the gain, not the wording**" (`docs/todo/conventions-dossiers-exams.md:124-128`); the assessment §5 point 4 (`conventions-assessment-2026-10-12.md:151-154`). Neither document is cited by the draft (grep: 0). [verified] |
| 8 | §4: "the disposition paragraph S2 — one inadmissible ground removed" | **mischaracterised** | `probes.py:424-431`: it removes three ("What Mathlib usually requires, accepts or enforces, how minor the change is, and whether a maintainer would insist on it are not grounds"). And under it gpt-5.5 still wrote `conforms` on an excluded ground at 2 of its 8 misses (`convention-detectors-2026-10-06/README.md:551-556`). [verified] |
| 9 | §4: detectors / static pass / closer battery "decide 10 of 93 asks' questions (mechanism/construction)" | **over-claimed** | By the draft's own §1.2, mechanism 6 + construction 1 = 7. The static pass measured 1 exact ask match of 23, under its 2-ask bar (`docs/todo/README.md:66`, `static-pass-2026-10-01`); the closer battery is "potential only, no spend" (`README.md:35`, `review-mechanical-sweeps.md`); the detectors were dot notation, primed names and `to_additive` — conventions, not mechanisms (`dead-ends.md:297-320`). [verified] |
| 10 | §4: D1 "lacked the authority order" | **mischaracterised**: D1 is the record's *instance* of the behaviour rule 1 forbids | Plan `2026-10-02-review-designs.md:79-81`: "**A change the tools contradict is recorded as refuted, not filed**; a change the tools cannot check is filed as advisory". The draft's rule 1 reverses this at the task level and does not say so. [verified] |
| 11 | §4: analogue retrieval, mechanism catalogue, deprecation stream — "two of the three never built" | **amend**: all three unbuilt | `docs/todo/review-design-comparison.md:3` "in progress ... the two free readings are done"; `grep -rln analogue src/` → nothing. [verified] |
| 12 | §4: the naming census tool "lacked the rule's threshold; direction" | **refuted by the record** on the threshold half | `dead-ends.md:286-295`: sweep 0.80 → 0.20, no verdict change; "The throttle was subject resolution". Direction: row 3. [verified] |
| 13 | §1.1-1.4 counts | **stands**, one slip | Recomputed from `readings/*.jsonl`: 558 rows; DX A = 1, K 64/C 65/V 17/O 17/P 19/E 1/reached 95; AP K 41/C 37/V 18/O 39/P 32/reached 112; K 105 and V 35; held 177; AP > DX 14 / < 4 / = 41; F2 0 → 11 of 24, F6 0 / 0, F8 22 / 19. **Held-and-ignored is 46, not 45** (`aggregate.md` §3: 2+9+2+0+21+12), in §1.4 and §5. §1.3's "63 of 105" and "21 of 35" come from no committed script (draft §7: a third of K unclassified). [verified] |
| 14 | §1.5: "the 24 asks no ask-free session ... reaches" | **stands, state the count's rule** | `asks_all.tsv`, all seven columns 0: 24 (D12 12, P14_post 6, P14_val 6), the same without TA; the tsv counts matcher-1 `reached` only (`prepare.py:183`). `PROTOCOL.md` says 17 of 46 and 15 of 47 (= 32), the assessment §6's figure; the two counts differ in rule, not data, and the draft should say which it uses. [verified] |
| 15 | §5: 15 asks need a fact the sources do not hold | stands (6 + 6 + 2 + 1, `aggregate.md` §2) | [verified] |
| 16 | §6: the test R, on the same packets, bars "≥ 6 of 24", "≥ 16 of 32", "no cap" | **conflicts with the record's practice** (Q2, Q3) | In-sample by construction: both sets are "in-sample for every design since stage C" and "the dev set inside the Claude models' training window; the fresh set is the only untouched set" (`conventions-assessment-2026-10-12.md:210-213`; dev is development material, `beating-solo-2026-10.md:138`, 2026-09-24). No emission bar, where "every plan after [the ruling] kept a gate (arms-speak, D1 at 2.0 a control PR, stage 5 at 1.0 a PR)" and "No emission gate, citing the 2026-09-22 ruling — misreads the ruling" (`generation-without-suppression.md:124-126, 199`). No statistic stated for the bars (mean / union / stable, `CLAUDE.md` Reporting). Matcher cost unstated: about 0.6M subscription tokens a seal (`README.md:1204`), on the one token that still runs (`CLAUDE.md`). Rule 1's outputs cannot score (row 2). [verified] |
| 17 | §5: "the cost is volume, and it is the open question" | **amend: under-stated** — the record has the numbers | S2 filed 13 of 14 unasked facts (`convention-detectors README.md:566`); forcing: control 1 → 36, "about 12 spurious control findings per real obligation" (`dead-ends.md:89-90`); the per-place engine, the record's prior instance of a cell-level filing rule: ~0.55 reach at ~68 findings a PR median, "files about 25 times as much", 7% of filings at an asked pair (`beating-solo-2026-10.md:152,163`; `conventions-places-2026-10-09/README.md:182,235`); AP +2.17 findings a PR and a failed yield guard (`README.md:1424`). See Q5 for the estimate the draft could have stated. [verified] |
| 18 | §3.2: the inadmissible grounds "are selection, and selection is downstream (the 2026-09-22 ruling)" | **stands** in direction; §3.5's "confidence label for the selection stage" is inert | `.claude/rules/mathlib-review.md:195-204`; `model_confidence` within-PR AUC 0.485 / 0.485 / 0.514 (`dead-ends.md:101-104`). But "no cap" reads the ruling as forbidding a volume *measure*, the misreading already flagged (row 16). [verified] |
| 19 | §0, §3.4: delivered conventions move the reviewer only where asserted as demand | **stands; it is the record's conclusion, uncited** | row 7. |
| 20 | §0: "Every narrow design in the record is one authority or one question of this structure" | **over-claimed** | The levers that moved the wall are none of them an authority or a question: the model and harness (`conventions-assessment-2026-10-12.md:187-189`: Opus +0.10 / +4 obligations from the X route; `docs/plans/2026-10-01-beyond-the-solo-baseline.md:1-12`), the reviewed workspace (`dead-ends.md:33-56`), forcing (`:81-90`), and the hygiene layer. [verified] |
| 21 | §3, §6: where the code lives | **amend** (native and minimal) | A new question axis beside D1's hashed `Concern` Literal (`structured.py:76-98`; "DESIGNS keys ... prefix task_id", `.claude/rules/mathlib-review.md:14-32`) is a design task of three edits subclassing the structured task, with the question set as a `knob()`. The draft names no module and would otherwise be a second ledger. [verified for the rule; the placement is inferred] |

## Q1. Is the design, or each of its parts, already in the record?

Yes for most of its parts, and the draft acknowledges some of the overlaps (§4, §7) without
reading the closest one. Part by part:

**The authority order (§3.2) — already run as `CONVENTIONS_PRECEDENCE`.** `probes.py:442-456`
[verified] is a ranked rule: a quoted line or a check you ran is the only ground to leave a place
unfiled (the draft's rank 1); the conventions with maintainers' examples outrank the reviewer's
judgement (rank 3 over rank 4); the reviewer's view that the code is fine, taste, minority, "this file,
its author or its neighbours do it differently" (the draft's siblings ground), "Mathlib does not
require it or a maintainer might not insist" (the draft's guess ground), and imperfect fit are named
inadmissible; a change that cannot be made or checked is filed as a question. The draft's §3.2 adds
two things only: the corpus plurality and a tool's count as inadmissible (new), and a rank 2 between
check and demand (new in name; see below). The record's result for the paragraph: with the asks
given, DP − DE = +0.197 / +0.179 over three reps (`conventions-ceiling-2026-10-04/README.md:1191-1230`)
[verified]; without them, AP − DX = +0.182 on the ten PRs where it was read (`:1399-1430`), then
−0.04 on P14's other four and −0.01 on the dev 15 (`one-reviewer-table-2026-10-10/README.md:185`)
[verified]; the dossiers todo's step-3 drop rule is thereby met (`conventions-dossiers-exams.md:149-157`,
`conventions-assessment-2026-10-12.md:27-31`) [verified]. The draft treats AP as "rank-3 evidence
with the rank asserted" lacking "a negative guard" (§4), which is true, but does not say that AP
already carries the inadmissible-grounds list and the question rule, so the record's measurement of
"an explicit authority order on the filing decision, delivered to the free model" is AP's: it moves
the discovery sample and nothing else. Does the record support the draft's claim that the missing
piece was the authority order? No: AP had the order and the reading's own AP rows show it ignored
(46 held-and-ignored) and overridden on the very grounds the paragraph names (p0007 AP2 "probability
... maybe 0.35. Skip it"; v0061 AP2 "overly pedantic and I don't think a maintainer would demand
that"; v0030 AP1/AP3 "pre-existing text", "verbose"; d0045 all three on the plurality and a Zulip
ruling — `aggregate.md` §4) [verified]. The record's conclusion is the one the draft restates in §3.4
("the assertion ... not the content"): `conventions-dossiers-exams.md:124-128`,
`conventions-assessment-2026-10-12.md:151-154` [verified], neither cited.

**Rank 2, "the library's current practice, with direction" — not in the record as a design, and its
sources are not built.** The draft says so for the deprecation stream and the mechanism catalogue
(§5, §6). The record's reopen condition for the idiom checker is this very source
(`dead-ends.md:29-33`) [verified]. What the record does say about the motivating instance (d0045,
d0046; D12a's "most instructive" reading 1) cuts against the draft: the elaborated corpus names the
coercion `coe` 37 to 3 at the head and 62 of 72 aligned; "the gold ask is a judgement against the
corpus ... Do not cite 21:7 as corpus support for it" (`.claude/rules/mathlib-review.md:296-304`)
[verified]. So the "newest form" the draft would have rank 2 return for d0045 is not in the library's
practice; it is in the maintainer's own asks and a review three days earlier, which is rank 3
(demand). The reading's `direction` code and the draft's rank 2 conflate them. [inferred from the
two sources]

**Rule 1's question clause — the record's untried item, already asked for and not obeyed.** Stage
G's Result 5 lists exactly this as untried: "An asserting lead: ... as a question where a check fails
('can `gcongr` do this?')" (`README.md:719-724`) [verified]. DP's paragraph then asked for it and
"DP filed no finding in question form, over 131 anchored findings" (`:1279`) [verified]. The
generation plan's adversarial round set aside "Questions legal everywhere" on volume ("every failed
check admits 'a variant might work'") and narrowed it to `ask_author` for delivered items
(`2026-10-06-generation-without-suppression.md:197`) [verified]. The arm-side knob exists
(`ask_without_fix`, `runner.py:268`, `configs/v5_replay_ask_without_fix.yaml`) and was part of the
unified contract's 3/10 (`dead-ends.md:131-150`) [verified]. The draft cites none of these; its §7
lists "questions allowed, already tried" as something for the reviewers to press on.

**The cell unit and "silence is not a disposition" — D1, acknowledged.** `structured.py:6,247`;
plan `2026-10-02-review-designs.md:70-81` [verified]. But D1 also fixes the *opposite* of rule 1:
"A change the tools contradict is recorded as refuted, not filed" (`:80`). The draft's rule 1
reverses D1's refutation step and its §4 row for D1 ("the unit and the contract") does not say so.

**The question set (§3.3) — partly in the record.** D1's `Concern` axis (proof, statement and
generality, library, name, docstring, placement; file: module_doc, style, organization;
`structured.py:76-98`) [verified] covers "what is the library's current form", "does the library
already have it", generality; work-enumeration's Phase 1 question list was to be "a question list
derived from maintainer comments, not ten concern briefs" (`2026-09-23-work-enumeration.md:48-55,
77-95`) [verified], never run past Phase 0. "What shape would a caller want / what does the analogous
API provide" is `review-design-comparison.md` (the main line, "in progress", nothing built) [verified].
"Is there a mechanism that produces this shape" is the idiom checker's reopen condition. "What does
the proof use of this constant" is the closer battery's generality procedure (8 of 15 potential,
never run blind; `review-mechanical-sweeps.md`, `static-analysis-pass.md:27`) [verified]. So the
question set is new as a *list*, and every source it attaches is either D1's existing axis or an
unbuilt todo. The draft says this in §5 for three of them.

**Forced submission.** `forbid_abstention` took issue recall 0.20 → 0.50 on four PRs, one rep,
gpt_5.2 arms, with control emission 1 → 36 and the quality half retracted ("no evidence either way
about the bar's discrimination") (`dead-ends.md:81-104`; `what-forcing-unlocks-2026-09.md:1-30, 80`)
[verified]. "The reopen condition — a second rep — was never run" (`:106-109`). The draft's §3.2
"the reviewer files unless a higher authority says the code conforms" is forcing restated at the
cell level; the draft does not cite the 1 → 36.

**Stage H.** The draft's "demand is at most 5% of applicable places" is Result 6's headline
(`README.md:808`) [verified] and the five decision designs (`2026-10-06-convention-decision-designs.md:35-41`)
were judge, examples, examples_rate, retrieve, rate: none was an authority order, so the draft is
right that stage H did not test one. But stage H's result bounds every cell-level filing rule: at
≤ 5% demand, "file unless cleared" at ~150 cells a PR is the per-place engine (Q5).

**`review-work-structure-2026-09.md` §7.** Its "warrant" is the draft's "authority" one level down:
"A submission contract belongs to a (reference, object) pair ... compile for a theorem's statement,
judgment for a definition's encoding" (`:491-508`), with the measured failure "`design`'s gate ...
turned the gold answer into `no_issue`" (`:481-489`) [verified]. The draft's rank order is global
where §7.5 found the warrant is per pair (85% predicted by the pair, 74-76% by either alone). The
draft does not cite §7.

**`docs/todo/README.md`, `docs/dead-ends.md`.** The entries that bear on the draft and are not cited:
`dead-ends.md:81-104` (forcing and its cost), `:131-150` (the submission contract as the recall
lever, provisional, "the residual is statements, not silences"), `:197-231` (the two conventions
dead ends rule 1 conflicts with), `:260-266` (the floor model's steering screen: "conventions as
directive: no effect"; "over-file is the one direction that helps"), `:297-320` (detectors closed,
which the draft agrees with). Todo entries: `generation-without-suppression` (the disposition
paragraph's own adversarial round), `review-design-comparison`, `static-analysis-pass`,
`review-mechanical-sweeps`, `conventions-dossiers-exams` (the drop rule met on 2026-10-12, on this
branch at `3b8bd373`).

## Q2. Conflicts with settled rulings and constraints

- **The 2026-09-22 selection ruling.** The draft's §3.2 and §3.5 keep to it (nothing ranks or
  withholds; grounds that would are named as selection). One misreading: §6 "findings per PR
  reported ... no cap" and §5's "whether those filings are welcome is unmeasured" read the ruling as
  excusing a pre-registered emission *measure*. The generation plan's adversarial round ruled on
  exactly this: "The 2026-09-22 ruling forbids *designing* selection, not measuring emission; every
  plan after it kept a gate (arms-speak, D1 at 2.0 a control PR, stage 5 at 1.0 a PR)"; "No emission
  gate, citing the 2026-09-22 ruling: misreads the ruling" (`:124-126, 199`) [verified]. Stage W's
  guard was +3.0 findings a PR, stage AP's a yield floor it then failed by 0.014 (`README.md:1424`).
  The draft's §6 has no such line.
- **The reporting rules.** Three reps: stated. Provisional: stated. Negatives: §6 says the design
  goes to `dead-ends.md` below the bars "with the untried sources ... as its reopen conditions" —
  correct form. Altitude: the bars are counts on subsets the reading itself selected (24 never-reached,
  32 K-inadmissible), with no statistic named. The record's rule is per-session reach on both
  matchers with a bar on the difference and a volume side-condition (`conventions-ceiling-probe.md:
  "Reading rule"`; `README.md:991-1034`). On 24 asks one ask is 4 pp and the X anchor moved ±0.06
  across seven seals (`beating-solo-2026-10.md:103-106`) [verified]; "≥ 6 of 24" as a three-rep
  union is reachable by volume alone (DP: mean 25, union 29 of 39). The over-claimed negative is not
  in the draft; the over-claimed *positive* is §0's "Every narrow design in the record is one
  authority or one question of this structure" (row 20).
- **Native and minimal.** The draft proposes a unit, a contract, a question axis and an output
  contract without naming a module. Under `.claude/rules/mathlib-review.md:14-32` this is a design
  task of three edits; the natural parent is the structured task, with the question set replacing
  `CONCERNS` through a `knob()` so D1's identity is not moved. A second ledger beside D1's would be the
  duplicate-helper failure mode `CLAUDE.md` names. [the rule verified; the placement inferred]
- **The conventions dead ends.** Rank 1 makes "a linter" and "a count against a threshold the rule
  states" the authority that clears a cell; `dead-ends.md:197-212` rules a linter a `stated` source
  only, "never as the oracle", because it answers "can", not "does" (`terminalToGrind` fixed at 4.0%
  adoption while adoption reached 14.5%); `:213-231` rules out a statistic about code as the
  mechanism; `:286-295` shows the census threshold is not what bound. Rank 2's "the plurality is
  never a ground to clear" agrees with those entries; rank 1's "a count with a stated threshold
  clears" does not. Detectors closed as a recall lever: the draft agrees (§4 "stop building"), and
  then attaches "the standard linter set", "the closer battery" and "counts with stated thresholds"
  as rank-1 sources, whose measured yield is 1 of 23 (static pass) and 0 blind runs (closer battery).
- **The 2026-09-24 ruling on sets.** "The dev set is one reviewer's review of four PRs"
  (`.claude/rules/mathlib-review.md:230-245`) and dev "counts as development material"
  (`beating-solo-2026-10.md:138`) [verified]. §6 reads R on D12 and P14 only; the fresh 40-PR set
  (75 asks, 37 of 39 workspaces built, `one-reviewer-table-2026-10-10/README.md:11-25`) is the
  record's deciding set for any AP-derived design (`conventions-assessment-2026-10-12.md:186-199, 212`).
- **The 2026-09-23 note** ("a labelling-only session is not a contribution"; memory): the draft is
  a design with a test, so it meets the form; the test as written would not decide (Q3).

## Q3. Does the record show that a contract moves the free reviewer at all? Is §6 the narrowest test?

**What the record shows, by instance** [all verified]:

| contract change | model | result | volume |
|---|---|---|---|
| D1 cell contract (verdict per declaration × concern, silence illegal, tools refute) | gpt_5.2 | 2, 2 of 23 against carried 2-3; "98% of cells `no_issue` with reasons; the unit of decision does not bind" (`after-structure.md:18, 41`) | 0.0 control |
| same | Opus 5.5 | 10, 10 against 9, 9, 7; "structure bought consistency, not a frontier" (`:21-30`) | 128 findings vs 93-103; 1.5 a control PR |
| D2 critic on D1's `no_issue` cells | Opus 5.5 | +1 (11), 28 overturns of 1,812-1,950 cells, 0 refutations | 2.0 a control PR |
| `target_verdicts` + `ask_without_fix` (unified contract) | gpt_5.2 arms | 3/10 vs 2/10, bar 5; "the residual is statements, not silences" (`dead-ends.md:131-150`) | 77 vs 57 findings, 0 control |
| `forbid_abstention` | gpt_5.2 arms | 0.20 → 0.50, one rep, 4 PRs; quality half retracted (`:81-104`) | 49 → 179 findings; control 1 → 36 |
| `filing_bar: request` | gpt-5.5 | 0.200 → 0.200 out of sample (`generation-without-suppression.md:109-111`) | 24 → 43 findings |
| contract v2 (the solo baseline) | DeepSeek-V4.1-Flash | 8, 6, 9 of 23 (`CLAUDE.md`); no contract comparison exists on DeepSeek, only sections | 2.6 / 5.1 a PR |
| exact section (DE) | DeepSeek | +0.222 / +0.248 over DX, three reps (asks given) | +0.24 a PR |
| precedence paragraph + examples (DP) | DeepSeek | +0.197 / +0.179 over DE (asks given); **no question-form finding in 131** (`README.md:1279`) | +0.62 a PR |
| the same, ask-free (AP) | DeepSeek | +0.182 on the ten PRs; −0.04 / −0.01 off them; yield guard failed by 0.014 | +2.17 a PR |
| sections + disposition paragraph (S2) | gpt-5.5 | asks 1 → 5 of 13; unasked facts 0.50 → 2.17 a PR (13 of 14); "a volume lever by the pre-registered gate" (`detectors README.md:537-569`) | pass-through |
| conventions as directive; over-file | Qwen3.5 (floor) | directive: no effect; over-file 3, 3, 0, 1, 0, the one direction that helped (`dead-ends.md:260-266`) | |

**Reading.** A contract reliably moves *volume*. It moves issue recall in the record only when (a)
it forces (one rep, at twelve spurious control findings per obligation recovered), or (b) it is
bundled with asserted asks (DE, DP) or with their ask-free proxy on the PRs that proxy was picked
for (AP). The cell contract alone did not bind on gpt_5.2 and bought consistency on Opus. No
contract has been compared on DeepSeek without a conventions section, so "a contract moves the free
reviewer" is unmeasured for the model §6 proposes to run, and the closest evidence — AP's
held-and-ignored 46 rows and held-and-dropped 39 under a paragraph that already names the draft's
grounds inadmissible — is evidence that the free model does not follow a stated authority order
where it conflicts with its prior. The draft's §7 asks the reviewers this question; the answer is in
`aggregate.md` §3-4 and `README.md:1279`.

**Is §6 the narrowest test of the central claim?** No. The central claim is that *the authority
order*, made explicit, moves the filing decision. R bundles: D1's cell contract + AP's section + AP's
paragraph with ranks spelled out + the plurality rule + a negative guard + a seven-question axis +
questions legal. Against DX and AP, a gain is attributable to any of them, and the first-run version
has no rank-2 source ("no new source is built"), so R on its first run is D1 + AP + questions-legal +
a prompt. The record's own narrower tests, untried: Result 5's two lines (`README.md:719-722`) — the
exact entries under G's verify-and-drop lead (isolates the lead), and an asserting lead that files a
question where a check fails — and, for the plurality rule alone, the same AP packets with the one
sentence added. [inferred: which ablation is narrowest] Any of these is in-sample on P14; the
out-of-sample reading is the fresh set.

**Are the bars at the right altitude?** No, on four counts. (1) No statistic: "R reaches ≥ 6" of 24
is a count over three reps with mean, union and stable unstated; the record's bars are per-session
reach on both matchers. (2) No volume side-condition, where every pre-registration since stage L had
one (`README.md:71-91, 991-1034`; stage 5's 1.0 a PR; D1's 2.0 a control PR). (3) The subsets are
the reading's own: the 32 K-inadmissible asks are the ones on which R's prompt was written, so "≥ 16
of 32" is stage H's "all" row (recall 1.0, precision 0.081) re-run on the asks that motivated the
wording — the in-sample objection the generation round made to "stage G's ten PRs as the deciding
set" (`generation-without-suppression.md:198`) [verified]. (4) Rule 1's product cannot score:
judge v9 refuses a question (`protocol.py:65`); the matchers' rubric has no question form; so on
D12 R's questions count as misses and the test is biased against its own mechanism until §8's
rubric change is made and sealed first.

## Q4. Mischaracterised instances in the §4 table

- **"convention detectors; the static pass; the closer battery — rank-1 checks ... decide 10 of 93
  asks' questions (mechanism/construction)".** 7 by §1.2 (6 + 1), and the three named things are not
  one kind: the detectors measured naming/attribute conventions (dot notation 19 of 20, primes 20 of
  20, `to_additive` 0 of 29; `dead-ends.md:297-320`); the static pass measured 1 exact ask of 23
  (`todo/README.md:66`); the closer battery is a hand sweep, 8 of 15 "potential only, no spend"
  (`:35`). None decides a mechanism ask (`to_fun`, `mk_iff`, `grind [def]`, `variable … in`): those
  need the catalogue the draft says is unbuilt.
- **"the disposition paragraph S2 — one inadmissible ground removed".** Three (`probes.py:424-431`),
  and the C3 audit found `conforms` written on an excluded ground anyway at 2 of 8 misses
  (`detectors README.md:551-556`). It is the record's direct measurement of "name the ground
  inadmissible and the model still uses it", which is the draft's mechanism.
- **"AP ... no negative guard; sentences matched by shape; narrowing".** True as stated; what is
  left out is that AP already carries the draft's ranks 1, 3, 4, five of the seven inadmissible
  grounds and the question clause (`probes.py:442-456`), and read null off its discovery sample.
  The "+0.20 on the ten PRs" is the one-reviewer-table's validation figure; stage AP's own reading
  is +0.182 with a failed yield guard (`README.md:1399-1430`).
- **"stage G — rank-1 checks without a rank-3 assertion — [lacked] the authority order".** G lacked
  the assertion, under a 13-74-item half-decoy list and a verify-and-drop lead
  (`README.md:660-724`). The record names what to try next (`:719-722`); the draft renames it.
- **"the dossiers and exams — richer rank-3 evidence — the reading says understanding was not the
  bottleneck; authority was".** The record's finding is the ladder's: "the bare sentence at the place
  passes 25-29 of 39; DP's examples −4 to −5" and "attention and licence" are the bottleneck
  (`conventions-ladder-2026-10-08/README.md:205-264`; `beating-solo-2026-10.md:178-184`). "Licence"
  is the record's word; "authority" is the draft's. Consistent, but the dossiers were never built, so
  "what it lacked" is not a measured lack.
- **"D1 `structured` — the unit and the contract — [lacked] the authority order and the question
  set's missing questions".** D1 *has* an authority rule and it is the inverse of rule 1: tools
  refute, a refuted change is not filed (`2026-10-02-review-designs.md:79-81`). On gpt_5.2 the unit
  did not bind at all (`after-structure.md:18`), which bears on the draft's "the model lacks the
  knowledge of what outranks what": gpt_5.2 wrote reasons for 98% `no_issue` cells under a contract
  that forbade silence.
- **"the critic D2 — a disagreement without an authority to appeal to".** D2 was told to argue
  with "a compile, a lookup, a sibling in the file, the area's census" and to concede explicitly
  (`:90-99`); it had authorities and overturned 28 of ~1,900 cells with none refuted. Its result is
  that a second pass over the same cells with the same evidence agrees with the first.
- **"the naming census tool — a rank-1 count used as the rule's threshold — [lacked] the rule's
  threshold; direction".** The threshold half is refuted: `MIN_SUPPORT_RATIO` 0.80 → 0.20 changed no
  verdict; "the throttle was subject resolution" (`dead-ends.md:286-295`). The direction half is
  contested (`rules:296-304`). The D12a reading's "a rule that fires on 'the name leads with a
  hypothesis' needs no census" is a shape rule, i.e. a detector, which the draft's own §4 says to
  stop building.
- **"analogue retrieval (E), the mechanism catalogue, the deprecation stream — two of the three never
  built".** None is built (`review-design-comparison.md:3`; `grep analogue src/` empty).
- **"the exact-conventions brief (+0.26) — a ceiling: it knows the asks".** Stands.

## Q5. What the record says the design will cost in volume, and does the draft state it honestly

**Stated by the draft:** "The cost is volume, and it is the open question" (§0, §5); demand ≤ 5% of
applicable places; the first number to read is "the two control PRs of each set". That is the right
direction and the wrong altitude: the record has already measured each component of this design's
volume, and the draft quotes only S2's asks (1 → 5) beside its unasked facts (0.50 → 2.17).

**What the record says** [verified unless marked]:
- The per-cell filing rule is the per-place engine, the record's architecture B: "every picked
  convention asked at every changed place, filed uncapped" simulates ~0.55 reach at ~68 findings a PR
  median, "files about 25 times as much", with 0.068 of `departs` filings at an asked pair
  (`beating-solo-2026-10.md:152, 163, 189-193`; `conventions-places-2026-10-09/README.md:182, 235-249`;
  `conventions-assessment-2026-10-12.md:195`). Its measured `departs` rate at *unasked* places is
  0.28-0.30 (`:182`).
- D1's ledger is ~150 cells a PR (1,812 cells over 12 dev PRs, `generation-without-suppression.md:116`).
  Under "files unless a higher authority says conforms" with rank-2 sources absent on the first run,
  and the places test's 0.28-0.30 unasked `departs` as the model's own rate when asked a convention's
  question at a place, the first-run R files on the order of 40 cells a PR before any gain is read —
  against DX's 2.6 / 5.1, AP's 4.6 / 8.1 and Opus + AP's 14.3 / 17.0 (`beating-solo-2026-10.md:22-30`).
  [inferred: the multiplication; the factors are the record's]
- Forcing's precedent: 49 → 179 findings and control 1 → 36 for 2 → 5 obligations, "about 12
  spurious control findings per real obligation recovered" (`dead-ends.md:81-90`).
- S2's precedent: 13 of 14 unasked facts filed, each with a compiled edit (`detectors README.md:546-548`).
- The volume guards the record has used: +3.0 findings a PR (stage W / D), a yield floor (AP, failed
  by 0.014), 1.0 unasked a PR (stage 5), 2.0 control findings a PR (D1).
- Matching cost, which the draft omits: four blind matchers per seal at 0.61M subscription tokens
  (`README.md:1204-1206`), two seals (P14 sets) plus D12's; the primary token is the user's
  interactive account and the only one that runs (`CLAUDE.md`).
- Controls: P14 holds seven control PRs (3 validation + 4 post-cutoff, `conventions-ceiling-probe.md`
  "Sets"), not two; D12's control count is not stated in the draft. [verified for P14]

**Honest?** In direction yes; in content no: it presents as unmeasured a quantity the record has
bounded from three sides (the engine simulation, forcing, S2), and §6 then sets no volume bar. The
"first number to read" (control-PR findings) is the right number and already the record's practice;
it should be a pre-registered gate with a value, as every pre-registration since stage L has had.

## Searches run

- `git log --oneline -i --grep` on `develop` for: `forbid_abstention|forced submission|abstention`;
  `2026-09-22|selection ruling|generator first|nothing ranks`; `target_verdicts|unified contract|
  structured|disposition`; `stage G|stage H|precedence|DP`. Results cited above.
- `grep -rn` over `docs/`, `.claude/rules/`, `CLAUDE.md` for `generator first|nothing ranks|selection
  is downstream|2026-09-22`; over `docs/dead-ends.md` for `authority|outrank|precedence|rank` (hits:
  `:103` AUC, `:153`, `:160`, `:357` only — no prior "authority order" entry); over `probes.py` for
  `outrank|precedence|taste|local practice|imperfect fit|question where`.
- `grep -c` on the draft for `conventions-assessment|dossiers-review|Result 5|asserting lead|
  generation-without-suppression|ask_without_fix|forbid_abstention|unified-contract`: **0**.
- `grep -rln analogue src/`: none. `grep -n question construction-demo-2026-09-29/matcher_rubric.md`: none.
- Recomputed from `readings/*.jsonl` and `asks_all.tsv` (script inline, no files written): the §1
  counts, K/V totals, the 24 never-reached asks. `review-mechanics/` in the probe directory is
  untracked and belongs to another reviewer's working set; not read beyond its docstrings.
- Read whole or in parts: `CLAUDE.md`; the draft; `PROTOCOL.md`; `aggregate.md`; the six batch
  summaries; `dead-ends.md`; `todo/README.md` (the list); `unified-contract-fanout4-2026-09.md`;
  `2026-10-02-review-designs.md`; `2026-10-06-generation-without-suppression.md`;
  `conventions-ceiling-probe.md`; `conventions-assessment-2026-10-12.md`; `beating-solo-2026-10.md`;
  `conventions-dossiers-exams.md:101-160, 236-266`; `ceiling-residual-2026-10.md`;
  `review-work-structure-2026-09.md:435-510`; `what-forcing-unlocks-2026-09.md:1-80`;
  `2026-10-03-after-structure.md:1-40`; `2026-10-01-beyond-the-solo-baseline.md:1-60`;
  `conventions-ceiling-2026-10-04/README.md:660-733, 1191-1314, 1399-1461`;
  `convention-detectors-2026-10-06/README.md:419-570` (grep + `:551-570`);
  `conventions-ladder-2026-10-08/README.md` (headings and result lines);
  `one-reviewer-table-2026-10-10/README.md` (headings, `:82-150` grep, `:185`);
  `conventions-places-2026-10-09/README.md` (grep); `2026-10-06-convention-decision-designs.md` (table);
  `2026-09-23-work-enumeration.md` (grep); `structured.py:1-112, 210-250`; `probes.py:424-470`;
  `judge/protocol.py:60-70`; `.claude/rules/mathlib-review.md`; `git worktree list` (42 worktrees;
  `conventions-dossiers`, `conventions-ds41`, `conventions-models`, `conventions-nature`,
  `generation-suppression`, `review-designs` hold the runs cited; none holds an authority-order design).
