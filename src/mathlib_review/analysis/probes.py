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


#: A swap packet's session: the reviewer is given another reviewer's delivered messages as its
#: instructions (`write_swap_packets`) and submits what that reviewer's submission tool would take.
#: The rules are SESSION_PROMPT's, which the leak audit depends on.
SWAP_SESSION_PROMPT = """You are one reviewer in a research study of Mathlib code review. Your working directory is `{dir}`.

1. `system.md` and `user.md` in that directory are your instructions: the system and user messages another reviewer was given, verbatim except the user message's "Tools available" line. Read both, then do what they say.
2. Where they say to call `submit_findings`, write `submission.json` in your working directory instead: one JSON object holding exactly the arguments you would pass, `{{"notes": "...", "findings": [...]}}`, each finding with the fields the user message lists. Check that it parses. Write it once, when you have finished.
3. Rules, which the study depends on:
   - Read only files inside your working directory. Put any temporary file you need (a snippet, an arguments file) in `tmp/` inside your working directory, never in a shared scratch or temp folder.
   - Call the tools only through the `ptool` script in your working directory (start with `<dir>/ptool describe`). Paths such as `target/Mathlib/...` in your instructions are the paths its file tools take. It handles its own paths, so run it by its absolute path from anywhere.
   - Do not run git. Do not read or search any other path in the repository or on disk, including any Mathlib checkout. Do not use web search or web fetch. The tools show the PR as it stood at review time; anything else may show its future and would invalidate the study.
   - Do not look for or read other reviewers' output.

When done, reply with one line: the number of findings you submitted."""

#: What marks a packet finished: brief X's `findings.json`, or a swap session's `submission.json`.
SESSION_OUTPUTS = ("findings.json", "submission.json")


def finished(packet: Path) -> bool:
    return any((Path(packet) / name).exists() for name in SESSION_OUTPUTS)


def session_prompt(packet: Path) -> str:
    template = SWAP_SESSION_PROMPT if (Path(packet) / "user.md").exists() else SESSION_PROMPT
    return template.format(dir=Path(packet).resolve())


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


#: The conventions ceiling probe's section (`docs/todo/conventions-ceiling-probe.md`): census
#: principles as sentences, with no location. The lead is the same at every level of the probe
#: (exact, applicable, common, all) and for every reviewer; only the entries differ.
CONVENTIONS_TITLE = "Conventions the maintainers hold"
CONVENTIONS_LEAD = (
    "These are conventions Mathlib's maintainers hold when they review, one sentence each: a "
    "situation and the form preferred in it. They are stated in general, and none names a place in "
    "this PR. Check the changed code against each one. Where it departs from a convention, request "
    "the change that convention calls for, as a finding at the place it applies.")


#: Generation without suppression's closing paragraph for this section (the gpt-5.5 conditions;
#: docs/plans/2026-10-06-generation-without-suppression.md). Stage M's gpt-5.5 weighed the exact
#: section's full-words convention against `MGFs` on 28649 and filed nothing: "I doubt that
#: maintainers would request changes for commonly used acronyms". The section names no place, so the
#: disposition is per place the convention's situation occurs, with `departs` and `conforms` only.
CONVENTIONS_DISPOSITION = (
    "Give every convention above a disposition at each place in the changed code where its "
    "situation occurs, and say in your submission's `message` which you gave and on what ground. "
    "`departs`: file the change the convention calls for, as a finding at that place. `conforms`: "
    "only if a check you ran, or a line of the code you quote, shows the required form already "
    "holds there. What Mathlib usually requires, accepts or enforces, how minor the change is, and "
    "whether a maintainer would insist on it are not grounds for either disposition. For these "
    "conventions this replaces the brief's instruction to emit only what you would actually request.")


