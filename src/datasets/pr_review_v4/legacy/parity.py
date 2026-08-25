"""Field-level parity audit between raw v4 episodes and legacy first-round records."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict

from ..io import sha256_file
from ..schema import DatasetManifest, ReviewEpisodeBoundary, ReviewEpisodeInput


def parity_report(release_dir: Path, legacy_records: Path) -> Dict[str, Any]:
    manifest = DatasetManifest.model_validate_json((release_dir / "manifest.json").read_text())
    episode_ref = next(
        item for item in manifest.input_artifacts if item.schema_version == "episode1"
    )
    boundary_ref = next(
        item for item in manifest.gold_artifacts if item.schema_version == "episode-boundary1"
    )
    episodes = {
        item.pr_number: item
        for item in (
            ReviewEpisodeInput.model_validate_json(line)
            for line in (release_dir / episode_ref.path).read_text().splitlines()
            if line.strip() and json.loads(line).get("round_index") == 1
        )
    }
    boundaries = {
        item.pr_number: item
        for item in (
            ReviewEpisodeBoundary.model_validate_json(line)
            for line in (release_dir / boundary_ref.path).read_text().splitlines()
            if line.strip() and json.loads(line).get("round_index") == 1
        )
    }
    legacy = {
        int(item["pr_number"]): item
        for item in (
            json.loads(line) for line in legacy_records.read_text().splitlines() if line.strip()
        )
    }
    fields = Counter()
    mismatches = defaultdict(list)

    def check(field: str, pr_number: int, actual: Any, expected: Any) -> None:
        matched = actual == expected
        fields[(field, "match" if matched else "mismatch")] += 1
        if not matched and len(mismatches[field]) < 20:
            mismatches[field].append(
                {"pr_number": pr_number, "raw": actual, "legacy": expected}
            )

    for pr_number in sorted(set(episodes) & set(legacy)):
        episode = episodes[pr_number]
        boundary = boundaries[pr_number]
        record = legacy[pr_number]
        input_block = record["input"]
        validation = record["validation"]
        check("title", pr_number, episode.title.text, input_block.get("title") or "")
        if episode.description.text is None and input_block.get("description_maybe_post_edited"):
            fields[("description", "expected_provenance_omission")] += 1
        else:
            check(
                "description",
                pr_number,
                episode.description.text or "",
                input_block.get("description") or "",
            )
        check("base_sha", pr_number, episode.base_sha, input_block.get("base_sha"))
        check("reviewed_head_sha", pr_number, episode.reviewed_head_sha, input_block.get("head_sha"))
        check("diff", pr_number, episode.diff, input_block.get("diff") or "")
        check("review_started_at", pr_number, boundary.review_started_at, validation.get("t1"))
        check("feedback_window_end", pr_number, boundary.feedback_window_end, validation.get("t_push"))

    raw_only = sorted(set(episodes) - set(legacy))
    legacy_only = sorted(set(legacy) - set(episodes))
    by_field: Dict[str, Dict[str, int]] = defaultdict(dict)
    for (field, status), count in sorted(fields.items()):
        by_field[field][status] = count
    hard_mismatches = sum(
        count for (field, status), count in fields.items() if status == "mismatch"
    ) + len(raw_only) + len(legacy_only)
    return {
        "release": str(release_dir),
        "release_manifest_sha256": sha256_file(release_dir / "manifest.json"),
        "legacy_records": str(legacy_records),
        "legacy_records_sha256": sha256_file(legacy_records),
        "raw_episodes": len(episodes),
        "legacy_records_count": len(legacy),
        "raw_only_prs": raw_only,
        "legacy_only_prs": legacy_only,
        "fields": dict(sorted(by_field.items())),
        "mismatch_examples": dict(sorted(mismatches.items())),
        "hard_mismatches": hard_mismatches,
        "passed": hard_mismatches == 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit raw v4 versus legacy first-round parity")
    parser.add_argument("release", type=Path)
    parser.add_argument("legacy_records", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    report = parity_report(args.release, args.legacy_records)
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n")
    print(rendered)
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
