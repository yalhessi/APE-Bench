"""The one semantic-judge protocol: rubric text, prompt rendering, verdict, identity.

Both judge arms — the dataset-side evaluator (`semantic_judge.py`) and the registered task
(`src/ape/tasks/lean_tasks/formal_math/pr_review_v4/judgment.py`) — import everything here.
They previously carried byte-identical copies of the rubric and of the verdict parser, and
the copies drifted in exactly the way duplicated code does: the script's caller never passed
the reviewed code, so it ran the v8 rubric with an empty `## REVIEWED CODE` section while
reporting a v8 version string.

Three properties this module exists to guarantee:

1. **There is one rubric.** Not two that are asserted to be equal.
2. **A prompt that omits context is a different judge.** Optional context is declared through
   `ContextProfile`, which is part of `judge_identity`, so an ablation can never resume into
   or collide with a differently-contextualised verdict.
3. **The judge may decline.** A boolean judge forced to answer a genuinely ambiguous pair
   returns noise; `abstain` lets it say so, and the ambiguity registry records the ruling.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Literal, Optional, Tuple

from .io import canonical_json_bytes, extract_json_object, sha256_bytes


#: v9. Two changes from v8: the judge may `abstain`, and every optional context block is
#: declared in `ContextProfile` rather than silently present or absent.
#:
#: Numbers compare only within a rubric version. Everything through Phase 9 was measured
#: under v7.1 (`legacy/judge_v71.py`) and the judge-v8 audit under v8; neither is re-scored.
JUDGE_VERSION = "v4-semantic-v3-v9-rubric"

MAX_TARGET_CODE_CHARS = 4000

JUDGE_PROMPT = """You are scoring one candidate review request against one atomic gold maintainer
obligation on the same Mathlib pull request. Locating them at the same review target has already
been established; that alone is not a match. Judge semantic content strictly.

## REVIEWED CODE (the maintainer's target)
{gold_code}
{candidate_code_block}{context_blocks}
## GOLD MAINTAINER OBLIGATION
Concern families: {gold_concerns}
Requested action: {gold_action}
Requested change: {gold_claim}
Resolution criteria: {resolution_criteria}

## CANDIDATE REVIEW REQUEST
Primary subject: {primary_subject}
Concern family: {candidate_family}
Claimed present problem: {candidate_claim}
Requested change: {requested_change}
Suggested implementation: {suggested_fix}
Proposed edit: {proposed_edit}

