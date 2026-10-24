# Reusable review knowledge: the next transfer experiment

**Status: draft for iteration, 2026-10-24.** This plans the next experiment; it does not launch
acquisition, reviews or judging. Model-backed work remains user-run. The first implementation
deliverable is the bounded source/target selection and a costed Task recipe, not a full campaign.

This follows the [historical synthesis](../research/knowledge-transfer-experiment-synthesis-2026-10-23.md)
and [latest pilot assessment](../research/review-knowledge-transfer-pilot-assessment-2026-10-23.md).
It replaces the earlier conditional-preparation method as the candidate for the next experiment;
the [October 23 plan](2026-10-23-review-knowledge-transfer.md) and its results remain historical.

## 1. The question and the research decision

**Can knowledge acquired from independent earlier decisions improve ordinary whole-PR review
beyond the existing terse convention entries, while distinguishing when the same tempting
revision should be declined?**

The candidate intervention is a reusable resource, acquired before reviewing the targets. Its
entries explain the choice, applicability, competing reasons and useful checks. One shared
procedure acquires the entries; ordinary review consumes them. The reviewer is free to disagree,
investigate or remain silent. A new concern should require source data, not new runtime code.

The intended mechanism is specific: a better account of a distinction changes the comparison
at a relevant object, and that changes a delivered request appropriately. More citations, a
complete ledger, or more checks without better review do not establish success.

This is a development experiment. It can justify a later fresh transfer test or stop investment
in this representation. It cannot establish corpus-wide effectiveness, automatic convention
discovery, retrieval over hundreds of entries, or the superiority of a particular prose format.
Acquisition involves curated source packets; model weights remain fixed.

## 2. Already answered?

Read [questions](../questions.md), [dead ends](../dead-ends.md), and the linked synthesis before
implementing. The probe's eventual `PROTOCOL.md` must carry this comparison too.

| Earlier experiment | What it answers | What this experiment changes |
|---|---|---|
| Guidelines and July precedent priming | General rules and similar comments can arrive without a reliable reviewing gain. | Acquire conditional distinctions from independent cases, then compare final reviewing behavior. |
| Exact-convention ceilings and GPT stage W | Supplied applicable conventions and some decision instructions can substantially help. | Supply no target-specific applicability judgment or location; keep the review contract fixed. |
| F/G/AP ask-free delivery | Lists, pinpointing and examples/precedence did not reliably generalize. | Compare acquired knowledge against the same small bank's original terse entries, as well as solo review. |
| Oracle ladder | A sentence already recovers most possible changes at the known place; examples sometimes hurt. | No gold location, no assertion of applicability, whole-PR final output, and independently checked scope/correspondence. |
| Stage H and the places test | Example-based demand prediction and exhaustive application have discrimination/burden limits. | Use genuine contrary decisions or established technical consequences; silence is not a negative label. |
| October 16 departure readings | Some rules and detectors misstated the convention; primed naming remained unstable. | Check the acquired distinctions against reserved source cases; uncertain knowledge can remain uncertain or fail. |
| Reconstruction and source-supply diagnostics | Sources can improve consideration without reliably improving requests. | Test reuse across target PRs, rather than another known-site demonstration. |
| October 23 preparation pilot | Conditional investigation did not improve historical recovery over ordinary extra preparation. | No preparer per target; the treatment is a frozen reusable resource, and a solo arm is included. |

The dossier line was previously narrowed/closed as a recall lever. This is a bounded reopening
because the later construct corrections identify actual content/scope errors and source-derived
dossiers were not built. An unchanged sentence with decorative examples does not qualify as the
new intervention. The reopening is a hypothesis, not evidence that a richer resource will work.

## 3. Fixed design

