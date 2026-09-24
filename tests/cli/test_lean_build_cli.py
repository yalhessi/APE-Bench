"""The batch-build CLI hands its flags to the config the workers build with."""

from __future__ import annotations

import asyncio

from ape.toolkits.execute.lean import build


class _RecordingBuilder:
    """Stands in for `BatchBuilder` only to capture the config it is constructed with."""

    seen = []

    def __init__(self, config, logger):
        type(self).seen.append(config)

    async def build_from_file(self, **_kwargs):
        return {"total_commits": 0, "successful_builds": 0, "failed_builds": 0, "success_rate": 1.0}


def test_build_timeout_reaches_the_config_the_workers_build_with(monkeypatch):
    monkeypatch.setattr(build, "BatchBuilder", _RecordingBuilder)
    args = build.create_argument_parser().parse_args(
        ["--target_repo", "https://github.com/leanprover-community/mathlib4.git@@abc123",
         "--build_timeout", "5400", "--num_processes", "2"])
    assert asyncio.run(build.run_batch_build(args)) == 0
    config = _RecordingBuilder.seen[-1]
    assert isinstance(config, build.LeanVerifyToolConfig)
    assert config.build_timeout == 5400
    assert config.num_processes == 2
    # The workers receive the config as `model_dump`, so the timeout travels with it.
    assert config.model_dump(mode="json")["build_timeout"] == 5400


def test_an_input_file_that_yields_no_commit_is_a_failure_not_a_success(monkeypatch, tmp_path):
    monkeypatch.setattr(build, "BatchBuilder", _RecordingBuilder)          # reports 0 commits
    records = tmp_path / "bases.jsonl"
    records.write_text('{"commit_hash": "abc123"}\n')                     # not BaseLeanTaskData
    args = build.create_argument_parser().parse_args(["--input_file", str(records)])
    assert asyncio.run(build.run_batch_build(args)) == 1
