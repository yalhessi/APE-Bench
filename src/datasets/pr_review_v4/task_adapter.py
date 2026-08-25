"""Gold-free v4 work-unit to APE task adapter."""

from ape.tasks.lean_tasks import LeanPRReviewV4CandidateData
from ape.tasks.models import WorkspaceInfo

from .schema import (
    OpportunityEvidenceArtifact,
    OracleOpportunity,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewOpportunity,
    ReviewWorkUnit,
)


DEFAULT_MATHLIB_URL = "https://github.com/leanprover-community/mathlib4.git"


def build_candidate_task_data(unit: ReviewWorkUnit, episode: ReviewEpisodeInput,
                              prompt: RenderedPrompt) -> LeanPRReviewV4CandidateData:
    if unit.work_unit_id != prompt.work_unit_id:
        raise ValueError("prompt/work-unit mismatch")
    # A holistic production prompt must show the whole unit; omitting a target silently
    # shrinks what the model could possibly find. A *focused* prompt omits by design — its
    # scope is the sites its spec's rule selected — so the invariant is scoped to prompts
    # that claim to cover the unit.
    if prompt.omitted_change_ids and not prompt.spec_id:
        raise ValueError("incomplete production prompt")
    return LeanPRReviewV4CandidateData(
        task_id=f"pr4_{unit.work_unit_id.replace(':', '_')}",
        pr_number=episode.pr_number, pr_title=episode.title.text or "",
        pr_description=episode.description.text or "", diff=episode.diff,
        changed_files=episode.changed_files, snapshot_head_sha=episode.reviewed_head_sha,
        snapshot_base_sha=episode.base_sha, work_unit_id=unit.work_unit_id,
        episode_id=unit.episode_id,
        change_ids=unit.change_ids, entity_ids_by_change=unit.entity_ids_by_change,
        primary_subjects_by_change=unit.primary_subjects_by_change,
        paths_by_change=unit.paths_by_change,
        rendered_system_prompt=prompt.system_prompt,
        rendered_user_prompt=prompt.user_prompt, rendered_prompt_sha256=prompt.prompt_sha256,
        submission_verification_policy=prompt.submission_verification_policy,
        target_workspace=WorkspaceInfo(name="target", commit_hash=episode.base_sha,
                                       repo_url=DEFAULT_MATHLIB_URL, default_target="Mathlib"),
    )


def build_focused_task_data(unit: ReviewWorkUnit, episode: ReviewEpisodeInput,
                            prompt: RenderedPrompt):
    """One focused invocation's task data.

    The prompt carries the identity, not the caller: `render_focused_invocation` is what
    knows which spec was scheduled where, and taking `invocation_id`/`spec_id` from anywhere
    else would let the prompt an agent reads disagree with the label its candidates are
    attributed under.
    """

    from ape.tasks.lean_tasks import LeanPRReviewV4FocusedData

    if not prompt.invocation_id or not prompt.spec_id:
        raise ValueError("a focused prompt must carry invocation_id and spec_id")
    base = build_candidate_task_data(unit, episode, prompt)
    payload = base.model_dump(exclude={"task_type"})
    # Unit-keyed task ids collide across the four specs scheduled on one work unit, and a
    # collision here means four runs writing over each other's workspace.
    payload["task_id"] = f"pr4f_{prompt.invocation_id.replace(':', '_').replace('#', '__')}"
    # Narrowed to the sites this spec was scheduled on, not the whole work unit. The prompt
    # shows only those sites, and letting the contract accept the rest would allow a claim
    # about a target the agent was never shown — which would also make the enumeration the
    # arm's gold-free scheduling rests on inexact.
    payload["change_ids"] = list(prompt.included_change_ids)
    return LeanPRReviewV4FocusedData(
        **payload,
        invocation_id=prompt.invocation_id,
        spec_id=prompt.spec_id,
    )


def build_file_task_data(unit: ReviewWorkUnit, episode: ReviewEpisodeInput,
                         prompt: RenderedPrompt, reviewed_path: str, graph):
    """One file-scoped invocation's task data.

    The work unit is nominal: a file's targets may span several units, and the prompt's
    `included_change_ids` is the real scope. Every per-target map has to be widened to match,
    not just `change_ids` — the submission contract checks `primary_subject` and
    `primary_entity_id` against these maps, so a unit-sized map silently rejects any claim
    about a target outside the nominal unit, which is precisely the cross-unit claim this arm
    exists to make. The maps are rebuilt from the change graph, which is where they come from
    in the first place.
    """

    from ape.tasks.lean_tasks import LeanPRReviewV4FileData

    if not prompt.invocation_id:
        raise ValueError("a file-scoped prompt must carry invocation_id")
    base = build_candidate_task_data(unit, episode, prompt)
    payload = base.model_dump(exclude={"task_type"})
    scope = list(prompt.included_change_ids)
    targets = {item.change_id: item for item in graph.targets}
    missing = [cid for cid in scope if cid not in targets]
    if missing:
        raise ValueError(f"file prompt names targets absent from its graph: {missing[:3]}")
    payload["task_id"] = f"pr4file_{prompt.invocation_id.replace(':', '_')}"
    payload["change_ids"] = scope
    payload["primary_subjects_by_change"] = {
        cid: (targets[cid].declaration_name or targets[cid].path) for cid in scope
    }
    payload["entity_ids_by_change"] = {
        cid: list(targets[cid].reviewed_entity_ids + targets[cid].base_entity_ids)
        for cid in scope
    }
    payload["paths_by_change"] = {cid: targets[cid].path for cid in scope}
    return LeanPRReviewV4FileData(
        **payload, invocation_id=prompt.invocation_id, reviewed_path=reviewed_path,
    )


