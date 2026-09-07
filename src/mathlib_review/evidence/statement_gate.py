"""Decide whether an edit changed the declaration's *statement* or only its *proof*.

`verified_compile` is the strongest evidence tier, and for a focused proof-simplification
finding it is supposed to mean "the same theorem, proved better". It does not. The submission
path splices a whole replacement declaration — **signature included** —
(`pr_review_v2/base.py:299`, `src[:header_span[0]] + new_declaration + src[body_span[1]:]`)
and nothing anywhere compares the old signature to the new one. An agent that adds a
hypothesis, specialises a type variable, or weakens the conclusion produces a file that
compiles perfectly and earns the top evidence tier for a theorem nobody asked about.

The two focused specs need opposite guarantees, and the same comparison serves both:

* **golf / idiom** claim the statement is untouched. If it moved, the finding is not a proof
  simplification, whatever it compiles to.
* **generality** claims the statement *did* move. If it did not, it is a golf finding wearing
  a generality label — which `generality.py:41-46` already tells the agent to drop, but which
  nothing enforced.

Signatures are compared with the declaration's own name masked, reusing
`modification_inventory.declaration_components`, so a rename does not read as a statement
change on its own.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from ape.toolkits.code.lean.lean_parser import parse_major_declarations

from src.mathlib_review.release.modification_inventory import declaration_components

STATEMENT_GATE_VERSION = "statement-gate/1"


@dataclass(frozen=True)
class StatementComparison:
    """Whether the statement moved, or why that could not be decided."""

    verdict: Literal["unchanged", "changed", "undecidable"]
    detail: str
    original: Optional[str] = None
    replacement: Optional[str] = None


def masked_signature(code: Optional[str]) -> Optional[str]:
    """The declaration's signature with its own name masked, or None if not decidable."""

    components, problems = declaration_components(code)
    if problems or "statement_or_type" not in components:
        return None
    return components["statement_or_type"]


def declaration_source(file_code: str, declaration_name: str) -> Optional[str]:
    """The full source of one declaration in a file, located by name.

    Matches on the leaf name too, because an agent may cite `foo` where the file declares
    `Namespace.foo`. Ambiguity returns None rather than guessing — comparing against the
    wrong declaration would be worse than declining to compare.
    """

    leaf = declaration_name.rsplit(".", 1)[-1]
    matches = [
        item for item in parse_major_declarations(file_code)
        if (item.fullname or item.name or "") == declaration_name
        or (item.name or "").rsplit(".", 1)[-1] == leaf
        or (item.fullname or "").rsplit(".", 1)[-1] == leaf
    ]
    if len(matches) != 1:
        return None
    start, end = matches[0].span
    return file_code[start:end]


def compare_statements(original_code: Optional[str],
                       replacement_code: Optional[str]) -> StatementComparison:
    original = masked_signature(original_code)
    replacement = masked_signature(replacement_code)
    if original is None or replacement is None:
        return StatementComparison(
            "undecidable",
            "the original or the replacement does not parse as exactly one declaration, so "
            "the statement cannot be compared",
            original, replacement,
        )
    if original == replacement:
        return StatementComparison("unchanged", "the statement is byte-identical once the "
                                                "declaration name is masked",
                                   original, replacement)
    return StatementComparison(
        "changed",
        f"the statement changed: {original!r} -> {replacement!r}",
        original, replacement,
    )


#: What each issue kind requires of the statement. Kinds absent from this table are not
#: gated — the check only makes sense where the claim is *about* the statement/proof split.
STATEMENT_REQUIREMENT = {
    "proof_simplification": "unchanged",
    "generalization_available": "changed",
}


def gate_error(issue_kind: Optional[str], comparison: StatementComparison) -> Optional[str]:
    """The submission error for a comparison that violates the claim's own semantics."""

    required = STATEMENT_REQUIREMENT.get(issue_kind or "")
    if required is None:
        return None
    if comparison.verdict == required:
        return None
    if comparison.verdict == "undecidable":
        return (
            f"a {issue_kind} finding must be submitted as declaration_name + new_declaration "
            f"so its statement can be checked ({comparison.detail})"
        )
    if required == "unchanged":
        return (
            f"a {issue_kind} finding must not change the statement — it claims the proof can "
            f"be improved, not the theorem. {comparison.detail}"
        )
    return (
        f"a {issue_kind} finding must change the statement; this edit only rewrites the "
        f"proof, which is a proof-simplification finding. {comparison.detail}"
    )