| Item | Default |
|---|---|
| Knowledge scope | Six entries across three concern families; one bank shared by every target |
| Development targets | Six already-used PRs: two per family |
| Source separation | All targets excluded from acquisition; one common knowledge cutoff before every target |
| Arms | A: solo; B: original terse entries; C: acquired conditional entries |
| Reviewer | Opus 5.5, xhigh, current contained Claude Code route |
| Runtime | The same ordinary contract-2 reviewer, tools, pass-0 inputs and limits in all arms |
| Replications | Three independent final reviews per PR and arm: **54 final-review sessions** |
| Outputs scored | Canonical finalized findings; submissions and notes explain losses only |
| Primary quality evidence | Blinded project adjudication of correctness and request value |
| Separate reference measure | Canonical raw-ask matching, one measurement plan across all arms |

The synthesis proposed two repetitions/36 reviews. This plan uses three, following `CLAUDE.md`'s
reporting rule and the instability in prior runs. The added repetitions are included in the
allocation below. No further replication, second model or fresh PR tranche is automatic.

## 4. Step A: select the entries, targets and source cases together

This is a bounded data-selection task, using existing results rather than another corpus census.
Start from documented failures and the 19 `library_partial` cases in
`results/pr_review_v5/probes/library-knowledge-2026-10-13/asks.jsonl`.

Prefer three different types of decision:

1. **Scope/precedence:** namespace or naming choices where a superficial analogue can mislead.
2. **Automation/mechanism:** registration, tactic or mechanism choices with relevant operational
   consequences. The familiar aesop case may illustrate development; it does not earn another
   standalone source-supply campaign.
3. **Statement/API design:** assumptions, generality, formulation or a related API choice.

Choose two existing census entries per family, with at least one entry outside the top fifty
by the frozen census frequency. Record the ranks; this is a small breadth check, not a population
coverage estimate. Do not fill all three families with versions of wrapper removal/generation.
PRs 33066 and 33117 remain fixtures, not default targets for another campaign.

For each family select one previously observed review opportunity and one target with a
competing reason/form that tests overapplication. Known misses may inform development selection.
The target reviewer receives neither that designation nor a list of expected findings. A
contrary target requires an explicitly supported reason to retain the form, or project
adjudication of that choice; merely merging without a comment is insufficient. Target feedback
belongs to evaluation files, outside every model-visible acquisition/review packet.

Record all candidates considered and the reason for inclusion/exclusion. Freeze the six targets
before model acquisition; do not replace one because the acquired entry predicts its answer
poorly. Preserve AI-origin evidence and include such PRs when eligible; do not filter them out.

**Deliverable:** `selection.json` and `SELECTION.md`, containing exact PRs, episodes, release roots,
reviewed-head timestamps, base/reviewed SHAs, family assignments, existing run references,
census IDs/ranks, codebook revision, AI labels and source-case assignments. The acquisition
writer's packet omits target identities, expected answers and previous target trajectories.

Spend at most one working session on this assembly, initially about half a day. Failure to find
an adequately sourced three-family comparison is a useful result. Record the missing evidence
and stop or revise the design; do not silently turn this into an unbounded discovery project.
The exact IDs are intentionally an implementation deliverable, not invented in this plan.

## 5. Source eligibility and the terse comparator

Resolve each target's ordinary episode cutoff from its reviewed head. Choose a common cutoff
`K` no later than the earliest of those cutoffs. All knowledge evidence, including the full
discussion context used to interpret a decision, must have been available **strictly before K**.
Record `K` as an exact UTC timestamp. The target code still comes from each target's normal view.

Exclude all six target PRs, their reviews, later changes, and material elsewhere that reveals
their outcomes from acquisition sources. Exclude reserved validation cases from induction.
Broader project assessments and the historical synthesis can guide the researcher, but must not
enter a writer's packet: they contain the answers we are trying to transfer without.

**Arm B needs the same audit.** Use the original census sentence verbatim, but inspect its source
assignments: no target or reserved validation case may have contributed to it, and no supporting
case may postdate `K`. Check rationale/examples if they helped derive the sentence, not just the
one example shown at runtime. A codebook written now is not automatically pre-target knowledge.
Record source ancestry and any uncertainty. Prefer another eligible entry if this check fails;
do not silently rewrite B, call it the old baseline, and attribute C's gain to richer knowledge.

