# Plan — align the arms' decisions with maintainers', learned from the corpus, measured at scale

*2026-09-25. Written after the user's ruling that the probe thread had stopped short: "We must
inspect the pipeline and the results carefully and try to draft a solid plan for improving the
pipeline to be better aligned with gold obligations … we have over 20,000 PRs to learn from."*

## What the record settles: where the gold is lost

Every number below is from committed artifacts; the sources are named. Held-out set: the twelve
dev PRs, 22-23 counted obligations, three lead reps on `gpt_5.2`
(`pr5_A_lead_heldout12_v2_rep{1,2,3}`).

| stage | measured loss | source |
|---|---|---|
| **the question is not in any brief** | 2 of 23 obligations `none`, 4 `partial`; 17 `full`, of which **7 only because text was written from these PRs** | `the-question-is-already-asked-2026-09.md` |
| **the lead pruned the arm holding the question** | 25 of the 42 obligation-rep misses. But when fanout ran those same arms, they filed **0 of 7**; specialists alone reach 2-3 of 10 on the fanout PRs | same; `routing-remit-and-silence.md`; `unified-contract-fanout4-2026-09.md` |
| **the arm ran, had the question, and declined** | 15 of 42 misses. Of 58 gold-site silences, **17 are "the right arm considered the ask and declined on stated grounds"**; 37 are correct off-remit silences; tools and noise total 4 | `specialist-silences-2026-09.md` |
| **the arm filed a smaller or different ask at the right site** | 4 of the 7 residual misses once every arm answers every target: "introduce a lemma", "generalize the constant", refactors | `unified-contract-fanout4-2026-09.md` |
| **evidence the tool cannot produce** | 2 of 7: suffix and namespace naming; `naming_norm` counts leading tokens only | same; `naming-from-statement.md` |
| **a compound ask filed in halves** | 1 of 7 | same |
| **found but not published** | 7 found → 2 published; the family gate. **Parked by the user as selection** | `the-admission-gate-2026-09.md`; `dead-ends.md` |

Three facts frame those rows:

- **Forcing the decision moves recall more than anything else tried:** 0.20 → 0.50 on the fanout
  PRs, at the cost of 36 findings on the control PR. The arms *have* the maintainers' asks
  available and decide against filing them. The verdict contract (`target_verdicts`,
  `verify_edits_if_present`) keeps the direction at zero control cost, but reaches only 3 of 10.
- **Every `gpt_5.2` call in the record ran with reasoning off:** `reasoning_tokens: 0` in 2,857 of
  2,857 arm attempts; the config knob that appears to enable it is inert
  (`reasoning-in-the-arms.md`, parked 2026-09-23). The judgment failures above were all measured
  without reasoning.
- **The instrument cannot see a small improvement.** One obligation is 10 pp; the judge agrees
  with itself about 90% of the time; three reps' union (7) equals the best rep. The dev set is
  burned, is one reviewer's on 4 PRs, and has 1 PR-level obligation in 43. Validation has **no
  gold** but has **1,833 round-1 asks** labelled by family and by facet at κ 0.86-0.95, and **214
  PRs on which maintainers asked for nothing**, which is a control set the dev set never had.

**So the binding loss on the generator side is the decision:** the arm sees the site, holds the
question, and either judges the code fine or asks a smaller question than the maintainer would.
Pruning is not the story (the pruned arms file nothing when run); the questions mostly exist;
publication is parked. Reasoning was never on.

## Why the decision diverges, and what the corpus can supply

The facet relabel (`review-work-structure-2026-09.md` §7.8) says what settles a maintainer's ask,
on 552 validation asks both readers agree on:

| what settles the ask | share | what the arm has today |
|---|---|---|
| a compile | 39% | `lean_verify_edit`; it works when the arm tries (round 2 verified design points), and forcing shows the arm often does not try |
| a count of the library's norms | 25% | `naming_norm`, leading token only; nothing for statement form, binders, syntax or layout |
| **judgment** | **31%** | **nothing.** The arm substitutes its own taste for the maintainers': "is this the right encoding", "is this worth having", "should the sibling get the same fix", "is the description adequate" |
| exhibiting an existing declaration | 5% | `declaration_search`, `content_search` |

