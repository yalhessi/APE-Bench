"""Plan and run paired whole-PR reviews with four prior-history strategies."""

import asyncio
import json
from pathlib import Path
from typing import Literal, NamedTuple

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ape.toolkits.execute.lean.core.build_manager import reviewed_workspace_key
from src.mathlib_review.io import (
    canonical_json_bytes, jsonl_bytes, pretty_json_bytes, sha256_bytes, sha256_file, write_once,
)
from src.mathlib_review.analysis import probes, submissions
from src.mathlib_review.conventions import selection
from src.mathlib_review.retrieval import excerpts
from src.mathlib_review.retrieval_gate import RetrievalGate
from src.mathlib_review.review import runner
from src.mathlib_review.review.inputs import first_message, mcp_signatures

Strategy = Literal["solo", "history", "automatic", "exact"]
DEFAULT_STRATEGIES = ("solo", "history", "automatic", "exact")


class ReviewedCases(NamedTuple):
    dataset: runner.V5DatasetConfig
    release: dict
    units: list
    episodes: list
    cutoffs: dict


class ReviewStudy(BaseModel):
    """A paired comparison of four ways to deliver prior reviews to one whole-PR reviewer."""
    model_config = ConfigDict(extra="forbid")
    name: str
    output: Path
    reviewer: Path
    selector: Path
    matcher: Path
    reference: Path
    history: Path
    history_before: str
    heads: dict[int, str] = Field(min_length=1)

    strategies: tuple[Strategy, ...] = DEFAULT_STRATEGIES

    @field_validator("strategies")
    @classmethod
    def paired_with_solo(cls, names):
        if len(names) < 2 or names[0] != "solo" or len(names) != len(set(names)):
            raise ValueError("List solo first and at least one distinct comparison strategy")
        return names

    @property
    def selectors(self):
        return tuple(s for s in self.strategies if s in ("automatic", "exact"))

    def generation_definition(self):
        return self.model_dump(mode="json", exclude={"matcher"}, exclude_defaults=True)

    def cases(self, reference):
        ds, scaffold, _ = runner.load_run(self.reviewer, {"dataset": {"pr_numbers": sorted(self.heads)}})
        if scaffold.scaffold_type != "claude_code":
            raise ValueError("Review studies currently verify Claude Code reviewer transcripts")
        task = scaffold.task_config_overrides or {}
        if (set(scaffold.tools) != {"Read", "Grep", "Glob"} or scaffold.batch_preamble != "plain"
                or scaffold.workspace_environment or task.get("system_prompt_file") or task.get("context_file")):
            raise ValueError("Use the ordinary whole-PR contract with Read, Grep and Glob, plain preamble, "
                             "workspace environment disabled and no preloaded brief or context")
        if ds.design != "whole_pr" or ds.release != reference.release or not self.heads.keys() <= set(reference.pr_numbers):
            raise ValueError("A convention study needs whole_pr and a reference set covering the same reviewed cases")
        release = runner.load_release(ds)
        units, episodes = runner.select_units_and_episodes(ds, release)
        if {e.pr_number: e.reviewed_head_sha for e in episodes} != self.heads or len(episodes) != len(self.heads):
            raise ValueError("Release does not match the study's pinned heads")
        cutoffs = runner.cutoffs_by_episode(episodes)
        cutoff = RetrievalGate(as_of=self.history_before).cutoff_epoch
        if cutoff is None or any(cutoff > RetrievalGate(as_of=date).cutoff_epoch for date in cutoffs.values()):
            raise ValueError("History extends beyond a reviewed revision")
        return ReviewedCases(ds, release, units, episodes, cutoffs)


ADVICE = "Use these conventions when they apply. Decide whether any change is worth asking the author to make."
COMMON_TOOLS = {"code_goto", "code_hover", "declaration_search", "get_lean_goal",
                "lean_verify", "lean_verify_edit", "submit_findings"}


def context_rows(episodes, rules, choices):
    rows = []
    for ep in episodes:
        selected = choices[str(ep.pr_number)]
        if len(selected) != len(set(selected)) or set(selected) - rules.keys():
            raise ValueError(f"Invalid selection for {ep.episode_id}: {selected}")
        sentences = [sentence for key, sentence in rules.items() if key in selected]
        sections = []
        if sentences:
            sections.append({"title": "Conventions",
                             "text": ADVICE + "\n\n" + "\n".join("- " + s for s in sentences)})
        rows.append({"pr_number": ep.pr_number, "episode_id": ep.episode_id,
                     "reviewed_head_sha": ep.reviewed_head_sha, "sections": sections})
    return rows


