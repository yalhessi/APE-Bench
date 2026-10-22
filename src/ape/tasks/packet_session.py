"""A model works over a folder of inputs and leaves declared output files: a registered Task.

The shape of most research sessions in this project: a folder holding instructions and inputs, a
session prompt saying "your working folder is {dir}; read `instructions.md`; write `x.json`", and
outputs read back from the folder. Extractors, auditors, sketchers, blind readers and matchers all
ran that way, as hand-launched sessions outside the orchestrator (`run_claude_batch.sh` and its
audits), and only the digests of what each session read were kept, while its folder lived in a
scratch directory (`docs/research/task-dataflow-refactor-implementation-2026-10-22.md`, slice B).

As a Task, the folder's files are the task's data -- so the bytes a session read are its identity
and stay with its run -- the folder is laid into the attempt's own scratch workspace, the outputs
are declared up front and validated by `submit_outputs`, and the orchestrator runs, limits, retries
and records the session like any other task. Independent samples are independent sessions; nothing
is merged. Domain-free: what the instructions ask and what the outputs mean belong to the study.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ape.tasks.base import (
    BaseTask,
    BaseTaskConfig,
    BaseTaskData,
    BaseTaskResult,
    EvaluationResult,
    register_task,
)

PACKET_SESSION_TASK_TYPE = "packet_session"
#: The token a brief uses for the folder's absolute path, as every probe session prompt did.
DIR_TOKEN = "{dir}"
#: Where the folder sits in the attempt's workspace.
PACKET_DIR = "packet"


class PacketFile(BaseModel):
    """One input file, by its path inside the folder."""

    model_config = ConfigDict(extra="forbid")
    path: str
    content: str

    @model_validator(mode="after")
    def _inside_the_folder(self) -> "PacketFile":
        parts = PurePosixPath(self.path).parts
        if not parts or PurePosixPath(self.path).is_absolute() or ".." in parts:
            raise ValueError(f"packet file {self.path!r} must be a relative path inside the folder")
        return self


class OutputSpec(BaseModel):
    """A file the session must leave in the folder, and how it is checked."""

    model_config = ConfigDict(extra="forbid")
    name: str
    kind: Literal["json", "jsonl", "text"] = "text"
    required: bool = True


class PacketSessionConfig(BaseTaskConfig):
    """Reading and writing in the folder. On Claude Code the route's own tools do this."""

    enabled_tools: Optional[list] = Field(
        default_factory=lambda: ["file_read", "file_write", "content_search", "file_search"])


class PacketSessionData(BaseTaskData):
    task_type: str = PACKET_SESSION_TASK_TYPE
    #: The session prompt; `{dir}` is replaced by the folder's absolute path.
    brief: str
    files: List[PacketFile]
    outputs: List[OutputSpec]
    #: The sealed plan and the packet this session belongs to, for reading it back.
    plan_id: str = ""
    packet_id: str = ""

    @model_validator(mode="after")
    def _outputs_are_not_inputs(self) -> "PacketSessionData":
        clash = {o.name for o in self.outputs} & {f.path for f in self.files}
        if clash:
            raise ValueError(f"outputs {sorted(clash)} are already input files: a finished session")
        return self


class PacketSessionResult(BaseTaskResult):
    plan_id: str = ""
    packet_id: str = ""
    #: {output name: {"sha256", "content"}} as the session left them.
    outputs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


def output_problems(folder: Path, outputs: List[OutputSpec]) -> tuple:
    """`({name: content}, problems)` for the declared outputs as they are in `folder`."""

    found: Dict[str, str] = {}
    problems: List[str] = []
    for spec in outputs:
        path = Path(folder) / spec.name
        if not path.is_file():
            if spec.required:
                problems.append(f"{spec.name} is missing from the working folder")
            continue
        text = path.read_text(encoding="utf-8")
        try:
            if spec.kind == "json":
                json.loads(text)
            elif spec.kind == "jsonl":
                for n, line in enumerate(text.split("\n"), start=1):
                    if line.strip():
                        json.loads(line)
        except ValueError as error:
            problems.append(f"{spec.name} is not valid {spec.kind}: {error}")
            continue
        found[spec.name] = text
    return found, problems


class PacketSessionTask(BaseTask):
    task_type = PACKET_SESSION_TASK_TYPE
    data_class = PacketSessionData
    task_config_class = PacketSessionConfig
    task_result_class = PacketSessionResult
    submit_tool = "submit_outputs"

    @property
    def packet_dir(self) -> Path:
        if self.scratch_workspace is None or self.scratch_workspace.path is None:
            raise RuntimeError("the packet folder exists only once the task is set up")
        return Path(self.scratch_workspace.path) / PACKET_DIR

    async def setup(self, termination_callback, orchestrator_id: str, attempt_path=None):
        logger = await super().setup(termination_callback, orchestrator_id, attempt_path)
        folder = self.packet_dir
        (folder / "tmp").mkdir(parents=True, exist_ok=True)
        for item in self.data.files:
            path = folder / item.path
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text(item.content, encoding="utf-8")
        return logger

    @property
    def folder_reference(self) -> str:
        """The folder as the session's file tools name it, which is what `{dir}` becomes.

        APE's own file tools (the `ape_agent` scaffold) refuse an absolute path and resolve a path
        against the attempt's workspaces folder, so there it is `scratch/packet`. Every other route
        brings its own tools, which take the absolute path (Claude Code's are contained to the
        workspace). Before this, an `ape_agent` session was told an absolute folder that every one
        of its tools refused."""

        if self.config.scaffold_type == "ape_agent":
            return self.packet_dir.relative_to(self.workspaces_dir).as_posix()
        return str(self.packet_dir.resolve())

    async def create_user_prompt(self) -> str:
        names = ", ".join(f"`{o.name}`" for o in self.data.outputs)
        return (self.data.brief.replace(DIR_TOKEN, self.folder_reference)
                + f"\n\nWhen {names} {'is' if len(self.data.outputs) == 1 else 'are'} written in "
                  f"the working folder, call `{self.submit_tool}` to hand them in.")

    async def register_task_tools(self, mcp) -> None:
        @mcp.tool(description=(
            "Hand in the outputs written in the working folder. Refused, with the reasons, while "
            "a required output is missing or does not parse; the session ends when accepted."))
        async def submit_outputs() -> Dict[str, Any]:
            found, problems = output_problems(self.packet_dir, self.data.outputs)
            if problems:
                return {"success": False, "accepted": False, "problems": problems,
                        "error": "Outputs refused; write them and call again."}
            if self.termination_callback:
                await self.termination_callback(self.create_result(
                    success=True, score=1.0, plan_id=self.data.plan_id,
                    packet_id=self.data.packet_id,
                    outputs={name: {"sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                                   "content": text}
                             for name, text in found.items()}))
            return {"evaluation_result": EvaluationResult(success=True, score=1.0,
                                                          message=f"{len(found)} outputs"),
                    "accepted": True, "message": "Outputs recorded"}

    @classmethod
    def product_of(cls, result) -> Optional[Dict[str, Any]]:
        if not getattr(result, "success", False):
            return None
        return {"plan_id": result.plan_id, "packet_id": result.packet_id,
                "outputs": result.outputs}

    @classmethod
    def is_best_result(cls, result) -> bool:
        return bool(getattr(result, "success", False))

    @classmethod
    def aggregate_results(cls, results):
        """Nothing is merged: each sample is a session in its own right, read through
        `sample_products`. The first is the task's marker result."""

        results = [item for item in results if getattr(item, "success", False)]
        return results[0] if results else None


register_task(PACKET_SESSION_TASK_TYPE, PacketSessionTask)
