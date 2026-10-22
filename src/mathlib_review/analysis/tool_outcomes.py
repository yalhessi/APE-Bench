"""What every tool call in a run came back with.

Half the files of every wide thread in this project were fixes to shared machinery -- a tool that
refused a well-formed argument, a search that matched the wrong declaration, a compile that
warranted the wrong candidate -- and each was found by reading what the tools returned
(`docs/research/codebase-redesign-2026-10.md` §1.3). The hygiene layer's nine fixes came from one
such reading, written as a probe script against one scaffold's transcripts
(`results/pr_review_v5/probes/claude-models-2026-10-01/tool_outcomes.py`). This is that reading,
for any run on either scaffold, so the next one is a command rather than a script.

Each call is classified by what its result says:

- `answered`: the tool ran and answered (a compile, a hit list, a file);
- `negative`: the tool ran and found nothing (`compile_errors`, no matches, an empty census) -- an
  answer about the world, not a failure;
- `refused`: the tool refused the call's arguments (`invalid_request`, a bad path), so the
  reviewer spent a turn and learned nothing about the code;
- `error`: the call never ran (malformed input, a tool that does not exist, a containment
  refusal, a parameter the installed CLI lacks);
- `env`: the tool ran and could not answer (`environment_failure`, `timeout`, a missing store);
- `missing`: the transcript records the call and no result for it -- the session was cut off, or
  the transcript is partial. Unknown, never `answered`: until 2026-10-22 such a call paired with an
  empty text and `is_error=False`, which classified as answered, so an interrupted
  `lean_verify_edit` read as a check that ran.

`attempts_without_transcript` counts attempts whose directory holds neither transcript format, so
a reading says how much of the run it saw.

Every task's submission tool is counted apart (`ape.tasks.base.submission_tools`): the Claude Code
scaffold ends the session at submission, so the SDK records that one result as rejected ("The user
doesn't want to proceed with this tool use") whatever happened, and the task's stored result is its
record. Until 2026-10-22 only `submit_findings` was, so the first Claude Code smoke run of
`packet_session` reported its `submit_outputs` as an error.

Reads the orchestrator tree (`.ape/runs/<run>/`, gitignored) through `TaskStorage`, every sample
and every attempt -- a failed attempt's calls are part of what the tools did -- and descends into
nested subtask batches, so a lead run's arms are read with their lead.
"""

from __future__ import annotations

import asyncio
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple

from ape.orchestration.persistence import TaskStorage
from src.mathlib_review.analysis.trajectory import DEFAULT_APE_ROOT, _reroot
from src.mathlib_review.io import jsonl_rows

#: The two transcript formats, one per scaffold. Claude Code writes its SDK conversation;
#: `ape_agent` writes its session, never the cumulative per-turn files under `conversations/`.
TRANSCRIPTS = ("claude_code_conversation_*.jsonl", "ape_agent_session_*.jsonl")

CLASSES = ("answered", "negative", "refused", "error", "env", "missing")
NEGATIVE_OUTCOMES = {"compile_errors", "no_result"}
REFUSED_OUTCOMES = {"invalid_request", "blocked"}
ENV_OUTCOMES = {"environment_failure", "timeout"}


@dataclass(frozen=True)
class ToolCall:
    name: str
    input: Dict[str, Any]
    text: str
    is_error: bool
    #: False when the transcript holds the call and no result for it.
    has_result: bool = True


def _result_text(block: Dict[str, Any]) -> str:
    # ape_agent puts the body in `result_content`; the Claude SDK in `content`, a string or a
    # list of text blocks.
    if block.get("result_content") is not None:
        return str(block["result_content"])
    raw = block.get("content")
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        return "\n".join(b.get("text", "") for b in raw if isinstance(b, dict))
    return "" if raw is None else str(raw)


def tool_calls(attempt_dir: Path) -> Iterator[ToolCall]:
    """Every tool call one attempt made, paired with its result, from either transcript."""

    for pattern in TRANSCRIPTS:
        for transcript in sorted(Path(attempt_dir).glob(pattern)):
            uses: Dict[str, Tuple[str, Dict[str, Any]]] = {}
            results: Dict[str, Tuple[str, bool]] = {}
            for row in jsonl_rows(transcript):
                content = (row.get("message") or {}).get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use" and block.get("id"):
                        uses[block["id"]] = (str(block.get("name")), block.get("input") or {})
                    elif block.get("type") == "tool_result" and block.get("tool_use_id"):
                        results[block["tool_use_id"]] = (_result_text(block),
                                                         bool(block.get("is_error")))
            for use_id, (name, tool_input) in uses.items():
                if use_id not in results:
                    yield ToolCall(name, tool_input, "", False, has_result=False)
                    continue
                text, is_error = results[use_id]
                yield ToolCall(name, tool_input, text, is_error)


