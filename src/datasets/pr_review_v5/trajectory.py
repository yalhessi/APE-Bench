"""Extract a durable, compact trajectory from a run's orchestrator output.

A v5 run leaves two very different records. `results/pr_review_v5/runs/<run>/` holds the
conclusions — the agenda, the routing ledger, the candidates, the findings. The *work* is in
`.ape/runs/<run>/`: 147 MB per run of nested orchestrator directories, session transcripts,
per-task timings and token counts. That tree is gitignored, is 172 directories deep on this
machine, and is the first thing anyone deletes when a disk fills.

So the overlay must not read it directly. This module walks it once and writes a sidecar
into the run directory, after which every downstream view reads only `results/`.

Three things live in `.ape` and nowhere else, which is why the walk is worth doing:

* **Per-invocation timing.** `delegations.jsonl::wall_seconds` is the *tier's* duration
  copied onto every job in it — 239 rows carry 29 distinct values, one repeated 108 times.
  The nested `task_result.json` has real `started_at`/`completed_at`, on all 232 of them.
* **Per-invocation tokens.** `delegations.jsonl::token_usage` is likewise the tier
  aggregate; summing it over the held-out run gives $1,141.84 against a real ~$21. The
  sibling `cost` field *is* per-job and is trustworthy, but the token counts are not.
* **The transcripts.** What the lead asked, what a specialist did with its tools, and what
  either of them actually said.

The wave is in the directory name (`subtasks/wave2/...`), so the walk recovers it from the
path. The budget *tier* used to be there too; tiers were retired as orchestrator groupings
once per-task limits existed, so the segment is present only in runs made before that and the
tier now comes off the delegation ledger.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from src.datasets.pr_review_v4.io import display_path

from .paths import assert_repo_root, run_dir
from .schema import BUDGET_TIERS

#: Distinguishes an old tier segment from the orchestrator id that replaced it.
TIER_NAMES = frozenset(BUDGET_TIERS)

TRAJECTORY_VERSION = "v5-trajectory/1"

DEFAULT_APE_ROOT = Path(".ape/runs")

#: How much of a `tool_result` body to keep. A single `file_read` result is the bulk of the
#: bytes in a transcript — 1.97 MB of the held-out run's 3.80 MB of tool output — while the
#: assistant's own text (4.51 MB) is the part worth reading and is never truncated.
DEFAULT_TOOL_RESULT_CAP = 2000

#: Where an arm's result sits under its lead, for runs with no execution index. Depth is fixed
#: by the orchestrator: lead task -> sample -> attempt -> subtasks/<wave>/<tier>/<batch> -> arm
#: task. Two shapes, because the subtask layout changed when budget tiers were retired: tiers
#: existed only to vary `sample_max_cost`, which is orchestrator-wide, so `subtasks/<wave>/
#: <tier>/<id>/` became `subtasks/<wave>/<id>/` -- one segment shorter, and a second glob.
#:
#: Needing a second glob for a layout change is the reason `execution_index.jsonl` exists. A
#: run that wrote one is read through it and never reaches these; they stay for the September
#: runs, which did not.
_ARM_RESULT_GLOBS = (
    "tasks/*/samples/*/attempts/*/subtasks/*/*/tasks/*/task_result.json",
    "tasks/*/samples/*/attempts/*/subtasks/*/*/*/tasks/*/task_result.json",
)
_LEAD_RESULT_GLOB = "tasks/*/task_result.json"
_SESSION_GLOB = "ape_agent_session_*.jsonl"


@dataclass
class Turn:
    """One assistant or user turn, with its content flattened for display."""

    conversation_id: str
    index: int
    role: str
    ts: Optional[str]
    items: List[dict]


@dataclass
class Invocation:
    """One arm call: what ran, when, for how long, at what cost."""

    invocation_id: str
    arm_id: Optional[str]
    work_unit_id: Optional[str]
    pr_number: Optional[int]
    wave: Optional[str]
    tier: Optional[str]
    status: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    execution_time: Optional[float]
    cost: Optional[float]
    cached_cost: Optional[float]
    turns: int
    token_usage: Dict[str, Optional[float]] = field(default_factory=dict)
    tool_calls: Dict[str, int] = field(default_factory=dict)
    has_transcript: bool = False


@dataclass
class Lead:
    """One lead call. There is exactly one per PR round."""

    conversation_id: str
    pr_number: Optional[int]
    episode_id: Optional[str]
    status: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    execution_time: Optional[float]
    cost: Optional[float]
    turns: int
    token_usage: Dict[str, Optional[float]] = field(default_factory=dict)
    tool_calls: Dict[str, int] = field(default_factory=dict)
    candidate_assessments: List[dict] = field(default_factory=list)
    has_transcript: bool = False


# --- reading the orchestrator tree ----------------------------------------------------

def _load(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _wave_and_tier(path: Path) -> tuple:
    """Recover `(wave, tier)` from the `subtasks/<wave>/<tier>/` segment of a path.

    Neither is a field on any record. The orchestrator encodes them in the directory it
    creates for each batch, so the path *is* the provenance.
    """

    parts = path.parts
    if "subtasks" not in parts:
        return None, None
    index = parts.index("subtasks")
    wave = parts[index + 1] if len(parts) > index + 1 else None
    # The tier segment exists only in runs made before tiers were retired. In the current
    # layout the next segment is the orchestrator id (`<pr>_w<N>`), so a value that parses as
    # one is not a tier.
    candidate = parts[index + 2] if len(parts) > index + 2 else None
    tier = candidate if candidate in TIER_NAMES else None
    return wave, tier


def _token_block(result: dict) -> Dict[str, Optional[float]]:
    usage = result.get("token_usage") or {}
    return {
        key: usage.get(key)
        for key in (
            "input_tokens", "output_tokens", "total_tokens",
            "cache_read_input_tokens", "cache_creation_input_tokens",
            "reasoning_tokens", "total_cost", "cached_total_cost",
        )
    }


def _sample_cost(result_path: Path) -> tuple:
    """`(cost, cached_cost, status)` from the sibling `sample.json`.

    `task_result.json` carries the token block; the sample carries the attempt's accounted
    cost. They agree, but only the sample has the cached figure.
    """

    # `<task_dir>/samples/0/sample.json`, beside the result — not three levels up, which
    # resolved to the orchestrator root and never existed. The silent consequence was that
    # `cached_cost` was always null and `cost` fell back to the uncached token figure, so the
    # sidecar reported the no-cache counterfactual as if it were spend.
    sample = _load(result_path.parent / "samples" / "0" / "sample.json")
    if not sample:
        return None, None, None
    attempts = sample.get("attempts") or []
    if not attempts:
        return None, None, sample.get("status")
    # Cumulative across attempts: a sample that paused and resumed spent the sum, and reading
    # only the last attempt understates it.
    cost = sum(a.get("cost") or 0.0 for a in attempts)
    cached = sum((a.get("cached_cost") or a.get("cost") or 0.0) for a in attempts)
    return cost, cached, attempts[-1].get("status")


def _read_turns(session: Path, conversation_id: str, cap: int) -> List[Turn]:
    """Flatten one session transcript.

    Reads `ape_agent_session_*.jsonl` and never `conversations/`: the per-turn files are
    *cumulative* — turn 3 contains turns 1 and 2 — so that directory is roughly three times
    redundant and the session file is the same content once.
    """

    turns: List[Turn] = []
    try:
        lines = session.read_text().splitlines()
    except OSError:
        return turns
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("type") not in ("assistant", "user"):
            continue
        items: List[dict] = []
        for content in (row.get("message") or {}).get("content") or []:
            if not isinstance(content, dict):
                continue
            kind = content.get("type")
            if kind == "text" and content.get("text"):
                # Never truncated: the model's own words are the reason to read this at all.
                items.append({"t": "text", "v": content["text"]})
            elif kind == "tool_use":
                raw = json.dumps(content.get("input"), ensure_ascii=False)
                items.append({
                    "t": "use", "name": content.get("name"), "id": content.get("id"),
                    "v": raw[:cap], "bytes": len(raw),
                })
            elif kind == "tool_result":
                body = content.get("result_content") or ""
                items.append({
                    "t": "res", "name": content.get("name"),
                    "id": content.get("tool_use_id"),
                    "v": body[:cap], "bytes": len(body),
                })
            elif kind == "thinking" and content.get("reasoning_content"):
                items.append({"t": "think", "v": content["reasoning_content"]})
        if items:
            turns.append(Turn(conversation_id, len(turns), row["type"],
                              row.get("timestamp"), items))
    return turns


def _tool_counts(turns: Sequence[Turn]) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    for turn in turns:
        for item in turn.items:
            if item["t"] == "use" and item.get("name"):
                counts[item["name"]] += 1
    return dict(sorted(counts.items()))


def _session_for(result_path: Path) -> Optional[Path]:
    """The transcript beside a `task_result.json`, if the attempt kept one."""

    attempts = sorted((result_path.parent / "samples" / "0" / "attempts").glob("attempt_*")) \
        if (result_path.parent / "samples").is_dir() else []
    for attempt in reversed(attempts):
        found = sorted(attempt.glob(_SESSION_GLOB))
        if found:
            return found[-1]
    return None


# --- extraction -----------------------------------------------------------------------

def _indexed_arms(run_name: str) -> Dict[str, Dict[str, Any]]:
    """`invocation_id -> its index row`, when the run wrote one.

    Empty for every run made before the index existed, which is what the globs below are still
    for. A run that has one needs no glob at all: the row names the task directory and every
    attempt path, so neither the subtask depth nor the sample index has to be guessed.
    """

    from ape.orchestration.execution_index import INDEX_FILENAME, by_semantic_id

    try:
        return by_semantic_id(run_dir(run_name) / INDEX_FILENAME)
    except Exception:  # noqa: BLE001 - a missing results dir is not a trajectory failure
        return {}


def _arm_result_paths(root: Path, indexed: Dict[str, Dict[str, Any]]) -> List[Path]:
    """Where the arm results are, from the index when there is one and the globs when not."""

    if indexed:
        return sorted({Path(row["task_dir"]) / "task_result.json"
                       for row in indexed.values() if row.get("task_dir")})
    seen, paths = set(), []
    for pattern in _ARM_RESULT_GLOBS:
        for path in root.glob(pattern):
            if path not in seen:
                seen.add(path)
                paths.append(path)
    return sorted(paths)


def _indexed_cost(row: Dict[str, Any]) -> tuple:
    """Cumulative across attempts, like `_sample_cost` -- a sample that paused and resumed
    spent the sum, and reading only the last attempt understates it."""

    attempts = row.get("attempts") or []
    if not attempts:
        return None, None, None
    cost = sum(item.get("cost") or 0.0 for item in attempts)
    cached = sum((item.get("cached_cost") or item.get("cost") or 0.0) for item in attempts)
    return cost, cached, attempts[-1].get("status")


def _indexed_session(row: Dict[str, Any]) -> Optional[Path]:
    for attempt in reversed(row.get("attempts") or []):
        if not attempt.get("path"):
            continue
        found = sorted(Path(attempt["path"]).glob(_SESSION_GLOB))
        if found:
            return found[-1]
    return None


def extract(run_name: str, ape_root: Path = DEFAULT_APE_ROOT,
            cap: int = DEFAULT_TOOL_RESULT_CAP) -> dict:
    """Walk one run's orchestrator tree into invocations, leads and turns."""

    root = ape_root / run_name
    invocations: List[Invocation] = []
    leads: List[Lead] = []
    turns_by_pr: Dict[str, List[Turn]] = defaultdict(list)

    if not root.is_dir():
        return {"root": display_path(root), "present": False,
                "invocations": [], "leads": [], "turns_by_pr": {}}

    # --- arm invocations ---
    indexed = _indexed_arms(run_name)
    for result_path in _arm_result_paths(root, indexed):
        result = _load(result_path)
        if not result or not result.get("invocation_id"):
            continue
        row = indexed.get(result["invocation_id"])
        if row is not None:
            # `group` is the dispatcher's own name for the wave -- "wave2" -- rather than a
            # directory segment that happens to be spelled the same way. Kept verbatim so a
            # row read through the index and one read through the glob below carry the same
            # value in the same field; two spellings of one wave is how a field becomes
            # unusable for grouping.
            wave = str(row.get("group") or "") or None
            tier = None
            cost, cached, sample_status = _indexed_cost(row)
            session = _indexed_session(row)
        else:
            wave, tier = _wave_and_tier(result_path)
            cost, cached, sample_status = _sample_cost(result_path)
            session = _session_for(result_path)
        turn_rows = _read_turns(session, result["invocation_id"], cap) if session else []
        pr_number = result.get("pr_number")
        invocations.append(Invocation(
            invocation_id=result["invocation_id"],
            arm_id=result.get("arm_id"),
            work_unit_id=result.get("work_unit_id"),
            pr_number=pr_number,
            wave=wave, tier=tier,
            status=result.get("status") or sample_status,
            started_at=result.get("started_at"),
            completed_at=result.get("completed_at"),
            execution_time=result.get("execution_time"),
            cost=cost if cost is not None else _token_block(result).get("total_cost"),
            cached_cost=cached,
            turns=len(turn_rows),
            token_usage=_token_block(result),
            tool_calls=_tool_counts(turn_rows),
            has_transcript=bool(turn_rows),
        ))
        if turn_rows:
            turns_by_pr[str(pr_number)].extend(turn_rows)

    # --- leads ---
    for result_path in sorted(root.glob(_LEAD_RESULT_GLOB)):
        result = _load(result_path)
        # An arm result also matches nothing here (different depth), but a lead result is
        # distinguished positively: it carries routing output, never an invocation_id.
        if not result or result.get("invocation_id"):
            continue
        pr_number = result.get("pr_number")
        conversation_id = f"lead:{pr_number}"
        cost, _cached, sample_status = _sample_cost(result_path)
        session = _session_for(result_path)
        turn_rows = _read_turns(session, conversation_id, cap) if session else []
        leads.append(Lead(
            conversation_id=conversation_id,
            pr_number=pr_number,
            episode_id=result.get("episode_id"),
            status=result.get("status") or sample_status,
            started_at=result.get("started_at"),
            completed_at=result.get("completed_at"),
            execution_time=result.get("execution_time"),
            cost=cost if cost is not None else _token_block(result).get("total_cost"),
            turns=len(turn_rows),
            token_usage=_token_block(result),
            tool_calls=_tool_counts(turn_rows),
            candidate_assessments=result.get("candidate_assessments") or [],
            has_transcript=bool(turn_rows),
        ))
        if turn_rows:
            turns_by_pr[str(pr_number)].extend(turn_rows)

    return {
        "root": display_path(root), "present": True,
        "invocations": invocations, "leads": leads, "turns_by_pr": dict(turns_by_pr),
    }


