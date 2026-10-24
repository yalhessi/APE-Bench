# Reusable review knowledge: the next transfer experiment

**Status: revised implementation plan, 2026-10-24.** Sections 1–13 are the active handoff and
supersede the original draft. Claude's review of that draft is preserved verbatim afterward;
its section references and recommendations describe the earlier version, not additional gates.
Source/target selection and implementation have not started. Model-backed acquisition, reviews
and judging remain user-run; writing this plan does not launch them.

This follows the [historical synthesis](../research/knowledge-transfer-experiment-synthesis-2026-10-23.md)
and [latest pilot assessment](../research/review-knowledge-transfer-pilot-assessment-2026-10-23.md).
It replaces the earlier conditional-preparation method as the candidate for the next experiment;
the [October 23 plan](2026-10-23-review-knowledge-transfer.md) and its results remain historical.

## 1. The question and the research decision

**Can knowledge acquired from independent earlier decisions improve ordinary whole-PR review,
and does a compact account suffice or do fuller conditions and grounds add useful reviewing
ability? Can either resource distinguish when a tempting revision should be declined?**

The candidate intervention is a reusable resource, acquired before reviewing the targets. Its
entries explain the choice, applicability, competing reasons and useful checks. One shared
procedure acquires a compact and a full version of each entry from the same eligible packet;
ordinary review consumes one frozen version of the bank. The reviewer is free to disagree,
investigate or remain silent. A new concern should require source data, not new runtime code.

This deliberately revises the original comparator. The old census sentences remain historical
artifacts used to identify topics and document corrections; they are not arm B. Comparing a
new account with an incorrect old sentence would not tell us whether the fuller account is
worth using. Acquiring both versions now also avoids a mandatory corrected-one-liner campaign
before a useful compact resource can receive a fresh test.

The intended mechanism is specific: a better account of a distinction changes the comparison
at a relevant object, and that changes a delivered request appropriately. Better distinctions
may affect recognition, attention, applicability or judgment as well as supply a missing fact.
Each chosen opportunity must state the predicted change and what would count against it.
More citations, a complete ledger, or more checks without better review do not establish success.

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
| F/G/AP ask-free delivery | Lists, pinpointing and examples/precedence did not reliably generalize; offering an entry for verification often moved little. | Compare newly acquired compact and full accounts with ordinary review; no target-specific selector or applicability assertion. |
| Oracle ladder | A sentence already recovers most possible changes at the known place; examples sometimes hurt. | No gold location, no assertion of applicability, whole-PR final output, and independently checked scope/correspondence. |
| Stage H and the places test | Example-based demand prediction and exhaustive application have discrimination/burden limits. | Use genuine contrary decisions or established technical consequences; silence is not a negative label. |
| October 16 departure readings | Some rules and detectors misstated the convention; primed naming remained unstable. | Check the acquired distinctions against reserved source cases; uncertain knowledge can remain uncertain or fail. |
| Reconstruction and source-supply diagnostics | Sources can improve consideration without reliably improving requests. | Test reuse across target PRs, rather than another known-site demonstration. |
| October 23 preparation pilot | Conditional investigation did not improve historical recovery over ordinary extra preparation. | No preparer per target; the treatment is a frozen reusable resource, and a solo arm is included. |
| Ask readings and census-rank analysis | Statement/API sentences were often ignored; exact-delivery gains varied strongly by rank. | Use those observations to select explicit mechanism hypotheses, not as causal ceilings or automatic exclusions. |

The dossier line was previously narrowed/closed as a recall lever. This is a bounded reopening
because the later construct corrections identify actual content/scope errors and source-derived
dossiers were not built. An unchanged sentence with decorative examples does not qualify as the
new intervention. The earlier ask-free AP results met the dossier round's stopping condition
for a recall lever; that remains evidence against expanding the old intervention. The narrower
reopening rests on the later specification errors and independent acquisition, not on
reinterpreting AP as a success.
It is a hypothesis, not evidence that a richer resource will work. The linked synthesis names
the original instruments, denominators and limitations; do not pool their numbers.

## 3. Fixed design

| Item | Default |
|---|---|
| Knowledge scope | Six entries across three concern families; one bank shared by every target |
| Development targets | Six PRs outside the fresh set: an opportunity and a contrary target per family; prefer already-used opportunities |
| Source separation | All targets excluded from acquisition; one common knowledge cutoff before every target |
| Arms | A: ordinary review; B: acquired compact bank; C: acquired full bank; B/C share source packets |
| Acquisition and source checks | Opus 5.5, xhigh, contained Claude Code packet sessions, each a fresh conversation |
| Reviewer | Opus 5.5, xhigh, current contained Claude Code route |
| Runtime | The same ordinary contract-2 reviewer, tools, pass-0 inputs and limits in all arms |
| Replications | Three independent final reviews per PR and arm: **54 final-review sessions** |
| Outputs scored | Canonical finalized findings; submissions and notes explain losses only |
| Primary quality evidence | Blinded project adjudication; three preregistered opportunity concerns plus the full delivered union |
| Separate reference measure | Canonical raw-ask matching, one measurement plan across all arms |

The synthesis proposed two repetitions/36 reviews. This plan uses three, following `CLAUDE.md`'s
reporting rule and the instability in prior runs. The added repetitions are included in the
allocation below. No further replication, second model or fresh PR tranche is automatic.

## 4. Step A: select the entries, targets and source cases together

This is a bounded data-selection task, using existing results rather than another corpus census.
Start from documented failures and the `library_partial` determiner annotations in
`results/pr_review_v5/probes/library-knowledge-2026-10-13/readings/{A,B,C,D}.jsonl`, joined to the
41 asks in that probe's `asks.jsonl`. The diagnostic reported 19 ingredient-supplying cases;
retain reader disagreements rather than treating the count as a settled selection list.

