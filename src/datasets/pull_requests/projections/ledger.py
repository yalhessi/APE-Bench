"""The A→B ledger: every reviewer correction that arrives as code, paired with the code it replaces.

A convention is "code that looks like A should look like B". The August gate showed the situation
keys built earlier do not describe what reviewers ask for -- they describe the declaration, while
reviewers ask about a pattern in the code -- and that the evidence is already machine-readable:
30 % of reviewer comments carry a GitHub ```` ```suggestion ```` block, B written as compilable
code, and none of the 32 non-requests in the rated sample carried one.

One row per reviewer-view comment with a suggestion block:

* **A** -- the commented line(s). GitHub ends a comment's `diff_hunk` at the commented line
  (328/328 measured), so A is the hunk's tail; for a multi-line comment, the
  `original_start_line..original_line` range walked back from the tail on the comment's side.
  Rows collected before position fields existed get the tail alone, flagged `a_span="tail_only"`.
* **B** -- the suggestion block's contents.
* where it happened -- the declaration enclosing the tail (`review_join.situate_hunk`) and its
  situation keys, kept as metadata to condition on, not as the join key.
* when and who -- so a transformation can be counted per month, which is its direction.

`transformation` is the pair of leading tokens (`positivity -> grind`). That is the crudest useful
grouping and is named as such; `aesop -> grind` and `positivity -> grind` are one convention it
splits in two.
"""

from __future__ import annotations

import collections
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.datasets.pull_requests.projections.corpus import reviewer_view
from src.datasets.pull_requests.store import write_atomically
from src.mathlib_review.io import jsonl_bytes, sha256_bytes

LEDGER_VERSION = "ab-ledger/1"
SUGGESTION_BLOCK = re.compile(r"```suggestion[^\n]*\n(.*?)```", re.S)
_TOKEN = re.compile(r"^\s*(?:·\s*)?(?:\|\s*)?([A-Za-z_][A-Za-z0-9_'!?.₀-₉]*|@\[|/--|--|⟨|\(|\S)")


def leading_token(line: str) -> str:
    match = _TOKEN.match(line or "")
    return match.group(1) if match else ""


def _hunk_lines(hunk: str) -> List[str]:
    lines = (hunk or "").split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def commented_lines(row: Dict[str, Any]) -> tuple:
    """(A lines, span kind). Walks back from the hunk's tail over lines on the comment's side."""

    lines = _hunk_lines(row.get("diff_hunk") or "")[1:]          # drop the @@ header
    if not lines:
        return [], "empty"
    start, end = row.get("original_start_line"), row.get("original_line")
    if start is None and row.get("start_line") and row.get("original_position") is not None:
        start = row.get("start_line")
    if start is None or end is None or int(start) >= int(end):
        return [lines[-1][1:] if lines[-1][:1] in "+- " else lines[-1]], (
            "single" if row.get("original_position") is not None else "tail_only")
    want = int(end) - int(start) + 1
    drop = "-" if (row.get("side") or "RIGHT") == "RIGHT" else "+"
    picked: List[str] = []
    for line in reversed(lines):
        if line[:1] == drop:
            continue
        picked.append(line[1:] if line[:1] in "+- " else line)
        if len(picked) == want:
            break
    return list(reversed(picked)), "range"


def ledger_rows(corpus_rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    from src.mathlib_review.conventions.review_join import situate_hunk

    out = []
    for row in reviewer_view(corpus_rows):
        match = SUGGESTION_BLOCK.search(row.get("body") or "")
        if not match:
            continue
        a_lines, span = commented_lines(row)
        b_block = match.group(1).rstrip("\n")
        b_lines = b_block.split("\n") if b_block else []
        situated = situate_hunk(row.get("diff_hunk") or "")
        situation = situated.get("situation")
        a_tok = leading_token(a_lines[0]) if a_lines else ""
        b_tok = leading_token(b_lines[0]) if b_lines else "(deleted)"
        out.append({
            "schema_version": LEDGER_VERSION,
            "comment_id": row["comment_id"], "pr_number": row["pr_number"],
            "created_at": row["created_at"], "month": str(row["created_at"] or "")[:7],
            "reviewer": row["commenter"], "reviewer_basis": row["reviewer_basis"],
            "path": row["path"], "declaration": situated.get("declaration"),
            "kind": situated.get("kind"), "resolved_via": situated.get("resolved_via"),
            "situation_keys": situation.keys() if situation else {},
            "a_lines": a_lines, "a_span": span, "b_lines": b_lines,
            "a_leading": a_tok, "b_leading": b_tok,
            "transformation": f"{a_tok} -> {b_tok}" if a_tok != b_tok else f"{a_tok} (edited)",
            "html_url": row.get("html_url"),
        })
    out.sort(key=lambda r: (r["created_at"] or "", r["comment_id"] or 0))
    return out


def write_ledger(corpus_dir: Path, out: Optional[Path] = None) -> Dict[str, Any]:
    comments = corpus_dir / "comments.jsonl"
    corpus_manifest = json.loads((corpus_dir / "manifest.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in comments.read_text(encoding="utf-8").splitlines() if line.strip()]
    ledger = ledger_rows(rows)
    out = Path(out) if out else corpus_dir.parent / "ledger"
    content = jsonl_bytes(ledger)
    write_atomically(out / "ab_ledger.jsonl", content)
    by_month = collections.Counter(r["month"] for r in ledger)
    manifest = {
        "ledger_version": LEDGER_VERSION, "rows": len(ledger), "ledger_sha256": sha256_bytes(content),
        "source_corpus_sha256": corpus_manifest["comments_sha256"],
        "source_store_content_sha256": corpus_manifest["store_content_sha256"],
        "source_view": corpus_manifest["view"],
        "by_span": dict(collections.Counter(r["a_span"] for r in ledger)),
        "by_month": dict(sorted(by_month.items())),
        "top_transformations": dict(collections.Counter(
            r["transformation"] for r in ledger if "(edited)" not in r["transformation"]).most_common(40)),
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    write_atomically(out / "manifest.json", (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())
    return manifest


if __name__ == "__main__":
    import argparse

    from src.mathlib_review.paths import PULL_REQUESTS_STORE, assert_repo_root

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corpus", type=Path, default=PULL_REQUESTS_STORE / "projections" / "corpus")
    args = parser.parse_args()
    assert_repo_root()
    manifest = write_ledger(args.corpus)
    print(json.dumps({k: manifest[k] for k in ("rows", "by_span", "by_month")}, indent=2))
    print("top transformations:", json.dumps(dict(list(manifest["top_transformations"].items())[:20]), indent=1))
