"""A candidate whose fix spans several declarations, applied and compiled as one thing.

Five of the nineteen audited obligations — 26% — cannot be *resolved* by a reviewer confined
to one work unit with one edit, however well it is briefed. They are not hard problems that
better context would reach; they are shapes the submission contract cannot express:

* rename `X` **and** `Y` together, because a rename that updates one of a pair leaves the
  library inconsistent (PR 33337);
* add `Dense.ciInf'` **and** prove it from `Dense.ciSup'`, where neither exists yet
  (PR 33145);
* import `Mathlib.Tactic.ToFun`, attribute eleven lemmas, **and** delete thirteen generated
  siblings, all of which must compile together or none of them do (PR 33117).

Each is one decision. Split into single-edit candidates, each half is either unverifiable or
wrong on its own — deleting `Meromorphic.fun_add` without the attribute that regenerates it
breaks the build, so the compile gate correctly refuses it, and the correct review comment
becomes unpublishable.

**What this does not relax.** The existing site contract is untouched, and confinement is
strengthened rather than weakened: a patch set may only touch files the component already
changes, every edit must anchor inside it, and the *whole* candidate is rejected if any edit
escapes or any touched file fails to compile. One anchor still identifies the claim, so
pairing and merging are unchanged. What changes is only that a claim may carry more than one
edit, and that its warrant is one atomic compile rather than several independent ones.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

#: Guardrail on fan-out. A coordinated fix is a handful of edits; a hundred is a rewrite, and
#: the one measured here — PR 33117's `@[to_fun]` migration — is about twenty-five.
MAX_PATCH_EDITS = 32


@dataclass(frozen=True)
class PatchEdit:
    """One edit inside a patch set. Same two modes as `ProposedEdit`, deliberately."""

    path: str
    declaration_name: Optional[str] = None
    new_declaration: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    replacement: Optional[str] = None

    def mode(self) -> Optional[str]:
        if self.declaration_name and self.new_declaration is not None:
            return "declaration"
        if self.line_start and self.line_end and self.replacement is not None:
            return "span"
        return None


@dataclass(frozen=True)
class PatchSet:
    """Several edits that stand or fall together."""

    edits: Tuple[PatchEdit, ...]

    def paths(self) -> List[str]:
        return sorted({edit.path for edit in self.edits})

    def digest(self) -> str:
        payload = [
            {"path": e.path, "declaration_name": e.declaration_name,
             "new_declaration": e.new_declaration, "line_start": e.line_start,
             "line_end": e.line_end, "replacement": e.replacement}
            for e in self.edits
        ]
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"))
        return hashlib.sha256(encoded.encode()).hexdigest()


def validate(patch: PatchSet, allowed_paths: Iterable[str]) -> List[str]:
    """Every reason this patch set may not be applied. Empty means it may.

    Confinement is checked before anything is written, and against the *component's* files
    rather than the repository: a coordinated fix that reaches outside the change under
    review is not a review comment, it is a second PR.
    """

    allowed = set(allowed_paths)
    problems: List[str] = []
    if not patch.edits:
        problems.append("a patch set with no edits proposes nothing")
    if len(patch.edits) > MAX_PATCH_EDITS:
        problems.append(
            f"{len(patch.edits)} edits exceeds the {MAX_PATCH_EDITS} allowed; a coordinated "
            "fix is a handful of edits, and more than that is a rewrite rather than a review "
            "comment")
    for index, edit in enumerate(patch.edits):
        if edit.path not in allowed:
            problems.append(
                f"edit {index} touches {edit.path!r}, which this component does not change; "
                f"allowed: {sorted(allowed)}")
        if edit.mode() is None:
            problems.append(
                f"edit {index} must use exactly one complete mode: declaration_name + "
                "new_declaration, or line_start + line_end + replacement")
    # Two edits to one span would make the result depend on application order, and an atomic
    # patch whose meaning depends on order is not atomic.
    spans: Dict[str, List[Tuple[int, int, int]]] = {}
    for index, edit in enumerate(patch.edits):
        if edit.mode() == "span" and edit.line_start and edit.line_end:
            spans.setdefault(edit.path, []).append((edit.line_start, edit.line_end, index))
    for path, rows in spans.items():
        ordered = sorted(rows)
        for (a_start, a_end, a_i), (b_start, b_end, b_i) in zip(ordered, ordered[1:]):
            if b_start <= a_end:
                problems.append(
                    f"edits {a_i} and {b_i} overlap in {path} "
                    f"(lines {a_start}-{a_end} and {b_start}-{b_end}); the result would "
                    "depend on which was applied first")
    declarations: Dict[Tuple[str, str], int] = {}
    for index, edit in enumerate(patch.edits):
        if edit.mode() == "declaration" and edit.declaration_name:
            key = (edit.path, edit.declaration_name)
            if key in declarations:
                problems.append(
                    f"edits {declarations[key]} and {index} both replace "
                    f"{edit.declaration_name!r} in {edit.path}")
            declarations[key] = index
    return problems


def apply(patch: PatchSet, read: Any) -> Tuple[Dict[str, str], List[str]]:
    """Compute the patched text of every touched file. Nothing is written here.

    `read(path) -> str | None` supplies the current text, so this stays testable without a
    workspace and callers cannot accidentally mutate a shared snapshot.

    Span edits within a file are applied from the bottom up, so earlier line numbers stay
    valid while later ones are being rewritten.
    """

    problems: List[str] = []
    sources: Dict[str, str] = {}
    for path in patch.paths():
        text = read(path)
        if text is None:
            problems.append(f"{path} is not present in the workspace")
            continue
        sources[path] = text

    by_path: Dict[str, List[PatchEdit]] = {}
    for edit in patch.edits:
        by_path.setdefault(edit.path, []).append(edit)

    out: Dict[str, str] = {}
    for path, edits in by_path.items():
        if path not in sources:
            continue
        text = sources[path]
        for edit in [e for e in edits if e.mode() == "declaration"]:
            old = edit.declaration_name or ""
            # Located by its full text, exactly as the single-edit path does: a declaration
            # matched by name alone can hit a docstring mention or a call site.
            if text.count(old) == 0:
                problems.append(f"{old!r} does not occur in {path}")
                continue
            text = text.replace(old, edit.new_declaration or "", 1)
        spans = sorted(
            (e for e in edits if e.mode() == "span"),
            key=lambda e: -(e.line_start or 0))
        lines = text.splitlines(keepends=True)
        for edit in spans:
            start, end = int(edit.line_start or 0), int(edit.line_end or 0)
            if end > len(lines) or end < start:
                problems.append(f"edit span {start}-{end} is outside {path}")
                continue
            lines[start - 1:end] = [(edit.replacement or "").rstrip("\n") + "\n"]
        text = "".join(lines) if spans else text
        out[path] = text
    return out, problems


def verification_artifact(
    *, work_unit_id: str, candidate_ordinal: int, patch: PatchSet, success: bool,
    content: str, snapshot_sha: str, touched: Sequence[str],
) -> Dict[str, Any]:
    """One artifact for the whole patch, not one per file.

    A per-file artifact set would let a candidate be half-verified, which is exactly the
    state a coordinated fix must never be reportable in: `focused_findings` joins a warrant
    to a candidate, and a candidate whose warrant covers three of its four files has not been
    verified at all.
    """

    identity = {
        "work_unit_id": work_unit_id,
        "candidate_ordinal": candidate_ordinal,
        "stage": "proposed_edit",
        "kind": "lean_compile_patchset",
        "success": success,
        "paths": sorted(touched),
        "patch_sha256": patch.digest(),
        "edits": len(patch.edits),
        "content": content,
        "snapshot_sha": snapshot_sha,
    }
    encoded = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    return {
        "schema_version": "patchset-verification1",
        "artifact_id": f"patchset-verification:{digest[:24]}",
        **identity,
        "source_sha256": digest,
    }


def verify(
    patch: PatchSet, workspace: Path, *, timeout: int = 300,
) -> Tuple[bool, str, List[str]]:
    """Apply the patch and compile every file it touches. Returns `(ok, report, touched)`.

    **What "atomic" means here, precisely.** The candidate stands or falls as one: every
    touched file is compiled and the result is a single verdict, so a patch cannot be
    half-verified. What it does *not* do is capture cross-file consequences. Each patched
    file is compiled as a standalone unit against the workspace's existing build artifacts,
    exactly as the single-edit path does — so deleting a declaration in `A.lean` will not
    surface a break in `B.lean`, because `B` still resolves it from the unpatched `.olean`.

    Catching that would mean rebuilding the downstream closure, which for a Mathlib
    declaration with 1,671 downstream modules is hours. The honest position is that this
    verifies *the patched files elaborate*, which is a real warrant and a weaker one than
    "the library still builds". Reported as such rather than described as full verification.

    The workspace is never written to: patched text goes to temporary files, because these
    trees are symlink farms over a snapshot shared by every concurrent run.
    """

    import subprocess
    import tempfile

    from src.mathlib_review.workspace import run as _run

    def read(path: str) -> Optional[str]:
        source = workspace / path
        try:
            return source.read_text()
        except OSError:
            return None

    if not patch.edits:
        # An empty patch compiled nothing and must not report success. Vacuous truth is the
        # wrong default for a warrant: `focused_findings` joins a successful artifact to a
        # candidate, so "no files failed" would publish a claim backed by no compile at all.
        return False, "a patch set with no edits proposes nothing to verify", []

    patched, problems = apply(patch, read)
    if problems:
        return False, "patch could not be applied:\n" + "\n".join(problems), []
    if not patched:
        return False, "no file was patched", []

    lines: List[str] = []
    ok = True
    touched: List[str] = []
    for path, text in sorted(patched.items()):
        handle = tempfile.NamedTemporaryFile(suffix=".lean", mode="w", delete=False)
        handle.write(text)
        handle.close()
        temporary = Path(handle.name)
        try:
            proc = _run(["lake", "env", "lean", str(temporary)], workspace, timeout=timeout)
            output = (proc.stdout + "\n" + proc.stderr).strip().replace(str(temporary), path)
            if proc.returncode != 0:
                ok = False
            lines.append(f"=== {path}: exit {proc.returncode}\n{output[-4000:]}")
            touched.append(path)
        except (OSError, subprocess.TimeoutExpired) as error:
            ok = False
            lines.append(f"=== {path}: {type(error).__name__}")
        finally:
            temporary.unlink(missing_ok=True)
    return ok, "\n".join(lines), touched
