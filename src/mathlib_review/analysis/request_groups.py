"""Maintainer requests, grouped the way the maintainer made them.

An obligation is not the unit a reviewer works in. On PR33098 one comment -- *"this and the
next three lemmas can be proven with `grind [minimalCover]`"* -- becomes **four** obligations,
and a second becomes **three**. Scoring per obligation makes that one request look like seven
independent misses, and building per obligation makes it unbuildable: no single finding in the
system can span the four sites.

So the evaluation unit is the **request group**, keyed by the maintainer comment
(`source_event_ids`) that produced it, falling back to the judgment when a row carries no event.
On the development set that is **35 groups over 40 obligations**, and exactly two of them carry
more than one obligation -- both on 33098, both `grind` families.

Each group records what answering it would actually take:

* `answerable_arm_ids` -- which registered arms could produce this claim at all. Audited from
  the maintainer's comment, NOT from the gold concern label. The labels are unusable for this:
  13 of PR33098's 14 obligations carry `style`, the seven `grind` requests included, and the
  registry's own comment says so (`agenda/registry.py`, `arm.py:44-56`).
* `required_scope` -- how much must be in view (`obligation_capability.SCOPES`).
* `required_information` -- `diff`, `repository`, or `convention`: where the answer lives.
* `required_output` -- `single_edit`, `patch_set`, `rename`, or `deletion`: the shape the
  system must be able to emit. A group needing `patch_set` cannot be resolved by an arm
  confined to one work unit, however well briefed.

**Evaluation-only, and gold-derived.** Nothing here may reach a prompt, a routing artifact, or
a bench fixture used to *train* anything. Production scheduling is gold-free
(`agenda/focused_specs.py:10-15`) and stays that way; this exists to construct experiments and
to say afterwards which capability a rung actually exercised.

This is one side's classification (`classified_by: claude`), recorded per group so a reader can
disagree with a specific call rather than the whole table. Codex classifies independently and
disagreements are preserved rather than averaged.
"""

from __future__ import annotations

import argparse
import collections
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from src.mathlib_review.analysis.obligation_capability import SCOPES
from src.mathlib_review.io import load_jsonl
from src.mathlib_review.schema import InterventionView, JudgmentNode

REQUEST_GROUP_VERSION = "v5-request-groups/1"

#: Where the answer lives.
#:
#: `diff`        -- visible in the change under review.
#: `repository`  -- needs the library at the base commit: an existing lemma, a mechanism, how
#:                  a tactic is used elsewhere.
#: `convention`  -- needs a stated norm or migration direction that frequency contradicts.
INFORMATION_SOURCES = ("diff", "repository", "convention")

#: The shape the system must be able to emit for the group to be *resolved*, not merely named.
OUTPUT_SHAPES = ("single_edit", "patch_set", "rename", "deletion")

#: Every arm the agenda can schedule, for validating the audited answers.
KNOWN_ARMS = frozenset({
    "proof_golf", "proof_idiom", "duplication", "generality", "naming", "docs", "style",
    "api_reuse", "correctness", "family_design", "generalist",
})


@dataclass(frozen=True)
class Classification:
    """One audited request group. Keyed by its first obligation's id prefix."""

    lead_obligation: str
    pr_number: int
    answerable_arm_ids: Tuple[str, ...]
    required_scope: str
    required_information: str
    required_output: str
    why: str


