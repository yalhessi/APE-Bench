"""Where the PR's new code could use dot notation: census conventions P057 and P108.

Pre-registered, with its reading rule, in
`results/pr_review_v5/probes/convention-detectors-2026-10-06/README.md`; version 2 adds stage 4's
three conditions to the method-call shape (R1-R3, below). Two shapes, both over the change graph
alone and only on code the PR adds:

1. **Placement.** A declaration the PR adds or renames, concluding a predicate `H …`, whose leaf
   name is `h_of_rest` (`h` = `H` with its first letter lowered): inside `H`'s namespace it would
   be `H.of_rest`.
2. **Method call.** In a line the PR adds, `N.lemma x` where `x` is an explicit binder whose type's
   head has `N`'s last component: it can be written `x.lemma`.

A fact states the dotted form. It does not say anyone would ask for it.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from ape.toolkits.code.lean.lean_parser import mask_noncode_regions, parse_major_declarations

from src.mathlib_review.conventions.facets import split_binders
from src.mathlib_review.conventions.situations import predicate_head
from src.mathlib_review.evidence.operators.naming_contrast import declaration_conclusion
from src.mathlib_review.producers import Fact, added_lines, declarations
from src.mathlib_review.retrieval.declaration_table import conclusion_head

#: `Order.IsNormal.map_iSup h`: a capitalised (possibly namespaced) prefix, a lowercase lemma, an
#: argument. The prefix's last component is compared with the argument's type head. The argument
#: must not be followed by a projection: in `Finset.range F.card` the argument is `F.card`, not `F`
#: (dot_notation/3, found on the stage-4 holdout).
_CALL = re.compile(r"(?<![\w.])((?:[A-Z][\w']*\.)*[A-Z][\w']*)\.([a-z_][\w']*)\s+([a-zA-Z_][\w']*)\b(?!\.)")
#: `(h hf : Order.IsNormal f)`: the names, then the type's head identifier.
_BINDER = re.compile(r"^\(\s*([^:()]+?)\s*:\s*((?:[A-Z][\w']*\.)*[A-Z][\w']*)\b")


def _lower_first(name: str) -> str:
    return name[:1].lower() + name[1:]


class DotNotation:
    name = "dot_notation"
    version = "dot_notation/3"
    title = "Where dot notation may apply"
    lead = ("Mathlib places a lemma about a predicate in that predicate's namespace, and applies a "
            "lemma to a hypothesis through the hypothesis (`h.lemma`). These places in the code this "
            "PR adds have that shape; each line says what the code is and what the dotted form "
            "would be.")

    def facts(self, graph: Dict[str, Any]) -> List[Fact]:
        out: List[Fact] = []
        for target, entity, introduced in declarations(graph):
            parsed = parse_major_declarations(entity.get("code") or "")
            if len(parsed) != 1:
                continue
            signature = parsed[0].signature or ""
            # Only a name the PR introduced is placed; an anonymous declaration has none.
            if introduced:
                out += self._placement(target, entity, signature)
            out += self._calls(target, entity, signature)
        return out

    def _placement(self, target, entity, signature: str) -> List[Fact]:
        head = predicate_head(declaration_conclusion(signature))
        if not head:
            return []
        last = head.rsplit(".", 1)[-1]
        leaf = entity["fullname"].rsplit(".", 1)[-1]
        stem = _lower_first(last) + "_of_"
        if not leaf.startswith(stem) or len(leaf) == len(stem):
            return []
        dotted = f"{last}.{leaf[len(stem) - 3:]}"
        return [Fact(self.name, target["change_id"], target["path"], entity["span"]["line_start"],
                     entity["fullname"],
                     f"`{leaf}` concludes `{head} …` and is named beside that namespace; inside "
                     f"it, it is `{dotted}`.", "P108")]

    def _calls(self, target, entity, signature: str) -> List[Fact]:
        heads: Dict[str, str] = {}
        binder_names: set = set()
        for kind, text in split_binders(signature):
            names = text[1:].split(":", 1)[0].split() if ":" in text else []
            binder_names.update(names)
            match = _BINDER.match(text) if kind == "explicit" else None
            # R3 (dot_notation/2): a relation-typed binder (`h : a = b`) is not a receiver.
            if match and conclusion_head(text[1:-1].split(":", 1)[1]) == "other":
                for name in match.group(1).split():
                    heads[name] = match.group(2)
        if not heads:
            return []
        code = entity.get("code") or ""
        masked = mask_noncode_regions(code)
        added = added_lines(target)
        out, seen = [], set()
        for match in _CALL.finditer(masked):
            prefix, lemma, argument = match.groups()
            head: Optional[str] = heads.get(argument)
            if not head or head.rsplit(".", 1)[-1] != prefix.rsplit(".", 1)[-1]:
                continue
            # R1 (dot_notation/2): a qualified binder head resolves `x.lemma` in its own
            # namespace first, so the prefix must be exactly that head.
            if "." in head and prefix != head:
                continue
            # R2 (dot_notation/2): a variable is not a namespace (`P.lemma h`, `S.closed hf`).
            first = prefix.split(".", 1)[0]
            if first in binder_names or len(first) == 1:
                continue
            offset = match.start()
            end = code.find("\n", offset)
            line_text = code[code.rfind("\n", 0, offset) + 1: end if end >= 0 else len(code)]
            if line_text.strip() not in added or (prefix, lemma, argument) in seen:
                continue
            seen.add((prefix, lemma, argument))
            line = entity["span"]["line_start"] + code.count("\n", 0, offset)
            out.append(Fact(self.name, target["change_id"], target["path"], line,
                            entity.get("fullname") or f"({entity.get('kind')})",
                            f"`{prefix}.{lemma} {argument}` applies a `{prefix.rsplit('.', 1)[-1]}` "
                            f"lemma to `{argument} : {head} …`; it can be written "
                            f"`{argument}.{lemma}`.", "P057"))
        return out


DOT_NOTATION = DotNotation()
