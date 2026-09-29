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


def render_models(release: Path, prs: List[int]) -> Dict[int, str]:
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
    for line in (release / "derived/modification_inventory.jsonl").read_text().splitlines():
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
    models = render_models(spec.release, prs)
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
