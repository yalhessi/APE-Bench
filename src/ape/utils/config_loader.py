"""
Configuration utilities for loading YAML files and parsing CLI arguments.

Supports:
- YAML configuration files
- Dot-notation CLI overrides with Python literal syntax
- Deep merging of configurations

Priority: CLI overrides > YAML > Pydantic defaults

Examples:
    llm_config.temperature=0.7
    llm_config.streaming=False
    llm_config.api_key=None
    task_config.enabled_tools='["Read","Write"]'
"""

import sys
import ast
from pathlib import Path
from typing import List, Dict, Any


def load_yaml(yaml_path: Path) -> Dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        yaml_path: Path to YAML configuration file.

    Returns:
        Parsed configuration dictionary.

    Raises:
        FileNotFoundError: If YAML file does not exist.
        ValueError: If YAML file is invalid.
    """
    if not yaml_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

    import yaml
    with yaml_path.open('r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    if config is None:
        return {}

    if not isinstance(config, dict):
        raise ValueError(f"YAML configuration must be a dictionary, got {type(config).__name__}")

    return config


def parse_cli_args(argv: List[str] = None) -> Dict[str, Any]:
    """Parse dot-notation CLI arguments into nested dictionary.

    Uses Python literal syntax for values:
        True/False (not true/false)
        None (not null/none)
        Numbers: 123, 0.7
        Lists: '["Read","Write"]'
        Dicts: '{"key":"value"}'

    Examples:
        llm_config.temperature=0.7 → {"llm_config": {"temperature": 0.7}}
        llm_config.streaming=False → {"llm_config": {"streaming": False}}
        llm_config.api_key=None → {"llm_config": {"api_key": None}}
        task_config.enabled_tools='["Read","Write"]' → {"task_config": {"enabled_tools": ["Read", "Write"]}}

    Args:
        argv: Command-line argument list (defaults to sys.argv[1:]).

    Returns:
        Nested configuration dictionary.
    """
    if argv is None:
        argv = sys.argv[1:]

    config_dict = {}
    unparsed = []

    for arg in argv:
        if '=' in arg:
            key, value = arg.split('=', 1)
            _set_nested_value(config_dict, key, value)
        else:
            unparsed.append(arg)

    if unparsed:
        # Silently dropping these is how a documented command runs the wrong experiment. The
        # runbook checked into docs/research/medium-end-to-end-runbook.md spells overrides as
        # `--dataset.dry_run false` — space separated, `--` prefixed — and every token of it
        # was discarded here, so the command executed with the YAML's `dry_run: true` and the
        # previous run's output path. Refusing is the whole fix: the caller finds out at the
        # start rather than from a result that does not match what they asked for.
        raise ValueError(
            "unparsed command-line override(s): " + " ".join(unparsed) + "\n"
            "Overrides are `key.path=value` with no spaces and no leading dashes, e.g. "
            "`dataset.dry_run=False`. A token without `=` was previously ignored, which "
            "silently ran a different experiment than the command described."
        )

    return config_dict


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, with override taking precedence.

    Args:
        base: Base configuration dictionary.
        override: Override configuration dictionary.

    Returns:
        Merged configuration dictionary.
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def _set_nested_value(config_dict: Dict[str, Any], key_path: str, value_str: str) -> None:
    """Set nested dictionary value from dot-notation key path.

    Args:
        config_dict: Configuration dictionary to modify.
        key_path: Dot-separated key path (e.g., 'llm_config.temperature').
        value_str: String value to parse and set.
    """
    keys = key_path.split('.')
    current = config_dict

    # Navigate to the last level
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    # Set value with type conversion
    final_key = keys[-1]
    try:
        current[final_key] = ast.literal_eval(value_str)
    except (ValueError, SyntaxError):
        current[final_key] = value_str
