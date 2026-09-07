"""Emit one builder input row per distinct v4 base commit."""

import argparse
import json
from pathlib import Path

from ape.utils.project import PROJECT_ROOT
from ape.utils import parse_cli_args

from src.mathlib_review.io import load_jsonl
from src.mathlib_review.opportunities.runner import load_run
from src.mathlib_review.release.run_contract import select_units
from src.mathlib_review.schema import RenderedPrompt, ReviewEpisodeInput, ReviewWorkUnit
from src.mathlib_review.review.task_adapter import build_candidate_task_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Prebuild distinct v4 base workspaces")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path,
                        default=PROJECT_ROOT / "data/pr_review_v4/base_commits.jsonl")
    parser.add_argument("--num-processes", type=int, default=2)
    args, rest = parser.parse_known_args()
    dataset, _scaffold, _overrides = load_run(args.config, parse_cli_args(rest))
    release = dataset.release
    units = load_jsonl(release / "derived/work_units.jsonl", ReviewWorkUnit)
    units = select_units(
        units, dataset.pr_numbers, dataset.work_unit_ids, dataset.work_unit_limit
    )
    episodes = load_jsonl(release / "input/episodes.jsonl", ReviewEpisodeInput)
    prompts = load_jsonl(release / "derived/rendered_prompts.jsonl", RenderedPrompt)
    episode_by_id = {item.episode_id: item for item in episodes}
    prompt_by_id = {item.work_unit_id: item for item in prompts}
    seen, rows = set(), []
    for unit in units:
        episode = episode_by_id[unit.episode_id]
        if episode.base_sha in seen:
            continue
        seen.add(episode.base_sha)
        data = build_candidate_task_data(unit, episode, prompt_by_id[unit.work_unit_id])
        rows.append(data.model_dump(mode="json"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    print(f"Wrote {len(rows)} distinct base commits to {args.out}")
    print("Build before running candidate fan-out:")
    print("  export PATH=/research/projects/proofedit/ya475/.elan/bin:$PATH")
    print(f"  ./ape/bin/python -m ape.toolkits.execute.lean.build --input_file {args.out} "
          f"--num_processes {args.num_processes}")


if __name__ == "__main__":
    main()