def build_opportunity_task_data(
    unit: ReviewWorkUnit,
    episode: ReviewEpisodeInput,
    prompt: RenderedPrompt,
    opportunities: list[OracleOpportunity],
):
    from ape.tasks.lean_tasks.formal_math.pr_review_v4.opportunities import (
        LeanPRReviewV4OpportunityData,
    )

    if unit.work_unit_id != prompt.work_unit_id or prompt.omitted_change_ids:
        raise ValueError("prompt/work-unit mismatch or incomplete opportunity prompt")
    if not opportunities or any(item.work_unit_id != unit.work_unit_id for item in opportunities):
        raise ValueError("opportunity/work-unit mismatch")
    return LeanPRReviewV4OpportunityData(
        task_id=f"pr4_{unit.work_unit_id.replace(':', '_')}",
        pr_number=episode.pr_number,
        pr_title=episode.title.text or "",
        pr_description=episode.description.text or "",
        diff=episode.diff,
        changed_files=episode.changed_files,
        snapshot_head_sha=episode.reviewed_head_sha,
        snapshot_base_sha=episode.base_sha,
        work_unit_id=unit.work_unit_id,
        episode_id=unit.episode_id,
        change_ids=unit.change_ids,
        entity_ids_by_change=unit.entity_ids_by_change,
        primary_subjects_by_change=unit.primary_subjects_by_change,
        opportunity_ids=[item.opportunity_id for item in opportunities],
        evidence_ids_by_opportunity={
            item.opportunity_id: [evidence.evidence_id for evidence in item.evidence]
            for item in opportunities
        },
        change_ids_by_opportunity={
            item.opportunity_id: [item.primary_change_id, *item.related_change_ids]
            for item in opportunities
        },
        verification_required_opportunity_ids=[],
        rendered_system_prompt=prompt.system_prompt,
        rendered_user_prompt=prompt.user_prompt,
        rendered_prompt_sha256=prompt.prompt_sha256,
        target_workspace=WorkspaceInfo(
            name="target",
            commit_hash=episode.base_sha,
            repo_url=DEFAULT_MATHLIB_URL,
            default_target="Mathlib",
        ),
    )


def build_review_opportunity_task_data(
    unit: ReviewWorkUnit,
    episode: ReviewEpisodeInput,
    prompt: RenderedPrompt,
    opportunities: list[ReviewOpportunity],
    evidence: list[OpportunityEvidenceArtifact],
):
    """Adapt automatically discovered production opportunities to the same adjudication task."""

    from ape.tasks.lean_tasks.formal_math.pr_review_v4.opportunities import (
        LeanPRReviewV4OpportunityData,
    )

    if unit.work_unit_id != prompt.work_unit_id or prompt.omitted_change_ids:
        raise ValueError("opportunity prompt/work-unit mismatch")
    if not opportunities or any(item.episode_id != unit.episode_id for item in opportunities):
        raise ValueError("production opportunity/work-unit mismatch")
    evidence_ids = {item.artifact_id for item in evidence}
    if any(not set(item.source_artifact_ids) <= evidence_ids for item in opportunities):
        raise ValueError("production opportunity references unavailable evidence")
    return LeanPRReviewV4OpportunityData(
        task_id=f"pr4_{unit.work_unit_id.replace(':', '_')}",
        pr_number=episode.pr_number,
        pr_title=episode.title.text or "",
        pr_description=episode.description.text or "",
        diff=episode.diff,
        changed_files=episode.changed_files,
        snapshot_head_sha=episode.reviewed_head_sha,
        snapshot_base_sha=episode.base_sha,
        work_unit_id=unit.work_unit_id,
        episode_id=unit.episode_id,
        change_ids=unit.change_ids,
        entity_ids_by_change=unit.entity_ids_by_change,
        primary_subjects_by_change=unit.primary_subjects_by_change,
        opportunity_ids=[item.opportunity_id for item in opportunities],
        evidence_ids_by_opportunity={
            item.opportunity_id: item.source_artifact_ids for item in opportunities
        },
        change_ids_by_opportunity={
            item.opportunity_id: [item.primary_change_id, *item.related_change_ids]
            for item in opportunities
        },
        verification_required_opportunity_ids=[
            item.opportunity_id for item in opportunities
            if item.proposed_transformation is not None
            and item.method_id in {"canonical_api_search.v1", "wrapper_composition.v1"}
        ],
        rendered_system_prompt=prompt.system_prompt,
        rendered_user_prompt=prompt.user_prompt,
        rendered_prompt_sha256=prompt.prompt_sha256,
        target_workspace=WorkspaceInfo(
            name="target",
            commit_hash=episode.base_sha,
            repo_url=DEFAULT_MATHLIB_URL,
            default_target="Mathlib",
        ),
    )