#: Stage D's closing paragraph (DeepSeek-V4.1-Flash; the probe README's stage D): the conventions, and
#: maintainers' asks for them on other PRs, outrank the reviewer's own judgement of the code. With the
#: exact section the reviewers weighed a convention and passed the code on its merits: Claude "also
#: compiles as a term. That is a matter of taste, not an ask", "does not apply, since this is a
#: generalization"; the local Qwen "`gcongr` doesn't apply here as verified". The disposition paragraph
#: above rules out guesses about maintainers; this one rules out the reviewer's view of the code as
#: well, lets the examples decide where a convention applies, and turns a change it cannot make into
#: a question. Each sentence carries its examples (`exemplified`).
CONVENTIONS_PRECEDENCE = (
    "Under each convention are up to two comments in which a maintainer asked for it on another PR, "
    "each with the code it was on. Take the conventions and these examples as the standard for this "
    "review: they show what maintainers ask for, and they outrank your own judgement of this code. "
    "Where the changed code is in a situation like an example's, file the change its convention calls "
    "for, as a finding at that place. None of these is a reason to leave it out: that the code is "
    "correct, clear or idiomatic as it stands; that the change is minor or a matter of taste; that "
    "this file, its author or its neighbours do it differently; that Mathlib does not require it or a "
    "maintainer might not insist on it; that the convention's wording does not quite fit, where the "
    "code is like an example's. Where you cannot make or check the change, file it as a question to "
    "the author that names the convention and the change. Leave a place unfiled only where a line of "
    "the code you quote, or a check you ran, shows it already has the form the convention calls for. "
    "In your submission's `message`, list each convention with the places you filed and any place "
    "you left, with that line or check. For these conventions this replaces the brief's instructions "
    "to emit only what you would actually request and not to raise questions.")


def exemplified(principle: str, examples: List[Dict[str, str]]) -> str:
    """A convention's sentence with maintainers' asks for it on other PRs beneath it, each a comment
    (`comment`), the file it was on (`path`, None for a comment on the PR as a whole) and the code
    (`code`), indented to sit inside the sentence's list item in `conventions_section`."""

    def indented(text: str, prefix: str) -> str:
        return "\n".join(prefix + line if line.strip() else prefix.rstrip() for line in text.splitlines())

    parts = [principle]
    for n, ex in enumerate(examples, 1):
        where = f"at `{ex['path']}`" if ex.get("path") else "on the PR as a whole"
        parts.append(f"\n\n  Example {n}, asked on another PR {where}. The maintainer's comment:\n\n"
                     + indented(ex["comment"], "  > "))
        if ex.get("code"):
            parts.append("\n\n  The code it was on:\n\n  ```\n" + indented(ex["code"], "  ") + "\n  ```")
    return "".join(parts)


def conventions_section(principles: List[str], closing: str = "") -> str:
    """The section's text; `closing`, when given, is a paragraph after the sentences."""
    return (CONVENTIONS_LEAD + "\n\n" + "\n".join(f"- {p}" for p in principles) + "\n"
            + (f"\n{closing}\n" if closing else ""))


def load_conventions(briefs: Path, codebook: Path,
                     examples: Optional[Dict[str, List[Dict[str, str]]]] = None) -> Dict[int, List[str]]:
    """A level's briefs as sentences: `briefs` is `{"prs": {pr: [entry ids]}}`, `codebook` a census
    codebook. Sentences come in codebook order whatever order the brief lists its ids in. With
    `examples` (entry id -> its examples), each sentence carries its own (`exemplified`); an entry
    with none reads as its sentence."""

    principle = {entry["id"]: entry["principle"] for entry in json.loads(Path(codebook).read_text())}
    text = ((lambda i: exemplified(principle[i], examples.get(i, []))) if examples is not None
            else (lambda i: principle[i]))
    return {int(pr): [text(i) for i in sorted(set(ids))]
            for pr, ids in json.loads(Path(briefs).read_text())["prs"].items()}


#: Stage G of the same probe: conventions as guarded rules. A blind pinpointing pass evaluates each
#: rule's trigger on the PR's changed code, and the section names the places where one fires, with
#: how to tell a departure. Stage F delivered the sentences alone, 25 a PR, and moved nothing.
CANDIDATES_TITLE = "Places where a maintainers' convention may apply"
CANDIDATES_LEAD = (
    "A separate pass compared this PR's changed code with conventions Mathlib's maintainers hold "
    "when they review. Each item below names a place where one convention's situation occurs, the "
    "convention, and how to tell whether the code departs from it. The pass read the diff only and "
    "ran nothing. Treat every item as a claim to verify: where an item names a check, run it with "
    "your tools; where the code departs, request the change the convention calls for, as a finding "
    "at that place; where it does not, drop the item and say nothing of it. The items are not the "
    "whole review: review the rest of the PR as the brief above says.")


