"""Hydrate immutable base-file blobs needed for cg1 semantic parsing."""

import argparse
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from ..change_graph import parse_unified_diff
from ..io import write_once
from ..schema import ReviewEpisodeInput


RAW_ROOT = "https://raw.githubusercontent.com/leanprover-community/mathlib4"


def hydrate_sources(
    *, release_dir: Path, workspace_root: Path, cache_root: Path
) -> dict:
    episodes = [
        ReviewEpisodeInput.model_validate_json(line)
        for line in (release_dir / "input" / "episodes.jsonl").read_text().splitlines()
        if line.strip()
    ]
    required = set()
    for episode in episodes:
        workspace = workspace_root / episode.base_sha
        for diff_file in parse_unified_diff(episode.diff):
            old_path = diff_file.old_path or diff_file.path
            if (
                diff_file.status != "added"
                and diff_file.path.endswith(".lean")
                and diff_file.hunks
                and not (workspace / old_path).is_file()
            ):
                required.add((episode.base_sha, old_path))

    fetched = 0
    existing = 0
    failures = []
    for sha, path in sorted(required):
        destination = cache_root / sha / path
        if destination.is_file():
            existing += 1
            continue
        url = f"{RAW_ROOT}/{sha}/{quote(path, safe='/')}"
        request = Request(url, headers={"User-Agent": "ape-bench-pr-review-v4"})
        try:
            with urlopen(request, timeout=60) as response:
                payload = response.read()
            write_once(destination, payload)
            fetched += 1
        except (HTTPError, URLError, TimeoutError) as exc:
            failures.append({"base_sha": sha, "path": path, "error": str(exc)})
    return {
        "required": len(required),
        "fetched": fetched,
        "existing": existing,
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Hydrate base files for PR Review v4 cg1")
    parser.add_argument("release", type=Path)
    parser.add_argument(
        "--workspaces",
        type=Path,
        default=Path("data/code_execute/repos/mathlib4/workspaces"),
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path("data/pr_review_v4/cache/base_files"),
    )
    args = parser.parse_args()
    print(
        json.dumps(
            hydrate_sources(
                release_dir=args.release,
                workspace_root=args.workspaces,
                cache_root=args.cache,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
