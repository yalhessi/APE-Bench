"""The run summary names billed and nominal cost, so neither is reported as the other."""
import asyncio, json
from types import SimpleNamespace

from ape.orchestration.persistence import print_summary


def test_the_summary_labels_billed_and_nominal_cost(tmp_path):
    sample = tmp_path / "task" / "samples" / "0"
    sample.mkdir(parents=True)
    (sample / "sample.json").write_text(json.dumps({"attempts": [{"cost": 5.9, "cached_cost": 2.81}]}))
    results = SimpleNamespace(
        orchestrator_id="o", scaffold_type="s", completed_tasks=1, total_tasks=1, completion_rate=1.0,
        successful_tasks=1, success_rate=1.0, passed_tasks=1, pass_rate_local=1.0,
        pass_rate_global=1.0, average_score=1.0, wall_clock_time=1.0, workspace_path=tmp_path)
    lines = []
    asyncio.run(print_summary(results, tmp_path, SimpleNamespace(info=lines.append)))
    text = "".join(lines)
    plain = __import__("re").sub(r"\x1b\[[0-9;]*m", "", text)
    assert "Billed: $2.8100" in plain
    assert "(nominal $5.9000)" in plain
