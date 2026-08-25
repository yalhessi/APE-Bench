# Project status — Mathlib PR review on top of APE-Bench

*Branch `advisor-share`, cut 2026-08-25 against the APE-Bench drop at `main` (`2001734`).*

This branch restages roughly nine months of work as 43 commits, each one thing, ordered so
the design evolution reads forward. It is the same tree as the working repository, not a
subset or a rewrite: `src/`, `tests/`, `docs/`, `skills/` and `examples/` are byte-identical
to what the results were produced from.

**The question.** APE-Bench asks whether a model can write Lean that compiles. This work
asks a different one: given a real Mathlib pull request, would a maintainer merge it, and if
not, what specifically would they ask for? In formal mathematics correctness is *free* — the
kernel decides it, and the PRs in question compile. What decides acceptance is the residual:
duplication, generality, naming, documentation, idiom. Taste and convention, which is where
models are weakest.

**Throughline.** *Verifiable correctness is not enough.* An agent can find and
kernel-verify valid improvements. The wall is the calibrated judgment of which ones this
community would actually request.

---

## How to read this branch

| Commits | What |
|---|---|
| 1–17 | **Framework extensions to APE.** Nothing research-specific; a clean cherry-pick set. |
| 18–23 | Repository policy, the PR-review data pipeline, the curated Mathlib skills. |
| 24 | **The reviewer gate inside the generation loop** — the thesis task. |
| 25–28 | v2: decomposed checkers, the measurement, the selection wall, precedent retrieval. |
| 29 | v3: the intervention benchmark (superseded). |
| 30–36 | v4: sealed obligations, evidence, operators, the judge, the reach census. |
| 37 | The Zulip discussion store. |
| 39 | v5: the delegating lead agent (current). |
| 40–43 | Artifact policy, tests, docs. |

Commit bodies carry the reasoning and the measurements. They are the primary document; this
file is the index and the honest ledger of what is unfinished.

```
git log --reverse --stat main..advisor-share
```

---

## 1. Framework extensions to APE — commits 1–17, and 38

**Status: done, in use, and upstreamable.** Commits 1–17 touch only `src/ape/`, `examples/`,
`setup.py` and `tests/cli/`; commit 38 is the cost-model test, which lives under
`tests/datasets/` only because that directory arrives with the research code. Verified: the
range `main..caf19dc` contains nothing under `src/datasets/`, `formal_math/pr_*` or
`configs/`.

Four of these are bug fixes with measurements behind them, and they are the ones worth
looking at first:

- **Prompt-cache pricing** (`6381a83`). `_calculate_cost` added `cache_read_input_tokens` to
  `input_tokens`, charging every cached token twice. On one 9-turn conversation the repo's
  own logs reconcile as `sum(total_tokens)` = 334,970 = `sum(input) + sum(output)`, not
  `input + cached + output` = 620,794. Priced the old way that conversation came out at
  $1.164 nominal / $0.700 "discounted" against a true $0.200.
- **Budget enforcement** (`9b63f87`). `cost_limit` was charged against the no-cache
  counterfactual. One lead agent was terminated at a $1.00 cap having actually spent $0.200.
- **Task system prompts** (`1d32ef7`). `create_system_prompt()` is defined on seven task
  classes and was called by no scaffold. Every task-level contract in this project was
  silently discarded; only the user prompt reached the model.
- **Lean module system** (`190d68c`). Module-system files fail to parse under `lake env lean`
  without `experimental.module`, which the package build supplies and in-file verification
  did not. In-file verification was dead for ~33 of 138 evaluation PRs.

Also: an OpenAI provider, the unified `ape` CLI, managed agent skills, task variants, the
S3-backed remote artifact store with bundle acceleration, and the PR-head cache fast path.

**Outstanding**

- `gpt_5.4` pricing in `MODEL_MAPPINGS` is a placeholder copied from `gpt_5.2`. It affects
  reported `cost_usd` only, never behaviour, and is flagged in the mapping.
