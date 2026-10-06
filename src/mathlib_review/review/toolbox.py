"""The arms' own tools, callable outside a run, so a brief or a context can be probed before any
pipeline change.

A probe (`docs/research/facet-brief-probe-2026-09.md`) runs a reviewer agent that is not a
pipeline task. Before this module it had only hand-written `git grep` wrappers, so a finding
there said nothing about what an arm with the pipeline's tools would find, and its reviewers
could not compile: 6 of the 13 information gaps they stated were "could not confirm without
compiling". This module gives such an agent the arms' tools themselves, run by the arms' own
code:
- the context tools, through `register_context_tools`;
- `lean_verify_edit`, through the shared review base;
- the workspace file tools, through `FileSystemToolsProvider`.

It does so by standing a task up without a run. Nothing here reimplements a tool, so a result
from a probe is a result for the pipeline's tool.

**The stand-in** is a `BasePRReviewTask` built without `__init__`, carrying only what the tools
read:
- `data`: the PR, the base commit, the retrieval cutoff, the changed files, and a trace path;
- `target_workspace`: what a task's `setup_attempt` would verify against. That is the prebuilt
  reviewed workspace (base + diff + changed modules rebuilt) when one exists for this (base,
  diff), and otherwise the source-only overlay `ReviewPRCoreTask.prepare_reviewed_sources` lays
  over the compiled base;
- `config`: the scaffold of a real run config, so compile timeouts, memory and allowed axioms
  are a run's own;
- `logger`.

**The retrieval cutoff** is `episode_cutoff`, the reviewed head's commit time, so precedent and
Zulip reads are gated exactly as a run gates them.

**The reviewed workspace first, as a task does.** Until 2026-09-29 the toolbox always laid the
overlay, so a probe compiled every changed file against the base commit's build products. On a
multi-file PR that is the environment the rules file warns about: PR 30458 generalises
`div_right_injective` in `Algebra/Group/Basic.lean` and uses it in `Pointwise/Finset/Basic.lean`,
and the overlay reported `failed to synthesize Group α` in a file that builds. Every compile
result names its environment (`environment`), so the complement probe's results say which they
had.

**Refused without a compiled base.** A `lean_verify_edit` against a missing base would report
every import as an error. A built base is restored on first use, as a task restores it. One that
was never built is refused, with how to build it (`ape.toolkits.execute.lean.build`).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from src.mathlib_review.schema import ReviewEpisodeInput

from src.mathlib_review.agenda.registry import UNIVERSAL_CONTEXT_TOOLS
from src.mathlib_review.schema.review import CONTEXT_TOOLS as _VOCABULARY

#: Every context tool a registrar registers: the vocabulary less what the review base registers
#: for every task (`lean_verify_edit`). Derived, not copied -- this was the second of four
#: copies. `proof_profile` is registered but granted by no config.
CONTEXT_TOOLS = tuple(name for name in _VOCABULARY if name not in UNIVERSAL_CONTEXT_TOOLS)
#: The workspace tools the arms run with (`task_config.enabled_tools` in the v5 configs).
FILE_TOOLS = {"file_read", "content_search", "file_search"}


class _CapturingMCP:
    """Stands in for the MCP server: keeps each registered tool function, and the description
    the arm is shown, by name."""

    def __init__(self) -> None:
        self.tools: Dict[str, Callable[..., Any]] = {}
        self.descriptions: Dict[str, str] = {}

    def tool(self, *args: Any, **kwargs: Any):
        def register(fn):
            name = kwargs.get("name") or fn.__name__
            self.tools[name] = fn
            self.descriptions[name] = kwargs.get("description") or (fn.__doc__ or "")
            return fn
        return register


def describe(mcp: "_CapturingMCP") -> Dict[str, Any]:
    """Each tool as an arm sees it: its description and its arguments' descriptions."""

    import inspect
    from typing import get_args

    out = {}
    for name, fn in sorted(mcp.tools.items()):
        params = {}
        for pname, param in inspect.signature(fn).parameters.items():
            meta = get_args(param.annotation)
            field = next((m for m in meta[1:] if hasattr(m, "description")), None)
            params[pname] = {
                "type": getattr(meta[0], "__name__", str(meta[0])) if meta else str(param.annotation),
                "description": getattr(field, "description", None),
                "default": None if param.default is inspect.Parameter.empty else param.default,
                "required": param.default is inspect.Parameter.empty,
            }
        out[name] = {"description": mcp.descriptions.get(name, ""), "arguments": params}
    return out