#: Audited from the maintainer comment. `generalist` is omitted throughout: it has no concern
#: filter, so it is answerable for everything and listing it would say nothing.
CLASSIFICATION: Sequence[Classification] = (
    # --- PR 33066 -------------------------------------------------------------------------
    Classification("d4cc70e10c26", 33066, ("docs",), "site", "diff", "single_edit",
        "A one-word docstring typo, 'isometry' -> 'isometric'. Entirely inside the diff."),
    Classification("9c96e853db76", 33066, ("duplication", "api_reuse"), "file", "repository",
        "deletion",
        "Delete `ContinuousAlgEquiv.ofAlgEquiv` and its simp lemmas because Mathlib already "
        "provides the construction. Knowing that requires the library, not the diff."),
    Classification("3ad30059e6e6", 33066, ("style",), "site", "diff", "single_edit",
        "Blank line after `section auxiliaryDefs` and the `variable` moved after it. Pure "
        "local formatting."),

    # --- PR 33098: the two grind families -------------------------------------------------
    Classification("14f5e6d60163", 33098, ("proof_idiom", "proof_golf", "family_design"),
        "family", "repository", "patch_set",
        "'this and the next three lemmas can be proven with `grind [minimalCover]`'. Four "
        "obligations, one request. The four targets sit in four different work units, so no "
        "current invocation can see the family, and `grind`'s applicability is a fact about "
        "the repository at the base commit -- 684 of 7409 files -- not about the diff."),
    Classification("f4d1ab7fb96f", 33098, ("proof_idiom", "proof_golf", "family_design"),
        "family", "repository", "patch_set",
        "'this and the next two', the maximalSeparatedSet counterpart of the above. Three "
        "obligations, one request."),
    Classification("64630362c315", 33098, ("naming",), "convention", "convention", "rename",
        "`encard_` prefix. A naming norm; corpus frequency argues the other way, which is "
        "exactly why frequency must not decide it."),
    Classification("45433fc367bd", 33098, ("naming",), "convention", "convention", "rename",
        "The maximal-separated-set counterpart of the same `encard_` norm."),
    Classification("c7e1405471a2", 33098, ("naming",), "convention", "convention", "rename",
        "`card_le_of_isSeparated` under the same `encard_` norm."),
    Classification("d1a4bd4608f6", 33098, ("proof_idiom", "proof_golf"), "site", "diff",
        "single_edit",
        "Introduce `C := {x} ∪ maximalSeparatedSet ε A` and use `isSeparated_insert`. A "
        "specific restructuring of one proof, designable from what is on screen."),
    Classification("a58d0d5ea6ca", 33098, ("proof_idiom",), "site", "repository",
        "single_edit",
        "Replace a manual `by_cases` with the `by_cases!` pattern. `by_cases!` is in 192 "
        "files at the base commit and zero times in the reviewed file: repository knowledge."),
    Classification("48ec1f14120b", 33098, ("proof_idiom",), "site", "diff", "single_edit",
        "Change the shape of an `rcases` split. Local."),
    Classification("6db24d1d2328", 33098, ("proof_idiom", "proof_golf"), "site", "diff",
        "single_edit",
        "Rewrite a `calc` so the first line carries the goal equality. Local and specific."),

    # --- PR 33117 -------------------------------------------------------------------------
    Classification("57bcc9fd3846", 33117, ("duplication", "family_design", "api_reuse"),
        "family", "repository", "patch_set",
        "Import `Mathlib.Tactic.ToFun` and replace thirteen hand-written `fun_*` lemmas with "
        "`@[to_fun]`. The lead recognised the duplication and the specialist still failed: "
        "the mechanism is a repository fact, and the fix is an import plus attributes plus "
        "deletions that must compile together."),

    # --- PR 33145 -------------------------------------------------------------------------
    Classification("e83e6544d51c", 33145, ("naming",), "convention", "convention", "rename",
        "`Dense.continuous_upperBounds` -> `Dense.upperBounds_image`. A naming norm."),
    Classification("bd8a8d8cf88c", 33145, ("family_design", "generality"), "family", "diff",
        "patch_set",
        "Refactor into `Dense.ciSup`/`Dense.ciInf` and obtain the infimum by order duality. "
        "The maintainer supplied signatures and the dual proof in suggestion blocks, so the "
        "information is in the review; delivering it is still a multi-declaration edit."),
    Classification("8d887ce4bdd9", 33145, ("generality",), "site", "diff", "single_edit",
        "Generalise the supremum result into a typeclass-polymorphic `ciSup'`. The "
        "over-specialisation is visible in the one statement."),
    Classification("7fef913e9651", 33145, ("family_design", "generality"), "family", "diff",
        "patch_set",
        "Add `ciInf'` and prove it from `ciSup'` in the order dual. A claim about a pair, "
        "one of which does not exist yet."),
    Classification("e8e028215fa3", 33145, ("proof_idiom",), "site", "diff", "single_edit",
        "Restructure the proof around a `by_cases` on `BddAbove`. Deep but local."),

    # --- PR 33149 -------------------------------------------------------------------------
    Classification("3dacf72e309f", 33149, ("correctness",), "file", "diff", "deletion",
        "Remove newly introduced `axiom` declarations. `correctness` is the only arm that "
        "compiles the reviewed file and the only one whose warrant covers an unaccepted "
        "axiom."),
    Classification("61f68eedbddd", 33149, ("correctness", "api_reuse"), "file", "repository",
        "single_edit",
        "Replace an axiomatised Parseval identity with Mathlib's own. Needs the library."),
    Classification("f54010d8cfb9", 33149, ("correctness",), "file", "repository", "deletion",
        "Remove the remaining named axioms and prove them or cite existing results."),

    # --- PR 33285 -------------------------------------------------------------------------
    Classification("073625ede35e", 33285, ("proof_golf",), "site", "diff", "single_edit",
        "Golf a tactic block to a direct lambda. Length, locally."),
    Classification("585e5e0b5b8b", 33285, ("proof_golf", "proof_idiom"), "site", "repository",
        "single_edit",
        "Replace a manual injectivity/`ext`/`rfl` tail with a single `simp [...]`. Choosing "
        "the simp set needs the library."),

    # --- PR 33294 -------------------------------------------------------------------------
    Classification("7f098f6a7437", 33294, ("naming",), "convention", "convention", "rename",
        "Make `isFundamentalSequence_of_isNormal` dot-notation. A stated norm; flat "
        "`*_of_*` names dominate numerically, so frequency argues against it."),
    Classification("8e276803d0f4", 33294, ("proof_idiom",), "site", "convention",
        "single_edit",
        "`rw [Order.IsNormal.map_iSup h ...]` -> `rw [h.map_iSup ...]`. Dot-notation at a "
        "call site: idiom, not length."),

    # --- PR 33305 -------------------------------------------------------------------------
    Classification("cc44bb996114", 33305, ("docs", "style"), "site", "convention",
        "single_edit",
        "Wrap an over-long doc comment line. The project's own linter settles it."),

    # --- PR 33321 -------------------------------------------------------------------------
    Classification("c9739efcd0a6", 33321, ("docs",), "site", "diff", "single_edit",
        "Complete a docstring sentence that stops mid-thought."),
    Classification("5ffba48eb1e1", 33321, ("generality", "api_reuse"), "site", "diff",
        "single_edit",
        "Redefine `baseOf` as a set comprehension rather than via the predicate. A "
        "representation change to one definition."),
    Classification("0bb42bd28332", 33321, ("docs",), "file", "diff", "single_edit",
        "NOT HITTABLE -- see obligation_hittability_v1.json. The comment is a one-line "
        "wording suggestion; the obligation demands an 'Implementation details' section, and "
        "its own outcome records it dropped because the wording fix was adopted. Classified "
        "for completeness and excluded from every capability count."),

    # --- PR 33337 -------------------------------------------------------------------------
    Classification("ce7b5d2e038d", 33337, ("naming",), "convention", "convention", "rename",
        "`toLinearMap_` prefix. The corpus argues the other way -- `coe_` outnumbers the "
        "requested form 4707 to 50 -- so this is decided by migration direction, not count."),
    Classification("64e1164fcb58", 33337, ("naming",), "convention", "convention", "rename",
        "The sibling rename under the same norm."),

    # --- PR 33362 -------------------------------------------------------------------------
    Classification("695ae9fd914c", 33362, ("style",), "file", "diff", "single_edit",
        "Move declarations inside `namespace Complex`. A placement defect, which is in "
        "`style`'s subject kinds."),

    # --- PR 33421 -------------------------------------------------------------------------
    Classification("6b02b6118fcd", 33421, ("naming",), "convention", "convention", "rename",
        "`round_eq'` -> `round_eq_div`. The norm that primed names should be made "
        "descriptive is stated in review (PR 17669), not derivable from frequency."),
    Classification("38e72250fc9d", 33421, ("family_design", "duplication"), "family", "diff",
        "patch_set",
        "Factor the repeated `Tendsto (2 * ·)` argument out of the `tendsto_round_*` proofs "
        "into one reusable lemma. The repetition is only visible across several proofs."),
    Classification("55f6530478b3", 33421, ("generality",), "site", "diff", "single_edit",
        "Generalise `two_mul_fract_eq_one_iff_exists_int` to `mul_fract_...`. Visible in the "
        "one statement."),
)