The judgment share is where the 17 "considered and declined" silences and the "smaller ask at the
right site" residual live: a variant the maintainer wanted (54 of 170 judgment asks), intent (28),
siblings (22), process (20). A maintainer's judgment is not free-floating; it is what they have
asked before on code like this, and what they let through. **That is what 104,093 reviewer
comments on 14,718 PRs (2024-03..2026-08) contain, and what no tool gives the arm at the moment
it decides.**

What has been tried with the corpus and is dead (`dead-ends.md`): distilled guidelines appended to
the prompt (null at N=115); precedents as prompt priming (delivery worked, transfer failed);
unconditioned flag-rate priors (chance, and computed on leaked sites); selectors over the system's
own findings from artifact features (chance). What those entries say would reopen them:
**recognition mode, ranking, concern-conditioned, with an anti-precedent corpus** — the precedent
consulted *at the decision*, about *this ask*, with the base rate of code like this drawing no
such ask. That is untried, and it is the shape the diagnosis calls for.

## The design

Four phases, in order. Nothing is built on the dev set. Every paid step has its rule stated
before it runs.

### Phase A — the instrument: a validation bench at ask level, with controls

No treatment can be read without this. It replaces "22 obligations, ±10 pp" with a target
forty times larger and a real control set.

- **The sample:** 50 val1000 PRs, drawn with a seed from the sealed draw: 40 with at least 2
  agreed round-1 asks (stratified AI / main at val1000's rate, 12.6% AI, rounded up so AI ≥ 8),
  and **10 of the 214 no-feedback PRs as controls**. Work-unit cap 12, so no PR is most of a run.
- **The build:** a release from the val1000 structure build (already done for 970 PRs;
  `provenance/build_structure.py`), base workspaces (`ape.toolkits.execute.lean.build`, ~16 min a
  commit) and reviewed workspaces (`prebuild --reviewed`, 2-17 min each). Run in the background;
  about a day of wall time, no model spend.
- **The metric,** computed on the generator's output (`findings.jsonl`, every channel — what the
  run *found*, since publication is parked), by two blind matchers with the probe rubric
  (`results/pr_review_v5/probes/facet-brief-2026-09-25/match/matcher_rubric.md`), conditions
  shuffled per PR:
  - **ask recall:** asks reached, as mean over reps / union / stable, with a PR-bootstrap CI;
  - **emission:** findings per PR, findings per control PR, unmatched findings per PR.

  Always the pair, never one number. The matchers are Claude readers judging text; the reviewer
  cutoff caveat does not apply to them.
- **The baseline:** the current pipeline as a maintainer would receive it today — lead mode,
  `configs/bases/v5_generation.yaml`'s roster — **two reps**. Priced by `cli plan` before spend;
  the audit's val60 price was $131 worst case for 60 PRs in lead mode, so expect ~$50-70 a rep.
- **Deliverable:** the baseline's numbers with CIs, and the per-ask ledger. That is the first
  time the current system is measured against maintainers at this scale.

Cost: builds free; ~$100-140 for two baseline reps; matchers free.

### Phase B — the cheapest judgment lever: reasoning on

Parked, never ruled out, and one config flag.

1. **Free:** one `gpt_5.2` call at `reasoning_effort=low` against the same call without it, to
   see whether the provider reports a breakout and whether the $0.17 per-job cap would bind.
2. **~$8:** the twin of `pr5_V3_contract_fanout4_rep1` with reasoning on, same four PRs. Reads
   against the unified run's own residual: 4 of 7 misses were judgment failures at the right site.
   **Through if** it reaches ≥ 5 of 10 (the rule the unified run failed) with ≤ 1 control-PR
   finding; then two more reps.
3. **On the bench:** two reps of the baseline with reasoning on. **Adopt if** mean ask recall is
   ≥ 1.15× the baseline's and control emission is not above it.

If the arms were never reasoning, this is the largest untested variable in the record.

### Phase C — the corpus at the decision

Three parts, each with its own gate, so a part that fails is dropped without the others.

