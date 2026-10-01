"""The reviewer-model probe, as one harness over any set (`docs/plans/2026-09-29-probe-harness.md`).

The probe compares reviewers on one PR at a time against the asks its maintainers made in round 1:
Claude sessions driven through `cli tool`, the pipeline's `gpt_5.2` conditions through `cli run`, and
blind matchers between them. Until 2026-09-29 each step was a script under `results/…/probes/`
hard-coded to one set. This module is those steps with the set as a parameter; the scripts stay where
they are as the record of what ran, and the tests hold this module to their committed outputs on the
post-cutoff set.

A set is a `ProbeSet`, read from `configs/probe_sets/<name>.yaml`.

**Order is part of the method.** Feedback is extracted only after every reviewer session on the set
has finished, and nothing a reviewer reads is written by a step that has seen feedback. The
extractor refuses a test-set PR, as the one it replaces did.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

#: The sealed test set: run once, never probed.
TEST_MANIFEST = Path("inputs/pr_review_v4/releases/eval-2025-06-2026-03-v1/manifest.json")
#: The roster the post-cutoff and validation extractions used; a PR-list source reads it too.
DEFAULT_ROSTER = Path("inputs/pull_requests/rosters/mathlib_roster_2026-09-11.txt")
REPO = "leanprover-community/mathlib4"


class FeedbackSource(BaseModel):
    """Where a set's round-1 episodes come from: a sealed draw, or a release's PR list."""

    model_config = ConfigDict(extra="forbid")
    draw: Optional[str] = None
    prs_of_release: bool = False

    @model_validator(mode="after")
    def _exactly_one(self):
        if bool(self.draw) == self.prs_of_release:
            raise ValueError("feedback: name a sealed `draw`, or set `prs_of_release: true`, not both")
        return self


class ProbeSet(BaseModel):
    """One set the probe runs on. Paths are repo-relative."""

    model_config = ConfigDict(extra="forbid")
    name: str
    release: Path
    #: The dataset config `cli tool` reads for the tool grant and the retrieval cutoff.
    dataset_config: Path
    #: The PRs reviewed. Asks are matched only on these.
    pr_numbers: List[int]
    feedback: FeedbackSource
    #: Comment ids are `<prefix><4 digits>`, numbered over the whole source.
    cid_prefix: str = "v"
    #: Where this set's packets, sessions, feedback and asks live.
    probe_dir: Path
    #: Claude sessions made before this harness, by PR: {pr: directory holding pr<N>/<session>/}.
    sessions_from: Dict[int, Path] = {}
    #: The modification inventory the pass-0 model reads, when the release does not hold its own
    #: (the dev release's is a treatment's, as `configs/bases/v5_generation.yaml` names it).
    modification_inventory: Optional[Path] = None

    @property
    def inventory(self) -> Path:
        return self.modification_inventory or self.release / "derived/modification_inventory.jsonl"

    @property
    def feedback_file(self) -> Path:
        return self.probe_dir / "feedback.json"

    @property
    def asks_file(self) -> Path:
        return self.probe_dir / "asks.json"

    def session_dir(self, pr: int, session: str) -> Path:
        return Path(self.sessions_from.get(pr, self.probe_dir)) / f"pr{pr}" / session


def load_probe_set(path: Path) -> ProbeSet:
    return ProbeSet.model_validate(yaml.safe_load(Path(path).read_text()))


def _test_prs() -> set:
    return set(json.loads(TEST_MANIFEST.read_text())["pr_numbers"])


def _round1_episodes(spec: ProbeSet) -> List[Dict[str, Any]]:
    """[{pr_number, episode_id, stratum, month, targets, ai, author}] in the source's order."""

    if spec.feedback.draw:
        from src.datasets.pull_requests.projections.frame import Draw, load_sealed, seal_dir

        _spec, _members, seal_sha = load_sealed(spec.feedback.draw)
        draw = Draw.model_validate_json((seal_dir(spec.feedback.draw) / "draw.json").read_text())
        if draw.frame_seal_sha256 != seal_sha or not draw.complete:
            raise ValueError(f"{spec.feedback.draw}: the draw does not match its seal, or is incomplete")
        return [{"pr_number": a.pr_number, "episode_id": a.episode_id, "stratum": a.stratum,
                 "month": a.month, "targets": a.targets, "ai": bool(a.ai_evidence),
                 "author": a.author} for a in draw.accepted]
    rows = []
    for line in (spec.release / "input" / "episodes.jsonl").read_text().splitlines():
        e = json.loads(line)
        rows.append({"pr_number": e["pr_number"], "episode_id": e["episode_id"], "stratum": None,
                     "month": None, "targets": None, "ai": None, "author": None})
    return rows


def _seal_of(spec: ProbeSet) -> Optional[str]:
    if not spec.feedback.draw:
        return None
    from src.datasets.pull_requests.projections.frame import load_sealed

    return load_sealed(spec.feedback.draw)[2]


