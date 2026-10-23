# Review and disposition of the knowledge-transfer plan

**2026-10-23, Codex.** This records the assessment of Claude's response and preserves that
response verbatim below. The [current plan](../plans/2026-10-23-review-knowledge-transfer.md)
incorporates the decisions; this file is the review record, not a competing implementation plan.
The original draft is in `165347f2`, Claude's response in `a7138cf5`, and the theoretical companion
in `72bff55e`. No model generation, semantic judging or new usefulness assessment ran here.

## Assessment

Claude identifies real omissions: the July predecessor should be explicit, the missing input must
be concrete, retrieval must be checked rather than assumed, and a 72-session first campaign is too
large. These improve the proposal. The response also promotes several plausible diagnoses into
facts and turns development observations into numerical gates that they do not support.

The useful refinement is **using conditional knowledge to guide investigation**: independently sourced
knowledge changes what the investigator checks, and the result can change the proposed comparison
or request. A tradeoff table alone adds no demonstrated capability. A repaired construction alone
also does not decide the request. Whether this combination adds anything to ordinary investigation
remains the hypothesis; we should make it testable without declaring it a new solution.

## Decisions incorporated into the plan

| Recommendation | Disposition and reason |
|---|---|
| Name the July precedent design and Mode A's failure. | Adopt. This is a reopening with a proposed different use of cases, not a new research direction. |
| Use the 19 `library_partial` asks. | Use them as an existing development pool, alongside the already inspected cases. They are evidence that options and choices differ, not a required new 19-case campaign. |
| Make missing reasons and failed constructions concrete. | Adopt as distinct failure modes. Do not presume every decline lacks the same reason, or that a reason necessarily names a decisive executable check. |
| Read 35 places and stop below one third. | Do not adopt the gate. Sessions, asks and overlapping diagnostic pools are different units. No argument connects one third of this selected pool to the value of an autonomous method. |
| Check retrieval before launching. | Adopt a bounded source/readback and relevance check for the chosen recipe. Do not require hit@5 >= 0.5 on a different target before any experiment. |
| Replay 33066/33117 before fresh PRs. | Optional debugging only. Their construction and interpretation failures already motivate concrete requirements; another campaign there is not the default next step. |
| Stage the first campaign and account for subscription use. | Adopt. The first main pilot is at most 24 sessions; the other four PRs and second-model cell are separately justified expansions. Account availability and cost estimates must be checked at handoff. |
| Require 0/3 control versus >=2/3 treatment on two PR kinds and both matchers. | Retain as one strong historical-recovery pattern, not the only way to justify another test. It can miss a reduction in unwanted demands or a useful new request absent from historical asks. Keep matcher instruments separate. |
| Permit at most one extra finding on a no-ask PR. | Use volume as a burden warning, not a false-positive label or a universal quality threshold. Read the delivered requests under the same rubric. |
| Make this a consumer of operations increment 4. | Adopt the dependency. Reuse its episode-bound Task composition; do not build a parallel runner. The comparison-session handoff currently supplies the decision and alternatives, so autonomous target discovery is an additional study responsibility. |
| Require a second model. | Include cross-model validation before a general harness claim; stage it after a first-model mechanism signal. Different behavior on these fixtures does not disqualify Sonnet as a model. |
| Seek a new ruling about training and historical data. | Keep model weights fixed in this plan. Use independent historical decisions to infer conditional knowledge; exclude the target's outcome and discussion. This preserves the goal of general taste rather than repeating the target's historical review. |

## Corrections and limits of the evidence

**GPT stage W is a separate positive result.**
[The generation-suppression record](../../.claude/worktrees/generation-suppression/docs/plans/2026-10-06-generation-without-suppression.md)
at `d7c65fa6` explicitly reports GPT-5.5's stage W on the other 13 PRs: in-census reach
0.43 to 0.62, +0.189 on both matchers, nine asks gained and none lost, one run per condition.
It is conditional on exact convention supply and is not evidence of ask-free transfer. It is
nevertheless different from the detector pass-through result (5/13 asks and 13/14 unasked facts).
Claude's proposed correction conflates those experiments. DeepSeek's stage D is another result.
The revised plan retains the positive conditional evidence and its limits.