Use small source packets built from existing corpus readers: comments/discussion, relevant
before/after code, and dated library evidence. For each entry seek two independent source PRs;
include up to four cases where useful. Reserve two additional cases per family, one favorable
and one contrary, for the check in step C. These are practical bounds, not evidence-count
thresholds that establish a convention. Record author/scope concentration and thin evidence.

A contrary example is an explicit reason to retain a form, or a concrete, verified consequence
that defeats the tempting revision. Identify which kind it is. An inferred tradeoff may guide
investigation but must not be relabeled as a maintainer's stated preference.

Both bank variants must be portable to all six targets without per-target edits or references.
If that is impossible under one cutoff, revise selection before model work. Do not supply
different knowledge under the same condition label.

## 6. Step B: acquire six reusable entries through one Task recipe

Use `PacketSessionTask` with the shared source-study brief, one independent packet per entry,
one acquisition sample each. The model can read only its supplied source files and ordinary
instructions. A folder packet is sufficient: no live retrieval, target workspace or new task
hierarchy is needed to write the entry. Source collection and any local technical checks precede
the packet and retain their exact results.

The brief asks the writer to:

1. Recover the actual choice and the reason each source supports; inspect the associated code.
2. Explain what distinguishes the alternatives: semantic roles, scope, precedence, consequences
   or uncertainty. A citation alone is insufficient.
3. Seek contrary evidence in the packet and identify where a generalization would fail.
4. State what a reviewer should inspect or try to resolve a new occurrence. Use existing tools;
   do not invent an executable checker per convention.
5. Retain uncertainty when the sources do not determine a boundary. Do not manufacture an
   authoritative rule to make the resource look complete.

Each entry declares `entry.md` and `sources.json` as its outputs. The document contains:

| Content | Requirement |
|---|---|
| Choice | The alternatives and their roles, in language transferable beyond a source identifier |
| Conditions | Evidence favoring each form; scope, precedence and unresolved cases |
| Evidence | Short code/discussion excerpts with source IDs, dates and the relationship they establish |
| Application | What to inspect or test, and what result would defeat a proposed revision |
| Status | Distinguish stated reasons, observed consequences and inferred explanations |

Cap the runtime document at 500 words per entry, including excerpts: at most 3,000 words for
the six-entry bank. Keep fuller source material as acquisition evidence, not extra runtime
context. Check word counts locally. `sources.json` identifies the actual inputs supporting each
material claim; it is study data, not a new provenance subsystem. Verify citations and directional
correspondences against those inputs. Tool/file provenance does not prove model memory played
no role, nor establish that an inference is correct.

The same brief must handle all six entries. Data assembly can differ by concern; a special
runtime instruction, detector or source-study branch for each entry defeats this experiment's
purpose. Log human source selection and editing effort alongside model usage.

## 7. Step C: check the resource before reviewing targets

Use the six reserved source cases, already separated in selection: a favorable and a contrary
case per family. Their dated outcomes/reasons define the expected distinction. A fresh packet
session receives the candidate entry, visible case code/context, and no earlier reader's verdict,
historical answer or assessment. It reports the choice it would make, the source relationship,
the relevant check and uncertainty. Compare that output with the reserved evidence afterward.

This is a bounded check for actual specification errors, not an exam-calibrated authority score.
Agreement between repeated readers is not independent proof. A human inspects the six results
and the underlying sources for scope errors, reversed relationships and unjustified certainty.

Allow one repair pass per entry for a specific documented defect. A case used to repair an entry
becomes development evidence; recheck that entry on a newly reserved eligible case and retain
the first failure. If no such case exists, mark that distinction unvalidated. Do not repeatedly
tune until the same cases pass, or report six successful checks while dropping the failures.

Before whole-review generation, each family needs a defensible distinction and a usable contrary
check. Missing evidence or a repeated substantive failure ends this version's progression.
Retain the partial resource and write the result; a smaller-family experiment requires an
explicit revised protocol. It must not inherit this plan's claim to breadth.

Freeze the accepted bank and the source/check record before any target review. One frozen
acquisition serves all targets and repetitions; this experiment estimates review variation
conditional on that acquisition, not the reproducibility of the acquisition model itself.

