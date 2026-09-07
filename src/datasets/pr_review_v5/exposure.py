"""How much of the library leans on a declaration — the half of importance a PR cannot see.

PR centrality (`components.centrality`) answers "is this what the PR is about". It cannot
answer the other question a maintainer asks first: *is this someone else's widely-used code,
touched in passing?* A two-line change to a definition three thousand modules depend on
deserves more scrutiny than a rewrite of a lemma nothing imports, and nothing in the diff
says which is which.

**Where the data comes from.** Every built Lean module ships a `.ilean` index next to its
`.olean`, carrying three things: `decls` (what this module defines, with spans),
`references` (every symbol it mentions, keyed by defining module and name) and
`directImports`. Inverting `references` gives, for each declaration, how many modules
reference it; `directImports` gives the import graph for reach.

**Why not the language server.** `textDocument/references` is the obvious tool and the wrong
one: measured against a fully built snapshot, asking for references to `Ordinal.nfpFamily`
returned 27 hits, *all in the single open file*. Lean answers references from the files the
server has loaded, so library-wide reach would mean opening ~7400 files per query. The
`.ilean` scan covers the same snapshot in 3.7 seconds with no server at all.

**Abstention.** A partial build produces a partial index, and a reach of zero read off a
partial index is indistinguishable from a declaration nothing uses — the same trap
`LazyPopulationScan` documents for the naming corpus. So the scan checks its own coverage
against the source tree and resolves to `None` when the build is incomplete, and every
consumer treats `None` as "unknown", never as zero.

**This index is the BASE commit's, and it cannot quietly be made the PR's.**

Three states could in principle be measured, and only the first exists:

* *base* — what the library depended on before the PR. This is what we read, and it is the
  right question for importance: the risk a PR incurs is a function of the public surface it
  is touching, which is a pre-PR fact. A declaration the PR *adds* correctly scores 0.
* *reviewed* (PR head) — not built. The PR head is materialised by patching a base snapshot,
  never recompiled, so no `.ilean` exists for it.
* *post-edit* — what a proposed edit would leave behind. Would need a rebuild per edit.

The trap is that the second looks available and is not: **an attempt's `workspaces/target/.lake`
is a symlink straight to the base snapshot's `.lake`**, verified on a real run. So pointing
this scan at a reviewed workspace returns the *base* index while appearing PR-specific, and
nothing would look wrong. That is why `snapshot_workspace(base_sha)` is named explicitly at
every call site rather than reusing the reviewed workspace the evidence chain already has.

For the question "if the agent renames this, what breaks?", base reach is the honest
estimate available: the overwhelming majority of referencing modules lie outside the PR. On a
migration PR it *overstates* remaining breakage, because the PR is itself updating call
sites — which is the conservative direction for a caution signal. Anything sharper needs a
build of the reviewed state, and that is a separate piece of work, not a parameter change.
"""

from __future__ import annotations

import json
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

#: A build with fewer `.ilean` than this fraction of its `.lean` sources is partial, and a
#: reach measured from it would understate every declaration by an unknown amount.
MIN_INDEX_COVERAGE = 0.8

#: Reach at or above this many referencing modules marks a declaration as library-exposed.
#: Calibrated against the heldout set, where the declarations PRs actually touched sit
#: between 0 (new in the PR) and ~10, while library primitives run to thousands.
DEFAULT_EXPOSURE_FLOOR = 5


@dataclass(frozen=True)
class ExposureScan:
    """One snapshot's reference index, already inverted."""

    snapshot: str
    modules: int
    #: declaration fullname -> how many modules reference it
    referencing_modules: Dict[str, int]
    #: declaration fullname -> the module that defines it
    defining_module: Dict[str, str]
    #: module -> the modules it imports directly
    direct_imports: Dict[str, List[str]]

    def reach(self, name: str) -> int:
        """Modules that reference this declaration by name. 0 means "nothing references it"."""

        return self.referencing_modules.get(name, 0)

    def reverse_import_reach(self, name: str) -> Optional[int]:
        """How many modules sit transitively downstream of the one defining `name`.

        The broader measure: a declaration in a module that half of Mathlib imports is
        exposed even when few modules name it directly, because anything there is on the
        critical path. `None` when the defining module is unknown.
        """

        module = self.defining_module.get(name)
        if module is None:
            return None
        downstream: Set[str] = set()
        queue = deque([module])
        while queue:
            current = queue.popleft()
            for importer in self._importers.get(current, ()):  # type: ignore[attr-defined]
                if importer not in downstream:
                    downstream.add(importer)
                    queue.append(importer)
        return len(downstream)

    def __post_init__(self) -> None:
        importers: Dict[str, List[str]] = {}
        for module, imports in self.direct_imports.items():
            for imported in imports:
                importers.setdefault(imported, []).append(module)
        object.__setattr__(self, "_importers", importers)