Prefer three different types of decision:

1. **Scope/precedence:** namespace or naming choices where a superficial analogue can mislead.
2. **Automation/mechanism:** registration, tactic or mechanism choices with relevant operational
   consequences. The familiar aesop case may illustrate development; it does not earn another
   standalone source-supply campaign.
3. **Statement/API design:** assumptions, generality, formulation or a related API choice.

Choose two concern entries per family, using the census as a topic index. Prefer the middle and
tail where supporting evidence exists, and seek at least one entry outside the top fifty.
Evidence quality takes priority over a rank quota. Freeze the codebook revision and rank
calculation, including primary/secondary assignments. A thin census entry may have other
eligible supporting decisions or library evidence; its ask count alone is not an eligibility
test. Record deviations. Do not fill all three families with wrapper removal/generation.
PRs 33066 and 33117 remain fixtures, not default targets for another campaign.

For each family select one previously observed review opportunity and one target with a
competing reason/form that tests overapplication. Prefer opportunity targets with prior ordinary
reviews and diagnostic readings. Contrary targets may come from other buildable historical PRs
outside the reserved fresh set; the stated-grounds and attention-practice records are starting
points. Record the fresh-set exclusion source explicitly. Known misses may inform selection.
The target reviewer receives neither that designation nor a list of expected findings. A
contrary target requires an explicitly supported reason to retain the form, or project
adjudication of that choice; merely merging without a comment is insufficient. Record whether
the reference is a maintainer's stated reason, a verified consequence or a project judgment;
the last is a weaker fallback. Target feedback belongs to evaluation files, outside every
model-visible acquisition/review packet.

For each opportunity preregister **one primary concern**, its materially equivalent requested
change, the responsible entry or entries, the missing distinction and the predicted effect.
For each contrary target specify the tempting revision, the reason to retain the form and the
request that would count as overapplication. There are three primary opportunity concerns,
one per family; other gains remain exploratory. Consult old `knowledge`, `behaviour` and
`determiner` readings, but do not require a particular label. These session-specific diagnoses
are evidence, not proof that only fact/search misses can change. In particular, the DeepSeek
known-site ladder does not bound an Opus whole-review intervention's reachable concerns.

Record all candidates considered and the reason for inclusion/exclusion. Freeze the six targets
before model acquisition; do not replace one because the acquired entry predicts its answer
poorly. Preserve AI-origin evidence and include such PRs when eligible; do not filter them out.

**Deliverable:** `selection.json` and `SELECTION.md`, containing exact PRs, episodes, release roots,
reviewed-head timestamps, base/reviewed SHAs, family assignments, existing run references,
census IDs/ranks, codebook revision, AI labels, the three primary concerns and contrary
definitions, mechanism hypotheses, and entry-specific source/check assignments. Prefer a late,
narrowly spaced target cohort when evidence permits; report the cutoff spread. The acquisition
writer's packet omits target identities, expected answers and previous target trajectories.

Spend at most one working session on this assembly, initially about half a day. Failure to find
an adequately sourced three-family comparison is a useful result. Record the missing evidence
and stop or revise the design; do not silently turn this into an unbounded discovery project.
The exact IDs are intentionally an implementation deliverable, not invented in this plan.

## 5. Source eligibility shared by both acquired resources

Resolve each target's ordinary episode cutoff from its reviewed head. Choose a common cutoff
`K` no later than the earliest of those cutoffs. All knowledge evidence, including the full
discussion context used to interpret a decision, must have been available **strictly before K**.
Record `K` as an exact UTC timestamp. The target code still comes from each target's normal view.

Exclude all six target PRs, their reviews, later changes, and material elsewhere that reveals
their outcomes from acquisition sources. Exclude reserved validation cases from induction.
Broader project assessments and the historical synthesis can guide the researcher, but must not
enter a writer's packet: they contain the answers we are trying to transfer without.

**Both B and C are acquired from exactly the same eligible source packets.** The original census
sentence, rationale and examples do not enter acquisition or runtime. The researcher may use
them to locate a topic or candidate evidence, but must assemble the packet from the dated
primary sources. Save the original sentence and any correction separately for analysis. There
is no exception allowing future-derived knowledge into B, and no need to audit the complete
ancestry of an old sentence we do not supply. This remains a deliberately selected developmental
panel; it does not make researcher topic selection target-independent.

Use small source packets built from existing corpus readers: comments/discussion, relevant
before/after code, and dated library evidence. For each entry seek two independent source PRs;
include up to four cases where useful. Reserve a favorable and a contrary case **for each
entry**. Cases may be shared between entries only when each tests the entry's actual distinction;
family membership alone is insufficient. This requires twelve entry/case assignments and up
to twelve distinct reserved cases. All reserved evidence must also predate K. These are practical
bounds, not evidence-count thresholds that establish a convention. Record author/scope
concentration and thin evidence.

A contrary example is an explicit reason to retain a form, or a concrete, verified consequence
that defeats the tempting revision. Identify which kind it is. An inferred tradeoff may guide
investigation but must not be relabeled as a maintainer's stated preference.

Both bank variants must be portable to all six targets without per-target edits or references.
If that is impossible under one cutoff, revise selection before model work. Do not supply
different knowledge under the same condition label.

## 6. Step B: acquire six reusable entries through one Task recipe

Use `PacketSessionTask` with the shared source-study brief, one independent packet per entry,
one acquisition sample each. Fix `claude_model: claude-opus-5-5`, `effort: xhigh`, the contained
Claude Code route, and the exact CLI binary/config digest in the recipe. Source checks use the
same model/effort in fresh conversations. Writer and reviewer share model weights, not session
memory; this tests whether a source-backed resource helps fixed weights perform review.

