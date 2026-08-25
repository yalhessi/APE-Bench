"""Primitives for writing immutable release and treatment artifacts.

Thirteen modules independently hand-rolled the same four steps — write JSONL artifacts,
hash each into an `ArtifactRef`, stamp git provenance, assemble a manifest. That is why
conventions drifted (see `io.sealed_from_payload` vs `io.sealed_model`). These helpers
are the shared spelling; they change no bytes, so a release rebuilt through them is
byte-identical to one built by hand and `write_once` stays silent.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .io import (
    display_path,
    git_state,
    jsonl_bytes,
    sha256_file,
    write_once,
)
from .schema import ArtifactRef, DatasetManifest


@dataclass(frozen=True)
class ArtifactSpec:
    """One artifact to write into a release, plus the metadata its ref records."""

    rel_path: str
    rows: Sequence[Any] = ()
    schema_version: Optional[str] = None
    role: Optional[str] = None
    #: Verbatim bytes for an artifact carried unchanged from a parent release. Serializing
    #: through models would let a field normalise and change bytes the parent's manifest
    #: still vouches for; feeding raw lines to `jsonl_bytes` JSON-encodes each *string* and
    #: silently corrupts the file. Copying is the only way to copy.
    raw_bytes: Optional[bytes] = None

    @property
    def records(self) -> int:
        if self.raw_bytes is not None:
            return sum(1 for line in self.raw_bytes.splitlines() if line)
        return len(self.rows)


def artifact_ref(path: Path, root: Path, role=None, schema_version=None, records=None) -> ArtifactRef:
    """Hash a written artifact into a manifest reference, relative to its release root.

    Parameter order is `(path, root, role, schema_version, records)`, matching the
    private helper it replaces. Note that `phase9_fixed_orchestration._artifact_ref`
    takes *schema before role*, so it is deliberately not migrated onto this function —
    renaming it would silently transpose the two fields in a frozen manifest.
    """

    return ArtifactRef(
        path=path.relative_to(root).as_posix(),
        role=role,
        schema_version=schema_version,
        sha256=sha256_file(path),
        records=records,
    )


def parent_release_ref(parent: Path, *, role: str = "parent_release", records: int = 0) -> ArtifactRef:
    """Reference a parent release.

    By convention the path is the release *directory* while the hash is of its
    `manifest.json` — `verify_frozen` relies on this, so it lives in one place.
    """

    return ArtifactRef(
        path=display_path(parent),
        role=role,
        schema_version="pr4-manifest-1",
        sha256=sha256_file(parent / "manifest.json"),
        records=records,
    )


def write_artifacts(out: Path, specs: Sequence[ArtifactSpec]) -> List[ArtifactRef]:
    """Write every artifact immutably and return their manifest references."""

    refs = []
    for spec in specs:
        path = out / spec.rel_path
        write_once(
            path, spec.raw_bytes if spec.raw_bytes is not None else jsonl_bytes(spec.rows)
        )
        refs.append(artifact_ref(
            path, out,
            role=spec.role,
            schema_version=spec.schema_version,
            records=spec.records,
        ))
    return refs


def build_release(
    out: Path,
    *,
    dataset_id: str,
    release: str,
    pr_numbers: Sequence[int],
    corpus_cutoff_policy: str,
    generator_versions: Dict[str, str],
    created_at: str,
    sources: Sequence[ArtifactRef] = (),
    source_artifacts: Sequence[ArtifactSpec] = (),
    input_artifacts: Sequence[ArtifactSpec] = (),
    gold_artifacts: Sequence[ArtifactSpec] = (),
    derived_artifacts: Sequence[ArtifactSpec] = (),
    source_kind: str = "raw_event_ledger",
    split: str = "development",
) -> DatasetManifest:
    """Write a complete release directory and seal its manifest."""

    commit, tree_state = git_state()
    manifest = DatasetManifest(
        dataset_id=dataset_id,
        release=release,
        source_kind=source_kind,
        split=split,
        sources=list(sources),
        source_artifacts=write_artifacts(out, source_artifacts),
        input_artifacts=write_artifacts(out, input_artifacts),
        gold_artifacts=write_artifacts(out, gold_artifacts),
        derived_artifacts=write_artifacts(out, derived_artifacts),
        pr_numbers=list(pr_numbers),
        corpus_cutoff_policy=corpus_cutoff_policy,
        generator_git_commit=commit,
        generator_tree_state=tree_state,
        generator_versions=dict(generator_versions),
        created_at=created_at,
    )
    from .io import pretty_json_bytes

    write_once(out / "manifest.json", pretty_json_bytes(manifest))
    return manifest
