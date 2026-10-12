# Review of the filing-decision design: generality, falsifiability, and whether the model will follow it (2026-10-12)

**Lens.** One of four adversarial reviews of `docs/research/filing-decision-design-2026-10-12.md`
(commit `de7425b6`). The user asked for *"a clear general design that encapsulates as much as possible
... not too many pieces that apply narrowly, but a design that clearly navigates knowledge and
judgement."* This review judges the draft against that, and argues the strongest case that it is (a) a
prompt dressed as a structure, (b) a volume pass-through, or (c) blocked by the model rather than the
contract. Then what survives.

**Sources read.** The draft; `results/pr_review_v5/probes/ask-reading-2026-10-12/` (`PROTOCOL.md`,
`readings/aggregate.md`, the six batch `.md` files, the 558 `.jsonl` rows, `sessions.json`);
`docs/research/conventions-assessment-2026-10-12.md`; `docs/research/beating-solo-2026-10.md`;
`docs/todo/conventions-ceiling-probe.md`; the ceiling README's Results 5, 6 and AP
(`conventions-ceiling-2026-10-04/README.md`); the detectors README's stage 5 (S1/S2);
`docs/plans/2026-10-06-generation-without-suppression.md`; `contract-2026-10-01/README.md`;
`review-designs-2026-10-02/README.md` (D1); `docs/dead-ends.md`; `.claude/rules/mathlib-review.md`.
No model was run. Two counts were computed for this review from the reading's rows and from the 156
DeepSeek transcripts and are marked *(computed here)*; everything else is marked **verified** (quoted
from an artifact) or **inferred** (my reading).

## Verdict table

| question | verdict | the load-bearing evidence |
|---|---|---|
| 1. Generality | **Half a structure.** The clearing rule (file unless a *higher* authority says conforms; worth, guesses, siblings, plurality, budget and form rules are not grounds) is one rule and is general. The question set is seven entries, five of which name a source that does not exist; and the ranks are assigned to past designs by their outcome, so §4 is a relabelling. Of five asks walked through §3.2–3.3, two need no special case, three do. | walk-through below; draft §4's own "two of the three never built" |
| 2. Will the free model follow it | **Not shown, and the record points the other way.** Under the exact list with the same precedence wording (DP) DeepSeek still left 4 failed checks unfiled and made 5 merits judgements of 16 misses; under the ask-free list (AP) it used 92 of 177 held sentences and ignored or dropped 85. S2 on gpt-5.5 gave every disposition and still cleared 2 of 8 misses on a ground the paragraph excluded. What the draft adds over the AP paragraph is a rank label, not a mechanism; the one mechanical thing it could add (a schema in which `conforms` is illegal without rank 1–3 evidence) it does not state. | aggregate §3 **verified**; todo stage D **verified**; detectors README S2 **verified** |
| 3. Volume | **Understated by an order of magnitude, with the inputs for the estimate already on disk.** At gold places the design adds about 0.4 filings a session-PR; beyond them the sessions name and drop on the order of 20–30 concerns a session against 2.7–8 findings filed and 3.6 asks a PR. Stage G's "all" row (149 raises, 12 at an ask), the places test (about 68 a PR at 7%) and S2 (13 of 14 unasked filed) are the measured precedents. §5 names the cost and gives no number; "selection is downstream" misreads the ruling in the way the 2026-10-06 plan already flagged. | *(computed here)*; Results 5/6 **verified**; S2 **verified** |
| 4. Falsifiability | **§6 tests "R beats AP", not the central claim.** R bundles five changes, three of which (dispositions per cell, grounds removed, questions legal) already moved reviewers in the record. No control separates the authority *order* from S2 plus questions. The bars are reach bars with no volume bar ("no cap"), so a pass-through passes. A 2×2 is proposed. | plan 2026-10-06 **verified**; §6 **verified** |
| 5. The target | **Mixed.** Rank 2's lesson (a PR's own siblings are not conformance) fits AI PRs exactly and the draft does not say so; rank-3 policy sentences (AI disclosure, close) were AP's cleanest gains. Against: the cell unit scales with the PR (516 cells on 33294, 336 on 33149; 98% `no_issue` on gpt), and a systematic PR repeats one departure N times, which the design files N times. | D1 README **verified** |
| 6. Steelman | Stated in §6 below, with the one experiment. | |