The acquisition model can read only its supplied source files and ordinary instructions. On this
Task, inspecting code means reading packet files, not executing Lean or querying retrieval.
Source collection and local technical checks precede the packet and retain their exact results.
No live retrieval, target workspace or new task hierarchy is needed to write the entry. Do not
claim that packet containment eliminates prior model knowledge or training exposure.

The brief asks the writer to:

1. Recover the actual choice and the reason each source supports; inspect the associated code.
2. Explain what distinguishes the alternatives: semantic roles, scope, precedence, consequences
   or uncertainty. A citation alone is insufficient.
3. Seek contrary evidence in the packet and identify where a generalization would fail.
4. State what a reviewer should inspect or try to resolve a new occurrence. Use existing tools;
   do not invent an executable checker per convention.
5. Retain uncertainty when the sources do not determine a boundary. Do not manufacture an
   authoritative rule to make the resource look complete.

Each acquisition session declares **`compact.md`, `entry.md` and `sources.json`** as outputs.
The same brief requests both runtime versions from the same evidence, with neither target
identities nor target outcomes. The full `entry.md` contains:

| Content | Requirement |
|---|---|
| Choice | The alternatives and their roles, in language transferable beyond a source identifier |
| Conditions | Evidence favoring each form; scope, precedence and unresolved cases |
| Evidence | Short code/discussion excerpts with source IDs, dates and the relationship they establish |
| Application | What to inspect or test, and what result would defeat a proposed revision |
| Status | Distinguish stated reasons, observed consequences and inferred explanations |

`compact.md` states the choice, decisive boundary and uncertainty in at most **75 words per
entry** (450 for the bank). It may use several sentences; it must not repeat a known incorrect
rule or discard a crucial exception merely to be short. `entry.md` has at most **500 words per
entry**, including excerpts (3,000 for the bank). If a compact account must retain uncertainty,
say what it cannot decide rather than manufacture a universal rule. Neither version asserts
that it applies to a target.

Keep fuller source material as acquisition evidence, not extra runtime context. Check word
counts locally. `sources.json` maps material claims in both versions to actual packet inputs;
it is study data, not a new provenance subsystem. Verify citations and directional correspondences
against those inputs. Save corrections relative to the old census sentence outside runtime.
These are two practical resources with shared source eligibility, not information-equivalent
strings. Their comparison bundles compression, explanation, examples and length; it cannot
identify a pure formatting effect.

The same brief must handle all six entries. Data assembly can differ by concern; a special
runtime instruction, detector or source-study branch for each entry defeats this experiment's
purpose. Log human source selection and editing effort alongside model usage.

## 7. Step C: check the resource before reviewing targets

Use the twelve entry/case assignments separated in selection: a favorable and a contrary case
for each entry. Their dated outcomes/reasons define the expected distinction. Each assignment
gets one fresh packet session containing the compact and full versions, visible case code/context,
and no earlier reader's verdict, historical answer or assessment. It reports the case choice,
supporting relationship, useful check and uncertainty; then identifies unsupported claims or
boundaries lost in either version. Declare the response file in the Task plan. Compare the
response with the reserved evidence afterward, retaining the exact inputs and outputs.

This is a bounded check for actual specification errors, not an exam-calibrated authority score.
Agreement between readers is not independent proof. The checker sees both versions, so these
are **joint specification checks, not independent compact-versus-full performance measurements**.
A human inspects all twelve responses and the underlying sources, checking each version's
claims and scope separately. Only the whole-review comparison estimates their reviewing effect.

Allow one repair pass per entry for a specific documented defect, revising both versions as
needed from the same expanded evidence. A case whose feedback informs repair becomes development
evidence. Replace each such case with a newly reserved eligible case, at most two per entry,
and retain the first failure. Run at most two post-repair checks per entry. An untouched case
can be rechecked but is not new held-out evidence.
If no replacement exists, mark that distinction unvalidated. Do not repeatedly tune until the
same cases pass or report only the successful checks. Human edits receive the same record and
case-replacement treatment; they are not unrecorded extra acquisition samples.

Before whole-review generation, both versions of every entry need defensible claims and usable
favorable/contrary checks. Missing evidence or a repeated substantive failure ends this version's
progression.
Retain the partial resource and write the result; a smaller-family experiment requires an
explicit revised protocol. It must not inherit this plan's claim to breadth.

Freeze both accepted bank versions and the source/check record before any target review. One
frozen acquisition serves all targets and repetitions; this experiment estimates review variation
conditional on that acquisition, not the reproducibility of the acquisition model itself.

## 8. Step D: the controlled whole-PR comparison

| Arm | Context added to ordinary review |
|---|---|
| A | None; the common target-history exclusions still apply |
| B | The six acquired `compact.md` files, in a fixed neutral order |
| C | The six acquired `entry.md` files, in the same order and with the same entry IDs |

Give B and C the same neutral lead: these are independent project notes that may or may not
apply; compare them with the code and evidence. Neither receives extra authority, a mandatory
disposition, a target location or a request quota. Every target sees every entry, including
irrelevant entries. No selector or preparer runs per PR. A is ordinary review under the same
shared exclusions; do not call it byte-identical to an earlier historical baseline.

Use the current contract-2 solo reviewer with `filing_bar: request`, Opus 5.5/xhigh, CLI version
and contained tools pinned in the run plan. Use identical PR packets, pass-0 context, tool grants,
execution limits and task settings across arms. Treat historical targets as potentially exposed
in model training. Interpret between-condition differences, not absolute recall as evidence of
uncontaminated generalization. Source-study cost is an additional investment, not free improvement.

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

