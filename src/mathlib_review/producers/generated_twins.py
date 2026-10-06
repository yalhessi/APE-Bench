"""Hand-written declarations a generator attribute would produce: census convention P201.

Pre-registered in `results/pr_review_v5/probes/convention-detectors-2026-10-06/README.md`, stage 3
(amendment 2 for the ring-like skip). P201: "A dual, additive twin, projection or characterisation
lemma that a generator (`to_dual`, `to_additive`, `simps`, `mk_iff`) can produce is generated, not
written by hand." Two shapes, over declarations the PR adds or renames:

1. `@[to_fun]`: the PR adds `NS.fun_X` while `NS.X` is declared in the graph without `to_fun`.
2. `@[to_additive]`: the PR adds, in one file, a multiplicative declaration with no `to_additive`
   attribute and its word-for-word additive translation. A multiplicative declaration whose
   signature names a ring-like class is skipped: there `map_mul` and `map_add` are both primary.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from src.mathlib_review.producers import Fact, declarations, declared_names

#: Leaf words, `_`-separated, and the additive word each translates to.
_WORDS = {"mul": "add", "one": "zero", "prod": "sum", "inv": "neg", "div": "sub", "pow": "nsmul",
          "zpow": "zsmul", "smul": "vadd", "mulIndicator": "indicator"}
#: Namespace components and their additive forms.
_SPACES = {"Mul": "Add", "One": "Zero", "Monoid": "AddMonoid", "CommMonoid": "AddCommMonoid",
           "Group": "AddGroup", "CommGroup": "AddCommGroup", "Subgroup": "AddSubgroup",
           "Submonoid": "AddSubmonoid", "Units": "AddUnits", "MulAction": "AddAction",
           "MonoidHom": "AddMonoidHom", "MulEquiv": "AddEquiv"}
_RING_LIKE = re.compile(r"\b(?:Semiring|Ring|CommRing|Field|DivisionRing|Algebra|Module|NonUnitalNonAssocSemiring)\b")


def additive(full: str) -> Optional[str]:
    """The word-for-word additive translation of a full name, or None if no word translates."""

    *spaces, leaf = full.split(".")
    new_spaces = [_SPACES.get(part, part) for part in spaces]
    new_leaf = "_".join(_WORDS.get(word, word) for word in leaf.split("_"))
    translated = ".".join(new_spaces + [new_leaf])
    return translated if translated != full else None


class GeneratedTwins:
    name = "generated_twins"
    version = "generated_twins/1"
    title = "Declarations a generator attribute would produce"
    lead = ("Mathlib generates a declaration's `fun_` form with `@[to_fun]` and its additive twin "
            "with `@[to_additive]` rather than writing them by hand. Each declaration below is new "
            "in this PR and is written by hand beside the declaration that would generate it.")

    def facts(self, graph: Dict[str, Any]) -> List[Fact]:
        names = declared_names(graph)
        introduced = {}
        out: List[Fact] = []
        for target, entity, new in declarations(graph):
            if new:
                introduced[entity["fullname"]] = (target, entity)
        for full, (target, entity) in introduced.items():
            *spaces, leaf = full.split(".")
            if leaf.startswith("fun_"):
                source = names.get(".".join(spaces + [leaf[len("fun_"):]]))
                if source is not None and "to_fun" not in (source.get("code") or ""):
                    out.append(self._fact(target, entity, full, source, "@[to_fun]"))
        for full, (target, entity) in introduced.items():
            twin = additive(full)
            if not twin or twin not in introduced:
                continue
            twin_target, twin_entity = introduced[twin]
            code = entity.get("code") or ""
            if "to_additive" in code or _RING_LIKE.search(code.split(":=", 1)[0]) \
                    or twin_entity.get("path") != entity.get("path"):
                continue
            out.append(self._fact(twin_target, twin_entity, twin, entity, "@[to_additive]"))
        return out

    def _fact(self, target, entity, full: str, source: Dict[str, Any], attribute: str) -> Fact:
        where = f"{source.get('path')}:{(source.get('span') or {}).get('line_start')}"
        return Fact(self.name, target["change_id"], target["path"], entity["span"]["line_start"], full,
                    f"`{full.rsplit('.', 1)[-1]}` is written by hand; `{attribute}` on "
                    f"`{source['fullname']}` (`{where}`) generates it.", "P201")


GENERATED_TWINS = GeneratedTwins()