def candidate_line(item: Dict[str, str]) -> str:
    """One pinpointed candidate as a brief line: the place, what occurs there, the convention, then
    either that reading already shows a departure or the check that decides it."""

    decided = ("Decided by reading: the code departs." if item["status"] == "departs"
               else f"Check: {item['check']}")
    exception = f" Not when: {item['not_when']}" if item.get("not_when") else ""
    return (f"- `{item['file']}`, `{item['declaration']}`: {item['fact']} "
            f"Convention: {item['convention']} {decided}{exception}")


#: Generation without suppression (docs/plans/2026-10-06-generation-without-suppression.md): the
#: same items under leads that take the guess about maintainers out of the decision to file. Stage
#: G's sessions read the items, verified them and dropped some on "Mathlib does not require these".
#: "disposition" gives every item a disposition whose ground is the code, never uptake; "ledger"
#: keeps generation apart from assessment, so every change considered is an entry and the
#: reviewer's own judgement is a mark on it. Both say what is true of the items' source (asked for
#: on other PRs), not that maintainers raise them here, which stage H measured at 5% or less.
CANDIDATES_SOURCE = (
    "A separate pass compared this PR's changed code with conventions Mathlib's maintainers have "
    "asked for on other PRs. Each item below names a place where one convention's situation occurs, "
    "the convention, and how to tell whether the code departs from it. The pass read the diff only "
    "and ran nothing.")
DISPOSITION_LEAD = CANDIDATES_SOURCE + (
    "\n\nGive every item exactly one disposition, and list them in `notes.md`, one line an item: its "
    "place, its convention, the disposition and its ground.\n"
    "- `departs`: file the change the convention calls for, as a finding at that place. An item "
    "marked \"Decided by reading: the code departs\" is `departs` unless a line you quote shows the "
    "required form is already there.\n"
    "- `conforms`: only if a check you ran, or a line of the code you quote, shows the required form "
    "already holds, or the item's \"Not when\" applies. Name the check or quote the line.\n"
    "- `ask_author`: the check could not be run, or it failed for want of a piece the author could "
    "add (a missing lemma, attribute or import). File a question to the author that names the piece."
    "\n\nWhat Mathlib usually requires, accepts or enforces, how minor the change is, and whether a "
    "maintainer would insist on it are not grounds for any disposition. For these items this "
    "replaces the brief's instruction to emit only what you would actually request. Review the rest "
    "of the PR as the brief says.")
LEDGER_LEAD = CANDIDATES_SOURCE + (
    "\n\nIn this review, keep generation apart from assessment, for these items and for the rest of "
    "the PR.\n"
    "- Generation: every change you consider making at a place goes into `findings.json` as an entry "
    "with the brief's keys: each item whose check you run or whose departure you read, each edit you "
    "compile, each change you think of while reading. Leave none out, whatever you conclude about it.\n"
    "- Assessment: give every entry two more keys. `file`: true if you would put it to the author as "
    "a review comment, false if not. `assessment`: one sentence saying why. An item whose check shows "
    "the code already conforms is an entry with `file: false` that says so.\n\n"
    "The brief's instructions to emit only what you would actually request, and not to report what "
    "you checked, decide `file`; they do not decide whether an entry exists.")
CANDIDATES_LEADS = {"verify": CANDIDATES_LEAD, "disposition": DISPOSITION_LEAD, "ledger": LEDGER_LEAD}


def candidates_section(items: List[Dict[str, str]], lead: str = CANDIDATES_LEAD) -> str:
    return lead + "\n\n" + "\n".join(candidate_line(i) for i in items) + "\n"


def load_candidates(briefs: Path) -> Dict[int, List[Dict[str, str]]]:
    """A stage's pinpointed briefs: `{"prs": {pr: [item, ...]}}`, each item holding `file`,
    `declaration`, `fact`, `convention`, `status` (`departs` or `check`), `check` and `not_when`."""

    return {int(pr): items for pr, items in json.loads(Path(briefs).read_text())["prs"].items()}


def pr_markdown(episode: Dict[str, Any]) -> str:
    title = episode["title"]["text"] if isinstance(episode["title"], dict) else episode["title"]
    desc = (episode.get("description") or {}).get("text") or "(not recoverable at review start)"
    return (f"# PR #{episode['pr_number']}: {title}\n\n## Description\n\n{desc}\n\n## Changed files\n\n"
            + "\n".join(f"- `{c}`" for c in episode["changed_files"]) + "\n")