**The proposed 35-place denominator needs a join, not a threshold.** At 33117 there are six
assisted Opus C5/Cplus sessions; the three assisted Opus sessions at 33066 are additional. The
19 library-partial asks and ten exact-brief misses are ask-level selected pools, potentially
sharing targets with the sessions and each other. None is a random sample of prospective
opportunities. A small worked set can falsify a concrete input claim; its fraction cannot establish
that transferable knowledge exists or does not exist across the project. An absent stated reason
is also different from absence of usable library practice, technical evidence or a supported
conditional inference.

**Retrieval has two different objects.** The 43 comparison asks test finding a *library or PR
analogue* used by a maintainer. The dense precedent index returns *historical review situations*.
A relevant historical case need not be that analogue or come from its PR. The target's own
review thread must be excluded, and an alternative eligible case may supply the same useful
reason. Exact source-identity recovery is therefore not the sole relevance criterion. Report
eligibility, support, misleading analogies and query effort separately. The index's older corpus
benchmark is not validation on the proposed targets, and automatic semantic judging would not
be a CPU-only step. Do not rebuild the index as a side effect of a planning check.

**Known facts and a pointer are not the complete intervention.** The fixed-search 33117 result
establishes that all six assisted sessions made the correspondence; only one filed. Three of five
declines involved a faulty trial, while two involved no Lean attempt. The earlier successful
stand-in trial also did not guarantee filing. Those observations support requirements to repair
failed checks and compare client interfaces; they do not identify a single sufficient cause of
all declines. Counting wrapper uses or successfully calling generated declarations supplies a
fact, not a general decision rule. The two studied families' 3-4 remaining asks out of 93 bound
that narrow opportunity, not the headroom for every concern covered by a shared procedure.

**Broad negative statements exceed these runs.** The ceiling/pinpointing and decision-context
results are strong reasons against another generic brief. They do not show that every future
verification-based intervention must fail. Likewise, repeat-run overlap limits expectations of
resampling but does not make an equal-effort control unnecessary. A particular model's different
response to an oracle pointer is a limitation on cross-model extrapolation, not a reason to
exclude it from research. The long tail motivates reuse without proving that case retrieval is
the only possible architecture.

## Resulting next step

Prepare four worked choices across at least three concerns, including a justified retention of
the submitted form and a concern outside redundancy/generation. Use existing source and trace
assessments; do not commission a new census reading. Show the exact difference from ordinary
preparation, the independently eligible evidence and the observation it would lead the session
to investigate. Then produce one shared Task recipe, a local preflight and costed manual commands.

A two-PR, three-repetition paired pilot is a maximum first main batch, not an obligation. If the
specific uncertainty is use of already supplied evidence, use a clearly labeled fixed-evidence
diagnostic instead of an autonomous search campaign; do not routinely schedule both. The current
plan records what each test can answer and when to stop or expand.

---

## Original response (Claude, 2026-10-23)

Read against `develop@165347f2`, the worktree heads in section 12 (all verified by `git worktree
list`), `docs/dead-ends.md`, `docs/questions.md`, `docs/todo/README.md`, the reconstruction
`RESULTS.md`, the grounds reading with its assessment, the additions triage with its review, and
the two retrieval modules. No model ran; nothing was spent.

### The verdict in four lines

1. **The goal is right and the control is right.** A fixed method that handles more situations as
   more cases are supplied is the only shape that escapes the census tail, and the paired "same
   producer, ordinary extra work" comparator is what the Phase A review found missing.
2. **The plan is a reopening, not a new direction, and should say so.** It reopens two recorded
   entries under their own conditions. It should also cite the July design it restates.
3. **The distinct input is already known from the record.** Part A does not need an inventory: five
   of the six steps in section 4 were delivered to the strongest reviewer at two decisions and it
   declined 6 of 6. What was never delivered is the maintainers' conditional ledger with the check
   each side names, and a repaired construction. Part A should state that as the premise and
   falsify it on the sessions and asks already on disk.
4. **Part C as drafted is 72 Opus sessions on the user's interactive account, with a retrieval
   step whose instrument has never been measured on the asks it must find.** Stage it behind two
   cheap readings and state the headroom and the rules now.

### 1. What the record already says about this proposal

