"""Is a maintainer's ask answerable by editing a site, or does it require redesigning one?

Written to test a specific claim: that this reviewer is competent at *local* asks and
structurally unable to reach *design* asks, and that the smoke set's apparent 41% issue
recall came from being unusually local rather than from the system being good.

## The criteria

An obligation is **local** when the ask names a site and a replacement that fits inside it.
Answering it requires editing text that already exists:

* rename a declaration to a named new name
* replace a proof with a different tactic or a shorter form
* fix or reword a docstring
* formatting — blank lines, line wrapping, namespace placement
* replace one call spelling with another (`rw [X.f h]` for `rw [F.f X h]`)

An obligation is **design** when answering it requires deciding what should *exist*, not
just editing what does:

* introduce a declaration that is not there (`Dense.ciSup'`, a factored-out general lemma)
* restructure several declarations into a different set of declarations
* replace a family of lemmas with a mechanism that generates them (`@[to_fun]`)
* generalize a statement's typeclass structure
* derive one result from another (an order-dual proof)
* change a definition's representation (a predicate becomes a set comprehension)
* remove axioms and supply proofs

**borderline** is a real third answer, not a dodge. Some asks are a local edit whose *content*
requires design understanding — revising module documentation to explain why a proof needs an
ordered coefficient set is a docstring edit that presupposes reading the proof. Bucketing
those either way would move the headline, so they are reported separately and the result is
stated as a range.

## Provenance, stated plainly

These labels are hand-assigned by Claude from the obligation text, working from a dump that
did not show hit status — but not blind, since earlier analysis in the same session had
already surfaced some outcomes. The classification is therefore auditable rather than
independent: every label is recorded here with the claim it was assigned from, so a
disagreement is a diff rather than an argument. `scope_report` prints the sensitivity band so
the borderline calls cannot silently carry the conclusion.
"""

from __future__ import annotations

import collections
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

LOCAL, DESIGN, BORDERLINE = "local", "design", "borderline"

#: `obligation_id` prefix -> (label, the phrase the label was assigned from).
#: Keyed on prefix because the full ids are 64 hex characters and unreadable in review.
SCOPE: Dict[str, tuple] = {
    # --- PR 33057 -------------------------------------------------------------------
    "b9c6ec640c8": (BORDERLINE, "fix the remaining error(s) so CI passes, then merge — a "
                                "build outcome, not a named edit"),
    # --- PR 33066 -------------------------------------------------------------------
    "d4cc70e10c2": (LOCAL, "docstring typo: 'isometry' -> 'isometric'"),
    "9c96e853db7": (DESIGN, "delete a definition and its five simp lemmas; construct via the "
                            "existing ContinuousAlgEquiv.mk instead"),
    "3ad30059e6e": (LOCAL, "insert a blank line after `section auxiliaryDefs`"),
    # --- PR 33098 -------------------------------------------------------------------
    "d1a4bd4608f": (LOCAL, "rewrite one proof introducing `C := {x} ∪ …` and a named lemma"),
    "14f5e6d6016": (LOCAL, "replace a case-split proof with `grind [minimalCover]`"),
    "45433fc367b": (LOCAL, "rename with an `encard_` prefix"),
    "488d7b571fe": (LOCAL, "simplify one proof with grind"),
    "48ec1f14120": (LOCAL, "replace one `rcases` spelling with another"),
    "64630362c31": (LOCAL, "rename with an `encard_` prefix"),
    "6c1da5ab47f": (LOCAL, "simplify one proof with grind"),
    "6db24d1d232": (LOCAL, "restate the opening `calc` line"),
    "a73a79ae9a7": (LOCAL, "simplify one proof with grind"),
    "c7e1405471a": (LOCAL, "rename with an `encard_` prefix"),
    "d779f40f12c": (LOCAL, "simplify one proof with grind"),
    "ee282f05e9c": (LOCAL, "simplify one proof with grind"),
    "f4d1ab7fb96": (LOCAL, "simplify one proof with grind"),
    "a58d0d5ea6c": (LOCAL, "replace a manual `by_cases` with the `by_cases!` pattern"),
    # --- PR 33117 -------------------------------------------------------------------
    "57bcc9fd384": (DESIGN, "import a tactic and replace 13 duplicated lemmas with an "
                            "attribute that generates them"),
    # --- PR 33145 -------------------------------------------------------------------
    "7fef913e965": (DESIGN, "provide a new `Dense.ciInf'` and prove it via the order dual"),
    "8d887ce4bdd": (DESIGN, "generalize into a new typeclass-polymorphic `Dense.ciSup'`"),
    "bd8a8d8cf88": (DESIGN, "refactor the results into differently-named lemmas with a "
                            "specified signature"),
    "e83e6544d51": (DESIGN, "rename both lemmas AND reprove one by dualising the other"),
    "c9a216b70b5": (LOCAL, "swap the sides of the stated equalities"),
    "e8e028215fa": (DESIGN, "restructure the proof around a `by_cases`, applying the "
                            "`ciSup` lemma the other obligations introduce"),
    # --- PR 33149 -------------------------------------------------------------------
    "3dacf72e309": (DESIGN, "remove new axiom declarations and supply proofs"),
    "f54010d8cfb": (DESIGN, "remove named axioms and replace with proved definitions"),
    "3e19231da93": (DESIGN, "rewrite the file to meet Mathlib standards, eliminating axioms"),
    "61f68eedbdd": (BORDERLINE, "replace a custom Parseval identity with the existing "
                                "Mathlib lemma — a substitution, but of an axiomatised thing"),
    # --- PR 33285 -------------------------------------------------------------------
    "073625ede35": (LOCAL, "golf a proof to a direct lambda"),
    "585e5e0b5b8": (LOCAL, "replace a proof tail with a single `simp`"),
    # --- PR 33294 -------------------------------------------------------------------
    "7f098f6a743": (LOCAL, "rename to dot-notation"),
    "8e276803d0f": (LOCAL, "replace a `rw` spelling with the method call"),
    # --- PR 33305 -------------------------------------------------------------------
    "cc44bb99611": (LOCAL, "wrap an over-long doc comment line"),
    # --- PR 33321 -------------------------------------------------------------------
    "0bb42bd2833": (BORDERLINE, "revise module docs to explain why the proof needs an "
                                "ordered coefficient set — a doc edit presupposing the proof"),
    "c9739efcd0a": (LOCAL, "complete/fix a docstring sentence"),
    "5ffba48eb1e": (DESIGN, "redefine the definition as a set comprehension"),
    # --- PR 33337 -------------------------------------------------------------------
    "ce7b5d2e038": (LOCAL, "rename to the `toLinearMap_…` convention"),
    "64e1164fcb5": (LOCAL, "rename two lemmas to the `toLinearMap_…` convention"),
    # --- PR 33362 -------------------------------------------------------------------
    "695ae9fd914": (LOCAL, "move declarations inside `namespace Complex`"),
    # --- PR 33421 -------------------------------------------------------------------
    "38e72250fc9": (DESIGN, "factor a repeated argument out into a new reusable lemma"),
    "55f6530478b": (DESIGN, "replace a specialized lemma with a generalized one"),
    "6b02b6118fc": (LOCAL, "rename `round_eq'` to `round_eq_div`"),
}