def classify(name: str, text: str, is_error: bool, has_result: bool = True) -> Tuple[str, str]:
    """(class, detail) for one tool result. The rules of the 2026-10-01 probe, plus `missing`."""

    if not has_result:
        return "missing", "no result recorded"
    head = text[:400]
    if "<tool_use_error>" in head or is_error:
        if "No such tool available" in head:
            return "error", "no such tool"
        if "could not be parsed as JSON" in head:
            return "error", "malformed input"
        if "unexpected parameter" in head:
            return "error", "parameter the CLI lacks"
        return "error", head[:60]
    if head.startswith("PreToolUse:") and "hook error" in head:
        return "error", "containment refusal"
    if name in ("Grep", "Glob", "Read"):
        if "No matches found" in head or "No files found" in head:
            return "negative", ""
        if "File does not exist" in head or "Search failed" in head:
            return "refused", head[:60]
        return "answered", ""
    try:
        payload = json.loads(text)
    except (ValueError, TypeError):
        payload = None
    if not isinstance(payload, dict):
        return "answered", ""
    outcome = payload.get("outcome")
    if outcome in REFUSED_OUTCOMES:
        return "refused", str(payload.get("error", ""))[:70]
    if outcome in ENV_OUTCOMES:
        return "env", str(payload.get("message") or payload.get("error", ""))[:70]
    if outcome == "tool_error":
        return "error", str(payload.get("error", ""))[:70]
    if outcome in NEGATIVE_OUTCOMES:
        return "negative", ""
    if payload.get("success") is False:
        error = str(payload.get("error", ""))
        if "no declaration table" in error:
            return "env", "no declaration table"
        return "refused", error[:70]
    if payload.get("count") == 0 or payload.get("verdict") == "insufficient_evidence":
        return "negative", str(payload.get("empty_because", ""))
    return "answered", ""


async def _attempt_dirs(tasks_dir: Path, root: Path) -> List[Path]:
    """Every attempt directory under a `tasks/` directory, through the persisted samples, then
    the same for each nested subtask batch an attempt spawned."""

    found: List[Path] = []
    if not tasks_dir.is_dir():
        return found
    for task_dir in sorted(p for p in tasks_dir.iterdir() if p.is_dir()):
        samples = await TaskStorage(task_dir, task_dir.name).load_all_samples()
        for _index, sample in sorted(samples.items()):
            for attempt in sample.attempts:
                path = _reroot(str(attempt.path), root)
                if not path.is_dir():
                    continue
                found.append(path)
                subtasks = path / "subtasks"
                if subtasks.is_dir():
                    for nested in sorted(subtasks.rglob("tasks")):
                        # The first `tasks/` level under this attempt; deeper ones are reached
                        # by the recursion, through their own samples.
                        if nested.is_dir() and "samples" not in nested.relative_to(subtasks).parts:
                            found.extend(await _attempt_dirs(nested, root))
    return found


def tool_outcomes(run_name: str, ape_root: Path = DEFAULT_APE_ROOT) -> Dict[str, Any]:
    """Per tool: calls by class, and the commonest reasons where a call did not answer."""

    root = Path(ape_root) / run_name
    if not (root / "tasks").is_dir():
        raise SystemExit(
            f"no orchestrator tree at {root}: tool outcomes read the session transcripts, which "
            f"live only under the gitignored `.ape/runs/` of the machine that ran `{run_name}`.")
    attempts = asyncio.run(_attempt_dirs(root / "tasks", root))
    table: Dict[str, Counter] = defaultdict(Counter)
    details: Dict[Tuple[str, str], Counter] = defaultdict(Counter)
    import ape.tasks  # noqa: F401 - registers every task, so every submission tool is known
    from ape.tasks.base import submission_tools

    submits = tuple(submission_tools())
    submissions: Counter = Counter()
    without_transcript = 0
    for attempt in attempts:
        if not any(any(Path(attempt).glob(pattern)) for pattern in TRANSCRIPTS):
            without_transcript += 1
        for call in tool_calls(attempt):
            if call.name.endswith(submits):
                submissions[call.name] += 1
                continue
            cls, detail = classify(call.name, call.text, call.is_error, call.has_result)
            table[call.name][cls] += 1
            if cls in ("refused", "error", "env") and detail:
                details[(call.name, cls)][detail] += 1
    tools = {
        name: {"calls": sum(counts.values()), **{cls: counts[cls] for cls in CLASSES}}
        for name, counts in sorted(table.items(), key=lambda item: -sum(item[1].values()))
    }
    why: Dict[str, Dict[str, List[List[Any]]]] = defaultdict(dict)
    for (name, cls), reasons in sorted(details.items()):
        why[name][cls] = [[reason, count] for reason, count in reasons.most_common(4)]
    return {"run": run_name, "attempts": len(attempts),
            "attempts_without_transcript": without_transcript, "tools": tools,
            "why": dict(why), "submissions": dict(submissions)}
