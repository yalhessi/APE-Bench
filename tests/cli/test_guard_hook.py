"""`.claude/hooks/guard.sh` refuses a commit gated on a pipeline.

In `check | tail && git commit` the commit waits on tail's exit status, not the check's. CLAUDE.md
recorded it after a red suite was committed that way (2026-09-23), and on 2026-10-01 a failing
script went in the same way (`| tail -3 && git add && git commit`). A rule in prose did not stop
it, so the hook refuses the shape. These cases pin what it refuses and what it must let through:
every commit shape this repository uses, including pipes inside a commit message.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / ".claude" / "hooks" / "guard.sh"
COMMIT = "git " + "commit"

CASES = {
    f"ape/bin/python s.py | tail -3 && git add f && {COMMIT} -q -m 'x'": "deny",
    f"pytest tests -q | tail -2 && {COMMIT} -m 'x'": "deny",
    f"set -o pipefail; pytest tests -q | tail -2 && {COMMIT} -m 'x'": "allow",
    f"pytest tests -q > out.txt 2>&1; rc=$?; git add f && {COMMIT} -q -F - <<'EOF'\na | b && c\nEOF": "allow",
    f"git add a b && {COMMIT} -q -m 'probes: x -- a | b'": "allow",
    f"git log | head -3; git add a && {COMMIT} -q -m 'x'": "allow",
    f"test -f a || touch a && git add a && {COMMIT} -m 'x'": "allow",
    f"grep x f | wc -l\ngit add f && {COMMIT} -m 'x'": "allow",
}


@pytest.mark.skipif(not (shutil.which("bash") and shutil.which("jq")), reason="guard.sh needs bash and jq")
@pytest.mark.parametrize("command,expected", CASES.items())
def test_a_commit_gated_on_a_pipeline_is_refused(command, expected, tmp_path):
    # Outside any repository, so the branch rule (no commit on main) cannot answer for this one.
    payload = json.dumps({"tool_name": "Bash", "cwd": str(tmp_path), "tool_input": {"command": command}})
    out = subprocess.run(["bash", str(GUARD)], input=payload, capture_output=True, text=True).stdout
    assert ("deny" if '"deny"' in out else "allow") == expected, (command, out)
