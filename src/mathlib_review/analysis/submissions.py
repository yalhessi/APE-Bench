"""Archive exactly the accepted reviews, then blind and score independently of generation."""

import asyncio
import json
import re
from pathlib import Path

from ape.orchestration.persistence import TaskStorage
from src.mathlib_review.analysis import matching, probes
from src.mathlib_review.io import jsonl_rows, pretty_json_bytes, sha256_bytes, sha256_file, write_once
from src.mathlib_review.paths import run_dir


def read(path):
    return json.loads(path.read_bytes())


def archive(path, target):
    payload = path.read_bytes()
    write_once(target, payload)
    return {"path": str(target), "sha256": sha256_bytes(payload)}


def check_attempt(attempt, expected):
    session = read(attempt / "claude_code_session.json")
    init = session["init"]
    if (init["model"], init["claude_code_version"], session["effort"]) != (
            expected["model"], expected["cli_version"], expected["effort"]):
        raise ValueError(f"{attempt}: live model, CLI or effort differs from the plan")
    tools = sorted(expected["builtins"] + ["mcp__core__" + tool for tool in expected["mcp"]])
    if (init.get("permissionMode") != "dontAsk" or
            [(s["name"], s["status"]) for s in init.get("mcp_servers", [])] != [("core", "connected")]):
        raise ValueError(f"{attempt}: live SDK permissions or MCP server differ from the design")
    if init.get("memory_paths"):
        raise ValueError(f"{attempt}: SDK loaded additional instruction files")
    if sorted(init["tools"]) != tools:
        raise ValueError(f"{attempt}: live tools differ from the design: {init['tools']}")
    audit = read(attempt / "containment_audit.json")
    if not (audit["clean"] and audit["usable"]):
        raise ValueError(f"{attempt}: inspect the containment audit before comparing this review")
    transcript, = attempt.glob("claude_code_conversation_*.jsonl")
    first = next(row for row in jsonl_rows(transcript) if row.get("type") == "user")
    normalized = first["message"]["content"].replace(init["cwd"], "{attempt_workspaces}")
    if sha256_bytes(normalized.encode()) != expected["message_sha256"]:
        raise ValueError(f"{attempt}: live first user message differs from the preflight")
    calls = sum(t["by_tool"].get("mcp__core__precedent_search", 0) for t in audit["transcripts"])
    return transcript, calls


async def capture(out, runs):
    sources, records = {}, []
    generation = read(out / "generation.json")
    for arm, run in runs.items():
        name = run["run"]
        task_root = Path(".ape/runs") / name / "tasks"
        manifest = run_dir(name) / "run_manifest.json"
        if not manifest.exists() or read(manifest)["completion_status"] != "complete":
            raise ValueError(f"{name}: review generation is incomplete; resume the generation command")
        plan = read(run_dir(name) / "run_plan.json")
        if plan["run_name"] != name or plan["evaluation_settings"].get("design") != "whole_pr":
            raise ValueError(f"{name}: run plan belongs to a different reviewer")
        if arm == "history":
            index = plan["context_index_sha256"]
            if (index.get("precedent_corpus"), index.get("precedent_manifest")) != (
                    generation["history_sha256"], generation["index_manifest_sha256"]):
                raise ValueError(f"{name}: the live search index differs from the generation plan")
        base = out / "submissions" / name
        findings = {}
        run_files = {f: archive(run_dir(name) / f, base / f) for f in
                     ("run_manifest.json", "run_plan.json", "context_trace.jsonl")
                     if (run_dir(name) / f).exists()}
        trace_file = run_dir(name) / "context_trace.jsonl"
        search_rows = [r for r in jsonl_rows(trace_file) if r["tool"] == "precedent_search"] if trace_file.exists() else []
        for task_dir in sorted(p for p in task_root.iterdir() if p.is_dir()):
            storage = TaskStorage(task_dir, task_dir.name)
            samples = await storage.load_all_samples()
            raw = await storage.load_task_result()
            if set(samples) != {0} or samples[0].successful_attempt is None or not raw or not raw["success"]:
                raise ValueError(f"{task_dir}: no accepted submission for this sample")
            pr = str(raw["pr_number"])
            expected = run["episodes"][pr]
            if pr in findings or raw["episode_id"] != expected["episode_id"]:
                raise ValueError(f"{task_dir}: duplicate or incorrect review episode")
            accepted = samples[0].successful_attempt
            if not isinstance(accepted.result, dict) or any(
                    accepted.result.get(k) != raw.get(k)
                    for k in ("episode_id", "submitted_findings", "review_message")):
                raise ValueError(f"{task_dir}: task result differs from the accepted attempt's submission")
            if (accepted.max_turns, accepted.token_limit, accepted.cost_limit) != (
                    expected["max_turns"], expected["token_cap"], expected["cost_cap"]):
                raise ValueError(f"{task_dir}: live review budget differs from the preflight")
            attempt = Path(accepted.path)
            transcript, calls = check_attempt(attempt, expected)
            traced = [r for r in search_rows if r.get("invocation_id") == raw.get("invocation_id")]
            if len(samples[0].attempts) == 1 and calls != len(traced):
                raise ValueError(f"{attempt}: search calls in the transcript disagree with the run trace")
            if traced and (arm != "history" or any(
                    r.get("corpus_sha256") != run.get("history_sha256") or r.get("as_of") != expected["cutoff"]
                    for r in traced)):
                raise ValueError(f"{attempt}: search used an unverified corpus or cutoff")
            dest = base / pr
            files = {f: archive(attempt / f, dest / f) for f in
                     ("claude_code_session.json", "containment_audit.json", transcript.name)}
            files["task_result.json"] = archive(task_dir / "task_result.json", dest / "task_result.json")
            files["sample.json"] = archive(task_dir / "samples/0/sample.json", dest / "sample.json")
            # The accepted list is ordered. The classifier's default severity is not an author's finding.
            findings[pr] = [{"target": probes._solo_target(f), "claim": f["claim"],
                             "requested_change": f["suggested_fix"]} for f in raw["submitted_findings"]]
            records.append({"strategy": arm, "pr": pr, "run": name, "episode_id": raw["episode_id"],
                            "findings": len(findings[pr]), "search_calls": calls, "attempts": len(samples[0].attempts),
                            "files": files, "run_files": run_files})
        if set(findings) != set(run["episodes"]):
            raise ValueError(f"{name}: missing expected PR submissions")
        path = base / "findings.json"
        write_once(path, pretty_json_bytes(findings))
        sources[arm] = {"kind": "findings_file", "path": str(path)}
    artifact = {"generation_sha256": sha256_file(out / "generation.json"), "records": records,
                "sources": sources, "projection_sha256": {
                    arm: sha256_file(Path(src["path"])) for arm, src in sources.items()}}
    write_once(out / "archive.json", pretty_json_bytes(artifact))
    return artifact


