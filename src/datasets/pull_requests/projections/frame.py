"""The evaluation frame and its seeded draw: which PRs the one evaluation set comes from.

The rulings behind every choice here are in `docs/todo/eval-set-selection.md`, 2026-09-24:

* The frame is every PR created in `[created_from, created_to]` (UTC, the listing's `created_at`)
  that passes the pre-gate, minus the PRs used for development. Nothing else is excluded.
  - "Used for development" is PR-level and narrow: something ran on the PR, or a frozen release,
    tier or the v2 bundle cache holds it (`DEV_USED_SOURCES`). A PR that was only collected is
    recorded, not excluded.
  - AI-generated PRs are labelled, never excluded (CLAUDE.md).
* The main stratum draws `main_size` PRs, proportional by creation month: largest remainder over
  frame members, each month walked in its own seeded order.
* The AI stratum draws `ai_size` more PRs, from members with fetch-time AI evidence (label or
  description) that are not already in the main stratum. It is reported apart, since at the
  natural rate a 50-PR draw holds about 3.
* A walk accepts a candidate only if the funnel includes it and the caps allow it. It stops at the
  first candidate without tier 2, or without base files, instead of skipping it, so collection
  never reorders the draw.

The order is `sha256(seed \\0 pr_number)`. It is a pure function of the sealed inputs, so anyone
can re-derive the draw from the committed files; no RNG state is involved.

Verbs, all free except the collection that `candidates` prints and does not run:

  frame       count the frame by month and AI evidence; writes nothing
  seal        write the pre-registration (spec, dev-used list, frame members) under
              inputs/pull_requests/evaluation/<name>/, immutable
  seal-from   the same for a second set over a sealed frame minus that frame's draw (validation
              beside test: one distribution, disjoint PRs)
  candidates  write round k's candidate list for `collect --prs` (a prefix of each seeded order)
  walk        apply funnel and caps in seed order; writes draw.json only once every stratum is full
  release     the drawn episodes as a gold-free v5 generation release (inputs/pr_review_v4/releases)
"""

from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import math
import os
import re
from multiprocessing import Pool
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Literal, Mapping, Optional, Sequence, Tuple

from pydantic import BaseModel, ConfigDict

from src.datasets.pull_requests.collect import pre_gate
from src.datasets.pull_requests.definitions import (
    DEFINITIONS_VERSION, ai_authorship_evidence, load_roster, roster_sha256,
)
from src.datasets.pull_requests.projections.episodes import project_episodes
from src.datasets.pull_requests.store import PullRequestStore
from src.mathlib_review.io import (
    canonical_json_bytes, jsonl_bytes, jsonl_rows, pretty_json_bytes, sha256_bytes, sha256_file,
    write_once,
)
from src.mathlib_review.paths import (
    MATHLIB_CLONE, PULL_REQUESTS_STORE, PULL_REQUESTS_TRACKED, assert_repo_root,
)
from src.mathlib_review.schema import ReviewEpisodeInput

FRAME_VERSION = "evaluation-frame/1"
EVALUATION_ROOT = PULL_REQUESTS_TRACKED / "evaluation"
#: Base files for gold-free change graphs, read from the local clone. Never
#: `data/pr_review_v4/cache/base_files`, which five frozen manifests hash as a tree.
BASE_FILE_CACHE = PULL_REQUESTS_STORE / "base_files"

Stratum = Literal["main", "ai"]


# --- the spec ---------------------------------------------------------------------------------