## 8. Step D: the controlled whole-PR comparison

| Arm | Context added to ordinary review |
|---|---|
| A | None |
| B | The six eligible original census sentences, in a fixed neutral order |
| C | The six acquired runtime documents, in the same order and with the same entry IDs |

Give B and C the same neutral lead: these are independent project notes that may or may not
apply; compare them with the code and evidence. Neither receives extra authority, a mandatory
disposition, a target location or a request quota. Every target sees every entry, including
irrelevant entries. No selector or preparer runs per PR. A uses the ordinary baseline unchanged.

Use the current contract-2 solo reviewer with `filing_bar: request`, Opus 5.5/xhigh, CLI version
and contained tools pinned in the run plan. Use identical PR packets, pass-0 context, tool grants,
execution limits and task settings across arms. The treatment bundles corrected content,
examples and representation; length is not independently controlled. Source-study cost is an
additional investment, not free improvement.

Ordinary retrieval retains its episode date gate and self-exclusion. All six targets' outcome
material must also be excluded from review-history retrieval for every arm, so one target's
historical answer cannot become another's extra lesson. Inspect the current filter support
before promising this: `RetrievalGate` at the inspected develop revision has a singular
`exclude_pr`. Reuse supported scoped exclusions if available; otherwise make the smallest shared
source-filter extension, record it in run identity, and test origin/reference exclusions before
generation. Do not implement a probe-local retrieval tool or rebuild a large index for this.

Acquire only the common bank at `K`; ordinary date-eligible library/tools remain available equally
to all arms. Explicitly inspect indirect references to held-out outcomes in returned sources.
Contained sessions must not read project research documents, evaluation labels, other runs,
their repository's interactive memory or unrestricted web content.

Generate three independent repetitions, using the same bank throughout. Schedule complete
A/B/C blocks in a seeded, recorded order across repetitions to reduce time/window confounding.
Use a modest fixed concurrency supported by the existing orchestrator; no sequential-per-PR
custom runner is required. Do not read partial quality results and change later arms.

Resume infrastructure failures under the same task identities. A successful task is a retained
stochastic sample, never replaced because its answer is disappointing. Changed bank/prompt/tool
scope means a new version and run identity, not resume. Missing/failed tasks remain missing until
resolved; never score them as silence or silently complete the denominator with another PR.

## 9. Implementation and preflight

Implement in a topic worktree after reconciling the relevant foundation branches. At drafting,
`develop@2b306cef` has the Task/dataflow layer; `knowledge-transfer@1474776d` carries the later
review-operation/session fixes and the toolchain preflight (`4b7ee0ac`). Inspect and integrate the
needed fixes rather than copying their implementations or assuming branch-only work is merged.
Leave the old pilot runnable and its outputs untouched.

Use these existing surfaces:

- `src/ape/tasks/packet_session.py`: acquisition and bounded source-check sessions.
- `src/mathlib_review/analysis/sessions.py`: session plans, stored observations, input lineage
  and context derivation. B is a recorded deterministic input; C derives from the acquisition
  outputs. Preserve evidence of any human correction before composing the final bank.
- The ordinary solo task/run configs: whole-PR generation and standard finalized output.
- `TaskOrchestrator`, `ExecutionLimits`, `TaskStorage` and `Sample.successful_attempt`: execution,
  limits, resume and reading results. No private run loop, cache or usage counter.
- Canonical `match-plan` / `match` / `report match` and adjudication panels: measurement.

The same bank may require composing six outputs into one recorded context section. Do that
through the existing dataflow/derivation path, with deterministic composition and upstream
references. Do not hand-edit a derived context file or invent another store/class hierarchy.

Preflight must establish:

1. Exact source/target identities, cutoffs and exclusions; byte-identical bank per arm across PRs
   and repetitions. Config differences between arms are the intended context differences only.
2. Correct input/context binding and run names that distinguish bank version, arm and repetition.
3. Built base/reviewed workspaces and a working edit check on **each target toolchain**, under
   `ELAN_HOME=/research/projects/proofedit/ya475/.elan`. A smoke on an older PR is insufficient.
