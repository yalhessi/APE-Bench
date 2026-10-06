"""A new primed declaration beside its unprimed sibling: census convention P113.

Pre-registered in `results/pr_review_v5/probes/convention-detectors-2026-10-06/README.md`, stage 3.
P113: "A lemma variant is distinguished from its siblings by naming the term of its statement that
differs, not by appending primes." The fact names the sibling and gives both conclusions, so the
term that differs can be named. A primed name whose unprimed sibling the graph cannot see is
skipped: whether one exists elsewhere in Mathlib is not decidable from the PR's changed files.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ape.toolkits.code.lean.lean_parser import parse_major_declarations

from src.mathlib_review.evidence.operators.naming_contrast import declaration_conclusion
from src.mathlib_review.producers import Fact, declarations, declared_names


def _conclusion(entity: Dict[str, Any]) -> str:
    parsed = parse_major_declarations(entity.get("code") or "")
    text = declaration_conclusion(parsed[0].signature or "") if len(parsed) == 1 else ""
    return " ".join(text.split())[:160] or "(not parsed)"


class PrimedNames:
    name = "primed_names"
    version = "primed_names/1"
    title = "Primed names beside their unprimed sibling"
    lead = ("Mathlib distinguishes a lemma variant from its siblings by naming the term of its "
            "statement that differs, rather than by appending a prime. Each declaration below is "
            "new in this PR, ends in a prime, and has an unprimed sibling; both conclusions are "
            "given.")

    def facts(self, graph: Dict[str, Any]) -> List[Fact]:
        names = declared_names(graph)
        out: List[Fact] = []
        for target, entity, introduced in declarations(graph):
            full = entity.get("fullname") or ""
            if not introduced or not full.endswith("'"):
                continue
            sibling = names.get(full.rstrip("'"))
            if sibling is None:
                continue
            leaf, base_leaf = full.rsplit(".", 1)[-1], full.rstrip("'").rsplit(".", 1)[-1]
            where = f"{sibling.get('path')}:{(sibling.get('span') or {}).get('line_start')}"
            out.append(Fact(self.name, target["change_id"], target["path"],
                            entity["span"]["line_start"], full,
                            f"`{leaf}` is new, and `{base_leaf}` is declared at `{where}`. "
                            f"`{leaf}` concludes `{_conclusion(entity)}`; `{base_leaf}` concludes "
                            f"`{_conclusion(sibling)}`.", "P113"))
        return out


PRIMED_NAMES = PrimedNames()
