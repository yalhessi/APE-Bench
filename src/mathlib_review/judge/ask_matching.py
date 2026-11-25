"""The raw-ask matcher as a named, versioned instrument.

The matcher answers a different question from the registered judge (`judge/protocol.py`). The judge
scores one finding against one atomic gold obligation; the matcher scores a maintainer's first-round
ask, as the maintainer wrote it, against every finding of each anonymous reviewer at once, and says
`reached`, `partial` or `no`. Fourteen probes since 2026-09-29 read their results through it. Their
numbers and the judge's are never pooled or subtracted.

Two versions, and they are not declared equivalent:

- **`1-session`** (historical, import only). The rubric files under
  `results/pr_review_v5/probes/gpt52-postcutoff-2026-09-29/`, rendered for each batch's counts by
  `matcher_rubric`, handed to hand-launched Claude Code sessions that read input files from a folder
  and wrote `matches.json`. Results under it stay interpretable under that definition.
- **`2-task`** (active). The registered Task `lean_pr_review_ask_matching`. The judgment rules are
  v1's text byte for byte (pinned by a test against the v1 files); the input paragraph says the
  inputs are given below as sections named as v1's files were, and the output paragraph names a
  typed submit tool in place of `matches.json`. Whether a v2 verdict equals a v1 verdict on the same
  inputs is a calibration question on aligned saved examples, and calibration is user-run.

This module is the instrument's definition: its texts, the blind projection a matcher sees (fields
kept, redaction, location spelling), the blinding seal, the verdict's validation, and the unblinding
arithmetic every seal has been read with. It imports nothing from `analysis/`, so the registered Task
can use it (`tests/datasets/test_package_boundaries.py::test_the_task_layer_imports_no_reading`).
`analysis/probes.py` re-exports the names that lived there, for the readers on disk that import them.
"""

from __future__ import annotations

import json
import re
import secrets
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

from src.mathlib_review.io import sha256_bytes
from src.mathlib_review.schema import BlindPacket

INSTRUMENT = "ask-match"
V1_SESSION = "1-session"
V2_TASK = "2-task"
VERSIONS = (V1_SESSION, V2_TASK)
QUESTION_POLICIES = ("request_only", "questions")
QuestionPolicy = Literal["request_only", "questions"]

#: v1's two rubric files. Historical artifacts: read to identify and reproduce v1, never edited.
V1_RUBRIC_FILES = {
    "request_only": Path("results/pr_review_v5/probes/gpt52-postcutoff-2026-09-29/matcher_rubric.md"),
    "questions": Path(
        "results/pr_review_v5/probes/gpt52-postcutoff-2026-09-29/matcher_rubric_questions.md"),
}
MATCHER_RUBRIC = V1_RUBRIC_FILES["request_only"]
#: The same rubric with one paragraph more: a finding may be a question to the author (the filing
#: contract's pre-registration, 2026-10-12). A separate file, so every earlier seal stays reproducible.
MATCHER_RUBRIC_QUESTIONS = V1_RUBRIC_FILES["questions"]

_NUMBERS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
            9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}


def _word(n: int) -> str:
    return _NUMBERS.get(n, str(n))


def matcher_rubric(reviewers: int, prs: int, source: Path = MATCHER_RUBRIC) -> str:
    """v1: the rubric for this many reviewers and PRs. It was written for six and six, and for
    those it is returned unchanged. `source` is `MATCHER_RUBRIC` or `MATCHER_RUBRIC_QUESTIONS`;
    either reached the matcher as `matcher_rubric.md`, the name its prompt reads."""

    text = Path(source).read_text()
    pr_phrase = "one Mathlib pull request" if prs == 1 else f"{_word(prs)} Mathlib pull requests"
    text = text.replace("on six Mathlib pull requests. Six anonymous reviewers, `R1` to `R6`",
                        f"on {pr_phrase}. {_word(reviewers).capitalize()} anonymous reviewers, "
                        f"`R1` to `R{reviewers}`")
    text = text.replace("`R6_pr<N>.json`", f"`R{reviewers}_pr<N>.json`")
    text = text.replace('"R6": ..., "R6_finding": ...', f'"R{reviewers}": ..., "R{reviewers}_finding": ...')
    return text.replace('"R6": <count>', f'"R{reviewers}": <count>')


# --- v2: the registered Task's text --------------------------------------------------------------

