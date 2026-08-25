"""Shared agent skill configuration, discovery, and materialization helpers."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal, Optional, Sequence, TYPE_CHECKING

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

if TYPE_CHECKING:
    import logging


CODEX_REPO_SKILL_DIR = ".agents/skills"
CLAUDE_REPO_SKILL_DIR = ".claude/skills"
APE_AGENT_REPO_SKILL_DIRS = (CODEX_REPO_SKILL_DIR, CLAUDE_REPO_SKILL_DIR)
SKILLS_MANIFEST_FILENAME = "skills_manifest.json"
SKILLS_STORE_DIRNAME = "skills"
SKILL_TOOL_NAMES = {"list_skills", "read_skill"}


class SkillsConfig(BaseModel):
    """Shared scaffold-level configuration for managed skills."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    repo_discovery: bool = True
    extra_roots: list[Path] = Field(default_factory=list)

    @field_validator("extra_roots", mode="before")
    @classmethod
    def _coerce_extra_roots(cls, value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, (str, Path)):
            return [value]
        if isinstance(value, tuple):
            return list(value)
        return value


@dataclass(frozen=True)
class DiscoveredSkill:
    """A skill discovered from repo-local or configured roots."""

    skill_id: str
    name: str
    description: str
    source_path: Path
    source_kind: Literal["repo", "extra_root"]
    discovery_root: Path


@dataclass(frozen=True)
class MaterializedSkill:
    """A discovered skill copied into an attempt-local store."""

    skill_id: str
    name: str
    description: str
    source_path: Path
    source_kind: Literal["repo", "extra_root"]
    discovery_root: Path
    materialized_path: Path


@dataclass(frozen=True)
class MaterializedSkillSet:
    """All managed skills available for a task attempt."""

    attempt_path: Path
    manifest_path: Path
    store_root: Path
    skills: tuple[MaterializedSkill, ...]

    @property
    def has_skills(self) -> bool:
        return bool(self.skills)

    def select(
        self,
        *,
        source_kinds: Optional[set[Literal["repo", "extra_root"]]] = None,
    ) -> tuple[MaterializedSkill, ...]:
        if source_kinds is None:
            return self.skills
        return tuple(skill for skill in self.skills if skill.source_kind in source_kinds)

    def by_id(self, skill_id: str) -> Optional[MaterializedSkill]:
        for skill in self.skills:
            if skill.skill_id == skill_id:
                return skill
        return None


