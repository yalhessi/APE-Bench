"""Read and write v4 run artifacts through framework APIs rather than path layout.

The runner previously reached into the orchestrator's directory tree — globbing
`tasks/<global_index>/samples/*/attempts/*/workspaces/target` and picking the newest by
mtime, and reconstructing task IDs by string-mangling work-unit IDs. Both encode
assumptions the framework never promised, and both break silently rather than loudly
when the layout changes.

Everything here goes through the persistence API instead: `TaskStorage.load_all_samples`
returns `Sample` records whose `successful_attempt.path` is the attempt directory, and
task results carry `work_unit_id` directly.

Downstream phases (7, 8, 9) each parsed run directories independently; they read
candidate responses through `load_candidate_responses` so there is one parser.
"""

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from ape.orchestration.persistence import TaskStorage

CANDIDATE_RESPONSE_SCHEMA = "pr4-candidate-response1"


async def reviewed_workspace_map(
    tasks_dir: Path,
    task_data_by_id: Dict[str, Any],
    results: Iterable[Any],
    task_type: Optional[str] = None,
) -> Dict[str, str]:
    """Map each episode to the workspace root of the attempt that reviewed it.

    Uses the sample records the orchestrator persisted, so the attempt is the one that
    actually succeeded rather than whichever directory was touched most recently.
    """

    workspaces: Dict[str, str] = {}
    for result in results:
        raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        task_data = task_data_by_id.get(raw.get("task_id"))
        global_index = raw.get("global_index")
        if task_data is None or not raw.get("success") or not global_index:
            continue
        storage = TaskStorage(tasks_dir / str(global_index), str(global_index))
        samples = await storage.load_all_samples(task_type)
        for _index, sample in sorted(samples.items()):
            attempt = sample.successful_attempt
            if attempt is None:
                continue
            target = Path(attempt.path) / "workspaces" / "target"
            if target.exists():
                workspaces[task_data.episode_id] = str(target.resolve())
                break
    return workspaces


def candidate_response_rows(
    task_data_by_id: Dict[str, Any], results: Iterable[Any]
) -> List[Dict]:
    """Project task results into the stable per-work-unit response rows.

    Reads the fields off the typed result and falls back to the task data only for
    identity fields, so a schema change surfaces as a missing key rather than as a
    silently empty candidate list.
    """

    rows = []
    for result in results:
        raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        task_data = task_data_by_id.get(raw.get("task_id"))
        rows.append({
            "work_unit_id": raw.get("work_unit_id") or (
                task_data.work_unit_id if task_data else None
            ),
            "prompt_sha256": raw.get("rendered_prompt_sha256") or (
                task_data.rendered_prompt_sha256 if task_data else None
            ),
            "response": {
                "candidates": raw.get("candidates") or [],
                "adjudications": raw.get("adjudications") or [],
                "verification_artifacts": raw.get("verification_artifacts") or [],
            },
            "success": bool(raw.get("success")),
            "error": raw.get("error"),
        })
        # Arms that run several invocations against one work unit carry their own identity.
        # Without it `ingest_responses` reads four terminal responses for one unit as four
        # duplicates of one and raises, and candidates lose the spec that produced them.
        invocation_id = raw.get("invocation_id") or (
            getattr(task_data, "invocation_id", None) if task_data else None
        )
        if invocation_id:
            rows[-1]["invocation_id"] = invocation_id
        spec_id = raw.get("spec_id") or (
            getattr(task_data, "spec_id", None) if task_data else None
        )
        if spec_id:
            rows[-1]["spec_id"] = spec_id
    rows.sort(key=lambda item: (item.get("invocation_id") or item["work_unit_id"] or ""))
    return rows


def write_candidate_responses(path: Path, rows: Iterable[Dict]) -> Path:
    """Write response rows deterministically (sorted keys, one JSON object per line)."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    return path


def load_candidate_responses(path: Path) -> List[Dict]:
    """Read a candidate-response artifact. The single reader for phases 7, 8, and 9."""

    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


async def unbuilt_base_commits(commits: Iterable[str], repo_name: str = "mathlib4") -> List[str]:
    """Return the base commits whose Lean workspace is not ready to run against.

    Asks the toolkit that owns snapshot state rather than reading its `.state` JSON
    directly, so the definition of "ready" stays with the code that writes it.
    """

    from ape.toolkits.execute.lean.core.workspace_state import WorkspaceStateManager
    from ape.toolkits.execute.lean.models import WorkspaceStatus

    manager = WorkspaceStateManager(repo_name=repo_name)
    usable = {WorkspaceStatus.BUILT, WorkspaceStatus.READY}
    missing = []
    for commit in sorted(set(commits)):
        state = await manager.read_state(commit)
        if state is None or state.status not in usable:
            missing.append(commit)
    return missing


def failed_work_unit_ids(run_dir: Path) -> set:
    """Work units whose task result recorded failure in a previous run.

    Reads `work_unit_id` straight off the persisted result instead of rebuilding a task
    ID from the work-unit ID by string substitution.
    """

    failed = set()
    for result_path in sorted(run_dir.glob("tasks/*/task_result.json")):
        raw = json.loads(result_path.read_text())
        if raw.get("success"):
            continue
        work_unit_id = raw.get("work_unit_id")
        if work_unit_id:
            failed.add(work_unit_id)
    return failed
