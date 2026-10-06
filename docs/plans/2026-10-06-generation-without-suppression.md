# Generation without suppression: section items get a disposition, not a silent drop (draft plan, 2026-10-06)

**Status** — draft, revised after an adversarial round of three independent reviewers (the record,
the evidence, the measurement), which overturned most of the first draft's evidence claims and its
measurement. Nothing built, nothing run. The proposed run is the user's call: it uses the primary
Claude token, and it amends the pre-registration of another thread's pending stage.

**The user (2026-10-06).** *"We had two different results recently from conventions runs that suggest
prompting may need a bit of work to convince models to output the findings they consider and then
suppress because they assume maintainers wouldn't raise these findings. The generation step of
findings seems to deserve a separate step from assessment/suppression, but we can only study it once
the generation matches the maintainers sufficiently. ... ideally we want no findings to be considered
in the reasoning trajectories and then suppressed due to model's internal judgement. This is
especially true when we are briefing the models using conventions."*

## The two runs

Both are stages of the conventions ceiling probe
(`results/pr_review_v5/probes/conventions-ceiling-2026-10-04/`).

- **Claude: stage G, session G1** (2026-10-05/06, read in `28af426c`, README Result 5). Opus 5.5 on the
  subscription route, brief X plus "Places where a maintainers' convention may apply"
  (`probes.CANDIDATES_LEAD`): 13 to 74 pinpointed items a PR, 385 in all, about half from decoy rules.
  Sessions in `results/pr_review_v5/probes/{model-gap-val-small12,construction-demo-2026-09-29,postcutoff-2026-09-29}/pr<N>/G1/`.
  In-census reach +0.000 against unbriefed X; the exact brief E read +0.282.
- **GPT: stage M, run GE1** (2026-10-05, read in `1b40571a`, `cross_model.md`). gpt-5.5 through ELM,
  effort high, reasoning carried, summaries on; brief G, `filing_bar: merge`, plus the exact conventions
  section (`probes.CONVENTIONS_LEAD`). Runs `probe_conv_{val,post}_elmgpt55_exact_rep1`; summaries in
  `reasoning_content` of `.ape/runs/<run>/tasks/*/samples/0/attempts/*/conversations/`. In-census reach
  0.19 to 0.41, +0.222. Its unbriefed twin is Eb1 (`elm-parity-2026-10-05`).

## What the transcripts show

Read by hand and not blind: the first draft by this session, then every miss by the evidence reviewer,
checked against notes and raw logs. `cross_model.md` pre-registered the GE half of this reading and had
not reported it; it is recorded there now.

| how the ask was missed | stage G: the 10 asks only E reached | GE1: its 23 in-census misses |
|---|---|---|
| considered, then dropped on a guess about maintainers | **2** (p0003, p0007) | **2** (v0030; v0093 compiled, then withheld) |
| considered, rejected on the merits | 1 (p0012; could count either way) | 1 (v0067) |
| considered, untested, or the check failed | 0 | 7 |
| a different change filed at the place (matcher `partial`) | **6** | 2 |
| never considered | 1 | **11** |

The cases of the first row, verbatim:

| ask | the maintainer asked | the reviewer |
|---|---|---|
| 42814 p0007 (G1; delivered as *departs*) | one `variable {D}` for the repeated binder | notes l.75-76: "Missing docstrings on theorems, line-wrapping and `variable {D}` items: Mathlib does not require these, so I would not request them." |
| 42184 p0003 (G1) | a `HasProd` version | notes l.16: "A `HasProd.nonneg` form or a `positivity` extension for `tprod` would be natural follow-ups. ... I would not require any of these in this PR." |
| 28649 v0029 (G1; no reviewer reached it) | leave the author's prose alone | notes l.57: "A maintainer would not ask to revert it. Dropped." |
| 28649 v0030 (GE1) | full words in the docstring, not `MGFs` | t2: "However, I doubt that maintainers would request changes for commonly used acronyms, given their widespread acceptance." Then `findings: []`, `merge_ready_as_is: true`. |
| 32875 v0093 (GE1) | `simpa using` the lemma | compiled a `simpa only ... using` close early, then at t12: "not entirely confident about that choice". Not filed. |
| 43024 p0008 (Eb1, unbriefed) | `_mono` -> `_anti` | t17: "If I suggest a name change and the maintainers disagree, I could be creating a false positive" |