Implement in a topic worktree. At revision, `develop@29f90ba5` has the Task/dataflow layer;
`knowledge-transfer@1474776d` carries the later review-operation/session fixes, panel readers and
toolchain preflight (`4b7ee0ac`). Prefer integrating the reviewed foundation with its suite green
over copying selected implementations. Confirm the actual branch state before doing so.

A conflict-free `merge-tree` result does not check untracked checkout obstructions: some files
tracked on that branch already exist as untracked copies in the main checkout. Compare and
preserve those copies before integration; do not clear them blindly. Source selection and
packet assembly can proceed before integration, while generation requires a checked foundation.
Leave the old pilot runnable and its outputs untouched. This plan records the dependency; it
does not claim the merge or its checks have happened.

Use these existing surfaces:

- `src/ape/tasks/packet_session.py`: acquisition and bounded source-check sessions.
- `src/mathlib_review/analysis/sessions.py`: session plans, stored observations, input lineage
  and context derivation. Both B and C derive from declared acquisition outputs. Preserve
  evidence of any human correction before composing either final bank.
- The ordinary solo task/run configs: whole-PR generation and standard finalized output.
- `TaskOrchestrator`, `ExecutionLimits`, `TaskStorage` and `Sample.successful_attempt`: execution,
  limits, resume and reading results. No private run loop, cache or usage counter.
- Canonical `match-plan` / `match` / `report match` and adjudication panels: measurement.

Use the existing dataflow/derivation path to bind the six outputs. Each section must name its
entry packet explicitly through supported `packet_id`/`by_pr` binding; a bank entry is not a
`pr<N>` packet. Both banks retain upstream references. Use shared entry IDs, titles and order;
include the neutral lead once, not once per section. Do not hand-edit derived context files or
invent another store/class hierarchy. Locally verify the 75/500-word limits: context derivation
does not itself enforce them.

Pin the resolved baseline config and digest, not only the phrase "contract-2 solo reviewer".
The pilot used `configs/knowledge_transfer/consumer_opus55_claude_sub.yaml` on its branch, extending
the reconstruction validation baseline; develop's similarly named contract-2 config is not
byte-equivalent. Remove pilot-specific PR/context bindings through normal config overrides,
bind the selected release(s), and resolve every arm to verify the only intended differences.

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
and the allocation before model work. Verify that the shared panel path preserves all occurrences
needed for the per-arm sums below; do not assume a unique-concern count implements them. Extend
the singular retrieval exclusion at the shared gate if needed, testing origin and indirect-reference
exclusions in both consumers. Use a field for the excluded set, not a new gate vocabulary value.
Test substantive binding/exclusion/coverage changes through existing tests; avoid a new test suite
for document formatting. No new generic experiment or reviewing architecture is required.

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
existing `v5-adjudication/1` rubric. A person labels it. Stored resolved labels are `correct_ask`,
`valid_not_an_ask` and `wrong`; `unresolved` is a panel response, not a fourth adjudication-store
label. Compute the four-way reporting denominator from panel responses without inventing a new
store label. Group genuinely equivalent requests to reduce repeated reading, while keeping
all occurrences and materially different claims/fixes separate. A shared site, title or finding
key is insufficient to propagate a label: the previous reversed instance rename is the control
example. Keep exact finalized text and substantive supporting evidence; hide arm/session labels
and preparation-method identifiers. Content may still reveal a condition; report that limit
and instruct the reader to judge the request and evidence, not the presence of a bank citation.

Label the full union, including losses and off-family concerns, not just the apparent gains.
If the panel tooling cannot safely represent equivalence, use its existing occurrence-level
panel and consolidate in analysis; do not build a new adjudication subsystem. Unresolved cases
stay unresolved. Do not infer wrongness from absence in historical asks, or ask-worthiness from
compilation/author adoption alone. These are project judgments, not a recruited-maintainer study.

For a concern `g` on a PR, let `n_X(g)` be the number of the three final reviews in arm `X` that
deliver that materially equivalent request. For resource arm `X` against comparator `Y`, a
**stable gain** has:

    n_X(g) >= 2, and n_X(g) > n_Y(g).

Show the three planned contrasts: B−A, C−A and C−B. Show stable losses with the roles reversed.
Only gains on the three preregistered primary concerns count toward the advancement gate.
Other correct requests, including previously unasked ones, count in full-union quality totals
and remain exploratory gains. Report all primary concerns even when all arms miss them.
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

## 11. Investment rule: which resource earns the next spend?

Fix the following development rule in the execution protocol before generation. A resource arm
`X` **qualifies against comparator Y** only if all of these hold:

1. At least two of the three preregistered primary concerns are adjudicated `correct_ask` stable
   gains for X over Y, on two PRs in two families.
2. On the full union, X's expected useful-concern count is higher after losses, its expected
   wrong-concern count is no higher, and its useful share is no lower than Y's.
3. X makes no stable wrong/unworthy request to impose a revision that a contrary target was
   selected to defeat. Here stable means that materially equivalent bad request appears in at
   least two of X's three reviews, regardless of whether Y also makes it.
4. Inspect the exact gains/losses and resolve panel labels material to the decision. All 54
   final reviews and the full union must be accounted for; do not decide from a gains-only panel.

Evaluate B against A and C against A independently. Prefer B if it qualifies. C supersedes a
qualifying B only if C also qualifies against B by the same rule. If only C qualifies against A,
it can earn a fresh test, but that does not establish C's superiority over B; keep B in that next
comparison unless the present C−B evidence also meets the rule. This permits useful compact
knowledge to advance without first proving that fuller notes help.

