"""Resolve a named whole-PR reviewer, independently of any comparison or its rubric."""

import asyncio
import json
import re
import sys
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from src.mathlib_review.analysis import submissions
from src.mathlib_review.io import canonical_json_bytes, pretty_json_bytes, sha256_bytes, sha256_file, write_once
from src.mathlib_review.retrieval import excerpts
from src.mathlib_review.retrieval_gate import RetrievalGate
from src.mathlib_review.run_state import claim_execution
from src.mathlib_review.review import runner
from src.mathlib_review.review.inputs import COMMON_TOOLS, inspect_review


class ExcerptCollection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: Path
    before: str
    excluded: list[int]
    model_revision: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    def index(self):
        directory = Path(".ape/review-history") / self.sha256
        index = directory / "index"
        if not index.is_dir():
            excerpts.prepare(directory, self.source, self.before, self.excluded)
        built = submissions.read(index / "manifest.json")
        if (sha256_file(directory / "excerpts.jsonl") != self.sha256 or built["corpus_sha256"] != self.sha256
                or built["model_revision"] != self.model_revision):
            raise ValueError(f"{directory}: search corpus or embedding model differs from the named edition")
        return index


class Reviewer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile: Path
    history: ExcerptCollection | None = None


@dataclass(frozen=True)
class PreparedRun:
    """What one named run records before its reviewer is dispatched."""
    message: str
    manifest: dict
    inputs: dict
    run_name: str
    #: The name already holds a record that keeps its inputs inside it (`holds_inline_inputs`).
    inline_inputs: bool


@dataclass
class ReviewRequest:
    reviewer: str
    definition: Reviewer
    pr: int
    head: str
    directory: Path

    def accepted(self):
        return (self.directory / "archive.json").is_file()

    async def prepare(self, payload, ep, dataset, scaffold, *, inputs):
        """The generation record this request implies, checked against what its name already holds.

        Writes nothing, so a refused request leaves the name as it was. Returns what `record`
        writes and `preview` prints.
        """
        task_config = scaffold.task_config_overrides or {}
        if (dataset.design != "whole_pr" or scaffold.scaffold_type != "claude_code"
                or scaffold.batch_preamble != "plain" or scaffold.workspace_environment
                or set(scaffold.tools) != {"Read", "Grep", "Glob"} or task_config.get("system_prompt_file")
                or task_config.get("context_file") or scaffold.execution.sample_count != 1):
            raise ValueError("The profile differs from the standard single-session whole-PR contract")
        message, tools, record = await inspect_review(payload, dataset, scaffold, ep)
        expected = set(COMMON_TOOLS)
        run = {"run": dataset.run_name, "episodes": {str(self.pr): record},
               "tasks_dir": str(scaffold.execution.get_tasks_path(Path(scaffold.runs_base_dir) / dataset.run_name))}
        manifest = {"fixture": False, "reviewer": self.reviewer, "sample": 1, "runs": {self.reviewer: run},
                    "profile_sha256": sha256_bytes(canonical_json_bytes(scaffold.model_dump(mode="json"))),
                    "definition": self.definition.model_dump(mode="json"), "release": str(dataset.release)}
        if self.definition.history:
            history = self.definition.history
            if RetrievalGate(as_of=history.before).cutoff_epoch > RetrievalGate(as_of=record["cutoff"]).cutoff_epoch:
                raise ValueError(f"History extends beyond the reviewed head {ep.episode_id}")
            expected.add("precedent_search")
            run["history_sha256"] = manifest["history_sha256"] = history.sha256
            manifest["index_manifest_sha256"] = payload["precedent_manifest_sha256"]
        if set(tools) != expected:
            raise ValueError(f"{self.reviewer}: expected {sorted(expected)}, got {sorted(tools)}")
        record.update(mcp_schemas=tools, reviewed_head_sha=ep.reviewed_head_sha, base_sha=ep.base_sha,
                      message=str(self.directory / "first-message.txt"))
        inline = False
        saved = self.directory / "generation.json"
        if saved.is_file():
            held = submissions.read(saved)
            if submissions.holds_inline_inputs(held):
                run["inputs"] = inputs
                inline = True
            kept = {saved: pretty_json_bytes(manifest),
                    self.directory / "first-message.txt": message.encode()}
            if (self.directory / submissions.INPUTS_FILE).is_file():
                kept[self.directory / submissions.INPUTS_FILE] = pretty_json_bytes({dataset.run_name: inputs})
            if any(path.is_file() and path.read_bytes() != data for path, data in kept.items()):
                cases = []
                for name, held_run in held.get("runs", {}).items():
                    heads = [f"{pr}@{e.get('reviewed_head_sha', '?')[:8]}" for pr, e in held_run["episodes"].items()]
                    cases.append(f"{name} on {', '.join(heads)}")
                raise ValueError(f"{self.directory}: this name holds a different review ({'; '.join(cases)}) "
                                 "or one recorded with other inputs. Resume it with its own reviewer and case, "
                                 "or choose a fresh name.")
        return PreparedRun(message, manifest, inputs, dataset.run_name, inline)

    def preview(self, prepared):
        print(prepared.message)
        print(json.dumps(prepared.manifest, indent=2))
        print(f"Run inputs: {json.dumps(prepared.inputs, sort_keys=True)}", file=sys.stderr)

    def record(self, prepared):
        if not prepared.inline_inputs:
            submissions.record_inputs(self.directory, prepared.run_name, prepared.inputs)
        write_once(self.directory / "generation.json", pretty_json_bytes(prepared.manifest))
        write_once(self.directory / "first-message.txt", prepared.message.encode())


