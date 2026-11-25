"""Archive exactly the accepted reviews, then blind and score independently of generation."""

import asyncio
import json
import re
from pathlib import Path

from ape.orchestration.models import Sample
from ape.orchestration.persistence import TaskStorage
from src.mathlib_review.analysis import matching, probes
from src.mathlib_review.io import jsonl_rows, pretty_json_bytes, sha256_bytes, sha256_file, write_once
from src.mathlib_review.paths import run_dir
from src.mathlib_review.run_state import claim_execution


def review_directory(alias):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", alias):
        raise ValueError("Use a run name containing letters, digits, dots, underscores or hyphens")
    return Path(".ape/reviews") / alias


def read(path):
    return json.loads(path.read_bytes())


def archive(path, target):
    payload = path.read_bytes()
    write_once(target, payload)
    return {"path": str(target), "sha256": sha256_bytes(payload)}


#: What an archive keeps of each accepted session: these from its attempt, its transcript
#: (`claude_code_conversation_*.jsonl`), and the task's result and sample record.
ATTEMPT_EVIDENCE = ("claude_code_session.json", "containment_audit.json")
TASK_EVIDENCE = ("task_result.json", "sample.json")
TRANSCRIPT_PREFIX = "claude_code_conversation_"


def precedent_calls(audit):
    return sum(t["by_tool"].get("mcp__core__precedent_search", 0) for t in audit["transcripts"])


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
    transcript, = attempt.glob(TRANSCRIPT_PREFIX + "*.jsonl")
    first = next(row for row in jsonl_rows(transcript) if row.get("type") == "user")
    normalized = first["message"]["content"].replace(init["cwd"], "{attempt_workspaces}")
    if sha256_bytes(normalized.encode()) != expected["message_sha256"]:
        raise ValueError(f"{attempt}: live first user message differs from the preflight")
    return transcript, precedent_calls(audit)


#: A named review's design and search index, by run, written before its reviewer is dispatched.
INPUTS_FILE = "inputs.json"


def record_inputs(out, name, inputs):
    """Record a named run's inputs before its reviewer is dispatched, beside its generation record.

    Kept apart from `generation.json`, so a record written before runs kept their inputs still
    matches byte for byte on resume. Such a run that already sealed its run plan keeps that plan as
    its record; one interrupted before sealing it gains this record now.
    """
    path = out / INPUTS_FILE
    sealed = (out / "generation.json").is_file() and (run_dir(name) / "run_plan.json").is_file()
    if sealed and not path.is_file():
        return
    write_once(path, pretty_json_bytes({name: inputs}))


def generation_inputs(out, name, run):
    """The design and search index one generation ran with.

    A named run records them in `inputs.json` beside its generation record; one recorded on the
    development branch between 968c285e and 86bb0f88 kept them inside that record. Study
    generations, and named ones from before the change, sealed them in the runner's `run_plan.json`.
    """
    if (out / INPUTS_FILE).is_file():
        return read(out / INPUTS_FILE)[name]
    if "inputs" in run:
        return run["inputs"]
    plan = read(run_dir(name) / "run_plan.json")
    if plan["run_name"] != name:
        raise ValueError(f"{name}: run plan belongs to a different reviewer")
    return {"design": plan["evaluation_settings"].get("design"),
            "context_index_sha256": plan.get("context_index_sha256", {})}


def matcher_findings(raw):
    # Keep the author's order and wording. The classifier's default severity is not a submitted finding.
    return [{"target": probes._solo_target(f), "claim": f["claim"], "requested_change": f["suggested_fix"]}
            for f in raw["submitted_findings"]]


def accepted_submission(sample, raw, directory):
    accepted = sample.successful_attempt
    if sample.sample_index != 0 or accepted is None or not raw or not raw["success"]:
        raise ValueError(f"{directory}: no accepted submission for this sample")
    if not isinstance(accepted.result, dict) or any(
            accepted.result.get(k) != raw.get(k)
            for k in ("pr_number", "episode_id", "submitted_findings", "review_message")):
        raise ValueError(f"{directory}: task result differs from the accepted attempt's submission")
    return accepted


def run_evidence_names(directory, out, run, *, named):
    """The trace when one exists, plus the run records written by this generation format."""
    names = {f for f in ("context_trace.jsonl", "run_plan.json") if (directory / f).is_file()}
    if not (out / INPUTS_FILE).is_file() and "inputs" not in run:
        names.add("run_plan.json")
    if not named:
        names.add("run_manifest.json")
    return names