**It was proposed in July under another name.**
[`research/precedent-retrieval-design.md`](../research/precedent-retrieval-design.md) (2026-07-02):
"maintainer judgment is case law, not statute ... the missing piece is which principle is active
here, which is exactly what a retrieved precedent supplies". Its first use, Mode A, is a dead end:
delivery worked (47% of primed findings echoed a precedent) and transfer failed (13 against 11
covered on 41 shared PRs). It **reopens only** "with a different use of the precedent (recognition
mode, ranking), not as prompt priming" (`docs/dead-ends.md`). Section 4's use, an applicability
argument plus a checked alternative, is a different use, so the reopening is legitimate. Section 3
should carry this row; it is the closest prior result and the plan does not name it.

**It is the library-knowledge entry's own reopen condition.** The 2026-10-13 premise check found
that of 41 asks no free-reviewer session reached, the library decides 7 and for **19** "the library
points to the change but a choice remains" among its options. It stopped because "what decides
these asks is maintainers' preference among the library's options, which the library does not
record", and **reopens if** "the library is paired with a record of which option maintainers prefer
... and that pairing is tested on the 19" (`docs/dead-ends.md`;
`results/pr_review_v5/probes/library-knowledge-2026-10-13/asks.jsonl`, rows with the
`library_partial` reading). That pairing is this plan. The 19 are its premise-check set and
section 7A should use them instead of "up to six saved development cases".

**Five of the six steps were delivered to Opus, and it declined.** Step 4's C and Cplus sections at
33117 held the mechanism, the dated base-commit uses, one sentence relating the attribute to the
PR's twins, and a compiled demonstration; at 33066 the constructor's elaborated signature and the
relation. Opus 5.5 related the source to the declaration in every assisted session and filed in
**1 of 6** at 33117 (C5 0 of 3, Cplus 1 of 3) and **0 of 3** at 33066; Sonnet filed 4 of 5 at
33117 and 0 of 5 at 33066 (`RESULTS.md`, step 4 and amendment 7). Two things in that reading are
the plan's real openings:
- the declines name one side only: at 33117 the mechanism's costs (a new import, the file's
  hand-written siblings, "used in only one other file") and no cost of the hand-written form; at
  33066 the wrapper's benefit asserted and nothing counted (grounds response, §"The next steps"
  item 2);
- 3 of the 5 declines at 33117 rested on an attempt that failed for a missing import line, and
  the one session that repaired it filed (amendment 7).

**Assertion carried every positive; verification carried none.** The exact brief said "these
conventions apply here" and Claude read 0.46 to 0.74 of in-census asks. The same sentence
pinpointed at the place with a check to run, stage G, read **+0.000**, and at the 10 asks only the
exact brief reached, G's reviewer filed a different change at 6; picked from the diff without the
asks, stage F, +0.03; "offered for verification rather than asserted as applying" +0.00 to +0.03
(`docs/questions.md`, conventions; `research/conventions-dossiers-review-2026-10.md` §2.4). Section
6 is right to forbid asserting the target's conclusion, but it then places the method exactly in
the regime where nothing on record has moved a reviewer. The plan has to say where its effect
comes from instead. The grounds response gives the candidate: the reviewer **performs the check
the reason names** (counts uses at 33066, tries the client call at 33117, repairs the import) and
decides on it. That is visible in a transcript without a matcher, and it is the prediction that
separates this from the ceiling test.

**The decision-context packet is step 2 and step 3 without the alternative, and it moved nothing.**
Packets of library examples, uses, mechanisms and earlier review and Zulip decisions, gathered
without the asks, left the sketches' reach at 5/4 against 5/4 of 25 and "did not add reasons"; on
the free reviewer the packet alone lost one ask (`RESULTS.md`, decision-context round and Phase A).
Of the four target decisions, the ask-blind preparer found the deciding source at one (33066's
`mk`), missed the mechanism at one (`to_fun`), and at 43167 shipped the wrong pair of conventions
(the deciding family `inf_sup_left` was absent). So step 2 fails more often than it succeeds on
the only sample we have, and section 3's row 5 understates it.

**Retrieval of the comparable case is an unmeasured instrument.** The dense precedent index's hit@5
of 0.49 was measured on the bench's own corpus, never on census hunks
(`docs/todo/parked-corpora.md`; dossiers review §8). On the 43 agreed design-comparison asks a
name-token search from the PR's declarations found the analogue in the top ten for **0 of 43**;
unification by shape found 6 of 50 sites; **18 of 99** comparison asks have a plausible wrong
analogue, each a twin along one axis (`docs/todo/review-design-comparison.md`). The dossiers
review's step 1, retrieval as the selector over the shipped index, $0 of CPU, was registered and
**never run** (`probes/conventions-ladder-2026-10-08/README.md`: "skipped for now"). It is the
check section 7B needs before any producer searches for cases.

