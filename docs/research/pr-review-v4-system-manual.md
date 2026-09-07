# The PR-review v4 system, end to end: a design manual

*A self-contained walkthrough of every layer of the system — how Mathlib review data is
represented, how the reviewing task is posed to a model, how outputs are scored, and exactly what
a final evaluation number means. Each design decision is motivated by a concrete example or a
measured statistic, most of them failures of our own earlier designs. Written 2026-07-18;
normative specs live in the other `pr-review-v4-*.md` docs, code in `src/mathlib_review/`.*

---

## 0. What we are measuring, in one paragraph

Formal verification tells you a Lean proof is *correct*. It does not tell you whether Mathlib
would *accept* it: maintainers routinely require renames, deduplication against existing API,
proof golf, docstrings, generalization, and placement changes before merging code that already
compiles. This project benchmarks whether an AI reviewer can predict those demands. The ground
truth is what maintainers of real merged PRs actually asked for; the headline number is: **of the
atomic, evaluation-eligible maintainer obligations, what fraction did the system's review
candidates semantically identify (issue recall) and correctly resolve (resolution recall),
measured over three repetitions, alongside its false-finding rate on control PRs where
maintainers asked for nothing.** Every layer below exists to make that sentence precise,
leak-free, and reproducible.

---

## 1. Representing what happened: from GitHub to gold

### 1.1 The raw event ledger

Everything starts from an immutable, content-addressed ledger of raw GitHub/git objects — PRs,
commits, reviews, review comments, timelines, files, checks (~8,161 events for the current
corpus). Nothing downstream may invent facts not derivable from it.

*Motivation:* provenance failures cost us real conclusions before. In the v3 era, an evaluation
silently mixed two gold versions (the "v4-vs-v5 confound"), and a separate incident revealed
metric reports carried no provenance at all. v4 therefore content-hashes every artifact
(`source_sha256` on every record), writes releases with `write_once` (regenerating an artifact
with different bytes raises), and stamps every report with the hashes of its inputs.

### 1.2 Review episodes: the temporal cut that everything depends on

A **review episode** is one review round of one PR, split into two halves:

- the **visible half** (`ReviewEpisodeInput`): what the reviewer could see *before* giving
  feedback — base commit, reviewed head commit, the diff between them, title, description;
- the **hidden half** (`ReviewEpisodeBoundary`): the feedback events themselves and everything
  after — reviewer comments, the author's next push.

Only the visible half may ever reach a system under test. The benchmark currently uses round 1
episodes: review the PR as first submitted.

*Motivation — the leak postmortem.* The single most damaging bug of the project's v3 era: task
worklists were accidentally built from the PR's **post-review revision delta**, so the model's
checklist literally contained the author's eventual fix (on PR 33065 the checklist held both the
old and the corrected name). Location scores hit 99% and were meaningless. The episode split
makes this class of bug structural rather than a matter of care: the generation side receives an
object that *does not contain* the future. A standing test suite additionally poisons gold and
asserts every generation artifact is byte-identical (§2.4).

### 1.3 The change graph: stable, typed units of changed code

The episode diff is parsed into a **change graph**: a set of typed **change targets** — one per
changed declaration, import block, module doc, namespace, or non-Lean file — each carrying its
complete base code and reviewed code (never fragments), parse status, line ranges, and a stable
content-addressed `change_id`. Medium-tier scale: 16 PRs, 14 distinct base snapshots, and PR
sizes from 1 to 51 targets (PR 33294 alone has 51 — the size-stress case).

*Motivation:* `change_id`s are the **anchor currency** of the whole system. Gold obligations,
model candidates, scheduled investigations, and metrics all reference them, which is what lets us
say precisely "this candidate and this obligation concern the same code" (a *location* fact)
before asking the much harder question of whether they say the same thing (a *semantic* fact).
Conflating those two was a recurring early failure: co-location scores always look flattering
(§3.1).

### 1.4 The judgment graph: gold as atomic obligations

Raw maintainer feedback is conversational: one comment bundles several asks, threads say "same
here", asks get partially adopted. Gold is therefore built in stages:

- **Interventions** group the review events expressing one maintainer judgment.
- A **judgment node** captures its action (kind + object), speech act (request / suggestion /
  question / …), blocking force (blocking / advisory), and concern labels (naming, style,
  duplication, docs, correctness, scope, proof-golf, generalization).