def write_packets(spec: ProbeSet, sessions: List[str], scratch: Path, prs: Optional[List[int]] = None,
                  brief: Path = BRIEF_X, root: Optional[Path] = None,
                  conventions: Optional[Dict[int, List[str]]] = None,
                  candidates: Optional[Dict[int, List[Dict[str, str]]]] = None,
                  candidates_lead: str = "verify") -> List[Path]:
    """One packet per (PR, session): brief, PR text, diff, pass-0 model and the logging `ptool`.

    A packet that already holds findings is refused: it is a finished session, and rewriting its
    inputs would detach them from what it read. With `conventions`, each PR's brief ends with its
    conventions section; every PR must be named, and an empty list leaves the brief as it is.
    With `candidates` it ends with the pinpointed section instead, under the same two rules; a
    packet takes one or the other. `candidates_lead` names the section's lead in
    `CANDIDATES_LEADS`; the default is stage G's.

    A packet goes where `session_dir` will look for it, so a PR whose earlier sessions live under
    `sessions_from` gets its new ones beside them (until 2026-10-04 they were written under
    `probe_dir`, where neither `prompts` nor the matcher inputs would find them).
    """

    root = Path(root or Path.cwd())
    prs = list(prs or spec.pr_numbers)
    if conventions is not None and candidates is not None:
        raise ValueError("a packet's brief ends with conventions or with candidates, not both")
    if conventions is not None and set(prs) - set(conventions):
        raise KeyError(f"no conventions listed for PRs {sorted(set(prs) - set(conventions))}")
    if candidates is not None and set(prs) - set(candidates):
        raise KeyError(f"no candidates listed for PRs {sorted(set(prs) - set(candidates))}")
    lead = CANDIDATES_LEADS[candidates_lead]
    models = render_models(spec.release, prs, spec.inventory)
    episodes = {json.loads(l)["pr_number"]: json.loads(l)
                for l in (spec.release / "input/episodes.jsonl").read_text().splitlines()}
    written = []
    for pr in prs:
        for session in sessions:
            d = spec.session_dir(pr, session)
            if finished(d):
                raise FileExistsError(f"{d} is a finished session")
            (d / "tmp").mkdir(parents=True, exist_ok=True)
            held = conventions[pr] if conventions else []
            found = candidates[pr] if candidates else []
            section = (f"\n## {CONVENTIONS_TITLE}\n\n{conventions_section(held)}" if held else
                       f"\n## {CANDIDATES_TITLE}\n\n{candidates_section(found, lead)}" if found else "")
            (d / "brief.md").write_bytes(brief.read_bytes() + section.encode())
            (d / "model.md").write_text(models[pr])
            (d / "pr.md").write_text(pr_markdown(episodes[pr]))
            (d / "diff.patch").write_text(episodes[pr]["diff"])
            _write_ptool(spec, d, pr, session, scratch, root)
            written.append(d)
    return written


def _write_ptool(spec: ProbeSet, d: Path, pr: int, session: str, scratch: Path, root: Path) -> None:
    wrapper = (PTOOL_TEMPLATE.replace("__PR__", str(pr)).replace("__OUT__", str(root / d))
               .replace("__WORK__", str(scratch / f"work/pr{pr}/{session}"))
               .replace("__RAW__", str(scratch / f"raw/pr{pr}/{session}"))
               .replace("__ROOT__", str(root))
               .replace("__EPISODES__", str(spec.release / "input/episodes.jsonl"))
               .replace("__RUN_CONFIG__", str(spec.dataset_config)))
    (d / "ptool").write_text(wrapper)
    (d / "ptool").chmod(0o755)


#: The solo prompt's tool line names `lean_verify` and hover/goto, which `ptool` does not hold; a
#: swap packet's user message says what the session can call instead. Its only edit.
PTOOL_TOOLS_LINE = ("**Tools available:** read files, grep the repo (content_search), find files by "
                    "name (file_search), compile your edit against the reviewed workspace "
                    "(lean_verify_edit)")