**C1. The question list, from the corpus** (work-enumeration Phase 1, gold-independent).
- Label ~1,000 round-1 asks from ~200 corpus PRs drawn from the 14,718 **minus** val, test and
  the 232 dev-era PRs, with rubric v2 (family, generic question) and the facet rubric v1 (object,
  reference, warrant). Both rubrics are already calibrated: κ 0.94 on family, 0.86-0.95 on facets.
- Dedupe the generic questions into a list keyed by (object, reference, warrant), each with
  corpus support, example PRs and the deterministic `applies_to` the object gives (subject kind,
  component changed, lifecycle — the inventory already records all three).
- **Gate (out of sample):** a blind reader maps val1000's 1,833 asks to list entries; the list
  covers ≥ 80%. Val asks are never put in a prompt; only corpus-derived text is.
- Cost: readers only.

**C2. Precedent recognition, with base rates.**
- Index the corpus comments by **the ask and the code it sat on**: embed the comment body together
  with the situated declaration (`review_join.situate_hunk`), not the hunk alone, which is what
  the current index does and why it is chance-level for naming and rarely carried evidence.
- Add the **anti-precedent corpus**: every changed declaration of every corpus PR, from the same
  change-graph build val1000 used, so that for a (question, object kind, area) the tool can say
  how often code like this drew that ask and how often it merged without one.
- The tool at the decision: the arm forms a candidate ask, then asks the index: *has a maintainer
  asked this on code like this?* It gets k precedents with their comments, and the base rate.
