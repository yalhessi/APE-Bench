"""
PR review benchmark pipeline entry point.

Usage examples:
  python -m src.datasets.pr_review.main start_date=2025-01-01 end_date=2025-03-31
  python -m src.datasets.pr_review.main --config configs/pr_review_config.yaml
"""

import argparse
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING

from ape.utils.logging import create_logger
from ape.utils import parse_cli_args, load_yaml, deep_merge

from .collector import PRReviewDataCollector
from .config import PRReviewDatasetConfig
from .materialize_outputs import materialize_hybrid_outputs

if TYPE_CHECKING:
    import logging


class PRReviewDatasetPipeline:
    """Pipeline for extracting PR review benchmark records from GitHub."""

    def __init__(
        self,
        config: PRReviewDatasetConfig,
        logger: Optional["logging.LoggerAdapter"] = None,
    ):
        self.config = config
        self.logger = logger or create_logger()
        self.output_file = self._resolve_output_file()
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

    def _config_hash(self) -> str:
        exclude = {"output_file", "dataset_dir", "github_token"}
        payload = json.dumps(
            self.config.model_dump(mode="json", exclude=exclude),
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.md5(payload.encode("utf-8")).hexdigest()[:12]

    def _resolve_output_file(self) -> Path:
        if self.config.output_file:
            return self.config.output_file

        date_part = self.config.start_date or "begin"
        if self.config.end_date:
            date_part = f"{date_part}_to_{self.config.end_date}"

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        cfg_hash = self._config_hash()
        filename = f"mathlib_pr_review_{date_part}_{cfg_hash}_{timestamp}.jsonl"
        return self.config.dataset_dir / filename

    def run(self) -> Path:
        start_time = time.time()
        collector = PRReviewDataCollector(config=self.config, logger=self.logger)

        self.logger.info("Starting PR review dataset extraction")
        self.logger.info(f"Repository: {self.config.repo_owner}/{self.config.repo_name}")
        self.logger.info(f"Output file: {self.output_file}")

        try:
            records = collector.collect_records()
            materialized_outputs = materialize_hybrid_outputs(
                records,
                self.output_file,
                skill_bundle=self.config.variant_skill_bundle,
                write_aggregate=True,
                create_variants=self.config.create_variant_outputs,
            ) if self.config.materialize_slice_outputs else {"aggregate": self.output_file}
            if not self.config.materialize_slice_outputs:
                collector.save_records(records, self.output_file)
            summary = collector.build_summary(records)

            elapsed = time.time() - start_time
            self.logger.info(
                "Extraction completed: records=%d, unique_prs=%d, merge_ready_true=%d, merge_ready_false=%d, elapsed=%.2fs",
                summary["records"],
                summary.get("unique_prs", 0),
                summary["merge_ready_true"],
                summary["merge_ready_false"],
                elapsed,
            )
            if summary["skip_reasons"]:
                self.logger.info(f"Skip reasons: {summary['skip_reasons']}")
            self.logger.info("Materialized outputs: %s", {key: str(path) for key, path in materialized_outputs.items()})

            return self.output_file
        finally:
            collector.close()


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Mathlib PR review benchmark from GitHub PRs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--config", type=Path, default=None, help="Path to YAML config file")
    return parser


def main(
    config_path: Optional[Path] = None,
    cli_overrides: Optional[Dict[str, Any]] = None,
    logger: Optional["logging.LoggerAdapter"] = None,
) -> Path:
    logger = logger or create_logger()

    config_dict: Dict[str, Any] = load_yaml(config_path) if config_path else {}
    if cli_overrides:
        config_dict = deep_merge(config_dict, cli_overrides)

    config = PRReviewDatasetConfig.model_validate(config_dict)
    pipeline = PRReviewDatasetPipeline(config=config, logger=logger)
    return pipeline.run()


if __name__ == "__main__":
    cli_logger = create_logger()
    parser = create_argument_parser()
    args, remaining = parser.parse_known_args()
    output_file = main(
        config_path=args.config,
        cli_overrides=parse_cli_args(remaining),
        logger=cli_logger,
    )
    print(output_file)