def _scan(workspace: Path) -> Optional[ExposureScan]:
    build = workspace / ".lake" / "build" / "lib" / "lean"
    if not build.is_dir():
        return None
    ilean = sorted(build.rglob("*.ilean"))
    sources = sum(1 for _ in (workspace / "Mathlib").rglob("*.lean")) \
        if (workspace / "Mathlib").is_dir() else 0
    # Coverage, not presence: a build that stopped a third of the way through still has a
    # `.lake/build` directory full of real index files.
    if not ilean or (sources and len(ilean) < sources * MIN_INDEX_COVERAGE):
        return None

    referencing: Counter = Counter()
    defining: Dict[str, str] = {}
    imports: Dict[str, List[str]] = {}
    for path in ilean:
        try:
            payload = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        module = payload.get("module")
        if not module:
            continue
        imports[module] = [row[0] for row in (payload.get("directImports") or [])
                           if isinstance(row, list) and row]
        for name in (payload.get("decls") or {}):
            defining[name] = module
        # One module referencing a name ten times is one module, not ten: exposure is
        # breadth of dependence, and a single heavy user is not the same risk as ten light
        # ones.
        seen: Set[str] = set()
        for key in (payload.get("references") or {}):
            try:
                name = json.loads(key)["c"]["n"]
            except (ValueError, KeyError, TypeError):
                continue
            if name not in seen:
                seen.add(name)
                referencing[name] += 1
    return ExposureScan(
        snapshot=str(workspace), modules=len(imports),
        referencing_modules=dict(referencing), defining_module=defining,
        direct_imports=imports,
    )


class LazyExposureScan:
    """Built on first use and shared across every candidate in a run.

    Same contract as `evidence.LazyPopulationScan`, deliberately: lazy because a run with no
    importance question should not pay for the scan, cached because the answer is a property
    of the snapshot rather than of the caller, and abstaining because a partial index is not
    a small index — it is a wrong one.
    """

    def __init__(self, workspace: Optional[Path], cache: Dict[str, object]):
        self._workspace = workspace
        self._cache = cache

    def scan(self) -> Optional[ExposureScan]:
        if self._workspace is None:
            return None
        key = str(self._workspace)
        if key not in self._cache:
            try:
                self._cache[key] = _scan(Path(self._workspace))
            except OSError:
                self._cache[key] = None
        return self._cache[key]  # type: ignore[return-value]

    def available(self) -> bool:
        """Whether a scan could be built, so absence is not read as a finding."""

        return self.scan() is not None

    def reach(self, name: str) -> Optional[int]:
        """Referencing modules, or `None` when no complete index is available."""

        scan = self.scan()
        return None if scan is None else scan.reach(name)


def exposed_changes(
    subjects_by_change: Dict[str, str],
    scan: LazyExposureScan,
    *,
    floor: int = DEFAULT_EXPOSURE_FLOOR,
) -> Dict[str, int]:
    """`change_id -> reach`, for the changes the library actually leans on.

    Returns an empty mapping when no index is available, so a caller that merges this into
    an importance set degrades to PR-local signals rather than treating every declaration as
    unexposed.
    """

    if not scan.available():
        return {}
    out: Dict[str, int] = {}
    for change_id, subject in subjects_by_change.items():
        if not subject:
            continue
        reach = scan.reach(subject)
        if reach is not None and reach >= floor:
            out[change_id] = reach
    return out


def exposure_report(scan: LazyExposureScan, subjects: Iterable[str]) -> Dict[str, object]:
    """What the index knows about the declarations this run touches."""

    built = scan.scan()
    if built is None:
        return {"available": False,
                "reason": "no complete .ilean index for this snapshot; exposure abstains"}
    reaches = {name: built.reach(name) for name in sorted(set(subjects)) if name}
    return {
        "available": True,
        "modules_indexed": built.modules,
        "declarations_indexed": len(built.defining_module),
        "touched_declarations": len(reaches),
        "exposed_at_or_above_floor": sum(
            1 for value in reaches.values() if value >= DEFAULT_EXPOSURE_FLOOR),
        "max_reach": max(reaches.values()) if reaches else 0,
    }
