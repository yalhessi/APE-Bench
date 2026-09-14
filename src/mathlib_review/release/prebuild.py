"""Prebuild the Lean workspaces a run verifies in.

Two kinds, one command, because an operator preparing a run should have one place to look:

* **Base workspaces** (default): one builder input row per distinct base commit in the run's
  selection, for `ape.toolkits.execute.lean.build` to restore from the content store. The
  base is the snapshot every overlay is laid over; without it nothing runs at all, and the
  run's preflight refuses.

* **Reviewed workspaces** (`--reviewed`): for every episode in the selection, the base
  snapshot plus that PR's diff plus its changed modules rebuilt, at `workspaces/<base>+<fp>`.
  This is the environment in which a compile of a changed file sees the declarations the PR
  itself adds or renames. Without it every `lean_verify` resolves imports against the base
  commit's `.olean`s, and a sibling the PR renamed reads as `Unknown constant` -- 41 of 321
  arm sessions on the held-out run, 16 findings asserting a build failure on PRs that all
  build. The task falls back to the source-only overlay when the reviewed workspace is
  absent and says so at WARNING; `dataset.require_reviewed_workspaces: true` makes the run
  refuse instead.

The reviewed build is the toolkit's (`BuildManager.build_reviewed_workspace`); the sources it
lays down are the task layer's (`ReviewPRCoreTask.prepare_reviewed_sources`, the same function
the per-attempt overlay uses). This module only decides *which* episodes need one, in the
order the run would meet them, and refuses to start on an episode whose base is not built --
that failure would otherwise surface twelve minutes into a 2.7 GB copy.

Measured on this NFS for PR 33337 (2 changed files, 10 modules on the import path between
them): copy of `.lake/build` 585 s, `lake build` 67 s, 705 s end to end, base untouched.
Sequential on purpose: the copy is the cost and it is one filesystem.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence, Tuple

from ape.utils.project import PROJECT_ROOT
from ape.utils import parse_cli_args
from ape.utils.logging import create_logger

from ape.toolkits.execute.lean.models import BuildResult

from src.mathlib_review.analysis.runs import unbuilt_base_commits
from src.mathlib_review.io import load_jsonl
from src.mathlib_review.opportunities.runner import load_run as load_v4_run
from src.mathlib_review.release.run_contract import select_units
from src.mathlib_review.review.preflight import (
    assert_toolchain, reviewed_workspace_keys, unbuilt_reviewed_workspaces,
)
from src.mathlib_review.schema import RenderedPrompt, ReviewEpisodeInput, ReviewWorkUnit
from src.mathlib_review.review.task_adapter import build_candidate_task_data

READY = "ready"
MISSING = "to build"
BASE_MISSING = "base not built"


@dataclass(frozen=True)
class ReviewedBuild:
    """One episode's reviewed workspace: its key, and whether it exists."""

    key: str
    episode: Any  # ReviewEpisodeInput; anything with pr_number / base_sha / diff / changed_files
    status: str


async def plan_reviewed_builds(episodes: Sequence[Any]) -> List[ReviewedBuild]:
    """Classify every episode's reviewed workspace: ready, to build, or blocked on its base.

    Episodes with no diff have no reviewed state and are not listed -- the same rule the
    preflight applies, from the same function, so the two cannot disagree about which
    episodes need one.
    """

    keys = await reviewed_workspace_keys(episodes)
    missing = await unbuilt_reviewed_workspaces(episodes)
    bases_unbuilt = set(await unbuilt_base_commits({ep.base_sha for ep in keys.values()}))
    plan = []
    for key, episode in keys.items():
        if key not in missing:
            status = READY
        elif episode.base_sha in bases_unbuilt:
            status = BASE_MISSING
        else:
            status = MISSING
        plan.append(ReviewedBuild(key=key, episode=episode, status=status))
    return sorted(plan, key=lambda item: (item.episode.pr_number, item.key))