def delivered_messages(task_dir: Path) -> tuple:
    """`(system, user)`: the first system and user messages of the task's session, as sent.

    From the last per-turn file, which holds the whole session (the files are cumulative), and
    never a `_raw` file.
    """

    turns = [c for c in sorted(Path(task_dir).glob("samples/0/attempts/*/conversations/*.jsonl"))
             if not c.name.endswith("_raw.jsonl")]
    if not turns:
        raise FileNotFoundError(f"{task_dir} has no conversation")
    found = {}
    for line in turns[-1].read_text(encoding="utf-8").splitlines():
        node = json.loads(line) if line.strip() else {}
        kind = node.get("type")
        if kind in ("system", "user") and kind not in found:
            content = (node.get("message") or {}).get("content")
            found[kind] = ("".join(b.get("text", "") for b in content if isinstance(b, dict))
                           if isinstance(content, list) else str(content or ""))
    return found["system"], found["user"]


def swap_user_message(user: str) -> str:
    """The delivered user message with its tool line rewritten to what `ptool` provides."""

    lines = user.split("\n")
    hits = [i for i, line in enumerate(lines) if line.startswith("**Tools available:**")]
    if len(hits) != 1:
        raise ValueError(f"expected one 'Tools available' line, found {len(hits)}")
    lines[hits[0]] = PTOOL_TOOLS_LINE
    return "\n".join(lines)


def write_swap_packets(spec: ProbeSet, session: str, scratch: Path, source_run: str,
                       prs: Optional[List[int]] = None, root: Optional[Path] = None) -> List[Path]:
    """One packet per PR holding the messages `source_run`'s session on that PR was given.

    The swap: another model given a solo run's prompt verbatim (`system.md`, `user.md`), with the
    probe's own tools and rules, submitting what `submit_findings` would take (`submission.json`).
    A finished packet is refused, as in `write_packets`.
    """

    import asyncio

    from ape.orchestration.persistence import TaskStorage

    root = Path(root or Path.cwd())
    prs = list(prs or spec.pr_numbers)

    async def task_dirs():
        out = {}
        tasks = Path(".ape/runs") / source_run / "tasks"
        for task in sorted(p for p in tasks.iterdir() if p.is_dir()):
            result = await TaskStorage(task, task.name).load_task_result()
            if result and result.get("success"):
                out[int(result["pr_number"])] = task
        return out

    by_pr = asyncio.run(task_dirs())
    missing = [pr for pr in prs if pr not in by_pr]
    if missing:
        raise KeyError(f"{source_run} has no successful session for PR(s) {missing}")
    written = []
    for pr in prs:
        d = spec.session_dir(pr, session)
        if finished(d):
            raise FileExistsError(f"{d} is a finished session")
        system, user = delivered_messages(by_pr[pr])
        (d / "tmp").mkdir(parents=True, exist_ok=True)
        (d / "system.md").write_text(system, encoding="utf-8")
        (d / "user.md").write_text(swap_user_message(user), encoding="utf-8")
        (d / "source.json").write_text(json.dumps({"source_run": source_run, "task": by_pr[pr].name},
                                                  indent=1) + "\n")
        _write_ptool(spec, d, pr, session, scratch, root)
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


#: With `harness_blind`, also the cues a conventions condition leaves in its own words: a codebook
#: id, and "convention" itself (7 of 25 AP findings against 2 of 28 solo ones on validation,
#: 2026-10-10). Applied to every session alike, so it is not itself a cue.
_REDACT_CONVENTIONS = [(re.compile(r"\bP\d{3}\b"), "a practice"), (re.compile(r"\bconventions\b"), "practices"),
                       (re.compile(r"\bconvention\b"), "practice"), (re.compile(r"\bConventions\b"), "Practices"),
                       (re.compile(r"\bConvention\b"), "Practice")]


