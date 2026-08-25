"""
Prediction-side contract for the v2 first-round-review task (spec §4, D1+D2).

Defines what a system under evaluation must output, the prompt that elicits it
in `diff_only` mode, and the parser that turns raw model text into a
`PredictionRecord`. The output contract deliberately mirrors the gold schema:
findings carry anchors and severities so the D2 matcher can align them with
gold comments, and `merge_ready_as_is` + `confidence` give D1.
"""

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field, ValidationError

from .schema import PRReviewV2Record

PREDICTION_SCHEMA_VERSION = "pr_review_v2_pred/0.1"


class PredictedAnchor(BaseModel):
    path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None


class PredictedFinding(BaseModel):
    anchor: Optional[PredictedAnchor] = Field(default=None, description="None = PR-level finding")
    severity: Literal["blocking", "advisory"]
    claim: str
    suggested_fix: Optional[str] = None
    evidence: Optional[str] = Field(
        default=None,
        description="Verified artifact backing the finding (proof-carrying review): the existing "
        "declaration's name for a duplicate, the stronger statement for a generality issue.",
    )
    verified: Optional[bool] = Field(
        default=None,
        description="True if the task re-compiled this finding's evidence and it held (enforced "
        "submission). None for free-text findings (holistic pass).",
    )
    source: Optional[str] = Field(
        default=None,
        description="Which checker produced this finding in a composed/decomposed review "
        "(golf|dup|gen|...); None for single-task runs.",
    )
    confidence: Optional[float] = Field(
        default=None,
        description="Per-finding P(a maintainer would leave this comment); emitted by the "
        "apply-all instantiation mode as the downstream ranking signal.",
    )


class PredictionRecord(BaseModel):
    schema_version: str = PREDICTION_SCHEMA_VERSION
    pr_number: int
    model: str
    mode: Literal["diff_only", "workspace"]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    merge_ready_as_is: Optional[bool] = None
    confidence: Optional[float] = None
    findings: List[PredictedFinding] = Field(default_factory=list)
    review_message: str = Field(
        default="", description="Agent's free-text review summary (e.g. per-item SKIP reasons)")

    parse_ok: bool = True
    parse_error: Optional[str] = None
    raw_text: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_s: float = 0.0
    retried_parse: bool = False


SYSTEM_PROMPT = """You are an experienced Mathlib maintainer performing first-round review of a \
pull request to leanprover-community/mathlib4. The PR compiles; your job is to judge whether it \
is merge-ready *as submitted* and to surface the issues a Mathlib maintainer would raise: \
duplication of existing library material, insufficient generality, naming-convention violations, \
style and formatting, missing docstrings or API companions, proof quality (golfable or \
non-idiomatic proofs), scope problems, and anything else that would need to change before merge.

Be precise and selective: real maintainers raise a small number of well-grounded points. Do not \
pad the list. A finding is "blocking" if the author should be expected to address it before \
merge, "advisory" if it is optional or out of scope for this PR.

Respond with a single JSON object and nothing else."""

USER_PROMPT_TEMPLATE = """## PR title

{title}

## PR description

{description}

## Diff (against the merge base; line numbers below refer to the NEW file, right side)

```diff
{diff}
```

## Your task

Review this PR as submitted. Output a single JSON object:

{{
  "merge_ready_as_is": <true if a maintainer would approve/merge this without requesting changes>,
  "confidence": <0.0-1.0>,
  "findings": [
    {{
      "path": "<changed file the finding is anchored to, or null for PR-level findings>",
      "line_start": <first line in the NEW file the finding refers to, or null>,
      "line_end": <last line, or null>,
      "severity": "blocking" | "advisory",
      "claim": "<one- or two-sentence statement of the issue, as a maintainer would write it>",
      "suggested_fix": "<concrete replacement code or rename if you have one, else null>"
    }}
  ]
}}

At most {budget} findings. An empty findings list is the correct answer for a merge-ready PR."""

RETRY_PROMPT = (
    "Your previous response could not be parsed as JSON ({error}). "
    "Reply again with ONLY the JSON object, no prose, no code fences."
)


def build_user_prompt(record: PRReviewV2Record, *, budget: int) -> str:
    description = record.input.description.strip() or "(no description provided)"
    diff = record.input.diff or ""
    return USER_PROMPT_TEMPLATE.format(
        title=record.input.title,
        description=description,
        diff=diff,
        budget=budget,
    )


def _extract_json_object(text: str) -> Dict[str, Any]:
    """Extract the first JSON object from raw model output (fences/prose tolerated)."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    decoder = json.JSONDecoder()
    for start in range(len(cleaned)):
        if cleaned[start] != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(cleaned[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    raise ValueError("no JSON object found in response")


def parse_prediction_text(text: str, *, budget: int) -> Tuple[Optional[bool], Optional[float], List[PredictedFinding]]:
    """Parse model text into (merge_ready_as_is, confidence, findings). Raises ValueError."""
    payload = _extract_json_object(text)

    merge_ready = payload.get("merge_ready_as_is")
    if not isinstance(merge_ready, bool):
        merge_ready = None
    confidence = payload.get("confidence")
    confidence = float(confidence) if isinstance(confidence, (int, float)) else None

    findings: List[PredictedFinding] = []
    for raw in (payload.get("findings") or [])[:budget]:
        if not isinstance(raw, dict):
            continue
        anchor = None
        if raw.get("path"):
            anchor = PredictedAnchor(
                path=str(raw["path"]),
                line_start=raw.get("line_start") if isinstance(raw.get("line_start"), int) else None,
                line_end=raw.get("line_end") if isinstance(raw.get("line_end"), int) else None,
            )
        severity = str(raw.get("severity") or "").lower()
        if severity not in ("blocking", "advisory"):
            severity = "advisory"
        claim = str(raw.get("claim") or "").strip()
        if not claim:
            continue
        try:
            findings.append(
                PredictedFinding(
                    anchor=anchor,
                    severity=severity,  # type: ignore[arg-type]
                    claim=claim,
                    suggested_fix=(str(raw["suggested_fix"]) if raw.get("suggested_fix") else None),
                    evidence=(str(raw["evidence"]) if raw.get("evidence") else None),
                    verified=(raw.get("verified") if isinstance(raw.get("verified"), bool) else None),
                )
            )
        except ValidationError as exc:
            raise ValueError(f"invalid finding: {exc}") from exc
    return merge_ready, confidence, findings