Return three fields:
1. issue_match: true only when the candidate asserts the same specific problem or code aspect that
the maintainer says must change — the thing that would have to change. Use the reviewed code above
to decide whether the two statements name the same aspect rather than inferring it from wording.
Sharing a declaration, concern family, or nearby line is not enough. A request about a DIFFERENT
aspect of the same code — for example proof style when the ask is a rename, or a rename when the ask
is a proof change — is false. A defense, question, risk, or no-change conclusion is false. A
different fix for the same problem may still issue-match.
2. resolution_match: true only when issue_match is true and the candidate's concrete transformation
achieves the maintainer's requested result. Compare the CHANGES: the obligation's requested
transformation against the candidate's requested change and proposed edit, allowing different
wording but requiring the same end state. A vaguer fix that would not by itself produce the asked
transformation is issue_match only.
3. abstain: true only when this pair falls on a boundary the rubric does not settle — for example
when the candidate asks for a prerequisite of the maintainer's change rather than the change
itself, so "the same issue" is a question about where the rubric draws its line rather than about
what these two statements say. Do NOT abstain merely because the call is difficult or the evidence
is thin; those are false. When abstain is true the other two fields are ignored."""

_CANDIDATE_CODE_TEMPLATE = """
## CODE THE CANDIDATE POINTS AT (a different target in the same PR)
{candidate_code}
"""


@dataclass(frozen=True)
class ContextProfile:
    """Which optional context blocks a prompt carries.

    Part of `judge_identity`: two runs that show the judge different context are different
    judges, and their verdicts must never share a cache slot.
    """

    candidate_code: bool = False
    #: The maintainer's source review comment. Named for what it is: what can be recovered
    #: deterministically is the comment, not a distilled rationale, and a comment often
    #: contains a literal suggestion block — so this ablation partly measures "does showing
    #: the judge the maintainer's own fix help", which is not the same question.
    maintainer_comment: bool = False
    sibling_obligations: bool = False

    def as_key(self) -> str:
        enabled = [name for name, on in sorted(self.__dict__.items()) if on]
        return "+".join(enabled) or "base"


@dataclass(frozen=True)
class Verdict:
    issue_match: bool
    resolution_match: bool
    abstain: bool
    reason: str
    #: `unparseable` is an error, never a negative verdict. Scoring a garbled reply as
    #: "no match" silently converts judge failures into misses.
    status: Literal["parsed", "salvaged", "unparseable"]


def code_block(change_ids: Iterable[str], targets_by_change_id: Dict,
               limit: int = MAX_TARGET_CODE_CHARS) -> str:
    """Render the reviewed code of some change targets.

    Truncation is marked explicitly so a clipped body is never mistaken for a whole
    declaration. The empty-result string is deliberately conspicuous: it is the signature of
    the defect where the judge was asked to compare two prose descriptions of code it had
    never been shown.
    """

    blocks = []
    for change_id in change_ids:
        target = targets_by_change_id.get(change_id)
        if target is None:
            continue
        code = (target.reviewed_code or target.base_code or "").strip()
        if not code:
            continue
        if len(code) > limit:
            code = code[:limit] + "\n… (truncated)"
        blocks.append(f"### {target.declaration_name or target.path}\n```lean\n{code}\n```")
    return "\n\n".join(blocks) or "(reviewed code unavailable for this target)"


def proposed_edit_text(candidate) -> str:
    edit = getattr(candidate, "proposed_edit", None)
    if edit is None or not getattr(edit, "new_declaration", None):
        return "(none)"
    return f"{edit.declaration_name or edit.path}:\n{edit.new_declaration}"


def render_prompt(
    *,
    gold_code: str,
    gold_concerns: str,
    gold_action: str,
    gold_claim: str,
    resolution_criteria: str,
    primary_subject: str,
    candidate_family: str,
    candidate_claim: str,
    requested_change: str,
    suggested_fix: str,
    proposed_edit: str,
    candidate_code: str = "",
    maintainer_comment: str = "",
    sibling_claims: Tuple[str, ...] = (),
) -> str:
    """Render the rubric. Optional blocks are omitted entirely rather than stubbed.

    A block rendered as "(not recorded)" still tells the judge the field exists and is
    empty, which is a different prompt from one that never mentions it. Omission keeps the
    base prompt byte-identical to a run without the ablation.
    """

    candidate_code_block = (
        _CANDIDATE_CODE_TEMPLATE.format(candidate_code=candidate_code) if candidate_code else ""
    )
    context = ""
    if maintainer_comment:
        context += f"\n## WHAT THE MAINTAINER WROTE\n{maintainer_comment}\n"
    if sibling_claims:
        # Claim text only, and only of siblings in the *same* maintainer judgment: this is
        # what "same below" encodes. Sibling *candidates* are never shown — that would let
        # the judge credit this obligation using another candidate's content.
        joined = "\n".join(f"- {claim}" for claim in sibling_claims)
        context += (
            "\n## OTHER ASKS IN THE SAME MAINTAINER JUDGMENT (context only; do not score these)\n"
            f"{joined}\n"
        )
    return JUDGE_PROMPT.format(
        gold_code=gold_code,
        candidate_code_block=candidate_code_block,
        context_blocks=context,
        gold_concerns=gold_concerns,
        gold_action=gold_action,
        gold_claim=gold_claim,
        resolution_criteria=resolution_criteria,
        primary_subject=primary_subject,
        candidate_family=candidate_family,
        candidate_claim=candidate_claim,
        requested_change=requested_change,
        suggested_fix=suggested_fix,
        proposed_edit=proposed_edit,
    )


def parse_verdict(text: str) -> Verdict:
    """Parse a free-text judge reply.

    The registered task submits typed booleans through a tool and never needs this; it
    remains for reading historical text replies. `bool("false")` is `True`, so string values
    are coerced explicitly rather than passed to `bool`.
    """

    try:
        value = extract_json_object(text)
    except ValueError:
        issue = re.search(r'"issue_match"\s*:\s*(true|false)', text, re.IGNORECASE)
        resolution = re.search(r'"resolution_match"\s*:\s*(true|false)', text, re.IGNORECASE)
        if issue and resolution:
            issue_match = issue.group(1).lower() == "true"
            return Verdict(
                issue_match,
                resolution.group(1).lower() == "true" and issue_match,
                False,
                f"judge_partial_json: {text[:100]}",
                "salvaged",
            )
        return Verdict(False, False, False, f"judge_unparseable: {text[:100]}", "unparseable")
    issue_match = as_bool(value.get("issue_match"))
    return Verdict(
        issue_match,
        as_bool(value.get("resolution_match")) and issue_match,
        as_bool(value.get("abstain")),
        str(value.get("reason") or ""),
        "parsed",
    )


def as_bool(value: Any) -> bool:
    """Coerce a JSON-ish value to bool without `bool("false") is True`."""

    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def judge_identity(
    *,
    model: str,
    sample_count: int,
    max_tokens: Optional[int],
    thinking_budget_tokens: Optional[int],
    temperature: Optional[float],
    aggregation_policy: str,
    context_profile: ContextProfile,
    judge_version: str = JUDGE_VERSION,
) -> str:
    """Hash of everything that can change a verdict.

    Model and rubric alone are not enough. R0 measured the two arms disagreeing on 4 of 18
    pairs purely because their decode budgets differed — 1200/512 versus the framework
    defaults — with every disagreeing pair unanimous within its arm. Sampling and the
    aggregation policy decide what a set of samples *means*, so they belong here too.
    """

    return sha256_bytes(canonical_json_bytes({
        "judge_version": judge_version,
        "model": model,
        "sample_count": sample_count,
        "max_tokens": max_tokens,
        "thinking_budget_tokens": thinking_budget_tokens,
        "temperature": temperature,
        "aggregation_policy": aggregation_policy,
        "context_profile": context_profile.as_key(),
    }))
