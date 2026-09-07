"""Run v4's evidence chain over v5's candidates, so a discovery can become a review comment.

Until now `finalize(supported_candidate_ids=…)` was a parameter the runner never supplied.
The gate was therefore closed by construction: every generalist and every non-compile
specialist was admitted `diagnostic` no matter what it had found, and a run could report 319
findings with 2 published. That is not a strictness result — nothing was ever asked to
support those claims. On the verify probe it was 7 of 8 findings, five of them stopped with
"no collector can support this claim's concern family" when three of the five were ordinary
`style` claims that the repository's own linter can settle.

The chain is v4's, unchanged and imported: `evidence.collect_candidate` per candidate, then
`select.select_findings` as the gate. Nothing about the rules is re-implemented here, because
a second copy of a publication gate is a second thing to keep honest.

What is v5's is the wiring, and two workspace decisions carry it:

* **Evidence runs in the attempt's own reviewed workspace.** The collectors that matter
  (`policy` linting the changed file, `lean_compile`) must see the code as the PR leaves it,
  not as it was before. Those workspaces are symlink farms over a shared snapshot, so they
  are complete — measured at 7445 visible `.lean` files, with `scripts/lint-style.py`
  present — while still carrying the patched files. The partial-tree worry that governs the
  naming scan does not apply to them.
* **The naming population is read from the base snapshot instead.** The population question
  is "what did the corpus look like *before* this PR", and `LazyPopulationScan` abstains
  rather than measure a norm from a sample. Kept separate on purpose: conflating the two
  would either compile against the wrong tree or measure naming against the wrong corpus.

The `precedent` collector needs a boundary and event corpus that this release does not ship,
so it records a terminal failure and contributes nothing. That costs no recall — its
assertions are `context`-scoped and `inconclusive` by construction, so it could never have
supported a claim on its own.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

from src.datasets.pr_review_v4.evidence import (
    LazyPopulationScan,
    collect_candidate,
    snapshot_workspace,
)
from src.datasets.pr_review_v4.io import jsonl_bytes, write_once
from src.datasets.pr_review_v4.select import select_findings


async def reviewed_workspaces(
    tasks_dir: Path, data: Sequence[Dict[str, Any]], results: Any
) -> Dict[str, str]:
    """Episode -> the reviewed workspace of the attempt that produced its review.

    v4's `runs.reviewed_workspace_map` reads `task_data.episode_id` as an attribute; v5's
    task data are plain dicts. Adapted rather than duplicated so there is still one
    implementation of "which workspace actually reviewed this episode".
    """

    from types import SimpleNamespace

    from src.datasets.pr_review_v4.runs import reviewed_workspace_map

    by_task_id = {
        item.get("task_id"): SimpleNamespace(episode_id=item.get("episode_id"))
        for item in data if item.get("task_id")
    }
    return await reviewed_workspace_map(
        tasks_dir, by_task_id, getattr(results, "task_results", []))


def _collapse_compile_cascades(
    candidates: Sequence[Any], artifacts: Sequence[Any], graph_by_episode: Dict[str, Any],
    supported: Set[str], logger=None,
) -> Set[str]:
    """One broken file is one finding, not one per declaration downstream of the break.

    When a Lean file fails to elaborate, every declaration after the first error reports
    "unknown identifier" for names that are defined in that same file. Agents file each as a
    separate correctness claim and the evidence chain supports all of them, because the file
    genuinely does not compile. Measured on heldout11 rep2: PR 33294 published **eight**
    correctness findings that were one type error at `FixedPoint.lean:100` — `deriv_fp` and
    `mem_range_deriv` were reported "not found" while being declared in the file under test.

    The root is the claim whose target span contains the *first* diagnostic line the compiler
    reported for that file. Everything else in the same file is a consequence, and stays
    `diagnostic`: the observation was not wrong, it was not independent.

    Reuses v4's `candidate_spans` and `diagnostic_lines` rather than re-deriving spans —
    localisation is the part that is easy to get subtly wrong.
    """

    from src.datasets.pr_review_v4.evidence import candidate_spans, diagnostic_lines

    by_candidate = {item.candidate_id: item for item in candidates}
    baseline_by_candidate: Dict[str, Any] = {}
    for artifact in artifacts:
        if (artifact.collector == "lean_compile" and artifact.kind == "compile_result"
                and artifact.source_ref.endswith(":baseline")
                and "\nexit_code=0\n" not in artifact.content):
            baseline_by_candidate[artifact.candidate_id] = artifact

    groups: Dict[Any, List[Any]] = {}
    for candidate_id in sorted(supported):
        candidate = by_candidate.get(candidate_id)
        artifact = baseline_by_candidate.get(candidate_id)
        if candidate is None or artifact is None:
            continue
        # `source_ref` is "workspace:<path>:<compile_path>:baseline"; the compile path is the
        # penultimate segment and is what makes two claims siblings in one broken file.
        parts = artifact.source_ref.rsplit(":", 2)
        if len(parts) != 3:
            continue
        groups.setdefault((candidate.episode_id, parts[1]), []).append((candidate, artifact))

    collapsed: Set[str] = set()
    for (episode_id, path), members in sorted(groups.items()):
        if len(members) < 2:
            continue
        graph = graph_by_episode.get(episode_id)
        first_line = None
        for _candidate, artifact in members:
            lines = diagnostic_lines(artifact.content, path)
            if lines:
                first_line = min(lines) if first_line is None else min(first_line, min(lines))
        root = None
        if graph is not None and first_line is not None:
            for candidate, _artifact in members:
                spans = candidate_spans(candidate, graph).get(path, [])
                if any(start <= first_line <= end for start, end in spans):
                    root = candidate
                    break
        # No span owns the first error — the break is outside every claimed target. Keeping
        # the lowest candidate_id is arbitrary but deterministic, and still collapses the
        # cascade rather than publishing it N times.
        if root is None:
            root = min((c for c, _a in members), key=lambda c: c.candidate_id)
        for candidate, _artifact in members:
            if candidate.candidate_id != root.candidate_id:
                collapsed.add(candidate.candidate_id)
        if logger:
            logger.info(
                "compile cascade in %s: %d claims collapse into %s (first error line %s)",
                path, len(members), root.candidate_id, first_line,
            )
    return collapsed


def collect_supported(
    candidates: Sequence[Any],
    *,
    graphs: Iterable[Any],
    out: Path,
    workspace_by_episode: Optional[Dict[str, str]] = None,
    logger=None,
) -> Set[str]:
    """Collect evidence for each candidate and return the ids the gate would publish.

    Writes the packets, assertions and artifacts under `out/evidence/`. They are the audit
    trail for every admission decision, and without them a `diagnostic` finding cannot be
    told apart from one whose collector simply never ran — which is precisely the confusion
    that let a closed gate look like a strict one for eight runs.
    """

    graph_by_episode = {item.episode_id: item for item in graphs}
    workspace_by_episode = workspace_by_episode or {}
    artifacts, assertions, packets = [], [], []
    baseline_compile_cache: Dict[Any, Any] = {}
    population_cache: Dict[str, object] = {}
    skipped: Dict[str, int] = {}

    for candidate in candidates:
        graph = graph_by_episode.get(candidate.episode_id)
        if graph is None:
            # Nothing can be collected without the change graph, and guessing one would
            # fabricate the spans every collector localises its diagnostics against.
            skipped["no_change_graph"] = skipped.get("no_change_graph", 0) + 1
            continue
        configured = workspace_by_episode.get(candidate.episode_id)
        workspace = Path(configured) if configured else snapshot_workspace(
            getattr(graph, "base_sha", None))
        population = LazyPopulationScan(
            snapshot_workspace(getattr(graph, "base_sha", None)), population_cache)
        collected, asserted, packet = collect_candidate(
            candidate, graph, workspace, None, None, baseline_compile_cache, population,
        )
        artifacts.extend(collected)
        assertions.extend(asserted)
        packets.append(packet)

    evidence_dir = out / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    write_once(evidence_dir / "artifacts.jsonl", jsonl_bytes(artifacts))
    write_once(evidence_dir / "assertions.jsonl", jsonl_bytes(assertions))
    write_once(evidence_dir / "packets.jsonl", jsonl_bytes(packets))

    supported = {item.candidate_id for item in select_findings(candidates, packets, assertions)}
    cascaded = _collapse_compile_cascades(
        candidates, artifacts, graph_by_episode, supported, logger)
    supported -= cascaded
    if logger:
        by_status: Dict[str, int] = {}
        for packet in packets:
            by_status[packet.status] = by_status.get(packet.status, 0) + 1
        logger.info(
            "evidence chain: %d candidate(s) -> packets %s -> %d supported "
            "(%d collapsed as compile cascades)",
            len(packets), dict(sorted(by_status.items())), len(supported), len(cascaded),
        )
        if skipped:
            logger.warning("evidence chain skipped %s", skipped)
    return supported


def evidence_report(out: Path) -> Dict[str, Any]:
    """Why each candidate was or was not supported, read back off the written packets.

    Deliberately separate from the gate: this reads the artifacts rather than recomputing
    anything, so it cannot disagree with the decision that was actually made.
    """

    import json

    path = out / "evidence" / "packets.jsonl"
    if not path.is_file():
        return {"packets": 0}
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    by_status: Dict[str, int] = {}
    failures: Dict[str, int] = {}
    completed: Dict[str, int] = {}
    for row in rows:
        by_status[row.get("status")] = by_status.get(row.get("status"), 0) + 1
        for collector, reason in (row.get("terminal_failures") or {}).items():
            failures[f"{collector}:{reason}"] = failures.get(f"{collector}:{reason}", 0) + 1
        for collector in row.get("completed_collectors") or []:
            completed[collector] = completed.get(collector, 0) + 1
    return {
        "packets": len(rows),
        "by_status": dict(sorted(by_status.items())),
        "completed_collectors": dict(sorted(completed.items())),
        "terminal_failures": dict(sorted(failures.items())),
    }
