# Does knowing the conventions make a reviewer more like the maintainers?

**Status** — open, drafted 2026-10-04, **for a fresh session**; nothing here has run. Stage A is
free to start (local models); its paid half and Stage B wait on the readings written below.
**Cost** — Stage A: local models $0; `gpt-5-mini` about $25; `gpt_5.2` about $60-90 (cap $100);
Claude about two subscription windows. Stage B, only if Stage A passes: about $30 and four windows.

**The user (2026-10-04).** *"We started this work in order to assess whether a) an agent can
automatically learn the conventions being followed at a given point in development b) knowing about
the conventions yields better reviewing, more aligned with expert maintainers. It's this second
point that we can test at this point."*

**Motivating measurements.**
- **The census exists** (`results/pr_review_v5/adjudications/conventions-census-v1/results.md`).
  Two blind readers wrote 409 and 407 principles behind 1,833 val1000 asks. The top 50 cover 55% of
  principled asks, and 370 form a tail. The design-comparison reading found only 8 of 31 variant
  principles in any written document.
- **The residual wall is largely convention knowledge.** 25 of the 67 asks no reviewer reaches on
  three sets are convention or mechanism knowledge (Phase 1, `docs/plans/2026-10-03-after-structure.md`
  on `develop`). 5 of dev's 9 never-reached obligations are conventions a check can state.
- **A labelled held-out sample is ready, with no further labelling.** Reader A labelled all 269
  other-years asks (129 PRs, 2024-05..2025-05 and 2026-04..2026-08) against its codebook. 230 sit on
  a diff hunk, across 99 PRs. Against the frozen val1000 codebook (409 entries, `781a80b2`) they
  split as follows:

  | stratum | inline asks | meaning |
  |---|---|---|
  | frozen head | 61 | the ask's principle is one of the 50 most-used val1000 entries |
  | frozen tail | 68 | a val1000 entry outside the top 50 |
  | stretched | 55 | a val1000 entry that A broadened while reading these asks |
  | out of census | 28 | an entry A created on these asks |
  | none | 18 | a fact about this PR alone |

  7 sit on AI-authored PRs and 16 on PRs created after Claude's June 2026 cutoff. Every evaluation
  set (dev, val small12, val60, test60, post-cutoff) is PR-disjoint from every PR the census read
  (checked 2026-10-04).

**What the record already rules out, and why this is not a rerun.**
- **Rules in the prompt did nothing twice.** The "statute" guideline injection was null at N=115 on
  two models. Precedent priming was delivered (47% of findings echoed a precedent) but did not
  transfer, 13 against 11 (`docs/dead-ends.md`). Facts about the PR moved things instead: the
  counted rename for the naming arm, and the long line once the compile reported it.
- **Evidence in the packet is filed about one time in three.** On 33337 `naming_norm` gave every
  Opus cell the maintainers' name, and one rep of three filed it.
- **Local models sit at the floor as agentic reviewers.** Qwen3.5-397B reached 2, 0 and 2 of 23
  (`89435e84`), so they are an early-testing tier only.
- **What is new here.** The statute delivered the written guidance, which is the census's head. The
  census adds the tail no document holds. And Stage A asks a question no earlier probe isolated:
  does the knowledge change what a model asks when it is shown the exact site, with search and
  initiative removed? A null there closes the rules form for good. A positive there, followed by a
  Stage B null, puts the loss in search or filing, not in knowledge.

## The hypothesis

Supplying the census's knowledge makes a reviewer's asks more like the maintainers'. More of their
asks are reached, without asking more where they did not. The gain is concentrated on asks whose
principle the census holds.

**The specificity control comes free.** A generic prompt effect, such as "a long list of style rules
makes the model ask more style questions", lifts every stratum. Knowledge lifts the in-census strata
and not the out-of-census one. The control sites catch a general rise in asking.

## Stage A — the site-given test (knowledge without search)

**Item.** A site is a diff hunk ending at the commented line, with the PR title, the file path and
the enclosing declaration from the reviewed head. The model is asked one question: *what, if
anything, would a Mathlib maintainer ask the author to change here?* It replies `NONE` or one
request (object, change, one-sentence reason). No tools, single turn. It never sees the maintainer's
comment.
- **Ask sites:** the 230 inline held-out asks above.
- **Control sites:** 230 changed hunks from the same 99 PRs, drawn by a seed, with no round-1 comment
  within five lines. Draw them from the change graph at the reviewed head, as
  `arm-coverage-val1000-…/provenance/build_structure.py` does, not from `files[].patch`, which is the
  merged diff. Silence is not proof that nothing is wrong, so asks at control sites are reported as a
  rate, never as errors.