class FrameSpec(BaseModel):
    """Everything that decides the draw, fixed before any candidate's tier 2 is read."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    frame_version: Literal["evaluation-frame/1"] = FRAME_VERSION
    name: str
    created_from: str
    created_to: str
    #: The walked listing window whose tier 0 the frame reads (`collect --start/--end`).
    listing_window: Tuple[str, str]
    store_content_sha256: str
    roster_path: str
    roster_sha256: str
    definitions_version: str
    seed: str
    main_size: int
    ai_size: int
    main_target_cap: int
    ai_target_cap: int
    #: Across both strata: at most this many accepted PRs per author, and per base commit.
    per_author_cap: int
    per_base_cap: int
    #: Round k collects ceil(k * factor * quota) candidates per month, and likewise for AI.
    main_candidate_factor: float
    ai_candidate_factor: float
    #: The disclosed rules a reader needs and the code does not enforce, in words.
    rules: Dict[str, str]
    #: `<name>@<seal sha>` when this frame reuses another seal's members minus that seal's draw:
    #: a validation set drawn beside a sealed test set, from one distribution.
    frame_from: Optional[str] = None


class FrameMember(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    pr_number: int
    created_at: str
    month: str
    author: str
    #: Fetch-time evidence only (label, description): what the draw can stratify on.
    ai_evidence: Tuple[str, ...]


# --- used for development ----------------------------------------------------------------------

#: The narrow rule's sources, in scan order.
DEV_USED_SOURCES = ("runs", "v2_bundles", "tiers", "v4_releases", "proof_pr_review")
#: Only collected, never run on: disclosed, not excluded. The v1 AI dataset is 137 of the 362
#: AI-flagged pre-gate passes in Feb-Apr 2026, which is why the broad rule was not taken.
COLLECTED_NOT_USED = ("mathlib_pr_review_all_ai", "ape_bench")

_ID_RE = re.compile("|".join([
    r'"pr_number":\s*"?(\d{4,6})\b',
    r'leanprover-community/mathlib4:(\d{4,6}):',
    r'\bmathlib4_(\d{4,6})\b',
    r'\bpr_review_v\d_(\d{5})\b',
    r'\bmathlib_pr_split_(\d{4,6})_',
    r'"pr":\s*(\d{4,6})\b',
]))
_RUN_NAME_RE = re.compile(r'(?:^|_)(\d{5})(?:_|$)')
RUN_ROOTS = (Path(".ape/runs"), Path("results/pr_review_v4/runs"), Path("results/pr_review_v5/runs"))


def _numbers_in(text: str) -> set:
    return {int(next(g for g in match.groups() if g)) for match in _ID_RE.finditer(text)}


def _read(path: str, limit: Optional[int] = None) -> str:
    try:
        with open(path, errors="ignore") as handle:
            return handle.read(limit) if limit else handle.read()
    except OSError:
        return ""


def _scan_run(run_dir: str) -> Tuple[str, List[int]]:
    """PR numbers a run directory names: its name, its top-level JSON, and each task's result."""

    found = {int(m.group(1)) for m in _RUN_NAME_RE.finditer(os.path.basename(run_dir))}
    files = [os.path.join(run_dir, f) for f in os.listdir(run_dir) if f.endswith((".json", ".jsonl"))]
    files += glob.glob(os.path.join(run_dir, "*/metadata.json"))
    for path in files:
        found |= _numbers_in(_read(path))
    tasks = os.path.join(run_dir, "tasks")
    if os.path.isdir(tasks):
        for task in os.listdir(tasks):
            for path in (os.path.join(tasks, task, "task_result.json"),
                         os.path.join(tasks, task, "samples", "0", "sample.json")):
                if os.path.isfile(path):
                    found |= _numbers_in(_read(path, 400_000))
    return run_dir, sorted(found)


def _jsonl_pr_numbers(path: str) -> set:
    out = set()
    for row in jsonl_rows(Path(path)):
        for obj in (row, row.get("snapshot") or {}, row.get("metadata") if isinstance(row.get("metadata"), dict) else {}):
            if isinstance(obj, dict) and obj.get("pr_number") is not None:
                out.add(int(obj["pr_number"]))
                break
    return out


def scan_dev_used(*, processes: int = 32) -> Dict[str, object]:
    """Every PR the narrow rule counts as used for development, with its sources.

    Reads gitignored run directories, so the result is frozen into the pre-registration rather than
    re-derived. Measured 2026-09-24: 232 used, plus 195 only collected.
    """

    sources: Dict[str, set] = {}
    run_dirs = [str(root / name) for root in RUN_ROOTS if root.is_dir()
                for name in sorted(os.listdir(root)) if (root / name).is_dir()]
    with Pool(processes) as pool:
        runs = pool.map(_scan_run, run_dirs, chunksize=1)
    sources["runs"] = {n for _, prs in runs for n in prs}
    bundles = Path("data/pr_review_v2/cache/bundles")
    sources["v2_bundles"] = {int(f[3:-5]) for f in os.listdir(bundles) if re.fullmatch(r"pr_\d+\.json", f)}
    tiers = json.loads(Path("inputs/pr_review_v4/benchmarks/tiers-v1.json").read_text())
    sources["tiers"] = ({int(n) for t in tiers["tiers"].values() for k, v in t.items()
                         if k.endswith("_prs") and isinstance(v, list) for n in v}
                        | {int(n) for t in tiers["tiers"].values() for n in (t.get("additions_beyond_pilot9") or {})})
    sources["v4_releases"] = {int(n) for m in sorted(glob.glob("inputs/pr_review_v4/releases/*/manifest.json"))
                              for n in json.loads(Path(m).read_text()).get("pr_numbers") or ()}
    sources["proof_pr_review"] = set().union(*(_jsonl_pr_numbers(f) for f in sorted(glob.glob("inputs/proof_pr_review/*.jsonl"))))
    collected: Dict[str, set] = {
        "mathlib_pr_review_all_ai": set().union(*(_jsonl_pr_numbers(f) for f in sorted(glob.glob("data/mathlib_pr_review_all_ai*.jsonl")))),
        "ape_bench": set(),
    }
    for directory in ("data/ape_bench_pr_detail_cache", "data/ape_bench_pr_timeline_cache"):
        if os.path.isdir(directory):
            collected["ape_bench"] |= {int(f[:-5]) for f in os.listdir(directory) if re.fullmatch(r"\d+\.json", f)}
    for path in glob.glob("inputs/ape_bench/*.jsonl"):
        for row in jsonl_rows(Path(path)):
            refs = re.findall(r"\(#(\d{4,6})\)", (row.get("metadata") or {}).get("commit_message", ""))
            if refs:
                collected["ape_bench"].add(int(refs[-1]))
    used = sorted(set().union(*sources.values()))
    return {
        "rule": {"sources": list(DEV_USED_SOURCES), "run_roots": [str(r) for r in RUN_ROOTS],
                 "id_pattern": _ID_RE.pattern, "run_name_pattern": _RUN_NAME_RE.pattern},
        "used": used,
        "sources_by_pr": {str(n): [s for s in DEV_USED_SOURCES if n in sources[s]] for n in used},
        "collected_not_used": {name: sorted(prs - set(used)) for name, prs in collected.items()},
        "run_dirs_scanned": len(run_dirs),
    }