4. Containment, genuine availability of all granted tools, declared output submission and
   serialization into canonical findings. Use transport smokes for this, not as quality evidence.
5. Coverage/finalization refusal for missing sessions; resume skips successful tasks and retries
   only eligible failed work; allocation/concurrency settings are honored.

The implementation agent supplies exact dry-run and manual launch commands, generated configs,
and the allocation before model work. Test substantive binding/exclusion/coverage changes through
existing tests; avoid a new test suite for document formatting. No new generic experiment or
reviewing architecture is required.

## 10. Step E: evaluate the final delivered reviews

Export only complete, finalized runs and verify all 54 expected review samples. Keep channel
accounting so a lost submission is distinguishable from failure to find a concern. Include all
target asks, including documentation/PR-level asks outside the selected families.

**Historical recovery:** use ask-match/2-task with the pinned current rubric, question-form,
harness-blind inputs and two matcher repetitions in one canonical measurement plan. Record its
version, rubric, seal, reference asks, output channel, denominator and repetitions. Report per-PR
and per-family results as well as all-ask mean/union/stable results. These numbers do not join
older instruments or become precision. Resolve consequential matcher disagreements by inspecting
the recorded cases; retain their original verdicts and any separate audit.

**Correctness and request value:** prepare one blinded union of delivered concerns using the
existing `v5-adjudication/1` rubric: `correct_ask`, `valid_not_an_ask`, `wrong`, `unresolved`.
A person labels it. Group genuinely equivalent requests to reduce repeated reading, while keeping
all occurrences and materially different claims/fixes separate. A shared site, title or finding
key is insufficient to propagate a label: the previous reversed instance rename is the control
example. Keep exact finalized text and substantive supporting evidence; hide arm/session labels
and preparation-method identifiers. Content may still reveal a condition; report that limit.

Label the full union, including losses and off-family concerns, not just the apparent gains.
If the panel tooling cannot safely represent equivalence, use its existing occurrence-level
panel and consolidate in analysis; do not build a new adjudication subsystem. Unresolved cases
stay unresolved. Do not infer wrongness from absence in historical asks, or ask-worthiness from
compilation/author adoption alone. These are project judgments, not a recruited-maintainer study.

For a concern `g` on a PR, let `n_X(g)` be the number of the three final reviews in arm `X` that
deliver that materially equivalent request. A **stable gain over both comparators** has:

    n_C(g) >= 2, and n_C(g) > n_A(g), and n_C(g) > n_B(g).

Show stable losses against each comparator separately: `n_X(g) >= 2` and `n_X(g) > n_C(g)`.
For each arm report the sum of `n_X(g)/3` separately for useful, wrong, valid-but-unworthy and
unresolved concerns, plus raw findings and tokens. Also report useful share: the useful sum
divided by the sum across all four labels, including unresolved. These are expected delivered
concern counts/shares on this panel; repetitions are not independent PRs. Compare net useful
gains/losses and review burden, not union recall alone. Removing a valid-but-unworthy comment is
not a loss of a useful concern.

Read mechanism traces only after identifying gains/losses: did an eligible entry change the
distinction, consequence checked or request? Classify wrong scope, wrong correspondence, failure
to investigate, decision to retain, submission loss or evaluation mismatch. Apply the same reading
to successes and failures; do not count citations or compliance as the outcome.

## 11. Investment rule: what permits the next spend

Use the following development decision, fixed in the execution protocol before generation:

**Advance this candidate to planning a fresh test only if** C delivers at least two distinct
`correct_ask` stable gains over both A and B, on at least two PRs in two families; its total
expected useful-concern count exceeds both comparators after losses; its expected wrong-concern
count is no higher than either; its useful share is no lower than either; and it makes no stable
wrong/unworthy request to impose the specific revision that a contrary target was chosen to
defeat. Inspect the exact gains/losses
and resolve labels material to that decision before calling the criterion met.

These are investment heuristics on a deliberately selected small panel, not a significance test
or an estimate of deployable improvement. Declining the tempting change on a contrary target is
necessary here but not sufficient: blanket silence cannot pass the useful-gain requirements.