- The `prompt_inclusive` cost model is the default on the strength of this project's own
  logs, not a vendor invoice. If a bill disagrees,
  `llm_config.cost_model=prompt_exclusive` reproduces every historical figure exactly.
- Not yet offered upstream. The intended form is the commit range as-is.

---

## 2. The data pipeline — commits 21–22

**Status: done.** `src/datasets/pr_review/` reconstructs a review as it happened: base commit,
the head the reviewer was looking at (not the merged head — reviewing against the final state
leaks the answer), review events in order, and each comment with its anchored diff hunk.

**The set:** 138 reviewed mathlib4 PRs. 72 (52%) carry at least one actionable finding; 66
(48%) are clean. 143 findings, of which 115 are line-anchored and scorable. ~85% blocking.

The classifications that turned out to matter: merged vs unmerged vs *abandoned* (an author
giving up is a different signal than a rejection), AI-authored PRs held separately, and
maintainer vs drive-by commenters resolved against the roster.

**Outstanding:** the window is 2026-01-01 to 2026-03-31 plus the v2 window
(2025-09-01 to 2025-12-31). Extending it is mechanical (`config.pr_numbers` pins an exact
list) but every extension re-opens the matcher-validation question below.

---

## 3. The measurement — commits 26, and the tier scheme

**Status: done, and the most reusable thing here.**

A hit requires **same place AND same concern**, judged against the maintainer's actual
comment. Getting to that rule meant fixing three things that each inflated the score: a path
bug that hid half the true matches, location-only matching that credited a finding for
landing on the right line regardless of content, and gold that still contained
non-actionable comments. **Every loose metric flattered the agent**, without exception.

Findings sort into four verifiability tiers, and the tier predicts whether a model succeeds:

| tier | what it is | share | example | checked by |
|---|---|---:|---|---|
| V1 | decidable | 5% | "no new axioms" | grep for `axiom` |
| V2 | checkable by computation | **46%** | "this case should be `by simp_all`" | compile it — the kernel decides |
| V3 | codifiable convention | **41%** | "why not `injective_of_eq_imp_le`?" | naming rulebook plus judgment |
| V4 | genuine preference | 8% | "is this API really easier than `obtain`?" | maintainer discussion only |

92% are V1–V3. V2 is *many valid options, maintainer picks one*; V3 is *one right answer*.

Gold is grounded in revealed preference — `diff(first_pushed_head, merged_head)` is what
maintainers actually required, human-produced and model-independent, which breaks the
judge-grades-judge circularity.

**Outstanding**

- Recall is scored by an LLM judge. Spot-checked, with roughly 10–15% slack. Precision is
  kernel-anchored and does not have this problem.
- No inter-annotator ceiling. **Deferred by choice, not blocked**: recruited Mathlib
  annotators are off the table until the agent is mature enough that the comparison is
  worth their time.

---

## 4. Reviewer results, June 2026 — commits 25–27

**Status: measured once, single run and config. Treat as preliminary.**

Same 30–57 PRs, same task, tools vs prompting-only (gpt_5.4): prompting-only produced **69
findings**, the workspace-equipped agent **10** (~7×), at roughly half the precision. No
tools means ungrounded guesses — recall up, precision down; the workspace both grounds and
*suppresses* unverified findings.

Over 57 PRs / 115 findings:

| model · approach | findings | precision | recall all | rec V2 | rec V3 |
|---|---:|---:|---:|---:|---:|
| 5.4 holistic | 33 | **36%** | 10% | 4% | 15% |
| 5.4 guidelines | 31 | 29% | 9% | 4% | 11% |
| 5.4 decomposed (verified) | 125 | 13% | 11% | **14%** | 8% |
| 5.2 holistic | 168 | 24% | **31%** | 27% | 34% |
| 5.2 guidelines | 151 | 24% | 28% | 25% | 28% |
| 5.2 decomposed (verified) | 86 | 15% | 13% | 16% | 9% |

