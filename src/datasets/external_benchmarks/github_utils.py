#!/usr/bin/env python3
"""
Utilities for fetching Lean project metadata from GitHub.
"""

import re
import urllib.error
import urllib.request
from functools import lru_cache
from typing import Optional
from pathlib import Path

try:  # Python 3.11+
    import tomllib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for older Python
    try:
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover - last resort
        tomllib = None  # type: ignore


def fetch_file_from_github(repo_url: str, commit_hash: str, file_path: str, timeout: int = 30) -> Optional[str]:
    """Fetch a file from GitHub repository at a specific commit."""
    try:
        repo_url_clean = repo_url.rstrip('.git')
        parts = repo_url_clean.split('github.com/')
        if len(parts) < 2:
            print(f"  Warning: Invalid GitHub URL: {repo_url}")
            return None

        owner_repo = parts[1].strip('/')
        raw_url = f"https://raw.githubusercontent.com/{owner_repo}/{commit_hash}/{file_path}"

        req = urllib.request.Request(raw_url)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode('utf-8')

    except urllib.error.HTTPError as e:
        return None
    except Exception as e:
        print(f"  Warning: Failed to fetch {file_path}: {e}")
        return None


def _parse_default_target_from_toml(content: str) -> Optional[str]:
    """Extract the default target name from a Lake TOML file."""
    if not content:
        return None

    if tomllib is not None:  # type: ignore
        try:
            data = tomllib.loads(content)  # type: ignore[arg-type]
            candidates = (
                data.get('defaultTargets')
                or data.get('defaultTarget')
                or data.get('default_target')
                or data.get('default_targets')
            )
            if isinstance(candidates, list):
                for entry in candidates:
                    if isinstance(entry, str) and entry.strip():
                        return entry.strip()
            elif isinstance(candidates, str) and candidates.strip():
                return candidates.strip()
        except Exception as exc:
            print(f"  Warning: Failed to parse lakefile.toml via tomllib: {exc}")

    list_match = re.search(r'defaultTargets?\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if list_match:
        inner = list_match.group(1)
        for match in re.finditer(r'["\']([^"\']+)["\']', inner):
            candidate = match.group(1).strip()
            if candidate:
                return candidate

    single_match = re.search(r'defaultTargets?\s*=\s*["\']([^"\']+)["\']', content)
    if single_match:
        candidate = single_match.group(1).strip()
        if candidate:
            return candidate

    return None


_ANGLE_OPEN = chr(0x00AB)
_ANGLE_CLOSE = chr(0x00BB)

_LEAN_DECL_PATTERN = re.compile(
    r'lean_(?:lib|exe|pkg|script)\s+(?:{open}([^{close}]+){close}|"([^"]+)"|\'([^\']+)\'|([A-Za-z0-9_.-]+))'.format(
        open=_ANGLE_OPEN,
        close=_ANGLE_CLOSE,
    )
)


def _parse_default_target_from_lakefile(content: str) -> Optional[str]:
    """Extract the default target name from a lakefile.lean string."""
    if not content:
        return None

    lines = content.splitlines()

    def extract_target(text: str) -> Optional[str]:
        match = _LEAN_DECL_PATTERN.search(text)
        if not match:
            return None
        for group in match.groups():
            if group:
                return group
        return None

    for idx, raw_line in enumerate(lines):
        if 'default_target' not in raw_line or '@' not in raw_line:
            continue

        inline_target = extract_target(raw_line)
        if inline_target:
            return inline_target.strip()

        for next_idx in range(idx + 1, len(lines)):
            candidate_line = lines[next_idx].strip()
            if not candidate_line or candidate_line.startswith('--'):
                continue
            extracted = extract_target(candidate_line)
            if extracted:
                return extracted.strip()
            break

    return None


@lru_cache(maxsize=None)
def get_default_target(repo_url: str, commit_hash: str) -> Optional[str]:
    """Determine the default target for a Lean project by inspecting Lake files."""
    candidates = [
        ('lakefile.lean', _parse_default_target_from_lakefile),
        ('lakefile.toml', _parse_default_target_from_toml)
    ]

    for file_path, parser in candidates:
        content = fetch_file_from_github(repo_url, commit_hash, file_path)
        if not content:
            continue
        target = parser(content)
        if target:
            return target

    print(f"  Warning: Could not determine default target for repository {repo_url}")
    return None


def get_default_target_from_repo(repo_path: Path) -> Optional[str]:
    """Determine the default target for a Lean project by inspecting local Lake files."""
    candidates = [
        (repo_path / "lakefile.lean", _parse_default_target_from_lakefile),
        (repo_path / "lakefile.toml", _parse_default_target_from_toml),
    ]

    for file_path, parser in candidates:
        try:
            if not file_path.exists():
                continue
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            print(f"  Warning: Failed to read {file_path}: {exc}")
            continue
        target = parser(content)
        if target:
            return target

    print(f"  Warning: Could not determine default target from {repo_path}")
    return None


__all__ = [
    'fetch_file_from_github',
    'get_default_target',
    'get_default_target_from_repo',
]