def prepare_reading(out, sources, prs, question_form, *, reference, name, reading=None):
    # Two rubrics on the same blind order and same source bytes can be read side by side.
    seal_path = out / "seal.json"
    if not seal_path.exists():
        write_once(seal_path, pretty_json_bytes(probes.seal_labels(prs, list(sources))))
    policy = "questions" if question_form else "request_only"
    if reading is not None and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", reading):
        raise ValueError("Use a reading name containing only letters, digits, underscores and hyphens")
    digest = matching.rubric_sha256(matching.V2_TASK, policy)
    key = f"{reading or policy}-{digest[:12]}"
    folder = out / "readings" / key
    if (folder / matching.PLAN_FILE).exists():
        plan = matching.load_plan(folder)
        if plan.identity.rubric_sha256 != digest or plan.identity.seal_sha256 != sha256_file(seal_path):
            raise ValueError(f"{folder}: saved reading belongs to another rubric or seal")
    else:
        plan = matching.plan_matching(
            reference, name=f"{name}_{out.name}_{key}",
            seal=read(seal_path), seal_path=seal_path,
            sources={k: probes.Source.model_validate(v) for k, v in sources.items()},
            out_dir=folder, version="2-task", question_policy=policy, replicates=2, harness_blind=True)
    return plan, folder


def compare(out, question_form, execute, *, reference, name, config, reading=None):
    if not (out / "generation.json").is_file():
        raise ValueError(f"{out}: no saved generation. Generate this sample with study run --execute first.")
    generation = read(out / "generation.json")
    if generation["fixture"]:
        raise ValueError("Synthetic wiring fixtures cannot be evaluated as pilot runs")
    path = out / "archive.json"
    artifact = read(path) if path.is_file() else asyncio.run(capture(out, generation["runs"]))
    if artifact["generation_sha256"] != sha256_file(out / "generation.json"):
        raise ValueError("The archived reviews refer to another generation plan")
    arms = set(generation["runs"])
    if arms != set(artifact["sources"]) or arms != set(artifact["projection_sha256"]):
        raise ValueError(f"{out}: archived finding sources differ from the planned strategies")
    for arm, digest in artifact["projection_sha256"].items():
        if sha256_file(Path(artifact["sources"][arm]["path"])) != digest:
            raise ValueError(f"{arm}: archived matcher input changed")
    prs = sorted(int(pr) for pr in generation["runs"]["solo"]["episodes"])
    plan, folder = prepare_reading(out, artifact["sources"], prs, question_form,
                                   reference=reference, name=name, reading=reading)
    print(f"{folder}: {plan.expected_cells} cells per reading, {plan.identity.replicates} readings")
    if execute:
        from ape.utils.logging import create_logger
        from src.mathlib_review.review.preflight import assert_credentials
        from src.mathlib_review.run_config import load_run

        _, scaffold, _ = load_run(config, matching.MatchDatasetConfig)
        assert_credentials(scaffold)
        run = "m" + plan.source_sha256[:20]
        rows = asyncio.run(matching.run_matching(plan, folder, scaffold, run, create_logger()))
        if len(rows) != len(plan.batches) * plan.identity.replicates:
            raise ValueError(f"{folder}: incomplete matcher results")
        print(json.dumps(matching.report_matching(folder, producers=["task-" + run]), indent=2))