async def capture(out, runs):
    sources, records = {}, []
    generation = read(out / "generation.json")
    named = "reviewer" in generation
    for arm, run in runs.items():
        name = run["run"]
        task_root = Path(run.get("tasks_dir", Path(".ape/runs") / name / "tasks"))
        manifest = run_dir(name) / "run_manifest.json"
        if not named and (not manifest.exists() or read(manifest)["completion_status"] != "complete"):
            raise ValueError(f"{name}: review generation is incomplete; resume the generation command")
        inputs = generation_inputs(out, name, run)
        if inputs["design"] != "whole_pr":
            raise ValueError(f"{name}: generated with design {inputs['design']!r}, not a whole-PR review")
        search = "history_sha256" in run or arm == "history"
        if search:
            index = inputs["context_index_sha256"]
            if (index.get("precedent_corpus"), index.get("precedent_manifest")) != (
                    generation["history_sha256"], generation["index_manifest_sha256"]):
                raise ValueError(f"{name}: the live search index differs from the generation plan")
        base = out / "submissions" / name
        findings = {}
        run_files = {f: archive(run_dir(name) / f, base / f)
                     for f in run_evidence_names(run_dir(name), out, run, named=named)}
        trace_file = run_dir(name) / "context_trace.jsonl"
        search_rows = [r for r in jsonl_rows(trace_file) if r["tool"] == "precedent_search"] if trace_file.exists() else []
        for task_dir in sorted(p for p in task_root.iterdir() if p.is_dir()):
            storage = TaskStorage(task_dir, task_dir.name)
            samples = await storage.load_all_samples()
            raw = await storage.load_task_result()
            if set(samples) != {0}:
                raise ValueError(f"{task_dir}: no accepted submission for this sample")
            accepted = accepted_submission(samples[0], raw, task_dir)
            pr = str(raw["pr_number"])
            expected = run["episodes"][pr]
            if pr in findings or raw["episode_id"] != expected["episode_id"]:
                raise ValueError(f"{task_dir}: duplicate or incorrect review episode")
            if (accepted.max_turns, accepted.token_limit, accepted.cost_limit) != (
                    expected["max_turns"], expected["token_cap"], expected["cost_cap"]):
                raise ValueError(f"{task_dir}: live review budget differs from the preflight")
            attempt = Path(accepted.path)
            transcript, calls = check_attempt(attempt, expected)
            traced = [r for r in search_rows if r.get("invocation_id") == raw.get("invocation_id")]
            if len(samples[0].attempts) == 1 and calls != len(traced):
                raise ValueError(f"{attempt}: search calls in the transcript disagree with the run trace")
            if traced and (not search or any(
                    r.get("corpus_sha256") != run.get("history_sha256") or r.get("as_of") != expected["cutoff"]
                    for r in traced)):
                raise ValueError(f"{attempt}: search used an unverified corpus or cutoff")
            dest = base / pr
            files = {f: archive(attempt / f, dest / f) for f in (*ATTEMPT_EVIDENCE, transcript.name)}
            task_files = dict(zip(TASK_EVIDENCE, (task_dir / "task_result.json", task_dir / "samples/0/sample.json")))
            files.update({name: archive(path, dest / name) for name, path in task_files.items()})
            findings[pr] = matcher_findings(raw)
            records.append({"strategy": arm, "pr": pr, "run": name, "episode_id": raw["episode_id"],
                            "findings": len(findings[pr]), "search_calls": calls, "attempts": len(samples[0].attempts),
                            "files": files, "run_files": run_files})
        if set(findings) != set(run["episodes"]):
            raise ValueError(f"{name}: missing expected PR submissions")
        path = base / "findings.json"
        write_once(path, pretty_json_bytes(findings))
        sources[arm] = {"kind": "findings_file", "path": str(path)}
    artifact = {"generation_sha256": sha256_file(out / "generation.json"), "records": records,
                **({"inputs_sha256": sha256_file(out / INPUTS_FILE)} if (out / INPUTS_FILE).is_file() else {}),
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
    seal = read(seal_path)
    if (set(seal) != set(map(str, prs)) or not set(prs) <= set(reference.pr_numbers)
            or any(sorted(labels.values()) != sorted(sources) for labels in seal.values())):
        raise ValueError("Reference population or saved blind labels differ from the requested subjects")
    plan = matching.plan_matching(
        reference, name=f"{name}_{out.name}_{key}",
        seal=seal, seal_path=seal_path,
        sources={k: probes.Source.model_validate(v) for k, v in sources.items()},
        out_dir=folder, version="2-task", question_policy=policy, replicates=2, harness_blind=True,
        reuse=True)
    return plan, folder


def check_archived_run(out, arm, run, artifact, *, named):
    """Check the matcher's source and its evidence against the same run and reviewed episodes."""
    base = out / "submissions" / run["run"]
    source = artifact["sources"][arm]
    path = base / "findings.json"
    if source["kind"] != "findings_file" or Path(source["path"]).resolve() != path.resolve():
        raise ValueError(f"{arm}: archived matcher input belongs to a different run")
    if sha256_file(path) != artifact["projection_sha256"][arm]:
        raise ValueError(f"{arm}: archived matcher input changed")

    records = [r for r in artifact["records"] if r["strategy"] == arm]
    covered = sorted(r["pr"] for r in records)
    if covered != sorted(run["episodes"]):
        raise ValueError(f"{out}: archive records for {arm} cover PRs {covered}, "
                         f"not the generated {sorted(run['episodes'])}")
    run_files = run_evidence_names(base, out, run, named=named)
    findings = {}
    for record in records:
        pr = record["pr"]
        episode = run["episodes"][pr]
        if record.get("run") != run["run"] or record.get("episode_id") != episode["episode_id"]:
            raise ValueError(f"{out}: archive record for {arm} PR {pr} belongs to a different run or episode")
        if sha256_file(Path(episode["message"])) != episode["message_sha256"]:
            raise ValueError(f"{out}: archived first message changed for {arm} PR {pr}")
        dest = base / pr
        files = record["files"]
        missing = [name for name in (*ATTEMPT_EVIDENCE, *TASK_EVIDENCE) if name not in files]
        transcripts = [name for name in files if Path(name).match(TRANSCRIPT_PREFIX + "*.jsonl")]
        if len(transcripts) != 1:
            missing.append(TRANSCRIPT_PREFIX + "*.jsonl")
        if missing:
            raise ValueError(f"{out}: the archive record for PR {pr} lacks {missing}")
        if set(record["run_files"]) != run_files:
            raise ValueError(f"{out}: archived run evidence for {arm} must list {sorted(run_files)}")
        for directory, kept_files in ((dest, files), (base, record["run_files"])):
            for name, kept in kept_files.items():
                expected_path = directory / name
                if Path(name).name != name or Path(kept["path"]).resolve() != expected_path.resolve():
                    raise ValueError(f"{out}: archived {name} belongs to a different run or episode")
                if sha256_file(expected_path) != kept["sha256"]:
                    what = "accepted task result" if name == "task_result.json" else f"archived {name}"
                    raise ValueError(f"{out}: {what} changed")
        raw = read(dest / "task_result.json")
        sample = Sample.model_validate_json((dest / "sample.json").read_bytes())
        accepted_submission(sample, raw, dest)
        if str(raw["pr_number"]) != pr or raw["episode_id"] != episode["episode_id"]:
            raise ValueError(f"{out}: accepted task result differs from the generated episode for {arm} PR {pr}")
        findings[pr] = matcher_findings(raw)
        if (record["findings"] != len(findings[pr])
                or record["attempts"] != len(sample.attempts)
                or record["search_calls"] != precedent_calls(read(dest / "containment_audit.json"))):
            raise ValueError(f"{out}: archive counts differ from the accepted evidence for {arm} PR {pr}")
    if read(path) != findings:
        raise ValueError(f"{arm}: archived matcher input differs from the accepted submissions")


def saved_reviews(out, *, recover=False):
    if not (out / "generation.json").is_file():
        raise ValueError(f"{out}: no saved generation. Run the reviewer before scoring its submission.")
    generation = read(out / "generation.json")
    if generation["fixture"]:
        raise ValueError("Synthetic wiring fixtures cannot be evaluated as pilot runs")
    path = out / "archive.json"
    if not path.is_file() and not recover:
        raise ValueError(f"{out}: submission not yet archived. Resume the review before scoring.")
    artifact = read(path) if path.is_file() else asyncio.run(capture(out, generation["runs"]))
    if artifact["generation_sha256"] != sha256_file(out / "generation.json"):
        raise ValueError("The archived reviews refer to another generation plan")
    if (out / INPUTS_FILE).exists() or "inputs_sha256" in artifact:
        if artifact.get("inputs_sha256") != sha256_file(out / INPUTS_FILE):
            raise ValueError(f"{out}: the recorded run inputs changed")
    arms = set(generation["runs"])
    if arms != set(artifact["sources"]) or arms != set(artifact["projection_sha256"]):
        raise ValueError(f"{out}: archived finding sources differ from the planned strategies")
    if any(record["strategy"] not in arms for record in artifact["records"]):
        raise ValueError(f"{out}: archived record belongs to an unplanned strategy")
    for arm, run in generation["runs"].items():
        check_archived_run(out, arm, run, artifact, named="reviewer" in generation)
    return generation, artifact


def compare(out, question_form, execute, *, reference, name, config, reading=None):
    generation, artifact = saved_reviews(out, recover=True)
    prs = sorted(map(int, generation["runs"]["solo"]["episodes"]))
    plan, folder = prepare_reading(out, artifact["sources"], prs, question_form,
                                   reference=reference, name=name, reading=reading)
    score_plan(plan, folder, config, execute)


def score_plan(plan, folder, config, execute, *, scaffold=None):
    print(f"{folder}: {plan.expected_cells} cells per reading, {plan.identity.replicates} readings")
    if execute:
        from ape.utils.logging import create_logger
        from src.mathlib_review.review.preflight import assert_credentials
        from src.mathlib_review.run_config import load_run

        if scaffold is None:
            _, scaffold, _ = load_run(config, matching.MatchDatasetConfig)
        assert_credentials(scaffold)
        run = "m" + plan.source_sha256[:20]
        rows = asyncio.run(matching.run_matching(plan, folder, scaffold, run, create_logger()))
        if len(rows) != len(plan.batches) * plan.identity.replicates:
            raise ValueError(f"{folder}: incomplete matcher results")
        print(json.dumps(matching.report_matching(folder, producers=["task-" + run]), indent=2))


SCORERS = {"round1-requests-v1": False, "round1-questions-v1": True}
REFERENCE = Path("configs/probe_sets/postcutoff_2026_07_08_v1.yaml")
MATCHER = Path("configs/match/ask_match_opus55_claude_sub.yaml")


def scoring_description(scorer):
    policy = "question form" if SCORERS[scorer] else "request only"
    return (f"{scorer}: ordered submitted findings against {REFERENCE}, "
            f"{policy} rubric, two blind readings via {MATCHER}")


def score_reviews(directories, scorer, *, execute):
    """Read independently accepted submissions on the same reviewed head."""
    from src.mathlib_review.io import canonical_json_bytes

    if len(directories) != len(set(directories)):
        raise ValueError("Each requested submission must be distinct")
    reference = probes.load_probe_set(REFERENCE)
    reference_heads = {(r["pr_number"], r["episode_id"], r["patch_sha256"], r["reviewed_head_sha"])
                       for r in jsonl_rows(reference.release / "input/episodes.jsonl")}
    sources = {}
    case = None
    receipts = {}
    subjects = {}
    if not directories:
        raise ValueError("Supply at least one saved run to score")
    for directory in sorted(directories):
        generation, archive_record = saved_reviews(directory)
        reviewer = generation.get("reviewer")
        if reviewer is None or set(generation["runs"]) != {reviewer}:
            raise ValueError(f"{directory}: expected one named reviewer")
        ((pr, episode),) = generation["runs"][reviewer]["episodes"].items()
        current = (int(pr), episode["episode_id"], episode["patch_sha256"], episode["reviewed_head_sha"])
        if current not in reference_heads or (case is not None and current != case):
            raise ValueError("Submissions and reference must cover the same reviewed revision")
        case = current
        sources[directory.name] = archive_record["sources"][reviewer]
        receipt = sha256_file(directory / "archive.json")
        receipts[directory.name] = receipt
        subjects[directory.name] = {
            "reviewer": reviewer, "pr": current[0], "head": current[3], "archive_sha256": receipt,
            "profile_sha256": generation["profile_sha256"], "model": episode["model"], "effort": episode["effort"],
            "history_sha256": generation.get("history_sha256"),
        }
    out = Path(".ape/review-comparisons") / sha256_bytes(canonical_json_bytes(receipts))[:24]
    with claim_execution(out):
        write_once(out / "subjects.json", pretty_json_bytes(subjects))
        from src.mathlib_review.run_config import load_run
        _, scaffold, _ = load_run(MATCHER, matching.MatchDatasetConfig)
        asks = probes.ask_packet(read(reference.feedback_file), read(reference.asks_file)["asks"][str(case[0])])
        settings = {
            "name": scorer, "config": str(MATCHER), "executor": matching.executor_of(scaffold),
            "route_sha256": matching.route_sha256(scaffold), "max_turns": scaffold.execution.max_turns,
            "token_cap": scaffold.execution.sample_max_tokens, "cost_cap": scaffold.execution.sample_max_cost,
        }
        identity = sha256_bytes(canonical_json_bytes([asks, settings]))
        plan, folder = prepare_reading(out, sources, [case[0]], SCORERS[scorer],
                                       reference=reference, name="reviews", reading=f"{scorer}-{identity[:16]}")
        write_once(folder / "scorer.json", pretty_json_bytes(settings))
        print(scoring_description(scorer))
        packet, = plan.packets
        for label, found in packet.reviewers.items():
            alias = plan.seal[str(case[0])][label]
            subject = subjects[alias]
            print(f"{alias} ({subject['reviewer']}, {subject['model']}, {subject['effort']}), "
                  f"PR {case[0]}@{case[3][:8]}: {len(found)} findings, {len(packet.asks)} eligible requests")
    with claim_execution(folder):
        score_plan(plan, folder, MATCHER, execute, scaffold=scaffold)
    return 0