def reconcile_cost(run_name: str, extracted: dict) -> dict:
    """Total spend by bucket, against what the run manifest claims.

    `trace.reconcile` computes `total_cost` as the leads' own cost plus the cost of
    `proposed` and `agent_added` delegations. The mandatory floor runs *inside* the lead's
    nested orchestrator, so it is in neither term — on the held-out run that omits $14.52 of
    a $21.06 spend and the manifest reports $6.54. The floor being two thirds of the bill is
    the most interesting fact about the run, so the sidecar records the split rather than a
    single corrected number.
    """

    directory = run_dir(run_name)
    dispositions: Dict[str, str] = {}
    ledger = directory / "delegations.jsonl"
    if ledger.is_file():
        for line in ledger.read_text().splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            dispositions[row["invocation_id"]] = row.get("disposition")

    buckets: Dict[str, float] = defaultdict(float)
    for item in extracted["invocations"]:
        if item.cost is None:
            continue
        buckets[dispositions.get(item.invocation_id) or "unknown"] += item.cost
    lead_cost = sum(item.cost or 0.0 for item in extracted["leads"])

    manifest = _load(directory / "run_manifest.json") or {}
    actual = lead_cost + sum(buckets.values())
    reported = manifest.get("total_cost")
    return {
        "lead": round(lead_cost, 6),
        "by_disposition": {key: round(value, 6) for key, value in sorted(buckets.items())},
        "actual_total": round(actual, 6),
        "manifest_total": reported,
        # `trace.reconcile` omits the floor; recording the gap makes the defect visible in
        # the artifact rather than only in a commit message.
        "manifest_understates_by": (
            round(actual - reported, 6) if isinstance(reported, (int, float)) else None
        ),
    }


