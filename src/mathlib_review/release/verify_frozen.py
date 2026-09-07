"""Verify that frozen v4 research artifacts still hash to their recorded values.

Every number this project reports is traceable to an immutable artifact, so a refactor
must be able to prove it changed no artifact. Two layers of protection:

1. **Manifest verification** — every `ArtifactRef` in every release, treatment, and run
   manifest is re-hashed and compared to its recorded `sha256`. This covers artifacts
   whose provenance is declared.
2. **Lock coverage** — `inputs/pr_review_v4/FROZEN.lock` records every file under the
   frozen roots, including the ones no manifest references (treatment registries, audit
   reports, census rows). Adding files is normal progress; *changing* a locked file is
   the alarm this module exists to raise.

`io.write_once` already refuses to overwrite an artifact with different bytes, but it
only fires when a builder reruns. This ledger is checkable at any moment, which is what
makes it usable as a per-step gate during a refactor.

Usage:
    python -m src.mathlib_review.release.verify_frozen verify
    python -m src.mathlib_review.release.verify_frozen build-lock
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

from src.mathlib_review.io import pretty_json_bytes, sha256_directory, sha256_file

FROZEN_ROOTS = (
    Path("inputs/pr_review_v4"),
    Path("results/pr_review_v4"),
)
LOCK_PATH = Path("inputs/pr_review_v4/FROZEN.lock")

# Release/run manifests carry these ArtifactRef lists; treatment manifests carry
# `derived_artifacts` plus two singleton refs handled separately.
_REF_LISTS = (
    "sources",
    "source_artifacts",
    "input_artifacts",
    "gold_artifacts",
    "derived_artifacts",
    "artifacts",
)
_SINGLETON_REFS = ("parent_dataset_manifest", "method_registry")


def _hash_any(path: Path) -> Optional[str]:
    """Hash an artifact reference target.

    Files hash directly. A ref whose path is a *directory* is a parent-release pointer,
    and by convention its recorded hash is that of the parent's `manifest.json`, not of
    the tree (see the `parent_release` source ref built in `pilot.py`). Directories
    without a manifest fall back to a content hash of the tree.
    """

    if path.is_file():
        return sha256_file(path)
    if path.is_dir():
        manifest = path / "manifest.json"
        return sha256_file(manifest) if manifest.is_file() else sha256_directory(path)
    return None


def _resolve(ref_path: str, root: Path) -> Path:
    """Refs are root-relative (`derived/x.jsonl`) or repo-root-relative (`inputs/...`)."""

    candidate = root / ref_path
    return candidate if candidate.exists() else Path(ref_path)


def iter_manifests() -> Iterator[Tuple[str, Path, Path]]:
    """Yield (kind, manifest_path, root) for every manifest under the frozen roots."""

    releases = Path("inputs/pr_review_v4/releases")
    treatments = Path("inputs/pr_review_v4/treatments")
    runs = Path("results/pr_review_v4/runs")
    for parent, kind in ((releases, "release"), (treatments, "treatment")):
        for manifest in sorted(parent.glob("*/manifest.json")):
            yield kind, manifest, manifest.parent
    for manifest in sorted(runs.glob("*/run_manifest.json")):
        yield "run", manifest, manifest.parent


def verify_manifests() -> Tuple[List[Dict], int]:
    """Re-hash every declared artifact reference. Returns (failures, refs_checked)."""

    failures: List[Dict] = []
    checked = 0
    for kind, manifest_path, root in iter_manifests():
        payload = json.loads(manifest_path.read_text())
        refs = [
            ref
            for key in _REF_LISTS
            for ref in (payload.get(key) or [])
        ]
        refs += [payload[key] for key in _SINGLETON_REFS if isinstance(payload.get(key), dict)]
        for ref in refs:
            checked += 1
            target = _resolve(ref["path"], root)
            actual = _hash_any(target)
            if actual is None:
                failures.append({
                    "kind": kind,
                    "manifest": manifest_path.as_posix(),
                    "path": ref["path"],
                    "problem": "missing",
                })
            elif actual != ref["sha256"]:
                failures.append({
                    "kind": kind,
                    "manifest": manifest_path.as_posix(),
                    "path": ref["path"],
                    "problem": "hash_mismatch",
                    "expected": ref["sha256"],
                    "actual": actual,
                })
        # Sealed run manifests additionally name their plan and dataset manifest.
        for path_key, hash_key in (
            ("run_plan_path", "run_plan_sha256"),
            ("dataset_manifest_path", "dataset_manifest_sha256"),
        ):
            if path_key not in payload:
                continue
            checked += 1
            target = _resolve(payload[path_key], root)
            actual = _hash_any(target)
            if actual != payload[hash_key]:
                failures.append({
                    "kind": kind,
                    "manifest": manifest_path.as_posix(),
                    "path": payload[path_key],
                    "problem": "missing" if actual is None else "hash_mismatch",
                    "expected": payload[hash_key],
                    "actual": actual,
                })
    return failures, checked


def _frozen_files() -> List[Path]:
    return sorted(
        path
        for root in FROZEN_ROOTS
        for path in root.rglob("*")
        if path.is_file() and path != LOCK_PATH
    )


def build_lock() -> Dict[str, str]:
    return {path.as_posix(): sha256_file(path) for path in _frozen_files()}


def verify_lock() -> Tuple[List[Dict], List[str], int]:
    """Check every locked file. Returns (failures, unlocked_paths, files_checked)."""

    if not LOCK_PATH.is_file():
        raise FileNotFoundError(
            f"{LOCK_PATH} is absent; run `build-lock` once to seal the current state"
        )
    locked: Dict[str, str] = json.loads(LOCK_PATH.read_text())["files"]
    failures = []
    for path_str, expected in sorted(locked.items()):
        path = Path(path_str)
        if not path.is_file():
            failures.append({"path": path_str, "problem": "missing"})
            continue
        actual = sha256_file(path)
        if actual != expected:
            failures.append({
                "path": path_str,
                "problem": "hash_mismatch",
                "expected": expected,
                "actual": actual,
            })
    unlocked = [path.as_posix() for path in _frozen_files() if path.as_posix() not in locked]
    return failures, unlocked, len(locked)


def verify() -> Dict:
    manifest_failures, refs_checked = verify_manifests()
    lock_failures, unlocked, files_checked = verify_lock()
    return {
        "manifest_refs_checked": refs_checked,
        "manifest_failures": manifest_failures,
        "locked_files_checked": files_checked,
        "lock_failures": lock_failures,
        "unlocked_files": unlocked,
        "status": "ok" if not (manifest_failures or lock_failures) else "drift_detected",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify frozen v4 artifacts")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("verify")
    subparsers.add_parser("build-lock")
    args = parser.parse_args()

    if args.command == "build-lock":
        files = build_lock()
        LOCK_PATH.write_bytes(pretty_json_bytes({
            "schema_version": "pr4-frozen-lock1",
            "roots": [root.as_posix() for root in FROZEN_ROOTS],
            "note": (
                "Hashes of every frozen research artifact. Adding files is normal; a "
                "changed hash means a supposedly immutable artifact was rewritten."
            ),
            "files": files,
        }))
        print(json.dumps({"lock": LOCK_PATH.as_posix(), "files": len(files)}, indent=2))
        return

    report = verify()
    print(json.dumps({
        **{key: value for key, value in report.items() if key != "unlocked_files"},
        "unlocked_files": len(report["unlocked_files"]),
    }, indent=2, default=str))
    if report["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