def redact(text, conventions: bool = False):
    """Remove the construction conditions' cues ("pass 3's", "c12") from a finding's text, and with
    `conventions` the conventions conditions' (`_REDACT_CONVENTIONS`)."""
    if not isinstance(text, str):
        return text
    for pattern, repl in _REDACT + (_REDACT_CONVENTIONS if conventions else []):
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
                 seal: Dict[str, Dict[str, str]], sources: Dict[str, Source], out: Path,
                 harness_blind: bool = False) -> Dict[str, Any]:
    """Blind inputs: per sealed PR, its asks and every session's findings under its shuffled label.

    Findings are stripped to `KEEP` with cues redacted. A finding without a target is refused, since
    a matcher would judge it without a location (test (b)'s solo findings reached the matchers as
    `None:None` until 2026-09-29).

    `harness_blind` (the one reviewer table's seals, 2026-10-10) removes what still says which harness
    wrote a finding when Claude sessions sit beside solo runs in one seal: a Claude session is cut to
    the solo budget (its first 20, as `import_probe_session` cuts it), its prose target is located by
    `resolve_target` and written `path:line` as a solo finding's is (an unresolved one keeps its text),
    and every session's text loses the conventions cues. The counts go into `session_stats.json`.
    """

    out.mkdir(parents=True, exist_ok=True)
    used = {s for labels in seal.values() for s in labels.values()}
    missing = used - set(sources)
    if missing:
        raise ValueError(f"no source for sessions {sorted(missing)}")
    loaded = {s: (_solo(sources[s].run) if sources[s].kind == "solo" else _lead(spec, sources[s].run))
              for s in used if sources[s].kind != "claude"}
    stats: Dict[str, Dict[str, Any]] = {}
    graph_by_pr = _graphs(spec) if harness_blind and any(sources[s].kind == "claude" for s in used) else {}
    for pr, labels in seal.items():
        write_json(out / f"asks_pr{pr}.json", ask_packet(feedback, asks["asks"][pr]))
        for label, session in labels.items():
            if sources[session].kind == "claude":
                found, st = _claude(spec, int(pr), session)
                if harness_blind:
                    found, st = _claude_as_solo(found, st, graph_by_pr[int(pr)])
            else:
                if int(pr) not in loaded[session]:
                    raise ValueError(f"{session} has no successful session for PR {pr}")
                found, st = loaded[session][int(pr)]
            stats.setdefault(pr, {})[session] = st
            stripped = [{"i": n, **{k: repo_target(f.get(k)) if k == "target" else redact(f.get(k), harness_blind)
                                    for k in KEEP}} for n, f in enumerate(found)]
            lost = [f["i"] for f in stripped if not f["target"] or str(f["target"]).startswith("None")]
            if lost:
                raise ValueError(f"{session} on PR {pr}: findings {lost} have no target")
            write_json(out / f"{label}_pr{pr}.json", stripped)
    write_json(out / "session_stats.json", stats)
    return stats


def _graphs(spec: ProbeSet) -> Dict[int, Any]:
    """The set's round-1 change graphs by PR, as `import_probe_session` reads them."""

    from src.mathlib_review.review.runner import load_release, load_run

    dataset, _scaffold, _ = load_run(Path(spec.dataset_config),
                                     overrides={"dataset": {"pr_numbers": list(spec.pr_numbers)}})
    return {g.pr_number: g for g in load_release(dataset)["graphs"] if ":round1:" in g.episode_id}


#: SoloReviewConfig.finding_budget, the cap a solo submission is cut to.
SOLO_FINDING_BUDGET = 20


def _claude_as_solo(found: List[Dict[str, Any]], st: Dict[str, Any], graph) -> tuple:
    """A Claude session's findings as a solo submission reaches a matcher: its first
    `SOLO_FINDING_BUDGET`, each prose target located as `path:line` where `resolve_target` can."""

    kept, unresolved = [], 0
    for f in found[:SOLO_FINDING_BUDGET]:
        path, line, method = resolve_target(f.get("target"), graph)
        if path:
            f = {**f, "target": f"{path}:{line}" if line is not None else path}
        else:
            unresolved += 1
        kept.append(f)
    return kept, {**st, "findings": len(kept), "cut_to_budget": max(0, len(found) - SOLO_FINDING_BUDGET),
                  "targets_unresolved": unresolved}


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
            if not finished(spec.session_dir(pr, s))]


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
            # `diff --git` is the header line of the packet's own diff.patch, grepped for by name
            # (2 of 44 calls of a Phase 1 reader, 2026-09-30); it runs no git.
            if re.search(r"\bgit\b", text.replace("diff --git", "")):
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