# --- the frame ---------------------------------------------------------------------------------

def frame_members(store: PullRequestStore, spec: FrameSpec, dev_used: Iterable[int],
                  roster: Iterable[str]) -> Tuple[List[FrameMember], Dict[str, object]]:
    """The frame, in PR order, and a report of what the created range held and why each non-member
    is out. Reads tier 0 and 1 only."""

    roster = set(roster)
    dev_used = set(dev_used)
    members, reasons = [], collections.Counter()
    by_month = collections.defaultdict(collections.Counter)
    for number in store.numbers():
        endpoints = store.ledger(number)["endpoints"]
        # The listing, else the pr endpoint: the same fallback as `pre_gate`. Seeded PRs have no listing.
        listing = next((store.read(number, name) for name in ("listing", "pr")
                        if endpoints.get(name, {}).get("present")), None)
        created = str((listing or {}).get("created_at") or "")
        if not (spec.created_from <= created[:10] <= spec.created_to):
            continue
        month = created[:7]
        passed, reason = pre_gate(store, number, roster)
        if passed and number in dev_used:
            passed, reason = False, "dev_used"
        reasons[reason] += 1
        by_month[month][reason] += 1
        if not passed:
            continue
        evidence = ai_authorship_evidence(listing.get("labels") or [], listing.get("title"), listing.get("body"))
        members.append(FrameMember(pr_number=number, created_at=created, month=month,
                                   author=str((listing.get("user") or {}).get("login") or ""),
                                   ai_evidence=tuple(sorted(evidence))))
    report = {"members": len(members), "by_reason": dict(sorted(reasons.items())),
              "by_month": {m: dict(sorted(c.items())) for m, c in sorted(by_month.items())},
              "ai_members": sum(1 for m in members if m.ai_evidence)}
    return members, report


# --- the order ---------------------------------------------------------------------------------

def draw_key(seed: str, number: int) -> str:
    return hashlib.sha256(f"{seed}\0{number}".encode("utf-8")).hexdigest()


def seeded_order(members: Iterable[FrameMember], seed: str) -> List[FrameMember]:
    return sorted(members, key=lambda m: draw_key(seed, m.pr_number))


def month_quotas(members: Sequence[FrameMember], size: int) -> Dict[str, int]:
    """Proportional allocation by largest remainder; ties go to the earlier month."""

    counts = collections.Counter(m.month for m in members)
    total = sum(counts.values())
    exact = {month: size * n / total for month, n in counts.items()}
    quotas = {month: math.floor(value) for month, value in exact.items()}
    by_remainder = sorted(exact, key=lambda month: (-(exact[month] - quotas[month]), month))
    for month in by_remainder[: size - sum(quotas.values())]:
        quotas[month] += 1
    return dict(sorted(quotas.items()))


def strata_orders(spec: FrameSpec, members: Sequence[FrameMember]) -> Dict[str, List[FrameMember]]:
    """`main:<month>` for each month, and `ai`, each in seeded order."""

    ordered = seeded_order(members, spec.seed)
    orders = {f"main:{month}": [m for m in ordered if m.month == month]
              for month in month_quotas(members, spec.main_size)}
    orders["ai"] = [m for m in ordered if m.ai_evidence]
    return orders