async def generation_plan(study, out, sample, fixture, cases, products):
    base, release, units, episodes, cutoffs = cases
    await runner.assert_reviewed_workspaces_prebuilt(episodes, required=True)
    history = study.output / "history"
    conventions = study.output / "conventions"
    if fixture:
        # Both selectors receive identical selections here, including an empty one.
        rules = {"C1": "Demonstration sentence for the local rendering check."}
        example = {str(pr): (["C1"] if i % 2 or len(study.heads) == 1 else [])
                   for i, pr in enumerate(sorted(study.heads))}
        assignments = {arm: example for arm in study.selectors}
    else:
        rules = {r["id"]: r["principle"] for r in products.get("catalogue", [])}
        assignments = {arm: products[arm]["prs"] for arm in study.selectors}

    # Run and context filenames are opaque even in the first model-facing message.
    manifest = {"sample": sample, "fixture": fixture, "runs": {},
                "history_sha256": sha256_file(history / "excerpts.jsonl")}
    if "history" in study.strategies:
        index_path = history / "index/manifest.json"
        if json.loads(index_path.read_bytes())["corpus_sha256"] != manifest["history_sha256"]:
            raise ValueError("Direct search and catalogue construction have different excerpt sources")
        manifest["index_manifest_sha256"] = sha256_file(index_path)
    if not fixture and study.selectors:
        manifest["convention_files"] = {f: sha256_file(conventions / f)
                                        for f in ("catalogue.json", *(s + ".json" for s in study.selectors))}
    agenda, _ = runner.agenda_for_release(base, release, units, episodes, sorted(study.heads))
    base_messages, common_signatures = {}, None
    commands = []
    # Existing manifests keep their original opaque run names. New samples also bind
    # the study definition, so another study with the same display name cannot resume them.
    prior_path = out / "generation.json"
    prior = json.loads(prior_path.read_text())["runs"] if prior_path.is_file() else {}
    for arm in study.strategies:
        identity = [study.generation_definition(), sample, arm, fixture]
        name = "r" + sha256_bytes(canonical_json_bytes(identity))[:20]
        if arm in prior:
            name = prior[arm]["run"]
        overrides = {"dataset": {}}
        expected_tools = COMMON_TOOLS.copy()
        if arm == "history":
            expected_tools.add("precedent_search")
            overrides["dataset"].update(solo_context_tools=["declaration_search", "precedent_search"],
                                        solo_precedent_index=str(history / "index"))
        contexts = {}
        if arm in assignments:
            rows = context_rows(episodes, rules, assignments[arm])
            path = out / "inputs" / (name + ".jsonl")
            write_once(path, jsonl_bytes(rows))
            overrides["task_config"] = {"context_file": str(path)}
            contexts = {row["pr_number"]: row["sections"] for row in rows}
        run_options = {**overrides, "dataset": {**overrides["dataset"], "pr_numbers": sorted(study.heads),
                                               "run_name": name}}
        ds, scaffold, _ = runner.load_run(study.reviewer, run_options)
        runner.pin_input_files(scaffold)
        tasks = runner._solo_task_data(agenda, episodes, ds, cutoffs, runner.run_dir(name) /
                                       "context_trace.jsonl", release["graphs"])
        record = {"run": name, "overrides": overrides, "episodes": {}}
        for payload in tasks:
            pr = payload["pr_number"]
            task = runner.create_task_from_data(payload, scaffold, task_config_overrides=scaffold.task_config_overrides)
            key = reviewed_workspace_key(task.data.snapshot_base_sha, task.data.diff)
            target = Path("data/code_execute/repos/mathlib4/workspaces") / key
            cwd = (Path(".ape/runs") / name / "workspaces").resolve()
            message = (await first_message(task, cwd, target)).replace(str(cwd), "{attempt_workspaces}")
            tools = await mcp_signatures(task)
            if set(tools) != expected_tools:
                raise ValueError(f"{arm}/{pr}: unexpected tool grants {sorted(tools)}")
            shared = {k: tools[k] for k in sorted(COMMON_TOOLS)}
            if common_signatures is None:
                common_signatures = shared
            if common_signatures != shared:
                raise ValueError(f"{arm}/{pr}: common tool schemas changed")
            if arm == "solo":
                base_messages[pr] = message
            sections = contexts.get(pr, [])
            suffix = ("\n\n## Conventions\n\n" + sections[0]["text"]) if sections else ""
            if message != base_messages[pr] + suffix:
                raise ValueError(f"{arm}/{pr}: rendered difference beyond the supplied conventions")
            # Preserve the expected full first message for comparison with the live SDK transcript.
            message_path = out / "inputs" / f"{name}-{pr}.txt"
            write_once(message_path, message.encode())
            ep = next(e for e in episodes if e.pr_number == pr)
            record["episodes"][str(pr)] = {
                "episode_id": ep.episode_id, "patch_sha256": ep.patch_sha256, "cutoff": cutoffs[ep.episode_id],
                "message": str(message_path), "message_sha256": sha256_file(message_path),
                "mcp": sorted(tools), "mcp_schema_sha256": sha256_bytes(canonical_json_bytes(tools)),
                "builtins": sorted(scaffold.tools), "model": scaffold.claude_model,
                "effort": scaffold.effort, "cli_version": scaffold.cli_version,
                "max_turns": scaffold.execution.max_turns, "token_cap": ds.solo_token_cap,
                "cost_cap": ds.solo_cost_cap,
            }
        if set(record["episodes"]) != {str(pr) for pr in study.heads}:
            raise ValueError(f"{arm}: incomplete episode coverage")
        manifest["runs"][arm] = record
        if arm == "history":
            record["history_sha256"] = manifest["history_sha256"]
        commands.append((name, run_options))
    write_once(out / "generation.json", pretty_json_bytes(manifest))
    return commands