- Each judgment decomposes into **atomic obligations**: single-checkable asks, each with a
  `claim`, explicit `resolution_criteria`, and anchoring `change_ids`.

*Motivating example.* On PR 33098 one maintainer comment produced a judgment labeled **style**
whose obligations include *"Rename the maximal-separated-set cardinality lemma with an `encard_`
prefix"* (a naming ask) and *"Simplify the cardinality proof with the requested grind-based
treatment"* (proof golf). Scored at comment granularity, a system that did the rename but missed
the golf would be un-scoreable; the concern label alone would even misclassify the rename. Atomic
obligations are the unit at which recall is honest. Medium currently has 33 judgments → 43
obligations; per-obligation issue classes: 13 proof-simplification, 8 naming, 7 duplication,
5 style-norm, 3 docs, 2 correctness, 1 scope, 1 generalization.

Two guarded workflows keep gold quality explicit rather than assumed:

- **Atomicity review**: judgments flagged `needs_decomposition` must receive a curator decision
  (`accept_atomic` / `split`), and the release builder hard-fails unless the decision set equals
  the flagged set exactly — no judgment can silently skip review.
- **Provenance statuses**: every judgment carries `migration_proposal` → `curator_confirmed` →
  `human_confirmed` (or `rejected`), so any number can be qualified by how much of its gold has
  had human eyes.

Separately, **outcome observations** record what actually happened to each ask (adopted /
partially adopted / contested / dropped / unknown). This matters because maintainer asks are not
all satisfied: mechanical cross-checking showed ~23% of judgeable asks were genuinely dropped by
authors — real review economics, and later a calibration target for "worthiness" policies.

### 1.5 Evaluation views: the denominator, made explicit

Not every obligation is fairly scoreable. **Intervention views** aggregate obligations and assign
an eligibility: `included`, `excluded_not_judgeable` (e.g. asks about PR process), or
`unresolved_scope` (anchoring still ambiguous). Only `included` obligations enter any denominator.
Medium: 30 included views → **40 included obligations** (of 43); the 3 exclusions are reported,
never silently dropped.

### 1.6 Controls: the license to trust recall

Every benchmark tier includes **control PRs** — substantive merged PRs where maintainers made no
intervention (medium has 3 alongside 13 intervention PRs). A system that floods plausible-sounding
requests can score recall without being a good reviewer; the **control false-finding rate** is
the counterweight, and it has caught real behavior: in the 0.9.0 baseline replication, one of
three repetitions published a confident naming finding on a control PR.

---

## 2. Representing the reviewing task

### 2.1 Work units

A model is not shown a whole PR at once. The change graph is packed into **work units**: groups
of same-file targets, complete targets only (a target is never split or truncated; content cap
24k chars per unit). Medium = **225 work units** across its 16 PRs. Every metric that follows can
be traced to the exact prompt bytes of the unit that produced each candidate.

### 2.2 The rendered prompt

One production renderer (`candidate-prompt/11`) serves previews and execution — what you inspect
is byte-for-byte what runs. The prompt contains:

- **Role and register**: "Act as a Mathlib maintainer… Predict concrete changes a maintainer
  would plausibly request, not general risks, questions, defenses of the code." **No quota:
  an empty candidate list is valid.**
- **The 8-facet checklist** (proof-golf, generalization, duplication, naming, documentation,
  style, scope, correctness), applied to every target.
- **Synthetic exemplars** of weak-observation vs maintainer-request phrasing, marked as teaching
  register only.
- The complete reviewed code of each target with its `change_id`s and subjects to copy exactly.

*Motivations, each from a measured failure:*

- *No quota* — v3's forced-findings arm bought +27pp recall at the price of filler and a
  precision collapse; volume must be a free variable the system owns.
- *All facets for every target* — failure analysis of 33 identified-but-unmatched interventions
  showed **73% were concern-delivery misses**: the right site was examined under the wrong
  concerns when a retrieval step chose which facets to mention. Delivering the full battery
  removed that channel.
- *Register exemplars* — a divergent-judgment audit found model comments are *generic* while
  maintainer comments are *indexical* (they point into local conventions and the library);
  exemplars teach the form "name the defect, request one checkable end state".

### 2.3 Verification tools

Runs may expose Lean tooling (`lean_verify`, goal inspection, hover/goto/references) against the
frozen base snapshot, so a candidate proposing an edit can carry a *compiled* replacement rather
than a hope. This is review-time-safe: the workspace is the base commit, not the future.