In the draft's own three-way: **(a)** the ranks are prompt text and §4 is a relabelling; the schema
constraint on `conforms` would be structure, and it is not in the draft. **(b)** As written ("nothing is
withheld on worth", "no cap", every cell where ranks 1–3 are silent ends in a finding or question) it is
a pass-through by construction. **(c)** The deepest objection is neither: the model's "wrong authority"
is a calibrated prediction (maintainers raise at most 5% of the places a convention applies, stage H),
and the design asks the model to act as if that prediction were wrong, which is a *policy* about what
to file, not knowledge the model lacks. A policy can be enforced by a validator; it cannot be made true
by a rank.

## 1. Generality: is the authority order one structure?

### 1.1 The one-rule half

§3.2's clearing rule is genuinely one rule: *a cell is cleared only by an authority of higher rank than
the one that raised the concern, and these six grounds are not authorities.* It applies to every cell
the same way, it is what the `K` rows (105, 64 DX / 41 AP, **verified** aggregate §1) violate, and
each of the record's partial designs removed one ground (S2: the guess about maintainers; `filing_bar:
request`: the worth bar; forcing: abstention). Stated as a single list of inadmissible grounds it is
general in the user's sense, and it is the part worth keeping.

### 1.2 Where the special cases hide: the question set

The `C` rows (102, 65 DX / 37 AP, **verified**) are the places where the ask's question never arose.
The clearing rule cannot reach them; only §3.3 can, and §3.3 is seven questions each tied to a source:

| §3.3 question | source named | exists? |
|---|---|---|
| does a check settle this | linters, try-it, counts with stated thresholds | linters yes; "stated thresholds" exist for no rule |
| is there a mechanism for this shape | a dated tactic/attribute catalogue | no (draft §4: "never built") |
| library's current form vs the file's | the deprecation stream, dated | no (draft §4: "never built"); and d0045's direction is not a deprecation |
| what shape would a caller want / the analogue | analogue retrieval by role | no (assessment §7 B: "the measurement is the step") |
| what the proof uses of a constant | the closer battery's constructions | partly (hand sweep 0 of 3, assessment §7 C) |
| do maintainers ask for this here | the census with examples | yes (AP's section) |
| what does the import cost / what must the description state | import graph; the PR node | import graph yes; the PR node has no question set |

So the design "navigates knowledge" by listing the five kinds of knowledge the reading found missing
and attaching each to a rank. That is the detector-per-kind structure the user asked to stop building,
with the detectors renamed questions. The generality is in the *rule about clearing*; the *reaching* is
a list.

### 1.3 Is §4 a relabelling?

§4 assigns every prior design a rank by what it did: the exact brief "is rank-3 evidence" because it
moved; stage G "lacked a rank-3 assertion" because it did not; AP has "the rank asserted" and moved on
the ten PRs. The test of a structure rather than a relabelling is whether the rank predicts before the
run. The structure's one prediction is: *rank-3 evidence delivered with its assertion moves the
reviewer.* AP is exactly that (the precedence paragraph, **verified** PROTOCOL.md), and on the asks
where it held the convention it moved 14, lost 4 and tied 41 (**verified** aggregate §3a); off the ten
PRs it reads null (assessment §2). To keep the prediction, "assertion" has to mean "the list is short
and right", which is the ceiling leak, not a rank. **Inferred:** §4 is a relabelling in the one place it
matters.

### 1.4 Five asks through §3.2–3.3

Each walk asks: which question, which authority, what is filed, and whether a special case was needed.

**Naming, d0045** (`coe_` → `toLinearMap_` for the CLM→LinearMap coercion written as an ascription).
Question: "the library's current form, is the file's older?" Rank 1: `naming_norm` returned `coe_` 48
of 124, and the rule states no threshold, so rank 1 is silent by the draft's own clause. Rank 2: the
source is "the deprecation stream" and there is none; the direction lives in the maintainer's two asks
on this PR, in `toLinearMap_mapIsometry`, and in a three-day-old review of the same file (#32927) that
AP1 found and read as accepted rather than asked (**verified** D12a). That is rank 3 evidence by
recency, which the census has no field for (assessment §6: "the census has no maturity field"). And
the hard step is not the rank: DX2 cited the dated 2025-12-05 `toLinearMap_` rename for d0046 and still
took the plurality for d0045, because the ascription spelling read as a different cell (D12a: "the
sessions name by syntax, the maintainer by the coercion"). **Special case needed:** cell identity
across spellings, and a recency-ordered precedent source not in the table. The order says "file the
older-form finding with dated evidence"; nothing in it tells the model the two spellings are one cell.

**Statement and API design, d0003** (`∃ U, f = U.conj…` → `Function.Surjective`). Question: "what
shape would a caller want / the analogue?" Rank 1 silent. Rank 2: analogue retrieval does not exist;
the only comparison object in the packet is the sibling, which the rule says is "evidence of the older
form, never grounds to clear". Rank 3: P007 absent from the section. Rank 4: "a finding or a question
with its reasons, never silence." So the design's output at this cell is a question ("is the `∃` form or
`Surjective` wanted?"), and it is the same output at every statement cell with a sibling and no newer
form on record, which is most of them. **No special case,** but only because the design is
indiscriminate here: it reaches d0003 by asking at every statement. p0004 (an alias for the direction)
goes the same way: the audit "never asks what shape a caller wants" (**verified** P14post), the
question set adds it, the authority is 4, the output is a question at every iff.

**Proof try-it, v0068** (`gcongr`). Rank 1: AP1 and AP3 ran `lean_verify_edit` with `gcongr`, it
failed, and both cleared ("that removes that finding", **verified** P14val_b). Under rule 1 the failed
check on the reviewer's own candidate becomes the question "gcongr does not fire on `MonotoneOn`; is
the side condition needed?", which is the gold ask. **No special case**, and this is the cleanest fit
in the draft. Two notes. First, the same clause makes every failed candidate compile a question, which
the 2026-10-06 plan considered and set aside ("42814 alone carried about 60 check items; every failed
check admits 'a variant might work'. Narrowed to `ask_author`", **verified**); the draft re-opens it
without citing it. Second, d0008/d0009 (`grind [def]`) go through the same row and stall: "is there a
mechanism?" has no catalogue, AP3's own `proof_profile` reported `grind` as "NEW ... 9.18% of files" and
it did not act (**verified** D12b). The reaching step there is a procedure ("try the modern finisher on
every short proof you find awkward"), not an authority.

**Interface, p0007** (`variable {D : ℤ}`). Rank 3 held (P048); AP2 derived the exact fix and dropped it
at "probability ... 0.35. Skip it" and "I'm already at 7" (**verified** P14post). Both grounds are on
the inadmissible list; rank 3's "a licence to file, not a prediction that this maintainer will" is
written for this row. **No special case.** But note what did the work: removing two grounds and
forcing a disposition, which is S2's paragraph verbatim ("whether a maintainer would insist on it [is]
not [a] reason", **verified** plan C1). v0060/v0061 (`variable … in`) also pass: AP2 reasoned from the
bullet to the maintainer's form and dropped on "overly pedantic" and "the mul analogues use sections"
(**verified** P14val_b), both inadmissible.

**PR-level, p0000** ("explain why the old names are bad"). All six sessions ran the check (Zulip:
`motive` is the convention) and it passed (**verified** P14post). At the declaration cell, rule 1
*clears* it: a passing check clears the cell. The ask is only reachable at a PR cell whose question is
"does the description state the reason for the rename?", and D1's ledger has no PR cell (it gained file
cells after 33305, `review-designs-file-cells.md`, **verified**). §3.3's last row names "the PR node"
without a question set for it. **Special case needed:** the PR object's questions (P041: motivate a
design change) and the rule that a check at one cell does not clear another. d0032 (AI disclosure) by
contrast is clean: a rank-3 policy sentence, 0→3 of 3 under AP (**verified** D12c).

**Tally.** Two of five need no special case (v0068, p0007), and both are reached by the S2 paragraph
plus a legal question form, without a rank. Three need something the order does not supply: cell
identity and a recency source (d0045), a comparison source that does not exist and otherwise a question
at every statement (d0003), and a PR-level question set with a cross-cell rule (p0000).

## 2. Will the free model follow it?

### 2.1 What the record says about this model and precedence wording

- **AP** (DeepSeek, 25 picks, two asks each, a paragraph saying they outrank its judgement): held at
  177 rows; used 92, considered and dropped 39, ignored at the place 46 (*(computed here)* from the
  rows; the draft's 45 is off by one). Of the 39 drops, 20 are `K` rows, the concern named and dropped (whether all 20 rest on the grounds the draft rules
  inadmissible is the draft's keyword classification) (**verified** aggregate §3).
- **DP** (the same model, the *exact* list, examples and a precedence paragraph that also asks for a
  question where a check fails): +0.197 / +0.179 over DE. "It files no question, though its paragraph
  asks for one where a check fails." DP1's 16 misses: "four a failed check left unfiled where the
  paragraph asks for a question, five merits judgements, three the right convention in another form"
  (**verified** todo, stage D). So under the best list the record has, with the draft's rule 1 already
  in the paragraph, the model obeyed the question clause 0 times in 4 and made a merits judgement 5
  times.
- **S2** (gpt-5.5, disposition per detector item, guess-about-maintainers banned as a ground): every
  session gave the dispositions; at the 8 misses, 2 `conforms` "on precedent, which the paragraph
  excludes as a ground", 2 `departs` filed as a different change, 1 `departs` not filed (**verified**
  detectors README round 2). The mechanical part was obeyed; the ground ban was not, in 2 of 8.
- **Stage G** (Claude, rule + place + check): verified and overrode (**verified** Result 5).
- **Contract v2 on gpt-5.5**: "looks at what Claude looks at, compiles what Claude compiles, and
  concludes 'nothing to ask' two times in three where Claude asks" (**verified**). **D1 on gpt-5.2**:
  1,698 cells, 98% `no_issue`, 2 of 23 as the baseline (**verified**). **D1 on Claude**: 10 of 23
  against a hygiene mean of 8.3, "a lever, at the threshold, provisional" (**verified**).

The pattern across these: a contract's *mechanical* clauses are obeyed by every model (cells filled,
dispositions written, ledgers complete), and its *judgement* clauses are obeyed in proportion to how
right the list is. DP's list was right and the paragraph moved the model +0.20; AP's list holds about
2.8 true entries in 25 (assessment §3) and the same paragraph moved 92 of 177. Nothing in the draft
changes the list (§6: "the AP section as its rank-3 evidence"), so nothing changes the basis on which
the model disbelieves it. **Inferred, provisional:** compliance tracks the precision of the evidence
the paragraph asserts, not the strength of the paragraph.

### 2.2 What the draft adds, and whether it is a mechanism

§3.4: "The design makes the rank explicit on every piece of evidence the reviewer sees and on every
disposition it writes." Two things:

1. **Rank labels on the input.** A plurality count delivered "as rank 1 evidence that the rule's
   threshold is not met" is still a count the model reads; a sibling delivered "as rank 2 evidence of
   the older form" is still the sibling. The model decides what it believes about the label. This is
   prompt text, and the AP paragraph was prompt text of the same kind.
2. **An authority tag on the output.** This could be a mechanism, if stated as a schema: `conforms`
   requires an authority in {check, library_form, demand} and an evidence field; `judgement` can only
   file or question. A validator can refuse a submission that violates it, as `_check_ledger` refuses an
   unstated D1 cell. The draft does not say this; it says the output "carries" a rank and a confidence
   label. Said as a schema it is enforceable; said as a contract it is the AP paragraph.

And even the schema is gameable in the way the record shows: gpt's v2 ledger entries "mostly assert a
check from reading ('checked ...; nothing to ask')" (**verified** contract README); S2's `conforms`
came "with lines that show the variant differs, not that its name says how" (**verified**). A model
that must cite a check will cite a reading as a check. The validator can require the tool call's id
(C3's "compiled edits whose declaration no finding targets" is the pattern), which is the one place a
contract can bind; it binds `conforms`, not `file`.

### 2.3 The separation the question asks for

| the design asks the model to | mechanical? | precedent in the record |
|---|---|---|
| write a disposition for every cell | yes (D1 `_check_ledger`) | obeyed by gpt-5.2, gpt-5.5, Claude; moved recall only on Claude, by 1.7 at threshold |
| name an authority and evidence on `conforms` | yes, as a schema with tool-call ids; not as prose | S2 gave them; 2 of 8 on an excluded ground |
| treat a question as a legal finding | yes (the finding schema) | DP's paragraph allowed it; 0 of 4 taken |
| not clear on worth, guess, siblings, plurality, budget, form | as a ban on words, no; as a schema on `conforms`, partly | S2: the ban moved 4 of 13 and 13 of 14 unasked |
| rank 2 (newest form) over the file and the plurality | no: "newest" is the model's own judgement without a dated source | d0045: the dated rename was in hand and did not decide |
| rank 3 (a sentence with two asks) over its own judgement at every matching place | no | AP: 92 of 177 |

The rows that are mechanical are D1 plus S2 plus a question form. The rows that are not are the ones
the draft calls the design.

### 2.4 Why the model's prior is not simply wrong

The draft's diagnosis is that the model clears cells on "the wrong authority", its own guess about
maintainers. Stage H measured that guess's object: maintainers raise a convention at 2.9–5% of the
places its situation is flagged, and model deciders given the convention, the code and examples put p
at 0.05–0.10 everywhere, "about the true 0.08" (**verified** Result 6). AP2's "maybe 0.35. Skip it" on
p0007 is, against that base rate, generous. The design does not supply a reason for the model to
believe otherwise; it supplies an instruction to file anyway. That is a legitimate policy (file what
could be asked; let a later stage choose), but it should be named as one, because a policy's cost is
its volume and its test is whether the filings are welcome, which is the adjudication nothing has run.

## 3. Volume: what the design would file

### 3.1 The rates in the record

- Maintainers' asks on these PRs: 93 on 26 PRs, **3.6 a PR** (**verified** `asks_all.tsv`), and D12's
  47 are weighted by one reviewer's 29 (**verified** beating-solo).
- Findings filed, per session-PR *(computed here from the packets)*: DX 3.78 (D12 5.1, P14 2.6), AP
  6.18 (D12 8.1, P14 4.6). These match the one reviewer table.
- Demand: a convention is raised at 2.9–5% of the places its situation is flagged (**verified** Result 6).
- The measured pass-throughs: stage G's "all" row, 149 raises for 12 at an ask on ten PRs (15 a PR,
  precision 0.081, **verified** Result 6); the per-place engine, about 68 a PR median at about 7%
  (**verified** beating-solo); S2, 13 of 14 unasked facts filed, +1.67 unasked a stratum-B PR for +4 of
  13 asks (**verified** detectors README).

### 3.2 What the reading's rows can and cannot say

The reading looked only at gold places. Its `K` rows are drops *at asks*: 105 over 156 session-PRs,
**0.67 a session-PR**; the draft's 63 on inadmissible grounds (its keyword classification, a third
unclassified, §7) give **0.40 a session-PR** *(computed here)*. So converting every inadmissible drop
at a gold place adds about 0.4 filings a session-PR, which is small and is the part that would be
counted as reach. That is the numerator of a ratio whose denominator the reading never measured: the
concerns the sessions name and drop at places that are not asks.

A rough denominator *(computed here; inferred, order of magnitude only)*: a regex over the sessions'
thinking blocks for the draft's six inadmissible grounds ("not worth / marginal / minor / skip",
"maintainers wouldn't / would not request / does not require", "consistent with the file / sibling",
"plurality / common enough / unmeasured", "the brief says / concrete request", "already at N /
dilutes precision") hits a median of **60 times a DX session and 53 an AP session** (means 68 and 59;
worth 24, guess 25, brief-form 6–8, file-style 2, plurality ≤ 1 at the median), over about 200k
characters of reasoning a session. Phrase hits overlap and repeat; dividing by two or three for
distinct concerns leaves **20–30 named-and-dropped concerns a session** against 3.8–6.2 filed. The
design's rule at those places is "file, or file a question", so the expected output is on the order of
**15–40 findings a PR**, in the range the record already measured for the two pass-throughs (15 from
ten rules; 68 from the whole census at every place), against 3.6 asks a PR. Add the `C` conversions
(every cell at which ranks 1–3 are silent must end in a finding or a question) and the number is
bounded only by the cell count.

### 3.3 Is §5 at the right altitude?

§5 says "the cost is volume, and it is the open question" and that the two control PRs' counts are
"the first number to read". Naming the cost is right; not sizing it is not, when every input for the
size is on disk (stage H's rate, stage G's 149/12, the places test's 68, S2's 13/14, the finding
counts above). On the control PRs the number is predictable: there are no asks, so every filing is
unasked; S2 filed 2.17 unasked a PR from 14 delivered facts; the design delivers every cell.

"Selection is downstream" is doing two jobs in the draft. As a reason not to *propose a gate* it is
the ruling (**verified** `.claude/rules/mathlib-review.md`: "proposing a different gate is not"
allowed; "measuring the gate is fine"). As a reason to run with **no cap** (§6) and "nothing withheld on
worth" (§3.5) it is the misreading the 2026-10-06 plan already set aside: "No emission gate, citing the
2026-09-22 ruling: misreads the ruling; every plan since kept a gate" (**verified**). Stage AP's own
guard (asks reached a finding no lower than solo's; +3.0 findings a PR) and D1's (≤ 2.0 findings a
control PR) are the record's standard, and §6 drops both. And the stage the cost is deferred to has
nothing to select with: every uptake signal on record reads AUC 0.49–0.64 (plan 2026-10-06, **verified**;
`model_confidence` 0.485–0.514, dead-ends, **verified**), so the "confidence label carried for the
selection stage" is a label the downstream stage cannot use. The answer is deferral, and to a stage the
record says cannot do the job.

**What would make the volume argument honest:** state the expected findings a PR before the run, from
the counts above; keep AP's yield guard and D1's control-PR guard as pre-registered failure conditions;
and name the adjudication ("would a maintainer accept this if proposed?", `docs/todo/adjudication-rubric.md`)
as the measurement that decides whether a pass-through is a reviewer. Without it, R's "reach" is the
places test's recall with the precision left unreported.

## 4. Falsifiability

### 4.1 What §6 tests

R = D1's cell contract + the authority order + the inadmissible grounds named + the question set + the
AP section as rank-3 evidence + a negative guard + questions legal. Bars: ≥ 6 of the 24 never-reached
asks; ≥ 16 of the 32 `K`-inadmissible asks; findings a PR reported, no cap; a re-read of 40
dispositions.

The central claim is "the authority order, not new facts, moves the filing decision". §6 tests whether
R beats DX and AP. R differs from AP in five ways, and three of them already moved reviewers in the
record without any order: dispositions per cell (D1: 10 against 8.3 on Claude), the guess and worth
grounds removed (S2: +4 of 13 on gpt-5.5, with 13 of 14 unasked), and questions legal (untested alone;
DP's paragraph allowed it and the model took none). If R clears the bars, the draft will read it as
the order; the record will read it as S2 with cells and questions. Nothing in §6 separates the two.

Three smaller points. **(i)** The 32 `K`-inadmissible asks were chosen by reading the sessions' drops,
so "≥ 16 of 32" is a bar on the set that motivated the wording; the plan of 2026-10-06 set aside the
same move for stage G's ten PRs ("the notes motivated the wording", **verified**). **(ii)** "≥ 6 of 24
never-reached" is the stronger bar: by §5's own count 15 of the 24 need a source that does not exist,
so it is 6 of about 9 reachable, which is falsifiable; keep it. **(iii)** The re-read of 40
dispositions "to see whether the inadmissible grounds fell" measures phrasing, which the same plan
ruled out ("the treatment bans the words, so that count would measure phrasing", **verified** C3).
Count instead what C3 counts: delivered or derived `departs` not filed, `conforms` without a tool-call
id, compiled edits with no finding at the declaration.

### 4.2 The control, and the minimal factorial

The control that separates the order from "the D1 contract plus questions allowed" is **R minus the
order**: the same cells, the same AP section, the same inadmissible grounds listed, questions legal,
with no ranks on the evidence and no "higher authority" rule, i.e. S2's paragraph generalised to every
cell. If R − (R minus the order) is inside the noise, the order is a label.

Minimal factorial, free model, same packets, three reps, the AP section present in every cell so that
rank-3 evidence is held constant:

| | questions legal + disposition per cell: off | on |
|---|---|---|
| **authority order + grounds named: off** | AP (exists) | AP + cells + questions |
| **on** | AP + order | R without the question set |

Read the order's main effect at both levels of the other factor; the minimum detectable difference on
these sets is about 0.14–0.18 (assessment §6), so an effect under that is "not shown". Add the question
set as a fifth cell only if the order moves. Pre-register the volume guards with the reach bars: asks
reached a finding ≥ AP's 0.295, findings a control PR ≤ 2.0. If three reps are not affordable, the
three-cell fallback is AP, AP + cells + questions, and R without the question set, which still gives
the one contrast that matters.

## 5. The target: AI-generated PRs

The project's target is large, systematic, AI-generated PRs (CLAUDE.md). Where the design's parts meet
that:

- **Helps, and the draft does not say it:** rank 2's "the file's siblings ... are evidence of the older
  form, never grounds to clear". On an AI PR the siblings are often the PR's own output: on 33098 three
  sessions propagated the `by_cases; simp only [..., ↓reduceDIte]` dance into lemmas they wrote
  themselves because it "read to them as the house style" (**verified** D12b), and on 33149 (which
  DX2 and DX3 called "clearly a fake / AI-generated proof") the vacuous definitions were each other's
  precedent. Internal consistency is the one ground a systematic generator always satisfies; a rule
  that refuses it as a ground is the right rule for the target.
- **Helps:** rank-3 policy sentences at the PR cell. d0032 (AI disclosure, 0→3 of 3) and d0033 (close
  the PR) are PR-level asks on an AI PR, and they were AP's cleanest conversions. A census of PR-level
  demands (disclosure, motivation, scope) is cheap and the design has a cell for it.
- **Helps, if the harness runs it:** rank 1 scales with size at no judgement cost. On 33305 AP2
  counted every changed line and reached the long-line ask; AP1 and AP3 counted one and stopped
  (**verified** D12a). The design leaves checks to the model's own tool calls; on a 2,000-line PR the
  model will sample. The linter set should run before the session, as the detectors thread did.
- **Hurts: the cell unit scales with the PR.** D1 wrote 1,698 cells over 15 dev PRs, 516 on 33294 and
  336 on 33149, 98% `no_issue` on gpt-5.2 and 93% on Claude, at 27.7–33M processed tokens a rep with
  59% prompt re-read (**verified** review-designs README). An AI PR is where the cell count is largest
  and the free model's 35-minute rep and 1M context are the budget. "Silence is not a disposition" on a
  500-cell PR produces either truncation or templated dispositions, which is the gpt ledger.
- **Hurts: repetition.** A systematic PR repeats one departure N times (d0022–d0027 one rename ×4,
  d0010–d0012 ×3, v0106–v0108 ×3). The design files per cell, so one ask becomes N findings; the
  matcher counts one, the maintainer reads N. D1's ledger has no family cell for a repeated departure,
  and grouping them is a selection step the draft has deferred.
- **Neutral:** nothing in the design depends on the PR being human-written, and nothing labels or
  filters AI PRs; that is a dataset property, already required.

Net: the rank-2 direction lesson and the PR-cell policy sentences are the parts of the design that fit
the target best, and they are also the parts closest to a plain rule ("the PR's own siblings are not
conformance"; "these policies are asked on every PR"). The cell contract is the part that fits it
worst.

## 6. The steelman, and the experiment

**The strongest version.** The free reviewer already holds the facts behind two thirds of the asks it
misses (34 `none` and 14 `demand` of 66, **verified** aggregate §2) and clears them on grounds a
maintainer would not accept as a reason for silence; when a short, right list tells it these are asked
for, it files them (DP +0.197; v0106–v0108, v0029 and d0032 each 0→3 of 3 and v0062/v0063 0→2 on one sentence,
**verified**). So the thing to build is not another source but a submission contract in which
`conforms` is legal only with a named check (tool-call id), a dated library form or a cited
convention; every other cell ends in a finding or a question; worth, a guess, siblings, a plurality, a
budget and the brief's form are not reasons; a satisfied sentence clears only its own cell; and a
failed check on the reviewer's candidate is reported as a question with the check's output. That is
S2's paragraph generalised from a detector list to every cell, D1's ledger made refusable on its
evidence, and the question form that five of the 93 gold asks take (v0068, v0092, v0105, p0005,
p0000); its precedents (D1 +1.7 at threshold on Claude, S2 +4 of 13 on gpt-5.5, DP +0.20 on DeepSeek)
all point the same way, and it is one rule instead of three partial ones. Its honest cost is volume at
about 5% demand, which is why it is a generator for an adjudicated selection stage, not a reviewer.

**The one experiment that would most change my mind:** the factorial's order contrast with the volume
guards on: R without the question set against AP + cells + questions, on the ten PRs that hold the 32
`K`-inadmissible asks and the four control PRs, three reps, matched by the table's matchers. If the
order adds more than the noise on reach *and* asks reached a finding stay at or above AP's 0.295 *and*
the control PRs stay at or under 2.0 findings, the order is a design and not a label, and I would
withdraw (a) and (b). If reach rises with the guards tripped, it is the places test again. If the
contrast is inside the noise, the design is S2 with cells and a question form, and should be written up
as that, with the question set as the detector list it is.

## 7. What survives

- **The inadmissible-grounds rule, as a schema on `conforms`, not as prose.** Enforceable, general,
  and the one thing the record has not built as a validator. Pair it with C3's counts.
- **Questions as legal findings carrying a check's result.** Five gold asks need it; the matcher needs
  a question form (§8 of the draft is right); the 2026-10-06 plan's narrowing to `ask_author` (the
  check failed for want of a piece the author could add) is the version that does not file every
  failed compile.
- **The negative guard:** a satisfied convention clears its own cell and nothing adjacent (p0012,
  p0008). Cheap, and it addresses AP's two measured losses.
- **The direction lesson for the target:** a PR's own siblings are not conformance. State it as a rule
  for the reviewer and as a note on the AI-PR label.
- **§8's gold defects** (question asks, twins counted twice, a rename counted four times).
- **Not surviving as stated:** the rank numbers as a prompt device; §3.3 as "one structure" (it is seven
  sources, five unbuilt); "no cap" and "nothing withheld on worth"; the dispositions re-read; the claim
  that the design is distinct from S2 plus cells plus questions, until the contrast in §4.2 is run.
