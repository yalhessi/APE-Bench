"""Compatibility wrapper for the APE-Agent interactive CLI."""

from __future__ import annotations

from typing import Optional, Sequence

from ape.cli.registry import get_agent_cli_spec
from ape.cli.shared import create_standalone_agent_parser, run_agent_alias


def create_argument_parser():
    """Create the standalone `apea` parser."""
    return create_standalone_agent_parser(get_agent_cli_spec("ape-agent"), prog="apea")


def cli_main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the standalone APE-Agent compatibility alias."""
    return run_agent_alias("ape-agent", argv=argv, prog="apea")


if __name__ == "__main__":
    raise SystemExit(cli_main())