**Conditions.** Only the knowledge section varies. Each section is built once, before any model sees
an ask, frozen, and hashed into the run plan.

| id | knowledge section | what it tests |
|---|---|---|
| K0 | none | the baseline |
| K1 | the written guidance: style guide, review guide, values and naming pages as summarised in `design-comparison-val1000-v1/written_sources.md`, plus the library-note titles | the statute's content: what is written |
| K2 | the census head: A's 50 most-used val1000 principles | the head alone |
| K3 | the full census: A's 409 val1000 principles (`781a80b2`, about 15k tokens) | the head plus the tail, as rules |
| K4 | a shortlist: the 10 census principles a local model picks for this site | rules, restricted to the site |
| K5 | facts: for each shortlisted principle the local model judges to apply, one sentence about this code ("`foo_of_isBar` takes `h : IsBar x` first; principle: …") | facts about the PR, the delivery the record favours |

K4 and K5 come from one instantiation pass by `elm_qwen_3.5` over the frozen codebook and the site,
run once. Every reviewer model then reads the same shortlist and facts. The pass is measured alone,
before any reviewer reads it:
- shortlist recall at 10 against A's label on the 129 frozen in-census sites;
- facts emitted per control site.
The gate is recall@10 of at least 0.5 and at most two facts per control site. Below it, K4 and K5
are dropped from the paid cells and the pass is iterated on local models.

An optional K3b uses B's codebook in place of A's, on `gpt-5-mini` only. It checks that an effect
does not belong to one reader's phrasing.

**Models, in tiers.** Run a tier only after the one before it.

| tier | model | role | reps |
|---|---|---|---|
| A0 | `elm_qwen_3.5` (reasoning none), `elm_mistral_small_4` | free shakeout: prompts parse, outputs conform, the matcher pipeline runs; a first signal, never quoted as a result | 2 |
| A1 | `gpt-5-mini` | cheap signal across all six conditions | 2 |
| A2 | `gpt_5.2`, reasoning high | **decisive**: K0, K1, the best of K2-K4 from A1, and K5 | 2 |
| A2 | Claude Opus 5.5 (subscription) | the ceiling model: K0 and the best census condition | 1 |

**Outcome.**
- **Primary: site reach.** The share of ask sites where the model's request is the maintainer's
  request: the same object and the same change. `Partial` (the right concern, a different fix) is
  reported beside it and not counted.
- **Control ask rate.** The share of control sites where the model asks anything.
- **Selectivity.** Ask rate at ask sites minus ask rate at control sites.

Every outcome is reported by stratum, with AI-authored PRs and post-cutoff PRs as their own rows.
Means, unions and stable sets are over the reps.

**Matching.** The decisive cells get two blind Claude matchers, condition-blind with the conditions
shuffled per site, on a site-level adaptation of `construction-demo-2026-09-29/matcher_rubric.md`.
The A0 and A1 cells use a `gpt-5-mini` matcher calibrated against the two on 300 stratified pairs.
If that matcher agrees with them below 0.85, it is not used and those cells are matched by Claude.

**Reading rule, fixed before any run.** It is read on the decisive models only. Here Δ(K) means
reach under K minus reach under K0, on the 129 frozen in-census sites; Δ_out is the same on the 28
out-of-census sites.

| reading | when |
|---|---|
| **T1, the knowledge transfers at the site** | some K in {K3, K4, K5} has Δ ≥ +0.10 on both matchers, with Δ_out ≤ Δ / 2 and a control ask rate no more than 0.10 above K0's |
| **T2, the census adds to what is written** | on the 68 frozen-tail sites, that K's Δ exceeds K1's Δ by ≥ 0.10, in the same direction on both decisive models |
| **null** | every census condition has \|Δ\| ≤ 0.05 on both decisive models: the knowledge does not change what a model asks even at the exact site |
| **ambiguous** | anything else: run a third rep of the best condition before deciding |

At these sizes one site is 0.8 points of reach on the in-census stratum and 1.5 on the tail, so the
thresholds sit at about two standard errors and three repetitions are the floor for anything quoted.
K5 against K3 is reported as the facts-against-rules contrast, with no threshold. The stretched
stratum (55) is reported apart and enters no reading.

