"""`.claude/skills/spawn-session/spawn.sh` -- what a spawned session inherits, and what it refuses.

The user's rule (2026-10-02): model and effort default to the spawning session's own. They are read
from its transcript, where each assistant entry carries `message.model` and `effort` and user
entries carry `permissionMode`; a `<synthetic>` model entry is not a model. Every refusal fires
before a worktree or a session exists, so these run in a scratch repository and start nothing.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPAWN = ROOT / ".claude" / "skills" / "spawn-session" / "spawn.sh"

pytestmark = pytest.mark.skipif(not (shutil.which("jq") and shutil.which("git")), reason="spawn.sh needs jq and git")


def run(args, cwd, **env):
    full = {"PATH": "/usr/bin:/bin", "HOME": str(cwd), **env}
    return subprocess.run(["bash", str(SPAWN), *args], cwd=cwd, env=full, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def test_defaults_are_the_spawning_sessions_latest_model_effort_and_mode(repo):
    entries = [
        {"type": "user", "permissionMode": "default"},
        {"type": "assistant", "message": {"model": "claude-sonnet-5-5"}, "effort": "medium"},
        {"type": "user", "permissionMode": "bypassPermissions"},
        {"type": "assistant", "message": {"model": "claude-opus-5-5"}, "effort": "xhigh"},
        {"type": "assistant", "message": {"model": "<synthetic>"}},
    ]
    transcript = repo / "t.jsonl"
    transcript.write_text("".join(json.dumps(e) + "\n" for e in entries))
    out = run(["defaults"], repo, SPAWN_TRANSCRIPT=str(transcript))
    assert out.returncode == 0, out.stderr
    assert out.stdout.split() == ["model=claude-opus-5-5", "effort=xhigh", "permission-mode=bypassPermissions"]


REFUSALS = {
    "spawned sessions do not spawn": (["start", "t1", "--brief", "b.md"], {"APE_SPAWNED_BY": "abc"}, "do not spawn"),
    "topic is branch-safe": (["start", "Bad Topic", "--brief", "b.md"], {}, "branch-safe"),
    "the brief is a file": (["start", "t1"], {}, "--brief <file> is required"),
    "effort is one claude accepts": (
        ["start", "t1", "--brief", "b.md", "--model", "m", "--effort", "huge", "--permission-mode", "auto"], {}, "effort 'huge'"),
    "no transcript, no silent default": (["start", "t1", "--brief", "b.md"], {}, "cannot find this session's transcript"),
    "bypass needs the CLI's own disclaimer": (
        ["start", "t1", "--brief", "b.md", "--model", "m", "--effort", "high", "--permission-mode", "bypassPermissions"],
        {}, "disclaimer accepted once"),
}


def test_report_is_the_last_text_and_wait_returns_once_it_is_not_busy(repo):
    sid = "f1d15fff-0000-0000-0000-000000000000"
    bin_ = repo / "bin"
    bin_.mkdir()
    fake = bin_ / "claude"  # `claude agents --json [--all]`: one idle background session
    row = {"name": "probe", "sessionId": sid, "kind": "background", "status": "idle", "cwd": str(repo)}
    fake.write_text(f"#!/bin/sh\necho '{json.dumps([row])}'\n")
    fake.chmod(0o755)
    project = repo / ".claude" / "projects" / "-x"
    project.mkdir(parents=True)
    entries = [
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "working"}]}},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read"}]}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Report: done."}]}},
    ]
    (project / f"{sid}.jsonl").write_text("".join(json.dumps(e) + "\n" for e in entries))
    path = f"{bin_}:/usr/bin:/bin"
    out = run(["report", "probe"], repo, PATH=path)
    assert out.returncode == 0, out.stderr
    assert out.stdout.splitlines()[-1] == "Report: done." and "idle" in out.stdout
    assert run(["wait", "f1d15fff"], repo, PATH=path).returncode == 0  # idle: returns at once


@pytest.mark.parametrize("args,env,message", REFUSALS.values(), ids=REFUSALS.keys())
def test_refuses_before_anything_is_created(repo, args, env, message):
    (repo / "b.md").write_text("Thread: x.\n")
    out = run(args, repo, **env)
    assert out.returncode != 0 and message in out.stderr, out.stderr
    assert not (repo / ".claude" / "worktrees").exists()