These are investment heuristics on a deliberately selected small panel, not a significance test
or an estimate of deployable improvement. Three repetitions do not make a discovered difference
statistically stable. For example, under independent Binomial(3, 0.5) counts in three identical
arms, the original rule `n_C >= 2, n_C > n_A, n_C > n_B` passes for a given concern about 19%
of the time. Preregistering three concerns reduces post hoc selection; it does not eliminate
noise, multiple comparisons or within-PR dependence. Do not import the appended review's
simulation percentages as a measured false-positive rate for this revised design. Inspect
mechanism evidence and losses, and use fresh PRs for the next actual test of generalization.

| Result | Decision |
|---|---|
| B qualifies against A; C does not qualify against B | Prefer the compact bank for fresh-test planning. Fuller explanations have not earned their added runtime context. |
| C qualifies against A and B | Prefer the full bank for fresh-test planning; the grounds/conditions have earned a bounded follow-up. |
| Only C qualifies against A, without qualifying against B | Plan a fresh comparison retaining B. There is a candidate effect over ordinary review, but the compact/full choice remains uncertain. |
| Neither qualifies, but one helps only one family | Record a scoped result. A family-specific follow-up needs a concrete payoff; no automatic expansion or claim of cross-family transfer. |
| Accurate entries leave whole review unchanged | Park this resource/procedure as a review intervention; do not elaborate notes or expand the bank by default. |
| Gains come with wrong/unworthy contrary requests or lost useful coverage | No unchanged adoption. Diagnose the concrete tradeoff; more comments are not success. |
| Source checks cannot establish reliable distinctions | Stop this version before the review batch. Record the acquisition failure and missing evidence. |
| Instrument, environment or material labels remain unresolved | Report the missing condition and repair that specific issue; do not call the design ineffective or launch a larger batch to compensate. |

A qualifying result permits **planning**, not launching, a fresh test: freeze the chosen resource,
use target-independent selection, and test adding a new entry through data alone. Do not consume
fresh PRs here or call another repetition of these six targets a transfer test. A positive result
does not itself justify a retrieval platform. Both resources share the same acquisition cost in
this experiment; a compact win saves runtime context, not demonstrated acquisition effort.

## 12. Allocation, artifacts and execution order

Defaults to carry into the costed recipe, all **processed-token ceilings**:

| Work | Sessions / allocation | Ceiling |
|---|---|---:|
| Acquire entries | 6 × 2M | 12M |
| Reserved source checks (both versions inspected jointly) | 12 × 1M | 12M |
| Optional single repair and up to two post-repair checks per entry | at most 18 × 1M | 18M |
| Final reviews | 54 × 4M | 216M |
| Transport smokes | at most 2 × 1M | 2M |
| Canonical matching | all scheduled matcher tasks combined | 6M |
| **Total maximum** | including optional work | **266M** |

The previous pilot used about 29M across 24 main sessions; its final reviews used about 9.9M
across twelve. The proposed review ceiling is intentionally above those typical per-session
uses. It is not an expected cost. A provisional ordinary-work estimate is about **45–95M**
processed tokens before optional repairs, based on the pilot/review sessions cited in the
appended review. At the historically observed roughly 19–24M per five-hour window this is about
two to five window-equivalents, not a promise of present quota or elapsed time. Replace this
estimate with the selected targets' actual prior usage before launch.

For the nine six-PR review runs, set `solo_token_cap: 4000000` and
`run_total_token_cap: 24000000`; retain the enclosing batch allocation. If dataset constraints
require smaller run groups, keep the same 54 cells and total allocation, and document the
grouping before generation. A producer/check Task also needs its own enforced token allocation.

Budget human time, not just model tokens. Initial planning allowances are 2–4 hours for bounded
selection, 4–8 for packet assembly, 1–3 for source-check inspection, and 5–12 for the findings
panel. These are estimates to revise from actual packet size and overlap, not staffing promises.
At the pilot's rate, 54 reviews could deliver about 300 findings, perhaps 100–150 distinct
concerns; correct equivalence grouping matters. The source inventory is 12–24 induction-case
assignments plus 12 validation assignments, with legitimate sharing reducing distinct cases.
Label the primary and contrary concerns first to expose problems promptly, then the complete
union; the advancement decision waits for both. On the subscription route tokens consume shared
windows even when billed cash is zero, and those windows are shared with interactive use.

Use existing execution limits/run allocations to bound every stage, including failed attempts
and repairs; confirm their accounting before launch. A refusal/failure does not create a free
replacement allocation. The whole batch, matching included, is user-run. An exhausted window
means resume the same work later, not change model or silently drop repetitions.

The implementation deliverable includes exact user-run commands for generation and canonical
matching, and local commands for preparing/reading the human panel. No model/API work is launched
as part of implementing or reviewing this plan. Check current window availability before each
user-launched block; quota exhaustion means resume with the same model/configuration.

Proposed experiment root (create it with its protocol and register it in the research index):

    results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/

Keep `PROTOCOL.md`, selection/cutoff/source assignments, source packets, session plans and stored
outputs, bank versions, context-derivation specs, allocation, evaluation sources and `RESULTS.md`
there. Use standard `results/pr_review_v5/runs/` and `.ape/runs/` for reviewer and Task outputs;
use the existing adjudications root for the panel. Configs may live under
`configs/reusable_review_knowledge/`. These are proposed paths, not files already created.

The dependency order is:

    A. Select entries/targets; verify source separation and common cutoff
      -> B. Acquire compact/full pairs through the shared Task recipe
        -> C. Reserved source checks; bounded repair; freeze both banks
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

## 13. First implementation handoff and decisions from review