def prepare_sources_for(episode: Any, *, logger) -> Callable[[Path, Path], Awaitable[None]]:
    """The task layer's half of one reviewed build, closed over one episode.

    Handed to the toolkit as a callable because overlay creation and patching belong to the
    task that owns the patch rules, and the toolkit must not import a task. It is the same
    classmethod the per-attempt overlay calls, so the prebuilt workspace and the fallback
    overlay lay down identical sources.
    """

    from ape.tasks.lean_tasks.formal_math.pr_review.core import ReviewPRCoreTask

    async def prepare(build_root: Path, base_root: Path) -> None:
        await ReviewPRCoreTask.prepare_reviewed_sources(
            build_root, base_root, pr_diff=episode.diff,
            changed_files=list(episode.changed_files), logger=logger)

    return prepare


async def build_reviewed_workspaces(
    plan: Sequence[ReviewedBuild], *, manager, logger, force_rebuild: bool = False,
) -> Dict[str, Any]:
    """Build the reviewed workspaces the plan says are missing; return `key -> BuildResult`.

    Ready ones are skipped unless `force_rebuild`. Ones whose base is not built are refused
    up front with the base named, never attempted. A failed build is logged and recorded, and
    the next episode still builds: the operator wants the twelve that succeed and the one
    message about the thirteenth, not an exception after the first.
    """

    results: Dict[str, Any] = {}
    for item in plan:
        pr = item.episode.pr_number
        if item.status == BASE_MISSING:
            logger.error(
                "PR %s: reviewed workspace %s needs base %s, which is not built; build the base "
                "first (prebuild without --reviewed, then ape.toolkits.execute.lean.build)",
                pr, item.key, item.episode.base_sha)
            continue
        if item.status == READY and not force_rebuild:
            logger.info("PR %s: reviewed workspace %s is ready", pr, item.key)
            continue
        logger.info("PR %s: building reviewed workspace %s (%d changed files)",
                    pr, item.key, len(item.episode.changed_files))
        try:
            result = await manager.build_reviewed_workspace(
                item.key, item.episode.base_sha,
                prepare_sources=prepare_sources_for(item.episode, logger=logger),
                changed_files=list(item.episode.changed_files), force_rebuild=force_rebuild)
        except Exception as exc:  # noqa: BLE001 -- the builder has already marked the state FAILED
            result = BuildResult(success=False, commit_hash=item.key, error_message=str(exc))
        results[item.key] = result
        if result.success:
            logger.info("PR %s: built %s in %.0fs", pr, item.key, result.build_duration or 0.0)
        else:
            logger.error("PR %s: reviewed workspace %s FAILED: %s",
                         pr, item.key, result.error_message)
    return results


def _selected_episodes(config: Path, overrides: Dict[str, Any]) -> Tuple[List[Any], Any]:
    """The episodes this run config would review, by the run's own selection rule."""

    from src.mathlib_review.review.runner import load_release, load_run, select_units_and_episodes

    dataset, scaffold, _task_overrides = load_run(config, overrides)
    _units, episodes = select_units_and_episodes(dataset, load_release(dataset))
    return episodes, scaffold


def _build_manager(scaffold: Any, logger):
    """A `BuildManager` on the run's own Lean tool config, so the workspace is built with the
    same repository, timeouts and toolchain the run will verify with."""

    from ape.toolkits.execute.lean.config import LeanVerifyToolConfig
    from ape.toolkits.execute.lean.core.build_manager import BuildManager

    config = getattr(getattr(scaffold, "tools_config", None), "lean_verify", None)
    config = config or LeanVerifyToolConfig()
    _repo_name, repo_url = config.resolve_repo(None)
    return BuildManager(config, logger, repo_url=repo_url)


def _print_plan(plan: Sequence[ReviewedBuild]) -> None:
    counts = {status: sum(1 for item in plan if item.status == status)
              for status in (READY, MISSING, BASE_MISSING)}
    print(f"reviewed workspaces for {len(plan)} episode(s): "
          f"{counts[READY]} {READY}, {counts[MISSING]} {MISSING}, "
          f"{counts[BASE_MISSING]} {BASE_MISSING}")
    for item in plan:
        print(f"  PR {item.episode.pr_number:<6} {item.key}  {item.status}"
              f"  ({len(item.episode.changed_files)} changed files)")


