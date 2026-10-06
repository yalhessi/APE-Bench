"""Hand-written `fun_` forms that `@[to_fun]` would generate: census convention P201.

Pre-registered in `results/pr_review_v5/probes/convention-detectors-2026-10-06/README.md`, stage 3.
P201: "A dual, additive twin, projection or characterisation lemma that a generator (`to_dual`,
`to_additive`, `simps`, `mk_iff`) can produce is generated, not written by hand." One shape, over
declarations the PR adds or renames: `NS.fun_X` written by hand while `NS.X` is declared in the
graph without `to_fun`.

Version 2 (stage 4) retired the `@[to_additive]` shape -- a multiplicative declaration beside its
word-for-word additive translation. It was wrong on 29 of 29 facts across every set: `one`/`zero`
and `mul`/`add` coincide in evaluation lemmas (`epow_zero` beside `epow_one`), in sums and products
of functions, in ordinal arithmetic and in modules, and a name alone cannot tell them from a twin.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.mathlib_review.producers import Fact, declarations, declared_names


class GeneratedTwins:
    name = "generated_twins"
    version = "generated_twins/2"
    title = "Declarations a generator attribute would produce"
    lead = ("Mathlib generates a declaration's `fun_` form with `@[to_fun]` rather than writing it "
            "by hand. Each declaration below is new in this PR and is written by hand beside the "
            "declaration that would generate it.")

    def facts(self, graph: Dict[str, Any]) -> List[Fact]:
        names = declared_names(graph)
        out: List[Fact] = []
        for target, entity, introduced in declarations(graph):
            if not introduced:
                continue
            *spaces, leaf = entity["fullname"].split(".")
            if not leaf.startswith("fun_"):
                continue
            source = names.get(".".join(spaces + [leaf[len("fun_"):]]))
            if source is None or "to_fun" in (source.get("code") or ""):
                continue
            where = f"{source.get('path')}:{(source.get('span') or {}).get('line_start')}"
            out.append(Fact(self.name, target["change_id"], target["path"],
                            entity["span"]["line_start"], entity["fullname"],
                            f"`{leaf}` is written by hand; `@[to_fun]` on `{source['fullname']}` "
                            f"(`{where}`) generates it.", "P201"))
        return out


GENERATED_TWINS = GeneratedTwins()
