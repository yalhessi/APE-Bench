# What do earlier expert reviews contribute to an independent Mathlib review?

**Research assessment, 23 November 2026.** The strongest paper direction I can defend is an empirical evaluation of how much expert guidance transfers to an independent Mathlib review. The project has already retrieved earlier comments, extracted rules and adopted edits, compared designs, and tested how reviewers use the resulting evidence. In the strongest whole-PR comparison, several apparent gains have different explanations once we check the source dates, the complete submissions and the feedback that the matcher actually saw. I would give the next independent review budget to a confirmatory comparison of the best existing procedure.

The project has evidence for responsiveness to relevant information. It still needs independent evidence of transfer of judgement. That distinction is large enough to frame a paper and narrow enough to test. I would target ICML 2027, use **4 January** as the internal decision on the evidence and full draft, and keep the remaining time for criticism and revision. The official dates are **14 January 2027** for the abstract and **22 January** for the eight-page paper, both at 11:59 p.m. Anywhere on Earth. The ICLR 2027 and AAAI-27 main-paper deadlines passed in September and July respectively. [ICML call](https://icml.cc/Conferences/2027/CallForPapers) · [ICLR dates](https://iclr.cc/Conferences/2027/Dates) · [AAAI dates](https://aaai.org/conference/aaai/aaai-27/submission-instructions/)

## What the project has established

| Evidence | Implication for the paper |
|---|---|
| On 39 requests represented in the convention catalogue, Claude recovered 46–49% unaided and 74% when given the applicable conventions. The two readings are from the original blinded comparison. GPT-5.5 and DeepSeek also responded to this intervention in their own comparisons. | An expert-selected cue can change the delivered review. Selection used the target expert requests, so the cue supplied information about *which principle mattered here* as well as its content. [Exact-supply results](../../results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md) · [Cross-model synthesis](knowledge-transfer-experiment-synthesis-2026-10-23.md) |
| In July, 47% of findings written with code-similar precedents echoed a precedent. On the 41 PRs shared by the two saved reports, ordinary review covered **13/88** anchored expert comments and review with precedents covered **11/88**. Four PRs gained coverage, five lost it, and 32 had the same count. Later, selecting convention sentences from the diff moved Claude’s in-catalogue recovery about three points. With examples and a stronger instruction, Opus 5.5 rose from 48% to 67% on one matcher on the 14-PR comparison, with 5.4 versus 14.3 findings per PR. That panel included cases selected for solo misses. On the separate 12-PR comparison, gains across 47 requests were 2.1 or 6.4 points. Both intervals crossed zero. | The July result uses an earlier topical measure. The October measures count matches in the delivered review. Within each comparison, the paired results preserve both gains and losses. [July baseline](../../inputs/pr_review_v2/predictions/preds_idiom_gpt_5.2_decl_d2_target_report.json) · [July primed](../../inputs/pr_review_v2/predictions/preds_idiom_primed_gpt_5.2_decl_d2_target_report.json) · [October comparison](../../results/pr_review_v5/probes/one-reviewer-table-2026-10-10/README.md) |
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

## Which versions of historical transfer have already been studied?

| Proposed use of history | Closest completed study and what it established |
|---|---|
| Find a useful earlier comment from the current code. | At **109 locations supplied by the evaluation**, code embeddings retrieved an example judged predictive in the first five for 53 and in the first ten for 67. July also measured the effect of supplying precedents in the idiom review task on the 41 shared PRs above. October subsequently issued 21 prewritten queries on four worked choices, with follow-ups and an answer-informed control. Code-similarity search returned none of the identified review reasons on those four. Some items were missing from the index, others were in it and ranked elsewhere. The four choices came from the reconstruction panel and the person writing the queries knew the expert requests. [Known-location benchmark](../../inputs/pr_review_v2/precedent_bench/report.json) · [October source check][source-check] |
| Give the reviewer the historical code and the request together. Add the accepted edit if the request is ambiguous. | The July v4 lexical retrieval trial matched submitted code to earlier code and supplied the associated maintainer request. Relative to the same candidate pipeline without the block, one of three samples gained an issue match and none gained a resolution match. The team then built **113** linked historical situations with request and observed outcome. Its frozen search found a useful adopted source for **0/3** queries on PR 33098, and the planned generation comparison stopped. Holding the same historical code visible and hiding only its comment would be a more specific attribution control. The previous trials already tested its practical premise. [Paired retrieval verdict](../../results/pr_review_v4/audits/dev-pilot-0.8.9-vs-0.8.11-paired-three-sample-verdict.md) · [Adopted-edit study](../../results/pr_review_v4/audits/systematic-opportunities-v1-phase6-historical-offline-verdict.md) |
| Teach an applicable principle, add demonstrations or explain its exceptions. | At the expert's location, telling DeepSeek that somebody asked for a change yielded 5 or 6 passes out of 39 on the two matchers. Giving the convention and telling it the convention applied yielded 29 on both. Adding examples yielded 27 or 29. In whole review, 22 requests had the same convention sentence available in both briefs. The reviewer reached 18 with the expert-targeted shortlist and 12 with 25 diff-selected entries. Applicability cues and list length changed together. The subsequent compact/full bank and focused tests above directly examined conditional notes. All three focused PRs also belonged to both the six-PR bank and the 12-PR reviewer comparison. [Known-location experiment](../../results/pr_review_v5/probes/conventions-ladder-2026-10-08/README.md) · [Whole-review comparison](../../results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md) · [Experiment map](../../supervisor_update_2026-11/experiment-map.md) |

## What changed in the strongest independent-selection comparison?

The October comparison ran the same Opus reviewer unaided and with 25 conventions selected from the submitted diff, examples from other PRs, and an instruction to give them precedence. On the 12 development PRs, the two matchers found **five gains and two losses**, or **three gains and two losses**. All gains were on PRs 33149 and 33421. Across those 12 PRs the model submitted 126 findings unaided and 301 with guidance. The comparison scored 117 and 204 after applying its prespecified first-20 limit per PR. [Matched requests][dev-outcomes] · [Session counts][dev-counts] · [Matching code][first-twenty]

| Change identified by both matchers | What the actual submissions show |
|---|---|
| Gain on 33149, reuse Mathlib's Parseval theorem | Both reviewers explicitly requested the same replacement. It was the **21st** unaided finding and the **17th** guided finding. The scored difference is entirely explained by the delivery limit. A separate gain on this PR was a substantive difference in the recommendation. The guided review opened by asking to close the PR for a rewrite, while the unaided review asked for changes to the axioms and definitions. [Unaided submission][parseval-solo] · [Guided submission][parseval-guided] |
| Gain on 33421, extract two recurring limit arguments into reusable lemmas | The unaided reviewer explicitly identified the duplication, searched for an existing lemma and stopped. The guided reviewer proposed extracting new lemmas and checked the change. Its selected principle explicitly recommends extracting an independently useful fact. Both accompanying examples were written **24 and 26 February 2026**, after the target's **31 December 2025** cutoff. This is a real difference in the recommendation on an already noticed issue. The package changed the instruction, rule and examples together. The separate request to generalize the constant 2 was missed in both reviews. [Unaided notes][extraction-solo] · [Guided notes][extraction-guided] · [Text shown][extraction-section] · [First dated comment](../../data/pull_requests/pr/35464/review_comments.jsonl) · [Second dated comment](../../data/pull_requests/pr/35534/review_comments.jsonl) |
| Loss on 33294, simplify a proof using dot notation | The guided reviewer wrote the exact requested proof at position **26**, beyond the same limit. The unaided review included it at position 9. [Guided submission][dot-guided] · [Matched requests][dev-outcomes] |
| Loss on 33285, replace a tactic proof with a short term | The unaided reviewer checked and requested the working qualified term. The guided reviewer tried an unqualified version that failed, then offered a smaller simplification. Both matchers credited partial coverage. This loss arose during construction and checking. [Unaided notes][term-solo] · [Guided notes][term-guided] |

The other two gains were matcher-dependent. One was a compound request about a PR's provenance and its axioms. The other was a rename where one reading credited a descriptive replacement and the other required the expert's specific name. These cases matter for reporting an issue separately from its requested resolution. The historical scores measure the original 20-finding contract. The traces identify how specific differences arose. A new uncapped aggregate would require scoring all the raw submissions under that contract. [First matcher][dev-m1] · [Second matcher][dev-m2]

**How much of that guidance existed when the PR was reviewed?** I joined every example listed in the delivered briefs to its GitHub event time and used the reviewed head's commit time as the exclusive cutoff. The example builder excluded the evaluation PRs by identity and chose examples by a fixed seed. Each count below is a comment shown to one target PR. This check covers the comments quoted in the briefs. Dating the evidence used to induce each convention is a separate requirement for a historical-transfer claim. [Example selection][build-examples] · [Example identities][examples] · [Reproduce the date audit][date-audit]

| Scored panel | Example appearances at or after the target cutoff | PRs receiving at least one |
|---|---:|---:|
| Eight validation PRs | 215 / 367 | 8 / 8 |
| Six later PRs | 2 / 269 | 2 / 6 |
| Twelve development PRs | 218 / 536 | 12 / 12 |

There is a positive case even among the four later PRs whose quoted examples all predate review. On PR 42814 the guided review requested moving repeated implicit arguments into a shared Lean `variable` declaration, the same change the maintainer requested. Both matchers credited it and neither credited the paired unaided review. All 45 examples supplied there were earlier. That is one concrete transfer candidate on a PR selected for a prior solo miss. The dates across the other panels limit the chronological interpretation of their scores. They do not tell us what caused any individual gain. [Later-panel verdicts][later-outcomes] · [Guided review][binders-guided] · [Panel selection](../../results/pr_review_v5/probes/one-reviewer-table-2026-10-10/README.md)

## What earns the next six weeks?

I would write the empirical paper around **how much of the apparent benefit of project-specific guidance survives review of independent PRs using only knowledge available at the time**. The prior studies already establish a large response to expert-targeted cues and some substantive changes under automatic selection. They also show how later examples, selection for earlier misses, comment volume and output order can change the interpretation. Repeating a code-search exercise or designing a comment-reveal prompt has a lower return than resolving those ambiguities for the strongest existing system.

The one comparison I would fund is a deliberate replication. Freeze a convention catalogue and its demonstrations from a dated source period, including the examples from which its rule text was learned. On fresh later PRs, run the same solo reviewer with or without the existing diff-selected guidance. Keep the review open-ended and match the tool access, route, resources and submission contract. Evaluate the entire submitted list and the prefix delivered at the fixed comment budget. Report paired expert-issue and resolution recovery, gained and displaced requests, burden on PRs with and without recorded requests, and uncertainty by PR. A historical nonmatch has unknown usefulness. This comparison estimates the effect of the complete guidance procedure. An effect specific to a particular example would require further evidence. [Paired review procedure](../../results/pr_review_v5/probes/one-reviewer-table-2026-10-10/run_claude_pair.sh) · [Atomic judge](../../src/mathlib_review/judge/protocol.py) · [Request matcher](../../src/mathlib_review/judge/ask_matching.py)

## What would justify an ICML paper

Other groups already retrieve review examples, summarize project rules, and evaluate AI reviews against human feedback. RAG-Reviewer retrieves code–comment exemplars, LAURA adds context and review guidance, and SWE-PRBench measures recovery of human-flagged issues. Atlassian has compared historical comments and diffs directly. A particularly close November 19 preprint by Asada and colleagues compares an unedited source thread with an extracted rule on 20 constructed changes and tracks which rules resulted in production comments. A rule-versus-thread ablation or a count of cited precedents would have substantial overlap. [RAG-Reviewer](https://arxiv.org/abs/2506.11591) · [LAURA](https://arxiv.org/abs/2512.01356) · [SWE-PRBench](https://arxiv.org/abs/2603.26130) · [Atlassian’s comparison](https://www.atlassian.com/blog/development/improving-code-reviewer-with-pr-context) · [Asada et al.](https://arxiv.org/abs/2611.25918)

MathlibPR predicts merge outcomes and audits some explanations. ProofJudge scores declaration quality and compares initial and accepted versions. Our opportunity is to establish which information in a dated expert review can transfer to a naturally occurring review and at what stage it changes the feedback. Demonstrations can help through cues about the topic and task even when their labels carry little information. Mathlib gives us independent expert requests and a way to check the technical plausibility of proposed changes. Claims about other communities would require data from them. [MathlibPR](https://arxiv.org/abs/2605.07147) · [ProofJudge](https://arxiv.org/abs/2608.20432) · [Min et al. on demonstrations](https://aclanthology.org/2022.emnlp-main.759/)

- **A methods paper** becomes credible if a source-selection and delivery method improves final expert-resolution recovery over matched solo review on fresh PRs. Show losses as well as gains and concentration by family, maintainer or period.
- **An empirical evaluation paper** becomes credible if the comparison gives a precise estimate of what the complete guidance procedure adds or loses on independent PRs under a realistic reading budget. A narrow estimate near zero would be informative alongside the measured response to expert-selected cues. ICML explicitly recognizes evaluations and informative negative results. [Contribution types](https://icml.cc/Conferences/2027/ContributionTypes)
- **Defer the submission** if the strongest result still depends on familiar targets, an expert selecting the relevant issue, or an interval wide enough to include practically important gains and losses.

## Where the six weeks go

| Window | Work and decision |
|---|---|
| **Nov 23–29** | Write the results from the completed studies. Establish from source manifests which rule text and examples can be frozen before a fresh target period. Quantify coverage and cohort size with metadata. If a usable historical resource and independent cohort cannot be assembled within the schedule, defer the methods claim. |
| **Nov 30–Dec 6** | Estimate attainable precision from paired development PRs and available compute. Set the smallest change that would alter the research conclusion, the maximum reading budget, and a decision on whether the sample can distinguish it. Fix both conditions and the independent target order before looking at any target outcomes. |
| **Dec 7–13** | Assemble workspaces and validate both output paths on development cases. Freeze the date-eligible resource, model route, prompts, issue and remedy scoring, and treatment of failed runs. Reserve the remaining compute for independent PRs. |
| **Dec 14–20** | Run one frozen paired comparison if justified. The existing 60-PR test design has 50 main-stratum and 10 AI-stratum PRs to report separately. Use a source period that ends before the chosen test cohort starts. If only a suffix of the sealed order's date range is eligible, predeclare the date filter, retain the sealed order within it and report the resulting population and precision. Exclude related PRs from source material and record possible model-training exposure separately. [Evaluation-set design](../todo/eval-set-selection.md) |
| **Dec 21–Jan 3** | Finish blinded matching and the per-PR analysis. Show uncertainty, disagreements, failed transfers, and the strongest case against the proposed interpretation. Prepare the dated cases, eligible-source manifests, prompts, model and tool identities, final findings and evaluation recipe for anonymous reproduction. Complete the eight-page draft. |
| **Jan 4, then Jan 14 and 22** | Decide which claim the results support on Jan 4. Use the remaining days for a critical read, revisions and the artifact. Submit an abstract on Jan 14 and the paper on Jan 22 if the claim survives. |

**Capacity matters.** Today’s read-only workspace preflight found **48/60 validation workspaces ready**, 11 awaiting assembly and one missing its base. For sealed test it found **0/60 ready**, with all 60 bases available. The release is drawn and locked. Workspace assembly, reference preparation, and matching still need scheduling. The October ordinary and full-bank runs used 39.49M and 43.30M processed tokens for 18 reviews each. At that observed rate a single paired pass over 50 PRs would be roughly **230M processed tokens before matching and source preparation**. That is a planning extrapolation from six selected PRs. Profile the chosen route on validation before buying the full comparison. Fund independent PRs first and use repetitions to check instability on a subset. [Recorded resources][bank-resources] · [Test configuration](../../configs/pr_review_v5_eval_2025_06_2026_03_v1.yaml)

Reuse the existing whole-PR task registry. The focused branch contains the fix that lets the reviewer search symlinked library directories. Pin that search behavior on both sides. The October evidence gives no reason to put a new comparison agent, policy training or another source index on the six-week schedule. [Review task registry](../../src/ape/tasks/lean_tasks/formal_math/review/__init__.py) · [Earlier design alternatives](review-harness-design-alternatives-2026-11-12.md)

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
[dev-outcomes]: ../../results/pr_review_v5/probes/one-reviewer-table-2026-10-10/match_D12b/unblinded.json
[dev-counts]: ../../results/pr_review_v5/probes/one-reviewer-table-2026-10-10/match_D12b/session_stats.json
[dev-m1]: ../../results/pr_review_v5/probes/one-reviewer-table-2026-10-10/match_D12b/matches.1.json
[dev-m2]: ../../results/pr_review_v5/probes/one-reviewer-table-2026-10-10/match_D12b/matches.2.json
[first-twenty]: ../../src/mathlib_review/analysis/probes.py
[parseval-solo]: ../../results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33149/T1/findings.json
[parseval-guided]: ../../results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33149/TA1/findings.json
[extraction-solo]: ../../results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33421/T1/notes.md
[extraction-guided]: ../../results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33421/TA1/notes.md
[extraction-section]: ../../results/pr_review_v5/probes/ask-reading-2026-10-12/ap_sections/D12_33421.md
[dot-guided]: ../../results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33294/TA1/findings.json
[term-solo]: ../../results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33285/T1/notes.md
[term-guided]: ../../results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33285/TA1/notes.md
[examples]: ../../results/pr_review_v5/probes/conventions-ceiling-2026-10-04/examples_apt.json
[build-examples]: ../../results/pr_review_v5/probes/conventions-ceiling-2026-10-04/build_context.py
[date-audit]: ../../results/pr_review_v5/probes/one-reviewer-table-2026-10-10/inspect_example_dates.py
[later-outcomes]: ../../results/pr_review_v5/probes/one-reviewer-table-2026-10-10/match_P14_post/unblinded.json
[binders-guided]: ../../results/pr_review_v5/probes/postcutoff-2026-09-29/pr42814/TA1/notes.md
