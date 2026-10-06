"""`.claude/hooks/commit-note.sh` notes a commit that mixed a framework file with an exploration file.

About half the files of every wide thread were fixes to shared machinery committed together with
the exploration that found them (`docs/research/codebase-redesign-2026-10.md` §1.3). The hook runs
after a commit, reads what actually went in, and adds a note for the session -- never a refusal,
since a mixed commit is often right. These cases pin when it speaks and when it stays quiet.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / ".claude" / "hooks" / "commit-note.sh"
COMMIT = "git " + "commit"

pytestmark = pytest.mark.skipif(not (shutil.which("bash") and shutil.which("jq") and shutil.which("git")),
                                reason="the hook needs bash, jq and git")

ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@t"}


def _repo(tmp_path: Path, files) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, env=ENV)
    (repo / "README").write_text("x")
    subprocess.run(["git", "add", "README"], cwd=repo, check=True, env=ENV)
    subprocess.run(["git", "commit", "-q", "-m", "root"], cwd=repo, check=True, env=ENV)
    for name in files:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")
        subprocess.run(["git", "add", name], cwd=repo, check=True, env=ENV)
    if files:
        subprocess.run(["git", "commit", "-q", "-m", "change"], cwd=repo, check=True, env=ENV)
    return repo


def _note(repo: Path, command: str) -> str:
    payload = json.dumps({"tool_name": "Bash", "cwd": str(repo), "tool_input": {"command": command}})
    out = subprocess.run(["bash", str(HOOK)], input=payload, capture_output=True, text=True).stdout
    if not out.strip():
        return ""
    return json.loads(out)["hookSpecificOutput"]["additionalContext"]


@pytest.mark.parametrize("files,speaks", [
    (["src/mathlib_review/review/runner.py", "configs/designs/x.yaml"], True),
    (["src/ape/toolkits/execute/lean/tools.py",
      "src/ape/tasks/lean_tasks/formal_math/review/focused_prompts.py"], True),
    (["src/mathlib_review/schema/findings.py", "results/pr_review_v5/probes/p/README.md"], True),
    (["src/mathlib_review/review/runner.py", "tests/datasets/test_x.py", "docs/x.md"], False),
    (["configs/designs/x.yaml", "src/mathlib_review/evidence/operators/naming_norm.py"], False),
    (["src/mathlib_review/analysis/report.py", "configs/x.yaml"], False),
])
def test_it_speaks_only_when_a_framework_file_and_an_exploration_file_share_a_commit(
        tmp_path, files, speaks):
    repo = _repo(tmp_path, files)
    note = _note(repo, f"git add -A && {COMMIT} -q -m 'x'")
    assert bool(note) == speaks, note
    if speaks:
        assert "Nothing was blocked" in note and files[0] in note


def test_it_is_silent_after_a_command_that_is_not_a_commit(tmp_path):
    repo = _repo(tmp_path, ["src/mathlib_review/review/runner.py", "configs/x.yaml"])
    assert _note(repo, "git log --oneline -1") == ""


def test_it_is_silent_when_the_head_commit_is_old(tmp_path):
    """A commit that failed leaves an older HEAD; the note must not describe that one."""
    repo = _repo(tmp_path, [])
    for name in ("src/mathlib_review/review/runner.py", "configs/x.yaml"):
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text("x")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, env=ENV)
    old = {**ENV, "GIT_COMMITTER_DATE": "2020-01-01T00:00:00", "GIT_AUTHOR_DATE": "2020-01-01T00:00:00"}
    subprocess.run(["git", "commit", "-q", "-m", "old"], cwd=repo, check=True, env=old)
    assert _note(repo, f"{COMMIT} -q -m 'x'") == ""