def extract_feedback(spec: ProbeSet, roster_path: Path = DEFAULT_ROSTER) -> Dict[str, Any]:
    """Round-1 reviewer feedback for every episode of the set's source, numbered `<prefix>0000…`.

    This is `arm-coverage-val1000-…/provenance/extract_draw_feedback.py` with the source and the id
    prefix as parameters, and it produces the same rows. A release episode whose id the store's
    projection does not reproduce is refused rather than matched loosely.
    """

    from src.datasets.pull_requests.definitions import load_roster
    from src.datasets.pull_requests.projections.episodes import project_episodes
    from src.datasets.pull_requests.store import PullRequestStore
    from src.mathlib_review.release.events import events_from_bundle

    episodes = _round1_episodes(spec)
    clash = {e["pr_number"] for e in episodes} & _test_prs()
    if clash:
        raise ValueError(f"test-set PRs in the source: {sorted(clash)}")
    if spec.feedback.draw:
        from src.datasets.pull_requests.projections.frame import load_sealed

        roster_path = Path(load_sealed(spec.feedback.draw)[0].roster_path)
    store, roster = PullRequestStore(), load_roster(roster_path)
    rows, no_feedback = [], []
    for a in episodes:
        n = a["pr_number"]
        proj = project_episodes(store, roster=roster, prs=[n])
        matches = [x for x in proj.boundaries if x.episode_id == a["episode_id"]]
        if len(matches) != 1:
            raise ValueError(f"PR {n}: the store projects no episode {a['episode_id']}")
        want = set(matches[0].feedback_event_ids)
        if not want:
            no_feedback.append(n)
            continue
        bundle = store.load_bundle(n)
        ids = {e.source_key: e.event_id
               for e in events_from_bundle(bundle, source_object=store.bundle_ref(n), repo=REPO)}
        got = []
        for kind, key in (("review", "reviews"), ("review_comment", "review_comments"),
                          ("issue_comment", "issue_comments")):
            for i, item in enumerate(bundle.get(key) or []):
                eid = ids.get(f"/{key}/{i}")
                if eid not in want:
                    continue
                got.append({
                    "pr": n, "event_id": eid, "kind": kind,
                    "author": (item.get("user") or {}).get("login"),
                    "at": item.get("submitted_at") or item.get("created_at"),
                    "state": item.get("state"), "path": item.get("path"),
                    "line": item.get("line") or item.get("original_line"),
                    "gh_id": item.get("id"), "in_reply_to": item.get("in_reply_to_id"),
                    "diff_hunk": (item.get("diff_hunk") or "")[-600:], "body": item.get("body") or "",
                    "pr_title": bundle["pr"].get("title"), "stratum": a["stratum"], "month": a["month"],
                    "targets": a["targets"], "ai": a["ai"], "pr_author": a["author"]})
        if len(got) != len(want):
            print("MISMATCH", n, len(got), len(want), file=sys.stderr)
        got.sort(key=lambda r: (r["at"] or "", r["kind"]))
        rows.extend(got)
    rows.sort(key=lambda r: (r["pr"], r["at"] or ""))
    ghmap = {}
    for i, r in enumerate(rows):
        r["cid"] = f"{spec.cid_prefix}{i:04d}"
        if r["gh_id"] is not None and r["kind"] == "review_comment":
            ghmap[r["gh_id"]] = r["cid"]
    for r in rows:
        r["reply_to_cid"] = (ghmap.get(r["in_reply_to"], "(parent outside round 1)")
                             if r["in_reply_to"] else None)
    return {"name": spec.feedback.draw or spec.name, "seal": _seal_of(spec),
            "accepted": len(episodes), "no_feedback": no_feedback, "rows": rows}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1))


# --- Readers and asks ---------------------------------------------------------------------------
#: The rubric both post-cutoff readers used: is it an ask, its val1000 family, its grain.
READER_RUBRIC = Path("results/pr_review_v5/probes/postcutoff-2026-09-29/reader_rubric.md")
READER_FIELDS = ("cid", "pr", "pr_title", "kind", "state", "author", "path", "line", "reply_to_cid",
                 "diff_hunk", "body")


