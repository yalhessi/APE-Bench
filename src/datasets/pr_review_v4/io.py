"""Canonical serialization, hashing, and immutable artifact writes."""

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable

from pydantic import BaseModel


def _plain(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=False)
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        _plain(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(_plain(value), ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(
        "utf-8"
    )


def jsonl_bytes(rows: Iterable[Any]) -> bytes:
    return b"".join(canonical_json_bytes(row) + b"\n" for row in rows)


def extract_json_object(text: str) -> Dict[str, Any]:
    """Extract the first JSON object from raw model output (fences/prose tolerated).

    Promoted from the v2 pipeline so that v4 carries no import edge to an earlier
    generation; the behaviour is deliberately identical, since cached judge verdicts
    were parsed with it.
    """

    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    decoder = json.JSONDecoder()
    for start in range(len(cleaned)):
        if cleaned[start] != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(cleaned[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    raise ValueError("no JSON object found in response")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_directory(path: Path) -> str:
    """Hash relative names and contents, independent of filesystem traversal order."""
    digest = hashlib.sha256()
    for file_path in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = file_path.relative_to(path).as_posix().encode("utf-8")
        digest.update(len(rel).to_bytes(8, "big"))
        digest.update(rel)
        file_hash = sha256_file(file_path).encode("ascii")
        digest.update(file_hash)
    return digest.hexdigest()


def load_jsonl(path: Path, cls):
    """Parse a JSONL artifact into pydantic records.

    Blank and whitespace-only lines are skipped. Artifacts written by `jsonl_bytes`
    never contain them, so this only ever turns a would-be crash into a clean parse.
    """

    return [
        cls.model_validate_json(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def load_jsonl_optional(path: Path, cls):
    """Like `load_jsonl`, but an absent artifact reads as empty rather than raising."""

    return load_jsonl(path, cls) if path.is_file() else []


def display_path(path: Path) -> str:
    """Render a path for storage in a manifest.

    Relative to the working directory when possible, which is why v4 tooling must run
    from the repo root (`paths.assert_repo_root`); absolute otherwise so the reference
    is never ambiguous.
    """

    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def git_state() -> tuple:
    """Return (commit, "clean"|"dirty"|"unknown") for provenance stamping."""

    import subprocess

    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"], check=True, capture_output=True, text=True
        ).stdout
        return commit, "dirty" if dirty.strip() else "clean"
    except (OSError, subprocess.CalledProcessError):
        return None, "unknown"


def sealed_from_payload(cls, prefix: str, payload: Dict[str, Any]):
    """Seal a record by hashing its payload; the digest also names the record.

    One of two sealing conventions in this package, and **not** interchangeable with
    `sealed_model`: this hashes only the caller's payload, whereas `sealed_model` hashes
    the constructed model including schema defaults. The two produce different digests
    for the same logical record, so a record must keep the convention it was frozen
    under or its `source_sha256` changes.
    """

    digest = sha256_bytes(canonical_json_bytes(payload))
    return cls(source_sha256=digest, **{f"{prefix}_id": f"{prefix}:{digest[:24]}", **payload})


def sealed_model(cls, **values):
    """Seal a record by hashing the fully constructed model, minus its own hash field.

    The caller supplies the record's ID. See `sealed_from_payload` for why the two
    conventions must not be merged.
    """

    draft = cls(source_sha256="", **values)
    identity = draft.model_dump(mode="json", exclude={"source_sha256"})
    return draft.model_copy(update={"source_sha256": sha256_bytes(canonical_json_bytes(identity))})


#: Placeholder for the throwaway `.lean` file a Lean subprocess was handed.
#:
#: Lean reports diagnostics against the file it compiled, and that file's name is random.
#: Any artifact that stores raw diagnostics therefore re-hashes on every run, which silently
#: destroys byte-reproducibility of everything derived from it. Every site that compiles a
#: temporary file must substitute this before the output is stored or truncated. The target
#: is always identified by the artifact's own `source_ref`, so the path carries no
#: information.
COMPILED_TARGET = "<compiled-target>"


def write_once(path: Path, content: bytes) -> bool:
    """Atomically create a release artifact; identical regeneration is a no-op."""
    if path.exists():
        if path.read_bytes() != content:
            raise FileExistsError(f"immutable artifact already exists with different content: {path}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as fh:
            tmp_name = fh.name
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        try:
            os.link(tmp_name, path)
            return True
        except FileExistsError:
            if path.read_bytes() != content:
                raise FileExistsError(
                    f"immutable artifact already exists with different content: {path}"
                )
            return False
    finally:
        if tmp_name:
            Path(tmp_name).unlink(missing_ok=True)