def _main_reviewed(args: argparse.Namespace, overrides: Dict[str, Any]) -> int:
    logger = create_logger()
    episodes, scaffold = _selected_episodes(args.config, overrides)
    plan = asyncio.run(plan_reviewed_builds(episodes))
    _print_plan(plan)
    to_build = [item for item in plan if item.status == MISSING]
    if not args.execute:
        print("Nothing built. Re-run with --execute to build the missing ones "
              "(about 12 minutes each on this filesystem; the copy is the cost).")
        return 0
    if not to_build and not args.force_rebuild:
        print("Nothing to build.")
        return 0
    # Before a manager exists and before anything is copied: a missing `lake` must be the
    # first thing found, not the last.
    assert_toolchain(scaffold, logger)
    manager = _build_manager(scaffold, logger)
    results = asyncio.run(build_reviewed_workspaces(
        plan, manager=manager, logger=logger, force_rebuild=args.force_rebuild))
    failed = [key for key, result in results.items() if not result.success]
    print(f"built {len(results) - len(failed)} of {len(results)} reviewed workspace(s)"
          + (f"; FAILED: {failed}" if failed else ""))
    return 1 if failed else 0


def _main_base(args: argparse.Namespace, overrides: Dict[str, Any]) -> int:
    dataset, _scaffold, _overrides = load_v4_run(args.config, overrides)
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
    return 0


def _main_norms(args: argparse.Namespace, overrides: Dict[str, Any]) -> int:
    """Warm the naming-norm index for every base commit this run's episodes sit on.

    `scan_population` walks ~7,400 Mathlib modules and costs about 35 s. Cached per base
    commit, that is fine once; paid inside an attempt it is not, and it is paid unevenly --
    the first rep of a condition would carry the scans that later reps read from disk, which
    is a difference between reps that is not the treatment. Warming costs no model money.
    """

    from src.mathlib_review.evidence.operators.naming_norm import NORM_CACHE_DIR, norm_index

    logger = create_logger()
    episodes, _scaffold = _selected_episodes(args.config, overrides)
    shas = sorted({episode.base_sha for episode in episodes})
    warm = [sha for sha in shas if (NORM_CACHE_DIR / f"{sha}.json").is_file()]
    print(f"naming-norm index for {len(shas)} base commit(s): {len(warm)} warm, "
          f"{len(shas) - len(warm)} to scan")
    if not args.execute:
        print("Nothing scanned. Re-run with --execute to warm the rest "
              "(about 35 s each; spends no model money).")
        return 0

    from ape.toolkits.execute.lean.config import LeanVerifyToolConfig

    workspaces = LeanVerifyToolConfig().get_workspace_dir("mathlib4")
    built = missing = 0
    for sha in shas:
        if (NORM_CACHE_DIR / f"{sha}.json").is_file():
            continue
        payload = norm_index(workspaces / sha, sha)
        if payload is None:
            missing += 1
            logger.warning("no base workspace for %s; its arms will ask the naming question "
                           "without counts", sha)
            continue
        built += 1
        logger.info("naming-norm index for %s: %d subjects, %d files parsed, representative=%s",
                    sha, len(payload.get("subjects") or {}), payload.get("parsed_files"),
                    payload.get("representative"))
    print(f"scanned {built}; {missing} base workspace(s) absent")
    return 1 if missing else 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare what a run reads before it starts: base workspaces (default), "
                    "--reviewed workspaces, or the --norms index")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--reviewed", action="store_true",
                        help="plan (and with --execute, build) the per-episode reviewed "
                             "workspaces -- base + diff + changed modules rebuilt")
    parser.add_argument("--norms", action="store_true",
                        help="warm the naming-norm index for this run's base commits, so the "
                             "~35s scan is not paid inside an attempt (and unevenly across reps)")
    parser.add_argument("--execute", action="store_true",
                        help="with --reviewed or --norms: actually do it; else only report")
    parser.add_argument("--force-rebuild", action="store_true",
                        help="with --reviewed --execute: rebuild ones that are already ready")
    parser.add_argument("--out", type=Path,
                        default=PROJECT_ROOT / "data/pr_review_v4/base_commits.jsonl")
    parser.add_argument("--num-processes", type=int, default=2)
    args, rest = parser.parse_known_args(argv)
    overrides = parse_cli_args(rest)
    if args.norms:
        return _main_norms(args, overrides)
    if args.reviewed:
        return _main_reviewed(args, overrides)
    return _main_base(args, overrides)


if __name__ == "__main__":
    sys.exit(main())
