"""Resolve independent study choices to ordinary generation configs before dispatch."""
import asyncio
import itertools
import json
import re
from functools import cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, PositiveFloat, PositiveInt

from ape.llm_clients.config import ConfigurationError, MODEL_MAPPINGS
from ape.tasks.lean_tasks.formal_math.review import DESIGNS
from ape.tasks.lean_tasks.formal_math.review.solo import solo_system_prompt
from ape.tasks.lean_tasks.formal_math.review.whole_pr import DEFAULT_BRIEF
from ape.scaffolds.skills import SKILL_TOOL_NAMES
from ape.toolkits import BashExecuteToolsProvider, FileSystemToolsProvider, get_all_tool_names
from ape.utils.config_loader import load_yaml
from src.mathlib_review.analysis import probes, submissions
from src.mathlib_review.io import canonical_json_bytes, jsonl_rows, pretty_json_bytes, sha256_bytes, write_once
from src.mathlib_review.retrieval_gate import RetrievalGate
from src.mathlib_review.review import runner
from src.mathlib_review.review.reviewers import Reviewer, ReviewRequest
from src.mathlib_review.run_state import claim_execution
from src.mathlib_review.review.inputs import inspect_review, pin_overrides, resolve_input_files


class Definition(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Stage(Definition):
    algorithm: str
    operations: list[str]
    context_tools: list[str] = []
    brief: str | None = None
    task: dict = {}
    case_context: bool = False
    history_from: Path | None = None
    # A reads_stage task receives this earlier stage's ledger through the runner's --of handoff.
    reads: str | None = None


class Design(Definition):
    stages: dict[str, Stage]

    def generation_order(self):
        roles = []
        role = "reviewer"
        while role:
            if role in roles or role not in self.stages:
                raise ValueError(f"Missing or circular stage dependency: {role}")
            roles.append(role)
            role = self.stages[role].reads
        if set(roles) != self.stages.keys():
            raise ValueError("Every stage must contribute to the reviewer")
        return reversed(roles)


class Budget(Definition):
    max_turns: PositiveInt
    solo_cost_cap: PositiveFloat
    solo_token_cap: PositiveInt
    run_total_cost_cap: PositiveFloat | None = None
    run_total_token_cap: PositiveInt | None = None


class Study(Definition):
    designs: list[str] = Field(min_length=1)
    models: list[str] = Field(min_length=1)
    scaffolds: list[str] = Field(min_length=1)
    cases: list[str] = Field(min_length=1)
    samples: PositiveInt
    budget: Budget
    stage_models: dict[str, str] = {}
    # Optional historical run configs for checking the shared reviewer contract on each case set.
    controls: dict[str, Path] = {}


def digest(value):
    return sha256_bytes(canonical_json_bytes(value))


def selections(study, condition):
    axes = {"design": study.designs, "model": study.models, "scaffold": study.scaffolds, "cases": study.cases}
    for axis, names in axes.items():
        if len(names) != len(set(names)) or any(not re.fullmatch(r"[\w.-]+", n) for n in names):
            raise ValueError(f"Invalid or repeated {axis} definition in {names}")
    seen = set()
    for item in condition.split(",") if condition else ():
        key, _, value = item.partition("=")
        if key in seen or key not in axes or value not in axes[key]:
            raise ValueError(f"Unknown or repeated --condition choice {item!r}; study axes: {axes}")
        axes[key] = [value]
        seen.add(key)
    return [dict(zip(axes, values)) for values in itertools.product(*axes.values())]


def cases_of(spec):
    if not spec.pr_numbers or len(spec.pr_numbers) != len(set(spec.pr_numbers)) or spec.heads.keys() - set(spec.pr_numbers):
        raise ValueError("pr_numbers must select distinct PRs and cover every pinned head")
    strata = spec.release / "derived/evaluation_strata.jsonl"
    metadata = {r["pr_number"]: r for r in jsonl_rows(strata)} if strata.exists() else {}
    episodes = []
    heads = {pr: spec.heads.get(pr, "") for pr in spec.pr_numbers}
    selected = runner.select_reviewed_episodes(spec.release, heads)
    for ep in selected:
        pr = ep.pr_number
        row = metadata.get(pr, {})
        evidence = row.get("ai_evidence")
        episodes.append({"pr_number": pr, "episode_id": ep.episode_id, "base_sha": ep.base_sha,
                         "reviewed_head_sha": ep.reviewed_head_sha, "patch_sha256": ep.patch_sha256,
                         "author": row.get("author"), "ai": bool(evidence) if evidence is not None else None,
                         "ai_evidence": evidence})
    return episodes, selected


def refuse_fields(raw, forbidden, owner):
    conflicts = sorted(raw.keys() & forbidden)
    if conflicts:
        raise ValueError(f"{owner} cannot set {', '.join(conflicts)}")


def route_model(model, scaffold):
    name = model.get("model_name")
    if not isinstance(name, str) or not name:
        raise ValueError("model definition requires model_name")
    if scaffold.get("route") == "subscription":
        if scaffold["scaffold_type"] != "claude_code":
            raise ValueError("subscription requires scaffold_type claude_code")
        refuse_fields(model, model.keys() - {"model_name", "reasoning_effort"}, "subscription model")
        return {"claude_model": name, "effort": model.get("reasoning_effort"), "llm_config": {"model_name": None}}
    if scaffold.get("route", "provider") != "provider":
        raise ValueError(f"Unknown scaffold route {scaffold['route']}")
    allowed = {"model_name", "reasoning_effort", "openai_api", "openai_responses_reasoning_carryover",
               "openai_responses_reasoning_summary", "temperature", "max_tokens", "thinking_budget_tokens"}
    refuse_fields(model, model.keys() - allowed, "model definition")
    if MODEL_MAPPINGS.get(name, {}).get("supports_tools") is False:
        raise ValueError(f"model_name {name} cannot call review tools")
    return {"llm_config": model}


def compose_stage(stage, model, scaffold, spec, study, episodes, logger, history):
    scaffold = scaffold.copy()
    allowed = {"scaffold_type", "route", "execution", "batch_preamble", "workspace_environment", "system_prompt_role",
               "permission_mode", "tools", "setting_sources", "strict_mcp_config", "disallowed_tools",
               "contain_to_workspace", "cli_version", "use_native_tools", "sandbox_mode", "approval_policy",
               "network_access", "web_search", "disabled_features", "relayed_builtin_tools", "list_mcp_tools_upfront"}
    refuse_fields(scaffold, scaffold.keys() - allowed, "scaffold")
    execution = scaffold.pop("execution", {})
    execution_fields = {"max_concurrency", "num_processes", "optimize_task_order", "task_retry_delay",
                        "task_retry_jitter", "task_max_retries", "worker_idle_timeout", "shuffle_seed"}
    if not isinstance(execution, dict):
        raise ValueError("scaffold.execution must be a mapping")
    refuse_fields(execution, execution.keys() - execution_fields, "scaffold.execution")
    if scaffold.get("scaffold_type") not in {"ape_agent", "codex", "claude_code"}:
        raise ValueError("scaffold_type must name a supported review scaffold")
    model_settings = route_model(model, scaffold)
    scaffold.pop("route", None)
    task = stage.task.copy()
    refuse_fields(task, {"enabled_tools", "disabled_tools", "system_prompt_sha256", "context_file_sha256"}, "stage.task")
    if stage.case_context:
        if not spec.review_context or "context_file" in task:
            raise ValueError("case_context requires one review_context from the case selection")
        task["context_file"] = str(spec.review_context)
    kind = scaffold["scaffold_type"]
    if kind == "claude_code":
        if (scaffold.get("tools") is None or not scaffold.get("contain_to_workspace")
                or not scaffold.get("strict_mcp_config") or scaffold.get("setting_sources") != []
                or scaffold.get("permission_mode") != "dontAsk"):
            raise ValueError("Claude review needs explicit tools, contain_to_workspace, strict_mcp_config, "
                             "empty setting_sources and permission_mode dontAsk")
    if kind == "codex":
        if (scaffold.get("relayed_builtin_tools") is None or scaffold.get("sandbox_mode") != "read-only"
                or scaffold.get("web_search") or scaffold.get("network_access")
                or not {"shell_tool", "unified_exec"} <= set(scaffold.get("disabled_features", []))):
            raise ValueError("Codex review needs relayed_builtin_tools, a read-only sandbox, "
                             "shell_tool and unified_exec disabled, and web_search and network_access off")
    unavailable = set(stage.operations) - (set(get_all_tool_names()) - SKILL_TOOL_NAMES)
    if scaffold["scaffold_type"] != "ape_agent" and not scaffold.get("use_native_tools", False):
        delivery = {"file_read": "Read", "content_search": "Grep", "file_search": "Glob"}
        builtins = set(scaffold.get("tools") or []) - set(scaffold.get("disallowed_tools") or [])
        unavailable.update(set(stage.operations) & set(BashExecuteToolsProvider.SUPPORTED_TOOLS))
        unavailable.update(op for op in stage.operations if op in FileSystemToolsProvider.SUPPORTED_TOOLS
                           and delivery.get(op) not in builtins)
    if unavailable:
        raise ValueError(f"Unavailable required operations: {sorted(unavailable)}")
    task["enabled_tools"] = stage.operations
    files = resolve_input_files(task)
    task.update(pin_overrides(files))
    budget = study.budget
    dataset = {"design": stage.algorithm, "routing_mode": "solo", "solo_context_tools": stage.context_tools,
               "release": str(spec.release), "pr_numbers": spec.pr_numbers, "require_reviewed_workspaces": True,
               "solo_cost_cap": budget.solo_cost_cap, "solo_token_cap": budget.solo_token_cap,
               "run_total_cost_cap": budget.run_total_cost_cap or budget.solo_cost_cap * len(episodes),
               "run_total_token_cap": budget.run_total_token_cap or budget.solo_token_cap * len(episodes)}
    if history:
        dataset["solo_precedent_index"] = str(history.index(prepare=False))
    if stage.brief is not None:
        dataset["whole_pr_brief"] = stage.brief
    if stage.algorithm != "whole_pr":
        dataset["modification_inventory"] = str(spec.inventory)
    raw = {**scaffold, **model_settings, "execution": {**execution, "max_turns": budget.max_turns},
           "task_config": task, "dataset": dataset}
    ds, config, overrides = runner.load_run(raw)
    runner.assert_the_model_keeps_its_reasoning(config)
    runner._report_budget(ds, {}, len(episodes), logger, enforce=True, scaffold=config)
    cls = DESIGNS[stage.algorithm]
    effective_task = cls.task_config_class.model_validate(overrides)
    if stage.algorithm == "whole_pr" and "precedent_search" in stage.context_tools and not history:
        raise ValueError("whole_pr precedent_search requires a named, pinned history collection")
    if cls.reads_stage != bool(stage.reads):
        raise ValueError(f"{stage.algorithm}: reads must bind exactly the required upstream ledger")
    if stage.algorithm == "whole_pr":
        brief = stage.brief or DEFAULT_BRIEF
    else:
        brief = solo_system_prompt(effective_task)
    return {"brief": brief, "history": history.model_dump(mode="json") if history else None,
            "run_config": raw, "model": runner._plan_model_name(config), "reads": stage.reads,
            "effective_scaffold": config.model_dump(mode="json"),
            "effective_task": effective_task.model_dump(mode="json"),
            "task_type": cls.task_type, "design_version": cls.design_version}


def preview_inputs(stage, episodes, cutoffs, releases):
    """Resolve the inputs through the generation task. A critic's ledger arrives at execution."""
    ds, scaffold, _ = runner.load_run(stage["run_config"])
    graphs = []
    if ds.design != "whole_pr":
        key = (ds.release, ds.modification_inventory)
        if key not in releases:
            releases[key] = runner.load_release(ds)
        release = releases[key]
        _, selected = runner.select_units_and_episodes(ds, release)
        if {ep.episode_id for ep in selected} != {ep.episode_id for ep in episodes}:
            raise ValueError("The frozen case selection differs from the episodes the runner would dispatch")
        graphs = release["graphs"]
    ledgers = {ep.episode_id: {} for ep in episodes} if stage["reads"] else None
    tasks = runner.review_task_data(episodes, ds, cutoffs, Path("context_trace.jsonl"), graphs, ledgers)
    by_id = {ep.episode_id: ep for ep in episodes}

    async def render():
        records = {}
        for payload in tasks:
            ep = by_id[payload["episode_id"]]
            _, _, record = await inspect_review(payload, ds, scaffold, ep)
            native = {"Read": "file_read", "Grep": "content_search", "Glob": "file_search"}
            provided = set(record["mcp"]) | {native.get(t, t) for t in record["builtins"]}
            missing = set(stage["effective_task"]["enabled_tools"] + ds.solo_context_tools) - provided
            if missing:
                raise ValueError(f"Missing required operations in the dispatched grant: {sorted(missing)}")
            records[ep.episode_id] = {k: record[k] for k in (
                "message_sha256", "mcp", "mcp_schema_sha256", "builtins", "cutoff", "patch_sha256")}
            if stage["reads"]:
                del records[ep.episode_id]["message_sha256"]
                records[ep.episode_id]["ledger_from"] = stage["reads"]
        return records

    return asyncio.run(render())


def check_control(stage, path):
    """A historical control supplies evidence about the intended contract, never generation inputs."""
    from src.mathlib_review.review.inputs import INPUT_FILE_FIELDS

    old_ds, historical, old = runner.load_run(path)
    old = DESIGNS[old_ds.design].task_config_class.model_validate(old).model_dump(mode="json")
    actual = stage["effective_task"]
    differences = []
    for key in sorted((old.keys() | actual.keys()) - set(INPUT_FILE_FIELDS.values()) - {"context_file"}):
        left, right = old.get(key), actual.get(key)
        if key == "system_prompt_file" and left and right:
            left, right = Path(left).read_bytes(), Path(right).read_bytes()
        if left != right:
            differences.append(f"{key}: {old.get(key)!r} in control, {actual.get(key)!r} in study")
    # Cases can supply different context material; the route, operations and instructions stay fixed.
    old_settings = historical.model_dump(mode="json", exclude={"task_config_overrides"})
    current = stage["effective_scaffold"]
    for key, value in old_settings.items():
        if value != current.get(key):
            differences.append(f"{key} differs")
    ds = stage["run_config"]["dataset"]
    for key in ("design", "whole_pr_brief", "solo_context_tools", "solo_cost_cap", "solo_token_cap"):
        if getattr(old_ds, key) != ds.get(key):
            differences.append(f"{key}: {getattr(old_ds, key)!r} in control, {ds.get(key)!r} in study")
    if differences:
        raise ValueError(f"Control {path} disagrees: " + "; ".join(differences))


def plan_study(path, condition, logger):
    study_raw = load_yaml(path)
    study = Study.model_validate(study_raw)
    if study.controls.keys() - set(study.cases) or "reviewer" in study.stage_models:
        raise ValueError("controls must name a selected case set; the reviewer is bound by the model axis")
    root = path.parent.parent

    @cache
    def definition(folder, name):
        source = root / folder / (name + ".yaml")
        raw = load_yaml(source)
        return raw, {"path": str(source), "sha256": digest(raw)}

    @cache
    def case_set(name):
        raw, source = definition("probe_sets", name)
        spec = probes.ProbeSet.model_validate(raw)
        rows, selected = cases_of(spec)
        return spec, rows, selected, runner.cutoffs_by_episode(selected), source

    @cache
    def history_source(path):
        reviewer = Reviewer.model_validate(load_yaml(path))
        if not reviewer.history:
            raise ValueError(f"{path}: no pinned history collection")
        return reviewer.history

    rendered = {}
    releases = {}
    cells = []
    for choices in selections(study, condition):
        try:
            design, source = definition("designs/composed", choices["design"])
            scaffold, scaffold_source = definition("scaffolds", choices["scaffold"])
            cases, episodes, selected, cutoffs, cases_source = case_set(choices["cases"])
            sources = {"design": source, "scaffold": scaffold_source, "cases": cases_source}
            stages = {}
            design = Design.model_validate(design)
            for role in design.generation_order():
                stage = design.stages[role]
                model_name = choices["model"] if role == "reviewer" else study.stage_models.get(role)
                if not model_name or not re.fullmatch(r"[\w.-]+", model_name):
                    raise ValueError(f"stage {role} needs a model binding and any upstream stage before it")
                if stage.reads:
                    producer = DESIGNS[design.stages[stage.reads].algorithm]
                    if "ledger" not in producer.task_result_class.model_fields:
                        raise ValueError(f"{role} reads {stage.reads}, whose algorithm produces no ledger")
                model, sources[role + "_model"] = definition("models", model_name)
                history = history_source(stage.history_from) if stage.history_from else None
                if history:
                    if "precedent_search" not in stage.context_tools or stage.algorithm != "whole_pr":
                        raise ValueError("history_from requires a whole_pr reviewer with precedent_search")
                    if not set(cases.pr_numbers) <= set(history.excluded) or any(
                        RetrievalGate(as_of=history.before).cutoff_epoch > RetrievalGate(as_of=c).cutoff_epoch
                        for c in cutoffs.values()
                    ):
                        raise ValueError("history must exclude each reviewed PR and precede every reviewed head")
                    sources[role + "_history"] = {"path": str(stage.history_from), "sha256": digest(history.model_dump(mode="json"))}
                resolved = compose_stage(stage, model, scaffold, cases, study, episodes, logger, history)
                # Model identity and sampling settings do not enter the task renderer.
                key = digest([stage.model_dump(mode="json"), scaffold, cases_source, cutoffs])
                if key not in rendered:
                    rendered[key] = preview_inputs(resolved, selected, cutoffs, releases)
                resolved["review_inputs"] = rendered[key]
                stages[role] = resolved
            if choices["cases"] in study.controls:
                check_control(stages["reviewer"], study.controls[choices["cases"]])
            cells.append({"choices": choices, "sources": sources, "episode_count": len(episodes),
                          "episodes": episodes, "samples": study.samples, "stages": stages})
        except (ValueError, KeyError, OSError, ConfigurationError, runner.BudgetTooSmall) as error:
            raise ValueError(f"{choices}: {error}") from error
    return {"study": str(path), "study_sha256": digest(study_raw), "conditions": cells}


def run_composition(args, logger):
    path = Path(args.study)
    if not path.suffix:
        path = Path("configs/studies") / (args.study + ".yaml")
    if (args.case or args.score or args.of_run or args.overrides
            or getattr(args, "redo", False) or getattr(args, "cost_model", None)):
        raise ValueError("Study settings belong to their source definitions; use --condition to select a combination")
    plan = plan_study(path, args.condition, logger)
    if not getattr(args, "execute", False):
        print(json.dumps(plan, indent=2))
        return 0
    if not args.run_name:
        raise ValueError("Supply --run-name to identify this execution of the study")
    return execute_plan(plan, args.run_name, args.resume, logger)


def run_whole_pr(cell, stage, sample, identity, resume, logger):
    for episode in cell["episodes"]:
        ds, scaffold, task = runner.load_run(stage["run_config"])
        ds.run_name = "r" + digest([*identity, episode["episode_id"]])[:24]
        out = submissions.review_directory(ds.run_name)
        request = ReviewRequest(cell["choices"]["design"], None, episode["pr_number"],
                                episode["reviewed_head_sha"], out, cell, sample)
        with claim_execution(out):
            started = (out / "generation.json").is_file()
            if started and not resume:
                raise ValueError(f"{out}: generation already exists")
            asyncio.run(runner.review_episode(ds, scaffold, task, logger, request, resume=started))
            submissions.saved_reviews(out, recover=True)
        print(f"Saved submitted review: {out}")


def run_stages(seal, cell, alias, sample, resume, logger):
    names = {}
    for role, stage in cell["stages"].items():
        identity = [alias, cell["choices"], sample, role]
        if stage["run_config"]["dataset"]["design"] == "whole_pr":
            run_whole_pr(cell, stage, sample, identity, resume, logger)
            continue
        ds, scaffold, task = runner.load_run(stage["run_config"])
        ds.run_name = names[role] = "r" + digest(identity)[:24]
        ds.stage_input_run = names.get(stage["reads"])
        out = runner.run_dir(ds.run_name)
        with claim_execution(out):
            write_once(out / "condition.json", pretty_json_bytes({
                "condition": cell, "stage": role, "sample": sample, "study_plan": str(seal)}))
            manifest = out / "run_manifest.json"
            if resume and manifest.is_file() and submissions.read(manifest)["completion_status"] == "complete":
                continue
            started = any(p.is_dir() for p in runner._scratch_dirs(ds.run_name, scaffold))
            asyncio.run(runner.run(ds, scaffold, task, logger, resume=resume and started,
                                   reviewed_episodes=cell["episodes"]))
            if not manifest.is_file() or submissions.read(manifest)["completion_status"] != "complete":
                raise ValueError(f"{out}: generation incomplete; inspect the run before resuming the study")
        print(f"Saved generation run: {out}")


def execute_plan(plan, alias, resume, logger):
    directory = Path(".ape/studies") / submissions.review_directory(alias).name
    with claim_execution(directory):
        seal = directory / "plan.json"
        if seal.exists() != resume:
            raise ValueError(f"{directory}: use --resume for an existing study run and a fresh name for a new one")
        if not resume:
            # Resolve ambient prerequisites for all requested cells before the first paid dispatch.
            # An interrupted study can recover already accepted tasks with generation unavailable.
            checked = set()
            for cell in plan["conditions"]:
                for stage in cell["stages"].values():
                    ds, scaffold, _ = runner.load_run(stage["run_config"])
                    runner.assert_ready(scaffold, logger)
                    key = (ds.release, tuple(ds.pr_numbers))
                    if key not in checked:
                        selected = runner.select_reviewed_episodes(ds.release, {
                            ep["pr_number"]: ep["reviewed_head_sha"] for ep in cell["episodes"]})
                        asyncio.run(runner.assert_reviewed_workspaces_prebuilt(
                            selected, required=ds.require_reviewed_workspaces, logger=logger))
                        asyncio.run(runner.assert_workspaces_prebuilt(
                            [{"target_workspace": {"commit_hash": ep.base_sha}} for ep in selected],
                            required=ds.require_prebuilt_workspaces))
                        checked.add(key)
        write_once(seal, pretty_json_bytes(plan))
        for cell in plan["conditions"]:
            for sample in range(1, cell["samples"] + 1):
                run_stages(seal, cell, alias, sample, resume, logger)
    return 0