def run_study(args, logger):
    path = Path(args.study)
    if not path.is_file() and not path.suffix:
        path = Path("configs/studies") / (args.study + ".yaml")
    study = ReviewStudy.model_validate(yaml.safe_load(path.read_text()))
    reference = probes.load_probe_set(study.reference)
    action = args.study_action
    sample = getattr(args, "sample", 1)
    if sample < 1:
        raise ValueError("A generation sample starts at 1")
    fixture = action == "plan"
    out = study.output / ("wiring" if fixture else f"sample-{sample}")
    if action == "score":
        submissions.compare(out, args.question_form, args.execute, reference=reference,
                            name=study.name, config=study.matcher, reading=args.reading)
        return 0

    # Pin the generation definition before paying for preparation. A scoring revision
    # can choose a different matcher without invalidating the already generated reviews.
    cases = study.cases(reference)
    if action == "run" and args.execute:
        _, scaffold, _ = runner.load_run(study.reviewer)
        runner.assert_ready(scaffold, logger)
        asyncio.run(runner.assert_reviewed_workspaces_prebuilt(cases.episodes, required=True))
    write_once(study.output / "study.json", pretty_json_bytes(study.generation_definition()))
    history = study.output / "history"
    collect = excerpts.prepare if "history" in study.strategies else excerpts.freeze
    collect(history, study.history, study.history_before, sorted(study.heads))
    retries = {}
    for item in getattr(args, "retry", []):
        stage, _, number = item.partition("=")
        if not number.isdecimal() or stage in retries:
            raise ValueError("Specify each retry once as --retry STAGE=N with a positive attempt number")
        retries[stage] = int(number)
    if retries and not study.selectors:
        raise ValueError("This comparison has no convention selection stages to retry")
    products = {}
    if study.selectors:
        products = selection.prepare(study.output / "conventions", history / "excerpts.jsonl",
                                     reference=reference, heads=study.heads, config=study.selector,
                                     selectors=study.selectors, execute=getattr(args, "execute", False), retry=retries)
    if action == "prepare" or (not fixture and products is None):
        if products is None:
            print("Convention selection awaits model output. Use study prepare or study run with --execute.")
        elif study.selectors:
            print(f"{len(products['catalogue'])} conventions and selections saved in {study.output}/conventions")
        else:
            print(f"Shared history ready in {history}")
        return 0
    commands = asyncio.run(generation_plan(study, out, sample, fixture, cases, products))
    print(f"{out}/generation.json: {len(study.strategies)} strategies × {len(study.heads)} reviewed heads")
    for execute in ([False, True] if getattr(args, "execute", False) else [False]):
        for name, overrides in commands:
            ds, scaffold, task_options = runner.load_run(study.reviewer, overrides)
            ds.dry_run = not execute
            path = runner.run_dir(name)
            manifest = path / "run_manifest.json"
            if execute and manifest.exists() and json.loads(manifest.read_text())["completion_status"] == "complete":
                continue
            resume = execute and (path.exists() or (Path(".ape/runs") / name).exists())
            asyncio.run(runner.run(ds, scaffold, task_options, logger, resume=resume))
    if fixture:
        print(f"Verified fixture prompts and grants for {', '.join(study.strategies)} on "
              f"PRs {', '.join(map(str, sorted(study.heads)))}.")
    if getattr(args, "execute", False):
        manifest = json.loads((out / "generation.json").read_text())
        asyncio.run(submissions.capture(out, manifest["runs"]))
        print(f"Accepted reviews archived at {out / 'archive.json'}")
    return 0