**What there is to transfer is bounded.** About 37% of asks state any ground; of 246 with one, a
technical fact 32%, a principle 27%, preference 16%, the scope's practice 11%
(`probes/stated-grounds-2026-10-16`). In the grounds reading, 154 in-scope asks hold 43 stated
reasons, 30 phrased to carry to another PR. The one supported reason is a cost-benefit with
conditions, not a priority: every library-side statement names a cost of the duplicate, every
local-side statement a benefit it keeps, with a checkable criterion on the benefit side (used as an
object, repeatedly: v1044, v1326, v0860). Step 3's "stated reason if present" will be absent for
most cases, and section 5 should say what the method does then.

**Headroom on the sets.** For Opus on the 93 asks of P14 and D12, the redundancy and generation
families hold 8 asks, 5 already reached, **3 remaining** (d0002, d0018, p0006), 3.2 points; the
generous envelope 4 of 93
(`research/review-design-decisions-revised-2026-10-19.md`, `audit.py`). The never-reached 37 of 93
are the population the method is for, and 34 of the free reviewer's 66 missed asks "lacked
nothing" (`probes/ask-reading-2026-10-12`). A positive Part C on six PRs can add a handful of
asks at most; the additions channel will carry most of its signal, and that channel's labels are
the ones the triage left pending.

### 2. Corrections to section 3

- Row 2, "GPT's stage W": the positive examples-and-precedence result is DeepSeek's stage D,
  +0.197 / +0.179 over three reps with the exact conventions (`conventions-ds41@18f7c3c1`);
  gpt-5.5 under the disposition paragraph filed 5 of 13 stated asks and 13 of 14 unasked facts,
  a pass-through, not a positive (`docs/dead-ends.md`, detectors).
- Add rows for: Mode A; the library-knowledge reopen condition; stage G's +0.000 and the
  assertion reading; the decision-context packet's null; the retrieval measurements above;
  "a second run of the same reviewer reaches the same asks, so resampling is not a lever"
  (`docs/questions.md`), which bounds the control; the stated-grounds shares.

### 3. Part A, rewritten as the premise check CLAUDE.md asks for

No spend, about half a day. The claim to falsify: *at the places the strongest reviewer declines
with the facts in hand, a dated maintainer reason for this kind of choice exists in the record,
the reviewer's reasoning never weighs the cost or benefit it names, and there is a check that would
settle it.* Data on disk:

| Set | Where | Already read |
|---|---|---|
| The 6 Opus C and Cplus sessions at 33117 and 33066 | `review-reconstruction` `step4/place_opus*/` | yes: one side of the ledger, no check |
| Claude's 10 exact-brief misses, 6 judged "a matter of taste" | `probes/conventions-ceiling-2026-10-04` | the grounds, not against the record's reasons |
| The 19 `library_partial` asks with the free reviewer's rows that named the topic | `probes/library-knowledge-2026-10-13/asks.jsonl`; `probes/ask-reading-2026-10-12` | no |

For each place: (i) is there a reason in the record for this kind of choice (the grounds
reading's 43; the stated-grounds probe's 246), dated before the target; (ii) did the reviewer weigh
it; (iii) does the reason name a check. **Threshold, stated now:** if a dated reason exists and was
absent from the weighing at fewer than a third of the 35 places, the knowledge is not there to
transfer, the mechanism is the decision itself, and Part C does not run. Output: the mechanism
table section 7A asks for, with the input difference named as the ledger and the repaired
construction, or the stop.

### 4. Part B, two additions

- **The retrieval check first**, the dossiers review's step 1: for each of the 43 agreed
  comparison asks and the 9 supporting PRs of the grounds reading, query the shipped index with its
  dated gate (`PrecedentIndex.eligible_mask(as_of, exclude_pr)`,
  `src/mathlib_review/retrieval/precedent_index.py:406`) from the target's hunk, and ask whether the
  maintainer's case is in the top 5; beside it, the design-comparison todo's routes (siblings,
  shape, neighbourhood, role). Threshold: recall at or above 0.5 on the 43 by any single route, or
  section 7D's first row applies before Part C, not after it.