_V2_HEAD = (
    "# Matching reviewer findings to maintainer asks\n\n"
    "You are judging, for a research study, which review findings reach which real maintainer "
    "requests\non {pr_phrase}. {reviewers_word} anonymous reviewers, `R1` to `R{reviewers}`, "
    "reviewed each PR without\nseeing the maintainers' comments. Their labels are shuffled per PR, "
    "so `R1` on one PR is not\nnecessarily `R1` on another.\n\n"
    "**Inputs.** They are given below, one section for each:\n"
    "- `asks_pr<N>.json`: the maintainers' first-round asks on PR N. Each has an `ask_id`, the file\n"
    "  `path`, `code_at_comment` (the code the comment is attached to, ending at the commented line),\n"
    "  the `comment`, and the comment it replies to, if any.\n"
    "- `R1_pr<N>.json` to `R{reviewers}_pr<N>.json`: each reviewer's findings, a list, indexed "
    "from 0.\n\n"
)

#: v1's judgment rules, verbatim, split where the question-form paragraph is inserted.
_JUDGMENT_HEAD = (
    "## For every ask, and each reviewer\n\nChoose one value:\n\n| value | when |\n|---|---|\n"
    "| `reached` | Some finding asks for the same change on the same thing, or for a change that, if "
    "the author made it, would satisfy the maintainer's ask. Wording may differ. \"Use the existing "
    "`foo`\" reaches \"this is `foo`\". |\n"
    "| `partial` | Some finding is about the same thing and the same kind of issue, but asks for a "
    "different change that would not satisfy the maintainer. For example, both say the name is "
    "wrong but propose different names, and the maintainer's reason is absent. |\n"
    "| `no` | Anything else. |\n"
)
_JUDGMENT_QUESTIONS = (
    "\nA finding may be a question to the author. Judge it like any other finding: it `reached` the "
    "ask when\nthe change it asks about is the maintainer's change (the author answering yes and "
    "making it would\nsatisfy the maintainer), or when the maintainer's ask is itself that question; "
    "it is `partial` when it\nasks about the same thing and the same kind of issue without naming the "
    "maintainer's change.\n"
)
_JUDGMENT_TAIL = (
    "\nAlso give the index of the best finding, or `null`.\n\n"
    "Judge only whether the finding would lead the author to the maintainer's change. Do not judge\n"
    "whether the finding is otherwise good.\n\n"
)

_V2_OUTPUT = (
    "## Output\n\n"
    "Call `submit_matches` once, with two arguments:\n"
    "- `asks`: one entry per ask, `{{\"pr\": N, \"ask_id\": \"...\", \"verdicts\": [{{\"reviewer\": "
    "\"R1\", \"value\": \"reached|partial|no\", \"finding\": i|null}}, ...], \"note\": \"<= 25 "
    "words\"}}`, with a verdict for each of `R1` to `R{reviewers}`.\n"
    "- `unmatched`: `{{\"<pr>\": {{\"R1\": <count of R1 findings reaching no ask>, ..., "
    "\"R{reviewers}\": <count>}}}}`.\n\n"
    "The tool refuses a submission that misses an ask or a reviewer, or names a finding that does "
    "not exist, and says which; correct it and submit again.\n"
)


def judgment_text(question_policy: QuestionPolicy) -> str:
    """The judgment rules, identical in v1 and v2 (`test_ask_matching.py` pins it)."""

    middle = _JUDGMENT_QUESTIONS if question_policy == "questions" else ""
    return _JUDGMENT_HEAD + middle + _JUDGMENT_TAIL


def v2_template(question_policy: QuestionPolicy) -> str:
    """The unrendered v2 rubric; its SHA-256 is the instrument's rubric identity."""

    return _V2_HEAD + judgment_text(question_policy) + _V2_OUTPUT


def render_v2_rubric(reviewers: int, prs: int, question_policy: QuestionPolicy) -> str:
    pr_phrase = "one Mathlib pull request" if prs == 1 else f"{_word(prs)} Mathlib pull requests"
    return v2_template(question_policy).format(
        pr_phrase=pr_phrase, reviewers_word=_word(reviewers).capitalize(), reviewers=reviewers)


def rubric_sha256(version: str, question_policy: QuestionPolicy) -> str:
    """The rubric identity: v1's file bytes, or v2's template. Both are rendered per batch."""

    if version == V1_SESSION:
        return sha256_bytes(V1_RUBRIC_FILES[question_policy].read_bytes())
    if version == V2_TASK:
        return sha256_bytes(v2_template(question_policy).encode("utf-8"))
    raise ValueError(f"unknown {INSTRUMENT} version {version!r}; known: {VERSIONS}")


def _json(payload: Any) -> str:
    """The bytes a v1 input file held (`probes.write_json`): indent 1, unescaped."""

    return json.dumps(payload, ensure_ascii=False, indent=1)


def packet_files(packet: BlindPacket) -> Dict[str, Any]:
    """{file name: content} for one PR, exactly as v1 wrote its input files."""

    files: Dict[str, Any] = {f"asks_pr{packet.pr}.json":
                             [a.model_dump(mode="json") for a in packet.asks]}
    for label in sorted(packet.reviewers, key=_label_order):
        files[f"{label}_pr{packet.pr}.json"] = [
            f.model_dump(mode="json") for f in packet.reviewers[label]]
    return files


def _label_order(label: str):
    digits = label[1:]
    return (label[:1], int(digits)) if digits.isdigit() else (label, 0)


def labels_of(packets: Sequence[BlindPacket]) -> List[str]:
    """The reviewer labels of a batch, which every PR in it must share."""

    shapes = {tuple(sorted(p.reviewers, key=_label_order)) for p in packets}
    if len(shapes) != 1:
        raise ValueError(f"every PR in a batch needs the same reviewer labels, got {sorted(shapes)}")
    return list(shapes.pop())


def render_matcher_prompt(packets: Sequence[BlindPacket], question_policy: QuestionPolicy) -> str:
    """v2's whole first message: the rubric for this batch's counts, then every input section."""

    labels = labels_of(packets)
    parts = [render_v2_rubric(len(labels), len(packets), question_policy), "## Inputs\n"]
    for packet in sorted(packets, key=lambda p: p.pr):
        for name, content in packet_files(packet).items():
            parts.append(f"### `{name}`\n\n```json\n{_json(content)}\n```\n")
    return "\n".join(parts)


# --- The blind projection ------------------------------------------------------------------------

#: A matcher sees a finding as these four fields and nothing else.
KEEP = ("target", "claim", "requested_change", "severity")
_REDACT = [(re.compile(r"\bpass \d(?:'s)?\s+"), ""), (re.compile(r"\bc\d{1,3}\b"), "a compiled check")]
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


def blind_findings(found: List[Dict[str, Any]], conventions: bool = False) -> List[Dict[str, Any]]:
    """Findings as a matcher sees them: an index and `KEEP`, the target respelt, the text redacted."""

    return [{"i": n, **{k: repo_target(f.get(k)) if k == "target" else redact(f.get(k), conventions)
                        for k in KEEP}} for n, f in enumerate(found)]


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

    seal = {}
    for pr in prs:
        pool, order = list(sessions), []
        while pool:
            order.append(pool.pop(secrets.randbelow(len(pool))))
        seal[str(pr)] = {f"R{i + 1}": s for i, s in enumerate(order)}
    return seal


# --- The verdict ---------------------------------------------------------------------------------


class ReviewerVerdict(BaseModel):
    """One reviewer's value on one ask, as `submit_matches` takes it."""

    model_config = ConfigDict(extra="forbid")
    reviewer: str = Field(description="The reviewer label, `R1`, `R2`, ...")
    value: Literal["reached", "partial", "no"]
    finding: Optional[int] = Field(default=None, description="Index of the best finding, or null.")


class AskVerdict(BaseModel):
    """Every reviewer's value on one ask."""

    model_config = ConfigDict(extra="forbid")
    pr: int
    ask_id: str
    verdicts: List[ReviewerVerdict]
    note: str = ""


def flat_rows(asks: Sequence[AskVerdict]) -> List[Dict[str, Any]]:
    """The historical `matches.json` row shape, which `unblind` reads."""

    rows = []
    for ask in asks:
        row: Dict[str, Any] = {"pr": ask.pr, "ask_id": ask.ask_id}
        for verdict in sorted(ask.verdicts, key=lambda v: _label_order(v.reviewer)):
            row[verdict.reviewer] = verdict.value
            row[f"{verdict.reviewer}_finding"] = verdict.finding
        row["note"] = ask.note
        rows.append(row)
    return rows


def verdict_problems(packets: Sequence[BlindPacket], rows: Sequence[Dict[str, Any]],
                     unmatched: Optional[Dict[str, Dict[str, Any]]], *,
                     require_unmatched: bool = True) -> List[str]:
    """Everything wrong with a verdict on these packets; empty when it covers exactly them.

    Every ask of every PR once, a legal value for every label, a finding index that exists, and an
    unmatched count per PR and label within that label's findings. Applied to a task submission
    (refused until it holds) and to an imported `matches.json` alike, so a missing cell is a
    coverage gap and never a silent `no` -- the old `unblind` read an absent cell as unreached.
    """

    problems: List[str] = []
    by_pr = {p.pr: p for p in packets}
    expected = {(p.pr, a.ask_id) for p in packets for a in p.asks}
    seen = set()
    for row in rows:
        try:
            key = (int(row.get("pr")), str(row.get("ask_id")))
        except (TypeError, ValueError):
            problems.append(f"a row has no usable pr: {str(row)[:80]}")
            continue
        if key not in expected:
            problems.append(f"PR {key[0]} has no ask {key[1]!r} in this batch")
            continue
        if key in seen:
            problems.append(f"ask {key[1]!r} on PR {key[0]} is answered twice")
        seen.add(key)
        packet = by_pr[key[0]]
        for label, found in packet.reviewers.items():
            value = row.get(label)
            if value not in ("reached", "partial", "no"):
                problems.append(f"ask {key[1]!r} on PR {key[0]}: {label} is {value!r}, not "
                                "reached, partial or no")
            index = row.get(f"{label}_finding")
            if index is not None and (not isinstance(index, int) or isinstance(index, bool)
                                      or not 0 <= index < len(found)):
                problems.append(f"ask {key[1]!r} on PR {key[0]}: {label}_finding {index!r} is not "
                                f"an index of its {len(found)} findings")
        extra = {k for k in row if k not in ("pr", "ask_id", "note")
                 and k.removesuffix("_finding") not in packet.reviewers}
        if extra:
            problems.append(f"ask {key[1]!r} on PR {key[0]} names {sorted(extra)}, which are not "
                            "this PR's reviewers")
    for pr, ask_id in sorted(expected - seen):
        problems.append(f"ask {ask_id!r} on PR {pr} has no verdict")
    if unmatched is None:
        if require_unmatched:
            problems.append("no unmatched counts")
        return problems
    for pr, packet in by_pr.items():
        counts = unmatched.get(str(pr))
        if counts is None:
            if require_unmatched:
                problems.append(f"no unmatched counts for PR {pr}")
            continue
        for label, found in packet.reviewers.items():
            count = counts.get(label)
            if not isinstance(count, int) or isinstance(count, bool) or not 0 <= count <= len(found):
                problems.append(f"PR {pr}: unmatched {label} is {count!r}, not a count of its "
                                f"{len(found)} findings")
    return problems


# --- Unblinding ----------------------------------------------------------------------------------


def condition(session: str) -> str:
    """A session label's condition: the label without its trailing digits (X1 -> X, Gr2 -> Gr)."""
    return session.rstrip("0123456789")


def missing_cells(asks: Dict[str, Any], seal: Dict[str, Dict[str, str]],
                  matches: Dict[str, Dict[str, Any]], scope: Optional[set] = None) -> Dict[str, List[str]]:
    """{matcher: ["<pr> <ask> <label>", ...]}: the cells a matcher's file gives no value for.

    `unblind` reads an absent cell as not reached. The shared report marks such a matching forensic
    (`analysis/matching.report_matching`); the historical `probe unblind` refuses it unless told
    the input is incomplete, which is the same rule."""

    items = [(pr, cid) for pr in seal for cid in asks["asks"][pr]
             if scope is None or asks["families"].get(cid) in scope]
    out = {}
    for m, d in matches.items():
        given = {(str(a["pr"]), a["ask_id"], label) for a in d["asks"] if str(a["pr"]) in seal
                 for label in seal[str(a["pr"])] if a.get(label) in ("reached", "partial", "no")}
        lost = [f"{pr} {cid} {label}" for pr, cid in items for label in seal[pr]
                if (pr, cid, label) not in given]
        if lost:
            out[m] = lost
    return out


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
            "condition_reach": {c: (sum(reach[s] for s in ss) / len(ss) if items else None)
                                for c, ss in conds.items()},
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