def model_context(spec: ProbeSet, prs: List[int],
                  conventions: Optional[Dict[int, List[str]]] = None, closing: str = "") -> str:
    """The solo task's `context_file`: each PR's pass-0 model as one section, JSON lines, so a
    `gpt_5.2` session reads the same model a Claude session's `model.md` holds.

    With `conventions`, each PR's principles follow its model as a second section. Every PR must
    then be named: a PR whose brief is empty says so with `[]`, and reads the model alone.
    `closing` ends every conventions section (`conventions_section`).
    """

    models = render_models(spec.release, prs, spec.inventory)
    if conventions is not None and set(prs) - set(conventions):
        raise KeyError(f"no conventions listed for PRs {sorted(set(prs) - set(conventions))}")

    def sections(pr: int) -> List[Dict[str, str]]:
        held = [{"title": "The PR model (pass 0)", "text": models[pr]}]
        if conventions and conventions[pr]:
            held.append({"title": CONVENTIONS_TITLE, "text": conventions_section(conventions[pr], closing)})
        return held

    return "".join(json.dumps({"pr_number": pr, "sections": sections(pr)}, ensure_ascii=False) + "\n"
                   for pr in prs)


# --- A probe session as a scoreable run --------------------------------------------------------
#: Every imported probe finding carries the unlabelled pair (`schema/findings.py`); the solo task's
#: `user_prompt: v2` stamps the same pair, so a gpt reviewer that is not asked for labels reaches the
#: judge exactly as an imported Claude finding does.
from src.mathlib_review.schema.findings import IMPORT_ISSUE_KIND, UNLABELLED_FAMILY  # noqa: E402


def resolve_target(target: str, graph) -> tuple:
    """`(path, line, method)` for a probe finding's free-text `target`, off the change graph.

    A probe reviewer names what it asks about (`Dense.ciSup`, `Mathlib/X.lean`, `import in
    Foo.lean`); the solo anchoring takes a path and the line of the declaration, which is what the
    solo prompt asks gpt for. A declaration resolves to its reviewed-side entity's first line, by
    full name, then by a unique dotted suffix (as `open` allows), then by a unique short name. A
    file-level target resolves to the first changed line in that file. Anything else is
    `unresolved`: the finding is still imported and anchors nowhere, as an unanchored solo finding
    does.
    """

    t = str(target or "").strip().strip("`").strip()
    reviewed = [e for e in graph.entities if e.side == "reviewed" and e.fullname]

    def one(entities, method):
        spots = sorted({(e.path, e.span.line_start) for e in entities})
        return (spots[0][0], spots[0][1], method) if len(spots) == 1 else None

    parts = re.split(r",\s*|\s+and\s+", t)
    # A target that lists several declarations anchors on the first it names.
    for candidate in [t] + ([parts[0].strip()] if len(parts) > 1 else []):
        for found in (one([e for e in reviewed if e.fullname == candidate], "fullname"),
                      one([e for e in reviewed if e.fullname.endswith("." + candidate)], "fullname_suffix"),
                      one([e for e in reviewed if e.name == candidate], "name")):
            if found:
                return found
    first_changed = {}
    for r in graph.changed_ranges:
        if r.reviewed_span is not None:
            first_changed[r.path] = min(first_changed.get(r.path, r.reviewed_span.line_start),
                                        r.reviewed_span.line_start)
    by_file = [path for path in first_changed
               if t == path or t.endswith(path) or re.search(r"(^|[\s/])" + re.escape(Path(path).name) + r"\b", t)]
    if len(by_file) == 1:
        return by_file[0], first_changed[by_file[0]], "file"
    return None, None, "unresolved"