Four readings:

1. **Recall is low.** Predicting *which* improvements a maintainer wants is far from solved.
2. **Guidelines did not help**, for either model. It "knows" the rules and still cannot make
   the call.
3. **The model gap is a flagging *threshold*, not capability.** 5.4 under-flags, 5.2
   over-flags; they bracket the maintainer and neither is calibrated.
4. **Verification is a stable floor.** Checker recall barely moves across models (11→13%)
   while free-text recall swings (10→31%).

**Outstanding:** single run per condition; no multi-seed, no error bars, only two models.

---

## 5. The selection wall — commit 27

**Status: a real result, deliberately stated narrowly.**

`miss_decompose.py` asks, for each gold finding a run missed, whether the pool contained
*any* candidate at that line. It did, for **81%** of them. The agent generates something at
nearly every place a maintainer comments, then does not raise it. **The bottleneck is
selection, not generation.**

Selectors tried: diff-only, listwise over the full pool, and agentic with tools. All three
leave V2 at roughly chance.

**This is not "V2 targets are inseparable."** It is "the signals these selectors were given
do not separate them." Untried and plausible:

- **Centrality weighting** — rank candidates by centrality in the change graph
  (`centrality_probe.py` is the cheap no-API version; the weighted selector is unbuilt).
- **NL distillation** — select over distilled natural-language form rather than raw findings
  (`distillation_probe.py` exists; the selector on top of it does not).
- Precedent-conditioned selection, now that retrieval measures out (§6) and the Zulip store
  exists (§8). Nothing has tried ranking candidates by *how often this community has raised
  this concern before*.

---

## 6. Precedent retrieval — commit 28

**Status: Stage 1 complete, gate passed. Stage 2 wired into v5, not yet exercised on a paid run.**

Scored precedent-hit@k against 109 gold query sites.
`inputs/pr_review_v2/precedent_bench/report.json`: **STRONG GO at 0.615**.

The measurement overrode the design intuition. Dense code embeddings beat lexical+feature at
the k a live tool uses — hit@5 **49% vs 42%**, and on the V2 tier **56% vs 44%** — where
lexical+feature had been the proposal. The index is 34640×384, a ~5-minute one-off build.

One implementation note that is not a detail: **the eligibility filter must run before
ranking**, since filtering an already-ranked top-k silently returns fewer than k.

**Outstanding:** no measurement of whether retrieval changes reviewer *output*. The gate
measured retrieval quality, not downstream effect. That is a v5 run.

---

## 7. The v4 deterministic pipeline — commits 30–36

**Status: built, frozen, and bounded by a measured constraint.**

v4 replaced v3's interventions with sealed, hash-identified obligations under an immutability
discipline: data never moves, only code moves; `io.write_once` raises on content change;
`verify_frozen` re-hashes 1130 files against `inputs/pr_review_v4/FROZEN.lock`. Two sealing
conventions (`sealed_from_payload` vs `sealed_model`) are deliberately not interchangeable,
with a guard test keeping them apart. `judge_version` is in both the cache key and the task
record hash, so two rubrics can never join or resume into each other.

**The two arms are complementary, not competing.** On the development PR the fixed
deterministic pipeline and the call-matched holistic reviewer tie on mean issue recall (33.3%
each) while recovering **nearly disjoint** obligations — union ~6/8 on matched scope. The
deterministic arm wins precision (88.9% vs 61.7%), control safety (0 vs 2 false candidates
per repetition), cost (~35% cheaper), and reproducibility: identical accepted opportunities
in 3/3 repetitions, the only structurally reproducible result in this project's history. The
holistic arm wins breadth, and found a real docstring typo absent from gold in 3/3.

**The binding constraint is implementation reach, not method design.** The static coverage
census over the 16-PR medium benchmark scored all 40 evaluation-eligible obligations:

- **C0** (a scheduled investigation overlaps the code): **40/40**
- **C1** (a frozen method contract covers the ask): **15/40**
- **C2** (an executable implementation accepts the target shape): **5/40 — all five on the
  development PR, 0 of 26 elsewhere**

The pre-registered gate returned `static_reachability_rejected` and the paid medium run was
skipped at zero model cost. The cause is that operators are single-shape:
`operators/naming_contrast.py` hardcodes `SUBJECT = "Set.encard"` and requires a `card_`
prefix, so it cannot fire on PR 33337's `toLinearMap_` renames even though the naming
*method* covers them.

**Outstanding**

- **Generalizing the operators is not free.** The Step 5 equivalence replay found
  `opportunity_executor` reproduces the phase 3/4/5 *discovery* layer exactly — same
  opportunities, same `discovery_score` and rank, same canonical transformation, zero control
  candidates — but emits **weaker evidence prose**. Where the frozen text carries the
  quantitative warrant ("87/91 direct-subject declarations with an `encard_` prefix and no
  `card_` examples"; "the top retrieval (score 28)"), the executor asserts the conclusion
  without it. Those strings render into the adjudication prompt, and Phase 9's precision and
  stability were measured against the frozen prose. Full verdict:
  `results/pr_review_v4/audits/phase10-executor-equivalence-verdict.md`.
- **Do not archive `phase3/4/5_*_smoke.py`.** The equivalence gate failed, so they remain the
  authoritative producers of the frozen 0.9.1–0.9.3 releases Phase 9 consumes.
- **Medium is gated on R1b.** `dev-medium-0.3.0` gold is still 31/33 `migration_proposal`
  and 2 `curator_confirmed` (43 obligations), and is a one-shot census look.

---

## 8. The Zulip discussion store — commit 37

**Status: built and validated offline. Serves R5, which gates R6. Not yet consumed by a paid run.**

The blind spot it addresses: every other evidence source reads the repository — what Mathlib
already *does*. A convention is established on Zulip long before it is visible in the tree,
and the maintainer who would flag it is often the one establishing it. Two measurements:

- `grind` had **2 temporally-eligible mentions in the 8,161-event GitHub ledger** and **180
  Zulip topic titles**.
- `toLinearMap_` sits at 17% in-tree adoption while a maintainer is actively pushing it.
- 147 maintainer review comments cite a Zulip link directly.

Current build: **180,162 messages / 12,033 topics** since 2024-11-01 across 9 core streams,
from the `leanprover-community/archive` mirror pinned at `317d0b01` (121 streams / 60,758
topic files). Identity resolution covers all 59 v2-roster maintainers plus 4 who joined since.

Generation-neutral by design: nothing in `src/datasets/zulip/` imports `pr_review_v*`.

**Outstanding:** R5, the norm-coverage report, is unbuilt. It is what turns "`grind` has two
eligible mentions in the ledger" from a silent blocker into a publishable measurement, and it
gates R6.

---

## 9. The v5 delegating agent — commit 39

**Status: built 2026-08-24. 77 new tests. `verify_frozen` clean over 1130 files. NOTHING PAID HAS BEEN RUN.**

One lead agent per review episode, routing specialist arms over work units. Hybrid routing:
deterministic rules propose, the lead prunes, adds and budgets. The lead's authority is
**routing only** — its arbitration is recorded but not applied, so a routing result cannot be
confounded with an arbitration one.

The agenda enumerates the **full pool**, not just eligible pairs, and pre-renders every
prompt, which is what makes `fanout` / `rules` / `lead` send byte-identical text for the same
(arm, unit) pair. Retrieval cutoff is gold-free — the committer timestamp of
`reviewed_head_sha`, never `review_started_at`, which lives under `gold/`. Verified
conservative on all 16 medium episodes: 0 leaks, median 6.8 hours before review started.

Smoke set 33057 / 33066 / 33098 / 33438 plans at 94 proposals / 58 eligible; floor $1.74,
fanout $7.43, rules $4.58.

**Outstanding, and read these before any v5 number**

- The **generalist evidence gate is closed** — it admits `diagnostic` — until the evidence
  chain is wired into `finalize`.
- The **`routing_report` degenerate-check must be read first.** A lead that prunes nothing,
  or everything, produces a number that looks like a routing result and is not.
- The smoke set carries **only 1 eligible golf job and 1 idiom job**, because those PRs
  mostly *add* declarations while golf and idiom schedule on *modified* proofs. It is a
  genuine test of whether lead-*adds* help and a thin one for the golf arms.

---

## 10. Planned, not started

- **L0 — norm provisioning (`norms/`).** A dated store with
  `lifecycle ∈ {announced, emerging, contested, established, hardened}`, `as_of_date` and
  `evidence_refs`, mined from in-tree adoption trends, recency-weighted precedent, and dated
  repo artifacts (lint rules, `@[deprecated]`, style-guide diffs). The Phase 6 lesson is the
  design requirement: **the store must declare its own coverage** and emit
  `insufficient_evidence` below threshold rather than provisioning silently.
- **L1 — generalized checkers (`checkers/`).** Same purity contract as the operators — that
  property is what makes their output trustworthy — but with reach as an improvable quantity
  rather than a hardcoded shape. This is the direct answer to C2 5/40.
- **Calibration.** Move the flag/no-flag threshold to the maintainer's, *during* review
  rather than as a wasteful post-filter. This is the throughline's actual target: the models
  bracket the maintainer and neither is calibrated.
- **The thesis experiment itself.** `lean_reviewed_proof_engineering` (commit 24) is built
  and has pilot configs; the comparison against compile-only feedback has not been run.
- **Replication.** Multi-seed, more models, error bars on everything in §4.
- **Deferred by choice:** recruited Mathlib annotators and the inter-annotator ceiling — not
  until the agent is mature enough to be worth their time.

---

## Running it

```bash
pip install -e .
python -m pytest tests -q          # 767 pass, 11 fail, 4 skip on a fresh clone
```

The 11 failures all require a built Lean workspace under `data/code_execute/` — the
wrapper-composition, canonical-API and blueprint tests read the reviewed file at its base
commit. Build one and they pass; there is no way to version tens of gigabytes of compiled
Mathlib.

```bash
ape/bin/python -m src.datasets.pr_review_v4.verify_frozen verify
ape/bin/python -m src.datasets.pr_review_v5.runner --config configs/pr_review_v5.yaml --dry-run
ape/bin/python -m src.datasets.zulip.browse --stats
ape task ape-agent lean_pr_review          # interactive single-task session
```

All tooling must run from the repository root (`paths.assert_repo_root`).

## What is not in this branch

| Excluded | Size | Rebuild with |
|---|---|---|
| `inputs/pr_review_v2/corpus/` | 100 MB | `-m src.datasets.pr_review_v2.corpus` |
| `inputs/pr_review_v2/precedent_bench/*.jsonl` | ~40 MB | `-m src.datasets.pr_review_v2.precedent_bench` (reports are tracked) |
| `results/*/runs/`, `results/blueprints/` | ~115 MB | re-run the condition, or `-m src.datasets.pr_review_v4.blueprint` |
| `data/pr_review_v2/cache/{matcher,precedent_judge,concern_classify,selector,…}` | ~25 MB | regenerated on demand; costs model calls |
| `data/code_execute/`, `data/lean_retrieve/` | tens of GB | `-m ape.toolkits.execute.lean.build`, `-m ape.toolkits.retrieve.lean.build` |
| ~29 superseded v2 run configs | 60 KB | named in `docs/research/progress-report-2026-06.md` |

The frozen v4 benchmark, the derived v2 gold, the cached GitHub bundles and every summary
report **are** tracked. The whole repository packs to about 16 MiB.
