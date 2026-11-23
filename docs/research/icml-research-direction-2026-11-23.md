# What do earlier expert reviews contribute to an independent Mathlib review?

**Research assessment, 23 November 2026, revised after checking the comparison experiments.** The question I would pursue is whether earlier reviews supply information that lets a reviewer independently raise a concern or request a change that a Mathlib expert actually raised. The first version of this assessment made choosing between two supplied designs the first two weeks of work. That priority gave too little weight to the experiments that already put concrete alternatives and decision evidence in front of reviewers. The immediate investment is to establish where the strongest observed historical signal came from and whether it can be obtained from the submitted PR alone.

The project has evidence for responsiveness to relevant information. It still needs independent evidence of transfer of judgement. That distinction is large enough to frame a paper and narrow enough to test. I would target ICML 2027, use **4 January** as the internal decision on the evidence and full draft, and keep the remaining time for criticism and revision. The official dates are **14 January 2027** for the abstract and **22 January** for the eight-page paper, both at 11:59 p.m. Anywhere on Earth. The ICLR 2027 and AAAI-27 main-paper deadlines passed in September and July respectively. [ICML call](https://icml.cc/Conferences/2027/CallForPapers) · [ICLR dates](https://iclr.cc/Conferences/2027/Dates) · [AAAI dates](https://aaai.org/conference/aaai/aaai-27/submission-instructions/)

## What the project has established

| Evidence | Implication for the paper |
|---|---|
| On 39 requests represented in the convention catalogue, Claude recovered 46–49% unaided and 74% when given the applicable conventions. The two readings are from the original blinded comparison. GPT-5.5 and DeepSeek also responded to this intervention in their own comparisons. | An expert-selected cue can change the delivered review. Selection used the target expert requests, so the cue supplied information about *which principle mattered here* as well as its content. [Exact-supply results](../../results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md) · [Cross-model synthesis](knowledge-transfer-experiment-synthesis-2026-10-23.md) |
| Directly supplying code-similar historical comments produced visible echoes in 47% of primed findings, with 13 versus 11 covered on 41 shared PRs. Later, selecting convention sentences from the diff moved Claude’s in-catalogue recovery about three points. A stronger ask-blind system with examples did improve Opus 5.5 on the 14-PR comparison, from 48% to 67% on one matcher, while findings rose from 5.4 to 14.3 per PR. The panel included cases chosen for solo misses. On the separate development comparison, the gain across all 47 requests was 2.1 or 6.4 points depending on the matcher. Both intervals crossed zero. | Relevance, preselection of misses, baseline strength, and willingness to emit comments can each change the result. Ordinary Opus 5.5 on the same route is the historical baseline to beat. [Precedent study](knowledge-transfer-experiment-synthesis-2026-10-23.md) · [Paired table](../../results/pr_review_v5/probes/one-reviewer-table-2026-10-10/table.txt) · [Development replication](../../results/pr_review_v5/probes/one-reviewer-table-2026-10-10/README.md) |
| Six selected PRs received ordinary review, a compact bank, or a full bank derived from earlier reviews. Thirty requests scored across three repetitions per condition gave **32, 31, and 37 reached out of 90 request-by-run observations**, with **165, 158, and 168 final comments**. Both matcher readings agree on every reached decision. The full bank’s five extra hits were one indentation request twice and one dot-notation request three times. All three prespecified design concerns were missed in every arm. The source discussions were earlier and disjoint, but the researchers chose their search prompts knowing the target distinctions. | A small, real change in final feedback is visible. It provides little evidence for steering the intended design decisions. The six PRs and the old source packets are development material. Repetitions establish behavior on those PRs. [Saved matches][bank-matches] · [Final output counts][bank-counts] · [Source selection][selection-note] |
| On PR 33421 a maintainer suggested extending a theorem about the constant 2 to a parameter greater than 1. All six focused Opus reviews constructed a compiling parameterization and preserved the special case. Without the note, two of three recommended a change, one full match and one partial. With the note, zero of three did. On PR 33294 the note surfaced the requested namespace in two of three runs, and both declined it. On PR 33098 the focused question was about tagging a lemma, while the missed request was about using automation to simplify a proof. | These are three different failures. One concerns choosing among available alternatives, another concerns both discovery and choice, and the third exposes a badly posed question. Measuring final recommendations alongside what the reviewer actually built makes the distinction observable. [Submitted answers][focused-answers] · [Full focused results][focused-results] |

Earlier architecture work explains the opportunity cost. Lead and solo reviewers found complementary issues, but the lead cost more per hit on the 12-PR diagnostic. A preference selector with tool access and compilation struggled to distinguish maintainer requests for proof simplification, duplication, and generality. Four of seven conclusions from a 60-PR analysis of coverage failed their tests on 973 PRs. The project already has machinery for real reviewed snapshots, executable alternatives, blinded matching, and a strong solo reviewer. Another broad decomposition, filing-threshold sweep, or model leaderboard would consume the time needed for an independent test of historical judgement. The original topical judge, the atomic issue/resolution judge, and later request matchers have different units and rubric versions. Their numbers belong in their original comparisons. [Lead/solo comparison](ab-heldout12-obligation-spine.md) · [Selector study](selector-upper-bound-2026-06.md) · [973-PR replication](pipeline-overfit-2026-09-replication.md) · [Measurement audit](project-assessment-2026-11-12.md)

## What the reviewer can actually retrieve

I checked the 24 historical PRs used to *induce* the six knowledge entries. Their manifest cites 97 inline review comments, 13 review bodies and 14 issue comments on those PRs. All **124** IDs resolve in the local PR store with timestamps before the bank cutoff. The current 43,736-row precedent index contains **47 of the 97 inline comments**, or **47 of the 124 cited discussion items**. It contains at least one cited item on **16 of 24 PRs** and every cited GitHub discussion item on **4 of 24**. Commits, linked PRs, Zulip and the twelve old bank-check cases are outside this count. None of the 24 source PRs is on the index’s exclusion list. [Source manifest][selection] · [Index manifest][index] · [Store layout](../../src/datasets/pull_requests/store.py)

For example, on PR 31307 the reviewer first asks the author to consider registering lemmas with Lean’s `grind` tactic. In a PR-level comment they explain why repeated use alone is insufficient. In line comments they ask to omit one registration and extend another to its related lemmas. None of the five cited items for this source PR appears in the precedent index. A reviewer given only “register repeatedly used lemmas” would miss precisely the distinction the expert made. [Original discussion in time order][grind-source]

These counts establish availability on a deliberately curated set. One comment can suffice to explain a decision, and the presence of a record says nothing about its rank for a new query. The bank experiment delivered its notes by another route. A previous four-choice diagnostic returned zero eligible review reasons through code-similarity search, including misses on material present in the index. The raw discussions make it possible to check whether a missing piece of evidence is retrievable before committing to another delivery experiment. [Retrieval diagnostic][source-check] · [Index construction](../../src/mathlib_review/retrieval/precedent_index.py)

## What the comparison experiments tell us

The rationale for supplying two feasible designs was experimental control. Holding the alternatives fixed lets us ask whether an earlier expert decision changes the model’s preference. The focused generality case motivated that question because the model could already construct the change. That observation identifies a disagreement after construction. It gives us no estimate of how often ordinary reviewers reach that point or how often an example would resolve the disagreement. An earlier reviewer’s observation that a proof’s use of square roots needlessly restricted an inequality, for instance, does not decide whether the constant in a different theorem merits generalizing. [Historical discussion][generality-source] · [Focused answers][focused-answers]

| Attempt | What happened in the delivered review |
|---|---|
| Give a reviewer an independently produced design sketch and dated context. | On eight selected PRs with 25 reference requests across six of them, some sketch proposals reached the author-facing output. Zero requests met the registered gain criterion of being missed by all three historical controls and recovered in at least two of three treatment runs on both matchers. [Reconstruction results][reconstruction] |
| Supply a concrete alternative and its connection to the target. | On PR 33117, telling Sonnet that `@[to_fun]` could generate the handwritten lemmas moved recovery from 0/5 to 4/5. Opus understood the connection in all three initially assisted runs and filed it in 0/3. With repaired search and added adoption evidence it filed the change in 1/3. This is evidence for a conditional, model-specific benefit. [Evidence-supply and follow-up runs][reconstruction] |
| Ask a preparer to find dated grounds, establish the correspondence, consider contrary evidence, and compare alternatives. | Across two PRs, ordinary and comparison-based preparation led to the same one of four expert requests being recovered in each of three repetitions. Both matchers agree. Both arms had access to the same sources, and compilation was unavailable on one PR. [Final matches][pilot-matches] · [Pilot conditions and limits][pilot] |

The sharpest example is PR 36784, where compilation **did** work. All six preparations inspected the same `aesop` automation rule and considered which rule set should contain it. The maintainer asked whether the rule could be marked safe. One preparation even found that neighboring rules were safe and that this rule matched a restricted expression, then used those facts to reason about rule-set membership. Giving the reviewer “safe or unsafe?” as its choice would supply the missing insight. On PR 33066 the failure was different. Opus recognized that a new constructor duplicated an existing one, then favored keeping the named interface. Both failures produce a missed expert request, but only the latter is a disagreement over a choice the reviewer actually formulated. [Recorded preparations][pilot-mechanism] · [Constructor comparison][reconstruction]

## What to do first

Keep the **review task open-ended**. Use the existing matched reviews to identify which information changed the author-facing feedback. In the convention study, the same underlying sentence was available for 22 requests in both conditions. The reviewer reached 18 when shown the few conventions selected using the expert’s requests and 12 when those entries appeared among 25 selected from the diff. The comparison also changed the contextual cue about applicability and the length of the list. It supports the value of knowing what bears on a PR. It leaves the separate effect of an earlier expert’s judgement unresolved. [Original decomposition](../../results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md)

Start from the recorded gains **and** losses and the existing per-request readings. For each, check whether ordinary review had already raised the expert’s question, entertained the requested change, or lacked both. Then check one fact the old analysis could not establish from a matching score: whether a dated, unrelated review retrievable from the visible target actually supplies the missing consideration. A reason found by searching for the known expert answer is a diagnostic example. A reason the ordinary reviewer already used gives little motivation to deliver it again. Report when neither explanation can be recovered from the trace. [Existing per-request readings](../../results/pr_review_v5/probes/ask-reading-2026-10-12/readings/aggregate.md) · [Source-selection history][selection-note]

If this yields a repeatable opportunity across independent development PRs, test it with the same ordinary reviewer and final submission contract. One possible contrast holds the retrieved source and its pre-review code fixed, then reveals or withholds the earlier expert comment. Freeze source selection from visible inputs. Let both reviewers choose what to inspect and what to say. Track whether the comment introduced a previously absent concern, supplied a concrete remedy, changed the recommendation on a concern already present, or displaced a baseline hit. Compare against unassisted solo review before making an end-to-end performance claim. This contrasts expert input within real review and can still fail if independently retrievable examples rarely carry the necessary information. A fixed-pair replay warrants a small diagnostic only if multiple unprompted reviews already formulate both relevant alternatives and earlier threads contain evidence that would distinguish them.

Use the finalized review to measure recovery of the expert’s specific issue and requested resolution separately. Preserve the scope of requests spanning siblings, abstentions by the matcher, and disclosures of what the expert considered optional or later withdrew. Additional unmatched findings have unknown value. Report comment volume, resource use, baseline losses, both matcher readings and paired uncertainty by PR. PRs without recorded requests still count toward reading burden. [Atomic judge](../../src/mathlib_review/judge/protocol.py) · [Request matcher](../../src/mathlib_review/judge/ask_matching.py)

## What would justify an ICML paper

Other groups already retrieve review examples, summarize project rules, and evaluate AI reviews against human feedback. RAG-Reviewer retrieves code–comment exemplars, LAURA adds context and review guidance, and SWE-PRBench measures recovery of human-flagged issues. Atlassian has compared historical comments and diffs directly. A particularly close November 19 preprint by Asada and colleagues compares an unedited source thread with an extracted rule on 20 constructed changes and tracks which rules resulted in production comments. A rule-versus-thread ablation or a count of cited precedents would have substantial overlap. [RAG-Reviewer](https://arxiv.org/abs/2506.11591) · [LAURA](https://arxiv.org/abs/2512.01356) · [SWE-PRBench](https://arxiv.org/abs/2603.26130) · [Atlassian’s comparison](https://www.atlassian.com/blog/development/improving-code-reviewer-with-pr-context) · [Asada et al.](https://arxiv.org/abs/2611.25918)

MathlibPR predicts merge outcomes and audits some explanations. ProofJudge scores declaration quality and compares initial and accepted versions. Our opportunity is to establish which information in a dated expert review can transfer to a naturally occurring review and at what stage it changes the feedback. Demonstrations can help through cues about the topic and task even when their labels carry little information. Mathlib gives us independent expert requests and a way to check the technical plausibility of proposed changes. Claims about other communities would require data from them. [MathlibPR](https://arxiv.org/abs/2605.07147) · [ProofJudge](https://arxiv.org/abs/2608.20432) · [Min et al. on demonstrations](https://aclanthology.org/2022.emnlp-main.759/)

- **A methods paper** becomes credible if a source-selection and delivery method improves final expert-resolution recovery over matched solo review on fresh PRs. Show losses as well as gains and concentration by family, maintainer or period.
- **An empirical evaluation paper** becomes credible if a controlled study on independent PRs isolates the information responsible for a gain, or measures a meaningful limit on transfer with adequate precision. The known contrast between an expert-selected cue and independently selected material motivates that study. ICML explicitly recognizes evaluations and informative negative results. [Contribution types](https://icml.cc/Conferences/2027/ContributionTypes)
- **Defer the submission** if the strongest result still depends on familiar targets, an expert selecting the relevant issue, or an interval wide enough to include practically important gains and losses.

## Where the six weeks go

| Window | Work and decision |
|---|---|
| **Nov 23–29** | Use the existing per-request readings and final reviews to trace gains and losses. Check whether pre-review, target-blind searches surface earlier discussions that supply a material consideration the ordinary reviewer missed. Record missing, contradictory, and already-known evidence. Draft the task and closest-prior-work sections. |
| **Nov 30–Dec 6** | If that check identifies a recurring source of transferable information, test one delivery contrast in ordinary open-ended review on development PRs. Otherwise, keep the empirical question about the expert-selected cue, assess whether it can be tested precisely on independent PRs, and release the reserved harness budget. |
| **Dec 7–13** | Freeze the supported claim, source cutoffs, comparison conditions, sampling frame and reading rule. Use development variation to size a fresh paired estimate. Prepare the whole-PR workspaces only if that comparison is warranted. |
| **Dec 14–20** | Run one frozen, paired whole-PR comparison if warranted. Start from the existing 60-PR test design with 50 main-stratum and 10 AI-stratum PRs reported separately. Fix any budget-limited subset from the sealed order before seeing outcomes. A test PR from June 2025 cannot receive a bank compiled through December 2025. Filter original events, linked evidence and any derived summaries by each target’s review cutoff, exclude target, related PRs and source duplicates, and record model-training exposure separately. Preserve retrieval misses and failed runs in the accounting. [Evaluation-set design](../todo/eval-set-selection.md) |
| **Dec 21–Jan 3** | Finish blinded matching and the per-PR analysis. Show uncertainty, disagreements, failed transfers, and the strongest case against the proposed interpretation. Prepare the dated cases, eligible-source manifests, prompts, model and tool identities, final findings and evaluation recipe for anonymous reproduction. Complete the eight-page draft. |
| **Jan 4, then Jan 14 and 22** | Decide which claim the results support on Jan 4. Use the remaining days for a critical read, revisions and the artifact. Submit an abstract on Jan 14 and the paper on Jan 22 if the claim survives. |

**Capacity matters.** Today’s read-only workspace preflight found **48/60 validation workspaces ready**, 11 awaiting assembly and one missing its base. For sealed test it found **0/60 ready**, with all 60 bases available. The release is drawn and locked. Workspace assembly, reference preparation, and matching still need scheduling. The October ordinary and full-bank runs used 39.49M and 43.30M processed tokens for 18 reviews each. At that observed rate a single paired pass over 50 PRs would be roughly **230M processed tokens before matching and source preparation**. That is a planning extrapolation from six selected PRs. Profile the chosen route on validation before buying the full comparison. Fund independent PRs first and use repetitions to check instability on a subset. [Recorded resources][bank-resources] · [Test configuration](../../configs/pr_review_v5_eval_2025_06_2026_03_v1.yaml)

Reuse the existing whole-PR task registry if the intervention advances. The focused branch contains the fix that lets the reviewer search symlinked library directories. `develop@c5bdbd0a` lacks that fix, so pin the same working search route for both arms. Reserve policy training for evidence that sufficiently many independent historical decisions exist but in-context transfer is limiting. Broader multi-agent coordination would become relevant if the measured loss is failure to discover or preserve a cross-declaration choice. Neither investment is needed to run the first comparison. [Review task registry](../../src/ape/tasks/lean_tasks/formal_math/review/__init__.py) · [Earlier design alternatives](review-harness-design-alternatives-2026-11-12.md)

### Reproducing the source availability count

Run this read-only check from the repository root with the local data store. It uses the original bank selection at `bbba4f24`, the three types of same-PR GitHub discussion items, and the original acquisition cutoff. It measures record availability before ranking. The outcome counts above use the two saved matcher readings and the finalized findings. This assessment introduced no new reviewer runs or semantic labels.

```python
import json
import subprocess
from collections import Counter
from pathlib import Path

selection_path = "results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/selection.json"
selection = json.loads(subprocess.check_output(["git", "show", f"bbba4f24:{selection_path}"]))
cases = [c for e in selection["entries"] for c in e["cases"] if c["role"] == "induction"]
source_prs = {case["pr"] for case in cases}
cutoff = selection["K"]
indexed = set()
with Path("data/pr_review_v5/precedent_index/meta.jsonl").open() as rows:
    for line in rows:
        row = json.loads(line)
        if row["pr_number"] in source_prs and row["created_at"] < cutoff:
            indexed.add((row["pr_number"], row["comment_id"]))

totals = Counter()
for case in cases:
    pr = case["pr"]
    cited = 0
    found = 0
    for endpoint in ("review_comments", "reviews", "issue_comments"):
        ids = set(case["comment_ids"].get(endpoint, []))
        if not ids:
            continue
        with (Path("data/pull_requests/pr") / str(pr) / f"{endpoint}.jsonl").open() as lines:
            rows = (json.loads(line) for line in lines)
            records = {row["id"]: row for row in rows if row["id"] in ids}
        assert ids == records.keys()
        assert all((r.get("submitted_at") or r["created_at"]) < cutoff for r in records.values())
        totals[endpoint] += len(ids)
        cited += len(ids)
        if endpoint == "review_comments":
            found += sum((pr, event_id) in indexed for event_id in ids)
    totals.update(cases=1, indexed=found, any_present=int(found > 0), all_present=int(found == cited))
print(totals)
```

[selection]: ../../.claude/worktrees/reusable-review-knowledge/results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/selection.json
[selection-note]: ../../.claude/worktrees/reusable-review-knowledge/results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/SELECTION.md
[index]: ../../data/pr_review_v5/precedent_index/manifest.json
[bank-matches]: ../../.claude/worktrees/reusable-review-knowledge/results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/eval/match_report.json
[bank-counts]: ../../.claude/worktrees/reusable-review-knowledge/results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/eval/export.json
[bank-resources]: ../../.claude/worktrees/reusable-review-knowledge/results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/eval/resources.json
[focused-answers]: ../../.claude/worktrees/focused-application/results/pr_review_v5/probes/focused-application-2026-10-26/eval/generality/answers.json
[focused-results]: ../../.claude/worktrees/focused-application/results/pr_review_v5/probes/focused-application-2026-10-26/RESULTS.md
[grind-source]: ../../.claude/worktrees/reusable-review-knowledge/results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/recipe/packets/acquire/e3/sources/S1.md
[generality-source]: ../../.claude/worktrees/reusable-review-knowledge/results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/recipe/packets/acquire/e5/sources/S1.md
[source-check]: ../../.claude/worktrees/knowledge-transfer/results/pr_review_v5/probes/knowledge-transfer-2026-10-23/source_check/RESULTS.md
[reconstruction]: ../../.claude/worktrees/review-reconstruction/results/pr_review_v5/probes/review-reconstruction-2026-10-19/RESULTS.md
[pilot]: ../../.claude/worktrees/knowledge-transfer/results/pr_review_v5/probes/knowledge-transfer-2026-10-23/RESULTS.md
[pilot-matches]: ../../.claude/worktrees/knowledge-transfer/results/pr_review_v5/probes/knowledge-transfer-2026-10-23/eval/match/unblinded.json
[pilot-mechanism]: ../../.claude/worktrees/knowledge-transfer/results/pr_review_v5/probes/knowledge-transfer-2026-10-23/eval/MECHANISM.md
