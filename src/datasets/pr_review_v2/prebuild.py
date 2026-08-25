"""
Emit a builder-compatible JSONL of the distinct base commits a workspace run
needs, then hand it to the existing Lean workspace builder.

Workspace mode materializes each PR as (merge-base snapshot + δ₀), so the base
commit must be BUILT first (the scaffold log error: "State file does not exist,
need to build first"). Bases are shared across PRs, so there are far fewer than
one per PR. This writes one task-data line per distinct base (build_task_data
already pins target_workspace at the base) — the format the builder reads
(task_data.target_workspace.commit_hash) — and prints the build command.

Usage:
  python -m src.datasets.pr_review_v2.prebuild --config configs/pr_review_workspace_v2.yaml
  # then run the printed command, e.g.:
  python -m ape.toolkits.execute.lean.build --input_file data/pr_review_v2/base_commits.jsonl --num_processes 4
"""

import argparse
import json
from pathlib import Path

from ape.utils.project import PROJECT_ROOT

from .runner import load_records
from .runner_workspace import load_workspace_run
from .task_adapter import build_task_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-build base workspaces for a v2 workspace run")
    parser.add_argument("--config", type=Path, required=True, help="The workspace run YAML")
    parser.add_argument("--out", type=Path, default=PROJECT_ROOT / "data" / "pr_review_v2" / "base_commits.jsonl")
    parser.add_argument("--num_processes", type=int, default=4, help="For the printed build command")
    args = parser.parse_args()

    dataset, _scaffold_config, _overrides = load_workspace_run(args.config, None)
    records = load_records(dataset)

    seen, lines = set(), []
    for record in records:
        data = build_task_data(record)
        base = data.target_workspace.commit_hash
        if base in seen:
            continue
        seen.add(base)
        # One task-data line per distinct base; the builder reads target_workspace.commit_hash.
        lines.append(json.dumps(data.model_dump(mode="json"), ensure_ascii=False))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n")
    print(f"Wrote {len(lines)} distinct base commits (from {len(records)} PRs) to {args.out}")
    print("\nNow build them with the existing builder:")
    print(f"  python -m ape.toolkits.execute.lean.build --input_file {args.out} --num_processes {args.num_processes}")
    print("\nThen run the review:")
    print(f"  python -m src.datasets.pr_review_v2.runner_workspace --config {args.config}")


if __name__ == "__main__":
    main()
