"""A new declaration without the generator attribute its file's siblings carry: census P201.

Pre-registered in `results/pr_review_v5/probes/convention-detectors-2026-10-06/README.md`, stage 6.
Stage 3 found most census P201 asks are a missing attribute on a lemma with no hand-written twin
("Missing `@[to_additive]` here"), which no twin shape can see. This states it from the file:
a declaration the PR adds that carries no `to_additive` (or `to_dual`) while at least 3 of the
file's other declarations, and at least half of them, carry it. An additive-named declaration is
skipped for `to_additive`: it is what the attribute generates.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set

from ape.toolkits.code.lean.lean_parser import mask_noncode_regions

from src.mathlib_review.producers import Fact, declarations

ATTRIBUTES = ("to_additive", "to_dual")
_ADDITIVE_WORDS = {"add", "zero", "sum", "neg", "sub", "nsmul", "zsmul", "vadd"}
#: The first declaration keyword, wherever it sits: `@[to_dual] lemma succ_max` puts the attribute on
#: the keyword's own line (missing_attribute/2; /1 read the block only when the keyword began a line).
_KEYWORD = re.compile(r"\b(?:theorem|lemma|def|instance|abbrev|structure|class|inductive)\b")
_WORD = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+")
MIN_SIBLINGS = 3


def name_words(full: str) -> Set[str]:
    """Every word of a full name, lowercased: `.`- and `_`-separated, then camelCase parts, so
    `AddSubmonoid.IsSpanning` holds `add` (missing_attribute/2; /1 read the leaf's `_` words only)."""

    return {word.lower() for part in re.split(r"[._]", full) for word in _WORD.findall(part)}


def attributes(code: str) -> Set[str]:
    """The generator attributes in a declaration's attribute block (before its keyword)."""

    match = _KEYWORD.search(mask_noncode_regions(code or ""))
    prefix = (code or "")[: match.start()] if match else ""
    return {name for name in ATTRIBUTES if re.search(rf"\b{name}\b", prefix)}


class MissingAttribute:
    name = "missing_attribute"
    version = "missing_attribute/2"
    title = "Generator attributes the file's other declarations carry"
    lead = ("Mathlib states a multiplicative or order lemma once and lets a generator attribute "
            "(`@[to_additive]`, `@[to_dual]`) produce its twin. Each declaration below is new in this "
            "PR and carries no such attribute, in a file where most declarations carry it.")

    def facts(self, graph: Dict[str, Any]) -> List[Fact]:
        by_path: Dict[str, Dict[str, Set[str]]] = {}
        for entity in graph.get("entities") or []:
            name = entity.get("fullname")
            if name:
                by_path.setdefault(entity.get("path"), {}).setdefault(name, set()).update(
                    attributes(entity.get("code") or ""))
        out: List[Fact] = []
        for target, entity, introduced in declarations(graph):
            if not introduced:
                continue
            full = entity["fullname"]
            siblings = {n: a for n, a in by_path.get(entity.get("path"), {}).items() if n != full}
            own = attributes(entity.get("code") or "")
            words = name_words(full)
            for attribute in ATTRIBUTES:
                if attribute in own or (attribute == "to_additive" and words & _ADDITIVE_WORDS):
                    continue
                carrying = sum(1 for a in siblings.values() if attribute in a)
                if carrying < MIN_SIBLINGS or 2 * carrying < len(siblings):
                    continue
                out.append(Fact(self.name, target["change_id"], target["path"],
                                entity["span"]["line_start"], full,
                                f"`{full.rsplit('.', 1)[-1]}` carries no `@[{attribute}]`; {carrying} "
                                f"of the {len(siblings)} other declarations in this file do.", "P201"))
        return out


MISSING_ATTRIBUTE = MissingAttribute()
