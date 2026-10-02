"""`.claude/hooks/lib.sh` counts the Claude Code sessions sharing a working tree.

The tree-rewrite and stash refusals in `guard.sh` and the `[session]` line rest on it. A background
session (`claude --bg`) runs the versioned binary itself, `~/.local/share/claude/versions/<v>`, under
a pty host that retitles itself into one string holding that same path; on 2026-10-02 neither was
recognised, so a `--bg` session in this checkout was invisible. Each case is a process faked with
`exec -a` in a scratch repository: what it is named, and whether it counts as a session there.
"""

import shutil
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / ".claude" / "hooks" / "lib.sh"
VERSIONED = "/home/u/.local/share/claude/versions/2.1.287"

PROCESSES = {
    "background session": (VERSIONED, True),
    "native binary": ("claude", True),
    "pty host": (f"claude bg-pty-host --bg-pty-host /tmp/d/pty/x.sock 200 50 -- {VERSIONED} --session-id x", False),
    "spare": ("claude bg-spare --bg-spare /tmp/d/spare/x.claim.sock", False),
    "versions directory itself": ("/home/u/.local/share/claude/versions/", False),
}


@pytest.mark.skipif(not (Path("/proc").is_dir() and shutil.which("pgrep") and shutil.which("git")),
                    reason="lib.sh reads /proc and needs pgrep and git")
def test_a_background_session_counts_and_its_pty_host_does_not(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    procs = {}
    try:
        for label, (argv0, _) in PROCESSES.items():
            procs[label] = subprocess.Popen(["bash", "-c", 'exec -a "$0" sleep 60', argv0], cwd=repo)
        for label, p in procs.items():  # wait until bash has exec'd into the faked name
            cmdline = Path(f"/proc/{p.pid}/cmdline")
            for _ in range(100):
                if cmdline.read_bytes().split(b"\0")[0].decode() == PROCESSES[label][0]:
                    break
                time.sleep(0.02)
        out = subprocess.run(["bash", "-c", f'source "{LIB}"; sessions_sharing_tree'], cwd=repo,
                             capture_output=True, text=True, check=True).stdout.split()
        counted = {label for label, p in procs.items() if str(p.pid) in out}
        assert counted == {label for label, (_, expected) in PROCESSES.items() if expected}
    finally:
        for p in procs.values():
            p.kill()
            p.wait()