def workbench(episode: ReviewEpisodeInput, workdir: Path, run_config: Path) -> "_CapturingMCP":
    """The tools an arm reviewing `episode` would hold, as plain async callables."""

    from ape.tasks.lean_tasks.formal_math.pr_review.core import ReviewPRCoreTask
    from ape.tasks.lean_tasks.formal_math.review.arm import ReviewArmData
    from ape.tasks.lean_tasks.formal_math.review.base import BasePRReviewTask
    from ape.tasks.lean_tasks.formal_math.review.context_tools import register_context_tools
    from ape.tasks.models import WorkspaceInfo
    from ape.toolkits.file_system.tools import FileSystemToolsProvider
    from ape.utils.logging import create_logger
    from src.mathlib_review.agenda.arms import ARM_TASK_TYPE
    from src.mathlib_review.agenda.cutoffs import episode_cutoff
    from src.mathlib_review.evidence.evidence import snapshot_workspace
    from src.mathlib_review.review.runner import load_run

    base = snapshot_workspace(episode.base_sha) or _restore(episode.base_sha)
    if base is None:
        raise RuntimeError(
            f"no compiled base workspace for {episode.base_sha}. Build it first: a row "
            '{"task_type": "probe", "task_id": "...", "target_workspace": {"name": "mathlib4", '
            f'"commit_hash": "{episode.base_sha}", ...}}}} through '
            "`ape/bin/python -m ape.toolkits.execute.lean.build --input_file <rows>`.")
    workdir.mkdir(parents=True, exist_ok=True)
    overlay = workdir / "target"

    _dataset, scaffold, _overrides = load_run(run_config)
    workspace = WorkspaceInfo(name="mathlib4", path=overlay, commit_hash=episode.base_sha)
    # The arms' own data model, so a field the tools read and this stand-in lacks fails here
    # rather than being invented. The unit-level fields a probe has no unit for say so.
    probe = f"probe:{episode.pr_number}"
    task = BasePRReviewTask.__new__(BasePRReviewTask)
    task.data = ReviewArmData(
        task_type=ARM_TASK_TYPE, task_id=probe, target_workspace=workspace,
        pr_number=episode.pr_number, diff=episode.diff, episode_id=episode.episode_id,
        snapshot_base_sha=episode.base_sha, changed_files=list(episode.changed_files),
        retrieval_cutoff=episode_cutoff(episode), context_tools=list(CONTEXT_TOOLS),
        trace_path=str(workdir / "context_trace.jsonl"), invocation_id=probe, arm_id="probe",
        work_unit_id=probe, change_ids=[], entity_ids_by_change={},
        primary_subjects_by_change={}, rendered_system_prompt="", rendered_user_prompt="",
        rendered_prompt_sha256="")
    # Before the workspace is resolved: the restore manager logs through it, and without one it
    # prints to stdout, which is where `cli tool` writes its JSON.
    task.logger = create_logger(log_file=workdir / "toolbox.log", to_console=False)
    task.target_workspace = _target_workspace(task.data, overlay, base, episode, task.logger)
    task.scratch_workspace = None
    # The file tools resolve `target/...` against the directory that holds the workspaces, as
    # an attempt directory holds `target/` in a run.
    task.workspaces_dir = workdir
    task.config = scaffold

    mcp = _CapturingMCP()
    register_context_tools(task, mcp)
    task._register_lean_verify_edit(mcp)
    FileSystemToolsProvider(task=task, config=scaffold, logger=task.logger).register_tools(
        mcp, FILE_TOOLS)
    return mcp


