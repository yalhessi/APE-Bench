"""Deterministic canonical-API retrieval over a review-time dependency neighborhood."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from ape.toolkits.code.lean.lean_parser import parse_major_declarations

from ..change_graph import apply_file_patch, parse_unified_diff
from src.mathlib_review.workspace import tool_env as _tool_env
from ..io import COMPILED_TARGET, canonical_json_bytes, sha256_bytes
from ..schema import (
    CanonicalRetrievalHit,
    ChangeTarget,
    InvestigationTask,
    OpportunityEvidenceArtifact,
    RepositoryDeclaration,
    ReviewEpisodeInput,
)


INDEX_VERSION = "canonical-dependency-neighborhood/1"
RETRIEVAL_VERSION = "canonical-api-lexical-shape/1"
MAX_HITS = 20
OPPORTUNITY_SCORE_FLOOR = 24.0

_IMPORT_RE = re.compile(r"^(?:public\s+)?import\s+([A-Za-z0-9_.]+)", re.MULTILINE)
_IDENT_RE = re.compile(r"[A-Za-z][A-Za-z0-9_']*(?:\.[A-Za-z][A-Za-z0-9_']*)*")
_CAMEL_RE = re.compile(r"([a-z0-9])([A-Z])")
_STOP = {
    "and", "autoimplicit", "by", "class", "def", "else", "exact", "false", "have",
    "iff", "if", "import", "instance", "lemma", "let", "match", "namespace", "only",
    "open", "private", "protected", "public", "return", "section", "simp", "structure",
    "theorem", "then", "true", "using", "variable", "variables", "where", "with",
}


@dataclass(frozen=True)
class ReplacementProposal:
    old_block: str
    new_block: str
    description: str


@dataclass(frozen=True)
class ApplicabilityResult:
    status: str
    content: str
    replacement: Optional[ReplacementProposal]


def _tokens(text: str) -> List[str]:
    values: List[str] = []
    for raw in _IDENT_RE.findall(text or ""):
        for qualified in (raw, raw.rsplit(".", 1)[-1]):
            exact = qualified.lower().strip("'")
            if len(exact) >= 3 and exact not in _STOP:
                values.append(exact)
            split = _CAMEL_RE.sub(r"\1 \2", qualified).replace("_", " ").replace("'", " ")
            values.extend(
                token
                for token in split.lower().split()
                if len(token) >= 3 and token not in _STOP and token != exact
            )
    return values


def _line_number(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def _namespace(fullname: str, name: str) -> Optional[str]:
    if fullname == name or "." not in fullname:
        return None
    return fullname.rsplit(".", 1)[0]


def dependency_neighborhood_paths(workspace: Path, target_path: str) -> List[Path]:
    """Return the target module and its direct imports, all from the frozen base snapshot."""

    target = workspace / target_path
    if not target.is_file():
        raise FileNotFoundError(f"review base file is unavailable: {target}")
    source = target.read_text(encoding="utf-8")
    paths = {target}
    for module in _IMPORT_RE.findall(source):
        candidate = workspace / f"{module.replace('.', '/')}.lean"
        if candidate.is_file():
            paths.add(candidate)
    return sorted(paths, key=lambda path: path.relative_to(workspace).as_posix())


def build_declaration_index(
    workspace: Path, snapshot_sha: str, target_path: str
) -> List[RepositoryDeclaration]:
    rows: List[RepositoryDeclaration] = []
    for path in dependency_neighborhood_paths(workspace, target_path):
        source = path.read_text(encoding="utf-8")
        relative = path.relative_to(workspace).as_posix()
        for declaration in parse_major_declarations(source):
            name = declaration.name or ""
            fullname = declaration.fullname or name
            signature = declaration.signature or ""
            if not name or not signature:
                continue
            dependencies = sorted({
                token
                for token in _IDENT_RE.findall(signature + "\n" + (declaration.proof or ""))
                if token not in {name, fullname} and token.lower() not in _STOP
            })
            identity = {
                "index_version": INDEX_VERSION,
                "snapshot_sha": snapshot_sha,
                "path": relative,
                "line_start": _line_number(source, declaration.span[0]),
                "line_end": _line_number(source, declaration.span[1] - 1),
                "declaration_kind": declaration.kind,
                "name": name,
                "fullname": fullname,
                "namespace": _namespace(fullname, name),
                "signature": signature,
                "type_shape_tokens": sorted(set(_tokens(signature))),
                "direct_dependencies": dependencies,
            }
            digest = sha256_bytes(canonical_json_bytes(identity))
            rows.append(RepositoryDeclaration(
                declaration_id=f"repository-declaration:{digest[:24]}",
                source_sha256=digest,
                **identity,
            ))
    return sorted(rows, key=lambda row: (row.path, row.line_start, row.declaration_id))


def _already_used(target_code: str, declaration: RepositoryDeclaration) -> bool:
    names = {declaration.name, declaration.fullname}
    return any(
        re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", target_code)
        for name in names
        if name
    )


def _investigation_query(target_code: str) -> str:
    """Focus retrieval on the largest locally reconstructed proposition when one exists."""

    blocks = re.findall(
        r"(^  have \w+ : [^\n]+ := by\n.*?)(?=^  (?:have|refine|exact|rw|rwa|simpa|show)\b)",
        target_code,
        re.MULTILINE | re.DOTALL,
    )
    substantive = [block for block in blocks if len(block.splitlines()) >= 5]
    return max(substantive, key=len) if substantive else target_code


def rank_declarations(
    task: InvestigationTask,
    target: ChangeTarget,
    declarations: Iterable[RepositoryDeclaration],
    limit: int = MAX_HITS,
) -> List[CanonicalRetrievalHit]:
    target_code = target.reviewed_code or target.base_code or ""
    query_text = _investigation_query(target_code)
    query_tokens = Counter(_tokens(query_text))
    query_sha = sha256_bytes(canonical_json_bytes({
        "retrieval_version": RETRIEVAL_VERSION,
        "primary_change_id": target.change_id,
        "target_source_sha256": target.source_sha256,
        "query_text_sha256": sha256_bytes(query_text.encode()),
        "tokens": sorted(query_tokens.items()),
    }))
    ranked = []
    for declaration in declarations:
        candidate_tokens = Counter(
            _tokens(f"{declaration.fullname}\n{declaration.signature}")
        )
        matched = sorted(set(query_tokens).intersection(candidate_tokens) - _STOP)
        score = sum(
            min(query_tokens[token], 3) * min(candidate_tokens[token], 2)
            for token in matched
        ) + 3 * sum("_" in token for token in matched)
        if score:
            ranked.append((float(score), declaration, matched))
    ranked.sort(key=lambda row: (-row[0], row[1].fullname, row[1].declaration_id))
    hits = []
    for rank, (score, declaration, matched) in enumerate(ranked[:limit], 1):
        payload = {
            "investigation_id": task.investigation_id,
            "primary_change_id": target.change_id,
            "declaration_id": declaration.declaration_id,
            "rank": rank,
            "score": score,
            "matched_tokens": matched,
            "already_used": _already_used(target_code, declaration),
            "query_sha256": query_sha,
        }
        digest = sha256_bytes(canonical_json_bytes(payload))
        hits.append(CanonicalRetrievalHit(
            retrieval_hit_id=f"canonical-hit:{digest[:24]}",
            source_sha256=digest,
            **payload,
        ))
    return hits


def is_high_confidence_insert_separation(
    hit: CanonicalRetrievalHit, declaration: RepositoryDeclaration
) -> bool:
    required = {"insert", "isseparated", "mem", "not"}
    return bool(
        hit.rank == 1
        and not hit.already_used
        and hit.score >= OPPORTUNITY_SCORE_FLOOR
        and required.issubset(hit.matched_tokens)
        and "isSeparated" in declaration.signature
        and "insert" in declaration.signature
    )


def match_insert_separation_template(target_code: str) -> Optional[dict]:
    """Match the inserted-set separation proof shape without constructing an edit."""

    let_match = re.search(r"^  let (\w+) := \{(\w+)\} ∪ (.+)$", target_code, re.MULTILINE)
    not_mem = re.search(r"^  have (\w+) : \w+ ∉ (.+) := by$", target_code, re.MULTILINE)
    distance = re.search(r"^  push_neg at (\w+)$", target_code, re.MULTILINE)
    block = re.search(
        r"(^  have (\w+) : IsSeparated ([^\n]+) := by\n)(.*?)(?=^  (?:have|refine|exact|rw|rwa|simpa|show)\b)",
        target_code,
        re.MULTILINE | re.DOTALL,
    )
    base = re.search(r"^    exact (\w+) \w+ \w+ \w+\s*$", block.group(4), re.MULTILINE) if block else None
    if not all((let_match, not_mem, distance, block, base)):
        return None
    return {
        "let": let_match, "not_mem": not_mem, "distance": distance,
        "block": block, "base": base,
    }


def propose_insert_separation_replacement(
    target_code: str, declaration: RepositoryDeclaration
) -> Optional[ReplacementProposal]:
    parts = match_insert_separation_template(target_code)
    if parts is None:
        return None
    let_match = parts["let"]
    not_mem = parts["not_mem"]
    distance = parts["distance"]
    block = parts["block"]
    base = parts["base"]
    collection, point, set_expression = let_match.groups()
    not_mem_name = not_mem.group(1)
    distance_name = distance.group(1)
    have_header = block.group(1)
    base_separation = base.group(1)
    old_block = block.group(0)
    new_block = (
        have_header
        + f"    simpa only [{collection}, singleton_union, "
        + f"{declaration.fullname} {not_mem_name}] using\n"
        + f"      And.intro {base_separation} {distance_name}\n"
    )
    description = (
        f"Replace the manual inserted-set separation case analysis with "
        f"`{declaration.fullname} {not_mem_name}`, reusing `{base_separation}` and "
        f"`{distance_name}` for the two required conjuncts over `{point}` and `{set_expression}`."
    )
    return ReplacementProposal(old_block=old_block, new_block=new_block, description=description)


def check_applicability(
    workspace: Path,
    episode: ReviewEpisodeInput,
    target: ChangeTarget,
    proposal: Optional[ReplacementProposal],
) -> ApplicabilityResult:
    if proposal is None:
        return ApplicabilityResult(
            status="unavailable",
            content="No supported source-to-edit structural template matched the reviewed target.",
            replacement=None,
        )
    env = _tool_env(workspace)
    lake = shutil.which("lake", path=env.get("PATH"))
    if lake is None:
        return ApplicabilityResult(
            status="unavailable",
            content=(
                "A source-derived replacement was constructed, but `lake` is unavailable in the "
                "current execution environment. The adjudication run must verify the edit with Lean."
            ),
            replacement=proposal,
        )
    diff_file = next(
        (item for item in parse_unified_diff(episode.diff) if item.path == target.path), None
    )
    if diff_file is None or not diff_file.old_path:
        return ApplicabilityResult(
            status="unavailable",
            content="The reviewed file could not be reconstructed from its base snapshot.",
            replacement=proposal,
        )
    reviewed = apply_file_patch((workspace / diff_file.old_path).read_text(), diff_file)
    if reviewed.count(proposal.old_block) != 1:
        return ApplicabilityResult(
            status="unavailable",
            content="The proposed replacement block was not unique in the reconstructed file.",
            replacement=proposal,
        )
    edited = reviewed.replace(proposal.old_block, proposal.new_block, 1)
    with tempfile.NamedTemporaryFile(suffix=".lean", mode="w", delete=False) as handle:
        temp_path = Path(handle.name)
        handle.write(edited)
    try:
        process = subprocess.run(
            [lake, "env", "lean", "-Dexperimental.module=true", str(temp_path)],
            cwd=workspace,
            env=env,
            text=True,
            capture_output=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return ApplicabilityResult(
            status="unavailable",
            content=f"Lean applicability check could not complete: {exc}",
            replacement=proposal,
        )
    finally:
        temp_path.unlink(missing_ok=True)
    # Lean names diagnostics after the throwaway file it compiled, whose name is random.
    # Left in, that name reaches the evidence content and re-hashes on every run, which
    # makes the deterministic arm's artifacts non-reproducible. See `COMPILED_TARGET`.
    output = (process.stdout + process.stderr).strip().replace(str(temp_path), COMPILED_TARGET)
    if process.returncode == 0:
        return ApplicabilityResult(
            status="compiled",
            content="The source-derived replacement compiled in the review-time workspace.",
            replacement=proposal,
        )
    return ApplicabilityResult(
        status="failed",
        content=f"The source-derived replacement did not compile: {output[-2000:]}",
        replacement=proposal,
    )


def evidence_artifact(
    task: InvestigationTask,
    kind: str,
    source_ref: str,
    content: str,
    snapshot_sha: str,
) -> OpportunityEvidenceArtifact:
    payload = {
        "investigation_id": task.investigation_id,
        "episode_id": task.episode_id,
        "pr_number": task.pr_number,
        "kind": kind,
        "source_ref": source_ref,
        "content": content,
        "snapshot_sha": snapshot_sha,
    }
    digest = sha256_bytes(canonical_json_bytes(payload))
    return OpportunityEvidenceArtifact(
        artifact_id=f"opportunity-evidence:{digest[:24]}",
        source_sha256=digest,
        **payload,
    )
