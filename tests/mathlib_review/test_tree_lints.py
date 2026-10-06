"""Two lints on where exploration code and prompt text live (2026-10-06).

`docs/research/codebase-redesign-2026-10.md` §1.5 measured where new code lands: 112 researcher
scripts under `results/`, most importing nothing from `src/`, re-reading runs by hand -- globbing
the orchestrator's directory layout and splitting JSONL with `splitlines()`, both of which the
rules file forbids -- and nine configs reading the reviewer's brief from a probe directory, so
prompt text depends on the results tree rather than the other way round.

Both lints are ratchets with exact allow-lists. The scripts and configs already there are the
record of what ran and stay as they are; a new one may not join them, and an entry that stops
offending (fixed, or deleted) must leave its list, so each list only shrinks. Only tracked files
are read: an untracked script another session is writing in the shared checkout must not turn
every session's suite red (CLAUDE.md, the 2026-09-24 entry on shared data stores).
"""

from __future__ import annotations

import ast
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="reads the tracked tree")


def _tracked(pattern: str):
    out = subprocess.run(["git", "ls-files", pattern], capture_output=True, text=True, check=True)
    return [Path(line) for line in out.stdout.split("\n") if line]


# --- results scripts read runs through src, not by hand -----------------------------------

#: The orchestrator's layout below a task: `samples/<n>/attempts/attempt_<id>_<stamp>/`. A script
#: that globs it picks attempts by path instead of by the persisted sample (`TaskStorage`), which
#: is the defect class `analysis/runs.py` was written to end.
LAYOUT = re.compile(r"attempts/\*|samples/\*|samples/0/attempts|attempt_\*")

#: Every tracked researcher script that offended on 2026-10-06. Agents' scratch under `tmp/` is
#: not researcher code and is not read. What to use instead: `StageInput.of(run)` for a run's
#: artifacts and its audit, `TaskStorage(...).load_all_samples()` for attempts,
#: `io.jsonl_rows` for JSONL, `cli report conditions` for the per-obligation spine and `cli
#: report tools` for tool outcomes.
READS_RUNS_BY_HAND = frozenset({
    "results/pr_review_v5/adjudications/coordination-design-check-2026-09-29/analyse.py",
    "results/pr_review_v5/probes/carryover-coherence-2026-09-30/coherence.py",
    "results/pr_review_v5/probes/claude-models-2026-10-01/consistency.py",
    "results/pr_review_v5/probes/claude-models-2026-10-01/hygiene_reading.py",
    "results/pr_review_v5/probes/claude-models-2026-10-01/tool_outcomes.py",
    "results/pr_review_v5/probes/construction-demo-2026-09-29/build_model.py",
    "results/pr_review_v5/probes/construction-demo-2026-09-29/unblind.py",
    "results/pr_review_v5/probes/contract-2026-10-01/focus.py",
    "results/pr_review_v5/probes/lean-build-2026-10-03/classify_edits.py",
    "results/pr_review_v5/probes/lean-build-2026-10-03/compile_share.py",
    "results/pr_review_v5/probes/lean-build-2026-10-03/compile_times.py",
    "results/pr_review_v5/probes/lean-build-2026-10-03/replay_bench.py",
    "results/pr_review_v5/probes/lean-build-2026-10-03/replay_bench_v2.py",
    "results/pr_review_v5/probes/lean-build-2026-10-03/replay_sessions.py",
    "results/pr_review_v5/probes/phase1-residual-mechanisms-2026-09-30/build_packets.py",
    "results/pr_review_v5/probes/postcutoff-2026-09-29/make_packets.py",
    "results/pr_review_v5/probes/postcutoff-2026-09-29/restore_bases.py",
    "results/pr_review_v5/probes/review-designs-2026-10-02/eof_linter_check.py",
    "results/pr_review_v5/probes/review-designs-2026-10-02/session_waste.py",
    "results/pr_review_v5/probes/review-designs-2026-10-02/smoke_structured.py",
    "results/pr_review_v5/probes/review-designs-2026-10-02/smoke_structured_critic.py",
    "results/pr_review_v5/probes/static-pass-2026-10-01/standard_set_alone.py",
    "results/pr_review_v5/probes/transcript-inspection-2026-09-30/process_profile.py",
})


def _is_call(node, attr: str, owner: str = None) -> bool:
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == attr
            and (owner is None or (isinstance(node.func.value, ast.Name)
                                   and node.func.value.id == owner)))