def write_trajectory(run_name: str, ape_root: Path = DEFAULT_APE_ROOT,
                     cap: int = DEFAULT_TOOL_RESULT_CAP) -> dict:
    out = run_dir(run_name) / "trajectory"
    extracted = extract(run_name, ape_root, cap)
    out.mkdir(parents=True, exist_ok=True)
    (out / "turns").mkdir(exist_ok=True)

    def dump(path: Path, rows: Iterable) -> int:
        payload = [asdict(row) if hasattr(row, "__dataclass_fields__") else row
                   for row in rows]
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")) + "\n" for row in payload),
            encoding="utf-8",
        )
        return len(payload)

    invocations = dump(out / "invocations.jsonl", extracted["invocations"])
    leads = dump(out / "leads.jsonl", extracted["leads"])

    # Sharded per PR so an overlay page loads only its own conversations. The held-out run's
    # PR 33149 alone is 109 conversations; a single file would make every page pay for it.
    turn_rows = 0
    for pr_number, rows in sorted(extracted["turns_by_pr"].items()):
        turn_rows += dump(out / "turns" / f"pr-{pr_number}.jsonl", rows)

    report = {
        "schema_version": TRAJECTORY_VERSION,
        "run_name": run_name,
        "ape_root": extracted["root"],
        "ape_present": extracted["present"],
        "tool_result_cap": cap,
        "invocations": invocations,
        "leads": leads,
        "turn_rows": turn_rows,
        "with_transcript": sum(
            1 for item in extracted["invocations"] + extracted["leads"] if item.has_transcript
        ),
        "cost": reconcile_cost(run_name, extracted),
        "bytes": sum(path.stat().st_size for path in out.rglob("*") if path.is_file()),
    }
    (out / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract a durable trajectory sidecar from a v5 run's .ape output"
    )
    parser.add_argument("--run", required=True)
    parser.add_argument("--ape-root", type=Path, default=DEFAULT_APE_ROOT)
    parser.add_argument("--tool-result-cap", type=int, default=DEFAULT_TOOL_RESULT_CAP)
    args = parser.parse_args()
    assert_repo_root()
    print(json.dumps(
        write_trajectory(args.run, args.ape_root, args.tool_result_cap), indent=2
    ))


if __name__ == "__main__":
    main()