def candidates(spec: FrameSpec, members: Sequence[FrameMember], round_index: int) -> Dict[str, List[int]]:
    """Round k's candidates: a prefix of each stratum's order, k times the base length. Round k+1
    extends round k, so a walk that runs out needs only the next round collected."""

    quotas = month_quotas(members, spec.main_size)
    out = {}
    for key, order in strata_orders(spec, members).items():
        slots = quotas[key.split(":", 1)[1]] if key.startswith("main:") else spec.ai_size
        factor = spec.main_candidate_factor if key.startswith("main:") else spec.ai_candidate_factor
        out[key] = [m.pr_number for m in order[: math.ceil(round_index * factor * slots)]]
    return out


# --- the walk ----------------------------------------------------------------------------------

class Accepted(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    pr_number: int
    stratum: str
    month: str
    author: str
    episode_id: str
    base_sha: str
    targets: int
    #: With tier 2's commits: label, description and trailer. For labelling and filtering only.
    ai_evidence: Tuple[str, ...]


class Skipped(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    pr_number: int
    stratum: str
    reason: str


class Draw(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frame_seal_sha256: str
    accepted: List[Accepted]
    skipped: List[Skipped]
    #: Per stratum: None if full, else why the walk stopped and at which PR.
    stopped: Dict[str, Optional[Dict[str, object]]]

    @property
    def complete(self) -> bool:
        return all(value is None for value in self.stopped.values())


def change_targets(episode: ReviewEpisodeInput, *, cache_root: Path = BASE_FILE_CACHE,
                   clone: Path = MATHLIB_CLONE) -> Optional[int]:
    """Gold-free change-target count, from base files read out of the local clone. None when a base
    file is not in the clone: the cap cannot be decided, and the walk stops rather than guess."""

    from src.mathlib_review.release.change_graph import build_change_graph, hydrate_blob_cache_from_git

    counts = hydrate_blob_cache_from_git(episode, cache_root=cache_root, clone=clone)
    if counts["missing"]:
        return None
    graph = build_change_graph(episode, workspace_root=cache_root / "_no_workspaces",
                               blob_cache_root=cache_root)
    return len(graph.targets)


def walk(spec: FrameSpec, members: Sequence[FrameMember], *, store: PullRequestStore,
         roster: Iterable[str], frame_seal_sha256: str,
         targets_of: Callable[[ReviewEpisodeInput], Optional[int]] = change_targets,
         replaced: Mapping[int, str] = {}) -> Draw:
    """Accept candidates in seed order, main stratum month by month and then AI. `replaced` names
    accepted PRs taken out afterwards (a reviewed state that does not compile), with the reason."""

    roster = set(roster)
    quotas = month_quotas(members, spec.main_size)
    orders = strata_orders(spec, members)
    accepted: List[Accepted] = []
    skipped: List[Skipped] = []
    stopped: Dict[str, Optional[Dict[str, object]]] = {}
    per_author: collections.Counter = collections.Counter()
    per_base: collections.Counter = collections.Counter()

    for key, order in orders.items():
        slots = quotas[key.split(":", 1)[1]] if key.startswith("main:") else spec.ai_size
        cap = spec.main_target_cap if key.startswith("main:") else spec.ai_target_cap
        taken = 0
        stopped[key] = {"reason": "order_exhausted", "at": None, "accepted": 0}
        for position, member in enumerate(order):
            if taken == slots:
                stopped[key] = None
                break
            number = member.pr_number

            def skip(reason: str) -> None:
                skipped.append(Skipped(pr_number=number, stratum=key, reason=reason))

            if key == "ai" and any(a.pr_number == number for a in accepted):
                skip("in_main")
                continue
            if 2 not in store.tiers(number):
                stopped[key] = {"reason": "needs_collection", "at": number, "position": position,
                                "accepted": taken}
                break
            projection = project_episodes(store, roster=roster, prs=[number])
            if not projection.episodes:
                skip(f"funnel:{projection.funnel[0].reason}")
                continue
            episode = projection.episodes[0]
            if number in replaced:
                skip(f"replaced:{replaced[number]}")
                continue
            targets = targets_of(episode)
            if targets is None:
                stopped[key] = {"reason": "needs_base", "at": number, "base_sha": episode.base_sha,
                                "position": position, "accepted": taken}
                break
            if targets > cap:
                skip(f"targets>{cap}")
                continue
            if per_author[member.author] >= spec.per_author_cap:
                skip("author_cap")
                continue
            if per_base[episode.base_sha] >= spec.per_base_cap:
                skip("base_cap")
                continue
            commits = store.read(number, "commits") or []
            pr = store.read(number, "pr") or {}
            evidence = ai_authorship_evidence(pr.get("labels") or [], pr.get("title"), pr.get("body"), commits)
            accepted.append(Accepted(
                pr_number=number, stratum=key, month=member.month, author=member.author,
                episode_id=episode.episode_id, base_sha=episode.base_sha, targets=targets,
                ai_evidence=tuple(sorted(set(evidence) | set(member.ai_evidence)))))
            per_author[member.author] += 1
            per_base[episode.base_sha] += 1
            taken += 1
        else:
            if taken == slots:
                stopped[key] = None
        if stopped[key] is not None:
            stopped[key]["accepted"] = taken
    return Draw(frame_seal_sha256=frame_seal_sha256, accepted=accepted, skipped=skipped, stopped=stopped)


# --- the sealed pre-registration ------------------------------------------------------------------

def seal_dir(name: str, root: Path = EVALUATION_ROOT) -> Path:
    return root / name


def seal(spec: FrameSpec, dev_used: Mapping[str, object], members: Sequence[FrameMember],
         report: Mapping[str, object], *, root: Path = EVALUATION_ROOT) -> str:
    """Write the pre-registration once; identical regeneration is a no-op, a different one raises."""

    out = seal_dir(spec.name, root)
    files = {
        "spec.json": pretty_json_bytes(spec.model_dump(mode="json")),
        "dev_used.json": pretty_json_bytes(dev_used),
        "frame.jsonl": jsonl_bytes([m.model_dump(mode="json") for m in members]),
        "frame_report.json": pretty_json_bytes(report),
    }
    digests = {name: sha256_bytes(content) for name, content in files.items()}
    seal_sha = sha256_bytes(canonical_json_bytes({"frame_version": FRAME_VERSION, "files": digests}))
    for name, content in files.items():
        write_once(out / name, content)
    write_once(out / "seal.json", pretty_json_bytes({"frame_version": FRAME_VERSION, "files": digests,
                                                     "seal_sha256": seal_sha}))
    return seal_sha


def load_sealed(name: str, root: Path = EVALUATION_ROOT) -> Tuple[FrameSpec, List[FrameMember], str]:
    """The sealed spec and members, refusing a file that no longer matches its recorded digest."""

    out = seal_dir(name, root)
    record = json.loads((out / "seal.json").read_text(encoding="utf-8"))
    for filename, digest in record["files"].items():
        if sha256_file(out / filename) != digest:
            raise ValueError(f"{out / filename} no longer matches its sealed digest")
    spec = FrameSpec.model_validate_json((out / "spec.json").read_text(encoding="utf-8"))
    members = [FrameMember.model_validate(row) for row in jsonl_rows(out / "frame.jsonl")]
    return spec, members, record["seal_sha256"]


# --- the generation release -------------------------------------------------------------------

EVALUATION_DATASET_ID = "mathlib-pr-review-evaluation"
DEFAULT_RENDERER = "candidate-prompt/14"


def write_evaluation_release(out: Path, spec: FrameSpec, draw: Draw, *, store: PullRequestStore,
                             seal_path: Path, renderer_version: str = DEFAULT_RENDERER,
                             cache_root: Path = BASE_FILE_CACHE):
    """The drawn episodes as a release a v5 config can run: episodes, source events, change graphs,
    work units, rendered prompts, the modification inventory, and the strata labels. No gold.

    Change graphs are built once, from git-hydrated base files and an empty workspace root, so
    their ids do not depend on which workspaces happen to exist. A child release at another
    renderer is a `rerender_release` of this one.
    """

    from datetime import datetime, timezone

    from src.datasets.pull_requests.projections.episodes import REPO
    from src.mathlib_review.agenda.render_prompts import render_all
    from src.mathlib_review.io import display_path
    from src.mathlib_review.release.change_graph import (
        CHANGE_GRAPH_BUILDER_VERSION, build_change_graph, hydrate_blob_cache_from_git,
    )
    from src.mathlib_review.release.episode_builder import RAW_EPISODE_BUILDER_VERSION
    from src.mathlib_review.release.events import STORE_EVENT_LEDGER_VERSION
    from src.mathlib_review.release.modification_inventory import (
        INVENTORY_VERSION, build_inventory, validate_inventory,
    )
    from src.mathlib_review.release.releases import ArtifactSpec, build_release
    from src.mathlib_review.release.work_units import (
        WORK_UNIT_VERSION, build_work_units, validate_work_unit_coverage,
    )
    from src.mathlib_review.schema import ArtifactRef
    from src.datasets.pull_requests.store import STORE_VERSION

    if not draw.complete:
        raise ValueError("the draw is not complete; a release is built from a finished walk only")
    roster_path = Path(spec.roster_path)
    prs = sorted(a.pr_number for a in draw.accepted)
    projection = project_episodes(store, roster=load_roster(roster_path), prs=prs, repo=REPO)
    by_pr = {episode.pr_number: episode for episode in projection.episodes}
    for accepted in draw.accepted:
        episode = by_pr.get(accepted.pr_number)
        if episode is None or episode.episode_id != accepted.episode_id:
            raise ValueError(f"PR {accepted.pr_number} no longer projects to the drawn episode")
    graphs = []
    for episode in projection.episodes:
        if hydrate_blob_cache_from_git(episode, cache_root=cache_root, clone=MATHLIB_CLONE)["missing"]:
            raise ValueError(f"PR {episode.pr_number}: base files missing from the clone")
        graphs.append(build_change_graph(episode, workspace_root=cache_root / "_no_workspaces",
                                         blob_cache_root=cache_root))
    units = build_work_units(graphs, renderer_version=renderer_version)
    validate_work_unit_coverage(graphs, units)
    prompts = render_all(units, projection.episodes, graphs, [])
    inventory = build_inventory(graphs)
    validate_inventory(graphs, inventory)
    strata = [{"pr_number": a.pr_number, "stratum": a.stratum, "month": a.month, "author": a.author,
               "ai_evidence": list(a.ai_evidence), "targets": a.targets}
              for a in sorted(draw.accepted, key=lambda a: a.pr_number)]
    return build_release(
        out, dataset_id=EVALUATION_DATASET_ID, release=spec.name, pr_numbers=prs,
        corpus_cutoff_policy="No historical review corpus is visible during generation.",
        generator_versions={
            "frame": FRAME_VERSION, "episodes": RAW_EPISODE_BUILDER_VERSION,
            "funnel": RAW_EPISODE_BUILDER_VERSION, "events": STORE_EVENT_LEDGER_VERSION,
            "store": STORE_VERSION, "definitions": spec.definitions_version,
            "change_graph": CHANGE_GRAPH_BUILDER_VERSION, "work_units": WORK_UNIT_VERSION,
            "renderer": renderer_version, "inventory": INVENTORY_VERSION,
        },
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        sources=[
            ArtifactRef(path=display_path(store.root), role="pull_request_store",
                        sha256=store.content_digest(), records=len(prs)),
            ArtifactRef(path=display_path(roster_path), role="reviewer_roster",
                        sha256=roster_sha256(roster_path), records=len(load_roster(roster_path))),
            ArtifactRef(path=display_path(seal_path), role="evaluation_seal",
                        sha256=sha256_file(seal_path), records=len(draw.accepted)),
        ],
        source_artifacts=[ArtifactSpec("source/events.jsonl", projection.events, "event1", "raw_event_index")],
        input_artifacts=[ArtifactSpec("input/episodes.jsonl", projection.episodes, "episode1",
                                      "reviewer_visible_episodes")],
        gold_artifacts=[ArtifactSpec("gold/episode_boundaries.jsonl", projection.boundaries,
                                     "episode-boundary1", "hidden_episode_boundaries")],
        derived_artifacts=[
            ArtifactSpec("derived/funnel.jsonl", projection.funnel, "funnel1", "eligibility_funnel"),
            ArtifactSpec("derived/change_graphs.jsonl", graphs, "cg1", "complete_change_graphs"),
            ArtifactSpec("derived/work_units.jsonl", units, "work-unit1", "candidate_work_units"),
            ArtifactSpec("derived/rendered_prompts.jsonl", prompts, "rendered-prompt1",
                         "production_prompt_preview"),
            ArtifactSpec("derived/modification_inventory.jsonl", inventory, "modification1",
                         "modification_inventory"),
            ArtifactSpec("derived/evaluation_strata.jsonl", strata, "evaluation-strata1",
                         "strata_and_ai_labels"),
        ],
        split="test",
    )


def derived_frame(parent: str, root: Path = EVALUATION_ROOT):
    """A sealed frame's members minus its completed draw, with the parent's spec, dev-used record
    and the reserved PRs. This is how a second set is drawn from the same distribution without
    touching the first."""

    parent_spec, parent_members, parent_seal = load_sealed(parent, root)
    draw = Draw.model_validate_json((seal_dir(parent, root) / "draw.json").read_text(encoding="utf-8"))
    if not draw.complete or draw.frame_seal_sha256 != parent_seal:
        raise ValueError(f"{parent}'s draw is incomplete or not of its seal")
    reserved = sorted(a.pr_number for a in draw.accepted)
    members = [m for m in parent_members if m.pr_number not in set(reserved)]
    dev_used = json.loads((seal_dir(parent, root) / "dev_used.json").read_text(encoding="utf-8"))
    return parent_spec, parent_seal, members, dev_used, reserved


# --- CLI --------------------------------------------------------------------------------------

def _spec_from_args(args: argparse.Namespace, store: PullRequestStore) -> FrameSpec:
    return FrameSpec(
        name=args.name, created_from=args.created_from, created_to=args.created_to,
        listing_window=(args.window_start, args.window_end),
        store_content_sha256=store.content_digest(),
        roster_path=str(args.roster), roster_sha256=roster_sha256(args.roster),
        definitions_version=DEFINITIONS_VERSION, seed=args.seed,
        main_size=args.main_size, ai_size=args.ai_size,
        main_target_cap=args.main_target_cap, ai_target_cap=args.ai_target_cap,
        per_author_cap=args.per_author_cap, per_base_cap=args.per_base_cap,
        main_candidate_factor=args.main_candidate_factor, ai_candidate_factor=args.ai_candidate_factor,
        rules=dict(RULES),
    )


#: What the code does not enforce, stated so a reader cannot miss it.
RULES = {
    "ai": "AI-generated PRs are labelled, never excluded. The AI stratum is drawn from fetch-time "
          "evidence (label or description) and reported apart from the main stratum.",
    "closed_unmerged": "Kept, with the count reported. 'Abandoned' cannot be told from 'rejected' "
                       "or 'superseded' without gold.",
    "size_gates": "The funnel's final-state gates (1..30 files, 10..800 lines) bound the frame; "
                  "they are not strata.",
    "censoring": "PRs still open at the 2026-09-11 listing walk are outside the frame.",
    "roster": "One dated roster for every month.",
    "replacement": "An accepted episode whose reviewed state does not compile (prebuild --reviewed "
                   "fails on a Lean error in a changed file) is replaced by continuing its "
                   "stratum's walk, and each replacement is recorded with its error.",
    "order": "Within a stratum, candidates are walked in sha256(seed \\0 pr_number) order; the "
             "walk stops at the first candidate without tier 2 or base files, and never skips it.",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="verb", required=True)
    for verb in ("frame", "seal"):
        p = sub.add_parser(verb)
        p.add_argument("--name", required=True)
        p.add_argument("--created-from", required=True)
        p.add_argument("--created-to", required=True)
        p.add_argument("--window-start", default="2024-03-01")
        p.add_argument("--window-end", default="2026-08-31")
        p.add_argument("--roster", type=Path, default=PULL_REQUESTS_TRACKED / "rosters/mathlib_roster_2026-09-11.txt")
        p.add_argument("--seed", required=True)
        p.add_argument("--main-size", type=int, default=50)
        p.add_argument("--ai-size", type=int, default=10)
        p.add_argument("--main-target-cap", type=int, default=100)
        p.add_argument("--ai-target-cap", type=int, default=150)
        p.add_argument("--per-author-cap", type=int, default=3)
        p.add_argument("--per-base-cap", type=int, default=2)
        p.add_argument("--main-candidate-factor", type=float, default=2.0)
        p.add_argument("--ai-candidate-factor", type=float, default=3.5)
    p = sub.add_parser("seal-from", help="seal a second set over another seal's frame minus its draw")
    p.add_argument("--name", required=True)
    p.add_argument("--from", dest="parent", required=True)
    p.add_argument("--seed", required=True)
    p.add_argument("--dry-run", action="store_true")
    for flag, kind in (("--main-size", int), ("--ai-size", int), ("--main-target-cap", int),
                       ("--ai-target-cap", int), ("--per-author-cap", int), ("--per-base-cap", int),
                       ("--main-candidate-factor", float), ("--ai-candidate-factor", float)):
        p.add_argument(flag, type=kind, default=None, help="default: the parent's")
    p = sub.add_parser("candidates")
    p.add_argument("--name", required=True)
    p.add_argument("--round", type=int, required=True)
    p = sub.add_parser("release")
    p.add_argument("--name", required=True)
    p.add_argument("--renderer", default=DEFAULT_RENDERER)
    p.add_argument("--out", type=Path, default=None, help="default: inputs/pr_review_v4/releases/<name>")
    p = sub.add_parser("walk")
    p.add_argument("--name", required=True)
    p.add_argument("--replaced", type=Path, default=None,
                   help="JSON object {pr_number: reason} of accepted PRs taken out after prebuild")
    args = parser.parse_args()
    assert_repo_root()

    if args.verb in ("frame", "seal"):
        store = PullRequestStore()
        spec = _spec_from_args(args, store)
        dev_used = scan_dev_used()
        members, report = frame_members(store, spec, dev_used["used"], load_roster(args.roster))
        report["main_quotas"] = month_quotas(members, spec.main_size)
        print(json.dumps({"spec": spec.model_dump(mode="json"), "dev_used": len(dev_used["used"]),
                          "collected_not_used": {k: len(v) for k, v in dev_used["collected_not_used"].items()},
                          **report}, indent=1))
        if args.verb == "seal":
            digest = seal(spec, dev_used, members, report)
            print(f"sealed {seal_dir(spec.name)} {digest}")
        return

    if args.verb == "seal-from":
        parent_spec, parent_seal, members, dev_used, reserved = derived_frame(args.parent)
        overrides = {key: getattr(args, key) for key in (
            "main_size", "ai_size", "main_target_cap", "ai_target_cap", "per_author_cap",
            "per_base_cap", "main_candidate_factor", "ai_candidate_factor") if getattr(args, key) is not None}
        frame_from = f"{args.parent}@{parent_seal}"
        spec = parent_spec.model_copy(update={
            "name": args.name, "seed": args.seed, "frame_from": frame_from, **overrides,
            "rules": {**parent_spec.rules, "frame_from": (
                f"Members are {args.parent}'s sealed frame minus the {len(reserved)} PRs its draw "
                "accepted, which are reserved to it; same rules, caps and strata, new seed.")}})
        spec = FrameSpec.model_validate(spec.model_dump())
        report = {"members": len(members), "ai_members": sum(1 for m in members if m.ai_evidence),
                  "frame_from": frame_from, "reserved_prs": reserved,
                  "main_quotas": month_quotas(members, spec.main_size)}
        print(json.dumps({"spec": spec.model_dump(mode="json"), **report}, indent=1))
        if not args.dry_run:
            digest = seal(spec, dev_used, members, report)
            print(f"sealed {seal_dir(spec.name)} {digest}")
        return

    spec, members, seal_sha = load_sealed(args.name)
    if args.verb == "candidates":
        lists = candidates(spec, members, args.round)
        numbers = sorted({n for prs in lists.values() for n in prs})
        path = seal_dir(spec.name) / f"candidates-r{args.round}.txt"
        header = f"# {spec.name} round {args.round}, seal {seal_sha}\n"
        write_once(path, (header + "".join(f"{n}\n" for n in numbers)).encode("utf-8"))
        print(json.dumps({k: len(v) for k, v in lists.items()}, indent=1))
        print(f"{len(numbers)} candidates -> {path}")
        print("collect with: ape/bin/python -m src.datasets.pull_requests.collect "
              f"--start {spec.listing_window[0]} --end {spec.listing_window[1]} --tier 2 "
              f"--roster {spec.roster_path} --prs {path}")
        return

    if args.verb == "release":
        from src.mathlib_review.paths import V4_RELEASES

        draw = Draw.model_validate_json((seal_dir(spec.name) / "draw.json").read_text(encoding="utf-8"))
        out = args.out or V4_RELEASES / spec.name
        manifest = write_evaluation_release(out, spec, draw, store=PullRequestStore(),
                                            seal_path=seal_dir(spec.name) / "seal.json",
                                            renderer_version=args.renderer)
        print(json.dumps({"release": str(out), "prs": len(manifest.pr_numbers),
                          "derived": {ref.path: ref.records for ref in manifest.derived_artifacts}}, indent=1))
        return

    store = PullRequestStore()
    replaced = {int(k): v for k, v in json.loads(args.replaced.read_text()).items()} if args.replaced else {}
    draw = walk(spec, members, store=store, roster=load_roster(Path(spec.roster_path)),
                frame_seal_sha256=seal_sha, replaced=replaced)
    summary = {"accepted": collections.Counter(a.stratum.split(":")[0] for a in draw.accepted),
               "skipped": collections.Counter(s.reason.split(":")[0] for s in draw.skipped),
               "stopped": {k: v for k, v in draw.stopped.items() if v is not None}}
    print(json.dumps(summary, indent=1, default=str))
    if draw.complete:
        suffix = "-replaced" if replaced else ""
        path = seal_dir(spec.name) / f"draw{suffix}.json"
        write_once(path, pretty_json_bytes(draw.model_dump(mode="json")))
        print(f"complete -> {path}")


if __name__ == "__main__":
    main()