**Start with Step A, not generation.** In a topic worktree, inspect the saved readings and source
records, then deliver `selection.json`, `SELECTION.md` and the initial `PROTOCOL.md` under the
experiment root. The protocol opens with `## Already answered?` and freezes this question,
the three primary concerns, contrary criteria, source cutoff/exclusions, check assignments,
model settings and advancement rule. The selection pass is bounded to about half a day; it
needs concrete source references and eligibility, not polished packets or a new collector.

After that selection is defensible, assemble packets and the costed recipe. Supply declared
acquisition/check outputs, context-derivation specifications, the shared baseline and nine run
configs (or documented equivalent grouping), exact manual commands, planned run names and the
local preflight results. Record foundation integration status explicitly. Update the plan-status
row as each deliverable lands. A handoff that merely repeats "use Tasks" without these bindings
is incomplete; a missing eligible panel should produce a bounded gap report, not speculative code.

The source/target selection and local implementation are the immediate work. Packet acquisition
then depends on valid source packets and the checked recipe. Final-review generation depends
on frozen, validated banks and successful generation preflight. Evaluation setup and foundation
integration can proceed alongside source work without entering target answers into acquisition.

The appended review informed this revision as follows:

| Review point | Decision in this plan |
|---|---|
| Missing writer settings, baseline pinning, data-path/tooling corrections, human cost | Adopted in §§3–4, 6, 9–10 and 12. |
| Old census ancestry/date feasibility; corrected-one-liner follow-up | Replaced B with a compact resource acquired from the same pre-K packet as C. Old sentences remain historical artifacts; no future-data exception or fourth arm. |
| Favorable/contrary coverage | Twelve entry/case assignments; explicit joint specification checks of both versions, with human inspection and no performance claim. |
| Historical knowledge labels bound reachable gains | Not adopted. Require entry-specific, falsifiable mechanism hypotheses; retain labels as diagnostic evidence. |
| Restrict census ranks | Sampling preference rather than a hard gate; evidence outside census asks is eligible. |
| Gains can occur by chance; full panel needed | Preregister three primary concerns; retain full-union quality guards and explicitly developmental advancement decisions. No claim of significance. |
| Foundation merge before any selection | Integration is required before generation, not before source selection. Preserve untracked checkout copies and verify the actual integrated tree. |

The historical review below is preserved verbatim from the original draft at `29f90ba5`.
Its statement that the plan is unchanged refers to that original append, before this revision.

---

## Review of this plan, 2026-10-24 (appended; the plan above is unchanged)

Read against `develop@29f90ba5` and `knowledge-transfer@1474776d`, the records in §2's table,
`docs/questions.md`, `docs/dead-ends.md`, `docs/todo/conventions-dossiers-exams.md`, the dossiers
adversarial round, the census store, the pilot's protocol and panel, and the code surfaces §9
names. Nothing was run except a null-rate calculation (script and numbers in §R3).

**Verdict.** This is the right next experiment on the record, and the plan is honest about what
it can establish. The dossiers line is an open todo narrowed by its adversarial round, not a dead
end, and §2 states the reopening and its ground (the October 16 construct errors) correctly. The
surfaces it names exist and do what it says, with the exceptions in §R6. Six things should be
settled before Step A begins (§R1); the investment rule needs one repair (§R3); and the cost table
should be restated in windows (§R4). None of this changes the design's shape.

### R1. Settle before Step A

1. **Name the acquisition model, route and effort.** §3 fixes the reviewer; §6 never says who
   writes the entries. `PacketSessionTask` on the Claude Code route has no Lean or retrieval tools
   (`enabled_tools` is read/write/search), so "inspect the associated code" in §6 means reading
   the packet's excerpts, and every technical check is human-run before the packet. If the writer
   is Opus 5.5, say the consequence: writer and reviewer share one memory, so C tests whether a
   written, source-backed account in context beats the same model's latent knowledge; the sources
   are the only new information.

2. **The arm-B date rule as written rejects nearly every entry; decide the standard now.** The
   census sentence is induced over the whole val1000 window (2025-06..2026-03) in seeded random
   order, and entries flagged `revised` were broadened across batches
   (`results/pr_review_v5/adjudications/conventions-census-v1/reader_A/codebook.json`). So for any
   target with a cutoff inside that window, "no supporting case may postdate `K`" fails by
   construction for most entries, and the rule leaves B empty. The audit §5 asks for is feasible:
   an entry's supporting asks are the `principle_id` / `second_principle_id` rows in
   `reader_A/labels_b*.jsonl`, each `cid` resolves to a PR through
   `adjudications/arm-coverage-val-2025-06-2026-03-v1/events.jsonl`, and the PR's dates follow.
   Recommended standard: a hard gate on provenance (no target or reserved case among an entry's
   supporting asks), and the date distribution of supporting asks relative to `K` *recorded*, not
   gated. Say in `PROTOCOL.md` that B is the existing resource as it stands, induced after `K`,
   and that this is a known asymmetry against C, which must be pre-`K`.

3. **Choose the targets so `K` is late, and say the targets are in-window.** One `K` at the
   earliest of six cutoffs makes every census ask between `K` and the latest cutoff ineligible for
   both the bank and the B audit. Report the cutoff spread before freezing, and prefer targets whose
   cutoffs sit within a few weeks of each other. Every already-used PR is inside Opus 5.5's training
   window; the pilot's protocol said so and read only between-condition differences
   (`.claude/rules/mathlib-review.md`, the 2026-09-25 rule). §3 should carry the same sentence.