**If null:** a `docs/dead-ends.md` entry, "census knowledge as prompt text", naming the untried
deliveries: few-shot exemplars of each principle's asks, principle-specific deterministic detectors
(`develop`'s plan, step 2), and a model trained on the census. Stage B does not run in this form.

**Optional replication, A3** (about $40, only after T1 passes). The decisive cell against K0 on the
same-window outside sample: 801 agreed asks from 300 PRs, which the census never read (its held-out
reading paused before them). This reading is unstratified and needs no census labels.

## Stage B — the full review (only if T1 passes on a decisive model)

**Design.** The instantiation pass runs over every changed declaration of each PR, through
`elm_qwen_3.5`. Its facts are delivered as a packet section, the delivery the develop plan's step 2
specifies for its detectors: facts keyed to declarations, restricted to the diff. The pass is
measured alone first, under the static-pass protocol:
- facts at gold sites, read by hand;
- emission on the control PRs;
- before any reviewer reads it.

The reviewers are Claude Opus 5.5 (subscription, probe harness, 2 reps) and `gpt_5.2` carried
(Responses, 2 reps). Sets are val small12 (30 asks) and post-cutoff (16 asks), with dev (23
obligations, judge v9) as a third, secondary reading. The baseline cells are the develop plan's
step 1 hygiene-baseline cells on the same sets: shared, not rerun.

**Reading rule** (the post-carry-over plan's general rule). Reach must rise by ≥ 0.10 on both
matchers on at least one set and fall on none, with asks reached per finding no lower than the
baseline's. At 16 asks, 0.10 is one and a half asks. A Stage B positive is therefore provisional
until the post-cutoff set grows (that plan, §6).

**Relation to the develop plan's detectors.** Its step 2 hand-writes five detectors. The census
pass is the generic version over 409 principles. If both exist, the combination is a later cell;
neither waits on the other.

## What to build (native to APE)

- **The site task.** A single-turn, no-tool task over (site, knowledge section), run by
  `TaskOrchestrator` through `cli run`. The condition and the model go into the run name. First check
  whether the judge's single-turn task can host it; extend that before adding a module. The
  zero-priced local models need the token block (`cli plan` refuses otherwise).
- **The site builder.** Ask sites come from `provenance/materialise_bodies.py` (by event id). Control
  sites come from the change graphs at the reviewed head. It writes `sites.jsonl` with no
  maintainer text in any field a reviewer reads, and the maintainer comments separately for the
  matcher.
- **The knowledge sections.** K1, K2 and K3 are built from committed files; K4 and K5 from the
  instantiation pass, frozen.
- **The analysis.** Reach, control rate and selectivity by stratum and cell; mean, union and stable
  over reps; the T1/T2 reading printed against the table above.

## What would close it

The Stage A table: models by conditions by strata, with control rates and the T1 and T2 verdicts.
Then either a dead-ends entry (null), or Stage B's two-set reading. The result is recorded here and
in the census's `results.md` §7. Point (a), whether an agent can learn the conventions itself, is
the census's own thread and is not tested here.

## Risks

- **The site task is easier than review.** A Stage A positive shows the knowledge *can* change the
  ask, not that a reviewer will find the site and file it (the 33337 discount). Stage B is the test
  of that.
- **The census was written by Claude from merged PRs.** For a Claude reviewer it may be redundant
  with what the model already knows. For `gpt_5.2` it is cross-model transfer. Either result is
  informative, and the two are read separately.
- **Most of the sample is in Claude's training window.** Only 16 inline asks are after the cutoff.
  The recall check (`reviewer-model-gap.md`, test (a)) found in-window reach is not mainly recall,
  but the post-cutoff row is reported apart.
- **Matching at the site is lenient toward the right concern.** That is why `partial` is never
  counted.
- **K3 is the statute with the tail added.** A null on K3 alone would replicate the statute, not
  close the question. The question closes only if K4 and K5 are null too.

## Start here

- **Read:** the census `results.md` (§1-5) and `reader_rubric_census_v1.md`; `crossmap.json` for
  how the two codebooks pair; `docs/dead-ends.md` ("statute", "Precedent priming, Mode A",
  self-hosted tier); `develop`'s `docs/plans/2026-10-03-after-structure.md` §1-2; the post-carry-over
  plan §5-6 on `pipeline-overfit-review`.
- **Run (spends nothing):** the strata table above comes from reader A's `labels_y*.jsonl`, the frozen
  codebook (`git show 781a80b2:…/reader_A/codebook.json`) and the materialised bodies;
  `analyse.py` in the census directory prints the census side.
- **First step:** build the site set, ask sites and control sites, and run K0 and K3 on
  `elm_qwen_3.5`. That proves the pipeline end to end at no cost before anything else is written.
