# PR review v6 implementation handoff

## Review of the fresh-package proposal, 25 November 2026

**Recommendation under discussion.** Use the existing named reviewer and registered matcher. Change how a whole-PR run selects its episode and reaches its accepted submission. The pilot branch at `478e6f27` already archives that submission before downstream processing and can prepare another reading with generation disabled. The walkthrough branch at `f106cb82` already previews requested episodes from a release containing only the visible input. Neither branch alone provides both behaviors. The focused suites passed on their respective tips (18 pilot tests, 4 walkthrough tests).

A replay of both saved 42184 submissions exposed a choice for the regression test. With the seal, two reference requests and request-only rubric fixed, the historical solo loader rendered each finding's severity as `"advisory"`. Projecting the same saved findings into the named review archive's target, claim and requested-change fields rendered severity as `null`. Those were the only differences in the final judge prompts, for the ordinary submission with one finding and the guided submission with two. Pin the named-review prompt before changing its run path. Retain the old projection when reproducing its measurements. This replay checked the scorer inputs and did not measure an effect on scores. [Saved submissions](../../results/pr_review_v5/probes/convention-scope-2026-11-24/full_tool_reviews.json) · [Matcher renderer](../../src/mathlib_review/judge/ask_matching.py)

The first implementation check would combine those existing behaviors in the named command. Preview and run a whole-PR design without specialist inputs, preserve message and tool grants, and recover the accepted review after an interruption. The historical obligation judge and verified reports still need placement and legacy joins. Keep those callers available. Title reconstruction and multi-finding credit are separate changes to the experimental inputs and the reading instrument, respectively. [Episode and source identities](../guides/review-episodes.md)

## Original implementation proposal

**Proposed 25 November 2026.** Start a fresh review package at `src/pr_review_v6/`, with its own entry point and tests. The first deliverable is one complete review that another researcher can reopen and score. Given a compiling Mathlib PR as it stood at a named review round, what would a maintainer ask the contributor to change or explain, and why? A reviewer may submit several requests, one, or none. This is a proposed v6. The source and saved runs inspected here implement v5. [Project task](../PROJECT-STATUS.md) · [Extracted episode walkthrough](../guides/review-episodes.md) · [Released systems and source traces](../research/released-reviewers-for-v6.md)

A new worker should be able to follow three things from the command line to disk, namely **which revision the reviewer received, what it submitted, and which requests a particular reading credited**. The history of the real review also tells us **what the contributor did next**. That history belongs to the episode and can be studied even when nobody runs a model. We have already observed all four on PR 42184.

| At PR 42184 | What survives into v6 |
|---|---|
| At review time | Round 1, merge base `5b3f719b`, head `c5474cb4`, a review-time-verified description and a stored title marked unverified, and a patch adding `tprod_nonneg` in `Order.lean`. The reviewer may inspect the library at that revision. |
| In the generated submission | The guided reviewer asked first to remove `[L.NeBot]`, then to add `HasProd.nonneg`. Their submitted ranges are 239–244 and 239–243. Its verified output had zero entries. A reader of the submission sees both requests in order. |
| In the historical review | Two maintainer comments on line 243 ask for those two distinct actions. Each has a source identity. A reading can credit the missing theorem before such a declaration exists at the reviewed head. |
| In the historical response | `66d50e17` is the identified next head. Its patch is absent from the local source store. A later compare at `b00f1b70` shows both changes and another edit in `Finprod.lean`. A researcher may cite that later endpoint. The real contributor saw the maintainer comments. |