def import_probe_session(spec: ProbeSet, session: str, out: Path, logger=None) -> Dict[str, Any]:
    """Write one probe session's findings as a solo run's scoreable artifacts.

    Through the solo runner's own tail, so a Claude session reaches the judge by the path a gpt
    solo session does: each finding in `_normalize_findings`' shape, then `solo_responses` (the
    same anchoring onto change targets and work units), then `finalize`, which writes the
    `findings.jsonl` the judge scores. What differs, and is recorded in `probe_import.json`: the
    location comes from `resolve_target` rather than the model, the concern family is `other` and
    `issue_kind` a placeholder, and no evidence chain runs, so admission and publication are not
    comparable to a solo run's. No run manifest is written: the judge reads the source run as
    `unchecked`, which is what it is.
    """

    import collections
    import hashlib
    from types import SimpleNamespace

    from src.mathlib_review.io import jsonl_bytes, write_once
    from src.mathlib_review.review.candidates import anchoring_report
    from src.mathlib_review.review.finalize import finalize
    from src.mathlib_review.review.runner import (solo_responses, load_release, load_run,
                                                  select_units_and_episodes)

    missing = [pr for pr in spec.pr_numbers if not finished(spec.session_dir(pr, session))]
    if missing:
        raise FileNotFoundError(f"{session} has no findings.json or submission.json for PR(s) {missing}")
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"{out} exists; an import writes a run directory once")
    dataset, _scaffold, _ = load_run(Path(spec.dataset_config),
                                     overrides={"dataset": {"pr_numbers": list(spec.pr_numbers)}})
    release = load_release(dataset)
    units, episodes = select_units_and_episodes(dataset, release)
    graph_by_pr = {g.pr_number: g for g in release["graphs"] if ":round1:" in g.episode_id}
    episode_by_pr = {e.pr_number: e for e in episodes if ":round1:" in e.episode_id}
    budget = 20  # SoloReviewConfig.finding_budget: the cap a solo submission is cut to

    rows, methods, packets, cut = [], collections.Counter(), {}, {}
    for pr in spec.pr_numbers:
        # A swap session submits `submit_findings`' arguments, located by `path` and line as a solo
        # session's are; a brief-X session names a `target`, which `resolve_target` locates.
        submission = spec.session_dir(pr, session) / "submission.json"
        path = submission if submission.is_file() else spec.session_dir(pr, session) / "findings.json"
        packets[str(pr)] = hashlib.sha256(path.read_bytes()).hexdigest()
        payload = json.loads(path.read_text())
        submitted = payload["findings"] if submission.is_file() else payload
        if len(submitted) > budget:
            cut[str(pr)] = len(submitted) - budget
        normalized = []
        for raw in submitted[:budget]:
            claim = str(raw.get("claim") or "").strip()
            if not claim:
                continue
            if submission.is_file():
                line = raw.get("line_start") if isinstance(raw.get("line_start"), int) else None
                file, method = (str(raw["path"]), "path_and_line") if raw.get("path") else (None, "unresolved")
            else:
                file, line, method = resolve_target(raw.get("target"), graph_by_pr[pr])
            methods[method] += 1
            severity = str(raw.get("severity") or "").lower()
            normalized.append({
                "anchor": {"path": file, "line_start": line, "line_end": line} if file else None,
                "severity": severity if severity in ("blocking", "advisory") else "advisory",
                "claim": claim,
                "concern_family": UNLABELLED_FAMILY,
                "issue_kind": IMPORT_ISSUE_KIND,
                "suggested_fix": (str(raw.get("requested_change") or raw.get("suggested_fix"))
                                  if (raw.get("requested_change") or raw.get("suggested_fix")) else None),
                "evidence": (str(raw["evidence"]) if raw.get("evidence") else None),
                "verified": None,
                "confidence": None,
            })
        rows.append({"success": True, "episode_id": episode_by_pr[pr].episode_id, "pr_number": pr,
                     "findings": normalized})

    responses, anchor_rows = solo_responses(SimpleNamespace(task_results=rows), release["graphs"],
                                             units, logger)
    out.mkdir(parents=True)
    report = anchoring_report(anchor_rows)
    write_once(out / "anchoring.jsonl", jsonl_bytes(anchor_rows))
    write_json(out / "anchoring_report.json", report)
    summary = finalize(
        out, units=units, responses=responses, routing_mode="solo",
        execution_release=dataset.execution_release, exclude_methods=dataset.exclude_methods,
        pr_numbers=list(spec.pr_numbers), candidate_assessments=[],
        apply_lead_synthesis=dataset.apply_lead_synthesis, collect_supported=None,
        pr_finding_limit=dataset.pr_finding_limit, logger=logger)
    provenance = {
        "source": "probe session", "set": spec.name, "session": session,
        "packets_findings_sha256": packets, "target_resolution": dict(methods),
        "findings_past_the_budget": cut,
        "anchoring": report, "concern_family": UNLABELLED_FAMILY, "issue_kind_placeholder": IMPORT_ISSUE_KIND,
        "evidence_chain": "not run: the gate is closed, so admission and publication are not "
                          "comparable to a solo run's; the judge's issue recall reads every finding",
        "run_manifest": "not written: the judge reads this source as unchecked",
    }
    write_json(out / "probe_import.json", provenance)
    return {"findings_in": sum(len(r["findings"]) for r in rows), "resolution": dict(methods),
            "anchored": report.get("anchored"), "unanchored_rate": report.get("unanchored_rate"),
            "issues_total": summary.get("issues_total")}


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