def _splits_jsonl_by_hand(tree) -> bool:
    """A loop or comprehension over `x.splitlines()` that calls `json.loads` on what it yields.
    Splitting a diff or a log is fine; parsing JSON lines that way cuts a record at U+2028."""

    for node in ast.walk(tree):
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            heads = [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]
            body = heads + [cond for gen in node.generators for cond in gen.ifs]
            iters = [gen.iter for gen in node.generators]
        elif isinstance(node, ast.For):
            body, iters = node.body, [node.iter]
        else:
            continue
        if any(_is_call(it, "splitlines") for it in iters) and any(
                _is_call(sub, "loads", "json") for part in body for sub in ast.walk(part)):
            return True
    return False


def reads_runs_by_hand(path: Path) -> list:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    kinds = []
    if any(isinstance(n, ast.Constant) and isinstance(n.value, str) and LAYOUT.search(n.value)
           for n in ast.walk(tree)):
        kinds.append("globs the attempt layout")
    if _splits_jsonl_by_hand(tree):
        kinds.append("splits JSONL with splitlines()")
    return kinds


def test_no_new_results_script_reads_runs_by_hand():
    offending = {str(path): kinds for path in _tracked("results/*.py")
                 if "tmp" not in path.parts and (kinds := reads_runs_by_hand(path))}
    new = {path: kinds for path, kinds in offending.items() if path not in READS_RUNS_BY_HAND}
    assert not new, (
        "a results script reads runs by hand; use StageInput.of, TaskStorage, io.jsonl_rows, "
        "`cli report conditions` or `cli report tools`:\n"
        + "\n".join(f"  {path}: {', '.join(kinds)}" for path, kinds in sorted(new.items())))
    gone = sorted(READS_RUNS_BY_HAND - set(offending))
    assert not gone, ("these no longer offend; remove them from READS_RUNS_BY_HAND so the list "
                      "only shrinks:\n" + "\n".join(f"  {path}" for path in gone))


@pytest.mark.parametrize("source,expected", [
    ('rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]',
     ["splits JSONL with splitlines()"]),
    ('for line in text.splitlines():\n    row = json.loads(line)', ["splits JSONL with splitlines()"]),
    ('hunks = [h for h in diff.splitlines() if h.startswith("@@")]\nx = json.loads(s)', []),
    ('glob.glob(str(base / "tasks/*/samples/0/attempts/*/x.jsonl"))', ["globs the attempt layout"]),
    ('rows = jsonl_rows(path)', []),
])
def test_the_lint_reads_the_two_shapes_and_nothing_else(tmp_path, source, expected):
    script = tmp_path / "s.py"
    script.write_text(source)
    assert reads_runs_by_hand(script) == expected


# --- prompt text is not read from the results tree ----------------------------------------

#: Configs that name the reviewer's brief under `results/` on 2026-10-06. Prompt text is an
#: input, and an input that lives in a probe's results directory makes the experiment depend on
#: its own output tree. A new brief goes beside the design that reads it. `context_file` is
#: different -- probe-produced *data*, which never moves -- and is not linted.
PROMPT_FROM_RESULTS = frozenset({
    "configs/pr_review_v5_dev_medium_gpt52_G.yaml",
    "configs/pr_review_v5_dev_medium_gpt52_Grc_contract2.yaml",
    "configs/pr_review_v5_probe_2026_07_08_v1_gpt52_G.yaml",
    "configs/pr_review_v5_probe_2026_07_08_v1_gpt52_K.yaml",
    "configs/pr_review_v5_probe_2026_07_08_v1_gpt54_Grc_bar.yaml",
    "configs/pr_review_v5_probe_2026_07_08_v1_gpt55_Grc_bar.yaml",
    "configs/pr_review_v5_val_small12_gpt52_G.yaml",
    "configs/pr_review_v5_val_small12_gpt54_Grc_bar.yaml",
    "configs/pr_review_v5_val_small12_gpt55_Grc_bar.yaml",
})

PROMPT_KEYS = ("system_prompt_file",)


def _prompt_paths(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in PROMPT_KEYS and isinstance(value, str):
                yield value
            else:
                yield from _prompt_paths(value)
    elif isinstance(node, list):
        for item in node:
            yield from _prompt_paths(item)


def test_no_new_config_reads_its_brief_from_results():
    offending = set()
    for path in _tracked("configs/*.yaml"):
        if any(Path(p).parts[:1] == ("results",)
               for p in _prompt_paths(yaml.safe_load(path.read_text(encoding="utf-8")))):
            offending.add(str(path))
    new = sorted(offending - PROMPT_FROM_RESULTS)
    assert not new, ("a config reads its brief from results/; put the brief beside the design "
                     "that reads it:\n" + "\n".join(f"  {p}" for p in new))
    gone = sorted(PROMPT_FROM_RESULTS - offending)
    assert not gone, ("these no longer read a brief from results/; remove them from "
                      "PROMPT_FROM_RESULTS so the list only shrinks:\n"
                      + "\n".join(f"  {p}" for p in gone))
