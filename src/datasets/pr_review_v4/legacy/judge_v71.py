"""The frozen v7.1-as-implemented judge rubric, retired 2026-08-05.

Every result reported through Phase 9 was measured under this rubric, and it is the key
under which 55 cached verdicts and 38 stamped artifacts were written. It is kept so those
numbers stay interpretable and auditable — not so it can be run.

It is superseded by the v8 rubric in `semantic_judge.py`, which restores three clauses
this version had dropped from the v3-era original and shows the judge the reviewed code.
Under v8 the judge's self-disagreement fell from 4/18 pairs to 0/18. See
`results/pr_review_v4/audits/judge-prompt-regression.md` and `audits/judge-v8/VERDICT.md`.

Its name overstated its fidelity: it was labelled `v7.1-rubric` but was a reduction of
`src/datasets/legacy/pr_review_v3/judge.py` (the real v7.1), missing the "different aspect
of the same lines" negative example, the "a vaguer fix is issue_match only" rule, the
instruction to compare transformations, and every context field except `suggested_fix`.

**v7.1 numbers are comparable only to other v7.1 numbers.** Nothing measured under it is
re-scored under v8.
"""

from ape.utils.project import PROJECT_ROOT

#: The retired script arm's verdict cache. It moved here with the rubric it belongs to:
#: the live judge no longer has a file cache, and the only remaining reader is
#: `r0_judge_equivalence`, which joins historical v7.1 verdicts.
LEGACY_CACHE_DIR = PROJECT_ROOT / "data" / "pr_review_v4" / "cache" / "semantic_judge"

LEGACY_JUDGE_VERSION = "v4-semantic-v1-v7.1-rubric"

LEGACY_JUDGE_PROMPT = """You are scoring one candidate review request against one atomic gold maintainer
obligation on the same Mathlib pull request. Stable change-ID overlap has already established only
that they concern the same review target. Judge semantic content strictly.

## GOLD MAINTAINER OBLIGATION
Concern families: {gold_concerns}
Requested change: {gold_claim}
Resolution criteria: {resolution_criteria}

## CANDIDATE REVIEW REQUEST
Primary subject: {primary_subject}
Concern family: {candidate_family}
Claimed present problem: {candidate_claim}
Requested change: {requested_change}
Suggested implementation: {suggested_fix}

Return two levels:
1. issue_match: true only when the candidate asserts the same specific problem or code aspect that
the maintainer says must change. Sharing a declaration, concern family, or nearby line is not enough.
A request about a different binder, tactic, name, branch, or style choice is false. A defense,
question, risk, or no-change conclusion is false. A different fix may still issue-match.
2. resolution_match: true only when issue_match is true and the candidate's concrete transformation
achieves the maintainer's requested result. A related, vaguer, or alternative transformation is
false unless it produces the same requested change.

Reply with JSON only:
{{"issue_match": true|false, "resolution_match": true|false, "reason": "one sentence"}}"""
