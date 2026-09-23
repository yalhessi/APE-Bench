"""Canonical serialization, hashing, and immutable artifact writes."""

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List

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


def jsonl_rows(path: Path) -> List[Any]:
    r"""The inverse of `jsonl_bytes`. Splits on "\n" and nothing else -- never `splitlines()`.

    `canonical_json_bytes` writes `ensure_ascii=False`, so a record keeps whatever exotic
    character a GitHub comment body carries, verbatim; `json.dumps` escapes "\n" and "\r" inside a
    string but nothing else. `str.splitlines()` additionally breaks on U+2028, U+2029, U+0085,
    \v, \f, \x1c, \x1d and \x1e -- so it cuts such a record in half mid-string, and both halves
    fail to parse. Measured: 2 of the 32,851 collected PRs carry U+2028 in a comment body, and
    reading either raised `JSONDecodeError: Unterminated string`. The files were not damaged --
    their recorded digests matched; the reader was.

    Splitting on "\n" is exactly right because it is exactly what the writer joined on.
    """

    text = Path(path).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.split("\n") if line.strip()]


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

    Splits on "\n" for the reason `jsonl_rows` gives: `splitlines()` would break a record that
    contains U+2028 or one of its relatives, which a quoted review comment can.
    """

    return [
        cls.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").split("\n")
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


def append_jsonl(path: Path, row: Any) -> Path:
    """Add one record to an append-only file, in the canonical form everything else reads.

    The counterpart to `write_once`, and the two are not interchangeable. `write_once` is what
    makes a run reproducible: a second write with different bytes is refused, so an artifact
    cannot be quietly revised. That guarantee is exactly wrong for a record written *while*
    work happens -- a journal, a trace, a stage ledger -- where a crash must leave what already
    ran still findable, and where the file is complete only when the work is.

    Appending rather than rewriting is also why a truncated final line is survivable: every
    reader here stops at the first line it cannot parse and keeps everything before it.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = row.model_dump(mode="json") if hasattr(row, "model_dump") else row
    with path.open("ab") as handle:
        handle.write(canonical_json_bytes(payload) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())
    return path


def appended_rows(path: Path) -> List[Any]:
    """Read an append-only file, stopping at the first line that will not parse.

    The reader for anything `append_jsonl` writes, and the difference from `jsonl_rows` is the
    whole point. A write-once artifact is complete or it is a defect, so a line that will not
    parse there is an error worth raising. An append-only file is written *while* work happens,
    so a crash mid-write truncates its last line by construction -- and everything before it is
    intact. Stopping rather than skipping is deliberate: the rows are ordered, so a later one
    cannot be trusted once one is unreadable.

    The lead's journal and the execution index already do this; they live in `src/ape/` and
    cannot import this module, which is the package boundary rather than a copy.
    """

    if not Path(path).is_file():
        return []
    rows: List[Any] = []
    for line in Path(path).read_text(encoding="utf-8").split("\n"):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            break
    return rows


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
