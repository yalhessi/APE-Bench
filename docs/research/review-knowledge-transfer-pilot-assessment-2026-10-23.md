# Knowledge-transfer pilot: independent reading and next investment

**Assessment, 2026-10-23.** Reviewed `knowledge-transfer@1474776d`, including the protocol,
preparation notes, all 66 finalized findings, matcher verdicts, channel accounting and persisted
session outcomes. This follows the [implementation review](review-knowledge-transfer-implementation-review-2026-10-23.md).
No model sessions or judging were launched. Usefulness labels remain pending.

**Follow-up after reviewing the earlier transfer experiments:** the
[historical synthesis and revised next-run recommendation](knowledge-transfer-experiment-synthesis-2026-10-23.md)
supersedes section 6.3's suggestion to make a targeted aesop evidence-supply probe the next main
experiment. Earlier source-supply diagnostics already establish conditional uptake. The proposed
next comparison tests independently acquired, reusable knowledge against solo review and the
existing terse resource. The recommendation against expanding this unchanged pilot still stands.

**Recommendation:** do not expand the current conditional-preparation method or make it the
default reviewer. Keep the shared Task/session implementation. Finish the existing usefulness
assessment before claiming a quality improvement, but do not make all further research wait for
it. If we pursue this direction further, the next test should change the decision-relevant
knowledge available to a reviewer and measure whether it changes the comparison correctly.
Another general instruction to search, compare and consider contrary evidence has a weaker
claim on our time after this result.

The result is informative about this candidate procedure. It does not establish that conventions,
knowledge transfer or review-grounded learning cannot improve reviewing.

## 1. What was compared

Both conditions used an Opus 5.5/xhigh preparation session, followed by a separate ordinary
Opus 5.5/xhigh final reviewer on the contained Claude Code route. The reviewer received the
preparation's notes, with the same 1,500-word allowance and the same final-review contract.

- **Ordinary preparation:** investigate the PR as a careful reviewer, using the available tools.
- **Conditional preparation:** explicitly recover dated reasons and library practice, establish
  correspondence, investigate consequences and contrary evidence, and record a comparison.

Both had access to the same sources and tools. Ordinary preparation could already retrieve
precedents, compare alternatives and compile edits. The intervention was the procedure, rather
than access to a new knowledge resource.

There were two PRs, three repetitions per condition, and two stages per repetition: **12
preparations and 12 final reviews**. This is a comparison with ordinary additional preparation.
There is no final-review-only control, so it does not establish whether either two-stage method
improves on a solo reviewer at a useful resource tradeoff.