### 2.4 The isolation invariant

Invariant #1 of the codebase: **poisoning gold must leave every generation artifact
byte-identical.** It is enforced by tests that corrupt gold inputs and hash-compare episodes,
work units, prompts, schedules, and capability assessments. Evaluation-side artifacts (anything
that reads judgments) live under `results/pr_review_v4/audits/` and are prohibited from prompts
and execution releases. This is the structural answer to §1.2's postmortem.

### 2.5 Candidates: typed claims, not free text

A system's output is a list of **candidate claims**, each typed: primary change/subject (copied
IDs), `claim` (a *present* problem), `requested_change` (an imperative transformation),
concern family, severity, optional `proposed_edit` (a complete replacement declaration), optional
confidence. Defenses of the code, questions, and "worth checking" notes are excluded by contract
— and scored false by the judge if they leak through (a lesson from v3, where "disbelief needs
its own channel": rubber-stamp agreement and hedged risk-notes both masqueraded as findings).

### 2.6 Evidence and selection

Downstream of generation, candidates can gather **evidence** (compile results, searches, policy
text — typed artifacts with polarity), get bundled into **packets** (supported / contradicted /
inconclusive), and pass a **selection** step that publishes ranked **findings**. This separates
three questions that were once conflated: what the model can surface (candidate recall), what
survives verification, and what a user would actually be shown (published precision, volume).

---

## 3. Evaluation: what a number is

### 3.1 Two layers, never conflated

**Layer 1 — location.** A candidate *covers* an obligation if their `change_id` sets intersect.
The funnel report labels this explicitly: *"Change-scope hits measure location recall, not
semantic issue/resolution correctness."* Location is cheap and flattering — in the v3-era
diagnostics ~81% of gold sites had *some* prediction at the same location — so it is only a
funnel stage, never a headline.

**Layer 2 — semantics.** Every location-paired (candidate, obligation) pair goes to a cached LLM
judge (`v4-semantic-v1-v7.1-rubric`) with two strictly ordered verdicts:

- `issue_match` — true only if the candidate asserts *the same specific problem or code aspect
  the maintainer said must change*. Same declaration, same concern family, or nearby line is not
  enough; a different binder/tactic/name is false; defenses, questions, and no-change conclusions
  are false. A **different fix** for the same problem may still issue-match.
- `resolution_match` — true only if issue_match holds *and* the candidate's concrete
  transformation achieves the maintainer's requested result (enforced `resolution ⇒ issue` in
  parsing).

The rubric's sharp edges each close a measured hole: v7's audit found "defend-the-code" findings
issue-matching until the no-change clause was added; the two-level split exists because
identifying a problem and fixing it as requested diverge widely (in Phase 9: issue 33.3% vs
resolution 25.0% for the fixed arm).

*Known noise floor:* the judge itself is a variance source. On byte-identical wrapper-edit
artifacts across three repetitions, it issue-matched 2/3 — at n=8 denominators one judge flip is
~4pp of recall. Reports therefore carry per-obligation hit frequencies and judge-disagreement
counts, and identical artifacts are keyed by content hash so disagreement is measurable.

### 3.2 The metrics

Over the included, atomic obligations in scope:

| Metric | Definition |
| --- | --- |
| **Issue recall** | fraction of obligations with ≥1 issue-matched candidate |
| **Resolution recall** | fraction with ≥1 resolution-matched candidate |
| **Paired precision** | fraction of location-paired candidates that issue-match |
| **Control false-finding rate** | fraction of control PRs where any finding was published |
| Full-intervention recall | fraction of views with *all* their obligations hit |
| Location recall | funnel diagnostics only |

### 3.3 The three-repetition protocol

No single-run number is quotable. The motivating measurement: the 0.9.0 baseline, run three times
identically, scored **3/6 → 2/6 → 1/6** obligations (union 4/6, stable-across-reps 0/6). At these
denominators single runs are noise; earlier still, four full-corpus checker runs (13, 13, 19, 12
covered) all sat in one ±6 noise band while we narrated differences between them. The standing
protocol: **3 repetitions per condition; report mean, union, and stable (≥2/3); evaluate each
repetition separately before aggregating.** The union-vs-mean gap is itself diagnostic — 0.9.0's
union 4/6 against per-run ~2/6 said capability was present but under-sampled per run, which is
what motivated the systematic treatment (§5.2).

