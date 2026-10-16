"""Score the stated-grounds reading by PROTOCOL.md, written before any label exists.

usage (repo root): ape/bin/python <this file>
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "src"))
from src.mathlib_review.io import jsonl_rows  # noqa: E402

HERE = Path(__file__).resolve().parent
KINDS = ("principle", "scope_form", "currency", "authority", "preference", "fact", "other")
PICTURE = ("principle", "scope_form", "currency", "fact")


def reader(letter: str) -> dict:
    out = {}
    for b in (1, 2, 3, 4):
        path = HERE / "readings" / f"{letter}_{b}.jsonl"
        if path.is_file():
            out.update({row["cid"]: row for row in jsonl_rows(path)})
    return out


def table(label: str, rows) -> None:
    c = Counter(r["primary"] for r in rows)
    stated = sum(c[k] for k in KINDS)
    if not stated:
        print(f"  {label:26} (no stated grounds)")
        return
    pa = (c["preference"] + c["authority"]) / stated
    pr = c["principle"] / stated
    pic = sum(c[k] for k in PICTURE) / stated
    verdict = ("CONTRADICTED" if pa >= 1 / 3 or pr < 0.1 else "SUPPORTED" if pic >= 2 / 3 else "mixed")
    shares = "  ".join(f"{k} {c[k]}" for k in KINDS)
    print(f"  {label:26} stated {stated:3} (none {c['none']:3}) | {shares} | pref+auth {pa:.0%} principle {pr:.0%} "
          f"picture {pic:.0%} -> {verdict}")


def main() -> int:
    sel = {row["cid"]: row for row in jsonl_rows(HERE / "selected.jsonl")}
    readers = {r: reader(r) for r in ("A", "B")}
    for r, got in readers.items():
        print(f"reader {r}: {len(got)} of {len(sel)} coded")
    both = [c for c in sel if c in readers["A"] and c in readers["B"]]
    agree = [c for c in both if readers["A"][c]["primary"] == readers["B"][c]["primary"]]
    print(f"agreement on primary: {len(agree)} of {len(both)}")
    for r, got in readers.items():
        table(f"reader {r}", [got[c] for c in sel if c in got])
    table("both agree", [readers["A"][c] for c in agree])
    print("\nmarginals (both agree):")
    table("AI-authored PRs", [readers["A"][c] for c in agree if sel[c]["ai"]])
    table("other PRs", [readers["A"][c] for c in agree if not sel[c]["ai"]])
    table("head (top-50 entry)", [readers["A"][c] for c in agree if (sel[c]["rank"] or 999) <= 50])
    table("tail", [readers["A"][c] for c in agree if (sel[c]["rank"] or 999) > 50])
    scopes = Counter(readers[r][c].get("scope") for r in readers for c in sel if c in readers[r]
                     and readers[r][c]["primary"] == "scope_form")
    principles = Counter((readers[r][c].get("principle_named") or "").lower() for r in readers for c in sel
                         if c in readers[r] and readers[r][c]["primary"] == "principle")
    print("\nscope levels named (scope_form, both readers):", dict(scopes.most_common()))
    print("principles named (both readers):", dict(principles.most_common(12)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