[Episode, events, revisions and archived submission](../guides/review-episodes.md#read-one-extracted-case) · [Submitted, reviewed and verified counts](../../results/pr_review_v5/probes/convention-scope-2026-11-24/full-tool.md)

For implementation, start with [Worker 1 and the dependency order](#worker-packets-and-dependencies). The first integration checkpoint is a second reading of a saved review with generation disabled.

## Why this design

| Candidate architecture | What we would borrow | Decision and local check |
|---|---|---|
| A single reviewer invocation returns a durable review. PR-Agent captures structured output before its inline renderer mutates it. Danger can reroute and sort inline failures. reviewdog explicitly completes empty output. | Give the reviewer one submission operation. Make its accepted text and order independently readable. | **Build this first.** Test empty, unplaceable and jointly supported requests. On 42184 changing the display or verification policy must leave both submitted requests available. |
| A policy-driven review pipeline. Anthropic's plugin scopes, summarizes, delegates and validates. Mozilla can retrieve examples, filter candidates and add a scope review. | Name the complete review strategy and record what it actually shows the reviewer. Earlier examples are a promising separate treatment. | **Keep this choice with the reviewer design.** On four Mathlib PRs exhaustive specialist fanout reached 2/10 reference obligations and solo reached 4/10. The historical result does not select a universal winner. A baseline that requires assignments or candidate validation would already test a different procedure. |
| An evidence model for the whole PR history. GitHub tracks review threads and their locations across revisions. Mozilla's matcher links comment IDs. | Preserve revision and event identities and link findings when reading them. | **Build concrete relations demanded by the cases below.** A common graph of declarations, obligations, worker assignments and candidate patches would require a target for a theorem that has yet to be written. Either putative design must account for the two same-location requests on 42184 and the location-free answer on 41930. |

An evaluation can otherwise silently bind to a different producer. In Mozilla's released notebook an intermediate generator returned a pair. An offline replay of its adapter and count with zero and three generated comments reported two both times. APE has a different instance of the same design hazard in 42184's two submitted versus zero verified requests. The first scorer acceptance test therefore changes the number of *submitted* findings while keeping every downstream projection unavailable. The research note links the pinned code, release versions, fixture and limits of the replay. [Released implementation traces](../research/released-reviewers-for-v6.md) · [Mathlib fanout record](../dead-ends.md) · [Previous aggregate anchoring audit](../questions.md)

**Where the old plan stage belongs.** Commit `ce976804` introduced CLI `plan` as the dry run for `run`, to render and price the configured work without calling a model. Both paths resolve the v5 agenda. Execution seals a run plan, while the dry run reports it. The dry run itself does not send the reviewer a planning prompt. The agenda, enabled evidence, task renderer and reviewer-specific instructions can determine which work actually gets done. V6 needs a reproducible run description and a preview of it. Have one resolver feed preview and execution, with the same episode, rendered messages and tool grants. The first baseline requires no intermediate agenda, specialist assignments or model-authored plan. The reviewer remains free to plan its own investigation. [CLI dispatch](../../src/mathlib_review/review/cli.py#L611) · [Runner](../../src/mathlib_review/review/runner.py#L2097)

## The minimum data contract

These are ownership boundaries and wire fields. Workers can use ordinary records and existing storage. A record type alone does not require a new service, database or CLI command.

| Record and owner | Required facts and operations |
|---|---|
| **Review episode**, owned by extraction | Stable episode ID includes repository, PR, round and reviewed head. Preserve merge base, full SHAs, changed paths, diff bytes/digest and title/description with source and visibility information. Resolving a human shorthand must yield exactly one episode. Several rounds can review the same head. Keep AI authorship and unknown provenance in selectable cohort metadata, included by default. Expose only the visible projection and pinned checkout to the reviewer. |
| **Historical review and response**, owned by extraction for research | Keep the round boundary, its resolution method, source event IDs and original payload locators. Identify each reference request and its supporting comment/thread context. Preserve author replies and acknowledgements as events. For subsequent code evidence record the actual pair of revisions, merge bases, evidence locator and availability. Label immediate, later and missing observations explicitly. A link from a request to an edit or reply records the researcher's interpretation and cited evidence. Several links in either direction are valid. |
| **Reviewer invocation**, owned by generation | Record the episode, immutable design revision, exact rendered initial messages, configured tool grant, material actually delivered or omitted, patch/workspace identity, model, scaffold, settings and limits, and sample/attempt locator. Keep subsequent tool use in the trace. Expose the initial input independently of what the reviewer later consulted. Use APE's run identity and accepted attempt. |
| **Submitted review**, owned by the task | One accepted author-facing review per successful sample, with optional overall message and ordered findings. A finding preserves the requested change or question and rationale in the reviewer's words, any offered edit, and original locations (revision/side/path/range as supplied). A finding ID is the immutable submission occurrence plus its zero-based ordinal. Keep an artifact digest as an integrity check. Identical text in two runs still has two occurrences. A valid empty review is observable. Invalid or unavailable attempts retain their run status. |
| **Reading**, owned by evaluation | Bind a reading to the submission occurrence and digest, episode, reference edition, rubric, reader/replicate and the author-visible fields considered. Save one assessment per selected reference request, with verdict, rationale and zero or more supporting finding IDs. If the rubric permits support from the overall message, identify its quoted passage separately. Count the request once even when two findings support it jointly. Preserve each finding's inverse links, including those cited by no request. A receipt compares expected and completed assessments, records failures, and distinguishes an empty reference set. |

A source location serves a different lookup from a historical match. Keep the submitted range unchanged. When a researcher needs code resolution, qualify the lookup by revision and side and return zero or more locations with the method used. Referenced unchanged code, a proposed new declaration, and a PR-wide question all have legitimate review text. Leave the location unresolved when the source cannot support one. Repacking the same targets on PR 33145 changes four specialist work units to one. A specialist's assignment, if that strategy is later studied, explains what the specialist saw. Repacking must preserve the episode, finding IDs and all reading links. [Work-unit replay and source owners](../guides/review-episodes.md#what-a-finding-can-be-mapped-to)

For example, the following is an **abbreviated new reading**, with the common submission ID and replicate shown once. On PR 34091 the two original readers each credited five of six requests. Their structured field exported one index for `v0110`, while both notes cite indices 1 and 2 for the two docstrings. A new, explicitly attributed reading of the saved text can encode that joint evidence. A historical import preserves its one recorded index and the original note.

```text
submission X1 on episode 34091, six findings, zero-based indices
new reading   reference   verdict     supporting ordinals
              v0105       no          []
              v0106       reached     [5]
              v0107       reached     [5]
              v0108       reached     [5]
              v0109       reached     [0]
              v0110       reached     [1, 2]
reading total             5 / 6       cited {0,1,2,5}, uncited {3,4}
```

Removing finding 2 for a new reading removes the submitted correction for the second docstring. A same-topic mention or the first finding alone cannot supply that text. Uncited findings may still be useful advice. Assess usefulness or false positives under a separately defined rubric. [Accepted X1](../../results/pr_review_v5/probes/construction-demo-2026-09-29/pr34091/X1/findings.json) · [Blind codes](../../results/pr_review_v5/probes/construction-demo-2026-09-29/blinding_SEALED.json) · [Reading 1](../../results/pr_review_v5/probes/construction-demo-2026-09-29/match/matches.1.json) · [Reading 2](../../results/pr_review_v5/probes/construction-demo-2026-09-29/match/matches.2.json)

## First two commands

**Proposed interface.** Start from a topic worktree based on current `develop`. Use the current checkout's sources with the shared interpreter. Worker 1 supplies the example fixture editions named below. Worker 2 supplies the first named reviewer, `solo-v6.1`. It receives the author text and patch, the pinned tree and generic read/search and Lean inspection/check operations. For this first historical baseline, render text marked review-time verified and record omissions with the field's provenance. On 42184 this delivers the description and withholds the unverified title. A run that deliberately shows current unverified values needs a different design revision. Its instruction asks what it would request and why. Workers record the concrete grant. Earlier v5 solo runs included review-specific declaration search and edit verification, so label this as its own baseline. Any restoration of those operations requires a defined change of design or a verified equivalence. [Baseline and strategy definitions](2026-11-25-four-review-strategies.md) · [Existing Lean toolkit](../../src/ape/toolkits/execute/lean)

```bash
export PYTHONPATH="$PWD/src:$PWD"
review=(ape/bin/python -m src.pr_review_v6)
case_id='leanprover-community/mathlib4:42184:round1:c5474cb4a68a515228b49225b38a2507264f91f7'
release=inputs/probes/probe-2026-07-08-v1
fixtures=tests/pr_review_v6/fixtures

# Preview. Adding --execute runs the resolved invocation. Provider calls are user-run.
args=(run --release "$release" --episode "$case_id" --reviewer solo-v6.1 --run-name v6-42184-a)
"${review[@]}" "${args[@]}"
"${review[@]}" "${args[@]}" --execute

# Import and validate a completed reader's assessments locally. Both consume the same run.
# The judgment files must identify this particular submission and its actual digest.
"${review[@]}" score --of v6-42184-a --reference "$fixtures/42184/requests.json" \
  --rubric "$fixtures/rubrics/action.json" --judgments readings/42184-action.json
"${review[@]}" score --of v6-42184-a --reference "$fixtures/42184/requests.json" \
  --rubric "$fixtures/rubrics/topic.json" --judgments readings/42184-topic.json
```

Here `readings/*.json` are outputs of an independent reader of that run. The local integration test generates a deterministic review and uses judgments for that known review. For a user-run live reading, Worker 4 supplies a pinned reader profile for the same command.

```bash
"${review[@]}" score --of v6-42184-a --reference "$fixtures/42184/requests.json" \
  --rubric "$fixtures/rubrics/action.json" --judge action-reader-v1 --execute
```

Blind the reviewer identity, supply source context specified by the rubric, and retain the seal to the original findings. Scoring can occur later with the generator disabled. A new case varies the episode and run name. A new reading varies the rubric, reference or reader while fixing the submission. Preview and execute must resolve the same input fingerprint even across fresh processes.

## Worker packets and dependencies

The parent issue tracks the complete researcher workflow. [Review a frozen Mathlib PR and reread its accepted submission (#3)](https://github.com/yalhessi/APE-Bench/issues/3). The packets below are independently assignable sub-issues with their acceptance contracts. Worker 1 fixes the shared fixture and wire examples first. Workers 2, 3 and 4 can then proceed in parallel against them. Worker 5 integrates their public behavior. Designate one owner for the command dispatcher and have the others deliver the operations it calls. Use the linked evidence from the walkthrough worktree even if a fixture has yet to land on the worker's base.

### 1. Freeze the public contract and one episode

Own the new package entry point, shared records and test fixtures. Read the released visible episode JSON through a narrow adapter. Verify identity and diff digest, including the release writer's encoding. Use the existing PR store and release as source artifacts. Freeze examples for a nonempty submission, a successful empty one, an unavailable attempt and the research-side records. [Release writer](../../src/datasets/pull_requests/projections/episodes.py) [Worker ticket #4](https://github.com/yalhessi/APE-Bench/issues/4)

**Acceptance.** A fresh process previews 42184 using only the visible input and reviewed tree. Perturb the hidden comments, next head and later patch and require identical rendered messages and tool permissions. Exercise the granted search/read tools in the reviewer workspace to verify that shared project results, hidden references and later Git objects are inaccessible. Reject an ambiguous round, mismatched patch or unavailable promised snapshot. Check AI and unknown cohort inclusion.

### 2. Run one whole-PR reviewer

Own the fresh task, reviewer definition and APE adapter. Register explicitly at the new entry point. Reuse the existing orchestrator, task storage, scaffold, execution limits and reviewed-workspace preparation. Verify the workspace key (merge base plus patch), build status of changed Lean modules and recorded actual head. The task's validated result holds all author-facing fields. Record its accepted attempt via APE's sample product reader. [Orchestrator](../../src/ape/orchestration/orchestrator.py) · [Reviewed build](../../src/ape/toolkits/execute/lean/core/build_manager.py#L387) · [Accepted products](../../src/ape/orchestration/products.py) [Worker ticket #5](https://github.com/yalhessi/APE-Bench/issues/5)

**Acceptance.** Through `run` with a local deterministic scaffold, submit two findings, then an empty review in another run. Simulate an interrupted or invalid attempt followed by a successful retry. Preserve attempt identity, message, ordering, edits and submitted ranges. Distinguish an offered edit from a patch tried privately during verification. The existing 33145 ticket supplies the coordinated-edit regression. [Submitted edit case](https://github.com/yalhessi/APE-Bench/issues/2) PR 28649 provides a saved positive control for an accepted empty review with an overall message. [Archived empty submission](../research/pr-review-harness-refactor-comparison-2026-11-24.md) Starting scoring in another process retrieves the accepted product. A stale base-only Lean build fails the declared profile.

### 3. Reconstruct the historical review

Own the research-only reference and outcome adapter. Follow source event locators through the raw store. Record the round's resolution method, requests and replies, and before/after comparisons at explicitly named endpoints. Preserve edits outside the originally reviewed file. Start with existing release data and the two demonstrated comparisons. [42184 and 41930](../guides/review-episodes.md) [Worker ticket #6](https://github.com/yalhessi/APE-Bench/issues/6)

**Acceptance.** On 42184 return two requests with distinct IDs at the same historical line. The immediate patch is missing, the later pair shows the companion and weakened assumption. On 41930 resolve the maintainer's rationale question, the author's answer and the acknowledgement with no next head. Running either reconstruction works without a generated review.

### 4. Score the accepted review

Own `score`, including reading identity, versioned blind projection, assessments, inverse lookup and coverage. Reuse generic APE execution for a model judge. Let a local reader supply judgments against the same contract. Use historical matcher exports as fixtures for the loss in the single-index representation. [Historical caller](../../src/mathlib_review/review/study.py) · [Projection](../../src/mathlib_review/analysis/matching.py) · [Single-index verdict](../../src/mathlib_review/judge/ask_matching.py) [Worker ticket #7](https://github.com/yalhessi/APE-Bench/issues/7)

**Acceptance.** The 34091 reading above round-trips both directions. Reject foreign or out-of-bounds IDs and duplicate or missing expected cells before reporting a complete score. Zero/three submitted findings give zero/three with projections disabled. Distinguish an incomplete execution, a successful empty review, and a completed reading with zero eligible requests. The last has an undefined reach denominator.

### 5. Prove the handoff through the CLI

Own cross-packet integration and the researcher runbook. Drive the two commands in separate processes from an isolated output directory. Supply a deterministic fixture reviewer and reader for tests through the same operations as the live profiles. Verify no fresh-domain source imports the historical reviewer or invokes its agenda, projection or finalizer. Do not copy the v5 runner or introduce a second scheduler, result store, checkout cache or global strategy registry. [Checkout and pilot procedure](../guides/checkout-and-runs.md#preparing-a-pilot-or-evaluation) [Worker ticket #8](https://github.com/yalhessi/APE-Bench/issues/8)

**Acceptance.** Reopen one saved review twice with different rubrics and generation disabled. Confirm the same input digest, accepted attempt, ordered finding IDs and unchanged review bytes across both readings. In a fixture where the reviewer asks only to weaken the hypothesis, credit that request alone even though both references point to the same line. Removing anchoring and repacking work units leaves the submitted text intact. Report cases, statuses and denominators alongside any resulting aggregate.

## Integration and first comparison

**A constraint on fresh source.** Importing the generic APE task base in this checkout also loads old review modules through eager built-in task registration. A local probe registered a fresh task successfully through the generic registry. Worker 5 should check direct imports and exercise the fresh CLI with the old review entry points made to fail if called. Requiring zero historical modules in the interpreter would require a separate APE registration change. Shared framework imports are sufficient for this milestone. [Task package initialization](../../src/ape/tasks/__init__.py) · [Lean base](../../src/ape/tasks/lean_tasks/base.py)

**Ready to hand to a researcher** means the offline run and both readings pass, the round and revision evidence can be opened from the result, and the runbook gives a complete user-run command for the first live generation and semantic reading. Before interpreting quality, hold episode set, source cutoff, model, scaffold, limits and reading protocol fixed across arms. Use familiar cases above to accept the implementation. Reserve independent episodes for testing whether review quality improves.

The next design worth testing is optional search over a dated collection of earlier review comments. On the same cases, compare solo with that single added grant, preserve the evidence actually consulted, and score both submissions under the same reader protocol. Later, an automatically selected convention list and an explicitly reference-informed diagnostic can share the same historical collection. The latter consults target expert feedback during preparation and must be reported separately. Promote another strategy or a shared abstraction only when its own caller and a discriminating case exist. [Shared history decision](../adr/0001-shared-history-for-review-comparisons.md) · [Four named strategies](2026-11-25-four-review-strategies.md) · [Prior experiments and stopped approaches](../dead-ends.md)