- **Gate (offline, no arm):** on val1000's judgment-cell asks, a same-question precedent is in the
  top 5 for ≥ 40% (the hunk index's own hit@5 on its bench was 49%). Below that the tool is not
  wired in, and the negative is recorded.
- Cost: compute; one background day.

**C3. The cell contract.**
- An arm is one (object, reference) cell (`review-work-structure-2026-09.md` §7.6): its question
  bundle from C1, scheduled by object from the inventory, holding the tool its warrant needs:
  compile → `verify_edits_if_present` and a verdict per target; count → the census, extended past
  naming to statement form, binders and syntax from the corpus code population; judgment →
  precedent recognition from C2, **cited in the finding**; exhibit → `declaration_search`.
- This is a generator contract, like the compile gate: it says what an arm must hold before it
  files, not which filed findings reach a maintainer. Publication is untouched.
- The generalist stays until "is the generalist droppable" is measured on the bench, not before:
  it holds 64 of 71 held-out hits.
- **Run on the bench,** two reps, against the Phase A baseline (or the Phase B baseline if B was
  adopted). **Through if** mean ask recall ≥ 1.2× baseline, the stable set is not smaller, and
  findings per control PR are not above baseline. Anything less is "this design did not reach
  more", with the untried variants listed.
- Cost: ~$100-140 for two reps in lead mode, less in lean fanout.

### Phase D — gold, and the held-out reading

- **Gold on validation.** The gold chain is the long pole (`eval-set-selection.md` §5) and must
  not reuse labels from the systems under test. Build it after C, so it scores a system worth
  scoring, and freeze the reading rule before the test-set gold is read.
- **The held-out twelve** are read last and as a secondary: burned, one reviewer, ±10 pp. A move
  there is reported; it decides nothing.

## What this plan rules out, and why

- **A facet re-division of the arms as the lever.** Three probe rounds: its apparent design gain
  was run variance (`facet-brief-probe-2026-09.md`).
- **Publication-rule changes.** Selection; the user's 2026-09-22 ruling stands.
- **A no-pruning run on the held-out twelve.** Ruled out 2026-09-23; the pruned arms file nothing
  when run.
- **Guidelines as prompt text, precedents as priming, artifact-only selectors.** Dead, with the
  reopen conditions this plan meets only for precedents (recognition at the decision).
- **Tuning the three retrieval tools for reach.** They carried 0-11% of findings' evidence in the
  probes; C2 replaces the precedent index's *key*, it does not tune the existing one.
- **Training a model.** Not the plan (user, 2026-09-24). The corpus is read into a list, an index
  and base rates.

## Risks

- **Contamination.** Val PRs are used to *measure*. No val ask, question or name enters a prompt;
  the contamination gate now sweeps tool text and gold subjects, and it should be extended to
  sweep the C1 list against val1000's declaration names before any run.
- **Model cutoff.** `gpt_5.2`'s training cutoff against the 2025-06..2026-03 window is the same
  question the eval-set plan chose the window for; state it in the bench's README before the
  baseline runs.
- **Matcher leniency.** The probe matchers credited multi-part asks; the bench rubric should
  score parts separately, and both matchers' agreement is reported.
- **Cost.** About $250-350 across A, B and C in lead mode, plus builds. Each paid step is gated
  on the one before, and `cli plan` prices every run first.
- **The generalist confound.** If C3 gains come from the generalist under the new contract, the
  droppable question is answered the other way; the bench's per-arm ledger says which.

## Sequence and bookkeeping

1. A: draw the 50 PRs (seal the list), build, run the baseline twice, publish the ledger.
2. B: the free check, the $8 twin, then the bench reps if through.
3. C1 and C2 in parallel, both offline, both gated.
4. C3 on the bench.
5. D.

Each phase is one topic branch off `develop`, merged only if it passes; the val1000 labels and
probes it depends on live on `pipeline-overfit-review` and must be merged first. Every rule above
is copied into the phase's README before its first run, with a digest.

## What this plan does not claim

It does not promise that held-out gold recall moves; that set cannot show a change smaller than
three obligations. It claims that the loss is at the decision, that the decision lacks the
maintainers' reference, that the corpus holds it, and that a bench exists on which a change of
20% is visible. If C3 fails its gate on that bench, the corpus-at-the-decision design is closed
with a measurement, which the record does not yet have.

## Revision, 2026-09-26: precedent recognition demoted; the mechanical two thirds first

**What the two validation runs added.** The current pipeline reaches 8 of 30 validation asks (27%),
the solo reviewer 2 of 30; neither reaches any of the 14 asks in interface, registration, PR level
and naming (`results/pr_review_v5/probes/val-small12-2026-09-25/README.md`). The reasoning twin
is parked (2 of 10 at 3.8× cost, 29 jobs cap-paused).

**The user's objection to Phase C2** (precedent recognition at the decision): it assumes the
reviewer can tell which past situations are similar to the one under review, and that is the deep
Mathlib knowledge the reviewer lacks. The record agrees twice: the hunk-embedded index is
chance-level for naming, and the shape-keyed join fitted 4-8% of asks ("reviewers ask about a
pattern in the code, not the declaration's shape"). Surface similarity finds code that looks
alike; a maintainer recognises code that plays the same role. **C2 is demoted to an offline
check, not a build.**

**The reframing.** Of what settles a validation ask (`review-work-structure-2026-09.md` §7.8):
compile 39%, count 25%, exhibit 5%, judgment 31%; the dev gold has the same shape. About two thirds
of asks are settled by something Lean or a census computes, with no notion of situation. The
pipeline reaches 27%. The recall is lost in the mechanical two thirds, where the dev silences also
sit (an arm that could have compiled the weaker hypothesis and did not try).

**Where similarity is needed, use the kind Lean computes:**
- *existence* is a type question: `exact?` / `apply?` / Loogle-style search at the base commit, not
  a name search (231 of the lead run's 350 tool calls were `declaration_search`);
- *consistency with siblings* is structural, from the change graph and inventory: the family's
  attributes, binders and forms against this declaration's;
- *norms* are counts over the library's text, the naming census extended to statement forms,
  binders and suffixes.

**The judgment third** (design, API completeness, location) is not reachable without the
knowledge, and a guess filed there is control-PR emission. Leave it to the maintainer until a
reviewer carries the knowledge.

**Sequence, replacing Phase C2/C3:**
1. Free: label the 22 dev misses and the 22 validation misses by what settles them.
2. Build type-directed existence search and the sibling-consistency check as tools; the contract
   files a compile-settled ask only when it compiled and an exists-ask only when the search
   returned it -- forcing restricted to the mechanical asks, which is the calibration forcing
   lacked (0.50 with 36 control findings).
3. Two runs per set against the baselines that now exist on both.