- **The mechanism reading on the fixtures, three sessions a cell, before any fresh PR.** Replay
  C at 33117 and 33066 with the ledger and its checks added, Opus on the existing route, and read
  only whether the session performs the named check and decides on it. This is development
  material and proves no benefit; it is the cheapest falsifier of the prediction in §1, about 1-2
  five-hour windows against Part C's 6-10. If no session runs the check, Part C has no mechanism.

A-B by hand is about two days, or one with subagents at about 1-2M tokens (Probe 0's eight
briefs with audits cost 2.72M).

### 5. Part C, what to fix before it is costed

- **Cost from the record.** Six Opus C sessions were about 20M processed tokens; a dev run of 12-15
  ordinary sessions is 19-24M, about one five-hour window. Thirty-six investigating producers are
  therefore 60-120M and thirty-six consumers 50-70M: **6-10 five-hour windows on the primary token**,
  which is the user's interactive account and the only one that runs. Stage it: two PRs by three
  reps (24 sessions) first, the rest only if the mechanism reading in §4 passed.
- **State the rules now, not "before the pilot".** Registered gain: an ask reached in 0 of 3
  control sessions and at least 2 of 3 treatment sessions on both matchers, on two PRs of
  different kinds (Phase A's gate). Burden: finalized findings on no-ask PRs at most the control's
  plus one a PR (the revised decisions' guard). Mechanism: the transcript-visible check. Report
  submitted, anchored and finalized counts apart; Phase A lost 33 of 255 submissions at anchoring,
  including both occurrences of its best documentation fix.
- **Say what the control will do.** Two runs of one Opus configuration reach the same asks (7
  and 7 of 23; the misses are systematic), while four passes unioned reach 12 against 7-9 at 7.0
  findings on a control PR. So the ordinary-extra-work control gains on volume and little on asks;
  the treatment is read against it on both.
- **Second model.** The user's standing rule is model-by-harness, never one model. Sonnet is not an
  instrument here: it filed on the stated relation where Opus declined, so a Sonnet gain says
  nothing about the weighing. The free reviewer is, at $0 when `first` is free, and the same
  recipe should run there as the second cell.
- **Infrastructure, named.** The producer needs base-commit search (the route's own tools, with
  amendment 7's symlink fix), dated review and Zulip sources through the index's gate, and Lean
  checks, which `review-operations@0123f43a` serves through an MCP server. That producer is
  increment 4's live consumer, which the comparison-session handoff
  (`review-operations`, `docs/plans/2026-10-22-review-comparison-next-step.md`) already selected;
  the plan should say Part C is that increment with ask-free targets, not a parallel line. The
  reconstruction probe's subagent route is the project's route and not a private runner, if
  increment 4 is not ready.
- **Output channel.** Finalized findings, as section 8 says; the producer's notes are retained and
  never scored.

### 6. Three things for the user to rule on

- **Section 10's "learned adaptation"** is training a model, which the project's framing has
  excluded (2026-09-24, leakage proportionate to not training). Keep it as a user decision, not as
  a branch of section 7D.
- **The review corpus as the reviewer's knowledge.** On 2026-09-26 the user said asks should
  "reflect a general taste or design choice the community follows, not repeat historically asked
  reviews", and that the corpus's legitimate use is "the taxonomy of what matters, not a lookup"
  (`docs/todo/review-design-comparison.md`). Sections 4 and 5 use dated prior decisions as the
  reviewer's evidence. The guards are there (sources predate the target, the target's thread is
  excluded, the finding names its case so a wrong one is refutable), and the 2026-10-13 reopen
  condition points the same way, but the ruling is the user's.
- **The five-hour windows.** Part C's full size is a week or more of the interactive account.

### 7. The order I would run

1. Part A as the premise check in §3, with its threshold. Half a day, $0.
2. The retrieval check in §4. Minutes of CPU, $0.
3. The mechanism reading on the two fixtures, Opus, three sessions a cell. 1-2 windows.
4. Part B's four worked examples and the protocol, opening with "Already answered?" and the rows
   in §2.
5. Part C on two PRs by three reps, then the rest. 6-10 windows in all, staged.
6. Parts D and E as written, with the tuning concerns (API redundancy, generation) listed before
   C so E's held-out concern is fixed in advance.
