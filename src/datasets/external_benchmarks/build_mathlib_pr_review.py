#!/usr/bin/env python3
"""
Backward-compatible wrapper for PR-review benchmark extraction.

New primary entry point:
  python -m src.datasets.pr_review.main ...
"""

from pathlib import Path
import argparse

from ape.utils import parse_cli_args
from ape.utils.logging import create_logger

try:
    from src.datasets.pr_review.main import main as run_pr_review_pipeline
except ImportError:  # pragma: no cover
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from datasets.pr_review.main import main as run_pr_review_pipeline


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Mathlib PR review benchmark from GitHub PRs (wrapper)."
    )
    parser.add_argument("--config", type=Path, default=None, help="Path to YAML config file")
    return parser


def main() -> None:
    logger = create_logger()
    parser = create_argument_parser()
    args, remaining = parser.parse_known_args()
    output_file = run_pr_review_pipeline(
        config_path=args.config,
        cli_overrides=parse_cli_args(remaining),
        logger=logger,
    )
    print(output_file)


if __name__ == "__main__":
    main()
