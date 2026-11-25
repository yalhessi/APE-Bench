"""Inspect #42184's four proposed reviewer inputs using the local inputs in reproduce-review-reading.md.

From the topic worktree with its prepared JSONLs and saved November 24 ordinary attempt:
    PYTHONPATH="$PWD/src:$PWD" ape/bin/python -B results/pr_review_v5/probes/convention-scope-2026-11-24/inspect_four.py

Use the saved agenda for episode membership and the saved workspace handles for prompt rendering.
The named-path render changes only the run directory component of the recorded attempt's path.
Compare the APE first message, MCP descriptions and input schemas offline. SDK-built-in tools,
reminders, responses and tool execution can be observed only in a real session.
"""

import asyncio
import json
import logging
from pathlib import Path

from src.mathlib_review.review.inputs import first_message, mcp_signatures
from src.mathlib_review.analysis import probes
from src.mathlib_review.io import jsonl_rows
from src.mathlib_review.review import runner
from src.mathlib_review.schema.review import ReviewAgenda


PROBE = Path(__file__).resolve().parent
WORK = Path(".ape/review-reading-20261125")
CONFIG = Path("configs/pr_review_v5_probe_2026_07_08_v1_opus55_G_claude_sub.yaml")
ARCHIVE = PROBE.parent / "conventions-ceiling-2026-10-04"
BOOK = PROBE.parents[1] / "adjudications/conventions-census-v1/reader_A/codebook.json"
LOGGER = logging.getLogger("inspect_four")


async def main():
    saved, = [r for r in json.loads((PROBE / "full_tool_reviews.json").read_text()) if r["arm"] == "ordinary"]
    run_dir = Path(saved["run"])
    messages = jsonl_rows(Path(saved["transcript"]))
    first = next(row for row in messages if row["type"] == "user")
    cwd = Path(first["cwd"])
    agenda = ReviewAgenda.model_validate_json((run_dir / "agenda.json").read_bytes())
    workspaces = json.loads((run_dir / "reviewed_workspaces.json").read_text())
    spec = probes.load_probe_set(Path("configs/probe_sets/postcutoff_2026_07_08_v1.yaml"))
    print(f"Reference SDK first message: {saved['transcript']}")
    print(f"Episode source: {spec.release}. Agenda and reviewed workspace: {run_dir}")

    baseline_tools = {}
    for arm, selection in [("solo", None), ("history", None), ("selected", "applicable"), ("exact", "exact")]:
        name = f"reading_42184_{arm}_r1"
        context = WORK / f"{arm if selection else 'solo'}.jsonl"
        rules = probes.load_conventions(ARCHIVE / f"briefs_{selection}.json", BOOK) if selection else None
        assert context.read_bytes() == probes.model_context(spec, [42184], rules).encode()
        grant = ["declaration_search", "precedent_search"] if arm == "history" else ["declaration_search"]
        dataset, config, _ = runner.load_run(CONFIG, {
            "dataset": {"pr_numbers": [42184], "run_name": name, "solo_token_cap": 600000,
                        "solo_context_tools": grant},
            "task_config": {"context_file": str(context)}, "execution": {"max_concurrency": 1},
        })
        runner.pin_input_files(config)
        release = runner.load_release(dataset)
        _, episodes = runner.select_units_and_episodes(dataset, release)
        cutoffs = runner.cutoffs_by_episode(episodes)
        data, = runner._solo_task_data(agenda, episodes, dataset, cutoffs,
                                       runner.run_dir(name) / "context_trace.jsonl", release["graphs"])
        task = runner.create_task_from_data(data, config, task_config_overrides=config.task_config_overrides)
        target = Path(workspaces[task.data.episode_id])
        assert target.is_dir() and target == (cwd / "target").resolve()
        fixed = await first_message(task, cwd, target)
        signatures = await mcp_signatures(task)
        base_text = first["message"]["content"]
        sections = json.loads(context.read_text())["sections"]
        tail = "" if not selection else f"\n## {sections[1]['title']}\n\n{sections[1]['text'].rstrip()}\n"
        assert fixed == base_text + tail
        if arm == "solo":
            baseline_tools = signatures
            print(f"{task.data.episode_id}, cutoff {task.data.retrieval_cutoff}")
            print(f"Common MCP tools: {', '.join(sorted(baseline_tools))}")
            print(f"Solo first message matches saved text byte for byte ({len(fixed)} characters).")
        extra = {"precedent_search"} if arm == "history" else set()
        assert signatures.keys() == baseline_tools.keys() | extra
        assert all(signatures[key] == signature for key, signature in baseline_tools.items())
        named_cwd = Path(str(cwd).replace(run_dir.name, name))
        named = await first_message(task, named_cwd, target)
        assert named != fixed and named == fixed.replace(str(cwd), str(named_cwd))
        print(f"{arm}: {len(rules[42184]) if rules else 0} conventions, +{len(tail)} characters,"
              f" extra MCP {sorted(extra)}, path exposes {name!r} {named.count(name)} times.")


if __name__ == "__main__":
    asyncio.run(main())