GE1 also left compiled edits unfiled with no reason given: a `rw` alternative at v0092, and a
`positivity` extension on 42184 (not an ask).

**What this supports, at its altitude.** Withholding on a guess about maintainers is real in both
families, and the transcripts show it directly. At the asks it is a minor share of the loss: two or
three of stage G's ten, two of GE1's twenty-three. Stage G's larger loss is a different change filed at
the right place; GE1's is the asked change never considered. Removing the withholding would move
stage G from 9 to at most 11-13 of its 21 at-place asks. The user's goal (nothing considered and then
silently dropped) is still worth meeting for its own sake: an assessment step can only be studied on
what generation emits. But it should not be sold as the recall lever.

**What the first draft claimed and the review overturned.**
- *"The same ask, 42814 p0004, was considered and dropped by both families."* Mispaired in both: G1's
  alias line sits under `Int.squarefree_iff_prime_sq_not_dvd`, not at the ask's declaration
  (`candidate_retrieval.json`: p0004 `place: false`); GE1's t8 passage asks whether the directions are
  used separately, which is the convention's own precondition, a merits test.
- *"Of the 10 asks only E reached, 8 had a candidate at the place and G reached none."* True of
  `reached`, but 6 of the 10 are `partial`: G1 filed at the place, a different change.
