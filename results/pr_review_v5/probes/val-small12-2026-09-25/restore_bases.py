"""Restore the built base snapshots of the small12 PRs into workspaces/<sha>, which the reviewed
build requires and the prebuild planner does not check (2026-09-25: 0 of 11 built, every one
"base workspace ... is not built ... build the base commit first" while its snapshot existed)."""
import asyncio, sys
from pathlib import Path
from ape.toolkits.execute.lean.config import LeanVerifyToolConfig
from ape.toolkits.execute.lean.core.restore_manager import RestoreManager
from ape.utils.logging import create_logger
from src.mathlib_review.io import load_jsonl
from src.mathlib_review.schema import ReviewEpisodeInput

PRS = [int(p) for p in sys.argv[1].split(",")]
episodes = load_jsonl(Path("inputs/pr_review_v4/releases/val-2025-06-2026-03-v1/input/episodes.jsonl"), ReviewEpisodeInput)
shas = sorted({e.base_sha for e in episodes if e.pr_number in PRS})
cfg = LeanVerifyToolConfig(); _, url = cfg.resolve_repo(None)
manager = RestoreManager(cfg, create_logger(to_console=False), url)
failed = []
for sha in shas:
    if asyncio.run(manager._requires_build_first(sha)):
        print("NOT BUILT", sha); failed.append(sha); continue
    for attempt in (1, 2):
        try:
            asyncio.run(manager.get_workspace(sha)); print("restored", sha); break
        except Exception as exc:  # noqa: BLE001
            print(f"attempt {attempt} failed {sha}: {type(exc).__name__}: {str(exc)[:120]}")
    else:
        failed.append(sha)
print(f"{len(shas) - len(failed)} of {len(shas)} restored"); sys.exit(1 if failed else 0)
