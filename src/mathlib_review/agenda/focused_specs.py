"""Versioned focused-agent specs, and the gold-free rule that decides where each one runs.

The deterministic arm covers no proof simplification at all — five of the six unreached asks
on the development PR are "simplify this proof using `grind`". The v2 generation had focused
LLM checkers that construct and kernel-verify a replacement, and their measured record is
specific: on the 57-PR corpus they tripled V2-stratum recall over the holistic arm (14% vs
4%) at ~9% precision, and their recall barely moved between models because the kernel gate,
not the model, bounds what they emit.

This module carries the *scheduling* half. Three properties it exists to guarantee:

1. **Scheduling is gold-free.** Sites come from the change graph's modification inventory,
   which is built from graphs alone. An agent is never activated because gold says an issue
   of that kind occurred there — that would be the leak the episode split exists to prevent,
   reintroduced through the back door of "we only run the checker where it is needed".
2. **Specs are not `InvestigationMethod`s.** Registering them there would pull them into
   `validate_schedule`'s exact-coverage check and into the C0–C2 census, and would flip
   `investigations.SMOKE_EXPECTATIONS`' `proof_compression.v1` entry from `planned_method_gap`
   to `unexpectedly_implemented_without_task`, failing the smoke gate. The reserved IDs
   `proof_compression.v1` and `structural_rewrite.v1` are deliberately not reused.
3. **The plan carries prompt hashes, not prompt text.** `contracts.assert_gold_free`
   substring-sweeps a serialized generation plan, and the focused prompts are full of words
   like "would a maintainer say" and "maintainers routinely ask". Shipping the hash keeps the
   contract verifiable without tripping a leak check on prose.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Optional, Tuple

from src.mathlib_review.io import canonical_json_bytes, sha256_bytes
from src.mathlib_review.schema import ModificationRecord, ReviewWorkUnit

SPEC_REGISTRY_VERSION = "focused-agent-specs/1"
SCHEDULER_VERSION = "focused-agent-scheduler/1"

#: Subject kinds that are declarations a duplication or generality claim could be about.
DECLARATION_KINDS: FrozenSet[str] = frozenset({
    "theorem", "definition", "instance", "structure_or_class", "inductive", "abbreviation",
})


@dataclass(frozen=True)
class FocusedAgentSpec:
    """One focused checker: what it claims, and where it is allowed to run."""

    spec_id: str
    spec_version: str
    task_type: str
    concern_family: str
    issue_kind: str
    #: Which lifecycles this spec applies to, and which changed component it needs.
    lifecycles: FrozenSet[str]
    component: Optional[str]
    subject_kinds: FrozenSet[str]
    prompt_sha256: str
    tools_sha256: str
    rationale: str

    def applies_to(self, modification: ModificationRecord) -> bool:
        if modification.lifecycle not in self.lifecycles:
            return False
        if modification.subject_kind not in self.subject_kinds:
            return False
        if self.component is None:
            return True
        return any(
            item.component == self.component and item.status in {"added", "modified"}
            for item in modification.component_deltas
        )

    def identity(self) -> Dict:
        return {
            "spec_id": self.spec_id,
            "spec_version": self.spec_version,
            "task_type": self.task_type,
            "concern_family": self.concern_family,
            "issue_kind": self.issue_kind,
            "lifecycles": sorted(self.lifecycles),
            "component": self.component,
            "subject_kinds": sorted(self.subject_kinds),
            "prompt_sha256": self.prompt_sha256,
            "tools_sha256": self.tools_sha256,
        }

    @property
    def source_sha256(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.identity()))


def prompt_hashes() -> Dict[str, Tuple[str, str]]:
    """Hash each prompt pair and tool list, without importing the text into any artifact.

    The text is read from `pr_shared`, not from the generation that first shipped it. The
    prompts are an asset both arms reuse; a code edge into v2 would keep that generation
    un-archivable, and a private copy would let the two texts drift apart while the whole
    point of reusing them is that the focused arm stays comparable to v2's measured baseline.

    Only the hashes leave this function. `contracts.assert_gold_free` substring-sweeps the
    serialized plan, and a spec carrying its own prompt text would put the reviewer's
    instructions into an artifact that is supposed to contain identities alone.

    **What the tools hash is, and is not.** It hashes the tool list the *prompt* declares --
    `FOCUSED_PROMPTS[arm][0]` -- which is not the list the arm runs with. Workspace tools come
    from `task_config.enabled_tools` in the run config, and retrieval tools from
    `arm_registry`. For `naming`, `docs` and `style` this list holds four entries while those
    arms run with six plus their grants.

    That is a naming problem and not a provenance hole, which is worth stating because it
    looks like one. Both real lists are sealed elsewhere: the workspace tools through
    `scaffold_config_sha256`, which hashes the scaffold including `task_config_overrides`, and
    the per-arm grant through `ReviewArm.context_tools`, which is inside the agenda the plan
    hashes. Changing either moves a recorded identity. Re-pointing this hash at the real lists
    would move all ten spec identities and the agenda hash to fix a field name, so it is
    deliberately not done.
    """

    from ape.tasks.lean_tasks.formal_math.review.focused_prompts import FOCUSED_PROMPTS

    return {
        name: (
            sha256_bytes(canonical_json_bytes({"system": system, "user": user})),
            sha256_bytes(canonical_json_bytes(sorted(tools))),
        )
        for name, (tools, system, user) in FOCUSED_PROMPTS.items()
    }


def default_specs() -> List[FocusedAgentSpec]:
    """The four focused checkers, with the scope each is measured to be good for.

    **golf and idiom are scheduled on `modified` proofs only.** v2's 14% V2-stratum recall
    was measured with golf looking at proofs the PR *changed*. On a brand-new proof the
    question is different and much weaker — there is no prior version it is a simplification
    of — and because a newly added declaration reports every component as `added`, scheduling
    both lifecycles would put all four specs on all 131 added theorems at medium.

    duplication and generality want exactly the opposite: they ask whether something *new*
    should exist in this form, which is only a question for an added declaration.
    """

    hashes = prompt_hashes()
    return [
        FocusedAgentSpec(
            spec_id="proof_golf",
            spec_version="focused/1",
            task_type="lean_pr_review_v4_focused",
            concern_family="proof-golf",
            issue_kind="proof_simplification",
            lifecycles=frozenset({"modified"}),
            component="proof",
            subject_kinds=DECLARATION_KINDS,
            prompt_sha256=hashes["proof_golf"][0],
            tools_sha256=hashes["proof_golf"][1],
            rationale="Can a proof this PR changed be written shorter? Verified by recompiling.",
        ),
        FocusedAgentSpec(
            spec_id="proof_idiom",
            spec_version="focused/1",
            task_type="lean_pr_review_v4_focused",
            concern_family="proof-golf",
            issue_kind="proof_simplification",
            lifecycles=frozenset({"modified"}),
            component="proof",
            subject_kinds=DECLARATION_KINDS,
            prompt_sha256=hashes["proof_idiom"][0],
            tools_sha256=hashes["proof_idiom"][1],
            rationale=(
                "Is a changed proof written the canonical way — `grw`/`gcongr`, `simp`, "
                "`omega`/`grind`, `fun_prop`, the canonical lemma? Explicitly not about "
                "length, which is why it needs its own warrant."
            ),
        ),
        FocusedAgentSpec(
            spec_id="duplication",
            spec_version="focused/1",
            task_type="lean_pr_review_v4_focused",
            concern_family="duplication",
            issue_kind="duplicate_implementation",
            lifecycles=frozenset({"added"}),
            component=None,
            subject_kinds=DECLARATION_KINDS,
            prompt_sha256=hashes["duplication"][0],
            tools_sha256=hashes["duplication"][1],
            rationale=(
                "Does a new declaration restate something Mathlib already has? Verified by "
                "closing the new declaration with the existing one."
            ),
        ),
        FocusedAgentSpec(
            spec_id="generality",
            spec_version="focused/1",
            task_type="lean_pr_review_v4_focused",
            concern_family="generalization",
            issue_kind="generalization_available",
            lifecycles=frozenset({"added"}),
            component=None,
            subject_kinds=DECLARATION_KINDS,
            prompt_sha256=hashes["generality"][0],
            tools_sha256=hashes["generality"][1],
            rationale=(
                "Is a new declaration stated less generally than it should be? The statement "
                "must move, which is the gate that separates it from a golf finding."
            ),
        ),
    ]


@dataclass(frozen=True)
class FocusedInvocation:
    """One scheduled agent call: a spec, a work unit, and the sites it may speak about."""

    invocation_id: str
    spec_id: str
    work_unit_id: str
    episode_id: str
    pr_number: int
    site_change_ids: Tuple[str, ...]
    source_sha256: str


def schedule_focused(
    specs: Iterable[FocusedAgentSpec],
    modifications: Iterable[ModificationRecord],
    work_units: Iterable[ReviewWorkUnit],
    pr_numbers: Optional[Iterable[int]] = None,
) -> List[FocusedInvocation]:
    """One invocation per (spec, work unit) that has at least one applicable site.

    A unit with no applicable site is not scheduled at all — that is the whole point of
    enumerating from the inventory rather than running every spec everywhere.

    The invocation ID is `wu:…#spec`, which is also the composite key the run plan needs:
    `prompt_sha256_by_work_unit` maps one hash per work unit, so four specs on one unit would
    otherwise collide there and trip the one-successful-response-per-unit rule.
    """

    wanted = set(pr_numbers) if pr_numbers else None
    units = [unit for unit in work_units if wanted is None or unit.pr_number in wanted]
    unit_by_change: Dict[str, ReviewWorkUnit] = {
        change_id: unit for unit in units for change_id in unit.change_ids
    }
    modifications = [
        item for item in modifications if item.primary_change_id in unit_by_change
    ]

    invocations: List[FocusedInvocation] = []
    for spec in sorted(specs, key=lambda item: item.spec_id):
        sites_by_unit: Dict[str, List[str]] = {}
        for modification in modifications:
            if not spec.applies_to(modification):
                continue
            unit = unit_by_change[modification.primary_change_id]
            sites_by_unit.setdefault(unit.work_unit_id, []).append(
                modification.primary_change_id
            )
        for work_unit_id, change_ids in sorted(sites_by_unit.items()):
            unit = next(item for item in units if item.work_unit_id == work_unit_id)
            payload = {
                "scheduler_version": SCHEDULER_VERSION,
                "spec_id": spec.spec_id,
                "spec_sha256": spec.source_sha256,
                "work_unit_id": work_unit_id,
                "site_change_ids": sorted(change_ids),
            }
            invocations.append(FocusedInvocation(
                invocation_id=f"{work_unit_id}#{spec.spec_id}",
                spec_id=spec.spec_id,
                work_unit_id=work_unit_id,
                episode_id=unit.episode_id,
                pr_number=unit.pr_number,
                site_change_ids=tuple(sorted(change_ids)),
                source_sha256=sha256_bytes(canonical_json_bytes(payload)),
            ))
    return invocations


def schedule_report(invocations: Iterable[FocusedInvocation],
                    control_pr_numbers: Iterable[int] = ()) -> Dict:
    """What the schedule would cost and where it would speak — before anything is spent."""

    invocations = list(invocations)
    controls = set(control_pr_numbers)
    by_spec: Dict[str, int] = {}
    sites_by_spec: Dict[str, int] = {}
    by_pr: Dict[int, int] = {}
    for item in invocations:
        by_spec[item.spec_id] = by_spec.get(item.spec_id, 0) + 1
        sites_by_spec[item.spec_id] = sites_by_spec.get(item.spec_id, 0) + len(
            item.site_change_ids
        )
        by_pr[item.pr_number] = by_pr.get(item.pr_number, 0) + 1
    return {
        "scheduler_version": SCHEDULER_VERSION,
        "invocations": len(invocations),
        "invocations_by_spec": dict(sorted(by_spec.items())),
        "sites_by_spec": dict(sorted(sites_by_spec.items())),
        "invocations_by_pr": dict(sorted(by_pr.items())),
        # Reported, never hidden: the focused arm is silent on most controls by
        # *enumeration*, not by judgment, so its control rate is not comparable with the
        # holistic arm's without saying so.
        "control_invocations": {
            pr: by_pr.get(pr, 0) for pr in sorted(controls)
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Schedule focused agents from the change graph")
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--pr-numbers", nargs="*", type=int, default=[])
    parser.add_argument("--control-pr-numbers", nargs="*", type=int, default=[])
    args = parser.parse_args()

    from src.mathlib_review.io import load_jsonl

    units = load_jsonl(args.release / "derived/work_units.jsonl", ReviewWorkUnit)
    modifications = load_jsonl(args.inventory, ModificationRecord)
    invocations = schedule_focused(
        default_specs(), modifications, units, args.pr_numbers or None
    )
    print(json.dumps(schedule_report(invocations, args.control_pr_numbers), indent=2))


if __name__ == "__main__":
    main()