def label_for(obligation_id: str) -> Optional[str]:
    for prefix, (label, _why) in SCOPE.items():
        if obligation_id.removeprefix("obligation:").startswith(prefix):
            return label
    return None


def scope_report(semantic_report: Path, judgments: Path,
                 pr_numbers: Optional[Iterable[int]] = None) -> Dict[str, Any]:
    """Hit rate by scope, with the borderline band reported rather than absorbed."""

    per = {
        item["obligation_id"]: item
        for item in json.loads(semantic_report.read_text())["per_obligation"]
    }
    wanted = set(pr_numbers) if pr_numbers else None
    counts: Dict[str, Dict[str, int]] = collections.defaultdict(
        lambda: {"obligations": 0, "issue_hit": 0, "located": 0})
    unlabelled = []
    for line in judgments.read_text().splitlines():
        if not line.strip():
            continue
        judgment = json.loads(line)
        if wanted is not None and judgment["pr_number"] not in wanted:
            continue
        for obligation in judgment.get("obligations") or []:
            status = per.get(obligation["obligation_id"])
            if status is None:
                continue
            label = label_for(obligation["obligation_id"])
            if label is None:
                unlabelled.append(obligation["obligation_id"])
                continue
            row = counts[label]
            row["obligations"] += 1
            row["issue_hit"] += int(status["issue_status"] == "hit")
            row["located"] += int(status["location_hit"])

    def rate(row):
        return round(row["issue_hit"] / row["obligations"], 3) if row["obligations"] else None

    local, design, border = counts[LOCAL], counts[DESIGN], counts[BORDERLINE]
    return {
        "by_scope": {k: {**v, "issue_recall": rate(v)} for k, v in sorted(counts.items())},
        # The band the borderline calls could move the design number to, if every one of
        # them were reassigned. If the two ends tell the same story, the calls do not matter.
        "design_recall_band": [
            rate({"obligations": design["obligations"] + border["obligations"],
                  "issue_hit": design["issue_hit"] + border["issue_hit"]}),
            rate(design),
        ],
        "unlabelled": unlabelled,
    }