_BY_LEAD: Dict[str, Classification] = {row.lead_obligation: row for row in CLASSIFICATION}


@dataclass
class Group:
    """One maintainer request, with the obligations it expanded into."""

    group_id: str
    pr_number: int
    source_event_id: Optional[str]
    obligation_ids: List[str]
    claims: List[str]
    classification: Optional[Classification]

    @property
    def size(self) -> int:
        return len(self.obligation_ids)

    def render(self, hittability: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        hittable = (None if hittability is None
                    else sum(1 for item in self.obligation_ids
                             if hittability.get(item, True)))
        row: Dict[str, Any] = {
            "group_id": self.group_id,
            "pr_number": self.pr_number,
            "source_event_id": self.source_event_id,
            "obligations": self.size,
            "hittable_obligations": hittable,
            "obligation_ids": list(self.obligation_ids),
            "claims": list(self.claims),
        }
        if self.classification is None:
            row["unclassified"] = True
            return row
        row.update({
            "answerable_arm_ids": list(self.classification.answerable_arm_ids),
            "required_scope": self.classification.required_scope,
            "required_information": self.classification.required_information,
            "required_output": self.classification.required_output,
            "why": self.classification.why,
        })
        return row


def build(release: Path) -> List[Group]:
    """Group the release's eligible obligations by the comment that produced them."""

    judgments = load_jsonl(release / "gold/judgments.jsonl", JudgmentNode)
    views = load_jsonl(release / "gold/intervention_views.jsonl", InterventionView)
    included = {obligation_id for view in views
                if view.evaluation_eligibility == "included"
                for obligation_id in view.obligation_ids}

    buckets: "collections.OrderedDict[Tuple[int, str], List[Any]]" = collections.OrderedDict()
    events: Dict[Tuple[int, str], Optional[str]] = {}
    for judgment in sorted(judgments, key=lambda item: item.pr_number):
        for obligation in judgment.obligations:
            if obligation.status != "proposed_atomic":
                continue
            if obligation.obligation_id not in included:
                continue
            event = (obligation.source_event_ids or [None])[0]
            key = (judgment.pr_number, event or f"judgment:{judgment.judgment_id}")
            buckets.setdefault(key, []).append(obligation)
            events[key] = event

    groups = []
    for (pr_number, key), obligations in buckets.items():
        lead = obligations[0].obligation_id[len("obligation:"):][:12]
        groups.append(Group(
            group_id=lead, pr_number=pr_number, source_event_id=events[(pr_number, key)],
            obligation_ids=[item.obligation_id for item in obligations],
            claims=[item.claim or "" for item in obligations],
            classification=_BY_LEAD.get(lead),
        ))
    return groups


def answerable_by(groups: Iterable[Group]) -> Dict[str, List[str]]:
    """`arm_id -> group_ids it could answer`. The bench's fixture selector."""

    index: Dict[str, List[str]] = collections.defaultdict(list)
    for group in groups:
        if group.classification is None:
            continue
        for arm in group.classification.answerable_arm_ids:
            index[arm].append(group.group_id)
    return {arm: sorted(rows) for arm, rows in sorted(index.items())}


def report(groups: Sequence[Group],
           hittability: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
    classified = [group for group in groups if group.classification]
    return {
        "schema_version": REQUEST_GROUP_VERSION,
        "classified_by": "claude",
        "note": (
            "Evaluation-only and gold-derived. Never read by generation. Answerable arms are "
            "audited from the maintainer comment, not from the gold concern label -- 13 of "
            "PR33098's 14 obligations carry `style`, the seven `grind` requests included."
        ),
        "groups": len(groups),
        "obligations": sum(group.size for group in groups),
        "unclassified": [group.group_id for group in groups if not group.classification],
        "multi_obligation_groups": [
            {"group_id": group.group_id, "pr_number": group.pr_number,
             "obligations": group.size}
            for group in groups if group.size > 1
        ],
        "by_required_scope": dict(sorted(collections.Counter(
            group.classification.required_scope for group in classified).items())),
        "by_required_information": dict(sorted(collections.Counter(
            group.classification.required_information for group in classified).items())),
        "by_required_output": dict(sorted(collections.Counter(
            group.classification.required_output for group in classified).items())),
        "answerable_by_arm": {
            arm: len(rows) for arm, rows in answerable_by(groups).items()
        },
        "groups_detail": [group.render(hittability) for group in groups],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--release", type=Path,
                        default=Path("inputs/pr_review_v4/releases/dev-medium-0.3.0"))
    parser.add_argument("--detail", action="store_true")
    args = parser.parse_args()

    from src.mathlib_review.judge.semantic_judge import load_hittability

    groups = build(args.release)
    payload = report(groups, load_hittability())
    if not args.detail:
        payload.pop("groups_detail")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