4. **A favorable target needs a mechanism check on readings already on disk, not only a known
   miss.** C supplies content: a condition, a consequence, a check. It supplies neither attention
   nor an applicability judgment. The ladder split the free reviewer's remaining misses into 4
   attention or decision, 3 "needs to be told it applies", 3 "needs a fact or a search"
   (`probes/conventions-ladder-2026-10-08`); the dossiers round put understanding at a quarter to
   a half of the residual. Only the last kind is reachable by this treatment. The per-ask,
   per-session readings exist: `probes/ask-reading-2026-10-12/readings/*.jsonl` carry `behaviour`,
   `knowledge` and `knowledge_detail` for every in-census ask on D12 and P14post, and
   `probes/library-knowledge-2026-10-13/readings/*.jsonl` carry `determiner`. Step A should accept
   a favorable target only where those readings put its miss in the knowledge kind, record the
   label, and state the ceiling: the number of such asks across the three favorable targets is the
   most C can add on historical recovery, probably three to six.

5. **Name the pool for contrary targets, and relax "already used" for them.** A target with an
   *explicitly supported* reason to retain the form, in the same family as an entry, among
   already-used PRs, is the hardest cell to fill. The stated-grounds and attention-practice probes
   found 23-24 stated declines of a convention (6-8 giving a fact about the place) on val1000 PRs
   that are not already used. Allow a contrary target from any PR outside the fresh set with a
   buildable reviewed state, and say up front that project adjudication of the retention is the
   weaker fallback, since then the researcher's judgment is the reference.