The artifacts live on the experiment branch, currently in
`.claude/worktrees/knowledge-transfer/`. The primary record is the
[pilot's results](../../.claude/worktrees/knowledge-transfer/results/pr_review_v5/probes/knowledge-transfer-2026-10-23/RESULTS.md),
alongside its `PROTOCOL.md`, `eval/MECHANISM.md` and `eval/SOURCES.md`. Final outputs are
`results/pr_review_v5/runs/kt_review_{ordinary,conditional}_rep{1,2,3}/findings.jsonl` in that
worktree.

## 2. The measured outcome

Historical recovery uses **ask-match/2-task**, question-form rubric `d1889a8bf62d`, seal
`5a13fdcc5378`, finalized findings, four agreed raw asks, and two matcher repetitions. Both
matchers agree on every verdict. Each entry below counts independent final reviews reaching an
ask, out of three in its condition.

| Historical ask | Ordinary | Conditional |
|---|---:|---:|
| 36784: consider `aesop safe apply` for the new rule | 0/3 | 0/3 |
| 37352: rename to `isClosed_setOf_convexOn` / `concaveOn` | 0/3 | 0/3 |
| 37352: clarify the module title refers to the set of functions | 0/3 | 0/3 |
| 37352: use `ContinuousConstSMul` and drop the scalar topology | 3/3 | 3/3 |

For each repetition, combining its two PRs yields **1 of 4 asks in both conditions**. Mean,
union and stable recovery therefore coincide within each condition. One ordinary review gets a
partial match on the aesop ask by proposing a rule-set change; it does not propose `safe`.
The four asks are not four large populations, and repeated sessions do not add independent PRs.

| Quantity | Ordinary | Conditional |
|---|---:|---:|
| Finalized findings, 36784 | 9, 7, 9 | 7, 7, 6 |
| Finalized findings, 37352 | 4, 4, 3 | 3, 4, 3 |
| Finalized findings, total | 36 | 30 |
| Preparation tokens | 8,597,180 | 10,490,549 |
| Final-review tokens | 4,844,919 | 5,053,238 |
| Main tokens, total | 13,442,099 | 15,543,787 |

Conditional preparation used about **16% more total processed tokens**, and delivered six fewer
findings, without improving historical recovery. Fewer findings might mean less burden or lost
useful coverage; the count does not decide which. About two thirds of all main tokens went to
preparation. That makes evidence of incremental value especially relevant before keeping either
preparation stage in a default harness.

I checked the current measured path through the shared readers: both preparation producers have
6/6 readable observations; every final-review run has successful coverage of both PRs; all
12 note bodies appear in their respective consumer's actual initial prompt, unchanged apart from
outer whitespace. The canonical finalized outputs contain 66 findings. The channel accounting
reports a one-to-one submission/finding mapping throughout. The old export/completeness review
findings do not invalidate these measured outputs.

## 3. What the concrete cases teach us

### A. A better-supported conclusion can still be the same conclusion

On 37352, all conditional preparations found `isClosed_setOf_map_smul`: a library theorem in
the same role, requiring only `ContinuousConstSMul`. This is a substantive role analogue, and
the final findings use it to explain why the stronger assumptions are unnecessary.

But ordinary preparations reached the same requested change from the proof's fixed scalars,
`Continuous.const_smul` and the instance graph. The conditional method improved the account of
the reason without recovering an additional ask. That is evidence of successful investigation,
but not evidence that this investigation procedure adds review capability here.

### B. The aesop miss concerns which question was asked of the evidence

Conditional preparation 2 on 36784 observed that the new rule matches only
`IsStrictlyPositive ↑(u : Aˣ)`, and that sibling rules use `safe`. Its conclusion addressed
whether the rule belongs in the default rule set or `CStarAlgebra`. The maintainer instead asked
why the rule was probabilistic rather than `safe`.

These are different choices. Evidence that a rule matches narrowly can bear on both, but a
justification for its rule-set membership does not settle the safety of its application. Calling
this simply a refusal to file would miss the failure: the requested alternative was never
properly formulated. No downstream anchoring repair can recover it.

This is also more specific than saying the model had the complete deciding reason. It noticed
relevant facts; we have not established that it understood their consequences for Aesop's eager,
non-backtracking safe rules. The pinned Aesop README explains that distinction. Source-specific
operational knowledge may still be missing even when a source analogy and several true facts
are present.

The historical follow-up also matters: the maintainer says, "I trust whatever way you end up
deciding for the `aesop` rule." Recovery measures whether the reviewer raises that question. It
does not prove that retaining `90% apply` is technically wrong or unacceptable.

### C. The theorem-name miss is a genuine competing-analogue case

The preparations considered `isClosed_setOf_*`, but also found `isClosed_monotoneOn` and its
siblings: the same kind of order property of functions, with the same set-closedness statement
shape, without `setOf`. The reviewers retained the submitted spelling or left the matter
unresolved.

I would qualify the results write-up's description of this as "judgment is wrong." It is a
historical disagreement with a plausible reason. Neither a larger count of `isClosed_setOf_*`
names nor the target maintainer's later request establishes a general rule for choosing the
right analogue before review. This case needs independent evidence about naming intent or a
better model of project preference, if it is to become actionable knowledge.

The module-title ask was absent from all preparation notes and final findings. That is a
different failure: no proposal was developed for that semantic mismatch. It cannot be explained
by the same claim that all misses were considered and rejected.

### D. Correctly cited evidence can be transferred incorrectly

There is an additional concrete error in conditional final review 1 of 37352,
`finding:2ba73574295d554c900d91c5`. It asks for:

- `instContinuousSMul_left : ContinuousSMul Mᵒᵈ X` to become unprimed;
- `instContinuousSMul_right : ContinuousSMul M Xᵒᵈ` to become primed.

That reverses the convention established by the directly visible `ContinuousConstSMul` pair:
the action **on** the dual is unprimed, and the action **by dual scalars** is primed. The other
conditional repetitions give that correspondence correctly. The error is already in
preparation 1's source account and survives into the final request.

This is an artifact-specific technical observation, not a replacement for the blinded human
panel. Its research significance is broader: citation provenance does not guarantee preservation
of the relation being transferred. A count of sourced claims, or a ledger declaring
"observed/inferred," will not detect a reversed correspondence by itself.

## 4. What remains unknown about usefulness

Most delivered concerns overlap between conditions: dot-notation regressions, redundant
assumptions, the unfinished `rpow_sqrt` migration, the `_of_nonneg` rename, proof simplifications,
the weaker continuity assumption, instance names and the unused scope opening.

The treatment-only proposals I found were dropping one redundant named autoparam argument in
36784 and switching to `public section` in 37352. Each appears in only one conditional final
review. They might be worthwhile, but they are a much narrower prospective gain than the method's
broader ambition. Conversely, all three ordinary reviews flag the abstraction-breaking `.mp`
proof of `Units.isStrictlyPositive_iff`, versus one conditional review. A smaller output is not
automatically a better output.

The frozen usefulness panel has all 66 findings and no submitted response files at this review.
It can still change the investment decision. We should preserve its agreed rubric and full-panel
reading rather than retrospectively call off-gold proposals either false positives or successes.
Repeated concerns should be compared as concerns, while keeping materially different fixes
separate: the reversed instance rename is exactly why one family label cannot automatically be
propagated to every occurrence.

For later protocols, reconsider treating the loss of a `valid_not_an_ask` finding as a burden in
itself. Removing a true but unworthy comment may improve a reviewer. That issue does not rescue
this pilot's historical-recovery result or justify changing its registered criterion afterward.

## 5. The compiler failure limits the result, but does not demand a full rerun

On 37352, all **24 edit checks across 12 sessions** returned `environment_failure`: the launch
lacked `ELAN_HOME`, and the default elan home lacked the required toolchain. Both methods were
tested without the compiler on that PR. On 36784, the 118 checks comprise 82 compiled outcomes
and 36 compile errors. I reproduced these counts from persisted successful attempts.

Equal failure preserves the comparison under that degraded environment. It does not establish
what the methods would do with functioning verification: the conditional procedure might depend
on it differently. The branch now contains a toolchain preflight refusal and corrected launch
instructions; this assessment did not launch a repaired model run.

I would not repeat all twelve 37352 sessions merely to complete the intended matrix. Its missed
asks concern a name and a title, while the assumption weakening was already found by every
review. Working compilation could affect other findings and their usefulness, so that inference
is bounded, but there is no concrete reason yet to expect it to reverse the research decision.
Keep these runs marked as lacking verification, and require a functioning check on each target
toolchain for the next experiment.

The source audit also has a bounded interpretation: explicit maintainer attributions were found
in the tools' returned results. That supports their provenance; it cannot prove that latent
model memory played no role. Both targets are inside the reviewer's training window.

## 6. What I would do next, in priority order

### 1. Close this candidate's expansion decision; retain the foundation

Do not launch the four-PR expansion, a second-model replication of this unchanged method, or a
larger conventions/retrieval platform because the trace looks principled. Keep ordinary review
as the reference and conditional preparation as an experimental recipe. The reusable session
binding, tool grants, handoff, completeness checks and canonical evaluation output retain their
value independently of the prompt's result.

The usefulness panel can reopen this decision if it reveals a concrete improvement. It is not
necessary to withhold the current recommendation until every label arrives, or to block unrelated
harness work on those labels.

### 2. Finish the existing usefulness comparison

Label the frozen panel under `v5-adjudication/1`, inspect the actual changes behind any claimed
gain or loss, and apply the existing criterion. This uses existing runs and tests whether there
is a reason to continue that historical recovery missed. It is a bounded completion task,
not a new model campaign or another corpus-wide audit.

### 3. If continuing knowledge transfer, test a change in knowledge content

The next useful question is:

> Can an independent source teach a reviewer a decision it currently gets wrong, including when
> the same apparent reason would not justify that decision?

The aesop example is a suitable **development diagnostic**, because it identifies a concrete
missing distinction. Use its original visible code, the relevant operational semantics and
eligible independent examples of safe and unsafe application. Do not supply the target review
comment, tell the model to choose `safe`, or count success on this now-familiar PR as fresh
validation. First establish that the independent material actually supports a discriminating
comparison; if it merely repeats the current notes, skip the run.

For one bounded diagnostic, keep the reviewer and its ordinary instructions fixed; vary access
to that independent decision-relevant material. Reuse the existing Task/session recipe. Record
whether it identifies the correct alternative, preserves the correspondence, investigates the
relevant consequence and delivers a justified request. Include a contrary case where the
tempting change should be rejected, so a pass-through rule cannot count as success.

This changes the supplied knowledge rather than adding another generic comparison prompt. It
tests use conditional on supplied evidence, not autonomous retrieval. Only a useful result would
justify testing an unchanged procedure and knowledge representation on an untouched related
case, then deciding whether acquiring more such knowledge is worth building for.

### 4. Let that result decide the larger investment

If independent evidence changes choices correctly, the promising resource is a growing set of
review decisions with their applicability conditions and contrary cases. New concerns enter as
data consumed by the same Tasks; no detector or runtime branch is required per convention. Text
retrieval over review reasons could then have a clear consumer and a measurable purpose.

If the model still makes the same mistakes with the relevant material explicitly available,
building a larger index has no demonstrated benefit for those mistakes. Park this intervention
or test a substantive change in the decision model, rather than produce more sourced narratives.
This does not close other review-knowledge designs; it makes the next investment depend on an
observed capability instead of on the appeal of the representation.

The unifying lesson is that a small harness and a rich knowledge resource remain compatible.
This pilot does not yet show that the proposed procedure turns a richer account of the evidence
into better review decisions. That conversion is the next capability to earn, before expanding
the surrounding machinery.
