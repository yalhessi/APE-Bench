"""The one command that runs a v5 review, in any of its three routing modes.

    ./ape/bin/python -m src.mathlib_review.review.runner --config configs/pr_review_v5.yaml

Two things this deliberately does differently from the pipeline it descends from.

**One run identity.** `run_name` derives the orchestrator scratch dir, the results dir, the
sealed plan, the arm pool and the context trace. v4 spells a run's identity three times —
`dataset.run_name`, the parent of `dataset.output_file`, and the release name repeated in up
to eight downstream `--path` flags — with nothing enforcing that they agree, so a run can be
assembled from artifacts that were never part of it.

**`--dry-run` is a flag, not a default.** v4's checked-in configs set `dry_run: true`, which
makes every real run a command-line override, and of the two override spellings the docs
carry only one actually parses. Here the safe thing is explicit and the default is the thing
you meant.

The three modes share one execution and finalization path, and one pre-rendered prompt pool,
so a difference between them is a difference in routing and nothing else.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, BaseModel, Field

from ape.orchestration import TaskOrchestrator
from ape.orchestration.execution_index import INDEX_FILENAME as EXECUTION_INDEX_FILENAME
from ape.orchestration.models import EXECUTION_LIMITS_KEY
from ape.tasks.base import create_task_from_data
from ape.utils import parse_cli_args
from ape.llm_clients.config import COST_MODELS
from ape.utils.config_loader import deep_merge, load_yaml
from ape.utils.logging import create_logger

from src.mathlib_review.io import (
    canonical_json_bytes,
    git_state,
    jsonl_bytes,
    jsonl_rows,
    load_jsonl,
    pretty_json_bytes,
    sha256_bytes,
    sha256_file,
    write_once,
)
from src.mathlib_review.schema import (
    ChangeGraph,
    ModificationRecord,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewWorkUnit,
)

from src.mathlib_review.agenda.agenda import agenda_report, build_agenda, initial_jobs
from src.mathlib_review.review.candidates import anchoring_report
from src.mathlib_review.agenda.arms import GENERALIST_ARM_ID
from src.mathlib_review.agenda.census import build_census, census_report
from src.mathlib_review.review.coordination import CoordinationConfig, assert_implemented
from src.mathlib_review.agenda.cutoffs import cutoffs_by_episode
from src.mathlib_review.evidence.chain import collect_supported, reviewed_workspaces
from src.mathlib_review.review.finalize import finalize
from src.mathlib_review.paths import PRECEDENT_INDEX, run_dir
from src.mathlib_review.review.preflight import (
    assert_ready, assert_reviewed_workspaces_prebuilt, assert_workspaces_prebuilt,
)
from src.mathlib_review.schema.review import ROUTING_MODES, V5RunManifest, V5RunPlan
from src.mathlib_review.review.trace import reconcile
from src.mathlib_review.run_config import load_run as _load_run

LEAD_TASK_TYPE = "lean_pr_review_v5_lead"


class V5DatasetConfig(BaseModel):
    # `extra="forbid"`, because the half of the config that spends money was the unvalidated
    # half. A misspelled key was silently ignored and the field fell back to its default:
    # `per_pr_cost_capp: 1.50` left the cap at 8.0, authorising five times the intended
    # budget, while `ExecutionConfig` rejected the same typo one block away in the same file.
    model_config = ConfigDict(extra="forbid")

    #: `fanout` (every arm everywhere) | `rules` (the deterministic rule's selection) |
    #: `lead` (the mandatory floor plus whatever the lead keeps or adds).
    routing_mode: str = "lead"
    release: Path
    #: The modification inventory is a treatment artifact, not part of a release, and it is
    #: what specialist eligibility is enumerated from.
    modification_inventory: Path
    #: The frozen deterministic execution release, so the non-model arm is identical in all
    #: three modes. Optional: without it the comparison is model-arms-only, which is a
    #: narrower claim but still a clean one.
    execution_release: Optional[Path] = None
    exclude_methods: List[str] = Field(default_factory=list)
    pr_numbers: List[int] = Field(default_factory=list)
    work_unit_limit: int = 0
    #: Supplied at the invocation (`--run-name`), not checked into the config.
    #:
    #: The sentinel is deliberate: a real default means a config that forgets to name its run
    #: lands on top of whatever ran under the default last. Configs used to name their own run,
    #: so every paid repetition needed its own file and four of them went on naming an
    #: already-spent run.
    run_name: str = "UNNAMED"
    dry_run: bool = False
    require_prebuilt_workspaces: bool = True
    #: Refuse a run whose episodes have no reviewed workspace -- base + diff + changed modules
    #: rebuilt. Without one, verification resolves imports against the base commit's `.olean`s
    #: and a declaration the PR renames in a sibling file reads as `Unknown constant`
    #: everywhere else (41 of 321 arm sessions on the held-out run; 16 false build-failure
    #: findings). Off by default only until the workspaces for the sets in use are prebuilt;
    #: `plan` reports how many are missing either way, and a run that proceeds without them
    #: is told so at WARNING per attempt. Flip it on in the base config once they exist.
    require_reviewed_workspaces: bool = False
    pr_finding_limit: int = 20
    #: Skip the evidence chain, restoring the closed gate every run before this one
    #: had. Kept so the eight runs already measured can be reproduced exactly, and
    #: because the chain compiles and lints per candidate — real time on a large set.
    #: Default off: a closed gate should be a choice someone made, not the default
    #: that made "no collector ran" indistinguishable from "the claim failed".
    skip_evidence_chain: bool = False
    #: Measure how much of the library references each changed declaration, from the base
    #: commit's `.ilean` index, and let that raise a proposal's priority.
    #:
    #: Off by default because it is the only input whose cost is visible: ~4.4s per distinct
    #: base commit, and a release has 14, so about a minute added to every plan build. The
    #: dry run must build the *same* plan as the real run — a dry run that skipped a routing
    #: input is how a config bug survives to a paid run — so this cannot be skipped for dry
    #: runs alone. Turn it on in the run config.
    use_exposure_index: bool = False
    #: Schedule the mandatory per-work-unit generalist. On by default: it is the coverage
    #: floor and every measurement so far was taken with it running.
    #:
    #: Turning it off makes a **specialist-only** run, which is the only way to ask whether
    #: the generalist's lead in gold-reaching candidates is quality or volume. smoke4 said
    #: volume: per candidate the two are indistinguishable (0.08 against 0.09), and the
    #: generalist's 4x lead per invocation comes entirely from emitting 2.0 candidates per
    #: run against the specialists' 0.5.
    #:
    #: Only turn it off on a set where the specialists already cover every work unit —
    #: `agenda_report` reports `units_without_specialist`, and a run that leaves units
    #: unreviewed measures coverage loss, not arm quality.
    #: Apply the lead's assessments, or only record them.
    #:
    #: **Off since 2026-09-08, under investigation.** `pr5_smoke4_rep9` was the first run to
    #: apply them: 54 candidates became 27 issues, and of the six obligations the run hit,
    #: **two are hit only by a candidate the lead removed** -- one dropped, and four of the
    #: five gold-matching removals were `duplicate_of` folds into a representative that did
    #: not itself match. Folding is meant to be lossless and was not.
    #:
    #: rep6 and rep7, the best runs on this set, recorded assessments and applied none of
    #: them, and scored 6 and 7 issue hits against rep9's 6 (4 after removals).
    #:
    #: Recording continues either way: `candidate_assessments.jsonl` is written regardless,
    #: because the question is whether the lead's judgment is *good*, and answering that needs
    #: the judgments whether or not they are acted on.
    apply_lead_synthesis: bool = False
    generalist_floor: bool = True
    #: Cost policy. Both are required for a real run; a lead with no cap can spend the whole
    #: run on one work unit.
    standard_budget_cap: float = 0.25
    lead_cost_cap: float = 2.0
    per_pr_cost_cap: float = 8.0
    max_delegations: int = 60
    #: `solo` only. The per-task billed ceiling for a whole-PR reviewer, and the instrument of
    #: the cost-matched comparison: set it to the *measured* billed per-PR spend of the `lead`
    #: run it is being compared against, not to `per_pr_cost_cap`, which is a ceiling no run
    #: has ever exhausted. Measured on the reference runs: $0.767/PR (`pr5_smoke4_rep9`) and
    #: $0.784/PR (`heldout11_rep2`), with a per-PR maximum of $1.445.
    solo_cost_cap: float = 1.50
    #: `solo` only. The retrieval grant, defaulting to the generalist arm's four — the
    #: scheduled design's own control keeps all of them "because that is the point of a
    #: control", and a narrower grant here would make an information difference read as an
    #: architecture difference. Empty disables retrieval entirely.
    solo_context_tools: List[str] = Field(
        default_factory=lambda: ["zulip_search", "precedent_search", "declaration_search",
                                 "proof_profile"])
    #: The whole run's ceiling, in billed dollars. 0 disables it.
    #:
    #: The last unbounded budget. `per_pr_cost_cap` binds only *discretionary* work — the
    #: coverage floor is deliberately exempt, because charging coverage to the routing
    #: allowance once left PR 33149 with a $10.05 floor against a $1.50 cap and therefore zero
    #: specialists. That exemption is right and it left nothing bounding the floor at all: it
    #: scales with work units times required arms, so a large PR set can authorise an
    #: arbitrary amount of mandatory work that no cap refuses.
    #:
    #: Checked in preflight against the agenda's own floor estimate, so a run that cannot fit
    #: is refused before the first model call rather than discovered on the invoice.
    run_total_cost_cap: float = 0.0


def load_run(config_path: Path, overrides: Optional[Dict[str, Any]] = None):
    """Load a v5 generation run. The convention itself is in `mathlib_review.run_config`, which existed
    three times byte-identical except for the model validated against."""

    return _load_run(config_path, V5DatasetConfig, overrides)


def load_release(dataset: V5DatasetConfig):
    release = dataset.release
    return {
        "units": load_jsonl(release / "derived/work_units.jsonl", ReviewWorkUnit),
        "episodes": load_jsonl(release / "input/episodes.jsonl", ReviewEpisodeInput),
        "graphs": load_jsonl(release / "derived/change_graphs.jsonl", ChangeGraph),
        "release_prompts": load_jsonl(release / "derived/rendered_prompts.jsonl", RenderedPrompt),
        "modifications": load_jsonl(dataset.modification_inventory, ModificationRecord),
    }


def select_units_and_episodes(dataset: V5DatasetConfig, release: Dict[str, Any]):
    """The work units a config selects, and the episodes those units belong to.

    One function because two things must agree on it: the run, which schedules the units, and
    the reviewed-workspace prebuild, which must build a workspace for exactly the episodes the
    run will verify in. `work_unit_limit` can drop a PR entirely, so the episode set follows
    from the unit set rather than from `pr_numbers` directly.
    """

    units = release["units"]
    if dataset.pr_numbers:
        wanted = set(dataset.pr_numbers)
        units = [unit for unit in units if unit.pr_number in wanted]
    if dataset.work_unit_limit:
        units = units[:dataset.work_unit_limit]
    if not units:
        raise ValueError("no work units selected; check dataset.pr_numbers")
    selected_prs = {unit.pr_number for unit in units}
    episodes = [item for item in release["episodes"] if item.pr_number in selected_prs]
    return units, episodes


def _context_index_identity() -> Dict[str, str]:
    """Hashes of the corpora a context read ranks over.

    Recorded in the plan because a retrieval result is only interpretable relative to the
    index that produced it: rebuild the index and the same query returns something else,
    with nothing in the run saying so.
    """

    identity: Dict[str, str] = {}
    manifest = PRECEDENT_INDEX / "manifest.json"
    if manifest.is_file():
        payload = json.loads(manifest.read_text())
        identity["precedent_corpus"] = payload.get("corpus_sha256", "")
        identity["precedent_model"] = payload.get("model_name", "")
        # The corpus sha and the model name do not move when the *recipe* does: re-embedding
        # a different slice of each hunk, or adding a metadata field the query path filters
        # on, changes every answer while leaving both untouched. This field exists to say a
        # retrieval regime changed, so it has to carry the things that change it.
        identity["precedent_index_version"] = payload.get("index_version", "")
        identity["precedent_meta_version"] = payload.get("meta_version", "")
        identity["precedent_model_revision"] = payload.get("model_revision", "")
        identity["precedent_rows"] = str(payload.get("rows", ""))
    from src.datasets.zulip.config import ZulipConfig

    zulip = Path(ZulipConfig().sqlite_path)
    if zulip.is_file():
        zulip_manifest = Path("inputs/zulip/manifest.json")
        if zulip_manifest.is_file():
            identity["zulip_corpus"] = sha256_file(zulip_manifest)
    return identity


def _write_pool(path: Path, pool: Dict[str, Dict[str, Any]], cutoff_by_episode: Dict[str, str],
                trace_path: Path) -> None:
    """Write the runnable arm payloads, with the gate instant baked into each one.

    The cutoff arrives as data rather than being resolved inside the worker, so a worker
    process can neither choose its own instant nor silently proceed without one.
    """

    rows = []
    for invocation_id, payload in sorted(pool.items()):
        data = dict(payload)
        data["retrieval_cutoff"] = cutoff_by_episode.get(data.get("episode_id"))
        data["trace_path"] = str(trace_path)
        rows.append({
            "invocation_id": invocation_id,
            "arm_id": data["arm_id"],
            "work_unit_id": data["work_unit_id"],
            "spec_id": data.get("spec_id"),
            "rendered_prompt_sha256": data.get("rendered_prompt_sha256"),
            "task_data": data,
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n")


def _slug(episode_id: str) -> str:
    """One path segment from an episode id.

    `ep:leanprover-community/mathlib4#33057#round1#<sha>` contains a slash, and replacing only
    the colon left it as a directory separator -- so the journals landed under
    `lead_journals/leanprover-community/`. Harmless in itself (the writer creates parents and
    the reader uses the same string), and exactly the kind of thing that becomes a bug the
    first time something globs the directory.
    """

    return re.sub(r"[^A-Za-z0-9_.-]+", "_", episode_id).strip("_")


def _lead_task_data(agenda, episodes, dataset, pool_path: Path, trace_path: Path,
                    cutoff_by_episode: Dict[str, str],
                    census_by_pr: Optional[Dict[int, List[Dict[str, Any]]]] = None,
                    journal_dir: Optional[Path] = None,
                    ) -> List[Dict[str, Any]]:
    """One lead per episode. A review round is the unit a maintainer actually reviews.

    One journal per episode too. A lead's state is its own — its spend against the per-PR cap,
    its dedup set, whether its floor has run — so a shared file would replay one PR's
    delegations into another PR's lead.
    """

    episode_by_id = {item.episode_id: item for item in episodes}
    by_episode: Dict[str, List[Any]] = {}
    for proposal in agenda.proposals:
        by_episode.setdefault(proposal.episode_id, []).append(proposal)

    data = []
    for episode_id, proposals in sorted(by_episode.items()):
        episode = episode_by_id[episode_id]
        data.append({
            "task_type": LEAD_TASK_TYPE,
            "task_id": f"pr5lead_{episode_id.replace(':', '_')}",
            "episode_id": episode_id,
            "pr_number": episode.pr_number,
            "pr_title": episode.title.text or "",
            "pr_description": episode.description.text or "",
            "diff": episode.diff,
            "changed_files": list(episode.changed_files),
            "snapshot_head_sha": episode.reviewed_head_sha,
            "snapshot_base_sha": episode.base_sha,
            "proposals": [item.model_dump(mode="json") for item in proposals],
            "census": (census_by_pr or {}).get(episode.pr_number, []),
            "arm_pool_path": str(pool_path),
            "routing_mode": agenda.routing_mode,
            "retrieval_cutoff": cutoff_by_episode.get(episode_id),
            "trace_path": str(trace_path),
            "journal_path": (
                str(journal_dir / f"{_slug(episode_id)}.jsonl")
                if journal_dir is not None else None
            ),
            # One index for the whole run, unlike the journal: it is a location map, and a
            # reader wants to resolve any invocation without knowing which lead ran it.
            "execution_index_path": (
                str(journal_dir.parent / EXECUTION_INDEX_FILENAME)
                if journal_dir is not None else None
            ),
            "target_workspace": {
                "name": "target",
                "commit_hash": episode.base_sha,
                "repo_url": "https://github.com/leanprover-community/mathlib4.git",
                "default_target": "Mathlib",
            },
        })
    return data


def _solo_task_data(agenda, episodes, dataset, cutoff_by_episode: Dict[str, str],
                    trace_path: Path) -> List[Dict[str, Any]]:
    """`solo`: one agent per episode, handed the whole PR and no work units.

    Built from the episodes rather than from `agenda.proposals`, because the proposals are the
    decomposition and this condition exists to do without it. The agenda is still built and
    still sealed -- it is what makes `agenda_report.json` scope identically to the `lead` run
    on the same config, which is the denominator the judge corroborates against.

    The retrieval cutoff is carried even though no work unit is: it is gold-free and it is what
    stops a retrieval tool answering from after the review happened.
    """

    from ape.tasks.lean_tasks.formal_math.review.solo import SOLO_TASK_TYPE

    wanted = {item.episode_id for item in agenda.proposals}
    data = []
    for episode in sorted(episodes, key=lambda item: item.episode_id):
        if episode.episode_id not in wanted:
            continue
        data.append({
            "task_type": SOLO_TASK_TYPE,
            "task_id": f"pr5solo_{episode.episode_id.replace(':', '_')}",
            "episode_id": episode.episode_id,
            "pr_number": episode.pr_number,
            "pr_title": episode.title.text or "",
            "pr_description": episode.description.text or "",
            "diff": episode.diff,
            "changed_files": list(episode.changed_files),
            "snapshot_head_sha": episode.reviewed_head_sha,
            "snapshot_base_sha": episode.base_sha,
            "context_tools": list(dataset.solo_context_tools),
            "retrieval_cutoff": cutoff_by_episode.get(episode.episode_id),
            # One invocation per episode, and both fields are load-bearing rather than
            # bookkeeping: every context tool stamps its trace row with `invocation_id` before
            # the best-effort write can swallow an error, so omitting it returned
            # `'SoloReviewData' object has no attribute 'invocation_id'` to the agent on every
            # retrieval call. The first paid run lost 3 of 3 that way and still closed clean.
            "invocation_id": f"{episode.episode_id}#{SOLO_ARM_ID}",
            "trace_path": str(trace_path),
            # Caps bind BILLED cost. The whole point of the condition is a cost-matched
            # comparison, so the ceiling is per task and stated by the run rather than
            # inherited from an orchestrator-wide setting.
            EXECUTION_LIMITS_KEY: {"billed_cost_limit": dataset.solo_cost_cap},
            "target_workspace": {
                "name": "target",
                "commit_hash": episode.base_sha,
                "repo_url": "https://github.com/leanprover-community/mathlib4.git",
                "default_target": "Mathlib",
            },
        })
    return data


def _direct_arm_task_data(agenda, pool: Dict[str, Dict[str, Any]],
                          cutoff_by_episode: Dict[str, str],
                          trace_path: Path) -> List[Dict[str, Any]]:
    """`fanout` and `rules`: run the arms straight, with no lead in the loop.

    Same payloads and the same pre-rendered prompts the lead would have dispatched, so these
    are controls for the routing decision and not for the prompt.
    """

    data = []
    for proposal in initial_jobs(agenda):
        payload = dict(pool[proposal.invocation_id])
        payload["retrieval_cutoff"] = cutoff_by_episode.get(payload.get("episode_id"))
        payload["trace_path"] = str(trace_path)
        data.append(payload)
    return data


def _responses_from_results(results, mode: str) -> List[Dict[str, Any]]:
    """Normalize both execution shapes into one list of arm responses."""

    responses: List[Dict[str, Any]] = []
    for result in results.task_results:
        raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        if mode == "lead":
            responses.extend(raw.get("arm_responses") or [])
        else:
            # A task that never reached a terminal submission carries no identity, so there
            # is nothing to attribute its (empty) output to. The failure itself is already
            # in the ledger via the delegation record, which is where a coverage failure
            # belongs; synthesizing a null-keyed response here made it look like an orphan
            # response instead and blocked reconciliation.
            if not raw.get("invocation_id"):
                continue
            responses.append({
                "invocation_id": raw.get("invocation_id"),
                "arm_id": raw.get("arm_id"),
                "work_unit_id": raw.get("work_unit_id"),
                "spec_id": raw.get("spec_id"),
                "pr_number": raw.get("pr_number"),
                "status": "success" if raw.get("success") else "failed",
                "candidates": raw.get("candidates") or [],
                "verification_artifacts": raw.get("verification_artifacts") or [],
                "rendered_prompt_sha256": raw.get("rendered_prompt_sha256"),
            })
    return responses


#: The arm a whole-PR reviewer's findings are filed under. Not `holistic`: that is the retired
#: spelling of `generalist` and `RETIRED_ARM_SPELLINGS` maps it away, so filing the baseline
#: there would make it indistinguishable from the treatment in every `by_arm` breakdown -- the
#: "an arm's whole output silently reads as zero" failure the derived `ARMS` exists to prevent.
#: Defined in `finalize`, which is the module that has to act on it, and re-exported here.
from src.mathlib_review.review.finalize import SOLO_ARM_ID  # noqa: E402


def _solo_responses(results, graphs, units, logger=None):
    """Anchor each whole-PR review and project it onto work units.

    Returns `(responses, anchor_rows)`. The responses are shaped exactly like an arm's, so
    `finalize` -- which resolves every response through `unit_by_id[work_unit_id]` and skips an
    unknown one with a warning only -- runs unchanged.
    """

    from src.mathlib_review.review.candidates import anchor_submitted_findings  # noqa: F401

    graph_by_episode = {graph.episode_id: graph for graph in graphs}
    units_by_episode: Dict[str, List[Any]] = {}
    for unit in units:
        units_by_episode.setdefault(unit.episode_id, []).append(unit)

    responses: List[Dict[str, Any]] = []
    anchor_rows: List[Dict[str, Any]] = []
    for result in results.task_results:
        raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        episode_id = raw.get("episode_id")
        if not raw.get("success") or not episode_id:
            # Booked as a coverage gap instead, which is what makes the run `partial`. A run
            # that silently recorded nothing here would be scored as a reviewer that found
            # nothing -- a statement about the budget or the harness presented as one about
            # the agent.
            continue
        graph = graph_by_episode.get(episode_id)
        if graph is None:
            if logger:
                logger.warning("solo: no change graph for episode %s — not anchored", episode_id)
            continue
        by_unit, rows = anchor_submitted_findings(
            raw.get("findings") or [], graph=graph,
            units=units_by_episode.get(episode_id, []), logger=logger)
        for row in rows:
            anchor_rows.append({**row, "episode_id": episode_id,
                                "pr_number": raw.get("pr_number")})
        unit_by_id = {unit.work_unit_id: unit
                      for unit in units_by_episode.get(episode_id, [])}
        for work_unit_id, findings in sorted(by_unit.items()):
            unit = unit_by_id[work_unit_id]
            responses.append({
                "invocation_id": f"{work_unit_id}#{SOLO_ARM_ID}",
                "arm_id": SOLO_ARM_ID,
                "work_unit_id": work_unit_id,
                "spec_id": SOLO_ARM_ID,
                "pr_number": raw.get("pr_number"),
                "status": "success",
                "candidates": [_solo_candidate(finding, unit) for finding in findings],
                "verification_artifacts": [],
                "rendered_prompt_sha256": None,
            })
    return responses, anchor_rows


def _solo_candidate(finding: Dict[str, Any], unit) -> Dict[str, Any]:
    """One anchored free-form finding, in the shape the candidate validator expects.

    `primary_subject` and `primary_entity_id` come from the work unit, never from the model:
    it was never told the subject, so requiring it to name one would be requiring it to guess
    the decomposition's vocabulary. Every other check the validator runs still applies.
    """

    change_id = finding["primary_change_id"]
    entity_ids = (unit.entity_ids_by_change or {}).get(change_id) or []
    return {
        "primary_change_id": change_id,
        "change_ids": finding["change_ids"],
        "primary_subject": (unit.primary_subjects_by_change or {}).get(change_id, ""),
        # `None` when the target has no entities, which the validator requires; a guess here
        # would be rejected, and a guess that happened to match would be worse.
        "primary_entity_id": entity_ids[0] if entity_ids else None,
        "concern_family": finding.get("concern_family") or "other",
        # The free-text label beside the closed family. An arm's is its spec's own phrasing;
        # a whole-PR reviewer has no spec, so the family is the most it can honestly say and
        # inventing a richer label here would be this module putting words in its mouth.
        "concern_label": finding.get("concern_family") or "other",
        "issue_kind": finding.get("issue_kind"),
        "severity": finding.get("severity") or "advisory",
        "claim": finding.get("claim") or "",
        "requested_change": finding.get("suggested_fix") or finding.get("claim") or "",
        "suggested_fix": finding.get("suggested_fix"),
    }


def _solo_coverage_gaps(results, data) -> List[Dict[str, Any]]:
    """Every episode whose whole-PR review did not reach a submission.

    Without this the run closes `complete` with an empty `findings.jsonl` -- `solo` has no
    mandatory jobs, so nothing else would notice -- and the judge would score it as a reviewer
    that found nothing. The likeliest cause is the cost cap: the relay refuses the next request
    once billed spend reaches it, and an external CLI handed that error usually dies without
    submitting. A budget result reported as a capability result is the same shape as the
    `exit 127` incident that voided a run's worth of numbers.
    """

    submitted = set()
    for result in results.task_results:
        raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        if raw.get("success") and raw.get("episode_id"):
            submitted.add(raw["episode_id"])
    return [
        {
            "episode_id": item["episode_id"],
            "pr_number": item["pr_number"],
            "arm_id": SOLO_ARM_ID,
            "reason": "the whole-PR review did not reach a submission",
        }
        for item in data
        if item["episode_id"] not in submitted
    ]


def _comprehension_from_results(results, mode: str) -> List[Dict[str, Any]]:
    """What each lead understood before it delegated.

    Recorded so the run can be read as a chain — what was understood, what was asked, what
    was routed, what was found — rather than as a set of findings with no account of how
    they came to be looked for.
    """

    if mode != "lead":
        return []
    rows: List[Dict[str, Any]] = []
    for result in results.task_results:
        raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        payload = raw.get("comprehension") or {}
        if payload:
            rows.append({"pr_number": raw.get("pr_number"), **payload})
    return rows


def _coverage_gaps_from_results(results, mode: str) -> List[Dict[str, Any]]:
    """Mandatory jobs that did not succeed, across every lead in the run.

    A run with any of these is `partial`. It is not a failure — the lead may have submitted
    perfectly legally — but it did not look at everything it promised to, so a recall number
    from it is measured against a denominator it never covered. On PR 33117 a paused floor job
    was booked as a plain failure, counted as coverage anyway, and the run was scored complete.
    """

    if mode != "lead":
        return []
    rows: List[Dict[str, Any]] = []
    for result in results.task_results:
        raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        rows.extend(raw.get("coverage_gaps") or [])
    return rows


def _assessments_from_results(results, mode: str) -> List[Dict[str, Any]]:
    """The lead's read on the claims that came back.

    Emitted since the first lead run and read by nothing: the field was sealed into the
    result, surfaced in the trajectory view, and applied nowhere. In the model-free modes no
    lead exists, so there is nothing to apply and the list is empty by construction.
    """

    if mode != "lead":
        return []
    rows: List[Dict[str, Any]] = []
    for result in results.task_results:
        raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        rows.extend(raw.get("candidate_assessments") or [])
    return rows


def _delegations_from_results(results, mode: str, agenda,
                              floor_records: Optional[List[Dict[str, Any]]] = None,
                              ) -> List[Dict[str, Any]]:
    """Delegation records: the lead's own plus the floor's, or synthesized for the
    model-free modes, where every job is decided by rule."""

    floor_records = list(floor_records or [])

    if mode == "lead":
        records = []
        for result in results.task_results:
            raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
            records.extend(raw.get("delegations") or [])
        return records + floor_records
    if mode == "solo":
        # Every proposal is `pruned`, and by nothing -- no lead declined it and no rule
        # excluded it; the condition simply schedules no work-unit job. The records still have
        # to exist because `reconcile` refuses a run that leaves a sealed proposal with no
        # disposition, and because the alternative -- an empty ledger -- would read as a run
        # that lost its accounting rather than one that had none to keep.
        #
        # The solo tasks' own outcomes deliberately do NOT go here: `reconcile` raises for any
        # invocation the sealed agenda did not enumerate, and a whole-PR review is not one of
        # them. A solo task that failed is a coverage gap, not a delegation.
        return [
            {
                "schema_version": "v5-delegation1",
                "invocation_id": item.invocation_id,
                "proposal_id": item.proposal_id,
                "arm_id": item.arm_id,
                "work_unit_id": item.work_unit_id,
                "pr_number": item.pr_number,
                "disposition": "pruned",
                "reason": "solo mode schedules no work-unit job",
                "budget_tier": None,
                "context_calls": [],
            }
            for item in agenda.proposals
        ]
    ran = {item.invocation_id for item in initial_jobs(agenda)}
    return [
        {
            "schema_version": "v5-delegation1",
            "invocation_id": item.invocation_id,
            "proposal_id": item.proposal_id,
            "arm_id": item.arm_id,
            "work_unit_id": item.work_unit_id,
            "pr_number": item.pr_number,
            "disposition": (
                "mandatory" if item.mandatory
                else "proposed" if item.invocation_id in ran else "pruned"
            ),
            "reason": ("" if item.invocation_id in ran else f"not selected in {mode} mode"),
            "budget_tier": "standard" if item.invocation_id in ran else None,
            "context_calls": [],
        }
        for item in agenda.proposals
    ]


class BudgetTooSmall(RuntimeError):
    """The run cannot pay for the work it is required to do."""


class CoverageGapAtPlanTime(RuntimeError):
    """The run would leave work units unreviewed, and the numbers would not mean what they say."""


def assert_coverage_is_reachable(dataset, report, logger) -> None:
    """A specialist-only run must not leave a work unit with nothing eligible on it.

    This was a comment on `generalist_floor`: "Only turn it off on a set where the specialists
    already cover every work unit -- `agenda_report` reports `units_without_specialist`, and a
    run that leaves units unreviewed measures coverage loss, not arm quality."

    A comment cannot check itself, and this one has already been read wrong once. On the rep2
    heldout run `units_without_specialist` came back empty and was used to green-light a
    specialist-only run -- but it was empty because a mandatory job that ran and *failed* was
    counted as covered, so a budget cutoff read as full coverage. The reconciliation bug is
    fixed; the unchecked precondition was not, and it is the cheaper of the two to enforce.

    Refused rather than warned. The output of such a run is not wrong, it is unreadable: a
    recall drop measures the units nobody looked at, and nothing downstream distinguishes that
    from arms that looked and missed.
    """

    if dataset.generalist_floor:
        return
    uncovered = report.get("units_without_specialist") or []
    if not uncovered:
        logger.info("specialist-only: all work units draw at least one specialist")
        return
    raise CoverageGapAtPlanTime(
        f"generalist_floor is off and {len(uncovered)} work unit(s) have no eligible "
        f"specialist: {sorted(uncovered)[:8]}. Without the floor those units are not reviewed "
        "at all, so the run measures coverage loss rather than arm quality. Either turn the "
        "floor back on, or restrict `pr_numbers` to a set the specialists cover."
    )


def assert_the_judge_model_is_pinned(dataset, logger) -> None:
    """The evidence gate must be a choice, not a default nobody made.

    `skip_evidence_chain` restores the closed gate every run before this one had, and its own
    docstring says why the default is off: a closed gate made "no collector ran"
    indistinguishable from "the claim failed", and eight runs reported publication rates under
    that regime as if they were strictness results.

    Nothing stopped a config from turning it back on silently, so it is said out loud here --
    at plan time, where it can still be reconsidered, rather than in the finalization report
    after the money is spent.
    """

    if dataset.skip_evidence_chain:
        logger.warning(
            "skip_evidence_chain is ON: the generalist gate is CLOSED, so no generalist claim "
            "can publish and `generalist_evidence_gate` will read `closed`. Publication rates "
            "from this run are not strictness results.")


def _report_budget(dataset, report, pr_count: int, logger, *, enforce: bool = False) -> None:
    """Say what this run is committed to before it starts, and refuse it if it cannot fit.

    The message this replaces compared the coverage floor against
    `per_pr_cost_cap * pr_count` and, when it did not fit, advised raising
    `per_pr_cost_cap` -- a cap that does not bind the floor at all. It bounds *discretionary*
    work only; the floor is deliberately exempt, because charging coverage to the routing
    allowance once left PR 33149 with a $10.05 floor against a $1.50 cap and therefore zero
    specialists.

    So the two are reported separately, against the caps that actually bind them, and the
    floor is checked against the run total.
    """

    run_cap = dataset.run_total_cost_cap

    if dataset.routing_mode == "solo":
        # There is no floor and no discretionary allowance: `solo` schedules no work-unit job
        # at all, so the agenda's `mandatory_floor_cost` describes work this run will never do.
        # Reporting it would be fiction, and checking against it would refuse a run for money
        # it cannot spend -- the agenda's floor for the smoke set is $2.35, which against an
        # $8.00 total cap turns a $6.00 run into "DOES NOT FIT".
        committed = dataset.solo_cost_cap * pr_count
        logger.info(
            "budget: no coverage floor (solo schedules no work-unit job) + up to $%.2f "
            "(%d PR x $%.2f billed)", committed, pr_count, dataset.solo_cost_cap)
        if not run_cap:
            logger.warning("no run_total_cost_cap set")
            return
        logger.info("run_total_cost_cap $%.2f vs worst case $%.2f — %s", run_cap, committed,
                    "fits" if committed <= run_cap else "DOES NOT FIT")
        if committed > run_cap:
            message = (
                f"{pr_count} PR x solo_cost_cap ${dataset.solo_cost_cap:.2f} = "
                f"${committed:.2f}, above the run_total_cost_cap of ${run_cap:.2f}.")
            if enforce:
                raise BudgetTooSmall(message)
            logger.warning("%s", message)
        return

    floor = float(report.get("mandatory_floor_cost") or 0.0)
    discretionary_cap = dataset.per_pr_cost_cap * pr_count

    logger.info(
        "budget: mandatory floor $%.2f (uncapped per PR by design) + discretionary up to "
        "$%.2f (%d PR x $%.2f)",
        floor, discretionary_cap, pr_count, dataset.per_pr_cost_cap)

    if not run_cap:
        logger.warning(
            "no run_total_cost_cap set: the mandatory floor is bounded by nothing. It scales "
            "with work units times required arms, so a larger PR set authorises more of it "
            "with no cap refusing.")
        return

    committed = floor + discretionary_cap
    logger.info("run_total_cost_cap $%.2f vs worst case $%.2f (floor + discretionary) — %s",
                run_cap, committed, "fits" if committed <= run_cap else "DOES NOT FIT")

    if floor > run_cap:
        message = (
            f"the mandatory coverage floor alone is ${floor:.2f}, above the "
            f"run_total_cost_cap of ${run_cap:.2f}. The floor is not optional and not "
            f"capped per PR, so this run cannot be paid for as configured. Raise "
            f"run_total_cost_cap, narrow pr_numbers, or turn off generalist_floor."
        )
        if enforce:
            raise BudgetTooSmall(message)
        logger.warning("%s", message)


def coordination_config(dataset) -> CoordinationConfig:
    """The run's coordination and synthesis policy, defaulted to what the code does.

    `max_jobs` mirrors `max_delegations` rather than duplicating it: the bound is enforced in
    `lead.py` and this records it, so the plan and the enforcement cannot disagree about what
    the run was allowed to do.
    """

    config = CoordinationConfig()
    config.coordination.max_jobs = dataset.max_delegations
    assert_implemented(config)
    return config


#: Plan fields a resume may change. Everything else is semantic: change it and the run is a
#: different experiment, whatever the directory is called.
#:
#: The line is drawn at "does this change what the run *measures*". A budget does not -- a
#: resumed run with a raised cap answers the same question, having been allowed to finish
#: asking it. A prompt hash, the model, the agenda, the routing mode, the coordination policy
#: and the evaluation settings all do.
RESUMABLE_PLAN_FIELDS = frozenset({
    "lead_cost_cap", "standard_budget_cap", "per_pr_cost_cap",
    "scaffold_config_sha256",  # carries retries and timeouts, which a resume may raise
    "git_commit", "git_tree_state",  # provenance of *this* attempt, not of the experiment
    "source_sha256",             # derived from the above
})


class PlanChangedSemantically(RuntimeError):
    """A resume would answer a different question than the run it is resuming."""


def seal_or_revise_plan(out: Path, plan: V5RunPlan, logger) -> Path:
    """Write the plan, or record a revision of it when only operational fields moved.

    `write_once` refuses a differing artifact, which is the right default and too blunt for a
    resume: a run paused on budget can only be finished by raising the budget, and that made
    the plan differ, and the resume was then refused at the first write. The two ways out were
    both bad -- a new run name, which forfeits every completed attempt in the orchestrator
    cache, or deleting the plan, which forfeits the pre-registration.

    So the plan stays immutable and revisions accumulate beside it: `run_plan.json` is what
    was sealed first, `run_plan_revision_2.json` is what the second attempt ran under. A
    semantic change is still refused -- with the specific fields named, since "the plan
    differs" was not enough to act on.
    """

    sealed = out / "run_plan.json"
    payload = pretty_json_bytes(plan.model_dump(mode="json"))
    if not sealed.exists():
        write_once(sealed, payload)
        return sealed
    if sealed.read_bytes() == payload:
        return sealed

    import json as _json

    before = _json.loads(sealed.read_text(encoding="utf-8"))
    after = plan.model_dump(mode="json")
    changed = {key for key in set(before) | set(after) if before.get(key) != after.get(key)}
    semantic = sorted(changed - RESUMABLE_PLAN_FIELDS)
    if semantic:
        raise PlanChangedSemantically(
            f"the sealed plan for {plan.run_name!r} differs in {semantic}, which changes what "
            "the run measures rather than what it may spend. Resuming under the same name "
            "would attribute two experiments to one pre-registration. Use a new run_name — "
            "the orchestrator cache is keyed on it, so this is also what makes the changed "
            "code actually execute."
        )

    revision = 2
    while (out / f"run_plan_revision_{revision}.json").exists():
        revision += 1
    path = out / f"run_plan_revision_{revision}.json"
    write_once(path, payload)
    logger.warning(
        "resuming %s under revision %d: %s changed. The original plan stands; %s records "
        "what this attempt ran under.",
        plan.run_name, revision, sorted(changed), path.name)
    return path


def _build_plan(dataset: V5DatasetConfig, scaffold, agenda) -> V5RunPlan:
    """Seal the pre-registration. Constructed identically in dry and real runs.

    The dry run builds it and throws it away rather than skipping it: sealing is the only
    step a real run performs that a dry run otherwise would not, so skipping it made the dry
    run unable to catch exactly the errors it exists to catch cheaply.
    """

    model_name = scaffold.llm_config.model_name
    if not model_name:
        raise ValueError(
            "llm_config.model_name is not set. The sealed plan records which model produced "
            "a run, and a run that cannot name its model cannot be compared with another — "
            "so this is refused rather than stamped as null."
        )
    commit, tree_state = git_state()
    plan = V5RunPlan(
        run_id=f"v5run:{dataset.run_name}",
        run_name=dataset.run_name,
        routing_mode=dataset.routing_mode,
        agenda_sha256=sha256_bytes(canonical_json_bytes(agenda.model_dump(mode="json"))),
        release=str(dataset.release),
        prompt_sha256_by_invocation={
            item.invocation_id: item.prompt_sha256 for item in agenda.proposals
        },
        arm_sha256_by_id={arm.arm_id: arm.source_sha256 for arm in agenda.arms},
        context_index_sha256=_context_index_identity(),
        model_name=model_name,
        scaffold_config_sha256=sha256_bytes(
            canonical_json_bytes(scaffold.model_dump(mode="json"))),
        lead_cost_cap=dataset.lead_cost_cap,
        standard_budget_cap=dataset.standard_budget_cap,
        per_pr_cost_cap=dataset.per_pr_cost_cap,
        coordination=coordination_config(dataset).report(),
        evaluation_settings={
            "execution_release": (str(dataset.execution_release)
                                  if dataset.execution_release else None),
            "skip_evidence_chain": dataset.skip_evidence_chain,
            "pr_finding_limit": dataset.pr_finding_limit,
            "generalist_floor": dataset.generalist_floor,
            "apply_lead_synthesis": dataset.apply_lead_synthesis,
            "use_exposure_index": dataset.use_exposure_index,
        },
        git_commit=commit, git_tree_state=tree_state,
        source_sha256="",
    )
    return plan.model_copy(update={"source_sha256": sha256_bytes(canonical_json_bytes(
        plan.model_dump(mode="json", exclude={"source_sha256"})))})


#: Artifacts whose presence means a previous execution already produced results here.
#: The sealed plan and agenda are deliberately not in this list: they are reproducible from
#: the same inputs, so re-writing them byte-identically is a `write_once` no-op.
_TERMINAL_OUTPUTS = (
    "run_manifest.json", "delegations.jsonl", "arm_responses.jsonl", "findings.jsonl",
    "issues.jsonl", "finalization_report.json",
)


def _scratch_dirs(run_name: str, scaffold=None) -> List[Path]:
    """Where the orchestrator would keep this run's resumable state.

    Read from the scaffold's `runs_base_dir` rather than hardcoded. The literal `.ape/runs`
    here was wrong for any config that sets `runs_base_dir` and for any launch from a
    directory other than the repo root: the guard then looked in a place nothing writes,
    found nothing, and passed — restoring the exact silent-resume hazard it exists to prevent.
    """

    if scaffold is not None:
        base = Path(getattr(scaffold, "runs_base_dir", None) or Path(".ape/runs"))
    else:
        from ape.scaffolds.config import BaseScaffoldConfig

        # The field's default, not an instance. `BaseScaffoldConfig` requires `scaffold_type`,
        # so constructing one bare raised `ValidationError` -- which made this whole branch
        # dead, and with it `--redo`, whose only job is to reach it. Nothing caught it because
        # the guard path always passes a scaffold; `redo_run` was the one caller that did not.
        base = Path(BaseScaffoldConfig.model_fields["runs_base_dir"].default)
    return [base / run_name, base / f"{run_name}_floor"]


def assert_run_is_named(dataset: V5DatasetConfig) -> None:
    """A run must say which run it is, before anything is rendered or spent."""

    if dataset.run_name and dataset.run_name != "UNNAMED":
        return
    raise ValueError(
        "this run has no name. Pass --run-name, e.g.\n"
        "  python -m src.mathlib_review.review.cli plan --config <config> "
        "--run-name pr_review_v5_specialist4_rep2\n"
        "The name is the results directory, the orchestrator's cache key, and the identity "
        "the judge scores this run under. It is supplied per invocation because a config "
        "describes a PR set and a policy, and `rep2` is part of neither."
    )


def guard_run_name(dataset: V5DatasetConfig, logger, scaffold=None,
                   *, fatal: bool = True) -> None:
    """Refuse to reuse a run name that already produced results, BEFORE spending anything.

    Two separate things go wrong when a name is reused after a code change, and neither
    announces itself:

    * `run_name` is the orchestrator's **resume key**. Every attempt that already succeeded
      is returned from cache, so the code you just changed never executes — the run looks
      like it re-ran and reports the old behaviour.
    * The derived outputs *do* get rebuilt, and `write_once` then refuses them for differing
      — but only at the very end, after the floor has been paid for again.

    So the check happens here, before the first orchestrator starts. This is the same
    discipline v4 records in its own configs ("bumped to FRESH names — prompt+tool changed,
    must not resume"); making it an error rather than a convention is the difference between
    remembering it and being told.
    """

    directory = run_dir(dataset.run_name)
    existing = [name for name in _TERMINAL_OUTPUTS if (directory / name).is_file()]
    scratch = [item for item in _scratch_dirs(dataset.run_name, scaffold) if item.is_dir()]
    if not existing and not scratch:
        return
    if not fatal:
        # A dry run must be able to say the name is spent. It used to run *after* the
        # dry-run early return, so `--dry-run` -- the one command whose whole job is to
        # tell you what the real run would do -- could not tell you it would refuse.
        logger.warning(
            "run_name %r is already spent%s%s; the real run will refuse it",
            dataset.run_name,
            f" (outputs: {', '.join(existing)})" if existing else "",
            f" (orchestrator state: {', '.join(str(i) for i in scratch)})" if scratch else "")
        return
    raise RuntimeError(
        f"run_name {dataset.run_name!r} has already been executed"
        + (f" (outputs: {', '.join(existing)})" if existing else "")
        + (f" (orchestrator state: {', '.join(str(item) for item in scratch)})" if scratch else "")
        + ".\n\n"
        "`run_name` is the orchestrator's resume key, so re-running it would return every "
        "previously successful attempt from cache — any code you changed since would not "
        "execute, and the run would report the old behaviour as if it were new.\n\n"
        "Either:\n"
        f"  - bump the name (dataset.run_name={dataset.run_name}_rep2), keeping the old run, or\n"
        "  - pass --redo to discard this run's results and orchestrator state and execute "
        "it again from scratch."
    )


def redo_run(dataset: V5DatasetConfig, logger, scaffold=None) -> None:
    """Discard a run's results AND its orchestrator state, so a redo really re-executes.

    Clearing only the results directory would leave the resume key intact, which is the
    failure this exists to prevent: the outputs would be rebuilt from cached attempts and
    look like a fresh run.

    `scaffold` is passed so the scratch directories are read from the config that wrote them.
    Without it this falls back to the packaged default, which is right for every config that
    does not set `runs_base_dir` and silently wrong -- removing nothing, and leaving the
    resume key intact -- for any that does.
    """

    import shutil

    directory = run_dir(dataset.run_name)
    for target in [directory, *_scratch_dirs(dataset.run_name, scaffold)]:
        if target.is_dir():
            shutil.rmtree(target)
            logger.info("redo: removed %s", target)


def _context_calls_by_invocation(trace_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Group the append-only context trace. Shared by the floor and the lead."""

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    if not trace_path.is_file():
        return grouped
    for line in trace_path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        grouped.setdefault(row.get("invocation_id", "?"), []).append(row)
    return grouped


async def run(dataset: V5DatasetConfig, scaffold, task_overrides, logger):
    assert_ready(scaffold, logger, enforce=not dataset.dry_run)
    if dataset.routing_mode not in ROUTING_MODES:
        raise ValueError(
            f"unknown routing_mode {dataset.routing_mode!r}; expected one of {ROUTING_MODES}")

    release = load_release(dataset)
    units, episodes = select_units_and_episodes(dataset, release)
    selected_prs = sorted({unit.pr_number for unit in units})

    agenda, pool = build_agenda(
        run_name=dataset.run_name, routing_mode=dataset.routing_mode,
        release=dataset.release, modification_inventory=dataset.modification_inventory,
        units=units, episodes=episodes, graphs=release["graphs"],
        release_prompts=release["release_prompts"], modifications=release["modifications"],
        pr_numbers=selected_prs,
        use_exposure_index=dataset.use_exposure_index,
        generalist_floor=dataset.generalist_floor,
    )
    assert_run_is_named(dataset)
    report = agenda_report(agenda)

    if dataset.dry_run:
        logger.info("DRY RUN — nothing is written and no model is called")
        # Warn, don't raise: a dry run must be able to say the real run would refuse this
        # name. The check used to sit *after* this block, so the one command whose job is to
        # tell you what the real run would do could not tell you it would not start.
        guard_run_name(dataset, logger, scaffold, fatal=False)
        logger.info("%s", json.dumps(report, indent=2))
        _report_budget(dataset, report, len(selected_prs), logger)
        assert_coverage_is_reachable(dataset, report, logger)
        assert_the_judge_model_is_pinned(dataset, logger)
        # Resolving cutoffs during a dry run is the cheapest place to discover that a gated
        # read would have been impossible.
        cutoffs_by_episode(episodes)
        logger.info("retrieval cutoffs resolve for all %d episode(s)", len(episodes))
        # Same for the verification environment: a dry run must say whether the real run
        # would verify against the PR's own build products or the base commit's.
        missing = await assert_reviewed_workspaces_prebuilt(
            episodes, required=dataset.require_reviewed_workspaces, logger=logger)
        logger.info("reviewed workspaces: %d of %d episode(s) prebuilt%s",
                    len(episodes) - len(missing), len(episodes),
                    "" if not missing else " — the rest would verify against base .oleans")
        plan = _build_plan(dataset, scaffold, agenda)
        logger.info("run plan seals (agenda %s, %d prompt hashes) — not written",
                    plan.agenda_sha256[:12], len(plan.prompt_sha256_by_invocation))
        return None

    _report_budget(dataset, report, len(selected_prs), logger, enforce=True)
    assert_coverage_is_reachable(dataset, report, logger)
    assert_the_judge_model_is_pinned(dataset, logger)
    guard_run_name(dataset, logger, scaffold)
    out = run_dir(dataset.run_name)
    out.mkdir(parents=True, exist_ok=True)
    cutoff_by_episode = cutoffs_by_episode(episodes)
    pool_path = out / "arm_pool.jsonl"
    trace_path = out / "context_trace.jsonl"
    _write_pool(pool_path, pool, cutoff_by_episode, trace_path)
    write_once(out / "agenda.json", pretty_json_bytes(agenda.model_dump(mode="json")))
    write_once(out / "agenda_report.json", pretty_json_bytes(report))

    plan = _build_plan(dataset, scaffold, agenda)
    seal_or_revise_plan(out, plan, logger)

    if dataset.routing_mode == "lead":
        # Rank each PR's work before the lead reads it. Relations are computed once for the
        # whole release: `pr_relations` already derives sibling families, shared name tokens
        # and repeated implementation shapes, and v5 had never used any of it.
        from src.mathlib_review.release.pr_relations import build_relations

        relations, _relation_evidence = build_relations(release["graphs"])
        census_by_pr: Dict[int, List[Dict[str, Any]]] = {}
        for pr_number in selected_prs:
            rows = build_census(
                [item for item in agenda.proposals if item.pr_number == pr_number],
                units, release["graphs"], episodes, relations,
            )
            census_by_pr[pr_number] = [row.render() for row in rows]
        write_once(out / "census.json", pretty_json_bytes({
            str(pr): rows for pr, rows in sorted(census_by_pr.items())}))
        logger.info("census: %d work unit(s) ranked across %d PR(s)",
                    sum(len(v) for v in census_by_pr.values()), len(census_by_pr))

        # No separate floor pass. The coverage floor is injected as the lead's first wave, so
        # there is one agent per PR delegating all of its own work — the shape the generation
        # is named for. The guarantee survives the move: `delegate` prepends the mandatory
        # jobs whatever the lead asked for, and `submit_routing` refuses to close until they
        # have run, so the floor is still not the lead's to skip.
        data = _lead_task_data(agenda, episodes, dataset, pool_path, trace_path,
                               cutoff_by_episode, census_by_pr,
                               journal_dir=out / "lead_journals")
        scaffold.task_config_overrides = {
            **(task_overrides or {}),
            "standard_budget_cap": dataset.standard_budget_cap,
            "max_delegations": dataset.max_delegations,
            "per_pr_cost_cap": dataset.per_pr_cost_cap,
        }
        scaffold.execution.sample_max_cost = dataset.lead_cost_cap
    elif dataset.routing_mode == "solo":
        # No census, no arm pool, no journal: there is nothing to route. The agenda was still
        # built and sealed above, which is what makes this run's `agenda_report.json` scope
        # identically to the `lead` run on the same config.
        data = _solo_task_data(agenda, episodes, dataset, cutoff_by_episode, trace_path)
        scaffold.execution.sample_max_cost = dataset.solo_cost_cap
    else:
        data = _direct_arm_task_data(agenda, pool, cutoff_by_episode, trace_path)
        scaffold.execution.sample_max_cost = dataset.standard_budget_cap

    await assert_workspaces_prebuilt(
        data, required=dataset.require_prebuilt_workspaces)
    await assert_reviewed_workspaces_prebuilt(
        episodes, required=dataset.require_reviewed_workspaces, logger=logger)

    logger.info("routing_mode=%s tasks=%d prs=%s", dataset.routing_mode, len(data), selected_prs)
    tasks = [create_task_from_data(item, scaffold,
                                   task_config_overrides=scaffold.task_config_overrides)
             for item in data]
    orchestrator = TaskOrchestrator(config=scaffold, orchestrator_id=dataset.run_name,
                                    logger=logger)
    results = await orchestrator.run(tasks)

    if dataset.routing_mode == "solo":
        responses, anchor_rows = _solo_responses(
            results, release["graphs"], units, logger)
        write_once(out / "anchoring.jsonl", jsonl_bytes(anchor_rows))
        report = anchoring_report(anchor_rows)
        write_once(out / "anchoring_report.json", pretty_json_bytes(report))
        # Loud, because a high loss rate makes every recall number downstream a measurement of
        # the anchoring pass rather than of the reviewer. ~5% is the rate measured on arm
        # output, which is the only prior available.
        log = logger.warning if report["unanchored_rate"] > 0.15 else logger.info
        log("anchoring: %d/%d findings anchored (%.1f%% lost) across %d work unit(s); %s",
            report["anchored"], report["findings_in"],
            100 * report["unanchored_rate"], report["work_units_reached"],
            report["by_failure"] or "no failures")
    else:
        responses = _responses_from_results(results, dataset.routing_mode)
    delegations = _delegations_from_results(results, dataset.routing_mode, agenda)
    assessments = _assessments_from_results(results, dataset.routing_mode)
    coverage_gaps = (
        _solo_coverage_gaps(results, data) if dataset.routing_mode == "solo"
        else _coverage_gaps_from_results(results, dataset.routing_mode))
    comprehension = _comprehension_from_results(results, dataset.routing_mode)
    write_once(out / "arm_responses.jsonl", jsonl_bytes(responses))
    write_once(out / "delegations.jsonl", jsonl_bytes(delegations))
    write_once(out / "candidate_assessments.jsonl", jsonl_bytes(assessments))
    write_once(out / "comprehension.jsonl", jsonl_bytes(comprehension))

    # Evidence runs in the workspace that actually reviewed the episode, so the collectors
    # see the code as the PR leaves it. Resolved here because only the runner knows which
    # attempt succeeded; `finalize` is handed a callable, never a workspace.
    workspace_by_episode = await reviewed_workspaces(orchestrator.tasks_dir, data, results)
    write_once(out / "reviewed_workspaces.json",
               pretty_json_bytes(dict(sorted(workspace_by_episode.items()))))
    if len(workspace_by_episode) < len(selected_prs):
        logger.warning(
            "only %d of %d episode(s) resolved a reviewed workspace; the rest fall back to "
            "the base snapshot, where a policy or compile check reads the pre-PR file",
            len(workspace_by_episode), len(selected_prs))

    summary = finalize(
        out, units=units, responses=responses, routing_mode=dataset.routing_mode,
        execution_release=dataset.execution_release,
        exclude_methods=dataset.exclude_methods, pr_numbers=selected_prs,
        candidate_assessments=assessments,
        apply_lead_synthesis=dataset.apply_lead_synthesis,
        collect_supported=(
            None if dataset.skip_evidence_chain else
            lambda candidates: collect_supported(
                candidates, graphs=release["graphs"], out=out,
                workspace_by_episode=workspace_by_episode, logger=logger)
        ),
        pr_finding_limit=dataset.pr_finding_limit, logger=logger,
    )

    manifest = reconcile(
        agenda=agenda, delegations=delegations, responses=responses,
        plan=plan, results=results, issues_total=summary["issues_total"],
        coverage_gaps=coverage_gaps,
        # Counted off the trace in `solo`, not off the ledger. The manifest's figure is the sum
        # over delegation rows, and a solo run's delegations are all `pruned` with empty call
        # lists -- so it reported 0 while `context_trace.jsonl` held real retrievals. Zero
        # retrieval calls and zero instrumentation are the two things this project has most
        # often confused, and they read identically in a manifest.
        context_calls_total=(
            len(list(jsonl_rows(trace_path))) if dataset.routing_mode == "solo"
            and trace_path.is_file() else None),
    )
    write_once(out / "run_manifest.json", pretty_json_bytes(manifest.model_dump(mode="json")))
    logger.info("run dir: %s", out)
    logger.info("completion_status=%s issues=%d cost=$%.2f",
                manifest.completion_status, manifest.issues_total, manifest.total_cost)
    if manifest.coverage_gaps:
        # Loud, and at the end where it is read. This is the signal that was missing when two
        # runs were scored as though complete: every arm result is still on disk and worth
        # inspecting, but a recall figure from this run is not comparable to a complete one.
        logger.warning(
            "PARTIAL RUN: %d mandatory job(s) did not succeed, so some work units were never "
            "reviewed. Recall from this run is measured against coverage it did not have. "
            "Gaps: %s",
            len(manifest.coverage_gaps),
            ", ".join(sorted(g.get("invocation_id", "?") for g in manifest.coverage_gaps)[:8]))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true",
                        help="Render and cost the agenda; write nothing, call no model.")
    parser.add_argument("--cost-model", choices=COST_MODELS, default=None,
                        help="How to read provider token accounting when pricing calls. "
                             "Default is the LLMConfig default (prompt_inclusive); pass "
                             "prompt_exclusive to reproduce pre-2026-08 figures.")
    parser.add_argument("--redo", action="store_true",
                        help="Discard this run_name's results and orchestrator state, then "
                             "execute it again. Without this, reusing a name is refused.")
    args, rest = parser.parse_known_args()
    dataset, scaffold, task_overrides = load_run(args.config, parse_cli_args(rest))
    if args.dry_run:
        dataset.dry_run = True
    if args.cost_model:
        scaffold.llm_config.cost_model = args.cost_model
    logger = create_logger()
    logger.info("cost model: %s", scaffold.llm_config.cost_model)
    if args.redo and not dataset.dry_run:
        redo_run(dataset, logger)
    result = asyncio.run(run(dataset, scaffold, task_overrides, logger))
    if result:
        print(result)


if __name__ == "__main__":
    main()