def reader_batch(feedback: Dict[str, Any], prs: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """What a reader labels: every round-1 comment on the set's PRs, with its reply context."""

    keep = set(prs) if prs is not None else None
    return [{k: r[k] for k in READER_FIELDS} for r in feedback["rows"]
            if keep is None or r["pr"] in keep]


def load_labels(path: Path) -> Dict[str, Dict[str, Any]]:
    return {r["cid"]: r for r in (json.loads(l) for l in Path(path).read_text().splitlines() if l.strip())}


def relabel_by_event(labels: Dict[str, Dict[str, Any]], events: List[Dict[str, Any]],
                     feedback: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Labels keyed by another study's comment ids, re-keyed to this feedback's ids by event id.

    The validation audit numbered its comments `c000…` in its own `events.jsonl`; the feedback
    numbers the same events `v0000…`. An event the feedback does not hold is dropped.
    """

    by_event = {r["event_id"]: r["cid"] for r in feedback["rows"]}
    out = {}
    for e in events:
        cid = by_event.get(e["event_id"])
        if cid is not None and e["cid"] in labels:
            out[cid] = {**labels[e["cid"]], "cid": cid}
    return out


def agreed_asks(feedback: Dict[str, Any], labels_a: Dict[str, Dict[str, Any]],
                labels_b: Dict[str, Dict[str, Any]], prs: List[int],
                families: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """The asks both readers call asks, on the set's PRs; the rest of those PRs are controls.

    A family is the readers' shared one, or "split" when they differ, unless an adjudicated
    `families` map (by this feedback's ids) is given, as the validation audit's is.
    """

    rows = {r["cid"]: r for r in feedback["rows"]}
    agreed = sorted(c for c in rows if labels_a.get(c, {}).get("is_ask") == "ask"
                    and labels_b.get(c, {}).get("is_ask") == "ask")
    asks = {str(pr): [c for c in agreed if rows[c]["pr"] == pr] for pr in prs}
    fam = {c: (families[c] if families is not None else
               labels_a[c]["family"] if labels_a[c]["family"] == labels_b[c]["family"] else "split")
           for c in agreed if rows[c]["pr"] in set(prs)}
    return {"asks": asks, "families": fam, "controls": [pr for pr in prs if not asks[str(pr)]]}


# --- Packets ------------------------------------------------------------------------------------
#: The generalist checklist brief every Claude control session has had (the construction
#: demonstration's X condition, `SYSTEM_PROMPT_V12`'s checklist).
BRIEF_X = Path("results/pr_review_v5/probes/construction-demo-2026-09-29/brief_X.md")
PTOOL_TEMPLATE = """#!/usr/bin/env bash
# ptool <tool>|list|describe ['<json arguments>'] -- one call to the pipeline's own review tools for
# this PR, as an arm makes it (`cli tool`). The wrapper, not the reviewer, logs every call.
set -o pipefail
PR=__PR__; OUT=__OUT__; WORK=__WORK__; RAW=__RAW__
cd __ROOT__ && export PYTHONPATH="$PWD/src" PATH="$HOME/.elan/bin:$PATH"
stamp=$(date +%s%N)-$$
mkdir -p "$RAW"
ape/bin/python -m src.mathlib_review.review.cli tool "$1" \\
  --episodes __EPISODES__ --pr "$PR" \\
  --workdir "$WORK" --run-config __RUN_CONFIG__ \\
  --arguments "${2:-}" > "$RAW/$stamp.out" 2> "$RAW/$stamp.err"
status=$?
ape/bin/python -m src.mathlib_review.review.cli probe log-call "$OUT/calls.jsonl" "$stamp" "$1" "${2:-}" "$RAW/$stamp.out" "$status"
cat "$RAW/$stamp.out"
[ $status -eq 0 ] || tail -5 "$RAW/$stamp.err" >&2
exit $status
"""
#: What every Claude reviewer session has been told, verbatim; `{dir}` is its packet.
SESSION_PROMPT = """You are one reviewer in a research study of Mathlib code review. Your working directory is `{dir}`.

1. Read `brief.md` in that directory and do what it says. Its other inputs (`pr.md`, `model.md`, `diff.patch`) are in the same directory.
2. Rules, which the study depends on:
   - Read only files inside your working directory. Put any temporary file you need (a snippet, an arguments file) in `tmp/` inside your working directory, never in a shared scratch or temp folder.
   - Call the review tools only through the `ptool` script in your working directory (start with `<dir>/ptool describe`). It handles its own paths, so run it by its absolute path from anywhere.
   - Do not run git. Do not read or search any other path in the repository or on disk, including any Mathlib checkout. Do not use web search or web fetch. The tools show the PR as it stood at review time; anything else may show its future and would invalidate the study.
   - Do not look for or read other reviewers' output.
3. Write your outputs into your working directory as the brief specifies, as valid JSON, and check that each JSON file parses.

When done, reply with one line: the number of findings you wrote."""


def session_prompt(packet: Path) -> str:
    return SESSION_PROMPT.format(dir=Path(packet).resolve())


def render_models(release: Path, prs: List[int], inventory_path: Optional[Path] = None) -> Dict[int, str]:
    """Pass 0: each PR's model, from the release's input and derived files only, never gold.

    `construction-demo-2026-09-29/build_model.py` as a function; it renders the same bytes.
    """

    from src.mathlib_review.agenda.components import build_components
    from src.mathlib_review.io import load_jsonl
    from src.mathlib_review.release.pr_relations import build_relations
    from src.mathlib_review.schema import ChangeGraph, ReviewEpisodeInput

    wanted = set(prs)
    episodes = {e.pr_number: e for e in load_jsonl(release / "input/episodes.jsonl", ReviewEpisodeInput)
                if e.pr_number in wanted}
    graphs = [g for g in load_jsonl(release / "derived/change_graphs.jsonl", ChangeGraph)
              if g.pr_number in wanted]
    inventory = {}
    for line in Path(inventory_path or release / "derived/modification_inventory.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["pr_number"] in wanted:
            inventory[row["primary_change_id"]] = row
    relations, _evidence = build_relations(graphs)
    components = build_components(graphs, relations, episodes.values())

    def text(value) -> str:
        return (getattr(value, "text", None) or "") if value is not None else ""

    def short(change_id: str) -> str:
        return change_id.split(":", 1)[-1][:10]

    out = {}
    for graph in graphs:
        pr = graph.pr_number
        episode = episodes[pr]
        name = {t.change_id: (t.declaration_name or f"{t.kind} in {t.path.split('/')[-1]}")
                for t in graph.targets}
        lines = [
            f"# The PR model for #{pr} (pass 0)",
            "",
            "Built deterministically from the diff and the change graph, with no review text. Every "
            "entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, "
            "not a premise. Not built, so not here: library candidates, the area's twin patterns "
            "and conventions, and other open PRs. Construct what you need of those with the tools.",
            "",
            "## The PR",
            "",
            f"- title: {text(episode.title)}",
            f"- description: {text(episode.description) or '(not recoverable at review start)'}",
            f"- changed files: {', '.join(episode.changed_files)}",
            "",
            "## Objects",
            "",
        ]
        removed = []
        for t in sorted(graph.targets, key=lambda t: (t.path, t.change_id)):
            inv = inventory.get(t.change_id, {})
            lifecycle = inv.get("lifecycle") or ("added" if not (t.base_code or "").strip()
                                                 else "removed" if not (t.reviewed_code or "").strip()
                                                 else "modified")
            changed = ", ".join(f"{d['component']}:{d['status']}" for d in inv.get("component_deltas", [])
                                if d.get("status") != "unchanged") or "-"
            kind = t.declaration_kind or t.kind
            lines.append(f"### `{name[t.change_id]}` ({kind}, {lifecycle}) [{short(t.change_id)}]")
            lines.append(f"- file: `{t.path}`; changed: {changed}")
            if lifecycle == "removed":
                removed.append(name[t.change_id])
            if t.kind in ("declaration",) or lifecycle != "unchanged_context":
                if (t.base_code or "").strip():
                    lines += ["- before the PR:", "```lean", t.base_code.rstrip(), "```"]
                if (t.reviewed_code or "").strip():
                    lines += ["- as the PR leaves it:", "```lean", t.reviewed_code.rstrip(), "```"]
            lines.append("")
        lines += ["## Removed or renamed", ""]
        lines += [f"- `{n}`" for n in removed] or ["- none"]
        lines += ["", "## Families (declarations that may be one decision)", ""]
        fams = [c for c in components if c.pr_number == pr and c.grain == "family"]
        for c in fams:
            lines.append(f"- [{c.evidence}] " + ", ".join(f"`{s}`" for s in c.subjects) + f" -- {c.reason}")
        if not fams:
            lines.append("- none found by the change graph")
        lines += ["", "## Relations between changed declarations", ""]
        rels = [r for r in relations if r.pr_number == pr]
        for r in sorted(rels, key=lambda r: (r.relation_kind, name[r.source_change_id])):
            related = ", ".join(f"`{name[c]}`" for c in r.related_change_ids if c in name)
            lines.append(f"- {r.relation_kind} [{r.confidence}]: `{name[r.source_change_id]}` -> {related}")
        if not rels:
            lines.append("- none")
        out[pr] = "\n".join(lines) + "\n"
    return out


def pr_markdown(episode: Dict[str, Any]) -> str:
    title = episode["title"]["text"] if isinstance(episode["title"], dict) else episode["title"]
    desc = (episode.get("description") or {}).get("text") or "(not recoverable at review start)"
    return (f"# PR #{episode['pr_number']}: {title}\n\n## Description\n\n{desc}\n\n## Changed files\n\n"
            + "\n".join(f"- `{c}`" for c in episode["changed_files"]) + "\n")


def write_packets(spec: ProbeSet, sessions: List[str], scratch: Path, prs: Optional[List[int]] = None,
                  brief: Path = BRIEF_X, root: Optional[Path] = None) -> List[Path]:
    """One packet per (PR, session): brief, PR text, diff, pass-0 model and the logging `ptool`.

    A packet that already holds findings is refused: it is a finished session, and rewriting its
    inputs would detach them from what it read.
    """

    root = Path(root or Path.cwd())
    prs = list(prs or spec.pr_numbers)
    models = render_models(spec.release, prs, spec.inventory)
    episodes = {json.loads(l)["pr_number"]: json.loads(l)
                for l in (spec.release / "input/episodes.jsonl").read_text().splitlines()}
    written = []
    for pr in prs:
        for session in sessions:
            d = spec.probe_dir / f"pr{pr}" / session
            if (d / "findings.json").exists():
                raise FileExistsError(f"{d} is a finished session")
            (d / "tmp").mkdir(parents=True, exist_ok=True)
            (d / "brief.md").write_bytes(brief.read_bytes())
            (d / "model.md").write_text(models[pr])
            (d / "pr.md").write_text(pr_markdown(episodes[pr]))
            (d / "diff.patch").write_text(episodes[pr]["diff"])
            wrapper = (PTOOL_TEMPLATE.replace("__PR__", str(pr)).replace("__OUT__", str(root / d))
                       .replace("__WORK__", str(scratch / f"work/pr{pr}/{session}"))
                       .replace("__RAW__", str(scratch / f"raw/pr{pr}/{session}"))
                       .replace("__ROOT__", str(root))
                       .replace("__EPISODES__", str(spec.release / "input/episodes.jsonl"))
                       .replace("__RUN_CONFIG__", str(spec.dataset_config)))
            (d / "ptool").write_text(wrapper)
            (d / "ptool").chmod(0o755)
            written.append(d)
    return written


def log_call(log: Path, stamp: str, tool: str, args: str, out: Path, status: int) -> None:
    """One compact row per tool call, written by the wrapper: what was asked and, for a compile,
    what it returned. The raw output stays in the scratch directory.

    `construction-demo-2026-09-29/bin/log_call.py`, as a function.
    """

    row: Dict[str, Any] = {"stamp": stamp, "tool": tool, "exit": int(status)}
    try:
        row["arguments"] = json.loads(args) if args else None
    except ValueError:
        row["arguments"] = args
    try:
        result = json.loads(Path(out).read_text())
    except (ValueError, OSError):
        result = None
    if tool == "lean_verify_edit" and isinstance(result, dict):
        row["result"] = {k: result.get(k) for k in ("mode", "success", "compiles") if k in result}
        row["result"]["errors_introduced"] = len(result.get("errors_introduced_by_your_edit") or [])
        row["result"]["errors_already"] = len(result.get("errors_already_in_the_file") or [])
        row["result"]["environment_reviewed"] = str(result.get("environment", "")).startswith(
            "Verified against the reviewed")
    elif result is not None:
        row["result_chars"] = len(json.dumps(result, ensure_ascii=False))
    with open(log, "a") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


# --- Matching -----------------------------------------------------------------------------------
#: A matcher sees a finding as these four fields and nothing else.
KEEP = ("target", "claim", "requested_change", "severity")
_REDACT = [(re.compile(r"\bpass \d(?:'s)?\s+"), ""), (re.compile(r"\bc\d{1,3}\b"), "a compiled check")]
MATCHER_RUBRIC = Path("results/pr_review_v5/probes/gpt52-postcutoff-2026-09-29/matcher_rubric.md")


def redact(text):
    """Remove the construction conditions' cues ("pass 3's", "c12") from a finding's text."""
    if not isinstance(text, str):
        return text
    for pattern, repl in _REDACT:
        text = pattern.sub(repl, text)
    return text


#: A workspace prefix on a finding's path: `target/` or `scratch/`, or a resolved
#: `.../workspaces/<commit>/`. Which one a reviewer writes depends on its harness, not on the code.
_WORKSPACE_PREFIX = re.compile(r"^(?:.*/workspaces/[^/]+/|(?:target|scratch)/)")


def repo_target(target):
    """A finding's target as a repository path, so its spelling does not say which harness wrote it.

    Seen on the harness comparison (2026-10-01): APE-Agent sessions wrote `target/Mathlib/...`,
    Claude Code sessions sometimes the absolute store path `.../workspaces/<commit>+<pr>/Mathlib/...`,
    and Claude's packets `Mathlib/...`. The same location, three cues. A target with no path (a
    declaration name) is left as it is.
    """
    if not isinstance(target, str):
        return target
    return _WORKSPACE_PREFIX.sub("", target, count=1)


class Source(BaseModel):
    """Where one session label's findings come from.

    `claude`: a packet's `findings.json` (the label is the session directory's name);
    `solo`: a `cli run` solo run's task results; `lead`: a lead run's `findings.jsonl`, all channels.
    """

    model_config = ConfigDict(extra="forbid")
    kind: Literal["claude", "solo", "lead"]
    run: Optional[str] = None


def _claude(spec: ProbeSet, pr: int, session: str):
    d = spec.session_dir(pr, session)
    found = json.loads((d / "findings.json").read_text())
    calls = [json.loads(l) for l in (d / "calls.jsonl").read_text().splitlines() if l.strip()]
    return found, {"findings": len(found), "compiles": sum(c["tool"] == "lean_verify_edit" for c in calls)}


def _solo_compiles(run: str) -> Dict[int, Dict[str, int]]:
    """Compile calls per PR from the trajectory reader. The solo grant holds `lean_verify` beside
    `lean_verify_edit`, and both count; the split is kept."""

    from src.mathlib_review.analysis.trajectory import extract

    calls = {}
    for inv in extract(run)["invocations"]:
        row = inv if isinstance(inv, dict) else inv.__dict__
        counts = row.get("tool_calls") or {}
        calls[int(row["pr_number"])] = {
            "lean_verify_edit": sum(v for k, v in counts.items() if k.endswith("lean_verify_edit")),
            "lean_verify": sum(v for k, v in counts.items() if k.endswith("lean_verify"))}
    return calls


def _solo(run: str) -> Dict[int, tuple]:
    import asyncio

    from ape.orchestration.persistence import TaskStorage

    compiles = _solo_compiles(run)

    async def load():
        out = {}
        tasks = Path(".ape/runs") / run / "tasks"
        for task_dir in sorted(p for p in tasks.iterdir() if p.is_dir()):
            storage = TaskStorage(task_dir, task_dir.name)
            samples = await storage.load_all_samples()
            result = await storage.load_task_result()
            for _i, sample in sorted(samples.items()):
                if sample.successful_attempt is None or not result or not result.get("success"):
                    continue
                pr = int(result["pr_number"])
                found = [{"target": f"{(f.get('anchor') or {}).get('path')}:{(f.get('anchor') or {}).get('line_start')}",
                          "claim": f.get("claim"), "requested_change": f.get("suggested_fix"),
                          "severity": f.get("severity")} for f in result.get("findings") or []]
                split = compiles.get(pr, {"lean_verify_edit": -1, "lean_verify": -1})
                out[pr] = (found, {"findings": len(found),
                                   "compiles": split["lean_verify_edit"] + split["lean_verify"],
                                   "compile_split": split})
                break
            else:
                # No legal submission: a session stopped at its turn, token or cost cap submitted
                # nothing, and that is what a matcher must see -- an empty list, marked. The PR is in
                # the task id (`pr5solo_<repo>_<pr>_round1_<sha>`). Seen first on the high-effort
                # runs, 10 of 32 sessions (2026-09-30).
                outcome = json.loads((task_dir / "task_outcome.json").read_text())
                m = re.search(r"mathlib4_(\d+)_round", outcome["task_id"])
                statuses = [str(getattr(s.current_attempt, "status", "")) for s in samples.values()
                            if s.current_attempt is not None]
                if m and statuses:
                    out[int(m.group(1))] = ([], {"findings": 0, "compiles": None,
                                                 "capped": statuses[0].split(".")[-1].lower()})
        return out

    return asyncio.run(load())


def change_locations(spec: ProbeSet, pr: int) -> Dict[str, str]:
    """{change_id: "path:line"}: the reviewed span of a change's first range, where the pipeline
    anchors a finding."""

    for line in (spec.release / "derived/change_graphs.jsonl").read_text().splitlines():
        g = json.loads(line)
        if g["pr_number"] != pr:
            continue
        ranges = {r["range_id"]: r for r in g["changed_ranges"]}
        return {t["change_id"]: f"{ranges[t['changed_range_ids'][0]]['path']}:"
                                f"{(ranges[t['changed_range_ids'][0]].get('reviewed_span') or {}).get('line_start')}"
                for t in g["targets"]}
    return {}


def _lead(spec: ProbeSet, run: str) -> Dict[int, tuple]:
    by_pr: Dict[int, List[Dict[str, Any]]] = {}
    for l in (Path("results/pr_review_v5/runs") / run / "findings.jsonl").read_text().splitlines():
        if l.strip():
            by_pr.setdefault(json.loads(l)["pr_number"], []).append(json.loads(l))
    out = {}
    for pr in spec.pr_numbers:
        where = change_locations(spec, pr)
        found, published = [], []
        for n, f in enumerate(by_pr.get(pr, [])):
            found.append({"target": where[f["primary_change_id"]], "claim": f.get("claim"),
                          "requested_change": f.get("requested_change"), "severity": f.get("severity")})
            if f.get("admission") == "published":
                published.append(n)
        out[pr] = (found, {"findings": len(found), "published": published})
    return out


def ask_packet(feedback: Dict[str, Any], cids: List[str]) -> List[Dict[str, Any]]:
    """What a matcher sees of each ask: the comment, the code it is attached to, what it answers."""

    rows = {r["cid"]: r for r in feedback["rows"]}
    packet = []
    for cid in cids:
        r = rows[cid]
        parent = rows.get(r["reply_to_cid"]) if r.get("reply_to_cid") else None
        packet.append({"ask_id": cid, "path": r["path"], "code_at_comment": r["diff_hunk"],
                       "comment": r["body"], "replies_to": parent["body"] if parent else None})
    return packet


def seal_labels(prs: List[int], sessions: List[str]) -> Dict[str, Dict[str, str]]:
    """A fresh blinding: per PR, the sessions shuffled to R1..Rn."""

    import secrets

    seal = {}
    for pr in prs:
        pool, order = list(sessions), []
        while pool:
            order.append(pool.pop(secrets.randbelow(len(pool))))
        seal[str(pr)] = {f"R{i + 1}": s for i, s in enumerate(order)}
    return seal


def match_inputs(spec: ProbeSet, feedback: Dict[str, Any], asks: Dict[str, Any],
                 seal: Dict[str, Dict[str, str]], sources: Dict[str, Source], out: Path) -> Dict[str, Any]:
    """Blind inputs: per sealed PR, its asks and every session's findings under its shuffled label.

    Findings are stripped to `KEEP` with cues redacted. A finding without a target is refused, since
    a matcher would judge it without a location (test (b)'s solo findings reached the matchers as
    `None:None` until 2026-09-29).
    """

    out.mkdir(parents=True, exist_ok=True)
    used = {s for labels in seal.values() for s in labels.values()}
    missing = used - set(sources)
    if missing:
        raise ValueError(f"no source for sessions {sorted(missing)}")
    loaded = {s: (_solo(sources[s].run) if sources[s].kind == "solo" else _lead(spec, sources[s].run))
              for s in used if sources[s].kind != "claude"}
    stats: Dict[str, Dict[str, Any]] = {}
    for pr, labels in seal.items():
        write_json(out / f"asks_pr{pr}.json", ask_packet(feedback, asks["asks"][pr]))
        for label, session in labels.items():
            if sources[session].kind == "claude":
                found, st = _claude(spec, int(pr), session)
            else:
                if int(pr) not in loaded[session]:
                    raise ValueError(f"{session} has no successful session for PR {pr}")
                found, st = loaded[session][int(pr)]
            stats.setdefault(pr, {})[session] = st
            stripped = [{"i": n, **{k: repo_target(f.get(k)) if k == "target" else redact(f.get(k))
                                    for k in KEEP}} for n, f in enumerate(found)]
            lost = [f["i"] for f in stripped if not f["target"] or str(f["target"]).startswith("None")]
            if lost:
                raise ValueError(f"{session} on PR {pr}: findings {lost} have no target")
            write_json(out / f"{label}_pr{pr}.json", stripped)
    write_json(out / "session_stats.json", stats)
    return stats


def condition(session: str) -> str:
    """A session label's condition: the label without its trailing digits (X1 -> X, Gr2 -> Gr)."""
    return session.rstrip("0123456789")


def unblind(asks: Dict[str, Any], seal: Dict[str, Dict[str, str]], matches: Dict[str, Dict[str, Any]],
            stats: Dict[str, Any], scope: Optional[set] = None) -> Dict[str, Any]:
    """Per matcher: each session's reach (asks reached / asks), each condition's mean, the asks every
    session of a condition reached (stable) and any reached (union), a lead session's reach counting
    only published findings, and the per-ask table; and the matchers' agreement.

    `scope`, a set of families, restricts every figure to the asks in them. Reading rules are
    each probe's own, stated in its README before its runs; this computes what they read.
    """

    items = [(pr, cid) for pr in seal for cid in asks["asks"][pr]
             if scope is None or asks["families"].get(cid) in scope]
    sessions = sorted({s for labels in seal.values() for s in labels.values()})
    out: Dict[str, Any] = {"asks": len(items)}
    cells_by = {}
    for m, d in matches.items():
        cells = {(str(a["pr"]), a["ask_id"], s): (a.get(label), a.get(f"{label}_finding"))
                 for a in d["asks"] if str(a["pr"]) in seal
                 for label, s in seal[str(a["pr"])].items()}
        cells_by[m] = cells

        def hit(pr, cid, s, published=False):
            value, i = cells.get((pr, cid, s), (None, None))
            return value == "reached" and (not published or i in stats[pr][s].get("published", []))

        reach = {s: (sum(hit(pr, cid, s) for pr, cid in items) / len(items)) if items else None
                 for s in sessions}
        conds: Dict[str, List[str]] = {}
        for s in sessions:
            conds.setdefault(condition(s), []).append(s)
        out[m] = {
            "reach": reach,
            "condition_reach": {c: sum(reach[s] for s in ss) / len(ss) for c, ss in conds.items()},
            "stable": {c: sorted(cid for pr, cid in items if all(hit(pr, cid, s) for s in ss))
                       for c, ss in conds.items()},
            "union": {c: sorted(cid for pr, cid in items if any(hit(pr, cid, s) for s in ss))
                      for c, ss in conds.items()},
            "published_reach": {s: sum(hit(pr, cid, s, True) for pr, cid in items) / len(items)
                                for s in sessions if items and any("published" in stats[pr].get(s, {})
                                                                   for pr in seal)},
            "table": {cid: {s: cells.get((pr, cid, s), (None,))[0] for s in sessions}
                      for pr, cid in items},
        }
    names = list(matches)
    if len(names) == 2:
        a, b = cells_by[names[0]], cells_by[names[1]]
        keys = [(pr, cid, s) for pr, cid in items for s in sessions]
        out["agreement"] = {"cells": len(keys),
                            "three_valued": sum(a.get(k, (None,))[0] == b.get(k, (None,))[0] for k in keys),
                            "reached_or_not": sum((a.get(k, (None,))[0] == "reached") == (b.get(k, (None,))[0] == "reached")
                                                  for k in keys)}
    return out


# --- Order, folders and audits ------------------------------------------------------------------
def unfinished_sessions(spec: ProbeSet, sessions: List[str]) -> List[str]:
    """The (PR, session) packets on the set that hold no findings yet."""
    return [f"pr{pr}/{s}" for pr in spec.pr_numbers for s in sessions
            if not (spec.session_dir(pr, s) / "findings.json").exists()]


_NUMBERS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
            9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}


def matcher_rubric(reviewers: int, prs: int) -> str:
    """The matcher rubric for this many reviewers and PRs. It was written for six and six, and
    for those it is returned unchanged."""

    text = MATCHER_RUBRIC.read_text()
    word = lambda n: _NUMBERS.get(n, str(n))
    pr_phrase = "one Mathlib pull request" if prs == 1 else f"{word(prs)} Mathlib pull requests"
    text = text.replace("on six Mathlib pull requests. Six anonymous reviewers, `R1` to `R6`",
                        f"on {pr_phrase}. {word(reviewers).capitalize()} anonymous reviewers, "
                        f"`R1` to `R{reviewers}`")
    text = text.replace("`R6_pr<N>.json`", f"`R{reviewers}_pr<N>.json`")
    text = text.replace('"R6": ..., "R6_finding": ...', f'"R{reviewers}": ..., "R{reviewers}_finding": ...')
    return text.replace('"R6": <count>', f'"R{reviewers}": <count>')


def judge_folders(root: Path, n: int, files: List[Path], rubric: Path,
                  rubric_text: Optional[str] = None) -> List[Path]:
    """`n` isolated folders for blind readers or matchers: the inputs, the rubric, a `tmp/`."""
    import shutil

    folders = []
    for i in range(1, n + 1):
        d = Path(root) / f"m{i}"
        if d.exists():
            shutil.rmtree(d)
        (d / "tmp").mkdir(parents=True)
        for f in files:
            shutil.copy(f, d / f.name)
        if rubric_text is None:
            shutil.copy(rubric, d / rubric.name)
        else:
            (d / rubric.name).write_text(rubric_text)
        folders.append(d)
    return folders


MATCHER_PROMPT = """You are a blind judge in a research study on code review of Mathlib (Lean 4) pull requests.

Your working folder is:
{dir}

Rules:
- Read `matcher_rubric.md` in that folder first and follow it exactly.
- Read only files inside that folder. Do not open, list or search anything outside it, do not use git, and do not use the web.
- If you need scratch files (for example a helper script), put them in the folder's `tmp/` subfolder.
- Judge every ask for every reviewer yourself, by reading the findings. A script may help you assemble the JSON, but the judgments must be yours.
- Write `matches.json` in the working folder, in the format the rubric gives.

When done, reply with what the rubric asks for: per reviewer label pooled over PRs, the counts of `reached` and `partial`."""
READER_PROMPT = """You are a labeller in a research study of Mathlib code review. Your working directory is `{dir}`.

Read `reader_rubric.md` there and label every comment in `batch.jsonl` as it says. Write your output to `labels.jsonl` in that directory.

Rules, which the study depends on:
- Read only the two files named above. Do not read anything else on disk, do not run git, and do not use web search or web fetch.
- Keep any temporary file inside your working directory.

Validate `labels.jsonl` (every cid once, valid JSON, every key present), then reply as the rubric asks."""

_ABS = re.compile(r"(?:^|(?<=[\s'\"=(<>|;:]))(/(?:research|common|home|tmp|opt|usr|etc|mnt|data|scratch|root|var|nfs|proc)(?:/[\w.\-+]+)*)")


def _own_tmp(folder: Path, name: str) -> bool:
    """Whether `name` (or a file it is the stem of) exists in the packet's own `tmp/`."""
    tmp = folder / "tmp"
    return tmp.is_dir() and any(f.name == name or f.name.startswith(name) for f in tmp.iterdir())


def _blocks(line: str) -> List[Dict[str, Any]]:
    try:
        content = (json.loads(line).get("message") or {}).get("content")
    except ValueError:
        return []
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def audit_transcript(folder: Path, transcript: Path) -> Dict[str, Any]:
    """Every tool call a reader, matcher or reviewer made, checked against its own folder: an
    absolute path outside it, git, the web, or a file tool pointed elsewhere is flagged. Flags are
    read by hand; a flag is not a verdict (a reviewer's `ptool` is inside its folder)."""

    folder = str(Path(folder).resolve())
    calls, flagged = 0, []
    lines = Path(transcript).read_text().splitlines()
    # The harness saves a large tool output to tool-results/<id>.txt and names it in that call's
    # result; reading it back is reading the session's own output (8 of 8 matcher flags on the dev
    # set, 4 reviewer flags, each named in no other transcript, 2026-09-29).
    results_text = " ".join(json.dumps(b.get("content"), ensure_ascii=False)
                            for line in lines for b in _blocks(line) if b.get("type") == "tool_result")
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        content = (row.get("message") or {}).get("content")
        for b in content if isinstance(content, list) else []:
            if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                continue
            calls += 1
            inp = b.get("input") or {}
            text = " ".join(str(v) for v in inp.values())
            why = []
            if b.get("name") in ("WebFetch", "WebSearch"):
                why.append("web")
            if re.search(r"\bgit\b", text):
                why.append("git")
            for p in _ABS.findall(text):
                if p.startswith(folder) or p in ("/dev/null", "/tmp") or p.startswith("/usr/bin"):
                    continue
                if p.startswith("/tmp/") and _own_tmp(Path(folder), p[len("/tmp/"):]):
                    # `D + '/tmp/a3.json'`, `"$D"/tmp/b{i}.json`: the packet's own tmp/, written
                    # after a variable, which the pattern reads as a root path. 25 of the dev
                    # sessions' 36 flags were this, each checked by hand (2026-09-29).
                    continue
                why.append("outside " + p[-70:])
            own_output = [p for p in _ABS.findall(text) if "/tool-results/" in p and p in results_text]
            why = [w for w in why if not any(w == "outside " + p[-70:] for p in own_output)]
            if (b.get("name") in ("Read", "Write", "Edit") and not str(inp.get("file_path", "")).startswith(folder)
                    and str(inp.get("file_path", "")) not in own_output):
                why.append("file tool outside")
            if why:
                flagged.append({"tool": b.get("name"), "why": sorted(set(why)),
                                "input": text.replace(folder, "<dir>")[:160]})
    return {"folder": folder, "calls": calls, "flagged": flagged}


def model_context(spec: ProbeSet, prs: List[int]) -> str:
    """The solo task's `context_file`: each PR's pass-0 model as one section, JSON lines, so a
    `gpt_5.2` session reads the same model a Claude session's `model.md` holds."""

    models = render_models(spec.release, prs, spec.inventory)
    return "".join(json.dumps({"pr_number": pr, "sections": [{"title": "The PR model (pass 0)",
                                                              "text": models[pr]}]},
                              ensure_ascii=False) + "\n" for pr in prs)


def restore_bases(spec: ProbeSet, prs: Optional[List[int]] = None) -> Dict[str, str]:
    """Restore each PR's built base snapshot into its workspace, which a reviewed build needs and the
    prebuild planner does not check (the validation and post-cutoff probes' `restore_bases.py`).

    Run it only while no build of those commits is running: a restore beside a finishing build
    marked the state failed (`.claude/rules/mathlib-review.md`, 2026-09-29).
    """

    import asyncio

    from ape.toolkits.execute.lean.config import LeanVerifyToolConfig
    from ape.toolkits.execute.lean.core.restore_manager import RestoreManager
    from ape.utils.logging import create_logger

    wanted = set(prs or spec.pr_numbers)
    shas = sorted({json.loads(l)["base_sha"] for l in (spec.release / "input/episodes.jsonl").read_text().splitlines()
                   if json.loads(l)["pr_number"] in wanted})
    cfg = LeanVerifyToolConfig()
    _, url = cfg.resolve_repo(None)
    manager = RestoreManager(cfg, create_logger(to_console=False), url)
    status = {}
    for sha in shas:
        if asyncio.run(manager._requires_build_first(sha)):
            status[sha] = "not built"
            continue
        for attempt in (1, 2):
            try:
                asyncio.run(manager.get_workspace(sha))
                status[sha] = "restored"
                break
            except Exception as exc:  # noqa: BLE001 - reported, and retried once
                status[sha] = f"failed: {type(exc).__name__}: {str(exc)[:120]}"
    return status