- *"The brief's clauses install the filter."* Not isolated. E1 carries the same clauses at the same
  lines, writes the same kind of note ("Mathlib does not require docstrings", 30641 l.16; "a minor nit
  and I did not file it", 43167 l.50), and still filed both of G1's clear cases: the `variable`
  refactor (42814 E1 l.47) and `HasProd.nonneg` (42184 E1 l.37-39), under the same convention sentences.
  What differs between E and G is the delivery: one to five conventions drawn from the real asks,
  against 13 to 74 items, half decoys, framed as "a claim to verify". The README's Result 5 reads it
  the same way.

## Where the prompt asks for the filter

Every clause below asks the reviewer to predict maintainer insistence and to file only above it. E1
shows they are not sufficient to suppress; they are what the reviewer cites when it does.

| id | text | where | G1 | GE1 |
|---|---|---|---|---|
| B1 | "Predict concrete changes a maintainer would plausibly request, not ... questions ... or notes that something is merely worth checking." | brief X / G / G2, l.3-5 | yes | yes |
| B2 | "Submit only actionable requests ... and submit none when no request is warranted." | brief l.20-21 | yes | yes |
| B3 | "Apply every item ... but emit a finding only for a concrete change you would actually request." | brief l.29-30 | yes | yes |
| B4 | "Do not report that an item was checked, does not apply, or is merely worth investigating." | brief l.43 | yes | yes |
| L1 | "where it does not [depart], drop the item and say nothing of it." | `probes.py:442` | yes | -- |
| H1-H3 | severity "if a maintainer would withhold merge"; `merge_ready_as_is`; the empty-review mandate | `solo.py:137`, `base.py:786`, `base.py:164` | -- | yes |
| H4 | the budget refusal: "keeping the changes you would most insist on" | `base.py:724` | -- | (not hit) |
| S1 | "Findings you do not believe cost more than the ones you omit." | `solo.py:82`, default solo brief only | -- | -- |

L1 drops only items that do not depart, a merits condition. G1 overrode the lead's instruction to file
on two items delivered as *departs* (p0007, p0012), so restating "departs: file" is not enough alone.
Contract v2 (stage 5's harness) has no H1-H3 and keeps B1-B4.

## What the record already tried

- **The unified contract** (2026-09-23, `docs/dead-ends.md`): arms told that "a claim you hold at advisory
  strength ... file it as advisory rather than withholding it", the silence licence removed, a verdict
  per target. 3/10 against a control's 2/10, under the bar of 5: "the residual is statements, not
  silences". The closest prior; the first draft left it out.
- **`filing_bar: request`** (`filing-bar-2026-09-30`): "would request, not would require", H1-H3
  removed. Released the withheld edits on unbriefed validation (gpt-5.5 24 to 43 findings), reach
  0.200 to 0.200. Its in-sample set gained +0.125 and was ruled not to decide.
- **`forbid_abstention`** (2026-09-14): refusal text "submit the single best candidate you considered,
  even if you judged it below your usual bar, and set model_confidence to reflect how weak it is"
  (`candidates.py:822-826`). Recall 0.20 to 0.50 on 4 PRs, control emission 1 to 36, one rep.
- **D1, a verdict per declaration and concern** (`review-designs-2026-10-02`): gpt_5.2 98% `no_issue`,
  2/23. On Opus 5.5, one rep: 10 of 23 against the hygiene baseline's 9, 9 and 7, with 128 findings
  against 93-103 and 1.5 control findings a control PR; D2's critic overturned 28 of 1,812 `no_issue` cells and refuted none.
- **The local-model steering screen** (`local-unlock-2026-10-03`): over-file 3, 3, 0, 1, 0, the one
  direction that helped the floor model.
- **Uptake as a signal**: `model_confidence` within-PR AUC 0.485 / 0.485 / 0.514 (`docs/dead-ends.md`);
  `severity=blocking` 0.601 (`docs/todo/selection-signal.md`); stage H's deciders 0.56-0.64.
- **Stage G's untried list** (Result 5): the exact entries under G's verify-and-drop lead; an asserting
  lead that files a question where a check fails. C1 below is the second, narrowed.
- **Emission gates.** The 2026-09-22 ruling forbids *designing* selection, not measuring emission;
  every plan after it kept a gate (arms-speak, D1 at 2.0 a control PR, stage 5 at 1.0 a PR). This plan
  keeps one.

## The proposed change

**C1. A disposition for every delivered item, with the guess about maintainers removed from it.** A new
lead constant beside `CANDIDATES_LEAD` (which `test_probes.py:478-498` pins), for pinpointed items:

> A separate pass compared this PR's changed code with conventions Mathlib's maintainers have asked
> for on other PRs. Each item below names a place where one convention's situation occurs, the
> convention, and how to tell whether the code departs from it. The pass read the diff only and ran
> nothing. Give every item exactly one disposition in your notes:
> - `departs`: file the change the convention calls for, as a finding at that place. An item marked
>   "Decided by reading: the code departs" is `departs` unless a line you quote shows the required
>   form is already there.
> - `conforms`: only if a check you ran, or a line of the code you quote, shows the required form
>   already holds, or the item's "Not when" applies. Name the check or quote the line.
> - `ask_author`: the check could not be run, or it failed for want of a piece the author could add
>   (a missing lemma, attribute or import). File a question that names the piece.
>
> What Mathlib usually requires, accepts or enforces, how minor the change is, and whether a
> maintainer would insist on it are not reasons for any disposition. For these items, this replaces
> the brief's instruction to emit only what you would actually request. Review the rest of the PR as
> the brief says.

For a detector section (stage 5), the same rule as a closing paragraph after the sections, with
`departs` and `conforms` only. The lead says maintainers asked for each convention *on other PRs*,
which is true; it does not say they raise it here, which stage H measured at 5% or less.

**C2 (GPT, built).** Any GPT condition runs under `filing_bar: request`, which removes H1-H3.

**C3. The audit, in code.** Per session, mechanically: delivered *departs* items not filed (brief
against findings); compiled edits whose declaration no finding targets (`model-inspection-2026-09-30/filing.py`,
which would have caught v0092 and v0093); `conforms` dispositions with no check or quote. The user's
target is the first two at zero. Not a lexicon count of uptake words: the treatment bans the words, so
that count would measure phrasing.

The brief stays byte-identical, so the condition differs from its baseline in one place.

## The first measurement

**Deciding, out of sample: a third condition in convention-detectors stage 5**
(`results/pr_review_v5/probes/convention-detectors-2026-10-06/README.md`, set up in `6a0ebaeb`, not
run). Sixteen census PRs disjoint from every evaluation set, 13 asks that a detector states word for
word, a stratum of unasked PRs as the emission control, read by hand. Its pre-registration already
predicts S1 null because of stage G's override. Add, before any of its sessions:
- **S2**: S1's context with C1's closing paragraph, from a new context file. Nothing else differs:
  same harness, brief G2, tools, finding budget (report any session the budget refusal reached). New
  run name, since the context file feeds the run's digest.
- **Rule**: S2 − S1 at least **4 of 13** asks filed: the disposition is a lever. **1 or fewer**: it is
  not. Between: a second rep decides. Skip S2 if S1 already files 10 of 13.
- **Gate**: stratum-B findings that repeat an unasked fact, S2 against S1; more than 1.0 more a PR
  makes it a volume lever whatever it does to the asks (stage 5's own bar).
- **Also read**: C3's counts, S1 against S2.
- **Cost**: 16 more sessions on the primary token. G1's ten moved the week 8 points, so about 13 points
  of the week; no matchers (read by hand).

**In-sample companion, optional.** G1' on the four PRs holding the documented stage G cases (42814,
43167, 42184, 28649) with C1 replacing `CANDIDATES_LEAD`, matched in a fresh seal beside G1 and E1, read
item by item: does it file at least 3 of p0007, p0012, p0003 and v0029, and do C3's counts fall to zero?
It checks that the wording reaches the observed behaviour. Like the filing bar's post-cutoff set, it
does not decide. About 3 points of the week and one seal.

**GPT: not yet.** GE1's misses are mostly never considered (11 of 23), which no filing instruction
reaches. A GPT replication under C1 and C2 follows only if S2 moves.

## Considered and set aside, with the evidence

| proposal (first draft) | why set aside | reopens if |
|---|---|---|
| Rewrite B2-B4 across the whole brief ("report every change you considered ...") | A generalised `filing_bar: request` (null out of sample), the unified contract's wording (3/10 vs 2/10), the floor model's over-file; and E1 carries B1-B4 and files anyway | C1 releases the section items while C3's count outside the section stays high |
| `maintainer_uptake` on every finding | Asks for exactly the judgement the user wants out of generation; `confidence` already exists in the tool; every uptake signal on record reads 0.49-0.64 | the assessment step is built and needs an in-session prior |
| Questions legal everywhere | 42814 alone carried about 60 check items; every failed check admits "a variant might work". Narrowed to `ask_author` | -- |
| Stage G's ten PRs as the deciding set, rule 14 of 21 | In-sample (the notes motivated the wording); the pool was chosen knowing the asks, so filing every item is stage H's "all" row (recall 1.0, precision 0.081); releasing every documented case reaches at most 13 | -- |
| No emission gate, citing the 2026-09-22 ruling | Misreads the ruling; every plan since kept a gate | -- |
| A decision-turn replay of GE1 | In-sample; `cli replay` handles arm sessions only; tests a closing instruction, not the brief | GPT replication is wanted cheaply after S2 |

## What it does not settle

- Whether the released findings are welcome. Gold is round-1 asks, a lower bound; stage H's open
  adjudication ("would a maintainer accept this if proposed?") is the assessment question this plan
  postpones.
- The larger losses: a different change filed at the right place (stage G), and the asked change never
  considered (GE1).
- Claude's thinking is not visible on the subscription route; its audit reads `notes.md` and the calls.
