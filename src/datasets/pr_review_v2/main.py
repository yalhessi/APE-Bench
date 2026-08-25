"""
First-round-review dataset pipeline (v2).

Stages (each idempotent, all reading/writing the on-disk cache):
  fetch   — search candidates and cache raw per-PR bundles
  derive  — bundles → gold records + funnel report (no network)
  delta   — hydrate δ₀ / Δ₁ / Δ* + comment↔hunk linkage (compare API, cached)
  all     — fetch → derive → delta → write JSONL

Usage:
  python -m src.datasets.pr_review_v2.main all --config configs/pr_review_v2.yaml
  python -m src.datasets.pr_review_v2.main derive --config configs/pr_review_v2.yaml
  python -m src.datasets.pr_review_v2.main all start_date=2025-09-01 end_date=2025-12-31 max_prs=50
"""

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ape.utils import deep_merge, load_yaml, parse_cli_args
from ape.utils.logging import create_logger

from .config import PRReviewV2Config
from .delta import hydrate_record
from .derive import derive_record, load_roster
from .fetch import bundle_path, fetch_pr_bundle, search_candidate_numbers
from .github import GitHubClient
from .schema import PRReviewV2Record, SkipReason


def _resolve_output_file(config: PRReviewV2Config) -> Path:
    if config.output_file:
        return config.output_file
    window = f"{config.start_date or 'begin'}_to_{config.end_date or 'now'}"
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return config.output_dir / f"mathlib_pr_review_v2_{window}_{stamp}.jsonl"


def _cached_bundle_numbers(config: PRReviewV2Config) -> List[int]:
    bundle_dir = config.cache_dir / "bundles"
    if not bundle_dir.exists():
        return []
    numbers = []
    for path in bundle_dir.glob("pr_*.json"):
        try:
            numbers.append(int(path.stem.split("_")[1]))
        except (IndexError, ValueError):
            continue
    return sorted(numbers, reverse=(config.pr_order == "newest"))


def run_fetch(client: GitHubClient, config: PRReviewV2Config, logger) -> List[int]:
    numbers = search_candidate_numbers(client, config)
    logger.info("Stage A: %d candidate PRs", len(numbers))
    fetched = []
    for i, number in enumerate(numbers, 1):
        cached = bundle_path(config, number).exists()
        fetch_pr_bundle(client, config, number)
        fetched.append(number)
        if not cached:
            logger.info("  [%d/%d] fetched PR #%d", i, len(numbers), number)
    return fetched


def run_derive(
    config: PRReviewV2Config,
    logger,
    numbers: Optional[List[int]] = None,
) -> Tuple[List[PRReviewV2Record], List[SkipReason]]:
    roster = load_roster(config)
    numbers = numbers if numbers is not None else _cached_bundle_numbers(config)
    records: List[PRReviewV2Record] = []
    skips: List[SkipReason] = []
    for number in numbers:
        path = bundle_path(config, number)
        if not path.exists():
            logger.warning("No cached bundle for PR #%d; run fetch first", number)
            continue
        bundle = json.loads(path.read_text())
        result = derive_record(bundle, config, roster)
        if isinstance(result, SkipReason):
            skips.append(result)
        else:
            records.append(result)
    logger.info("Stage C: %d records, %d skipped", len(records), len(skips))
    return records, skips


def run_delta(
    client: GitHubClient,
    config: PRReviewV2Config,
    records: List[PRReviewV2Record],
    logger,
) -> List[PRReviewV2Record]:
    hydrated = []
    for i, record in enumerate(records, 1):
        hydrated.append(hydrate_record(record, client, config))
        if record.validation.hydration_error:
            logger.warning(
                "  [%d/%d] PR #%d hydration failed: %s",
                i, len(records), record.pr_number, record.validation.hydration_error,
            )
    return hydrated


def build_funnel_report(
    records: List[PRReviewV2Record], skips: List[SkipReason]
) -> Dict[str, Any]:
    slice_counts = Counter()
    for record in records:
        for name, value in record.slices.model_dump().items():
            if value:
                slice_counts[name] += 1
    return {
        "kept": len(records),
        "skipped": len(skips),
        "skip_reasons": dict(Counter(f"{s.stage}:{s.reason.split('=')[0]}" for s in skips)),
        "verdicts": dict(Counter(r.gold.verdict for r in records)),
        "slices": dict(slice_counts),
        "comments_total": sum(len(r.gold.comments) for r in records),
        "linked_comments": sum(
            1 for r in records for c in r.gold.comments if c.link_confidence != "none"
        ),
        "hydration_errors": sum(1 for r in records if r.validation.hydration_error),
    }


def write_outputs(
    records: List[PRReviewV2Record],
    skips: List[SkipReason],
    output_file: Path,
    logger,
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w") as fh:
        for record in records:
            fh.write(record.model_dump_json() + "\n")
    report = build_funnel_report(records, skips)
    report["skips_detail"] = [s.model_dump() for s in skips]
    funnel_file = output_file.with_name(output_file.stem + "_funnel.json")
    funnel_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    logger.info("Wrote %d records to %s", len(records), output_file)
    logger.info("Funnel report: %s", funnel_file)
    logger.info("Funnel summary: %s", {k: v for k, v in report.items() if k != "skips_detail"})


def main(
    stage: str = "all",
    config_path: Optional[Path] = None,
    cli_overrides: Optional[Dict[str, Any]] = None,
    logger=None,
) -> Optional[Path]:
    logger = logger or create_logger()
    config_dict: Dict[str, Any] = load_yaml(config_path) if config_path else {}
    if cli_overrides:
        config_dict = deep_merge(config_dict, cli_overrides)
    config = PRReviewV2Config.model_validate(config_dict)

    client = GitHubClient(
        config.github_token,
        timeout_seconds=config.timeout_seconds,
        request_interval_seconds=config.request_interval_seconds,
    )
    if not client.authenticated:
        logger.warning("No GitHub token: unauthenticated REST (60 req/h), GraphQL enrichment disabled")

    try:
        numbers: Optional[List[int]] = None
        if stage in {"fetch", "all"}:
            numbers = run_fetch(client, config, logger)
            if stage == "fetch":
                return None
        records, skips = run_derive(config, logger, numbers=numbers)
        if stage in {"delta", "all"}:
            records = run_delta(client, config, records, logger)
        output_file = _resolve_output_file(config)
        write_outputs(records, skips, output_file, logger)
        return output_file
    finally:
        client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mathlib first-round-review dataset (v2)")
    parser.add_argument("stage", nargs="?", default="all", choices=["fetch", "derive", "delta", "all"])
    parser.add_argument("--config", type=Path, default=None)
    args, remaining = parser.parse_known_args()
    result = main(stage=args.stage, config_path=args.config, cli_overrides=parse_cli_args(remaining))
    if result:
        print(result)