| Result | Decision |
|---|---|
| C meets the criterion and uses the acquired distinction appropriately | Freeze the candidate. Plan fresh PRs, target-independent selection and one new entry added through data alone. No automatic expansion. |
| B and C improve similarly over A | Prefer the cheaper input; richer acquisition has not earned its cost. Small-bank attention may explain the effect. |
| C helps only one family | Record a scoped candidate. Do not present it as cross-family transfer; choose a family-specific follow-up only with a clear payoff. |
| C states accurate distinctions but whole review is unchanged | Park this resource/procedure as a review intervention; do not keep elaborating notes or expanding the bank by default. |
| C gains asks but adds wrong/unworthy contrary requests or loses useful coverage | No unchanged adoption/expansion. Diagnose the concrete tradeoff; more comments are not success. |
| Source checks cannot establish reliable distinctions | Stop this version before the review batch. Record the acquisition failure and the missing evidence. |
| Instrument, environment or material labels remain unresolved | Report what is known and the missing condition. Repair that specific issue; do not call the design ineffective or launch a larger batch to compensate. |

Do not consume fresh PRs for this development comparison. A later fresh test needs a new plan,
source-overlap/date audit and target-independent selection; it is not merely another repetition
of six hand-picked targets. A positive content result does not itself justify a retrieval platform.

## 12. Allocation, artifacts and execution order

Defaults to carry into the costed recipe, all **processed-token ceilings**:

| Work | Sessions / allocation | Ceiling |
|---|---|---:|
| Acquire entries | 6 × 2M | 12M |
| Reserved source checks | 6 × 1M | 6M |
| Optional single repair and new check per entry | at most 12 × 1M | 12M |
| Final reviews | 54 × 4M | 216M |
| Transport smokes | at most 2 × 1M | 2M |
| Canonical matching | all scheduled matcher tasks combined | 6M |
| **Total maximum** | including optional work | **254M** |

The previous pilot used about 29M across 24 main sessions; its final reviews used about 9.9M
across twelve. The proposed review ceiling is intentionally above those typical per-session
uses. It is not an expected cost. Report an expected range from the selected targets' actual
prior outcomes when building the recipe; do not promise wall time from this table. Human source
curation and full-panel adjudication are additional costs and should be estimated explicitly.
On the subscription route tokens consume shared windows even when billed cash is zero.

Use existing execution limits/run allocations to bound every stage, including failed attempts
and repairs; confirm their accounting before launch. A refusal/failure does not create a free
replacement allocation. The whole batch, matching included, is user-run. An exhausted window
means resume the same work later, not change model or silently drop repetitions.

Proposed experiment root:

    results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/

Keep `PROTOCOL.md`, selection/cutoff/source assignments, source packets, session plans and stored
outputs, bank versions, context-derivation specs, allocation, evaluation sources and `RESULTS.md`
there. Use standard `results/pr_review_v5/runs/` and `.ape/runs/` for reviewer and Task outputs;
use the existing adjudications root for the panel. Configs may live under
`configs/reusable_review_knowledge/`. These are proposed paths, not files already created.

The dependency order is:

    A. Select entries/targets; verify source separation and common cutoff
      -> B. Acquire entries through the shared Task recipe
        -> C. Reserved source checks; bounded repair; freeze the bank
          -> D. 54 ordinary final reviews with A/B/C context
            -> E. Canonical matching + blinded usefulness evaluation
              -> F. Write the investment decision and update the research record

While B/C run, implementation can prepare D's configs, export and evaluation path without
reading target outcomes into acquisition. Final generation depends on a frozen bank and valid
preflight. Evaluation setup can proceed in parallel with generation; interpreting partial
outcomes must not change the remaining runs. Commit each completed stage with its evidence.

Keep the existing pilot's usefulness panel as a separate completion task under its frozen rubric.
It can revise the earlier pilot's assessment, but does not need to block source selection or
local implementation of this experiment. A new index, AST/review IR, per-convention detector
catalogue, fine-tuning campaign and second scaffold/model comparison are outside this handoff.
