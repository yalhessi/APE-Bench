"""Inspect, generate and re-score the familiar four-strategy pilot. See pilot.md."""

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

from ape.toolkits.execute.lean.core.build_manager import reviewed_workspace_key
from src.mathlib_review.io import (
    canonical_json_bytes, jsonl_bytes, pretty_json_bytes, sha256_bytes, sha256_file, write_once,
)
from src.mathlib_review.review import runner
from inspect_four import first_message, mcp_signatures

CONFIG = Path("configs/designs/whole_pr_familiar.yaml")
ROOT = Path(".ape/four-review-pilot")
HISTORY = ROOT / "history"
CONVENTIONS = ROOT / "conventions"
CLI = [sys.executable, "-m", "src.mathlib_review.review.cli"]
ARMS = ("solo", "history", "automatic", "exact")
HEADS = {41930: "ec56eae52c28b70ec6cc92f1a295973c193353a0",
         42184: "c5474cb4a68a515228b49225b38a2507264f91f7"}
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


def cli_run(name, overrides, extra=()):
    args = CLI + ["run", "--config", str(CONFIG), "--run-name", name]
    for section, fields in overrides.items():
        for key, value in fields.items():
            args.extend(["--set", f"{section}.{key}={json.dumps(value)}"])
    subprocess.run([*args, *extra], check=True)


async def prepare(out, sample, fixture):
    base, _, _ = runner.load_run(CONFIG)
    release = runner.load_release(base)
    units, episodes = runner.select_units_and_episodes(base, release)
    if {e.pr_number: e.reviewed_head_sha for e in episodes} != HEADS or len(episodes) != len(HEADS):
        raise ValueError("The release does not match the two pinned first-round heads")
    await runner.assert_reviewed_workspaces_prebuilt(episodes, required=True)
    if fixture:
        # Both selectors receive identical selections here, including an empty one.
        rules = {"C1": "Demonstration sentence for the local rendering check."}
        assignments = {arm: {"41930": [], "42184": ["C1"]} for arm in ("automatic", "exact")}
    else:
        from pilot.conventions import load_verified
        products = load_verified(CONVENTIONS, HISTORY / "excerpts.jsonl")
        rules = {r["id"]: r["principle"] for r in products["catalogue"]}
        assignments = {arm: products[arm]["prs"] for arm in ("automatic", "exact")}

    # Run and context filenames are opaque even in the first model-facing message.
    manifest = {"sample": sample, "fixture": fixture, "runs": {},
                "history_sha256": sha256_file(HISTORY / "excerpts.jsonl")}
    index_path = HISTORY / "index/manifest.json"
    if json.loads(index_path.read_bytes())["corpus_sha256"] != manifest["history_sha256"]:
        raise ValueError("Direct search and catalogue construction have different excerpt sources")
    manifest["index_manifest_sha256"] = sha256_file(index_path)
    if not fixture:
        manifest["convention_files"] = {f: sha256_file(CONVENTIONS / f)
                                        for f in ("catalogue.json", "automatic.json", "exact.json")}
    agenda, _ = runner.build_agenda(
        run_name="local-render", routing_mode=base.routing_mode, release=base.release,
        modification_inventory=base.modification_inventory, units=units, episodes=episodes,
        graphs=release["graphs"], release_prompts=release["release_prompts"],
        modifications=release["modifications"], pr_numbers=sorted(HEADS),
        generalist_floor=base.generalist_floor, arm_ids=base.arm_ids)
    cutoffs = runner.cutoffs_by_episode(episodes)
    base_messages, common_signatures = {}, None
    commands = []
    for arm in ARMS:
        identity = ["familiar-four-v1", sample, arm, fixture]
        name = "r" + sha256_bytes(canonical_json_bytes(identity))[:20]
        overrides = {"dataset": {}}
        expected_tools = COMMON_TOOLS.copy()
        if arm == "history":
            expected_tools.add("precedent_search")
            overrides["dataset"].update(solo_context_tools=["declaration_search", "precedent_search"],
                                        solo_precedent_index=str(HISTORY / "index"))
        contexts = {}
        if arm in assignments:
            rows = context_rows(episodes, rules, assignments[arm])
            path = out / "inputs" / (name + ".jsonl")
            write_once(path, jsonl_bytes(rows))
            overrides["task_config"] = {"context_file": str(path)}
            contexts = {row["pr_number"]: row["sections"] for row in rows}
        ds, scaffold, _ = runner.load_run(CONFIG, overrides)
        ds.run_name = name
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
        if set(record["episodes"]) != {str(pr) for pr in HEADS}:
            raise ValueError(f"{arm}: incomplete episode coverage")
        manifest["runs"][arm] = record
        if arm == "history":
            record["history_sha256"] = manifest["history_sha256"]
        commands.append((name, overrides))
    write_once(out / "generation.json", pretty_json_bytes(manifest))
    return commands


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("check", help="local rendering fixture on both real PRs")
    gen = sub.add_parser("generate", help="prepare all four arms using verified catalogue and selections")
    gen.add_argument("--execute", action="store_true")
    comparison = sub.add_parser("compare", help="archive submissions and prepare a blind reading")
    comparison.add_argument("--reading", help="new evaluation name when changing the comparison (e.g. revised-asks)")
    comparison.add_argument("--question-form", action="store_true", help="apply the alternative question rubric")
    comparison.add_argument("--execute", action="store_true", help="run the semantic matcher")
    for p in (gen, comparison):
        p.add_argument("--sample", type=int, default=1)
    args = parser.parse_args()
    sample = getattr(args, "sample", 1)
    if sample < 1:
        parser.error("--sample must be positive")
    fixture = args.action == "check"
    out = ROOT / ("wiring" if fixture else f"sample-{sample}")
    if args.action == "compare":
        from pilot.measure import compare
        compare(out, args.question_form, args.execute, args.reading)
        return
    commands = asyncio.run(prepare(out, sample, fixture))
    print(f"{out}/generation.json: 4 strategies × 2 reviewed heads", flush=True)
    # Preflight every arm before the first provider call.
    for name, overrides in commands:
        cli_run(name, overrides)
    if fixture:
        from pilot.measure import replay_check
        replay_check(out / "archived-42184")
    if getattr(args, "execute", False):
        for name, overrides in commands:
            path = runner.run_dir(name)
            status = path / "run_manifest.json"
            if status.exists() and json.loads(status.read_text())["completion_status"] == "complete":
                continue
            started = path.exists() or (Path(".ape/runs") / name).exists()
            cli_run(name, overrides, ["--execute", "--resume"] if started else ["--execute"])


if __name__ == "__main__":
    main()