6. **Merge `knowledge-transfer` into `develop` before opening the topic worktree.** The branch
   holds the review-session task (`review/session.py`, operations increment 4), the toolchain
   preflight, the fixes both independent reviews asked for, the panel readers, and the recon and
   pilot configs that develop lacks (`configs/pr_review_v5_recon_baseline_*` are tracked only
   there; the pilot's consumer config extends one of them). `git merge-tree` reports zero conflicts,
   and develop has only three docs commits the branch does not. "Inspect and integrate the needed
   fixes" (§9) is more work and more risk than merging the whole branch with the suite green.

### R2. The design, where I would push

- **B ≈ A is the record's prediction, not a surprise.** §8's neutral lead ("may or may not apply;
  compare with the code") is the delivery that has never moved reach: offered for verification
  rather than asserted, +0.00 to +0.03 (`research/conventions-dossiers-review-2026-10.md`); bare
  sentences picked ask-free, +0.03 on Claude. Add that row to §2's table, and read B's role as the
  control for whether a small bank changes attention at all. The decision table's "B and C improve
  similarly" is then the unlikely branch, and "C > B" is the whole bet.

- **Family 3 has the worst prior for sentence delivery.** In the ask reading, statement and API
  design reached 0 of 18 with every held sentence ignored. That makes it either the family where a
  conditional account has the most to add or the one where nothing in context moves. Choose its two
  targets with the mechanism check in R1.4 especially carefully, and expect the per-family split to
  be the informative read.

- **Avoid head entries, not just "one outside the top fifty".** Exact delivery gained mostly past
  rank 100, head asks were stable misses, and the dossiers round's surviving thread aimed at ranks
  11-50 (`questions.md`, "Where, by census rank, does an exact-convention delivery gain?"). In the
  frozen census, rank 10 holds 32 labels, rank 50 holds 10, rank 100 holds 4, and 284 of 410
  entries hold three or fewer (`reader_A/labels_b*.jsonl`, both id fields). Prefer entries in the
  10-50 range and below; an entry with three or fewer asks cannot supply two source cases plus two
  reserved ones, which bounds how far down the tail Step A can go. Say which codebook revision the
  ranks come from: the census results report 409 entries, the ceiling probe's brief used 438 at
  `2bb3063a`.

- **Where C corrects B's sentence, keep the corrected one-liner.** If an entry's "Choice" line
  contradicts the census sentence (the namespace precedence case), then C > B cannot separate
  "corrected content" from "richer representation", and the ladder says a sentence carries most of
  the recoverable change at a known place. Do not add a fourth arm now, but record the corrected
  one-line statement as a derived artifact of acquisition so that a one-line-corrected arm is the
  first follow-up, before any fresh test.

- **Step C's pairing is unstated.** Six reserved cases, one favorable and one contrary per family,
  against six entries, two per family. If each entry meets one case, an entry checked only on a
  favorable case cannot fail for over-generalization. Check each entry on both of its family's
  reserved cases: twelve check sessions, not six, at about 6M more ceiling.

- **A is the ordinary baseline plus the shared six-target exclusion**, not "unchanged" (§8 says
  both). State it in the protocol and in the run name. Note also that the precedent index ends
  2025-12-31 (pilot protocol), so for targets with 2026 cutoffs the exclusion of other targets'
  review history is vacuous there and only Zulip's gate does work.

### R3. The investment rule

The "stable gain" clause alone is noise-prone at three repetitions. With all three arms sharing
one per-review delivery probability `p` for a concern, the chance that it shows as a stable C gain
(`n_C ≥ 2`, `n_C > n_A`, `n_C > n_B`) is:

| `p` | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.7 |
|---|---:|---:|---:|---:|---:|---:|---:|
| spurious stable gain | 0.03 | 0.09 | 0.14 | 0.18 | 0.19 | 0.19 | 0.17 |

Simulating the whole panel under that null (six PRs, per-concern `p` drawn U-shaped, two wrong
and four valid-not-ask concerns per PR, arms exchangeable):

| `correct_ask` concerns per PR | 2 | 4 | 6 |
|---|---:|---:|---:|
| "two stable gains on two PRs in two families" alone | 0.21 | 0.50 | 0.72 |
| the whole §11 criterion | 0.05 | 0.08 | 0.09 |

Script: `/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/16f8ebab-1f89-4b8d-a315-c4cb6a312096/scratchpad/null_rate.py`
(copy it into the probe directory if the figures are kept). Two consequences:

1. The totals and share clauses carry the criterion, and they exist only once the *full* union is
   labelled. The pilot's 66-item panel is still without a response file on the branch today; this
   panel is about five times larger (§R4). Do not read the gains clause early as a signal.
2. Pre-register, per favorable target, the ask its family's entry is meant to reach (R1.4 produces
   it). Count the primary gains clause on those asks; treat other stable gains as exploratory. The
   reviewer still sees none of this; it lives in the evaluation files, as §4 already requires.

Two smaller points. The stored adjudication vocabulary is three-way
(`schema/scoring.py::AdjudicationLabel`: `correct_ask`, `wrong`, `valid_not_an_ask`); `unresolved`
is a panel response, kept by the branch's panel reader, not a store label. §10's useful-share
denominator should say it is computed from the panel responses. And since a C review will cite
entries, the blinding hides the arm label but not the condition; §10 says so, and the labeller
should be told to label the request, not the citation.

### R4. Cost, in the unit that binds

The subscription bills nothing; the primary account's five-hour and seven-day windows bind, and
it is the user's interactive account, so the batch is the user's call before it starts
(`CLAUDE.md`). Basis on disk: contract-2 Opus final reviews median 0.75-1.3M processed tokens, up
to 6.3M on a large PR; the pilot's twelve averaged 0.83M; one five-hour window holds about 19-24M.

| Part | Sessions | Expected | §12 ceiling |
|---|---:|---:|---:|
| Acquisition (packet sessions, no tools) | 6 | 2-10M | 12M |
| Reserved checks, with R2's pairing | 12 | 2-6M | 12M |
| Final reviews | 54 | 40-70M | 216M |
| Matching, two replicates over 54 sessions | — | 2-4M | 6M |
| **Batch** | | **about 45-90M, 2-4 five-hour windows** | 254M |

Add this row to §12, and the reading rule the pilot used: check the window before each block, and
an exhausted window means resume, never a model change. The human work is larger than the plan
suggests and should be estimated in hours: 18-30 source cases to assemble as packets (six entries
at two to four cases, plus six reserved), the B ancestry audit, twelve check readings, and about
300 delivered findings to label at the pilot's rate of 5.5 per review, grouped into perhaps
100-150 concerns. Order the labelling: in-family concerns on the six targets first (they decide
the gains and contrary clauses), then the full union (it decides totals and share); the decision
waits for both.

### R5. Already answered, missing from §2's table

| Record | What it says | Where it bears |
|---|---|---|
| Offered for verification, not asserted | +0.00 to +0.03 (dossiers round; stages F, G) | §8's neutral lead; R2 first bullet |
| Ask reading by family | statement/API design 0 of 18, every held sentence ignored | family 3 selection |
| Gain by census rank | past rank 100; head asks stable misses; aim at 11-50 | R2 third bullet |
| The dossiers round's own stop rule | step 3 (ask-free AP on DeepSeek) ≤ +0.05 meant "drop dossiers as a recall lever"; AP read 0.00 post-cutoff and −0.01 dev | §2 overrides this on the October 16 evidence; cite the rule it overrides |
| Ladder split of remaining misses | 4 attention/decision, 3 told-it-applies, 3 fact-or-search | the recall ceiling in R1.4 |

### R6. Corrections and implementation notes

- §4: the 19 `library_partial` cases are the `determiner` field in
  `probes/library-knowledge-2026-10-13/readings/{A,B,C,D}.jsonl`; `asks.jsonl` holds the 41 asks
  without that label.
- §8: `RetrievalGate.exclude_pr` (`src/mathlib_review/retrieval_gate.py:64`) is one integer and
  both consumers compare against it (`precedent_index.eligible_mask`, `zulip.store.gate`). A set is
  a small change at that one seam; the gate's `gate` vocabulary is closed, so add the field, not a
  new gate value (`.claude/rules/mathlib-review.md`, the closed-vocabulary entry).
- §9: `derive_context` (`analysis/sessions.py`) takes one observation per section and defaults the
  packet to `pr<N>`; a bank entry is not per-PR, so each of the six sections names its entry packet
  through `packet_id` (or `by_pr`). Arm B's sentences become observations through
  `cli probe session-import` of a hand-written producer, which keeps them in lineage without new
  code. The solo task applies no size limit to context sections (the pilot's 1,500 words was the
  producer's `output_word_limit`), so §6's word cap is checked only where the plan says, locally.
  Each section carries its own title and lead; put the neutral lead on the first and empty leads on
  the rest, or the reviewer reads it six times.
- §9: the "ordinary contract-2 solo reviewer" the pilot ran is
  `configs/knowledge_transfer/consumer_opus55_claude_sub.yaml` on the branch, which extends the
  recon validation baseline (tracked only there). Develop's nearest is
  `configs/pr_review_v5_dev_medium_opus55_contract2_claude_sub.yaml`. Pin one, with its digest, in
  the protocol; the two are not byte-equivalent.
- §12: `solo_token_cap` and `run_total_token_cap` in the `dataset` block are the ceilings the
  worker enforces on processed tokens (`orchestration/worker.py`); the pilot set 4M and 8M. The
  per-run total here is nine runs of six PRs, so 24M a run at the review ceiling.
- `docs/plans/STATUS.md` has no row for this plan; add one when Step A's deliverable lands, and
  open the probe's `PROTOCOL.md` with the `## Already answered?` section including R5's rows.

### R7. Not checked here

Whether `cli probe session-import` accepts a producer with no plan on disk (it may need a stub
plan); the exact cutoffs of the candidate targets (R1.3 asks Step A to report them); the branch's
suite after a merge into develop; and whether `report adjudication-panel` on the branch computes
the per-arm sums §10 defines or only occurrence counts. Each is an hour at most and belongs to
Step A's half day.
