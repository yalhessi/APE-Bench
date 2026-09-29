"""Restore the probe's built base snapshots into workspaces/<sha>, which the reviewed build needs and
the prebuild planner does not check (the validation probe's restore_bases.py, on this release)."""
import asyncio, json, sys
from pathlib import Path
from ape.toolkits.execute.lean.config import LeanVerifyToolConfig
from ape.toolkits.execute.lean.core.restore_manager import RestoreManager
from ape.utils.logging import create_logger

shas = sorted({json.loads(l)["base_sha"] for l in
               Path("inputs/probes/probe-2026-07-08-v1/input/episodes.jsonl").read_text().splitlines()})
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