def run_reviewer(args, logger):
    case = re.fullmatch(r"([1-9][0-9]*)@([a-fA-F0-9]{7,40})", args.case or "")
    if not case:
        raise ValueError("Use --case PR@HEAD with at least seven hexadecimal digits of the reviewed head")
    pr, head = int(case[1]), case[2].lower()
    execute = getattr(args, "execute", False)
    if execute and not args.run_name:
        raise ValueError("Supply --run-name to identify this sample")
    if args.overrides or args.of_run or getattr(args, "redo", False) or getattr(args, "cost_model", None):
        raise ValueError("Named reviewers use their fixed profile. Use --config for custom overrides.")
    directory = submissions.review_directory(args.run_name or "preview")
    path = Path("configs/designs/reviewers") / (args.reviewer + ".yaml")
    definition = Reviewer.model_validate(yaml.safe_load(path.read_text()))
    request = ReviewRequest(args.reviewer, definition, pr, head, directory)
    opaque_name = "r" + sha256_bytes(canonical_json_bytes(["named-review", directory.name]))[:24]
    options = {"run_name": opaque_name}
    if definition.history:
        options.update(solo_context_tools=["declaration_search", "precedent_search"],
                       solo_precedent_index=str(definition.history.index()))
    dataset, scaffold, task_options = runner.load_run(definition.profile, {"dataset": options})
    dataset.dry_run = not execute
    with claim_execution(directory) if execute else nullcontext():
        resume = getattr(args, "resume", False)
        if execute and not resume and (directory / "generation.json").exists():
            raise ValueError(f"{directory}: name already used. Resume this sample or choose a fresh name.")
        if resume and execute and not (directory / "generation.json").exists():
            raise ValueError(f"{directory}: no saved named review to resume")
        asyncio.run(runner.review_episode(dataset, scaffold, task_options, logger, request, resume=resume))
        if execute:
            submissions.saved_reviews(directory, recover=True)
            print(f"Saved submitted review: {directory / 'archive.json'}")
    if args.score:
        if execute:
            return submissions.score_reviews([directory], args.score, execute=True)
        print(f"After submission: {submissions.scoring_description(args.score)}")
    return 0