def _target_workspace(data: Any, overlay: Path, base: Path,
                      episode: ReviewEpisodeInput, logger: Any) -> Any:
    """The reviewed workspace linked at `overlay` when one is built, else the source-only overlay.

    The same call `review/base.py::setup_attempt` makes, so a probe compiles where an arm would.
    A directory already at `overlay` is an overlay an earlier call laid down; it is kept only when
    no reviewed workspace exists, because linking over it would mislabel base-commit build
    products as the reviewed ones.
    """

    from ape.tasks.lean_tasks.formal_math.pr_review.core import ReviewPRCoreTask
    from ape.toolkits.execute.lean.core.build_manager import reviewed_workspace_key

    stale = overlay.exists() and not overlay.is_symlink()
    if stale:
        spec = data.target_workspace.model_copy(
            update={"commit_hash": reviewed_workspace_key(episode.base_sha, episode.diff)})
        if asyncio.run(ReviewPRCoreTask._maybe_resolve_cached_workspace(
                spec, logger=logger)) is not None:
            raise RuntimeError(
                f"{overlay} is a source-only overlay from an earlier call, and a reviewed "
                f"workspace ({spec.commit_hash}) exists for PR {episode.pr_number}. Use a new "
                "--workdir, so the tools compile against the reviewed workspace.")
        return data.target_workspace
    reviewed = asyncio.run(ReviewPRCoreTask._maybe_setup_reviewed_target_workspace(
        data, overlay, logger=logger))
    if reviewed is not None:
        return reviewed
    asyncio.run(ReviewPRCoreTask.prepare_reviewed_sources(
        overlay, base, pr_diff=episode.diff, changed_files=list(episode.changed_files)))
    return data.target_workspace


def _restore(commit_hash: str) -> Optional[Path]:
    """Restore a built base into `workspaces/<sha>` as a task would on first use, or None when
    it was never built. A build stores a snapshot; a run restores it only when a task needs it."""

    from ape.toolkits.execute.lean.config import LeanVerifyToolConfig
    from ape.toolkits.execute.lean.core.restore_manager import RestoreManager
    from ape.utils.logging import create_logger
    from src.mathlib_review.evidence.evidence import snapshot_workspace

    config = LeanVerifyToolConfig()
    _name, url = config.resolve_repo(None)
    manager = RestoreManager(config, create_logger(to_console=False), url)
    if asyncio.run(manager._requires_build_first(commit_hash)):
        return None
    try:
        asyncio.run(manager.get_workspace(commit_hash))
    except RuntimeError:
        # Seen once, on a snapshot whose build had just finished: the first restore fails and
        # the second completes it.
        asyncio.run(manager.get_workspace(commit_hash))
    return snapshot_workspace(commit_hash)


def call(tools: Dict[str, Callable], name: str, arguments: Dict[str, Any]) -> Any:
    if name not in tools:
        raise KeyError(f"unknown tool {name!r}; available: {sorted(tools)}")
    return asyncio.run(tools[name](**arguments))


def load_episode(episodes: Path, pr_number: int) -> ReviewEpisodeInput:
    from src.mathlib_review.io import load_jsonl

    for episode in load_jsonl(episodes, ReviewEpisodeInput):
        if episode.pr_number == pr_number:
            return episode
    raise KeyError(f"PR {pr_number} is not in {episodes}")


def main(args) -> int:
    """`cli tool`: one tool call, its result printed as JSON."""

    episode = load_episode(Path(args.episodes), args.pr)
    mcp = workbench(episode, Path(args.workdir), Path(args.run_config))
    if args.name == "list":
        print(json.dumps(sorted(mcp.tools)))
        return 0
    if args.name == "describe":
        print(json.dumps(describe(mcp), indent=1, ensure_ascii=False, default=str))
        return 0
    arguments: Dict[str, Any] = json.loads(args.arguments) if args.arguments else {}
    result = call(mcp.tools, args.name, arguments)
    print(json.dumps(result, indent=1, ensure_ascii=False, default=str))
    return 0
