---
name: spawn-session
description: Start a thread in its own background Claude Code session -- a topic branch and worktree off develop, a written brief, model and effort defaulting to this session's -- then watch it, read its report, and finish it. Use when a planning session should keep work moving without a person, e.g. "spawn a session for <todo>", "start phase 1 in a fresh session", "hand this thread off", or when CLAUDE.md's one-thread-per-session rule says a new thread needs a fresh session and the user wants it started rather than recommended.
---

# Spawn a session for a thread

CLAUDE.md keeps one thread per session and one working tree per session. This skill lets a
planning session act on that instead of only recommending it: it starts the thread in a background
session (`claude --bg`) in its own worktree, and stays the place where results come back.

## Before you spawn

1. **The thread is not already in flight.** `git worktree list`, `git log --oneline develop..<branch>`
   for the likely branches, and `claude agents --json`: a plan in flight lives on its branch
   (CLAUDE.md, Session discipline). Check `docs/dead-ends.md` for the direction too.
2. **The brief is on disk.** A spawned session starts from a file, never from this conversation,
   which it cannot see. Point it at the todo entry (`docs/todo/<x>.md`, its `Start here` block) or
   the plan phase (`docs/plans/<date>-*.md`); if neither says enough, write that down first, in
   the todo or plan, and commit it, so the brief can be three lines.
3. **It spends nothing unless you say so.** Every spawned session is told to run nothing with
   `--execute` and no paid call unless its brief names that exact command. A paid run follows
   the user's paid-run care (working key, first minutes watched), which nobody can do for a
   session that runs alone -- authorize one only when the user has asked for it.
4. **It draws on the same subscription.** A child's tokens come out of the same five-hour and
   weekly windows as yours and the user's interactive use. Start the threads that are ready, not
   every open todo.

## The brief

Write it to a scratch file. It names the thread, the reading list, the deliverable and the close
condition; the standing rules (commit per step on the topic branch, never merge, spend nothing,
do not spawn, no AskUserQuestion, end with a report) are appended to the child's system prompt
by `spawn.sh`, so do not repeat them.

```markdown
Thread: <one line -- what this session is for>.
Read first: docs/todo/<x>.md (Start here), then <plan or commit>.
Deliver: <the built change and the one measurement, with its pre-stated threshold>.
Done when: <close condition from the todo>. Stop there and report.
```

## Spawn

```bash
.claude/skills/spawn-session/spawn.sh start <topic> --brief <file> \
  [--model <id>] [--effort low|medium|high|xhigh|max] [--permission-mode <mode>] [--base <ref>]
```

- **Model, effort and permission mode default to this session's own**, read from this session's
  transcript (`spawn.sh defaults` prints what it would use). Pass the user's choice when they name
  one: "spawn it on Sonnet at medium" is `--model claude-sonnet-5-5 --effort medium`. The model is
  recorded without a context-window variant; pass `--model` explicitly if one matters.
- **The permission mode decides whether it can run alone.** `bypassPermissions` and `auto` can;
  `claude --bg` refuses each until the user has opted in once, interactively, in the CLI itself
  (`claude --dangerously-skip-permissions`, `claude --permission-mode auto`) -- VSCode's own
  bypass setting does not count. Accepting bypass writes `skipDangerousModePermissionPrompt: true`
  to `~/.claude/settings.json` (2.1.287), and `spawn.sh` refuses bypass early without it. `dontAsk` denies every call not on an allow list, and `manual`/`acceptEdits` stop at the
  first prompt with nobody to answer it.
- `<topic>` names the branch, the worktree (`.claude/worktrees/<topic>`) and the session. A new
  topic branches from `--base` (default `develop`); an existing branch or worktree of that name is
  reused, unless a session is already working in it (refused: one working tree per session).
- It refuses inside a spawned session (`APE_SPAWNED_BY` is set there), so threads fan out one
  level only.

**`claude --bg` does not survive the parent's restart.** Its daemon (`/tmp/cc-daemon-<uid>/…/control.sock`)
lives in the login-session scope, and a restart of the spawning session tears that scope down: on
2026-10-07 the `review-ir` child and its seven agents died at 07:46 with the parent, `claude logs`
answering `ECONNREFUSED`, nothing committed since its start. CLAUDE.md records the same for paid runs
(`setsid nohup` is not enough). What survived: a headless session as a systemd user unit, outside the
scope -- `systemd-run --user --collect --unit=<topic>-session --working-directory=<worktree>
--setenv=PATH=$PATH --setenv=HOME=$HOME --setenv=APE_SPAWNED_BY=<parent> /bin/bash -c "exec claude -p
\"$(cat <brief>)\" --model … --effort … --permission-mode bypassPermissions --append-system-prompt
\"$(cat <rules>)\" --output-format stream-json --verbose >> <log> 2>&1 < /dev/null"`, its cgroup under
`user@<uid>.service/app.slice`. Print mode ends with its turn, so the rules must tell it to run its
subagents in the foreground (several per message), never left in the background; watch it with
`systemctl --user status <topic>-session` and the log. Until `spawn.sh` does this itself, use it for
any child that must outlive the parent.

Right after it prints `spawned <topic> · <id>`, arrange to be woken when it finishes: run
`.claude/skills/spawn-session/spawn.sh wait <id>` with Bash `run_in_background`; the harness
re-invokes you when it returns. Beside it, `SendMessage` with `to: "<topic>"`,
`notify_when_idle: true` and no message: from a child in your own permission mode (the default)
the notice arrives with a one-line summary of its report; from one in another mode it is only
logged (2026-10-02: a `dontAsk` child of a bypass parent). The notice is one-shot, the waiter is not.

## While it runs, and when it is done

- `spawn.sh report <id|topic>` prints its status and its last message -- its report, once it is idle.
- `claude logs <id>` shows its terminal; `claude attach <id>` opens it in a terminal, live.
- **The user sees it in VSCode** only in a window opened on its worktree folder; the main
  checkout's Session history does not list another worktree's sessions. Opening it there while
  it runs warns "still open somewhere else" and two writers would mix its transcript, so
  `claude stop <id>` first (the conversation is kept), then open it.
- To answer it or redirect it, `SendMessage` to `<topic>`.

When the report says the thread succeeded, merging its branch into `develop` is a step of its own
(CLAUDE.md, Git: merge only when it succeeds; regenerate shared artifacts as part of the merge). If
it was abandoned, its `docs/dead-ends.md` entry comes before the branch goes. Then
`claude stop <id>` and `claude rm <id>`; `rm` keeps the transcript and leaves a worktree that
`spawn.sh` made, so remove that with `git worktree remove` once the branch is merged or recorded.

## Facts this rests on (2026-10-02, CLI 2.1.287)

- `claude --bg` refuses a directory that was never trusted; worktrees under this repository are
  trusted with it.
- A background session runs from `~/.local/share/claude/versions/<v>` under a background service
  that keeps itself updated, so it can run a newer CLI than `claude` in the shell.
- The hooks count background sessions in their tree since `9362a620`
  (`tests/cli/test_hook_sessions.py`); before that a `--bg` session was invisible to the guard.
- Background sessions are disabled wherever `disableAgentView` or `CLAUDE_CODE_DISABLE_AGENT_VIEW=1`
  is set.
