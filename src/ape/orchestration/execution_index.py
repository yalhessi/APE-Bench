"""Semantic ids to physical paths, written where the work runs.

Readers of a finished run recover what a directory *is* by parsing where it sits.
`trajectory.py` says so outright -- "the orchestrator encodes them in the directory it creates
for each batch, so the path *is* the provenance" -- and pays for it in two ways:

* `samples/0` and `attempts/attempt_*` are hardcoded, so a sample index other than 0 is
  invisible;
* the arm-result glob is depth-sensitive, so retiring budget tiers changed
  `subtasks/wave<N>/<tier>/<id>/` to `subtasks/wave<N>/<id>/` and the reader needed a second
  glob to keep the September runs readable. The next layout change needs a third.

Neither is a reader bug. The information -- which arm, which wave, which work unit -- is known
at dispatch and thrown away, leaving the reader to infer it from a directory name.

So it is written down instead. One append-only line per executed task, naming the semantic id
the caller dispatched under and every physical path that id produced. Appending rather than
rewriting matters for the same reason it matters in the lead's journal: a crash must leave what
already ran still findable.

This is not a second source of truth for cost. The rows carry per-attempt cost because that is
part of locating an attempt's record, and the ledger stays `task_outcome.json` and the samples.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

INDEX_VERSION = "execution-index/1"

#: Default filename. Callers pass a full path; this is here so every family that wants one
#: spells it the same way.
INDEX_FILENAME = "execution_index.jsonl"


def _relative(path: Path) -> str:
    """Repo-relative when it can be, absolute when it cannot.

    A run directory is inside the repo; a temp directory in a test is not, and refusing to
    record it would make the index untestable.
    """

    try:
        return str(Path(path).resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def attempt_rows(samples: Any) -> List[Dict[str, Any]]:
    """Flatten persisted samples into `(sample_index, attempt)` locations.

    Reads `attempt.path`, which the orchestrator already records, rather than reconstructing
    it -- the reconstruction is what hardcodes `samples/0`.

    `TaskStorage.load_all_samples()` returns `Dict[int, Sample]`, and iterating a dict yields
    its keys. Taking an `Iterable[Any]` here and iterating it directly meant every call got a
    list of ints and raised, which killed every delegation wave on `pr5_smoke4_rep8` -- after
    the arms had run, so their work was spent and discarded.
    """

    if isinstance(samples, dict):
        samples = [samples[index] for index in sorted(samples)]
    rows: List[Dict[str, Any]] = []
    for sample in samples or []:
        raw = sample.model_dump(mode="json") if hasattr(sample, "model_dump") else dict(sample)
        for attempt in raw.get("attempts") or []:
            item = (attempt.model_dump(mode="json") if hasattr(attempt, "model_dump")
                    else dict(attempt))
            rows.append({
                "sample_index": raw.get("sample_index"),
                "attempt_id": item.get("attempt_id"),
                "path": _relative(item["path"]) if item.get("path") else None,
                "status": item.get("status"),
                "cost": item.get("cost"),
                "cached_cost": item.get("cached_cost"),
            })
    return rows


def append(index_path: Optional[Any], row: Dict[str, Any]) -> None:
    """One line. Never raises: losing the index must not lose the work it indexes."""

    if not index_path:
        return
    try:
        target = Path(index_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"version": INDEX_VERSION, **row},
                                    sort_keys=True, default=str) + "\n")
    except Exception:  # noqa: BLE001 - see above
        pass


async def record(
    index_path: Optional[Any],
    orchestrator,
    results,
    *,
    semantic_ids: Dict[str, str],
    group: str,
    parent: Optional[str] = None,
) -> None:
    """Index every task this orchestrator scheduled.

    `semantic_ids` maps `task_id -> the id the caller dispatched under` -- an `invocation_id`
    for a review arm, a spec id for anything using `spawn_subtasks`. Tasks whose id is absent
    are still recorded, under their `task_id`: an unindexed task is worse than a
    coarsely-indexed one.
    """

    if not index_path:
        return

    from .persistence import TaskStorage

    for result in getattr(results, "task_results", []) or []:
        # Indexing must never be able to fail the work it indexes. `append` already swallows
        # its errors for that reason -- "losing the index must not lose the work it indexes" --
        # and this loop did not, so one shape bug in `attempt_rows` raised out of `run_wave`
        # and cost a run every arm result it had just paid for. The narrow fix was the dict;
        # this is the one that makes the class of bug survivable.
        try:
            raw = (result.model_dump(mode="json") if hasattr(result, "model_dump")
                   else dict(result))
            task_id = raw.get("task_id")
            global_index = raw.get("global_index")
            if global_index is None:
                continue
            task_dir = Path(orchestrator.tasks_dir) / str(global_index)
            try:
                samples = await TaskStorage(task_dir, str(global_index)).load_all_samples()
            except Exception:  # noqa: BLE001 - an unreadable task still gets a located row
                samples = {}
            append(index_path, {
                "semantic_id": semantic_ids.get(task_id, task_id),
                "task_id": task_id,
                "task_type": raw.get("task_type"),
                "group": group,
                "parent": parent,
                "global_index": global_index,
                "task_dir": _relative(task_dir),
                "attempts": attempt_rows(samples),
            })
        except Exception:  # noqa: BLE001 - see above
            logger = getattr(orchestrator, "logger", None)
            if logger is not None:
                logger.warning("execution index: could not record a task; continuing",
                               exc_info=True)


def load(index_path: Optional[Any]) -> List[Dict[str, Any]]:
    """Every row, in the order written. A truncated final line is dropped."""

    if not index_path or not Path(index_path).is_file():
        return []
    rows = []
    for line in Path(index_path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            break
    return rows


def by_semantic_id(index_path: Optional[Any]) -> Dict[str, Dict[str, Any]]:
    """`semantic_id -> its row`. A repeated id keeps the last, which is the retry."""

    return {row["semantic_id"]: row for row in load(index_path) if row.get("semantic_id")}
