# Run a named whole-PR reviewer directly on a review episode

**One implementation ticket.** A researcher selects a reviewed revision, runs `solo-v1` or `pr-search-v1`, and reads the accepted review against the expert requests. The reorganization belongs in the existing named command. Its first success is a review of PR 42184 that can run from the visible episode and be read again after generation has been disabled. [Worker ticket #9](https://github.com/yalhessi/APE-Bench/issues/9) · [Design decision](../adr/0002-run-named-reviewers-on-episodes.md)

## Follow one review

| Research operation | Its input and result | Existing owner |
|---|---|---|
| Extract the episode | The repository, PR, round and reviewed head identify the visible author text, merge base and patch. The pinned checkout supplies library context. Expert feedback, replies and later revisions are research-side records. | Release episode projection and PR store. [Trace through 42184 and 41930](../guides/review-episodes.md) |
| Run a reviewer design | A visible episode and a named design determine the first message, tools, workspace and limits. A successful sample yields the review as submitted to the contributor, including the overall message, ordered findings and original locations. | `review/reviewers.py` on the pilot branch resolves the design. APE executes the task. `analysis/submissions.py` checks the accepted attempt and archives its result. |
| Compare with expert feedback | A saved submission, reference and reading policy determine the blinded judge input. Multiple designs can be read together. Each reading can be reproduced from its inputs. | The existing `score --of` command, named submission projection and registered matcher. [Reading workflow](../../results/pr_review_v5/probes/convention-scope-2026-11-24/reproduce-review-reading.md) |

The unnecessary dependency is in the **second row**. The pilot runner chooses eligible PRs through work units, builds an agenda and continues into anchoring after capturing the accepted review. The walkthrough already selects whole-PR episodes and builds their task data directly, although it still creates an agenda record. Combine these behaviors where the named command dispatches a review. Specialist assignments, verified reports and the historical obligation judge retain their existing execution paths. [Historical placement and scoring consumers](../guides/review-episodes.md#what-a-finding-can-be-mapped-to)

## Implementation sequence

1. **Establish the baseline on a develop-based topic worktree.** Integrate the named-command implementation and prerequisites from `convention-scope-pilot-20261124@478e6f27`. Take the episode selection, `review_task_data` and relevant tests from `f106cb82` on `whole-pr-walkthrough`. The two lines diverge at `baea9011` and both edit `review/runner.py`. Resolve the overlap by exercising the named command. Before changing its route, capture the initial message, tool schemas and final matcher prompt for the fixed fixtures below.
2. **Give the named command a direct path to acceptance.** Resolve exactly one episode for the requested PR and head. Fail explicitly on a missing or ambiguous match. Use the same resolved task data for preview and execution. Use the existing APE orchestration, reviewed build, input pins, cutoff, execution limits, concurrency guard, audit and resume logic. Keep the accepted archive as the result of named generation. Trace `submissions.capture` as part of this change. It currently reads the legacy `run_plan.json` for the design and search-index pins. Supply the same checks from the named run's recorded inputs and keep existing archives readable. End the named run at capture. The specialist scheduler and legacy finalization have their own callers.
3. **Prove it through the researcher's commands.** Use the local deterministic provider in `tests/mathlib_review/test_named_reviewers.py`. Extend the existing tests at that boundary. Run a new process for scoring with generation disabled. Make the specialist agenda builder, anchoring and finalizer raise if the named route invokes them. Exercise the historical anchoring and pairing tests separately. Finish by updating the existing checkout/run guide in the implementation branch.

## Acceptance cases

| Case | Observable result |
|---|---|
| A release containing only `input/episodes.jsonl` | Preview and run 42184 at `c5474cb4` with ordinary runtime resources and the pinned Mathlib workspace available. The initial message and grant match the named baseline. Run the same check for search with its pinned history available. Search adds only the existing precedent tool. No derived work-unit file, change graph, or expert feedback is needed for generation. |
| A completed review and an interruption | Reopen the same accepted attempt after interruption, without a second model session. Preserve the ranges, order and overall message. An accepted empty list, a nonempty list containing a PR-wide question, and a failed attempt have distinct observable outcomes. A second launch that claims an active name and an archive with altered contents must be rejected. |
| Read the saved review twice | Hold the reference, blind labels, order and policy fixed for each before/after comparison. Require identical final matcher messages under the existing request and question policies respectively. The ordinary 42184 sample filed one request. The guided sample filed two starting at line 239 and had zero verified findings. All submitted requests remain available to the named reading. |
| Reproduce the historical route | In the 42184 replay the historical solo loader gave each finding severity `"advisory"` and the named projection rendered `null`. This was the sole final-prompt difference for both samples under the request-only policy. Use each route's own baseline. The replay did not measure an effect on scores. [Saved results](../../results/pr_review_v5/probes/convention-scope-2026-11-24/full-tool.md) |

From the integrated worktree, these are the existing command forms and offline regression suites. The score commands below prepare readings of an existing archive. The test provider exercises generation locally. A live generation or semantic judgment is user-run with `--execute`.

```bash
export PYTHONPATH="$PWD/src:$PWD"
review=(ape/bin/python -m src.mathlib_review.review.cli)
"${review[@]}" plan --reviewer solo-v1 --case 42184@c5474cb4
"${review[@]}" plan --reviewer pr-search-v1 --case 42184@c5474cb4
# User-run live generation when an independent sample is wanted
"${review[@]}" run --reviewer solo-v1 --case 42184@c5474cb4 --run-name solo-42184-a --execute
"${review[@]}" score --of solo-42184-a --using round1-requests-v1
"${review[@]}" score --of solo-42184-a --using round1-questions-v1

ape/bin/python -m pytest -q tests/mathlib_review/test_named_reviewers.py \
  tests/mathlib_review/test_matching.py tests/datasets/test_whole_pr_review.py \
  tests/datasets/test_pr_review_v5_anchoring.py tests/datasets/test_pr_review_v4_semantic_pairing.py
```

**Separate decisions.** Verifying titles from rename history changes the historical input a reviewer can see. Crediting several findings for one reference request changes the reading instrument. Each deserves its own evidence and version decision. Exact submitted edits already have a separate ticket. The comparisons of reviewer quality can resume through the same named commands after this refactor passes its offline checks. [Submitted edits (#2)](https://github.com/yalhessi/APE-Bench/issues/2) · [Four reviewer designs](2026-11-25-four-review-strategies.md)
