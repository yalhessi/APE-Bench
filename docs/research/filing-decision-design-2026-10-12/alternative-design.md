# Name, then judge: the filing decision as a contract boundary, not a rank order in one head (the alternative general design; advocate's draft, 2026-10-12)

**Status** — an advocate's document for the adversarial round on
`docs/research/filing-decision-design-2026-10-12.md` (the draft). Same evidence as the draft: the
per-ask reading (`results/pr_review_v5/probes/ask-reading-2026-10-12/`, 93 asks, 558 session-rows,
one reader a batch, provisional), the one reviewer table, and the record. Nothing was run; the two
counts marked *(computed here)* come from the reading's `.jsonl` and from one lexicon pass over the dev
DX1 transcripts, and are labelled for what they are. Candidate (a) of the four put to me, chosen and
reframed; (b), (c) and (d) are absorbed as generator-side sources, not rejected. Written to be argued
against; nothing in it is a conclusion.

## 0. The claim in one paragraph

The draft and I read the reading the same way: the free reviewer reaches the place (1 of 558 rows
unattended), mostly has the facts (34 `none` + 14 `demand` of its 66 missed asks need no fact about
the code), names or checks the maintainer's own concern in 81 of its 184 missed rows (64 `K`, 17 `V`) and clears it on a prediction
about the maintainer, the worth of the change, the file, a plurality, a tool's threshold, the brief's
form or a failed check on its own wrong candidate. Where we differ is what to do about it. The draft
puts an authority order *inside the reviewer's filing decision*: a prompt-and-schema rule about which
grounds may clear a cell. I say the reading has already tested that rule on this model and it did not
hold: the AP sessions held, word for word, a paragraph forbidding most of the draft's
inadmissible grounds (worth and taste, a guess about maintainers, the file and its neighbours, the
brief's form rules; not the plurality, the PR's own framing or a budget) and licensing questions (`ap_sections/*.md` l.898: *"None of these is a reason
to leave it out: that the code is correct, clear or idiomatic as it stands; that the change is minor
or a matter of taste; that this file, its author or its neighbours do it differently; that Mathlib
does not require it or a maintainer might not insist on it … Where you cannot make or check the
change, file it as a question … Leave a place unfiled only where a line of the code you quote, or a
check you ran, shows it already has the form"*), and with it in hand they dropped the held convention
on exactly those grounds 39 times and ignored it 46 times of 177 (p0007 AP2 *"probability … maybe
0.35. Skip it"*; v0061 AP2 *"overly pedantic and I don't think a maintainer would demand that"*;
v0094 AP1 *"Marginal. I'd rather not file that"*; d0043 AP1 *"a marginal finding dilutes
precision"*; d0008 AP1 *"the idiom is identical in all four siblings, so I did not file it"*). Every
move in the record that changed what the reviewer *files* was a schema the model could not route
around — forced abstention 0.20 → 0.50, `target_verdicts` 112 of 112 targets answered, D1's
silence-illegal ledger stable 6 → 8, S2's disposition 1 → 5 of 13 — and every move that was a rule
about grounds read null (stage F +0.03, stage G +0.000, the precedence paragraph above, the brief's own
"emit only what you would request"). So the general design is: **separate the two decisions the draft
says the reviewer conflates — what could be asked here, and whether it is asked for — into two stages
with a contract between them.** Stage 1 names every concern with its evidence *typed by source*
and never clears; stage 2 ranks and files, by a policy that is data-driven and replayable for nothing.
Knowledge lives in stage 1, judgement in stage 2, and the draft's authority order becomes stage 2's
first policy rather than a rule stage 1 is trusted to obey. What this costs is a candidate store, one
more call a PR, and a volume at stage 1 that the record already knows the shape of (about the forced
fanout's); what it buys is that a named concern cannot be lost, the grounds for dropping become
measurements, and the filing policy can be iterated offline on recorded candidates instead of in
paid runs.

## 1. The design, on one page

### 1.1 Two stages, one boundary

**Stage 1 — the namer.** One session a PR, the standard packet, the D1 unit (`(object, question)`
cells over declaration, family, file and PR objects) with the draft's §3.3 question set, which I keep
verbatim: it is the right set, and it is the part of the draft that reaches the `C` rows. The contract
differs from the draft's in one place: **stage 1 may not clear.** Its output per cell is one of

- `candidate`: the change or question the reviewer would put to the author, with its evidence; or
- `checked`: a check it ran, or a line it quotes, that shows the required form already holds (S2's
  `conforms` rule, which the record built and which is the only disposition the precedence paragraph
  let stand); or
- `nothing named`: the cell was read and no concern of this question's kind arose.

Every piece of evidence carries a **source type**, which is mechanical: `check` (a tool's output,
verbatim), `form` (a dated declaration, deprecation or migration the reviewer cites), `convention`
(a census sentence, held or recalled), `construction` (Lean text the reviewer wrote, with its compile
result), `analogue` (a named declaration the reviewer compares against), `own` (the reviewer's
reasoning). A `candidate` also carries **`would_clear_on`**: the ground on which the reviewer would
have left it out had it been allowed to, in its own words. The brief's "emit only what you would
request", "do not raise questions" and the finding cap are removed from stage 1; questions are
candidates like any other. Constructions are not optional for the proof and statement questions: the
cell's answer to "is there a shorter proof / a more general statement / the shape a caller wants" is
the built alternative and its result, or `cannot build`, never `fine` (candidate (d), absorbed; see
§2.3 for why the reading supports this at the generator and not at the filing decision).

**Stage 2 — the adjudicator.** Reads stage 1's candidate set for the PR, not the PR; applies a
**policy** and writes per candidate `file`, `question` or `withhold`, each with the rule that fired.
The first policy is the draft's §3.2 authority order, as written: a passing `check` withholds; a
failed `construction` on the reviewer's own candidate is filed as a question; a `form` newer than the
file outranks `convention` and `own`; `convention` asserted as demand outranks `own`; `own` files
unless outranked; and `would_clear_on` grounds of the draft's inadmissible kinds (worth, a guess
about maintainers, the file's siblings, a plurality or threshold the rule did not set, a form rule,
the PR's own framing, a budget) never withhold. Ranks 1 and 2 are decided from the source types
mechanically; ranks 3 and 4 need a model read of the evidence. The adjudicator never adds a
candidate: what stage 1 did not name, stage 2 cannot file (the critic D2's job, if wanted, is a
second stage-1 pass, not a stage-2 power).

**The boundary.** The candidate set, with its typed evidence and `would_clear_on`, is a stored
artifact (`TaskStorage`, per sample). Any policy can be replayed over it without a reviewer run,
which is the work-enumeration's own insight (*"the ceiling run is also the simulator"*,
`docs/plans/2026-09-23-work-enumeration.md`), applied to the filing decision instead of to
scheduling.

### 1.2 What is knowledge and what is judgement, under this design

| | stage 1 (knowledge) | stage 2 (judgement) |
|---|---|---|
| asks | what could be asked here, with what evidence | whether it is asked for |
| output | candidates with typed evidence and the ground the reviewer would have dropped on | a filing decision with the rule that made it |
| sources | checks, the library's current form with dates (candidate (c)), conventions, constructions (candidate (d)), analogues, the reviewer's reasoning | the policy, and nothing else |
| may it clear? | only on a `check` or a quoted line | yes, by rule |
| how it is measured | asks whose candidate set holds the ask (the matchers), candidates a PR on the controls | asks filed of asks named; published count on the controls; `would_clear_on` tallies |
| how it is iterated | new sources, new questions (paid: a reviewer run) | new policies (free: a replay over stored candidates) |

The draft's authority order is one row of the right-hand column. The record's other designs sit in
the left: the per-place engine (candidate (b)) is one way of asking stage 1's questions at every
place; the deprecation stream and the mechanism catalogue are `form` sources; analogue retrieval is
an `analogue` source; the closer battery is a `construction` source. None of them changes the
boundary, which is the design's only new commitment.

### 1.3 What the design refuses

- A filing rule stated to stage 1 ("do not clear on worth"): tried, as the precedence paragraph, and
  routed around 85 times of 177 (§2.5).
- A stage 2 that reads the PR: it would re-make stage 1's decisions and lose the replay property.
- A cap or a budget at stage 1: a budget is one of the recorded grounds ("I'm already at 7", p0007
  AP2), and the 2026-09-22 ruling puts selection after a generator that reaches.
- A stage 2 that is "selection": it *is* selection, under the ruling's own name, and §4 says so
  plainly rather than renaming it. The ruling orders generator first; stage 1 is the generator, run
  and measured uncapped, and stage 2 is where the draft's order lives in either design.

## 2. How it accounts for the reading's numbers

Two counts over the reading's rows *(computed here, from `readings/*.jsonl`)* frame everything
below. **Some session named the concern** (a `K`, `V`, `E`, `P` or `reached` row among its six) at
**81 of the 93 asks**; at 12 it was never named by anybody (d0003, d0004, d0007, d0016, d0036,
d0039, d0049, d0051, p0003, p0004, v0064, v0091 — all `C`/`O` rows). Of the **24 asks no ask-free
session on disk reaches**, 18 were named by at least one DeepSeek session and dropped or checked
away; 6 were never named (d0003, d0004, d0049, d0051, p0004, v0091). Per session, the named share of
rows is DX 196 of 279 (reached 95 + P 19 + E 1 + K 64 + V 17), AP 203 of 279.

**Not attended, 1 of 558.** Nothing for either design to do; the draft and I agree.

**`K` 64 and `V` 17 of DX's 184 misses (105 `K` and 35 `V` rows over both conditions).** These are
the boundary's rows. Under stage 1's contract each is a candidate by construction: the reasoning
that wrote *"`Dense.ciSup`? … Let me focus and be strategic"* (d0022 DX3 l.20), *"a real maintainer
might ask: state this … as a general UFD-style lemma … Hmm"* (p0005 DX2 l.26), *"it should get a
proper descriptive name like `commutator_sup_left_of_normal`"* (p0012 AP3 l.26), *"`[Infinite β]`
would be idiomatic … Meh. Not a finding"* (v0106 DX3 l.43), *"with their original proofs compile
under the new sections … A maintainer likely wouldn't reject them"* (v0062 DX1 l.38) has nothing
left to do but write the candidate and its `would_clear_on`. The draft reaches the same rows only if
the reviewer applies the order where it declined to apply the precedence paragraph; I return to that
in §2.5. The `V` rows split: a check that *passed* on the code (d0010–12's `encard_` 84 of 88;
v0068's `gcongr` test, which was right) is `checked` in both designs; a check that failed on the
reviewer's own candidate (d0035 AP2 compiled `intro m h; exact add_mem h.1 h.2` without
`mem_comap.mpr` and read *"close to minimal"*; v0093 AP2 tried two wrong one-liners and wrote
*"Can't"*; v0092 AP1 wrote the maintainer's `simpa … using` form and dropped it with *"no"*) is a
`construction` candidate with a failed result, which stage 2's first policy files as a question. The
draft's rule 1 says the same; the difference is again who applies it.

**`C` 65 (the question never arose).** Here the alternative adds nothing over the draft, and I say
so: the `C` rows are reached by the question set (draft §3.3) and by the constructions, both of which
live in stage 1 in both designs. The reading's own words for these rows are the question's absence,
not a filing decision: *"audited the lemma axis by axis (duplicate, name, proof, binder kind,
placement) and none asked what shape a caller would want"* (p0004), *"'generalization' in these
sessions means typeclass binders, never a constant in a statement"* (d0051), *"the sessions ask of
an import 'is it needed' … never 'what does this file now cost its importers'"* (d0007), *"every
session framed 'duplicate' as an existing named declaration and searched by name, which can never
surface a structure's own `mk`"* (d0002). The 12 never-named asks above are the measure of what a
question set must add; it is the same 12 for both designs.

**Knowledge: `none` 34, `demand` 14, a fact 15 of 66.** The 48 `none` + `demand` asks are the
boundary's population: the reading's phrase for what the AP section changed is *"what counts as
asked-for"* (every batch), and *"the delta is not knowledge of the code, it is permission to ask"*
(P14val_b). Permission is a stage 2 matter under this design, and it is given by policy, once, rather
than asserted per sentence and per place and obeyed or not. The 15 fact asks (`mechanism` `to_fun`,
`grind [def]`, `mk_iff`, `variable … in`, a structure's `mk`; `direction` `coe_` → `toLinearMap_`,
hand-written twins → generators, `def`-with-`∧` → `@[mk_iff] structure`, "tag, don't re-prove";
`api` the insert lemma, the contested `_left`; `construction` `2` → `k`) are stage 1 sources — the
draft's rank 2 sources, two of three unbuilt — and neither design reaches them until the sources
exist. The alternative only says where they plug in (`form`, `analogue`, `construction`) and that
their arrival changes nothing at stage 2.

**AP held-and-ignored 45, held-and-dropped 39.** The dropped 39 are the alternative's central
exhibit: a rule about grounds, delivered in the packet with precedence wording, overruled at the
place by the grounds it forbade (§0 quotes; also d0038 AP1/AP2 reading P108 and concluding the author
had no choice, v0030 AP1/AP3 *"pre-existing text"*, *"verbose"*, p0016 AP1/AP3 *"limited basis"*).
Under stage 1 these are candidates with `would_clear_on` filled in, and under the first stage 2
policy 20 of them (the `K` grounds the aggregate classifies) are filed. The ignored 45 are
*attention at the sentence*, not a filing decision — the sentence was never brought to the place
(d0036 ×3, d0049 ×3, p0003 ×3, d0013 AP2/AP3) — and neither design moves them except by making the
sentence a cell question, which the draft's §3.3 and my stage 1 both do for the held conventions.

**F6, 0 of 18 (statement and API design), every held sentence ignored.** Honest reading: the
alternative does not reach F6 by itself, and neither does the draft. The reading says what would:
*"judgement-shaped ones (d0049, d0051, d0006, d0007) need a per-declaration question with its own
check, not a sentence to match"* (D12c), and for d0003 the comparison object (`Function.Surjective`)
is a `form` newer than the file's sibling. In the alternative, F6 is a stage 1 bet on two sources —
the "what shape would a caller want" question answered by a `construction` (the `usage` of
`review-coordination-design-2026-09.md` §4) and an `analogue` source — and the construction demo
(2026-09-29) is the caution: constructions reached 5 and 6 of 11 asks, and so did the plain brief on
Claude; on a model that does not construct unprompted (`gpt_5.2`, and the DeepSeek sessions here,
which compiled a candidate of their own in a minority of the 140 named rows; the draft counts 11
that failed on the reviewer's own variant) it is untested. I claim no F6 number.

### 2.5 The row that decides between the designs

The draft's §7 names its own risk: *"whether the authority order is a prompt that the free model
will follow where it ignored the precedence paragraph"*. The reading measured that paragraph. It
told the reviewer that the held conventions *"outrank your own judgement"*, listed the inadmissible
grounds, licensed questions and allowed `conforms` only on a quoted line or a run check — the draft's
§3.2 in miniature for about 25 conventions a PR. Outcome on the 177 held rows: used 92, dropped 39,
ignored 46. On the 20 dropped rows the aggregate classifies, the ground was one the paragraph
forbade. The draft's reply is that its order is attached to a *cell contract* with an authority
field, so a `conforms` must carry a rank. True, and it is the draft's strongest structural element;
but the field the schema can check is *that a rank is stated*, not *that it is the right one*, and
mis-ranking is what the reading shows: a plurality read as a deciding check (d0045 ×3, *"`coe_` 48 of
124 … the plurality ✓"*), a sibling read as the library's current form (d0003 *"Consistent ✓"*,
d0004 *"the file's established style. Fine."*, d0018 *"consistent with the file"*), a satisfied
convention read as rank-3 endorsement of the neighbouring name (p0012 AP1, p0008 AP1), an outside
authority read as settling a doubt the maintainer kept (v0031 ×5, Wikipedia and Zulip). Under the
draft the same head that mis-ranked writes the rank into the field. Under the alternative stage 1
writes only the source type, which is mechanical (a `naming_norm` result is a `check`; a sibling is
an `analogue`; a Zulip hit is a `convention`), and the rank is assigned by stage 2's policy, which can
be wrong but is wrong *the same way every time and visibly*, and is changed by editing a policy, not
by re-prompting a reviewer.

The decision-turn replay is the other half of this argument (`decision-replay-case4-2026-09.md`):
the `naming` arm on 33337, cut before its first submission and re-sampled five times on byte-identical
evidence, filed the maintainer's exact rename twice and abstained three times citing the same
`naming_norm` verdict. The filing decision on this evidence is a draw at about 0.4. An in-line
authority order is applied by that draw; a contract that forbids the abstention is not.

## 3. Where it beats the draft, and where it loses

**Beats.**
1. *A named concern cannot be lost.* 81 of 93 asks were named by some session; the per-session named
   share is about 0.70. The draft converts the named-and-dropped rows into filings only to the extent
   the reviewer obeys a rule about grounds, and the record's measured obedience on this model is 92
   of 177 held rows (§2.5). The alternative converts them by contract, which is the one lever the
   record shows moving this model's filings (forced abstention, `target_verdicts`, D1, S2).
2. *Ranking is done where it can be audited.* Source type is mechanical and assigned at stage 1; rank
   is a policy and assigned at stage 2. The draft asks the head that read a plurality as a deciding
   check (d0045) to write "rank 1" or "rank 2" into a field and expects the field to be right.
3. *The filing policy iterates for nothing.* Stored candidates with typed evidence let the authority
   order, "file everything", "file on two-sample agreement" (the places test's one measured volume
   lever) or any later policy be replayed and matched without a reviewer run. The draft's §6 test
   costs a three-rep run per policy variant, and the record's history is prompt variants that remove
   one dropping ground at a time (the draft's own "what to stop building").
4. *The adjudication question gets its data.* `would_clear_on` on every candidate is the first corpus
   of "what the reviewer would have withheld and why", which `docs/todo/adjudication-rubric.md` has
   needed since 2026-09-21 and which no design in the record produces. The draft's confidence label is
   one number; the ground is a reason.
5. *Questions are first-class without a special rule.* v0068, v0092, v0105, p0000, p0005 are
   `construction`-failed or answered-question candidates; the draft needs rule 1's second clause and a
   brief change to admit them.

**Loses.**
1. *It is two stages, and the second is selection.* The user's ruling (2026-09-22): *"Talking about
   publishing is talking about selection. We currently don't have a good enough reviewer to start
   talking about selection."* Stage 2 is that stage, renamed only by being the place the draft's own
   order lives. The honest defence is the ordering, not the name: stage 1 is the generator, measured
   uncapped and first; stage 2's first policy is the draft's, not a cap; and the admission-gate
   precedent (`the-admission-gate-2026-09.md`: a downstream gate discarded 71–83% of the obligations
   the run had found) is exactly why stage 2 must be read as found / published side by side
   (`report buckets --audit` exists for this). If the user's ruling is that no second stage may exist
   yet, the alternative reduces to stage 1 with the "file everything" policy — which is still a design,
   and §5's bar 1 measures it.
2. *Volume at stage 1 is larger than the draft's, by construction.* The draft files what the reviewer
   would have cleared on inadmissible grounds; stage 1 files what the reviewer would have cleared on
   *any* ground but a check. §4 sizes it. If the adjudicator is weak, the published set is either the
   flood or the gate.
3. *A build.* A candidate schema with source types and `would_clear_on`, a stored candidate set per
   sample, and a stage 2 task reading it: three things in `src/ape/`, where the draft is a brief and
   a cell schema. D1's ledger (`structured.py`) and `target_verdicts` are most of stage 1; the
   adjudication socket (`cli adjudicate`, keyed findings, `labelled_by: task:<identity>`) is most of
   stage 2's store. It is a week, not a day.
4. *Stage 1 may stop naming when it cannot drop.* The one risk the record cannot price from existing
   runs: a reviewer told it may not clear may name less, to keep its output short (the "I'm already
   at 7" reflex turned inward). D1 on `gpt_5.2`, 98% of cells `no_issue` with reasons and 2 of 23 obligations, is the shape of
   that failure on a weak model. Bar 1 in §5 is written for it.
5. *It does not reach what the draft does not reach either:* the 12 never-named asks, F6, the 15 fact
   asks until their sources exist, and the gold's own defects (v0105, v0053/v0056, the four-counted
   33145 rename).

**Why not (b), (c) or (d) as the alternative.** Each is a stage 1 source and is kept there. (b) alone
asks each question at each place and still lets the answer be dropped — the places test's engine
files uncapped at 7% precision, and the forced fanout's residual was *"statements, not silences"*;
its gain is in what is asked, which the question set carries in both designs. (c) alone is a fact
source for 12–15 of 66 missed asks, and the reading's modal miss is not a fact; the draft already
ranks it. (d) alone changes what the reviewer builds before clearing a proof or statement cell, and
the reading supports it there (d0008/d0009 *"a missing candidate, not a missing suspicion"*; d0035,
v0093, v0092 cleared on a wrong build) — but constructions were dropped on worth after being built
(d0035 AP3 *"Not worth filing"*, v0094 AP1 *"Marginally"*, v0066 AP3 *"roughly the same length"*),
so a construction rule without the boundary meets the same filing decision. The boundary is the only
piece that is not already a source, and it is the piece the draft puts inside one head.

## 4. What each would cost in volume

Neither number is measured; both are priors from the record, and the experiment in §5 reports the
real ones beside each other on the controls.

- **The draft.** It files the `K` rows that rest on inadmissible grounds (63 of 105 at gold places)
  and turns the wrong-check `V` rows into questions (21 of 35). Off gold places the same rule fires on
  every concern the reviewer names and would clear on worth or a guess. The nearest measured
  analogue is S2 on stage 5 (one disposition per delivered item, worth excluded as a ground): asks
  1 → 5 of 13 and unasked facts 0.50 → 2.17 a PR, a pass-through of the detector by its own gate. The
  draft's §5 says the cost "is volume, and it is the open question". One session a PR; findings a PR
  unknown, with DX at 2.6 / 5.1 (P14 / D12) as the floor.
- **The alternative.** Stage 1 files every named concern. A lexicon pass over the dev DX1 transcripts
  *(computed here; a block count of drop phrases such as "not worth", "wouldn't ask", "marginal",
  "minor", "skip", "not a finding", "I won't flag", "fine."; it over-counts, since a block may hold one
  concern or none, and the S2 plan rightly warns that such counts measure phrasing)* gives a median
  of 15.5 reasoning blocks with a drop phrase on the 12 ask PRs against a median of 5 findings filed,
  and **21, 11 and 15 such blocks on the three control PRs (33304, 33315, 33438) against 1, 2 and 1
  findings filed.** Read as an order of magnitude only: a stage 1 that may not clear emits about
  10–20 candidates on a PR where maintainers asked for nothing, which is the forced-fanout regime
  (1 → 36 on a control, 2026-09-14) and below the places engine's median 68. Stage 2 then publishes a
  subset by policy; under the authority order the controls' published count is what R3's rule (d)
  reads (≤ 2.0 a no-ask PR). One session a PR plus one adjudicator call that reads candidates, not
  the PR: tens of thousands of tokens, free on the local tier.

So the alternative's *generator* is roughly four to eight times the draft's volume on a control PR by
this prior, and its *published* set is whatever the policy makes it, which is the same policy the
draft applies in-line. The draft's volume is its published volume; the alternative separates the
two numbers, and that separation is the point.

## 5. The one pre-registered experiment that separates them

**Conditions,** on the same 26 PRs and packets, the free reviewer, three reps each, one seal, the
table's two blind matchers:

- **R** — the draft's §6 condition, as it states it (D1 cell contract, the authority order as the
  filing rule, inadmissible grounds named, the §3.3 question set, the AP section as rank-3 evidence
  with a negative guard, questions legal). Unchanged, so the draft's own bars read from the same run.
- **G** — stage 1 of this design: the same cell contract and question set and AP section, with
  clearing forbidden, source types and `would_clear_on` on every candidate, no finding cap, no "not
  questions". Its candidate set is stored.
- **A(G)** — stage 2's first policy, the draft's authority order, applied offline to G's stored
  candidates by one adjudicator call a PR (deterministic for `check` and `form`, a model read for
  `convention` and `own`). Also **All(G)**, the "file everything" policy, as the ceiling of what G
  named. No reviewer run; the matchers score A(G)'s and All(G)'s published sets like any session.

**Bars, stated now.**
1. *Does a reviewer that may not clear still name?* All(G) reaches **≥ 24 of the 32** asks the
   reading marks `K` on inadmissible grounds, and **≥ 8 of the 24** never-reached asks (the draft's
   bar on R is 6), on the union of three reps. Below **16 of 32**, the contract suppresses naming (loss
   4 in §3) and the alternative is written to `dead-ends.md`, with "a stage 1 that names into a
   scratch ledger and submits only its candidates" as the one untried form.
2. *Prompt or contract — the separating measure.* **A(G) − R ≥ 4 asks of the 32** (the matcher's
   self-agreement puts ±12pp on n ≈ 32, about four asks) on both matchers, paired by rep: the in-line
   order loses asks to disobedience, and the boundary is needed. **|A(G) − R| ≤ 2**: the draft wins,
   being one stage with the same reach, and this document is withdrawn. Between: a fourth rep of each.
   Beside it, the draft's own re-read of 40 R dispositions by the protocol's codes, with one number
   added: the share of R's `conforms` dispositions whose stated authority is one the draft rules
   inadmissible. **≥ 20%** (the AP paragraph's held-and-dropped rate was 39 of 177, 22%) is the order
   not being followed, whatever the matchers say.
3. *Volume.* G's candidates a PR, A(G)'s and R's published findings a PR, each on the control PRs
   of each set (D12's three, 33304, 33315 and 33438; P14's as the draft names them) beside the ask
   PRs, no cap. A policy counts as a lever only if its
   published count on the controls is **≤ 2.0** while bar 2 holds; G's raw count is reported, never
   gated, as the generator-first ruling requires.
4. *Side readings, not bars.* All(G) − A(G): what the authority order itself discards of what was
   named, read on the matchers, which is the first measurement of the draft's order as a policy.
   `would_clear_on` tallied by the draft's ground categories over all of G's candidates, ask PRs and
   controls alike: the first corpus for the adjudication rubric.

**Cost.** R and G are six DeepSeek runs of 26 PRs on the local tier, about 35 min a rep: $0. A(G) is
26 adjudicator calls a rep, read-only over stored candidates: $0. The seal and the matchers are the
real cost, about 0.5–1M subscription tokens for two conditions plus two offline policies, on the
primary account, which is the user's call.

## 6. Limits

The same limits as the draft's §7, plus three of this document's own. The reading was done on gold
places only, so "names the concern" is measured where a maintainer asked and inferred elsewhere; the
control-PR volume prior is a lexicon count over three PRs and one rep, and over-counts by an unknown
factor. The decisive claim — that a contract moves this model's filings where a rule does not — rests
on four structural results and four null prompt results in the record, all one to three reps, none
on this exact contract. And stage 2's first policy is the draft's order, so if the order is wrong as a
policy the alternative publishes the wrong set too; the design's answer is that it can then be
changed for nothing, which is a property, not a result.