### 3.4 Caveats attached to every number

- **Gold is a lower bound on review quality.** The holistic arm found a real `extenal` docstring
  typo in 3/3 repetitions — absent from gold because no maintainer mentioned it. Unpaired
  candidates are therefore "not matched", never "false"; they get a manual audit lane.
- **Per-PR reporting is mandatory.** PR 33098 contributes 14 of medium's 40 obligations; pooled
  numbers alone would let one PR drive conclusions.
- **Contamination is tiered, not denied** — see §4.

---

## 4. Benchmark tiers and look budgets

All development so far has touched the same 57-PR corpus, so contamination is managed by
rationing *looks*, not by pretending it away:

| Tier | PRs | Role | Look budget |
| --- | --- | --- | --- |
| small | 3 (33057, 33098 + control 33438) | plumbing smokes, operator iteration | unlimited |
| medium | 16 (13 gold + 3 control; 225 work units, 40 obligations, all 8 concern families) | pre-registered treatment comparisons, method census | pre-registered runs only |
| large | 57 | confirmation at scale | ≤3 uses over the project's lifetime; report the ~44-PR unseen slice separately |
| temporal holdout | frozen, future window | the only source of generalization claims | untouched |

Medium's seven additions beyond the pilot were chosen to repair family gaps — the pilot's gold
had **zero** correctness, **zero** scope, and one naming intervention; medium adds the only
correctness-rich PR (33149), the cleanest scope case (33362), non-motivating naming cases
(33337, 33294), a docs/dropped-heavy PR (33321), a multi-anchor duplication family (33145), and
proof-golf outside the dev PR (33285). This composition is what makes the census of §6 meaningful.

---

## 5. Treatments: two ways to produce candidates

### 5.1 The holistic baseline

Run the §2 prompt over every work unit; optionally 3 repetitions and a union. This is the
comparator every structured treatment must beat *per call*: comparisons are labeled call-matched
(same number of generator calls), never falsely "cost-matched".

### 5.2 The systematic opportunity pipeline

*Motivation.* The 0.9.0 result said the model *can* surface most of what maintainers asked
(union 4/6) but any single run samples a small, random subset (per-run ~2/6, stable 0/6), with
occasional control false-positives. That is a coverage/consistency problem, not a capability
problem — so the treatment replaces "hope the model looks everywhere" with scheduled,
deterministic search:

1. **Methods** — a hash-sealed registry of four research strategies (baseline failure, canonical
   API search, wrapper composition, naming contrast), each with typed applicability facets,
   required inputs, operators, and a selection policy. Registry entries are validated to contain
   no gold vocabulary.
2. **Scheduler** — every applicable (method × changed target) pair becomes an investigation task;
   a validator requires the schedule to equal the applicable set *exactly* (nothing dropped,
   nothing extra). Medium: **1,177 tasks** (442 baseline-failure, 250 canonical-API, 273 wrapper,
   212 naming).
3. **Operators** — deterministic discovery: repository-index retrieval, naming-population scans
   over the frozen snapshot, template matching, composition search. Their output is
   **opportunities** with evidence artifacts; "checked, found nothing" is recorded, not lost.
4. **Adjudication and worthiness** — only opportunities needing judgment consume model calls
   (redundancy-gated); a deterministic policy layer decides publishability, with request force
   kept separate from technical validity.
5. **Synthesis/selection** — findings with full lineage back to opportunity, evidence, and
   investigation.

Evidence that the architecture works, from its integrated smoke (Phase 9, dev PR + control,
3 reps/arm): identical accepted opportunities in all repetitions (first structurally reproducible
result of the project), paired precision 88.9% vs the baseline's 61.7%, resolution recall 25.0%
vs 16.7%, issue recall tied at 33.3%, **zero** control candidates vs 2 per baseline rep, ~35%
cheaper. And the same smoke measured the wall: across the dev PR's 14 eligible obligations, 10
never received an opportunity — the methods' reach, not their judgment, is the binding
constraint. Which raises the question §6 answers.

---

## 6. Does the frozen treatment reach the benchmark? The coverage census

### 6.1 Methods are not implementations

The registry's seven *methods* are honest strategies; the *executable code* is far narrower —
each operator currently fires on essentially one shape:

| Implementation (own frozen identity) | Executable scope |
| --- | --- |
| `naming_contrast.encard_subject_prefix.v1` | `Set.encard` direct-LHS conclusions, `card_`→`encard_` only |
| `naming_norm.subject_prefix.v1` | *any* subject inferable from the conclusion, against a norm mined from the snapshot |
| `canonical_api.insert_separation.v1` | one inserted-set `IsSeparated` proof template |
| `wrapper_composition.packing_cover_chain.v1` | the `coveringNumber ≤ packingNumber` goal with 3 in-PR witnesses |
| `lint_norm.text_style.v1` | Mathlib's text-based style lints, reimplemented (18 rules, Mathlib's own ERR codes) |
| `repository_policy.forbidden_construct.v1` | an `axiom` or `sorry` the PR *introduces* |
| `baseline_failure.target_compile.v1` | any Lean target (compile attempt) |

As of registry `/3` the first two overlap: `naming_norm` reaches everything
`naming_contrast` does, and is kept alongside it only because Phase 9's frozen results
depend on the narrower one.

Medium has 8 naming obligations; PR 33337's are `toLinearMap_` renames — covered by the naming
*method*, unreachable by the `encard`-only *implementation*. A census at method granularity would
call that "covered" and authorize a paid run whose outcome is already decided. So implementations
get their own hash-sealed identities and their own deterministic **capability predicates**
(reusing the operators' own matching code), producing one verdict per (task, implementation):
medium = 2,253 assessments — 533 supported, 1,720 unsupported-shape, **0 failed** — where negative
verdicts are first-class evidence. (Registry `/1` produced 1,177; the growth is new
implementations, not new tasks.)

### 6.2 The C0–C6 ladder

Each included obligation is scored on a monotone ladder; each level isolates a failure with a
different remedy:

| Level | Question | Medium (static) | Gap means |
| --- | --- | --- | --- |
| C0 | any investigation overlaps its code? | 40/40 | scheduling bug |
| C1 | a frozen method contract covers the ask? | 20/40 (+21 pending audit) | design a new method |
| C2 | an implementation accepts the shape? | **13/40** (was 5/40 at registry `/1`) | generalize operators |
| C3–C6 | source found / edit built / issue matched / resolution matched | needs execution | retrieval, construction, judging |

C1 deserves its own note because it is the one judgment-laden layer. Concern labels are too
coarse (§1.4's naming-inside-style example), so two frozen prose classifiers annotate each
obligation — its issue class and its **requested transformation** class — and C1 holds only when
a contract covers the *pair*. The conjunctive rule exists because the v1 protocol let every
proof-golf ask count as expressible by the API-replacement method (C1 read 28/40; v2 reads 15/40
with 21 abstentions routed to a human-audit queue rather than counted). The reachability decision
deliberately does not rest on C1 at all — it rests on C2, which is mechanical.

### 6.3 The reachability gate and the current result

A paid medium run of a frozen arm is authorized only if the static census shows ≥3 C2-supported
obligations outside the dev PR, across ≥2 PRs, via ≥2 implementations — necessary consequences of
the expansion claim the run would exist to test. Rejection is asymmetric: low C2 kills a paid
run; high C2 only authorizes testing (it proves nothing about C3–C6).

**First result (2026-07-18, registry `/1`):** C2 outside the dev PR = **0/26** →
`static_reachability_rejected`. The five supported obligations were exactly the operators'
motivating cases. The paid smoke was skipped; the census cost zero model calls and saved one of
medium's rationed pre-registered runs.

**Current result (2026-08-06, registry `/3`):** C2 outside the dev PR = **8/26**, across 6 PRs
via 3 implementations → `authorized_for_paid_smoke`. All three gate conditions pass.

**But the gate's own metric has since been shown to be non-uniform, and this is the most
important caveat in this section.** A capability predicate answers "is this shape in scope?",
which for the near-exact predicates (`lint_norm`, `repository_policy`, `canonical_api`) is
nearly the same question as "is this a finding?" — but for `naming_norm` it is not.
`naming_norm` cannot decide whether the corpus *has* a convention for a subject without the
snapshot population scan, which is far too expensive for gold-free assessment, so its
predicate accepts the shape and defers the real decision to execution. The first full
deterministic execution over medium (`audits/phase10-medium-executor-v3.2/`) measured the
difference: **8 C2 obligations outside the dev PR, 2 actual opportunities.**

Two consequences carried forward:

- **C2 counts are comparable within an implementation across registry versions, not across
  implementations.** Quote reach from execution, not from the census.
- **Control safety must be measured at the runner, not at the census.** `naming_norm` is
  `supported` on two targets in control PR 33438; its norm-strength filter rejects both, and
  the executed arm emits zero opportunities on all three control PRs. The earlier claim of
  zero control firings was an assessment-layer measurement that happened to agree with the
  runner, and no longer does.

The repair is a precomputed per-snapshot subject-norm index carried as a release artifact,
which would let the predicate ask the real question cheaply and gold-free, restoring one
meaning to C2. It has not been built.

---

## 7. Worked example: reading "issue recall 33.3%"

Take the Phase 9 headline — *"fixed pipeline: mean issue recall 33.3%."* Unpacked, back through
the layers:

1. **Scope** (§1.5, §4): PR 33098's included views yield 14 eligible atomic obligations; 8 are
   in the matched evaluation scope for this comparison. The denominator is 8.
2. **Generation** (§2, §5.2): the treatment produced 3 candidates per repetition, each a typed
   claim anchored to `change_id`s, generated with zero gold access (§2.4).
3. **Pairing** (§3.1): candidates pair with obligations only on change-ID overlap; each pair is
   judged for `issue_match` under the strict rubric; verdicts are cached by content hash.
4. **Per repetition**: count obligations with ≥1 issue-matched candidate → 8ths.
5. **Aggregation** (§3.3): three repetitions, evaluated separately, then averaged → 33.3% mean;
   reported beside union, stable-count, per-obligation frequencies, and judge disagreement.
6. **Counterweights**: paired precision (88.9%), resolution recall (25.0%), control PR
   candidates (0 in all reps), cost ($0.149/rep), and the stage ledger attributing all 10
   unrecovered obligations to source-retrieval.

And what it does **not** mean: not "the system finds a third of review problems" (gold is a
lower bound, §3.4; the PR is development-contaminated, §4; the denominator is one PR's matched
scope, §3.4). The number is a controlled comparison against a call-matched baseline on frozen
gold — nothing more, and, because of the layers above, nothing less.

---

## 8. Where things stand

- **Built and frozen**: raw→episode→change-graph→judgment-graph→views pipeline; medium release
  `dev-medium-0.1.0` (16 PRs / 225 work units / 40 included obligations); holistic runner and
  prompts; semantic judge; systematic operators + Phase 9 fixed orchestration; implementation
  registry, capability assessments, static census (`static_reachability_rejected`).
- **Open, in order**: the 40-row C1 human audit; generic executor + terminal ledger + index
  cache + Phase 9 replay + deterministic medium dry run (Steps 5–9 of the Phase 10 design);
  generalized implementations under new registry versions; style/docs/correctness method design
  (the 12 obligations no method expresses); norm-maturity/knowledge-frontier track (evolving
  norms like `grind` are invisible to any historical corpus — separate design brainstorm);
  temporal holdout, last.

## 9. File map

| Layer | Code | Frozen artifacts |
| --- | --- | --- |
| Episodes, change graphs | `episodes.py`, `episode_builder.py`, `change_graph.py` | `inputs/pr_review_v4/releases/*/input/`, `derived/change_graphs.jsonl` |
| Gold | `judgment_graph.py`, `stabilize_judgments.py`, `migrate_interventions.py` | `releases/*/gold/{judgments,intervention_views,outcome_observations}.jsonl` |
| Task | `work_units.py`, `render_prompts.py`, `task_adapter.py`, `runner.py` | `derived/{work_units,rendered_prompts}.jsonl` |
| Candidates/evidence/selection | `candidates.py`, `evidence.py`, `select.py` | run dirs under `results/pr_review_v4/runs/` |
| Evaluation | `evaluate.py`, `semantic_judge.py` | `results/pr_review_v4/audits/` |
| Systematic treatment | `method_registry.py`, `investigations.py`, `operators/`, `phase7_adjudication.py`, `synthesis.py` | `inputs/pr_review_v4/treatments/` |
| Census (Phase 10) | `implementation_registry.py`, `method_coverage_census.py`, `phase10_medium.py` | `treatments/systematic-opportunities-v1-medium-c1v2/`, `audits/phase10-medium-static-census-c1v2/` |
| Tiers | — | `inputs/pr_review_v4/benchmarks/tiers-v1.json` |