def normalize_skills_config_paths(config_dict: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    """Resolve `skills.extra_roots` entries relative to a caller-provided base directory."""
    skills_config = config_dict.get("skills")
    if not isinstance(skills_config, dict):
        return config_dict

    extra_roots = skills_config.get("extra_roots")
    if extra_roots is None:
        return config_dict

    if isinstance(extra_roots, (str, Path)):
        extra_roots = [extra_roots]

    if not isinstance(extra_roots, list):
        return config_dict

    normalized_roots: list[Path] = []
    for raw_root in extra_roots:
        path = Path(raw_root).expanduser()
        if not path.is_absolute():
            path = base_dir / path
        normalized_roots.append(path.resolve())

    skills_config["extra_roots"] = normalized_roots
    return config_dict


def materialize_task_skills(
    task,
    logger: Optional["logging.LoggerAdapter"],
    *,
    repo_skill_dirs: Sequence[str],
) -> MaterializedSkillSet:
    """Discover, validate, and materialize managed skills for a task attempt."""
    skills_config = getattr(task.config, "skills", None)
    if skills_config is None:
        skills_config = SkillsConfig()

    if task.attempt_path is None:
        raise RuntimeError("Task attempt path must exist before materializing skills")

    discovered: list[DiscoveredSkill] = []
    seen_paths: set[Path] = set()

    if skills_config.enabled and skills_config.repo_discovery:
        repo_workspace = _get_repo_discovery_workspace(task)
        if repo_workspace is not None:
            for relative_dir in repo_skill_dirs:
                repo_root = repo_workspace / relative_dir
                if not repo_root.is_dir():
                    continue
                for skill in _discover_skills_from_root(
                    repo_root,
                    source_kind="repo",
                    strict=False,
                ):
                    real_source_path = skill.source_path.resolve()
                    if real_source_path in seen_paths:
                        continue
                    discovered.append(skill)
                    seen_paths.add(real_source_path)

    if skills_config.enabled:
        for extra_root in skills_config.extra_roots:
            extra_root = Path(extra_root).expanduser().resolve()
            for skill in _discover_skills_from_root(
                extra_root,
                source_kind="extra_root",
                strict=True,
            ):
                real_source_path = skill.source_path.resolve()
                if real_source_path in seen_paths:
                    continue
                discovered.append(skill)
                seen_paths.add(real_source_path)

    materialized = _materialize_skills(
        discovered,
        attempt_path=task.attempt_path,
        logger=logger,
    )
    setattr(task, "managed_skills_context", materialized)
    return materialized


def get_task_managed_skills(task) -> Optional[MaterializedSkillSet]:
    """Return the cached managed skill context for a task, loading from disk if needed."""
    cached = getattr(task, "managed_skills_context", None)
    if isinstance(cached, MaterializedSkillSet):
        return cached

    attempt_path = getattr(task, "attempt_path", None)
    if attempt_path is None:
        return None

    manifest_path = Path(attempt_path) / SKILLS_MANIFEST_FILENAME
    if not manifest_path.exists():
        return None

    loaded = load_materialized_skill_set(manifest_path)
    setattr(task, "managed_skills_context", loaded)
    return loaded


def load_materialized_skill_set(manifest_path: Path) -> MaterializedSkillSet:
    """Load a materialized skill set from a manifest written to disk."""
    manifest_path = manifest_path.resolve()
    attempt_path = manifest_path.parent
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    skills = tuple(
        MaterializedSkill(
            skill_id=entry["skill_id"],
            name=entry["name"],
            description=entry["description"],
            source_path=Path(entry["source_path"]),
            source_kind=entry["source_kind"],
            discovery_root=Path(entry["discovery_root"]),
            materialized_path=attempt_path / entry["materialized_path"],
        )
        for entry in payload.get("skills", [])
    )

    return MaterializedSkillSet(
        attempt_path=attempt_path,
        manifest_path=manifest_path,
        store_root=attempt_path / SKILLS_STORE_DIRNAME,
        skills=skills,
    )


def mirror_materialized_skills(
    skill_set: MaterializedSkillSet,
    destination_root: Path,
    *,
    source_kinds: Optional[set[Literal["repo", "extra_root"]]] = None,
) -> tuple[Path, ...]:
    """Copy selected materialized skills into a harness-specific discovery directory."""
    selected_skills = skill_set.select(source_kinds=source_kinds)
    if not selected_skills:
        return tuple()

    if destination_root.exists():
        shutil.rmtree(destination_root)
    destination_root.mkdir(parents=True, exist_ok=True)

    mirrored_paths: list[Path] = []
    for skill in selected_skills:
        destination = destination_root / skill.skill_id
        shutil.copytree(skill.materialized_path, destination)
        mirrored_paths.append(destination)

    return tuple(mirrored_paths)


def list_skill_relative_files(skill: MaterializedSkill) -> list[str]:
    """List files available inside a materialized skill directory."""
    files: list[str] = []
    for path in sorted(skill.materialized_path.rglob("*")):
        if path.is_file():
            files.append(path.relative_to(skill.materialized_path).as_posix())
    return files


def read_materialized_skill_file(skill: MaterializedSkill, relative_path: str = "SKILL.md") -> str:
    """Read a file from a materialized skill while preventing path traversal."""
    candidate = (skill.materialized_path / relative_path).resolve()
    skill_root = skill.materialized_path.resolve()

    try:
        candidate.relative_to(skill_root)
    except ValueError as exc:
        raise ValueError(f"Skill path must stay within {skill.skill_id}") from exc

    if not candidate.is_file():
        raise FileNotFoundError(
            f"Skill file '{relative_path}' not found in {skill.skill_id}"
        )

    return candidate.read_text(encoding="utf-8")


def _materialize_skills(
    discovered_skills: Sequence[DiscoveredSkill],
    *,
    attempt_path: Path,
    logger: Optional["logging.LoggerAdapter"],
) -> MaterializedSkillSet:
    store_root = attempt_path / SKILLS_STORE_DIRNAME
    manifest_path = attempt_path / SKILLS_MANIFEST_FILENAME

    if store_root.exists():
        shutil.rmtree(store_root)
    store_root.mkdir(parents=True, exist_ok=True)

    materialized_skills: list[MaterializedSkill] = []
    for discovered in discovered_skills:
        materialized_path = store_root / discovered.skill_id
        shutil.copytree(discovered.source_path, materialized_path)
        materialized_skills.append(
            MaterializedSkill(
                skill_id=discovered.skill_id,
                name=discovered.name,
                description=discovered.description,
                source_path=discovered.source_path,
                source_kind=discovered.source_kind,
                discovery_root=discovered.discovery_root,
                materialized_path=materialized_path,
            )
        )

    manifest_payload = {
        "version": 1,
        "skills": [
            {
                "skill_id": skill.skill_id,
                "name": skill.name,
                "description": skill.description,
                "source_kind": skill.source_kind,
                "source_path": str(skill.source_path),
                "discovery_root": str(skill.discovery_root),
                "materialized_path": skill.materialized_path.relative_to(attempt_path).as_posix(),
            }
            for skill in materialized_skills
        ],
    }
    manifest_path.write_text(
        json.dumps(manifest_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if logger:
        if materialized_skills:
            logger.info(
                "[Skills] Materialized managed skills: "
                + ", ".join(
                    f"{skill.skill_id} ({skill.name}) from {skill.source_path}"
                    for skill in materialized_skills
                )
            )
        else:
            logger.info("[Skills] No managed skills resolved for this task")

    return MaterializedSkillSet(
        attempt_path=attempt_path,
        manifest_path=manifest_path,
        store_root=store_root,
        skills=tuple(materialized_skills),
    )


def _get_repo_discovery_workspace(task) -> Optional[Path]:
    from ape.cli.task_session import is_internal_cli_task

    if is_internal_cli_task(task):
        local_workspace = getattr(task.data, "local_workspace_path", None)
        if local_workspace is None:
            return None
        return Path(local_workspace).expanduser().resolve()

    target_workspace = getattr(task, "target_workspace", None)
    if target_workspace is None or target_workspace.path is None:
        return None
    return Path(target_workspace.path).resolve()


def _discover_skills_from_root(
    root: Path,
    *,
    source_kind: Literal["repo", "extra_root"],
    strict: bool,
) -> list[DiscoveredSkill]:
    root = root.expanduser().resolve()
    if not root.exists():
        if strict:
            raise FileNotFoundError(f"Skill root does not exist: {root}")
        return []
    if not root.is_dir():
        raise NotADirectoryError(f"Skill root is not a directory: {root}")

    candidate_skill_dirs = _expand_skill_root(root)
    if not candidate_skill_dirs:
        if strict:
            raise ValueError(
                f"Skill root {root} must contain SKILL.md or immediate child skill directories"
            )
        return []

    discovered_skills: list[DiscoveredSkill] = []
    for skill_dir in candidate_skill_dirs:
        name, description = _load_skill_metadata(skill_dir / "SKILL.md")
        discovered_skills.append(
            DiscoveredSkill(
                skill_id=_build_skill_id(name=name, skill_dir=skill_dir),
                name=name,
                description=description,
                source_path=skill_dir,
                source_kind=source_kind,
                discovery_root=root,
            )
        )

    return discovered_skills


def _expand_skill_root(root: Path) -> list[Path]:
    if (root / "SKILL.md").is_file():
        return [root]

    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )


def _load_skill_metadata(skill_md_path: Path) -> tuple[str, str]:
    try:
        raw_text = skill_md_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Unable to read {skill_md_path}") from exc

    lines = raw_text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{skill_md_path} is missing YAML frontmatter")

    end_index: Optional[int] = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break

    if end_index is None:
        raise ValueError(f"{skill_md_path} has unterminated YAML frontmatter")

    frontmatter_text = "\n".join(lines[1:end_index])
    metadata = yaml.safe_load(frontmatter_text)
    if not isinstance(metadata, dict):
        raise ValueError(f"{skill_md_path} frontmatter must be a mapping")

    name = metadata.get("name")
    description = metadata.get("description")

    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{skill_md_path} frontmatter is missing a non-empty 'name'")
    if not isinstance(description, str) or not description.strip():
        raise ValueError(f"{skill_md_path} frontmatter is missing a non-empty 'description'")

    return name.strip(), description.strip()


def _build_skill_id(name: str, skill_dir: Path) -> str:
    slug = _slugify(name) or _slugify(skill_dir.name) or "skill"
    path_hash = hashlib.sha256(str(skill_dir.resolve()).encode("utf-8")).hexdigest()[:10]
    return f"{slug}-{path_hash}"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug
