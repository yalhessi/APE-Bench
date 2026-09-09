"""What the arms actually asked the repository, from the durable trajectory sidecar.

The run artifacts record *conclusions*. `trajectory.py` makes the work durable by walking
`.ape` once and writing turns into `results/`; this module turns those turns into the one
thing the oracle ladder has to be able to separate: did an arm fail because it never asked the
right question, or because asking did not help?

Measured on `pr5_smoke4_rep9`, which is what made this necessary. Of **176** `content_search`
calls in the whole run, **2** used a tactic-shaped pattern and neither came from a proof arm;
`proof_idiom` and `proof_golf` made 9 between them and confined every one to the file they were
handed, while `naming` went repository-wide 29 times and `duplication` 36. The search vocabulary
is nouns -- declaration names, namespaces, type signatures -- and almost never verbs.

**Two rates, both arm-scoped, never global targets.** A tactic-shaped rate is meaningful for
`proof_idiom` and close to meaningless for `naming`, whose job *is* identifier lookup. Reporting
one number over all arms would turn a correct division of labour into a defect.

**What this cannot tell you.** `content_search` returns at most `limit` files (default 20) with
no corpus total and no truncation flag of its own, so a returned-file count is a floor, never a
census: `possibly_truncated` marks where the tool stopped counting rather than ran out. And the
result bodies in the trajectory are capped, so a file count read back from one is a floor on a
floor -- `body_truncated` says when.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.mathlib_review.paths import assert_repo_root, run_dir

QUERY_ANALYSIS_VERSION = "v5-query-analysis/1"

#: Tactic names a Mathlib reviewer would reach for. Versioned with the analysis and reported
#: per arm, because "did this arm ever ask about a tactic" is only a question for the arms
#: whose warrant is tactic idiom.
TACTIC_VOCABULARY_VERSION = "v5-tactic-vocabulary/1"
TACTIC_VOCABULARY = (
    "grind", "by_cases", "gcongr", "grw", "omega", "fun_prop", "decide", "simpa",
    "simp_all", "norm_num", "positivity", "aesop", "field_simp", "ring_nf", "calc",
    "bound", "linarith", "nlinarith", "polyrith", "continuity", "measurability",
)

#: The same question asked with a deliberately generous boundary. `simp`, `rw` and `exact` are
#: tactic names too, and excluding them could be argued either way -- a search for `@[simp]`
#: is looking for an attributed lemma, not for tactic idiom.
#:
#: Both are reported because the finding must not rest on where that line is drawn. On
#: `pr5_smoke4_rep9` the wide vocabulary takes tactic-shaped queries from 2 to 14 and leaves
#: `proof_idiom` and `proof_golf` at **zero under both**, while `style` goes to nine. A result
#: that survives its own definition being loosened sevenfold is not a definition artifact.
WIDE_TACTIC_VOCABULARY = TACTIC_VOCABULARY + (
    "simp", "rw", "erw", "norm_cast", "push_cast", "ring", "abel", "exact", "apply",
)

#: The arms whose stated job is tactic idiom, and for whom a zero tactic-shaped rate is a
#: finding rather than correct behaviour.
PROOF_ARMS = frozenset({"proof_idiom", "proof_golf"})

#: `content_search`'s own default. Recorded per query so `possibly_truncated` means something
#: even when the arm did not state a limit.
DEFAULT_CONTENT_SEARCH_LIMIT = 20

#: Tools whose input is a query over the repository. `declaration_search` is included because
#: "did the arm look something up by name" is exactly the contrast the proof-arm finding rests
#: on; it has no scope of its own, so its scope class is always `null`.
QUERY_TOOLS = ("content_search", "declaration_search", "precedent_search", "zulip_search")

_WORKSPACE_ROOTS = ("target", "target/Mathlib")


@dataclass
class Query:
    """One repository question, as asked and as answered."""

    run_name: str
    pr_number: Optional[int]
    conversation_id: str
    arm_id: Optional[str]
    tool: str
    pattern: Optional[str]
    path: Optional[str]
    scope_class: Optional[str]
    limit: Optional[int]
    tactic_shaped: bool
    tactic_shaped_wide: bool
    returned_files: Optional[int]
    possibly_truncated: Optional[bool]
    result_bytes: Optional[int]
    body_truncated: Optional[bool]


def scope_class_of(path: Optional[str]) -> Optional[str]:
    """`corpus`, `subtree` or `file` -- never a path equality test.

    The earlier hand count keyed on `path == "target/Mathlib"`, which silently reclassifies the
    moment a caller writes a trailing slash or searches `target` instead.
    """

    if not path:
        # An omitted path is the tool's own default root, which is the whole workspace.
        return "corpus"
    cleaned = path.rstrip("/")
    if cleaned in _WORKSPACE_ROOTS:
        return "corpus"
    return "file" if Path(cleaned).suffix else "subtree"


#: Regex syntax that appears *inside* a query string and must not be read as word characters.
#: The case that forced this: the generalist searched for the literal pattern `\bgrind\b`, and
#: a naive word-boundary test scores it as NOT asking about `grind` -- the `b` of the escape
#: sits against the `g` and closes the boundary. Reading a `grind` search as a non-tactic
#: search is the exact error this analysis exists to avoid, so the query is normalized before
#: it is classified.
_REGEX_NOISE = re.compile(r"\\[bBsSwWdDAZzG]|[\\^$.|?*+()\[\]{}]")


def is_tactic_shaped(pattern: Optional[str],
                     vocabulary: Iterable[str] = TACTIC_VOCABULARY) -> bool:
    """Does this pattern ask about a tactic rather than a name?

    Word-boundary matched against the *normalized* query, so `card_le_of_isSeparated` is not
    read as asking about `calc`, a lemma called `decide_eq` is not read as asking about
    `decide`, and a regex like `\bgrind\b` is read as asking about `grind`.
    """

    if not pattern:
        return False
    cleaned = _REGEX_NOISE.sub(" ", pattern)
    return any(re.search(rf"\b{re.escape(word)}\b", cleaned) for word in vocabulary)


def _result_facts(body: str, byte_count: Optional[int], cap: int) -> Dict[str, Any]:
    """What the result says, and how much of it we are allowed to believe."""

    truncated_body = bool(byte_count and byte_count > cap)
    try:
        payload = json.loads(body)
        files = len(payload.get("results") or [])
    except (json.JSONDecodeError, AttributeError, TypeError):
        # A truncated body is not valid JSON; count path keys instead and say it is a floor.
        files = body.count('"path":') if isinstance(body, str) else None
    return {"returned_files": files, "result_bytes": byte_count,
            "body_truncated": truncated_body}


def _turn_files(run: str) -> List[Path]:
    return sorted((run_dir(run) / "trajectory" / "turns").glob("pr-*.jsonl"))


def _arm_by_conversation(run: str) -> Dict[str, Dict[str, Any]]:
    """`conversation_id -> {arm_id, pr_number}`, from the trajectory's own invocation rows."""

    index: Dict[str, Dict[str, Any]] = {}
    for name in ("invocations.jsonl", "leads.jsonl"):
        path = run_dir(run) / "trajectory" / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            key = row.get("invocation_id")
            if key:
                index[key] = {"arm_id": row.get("arm_id") or ("lead" if name.startswith("lead")
                                                              else None),
                              "pr_number": row.get("pr_number")}
    return index


def extract(run: str, cap: int = 2000) -> List[Query]:
    """Every repository question this run asked, from `results/` alone."""

    index = _arm_by_conversation(run)
    queries: List[Query] = []
    for path in _turn_files(run):
        pr_number = int(path.stem.split("-")[1])
        pending: Dict[str, Dict[str, Any]] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            conversation = row.get("conversation_id") or ""
            meta = index.get(conversation, {})
            for item in row.get("items") or []:
                if item.get("t") == "use" and item.get("name") in QUERY_TOOLS:
                    try:
                        payload = json.loads(item.get("v") or "{}")
                    except json.JSONDecodeError:
                        payload = {}
                    pattern = (payload.get("content_pattern") or payload.get("identifier")
                               or payload.get("query") or payload.get("text"))
                    query = Query(
                        run_name=run, pr_number=meta.get("pr_number") or pr_number,
                        conversation_id=conversation, arm_id=meta.get("arm_id"),
                        tool=item["name"], pattern=pattern,
                        path=payload.get("path"),
                        scope_class=(scope_class_of(payload.get("path"))
                                     if item["name"] == "content_search" else None),
                        limit=payload.get("limit") or (
                            DEFAULT_CONTENT_SEARCH_LIMIT
                            if item["name"] == "content_search" else None),
                        tactic_shaped=is_tactic_shaped(pattern),
                        tactic_shaped_wide=is_tactic_shaped(
                            pattern, WIDE_TACTIC_VOCABULARY),
                        returned_files=None, possibly_truncated=None,
                        result_bytes=None, body_truncated=None,
                    )
                    queries.append(query)
                    if item.get("id"):
                        pending[item["id"]] = {"query": query}
                elif item.get("t") == "res" and item.get("id") in pending:
                    query = pending.pop(item["id"])["query"]
                    facts = _result_facts(item.get("v") or "", item.get("bytes"), cap)
                    query.returned_files = facts["returned_files"]
                    query.result_bytes = facts["result_bytes"]
                    query.body_truncated = facts["body_truncated"]
                    if query.limit and facts["returned_files"] is not None:
                        query.possibly_truncated = facts["returned_files"] >= query.limit
    return queries


def by_arm(queries: Iterable[Query]) -> Dict[str, Dict[str, Any]]:
    """Per-arm query shape. Never aggregated into one number -- see the module docstring."""

    rows: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"queries": 0, "content_search": 0, "corpus_scope": 0, "file_scope": 0,
                 "subtree_scope": 0, "tactic_shaped": 0, "tactic_shaped_wide": 0,
                 "truncated": 0})
    for query in queries:
        row = rows[query.arm_id or "unattributed"]
        row["queries"] += 1
        if query.tactic_shaped:
            row["tactic_shaped"] += 1
        if query.tactic_shaped_wide:
            row["tactic_shaped_wide"] += 1
        if query.possibly_truncated:
            row["truncated"] += 1
        if query.tool == "content_search":
            row["content_search"] += 1
            if query.scope_class:
                row[f"{query.scope_class}_scope"] += 1
    for arm, row in rows.items():
        searches = row["content_search"]
        row["corpus_rate"] = round(row["corpus_scope"] / searches, 4) if searches else None
        row["tactic_shaped_rate"] = (
            round(row["tactic_shaped"] / searches, 4) if searches else None)
        row["tactic_shaped_wide_rate"] = (
            round(row["tactic_shaped_wide"] / searches, 4) if searches else None)
        row["is_proof_arm"] = arm in PROOF_ARMS
    return dict(sorted(rows.items()))


def report(run: str, queries: Iterable[Query]) -> Dict[str, Any]:
    queries = list(queries)
    return {
        "schema_version": QUERY_ANALYSIS_VERSION,
        "tactic_vocabulary_version": TACTIC_VOCABULARY_VERSION,
        "tactic_vocabulary": list(TACTIC_VOCABULARY),
        "wide_tactic_vocabulary": list(WIDE_TACTIC_VOCABULARY),
        "run_name": run,
        "queries": len(queries),
        "note": (
            "Rates are per arm and are diagnostics, not targets. A tactic-shaped rate is a "
            "question for the arms whose warrant is tactic idiom and close to meaningless for "
            "`naming`, whose job is identifier lookup. `returned_files` is a floor: "
            "content_search stops at `limit` and reports no corpus total."
        ),
        "by_arm": by_arm(queries),
    }


def write(run: str, cap: int = 2000) -> Dict[str, Any]:
    out = run_dir(run) / "trajectory"
    out.mkdir(parents=True, exist_ok=True)
    queries = extract(run, cap)
    (out / "queries.jsonl").write_text(
        "".join(json.dumps(asdict(query), ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")) + "\n" for query in queries),
        encoding="utf-8")
    payload = report(run, queries)
    (out / "queries_report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    assert_repo_root()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", required=True)
    parser.add_argument("--tool-result-cap", type=int, default=2000)
    args = parser.parse_args()
    payload = write(args.run, args.tool_result_cap)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
