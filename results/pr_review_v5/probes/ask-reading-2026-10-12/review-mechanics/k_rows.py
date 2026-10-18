"""Dump every K row (concern named and dropped) with its full quote, for the hand classification of
the ground; writes k_rows.tsv. The hand codes go in k_grounds.jsonl (one row each: set, ask, session,
ground, note); tally.py compares them with the draft's counts."""
import csv
from pathlib import Path

from load import rows

HERE = Path(__file__).resolve().parent


def main():
    K = [r for r in rows() if r["behaviour"] == "K"]
    with open(HERE / "k_rows.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["n", "batch", "set", "ask", "family", "session", "line", "knowledge", "ap_use", "quote"])
        for i, r in enumerate(K, 1):
            w.writerow([i, r["batch"], r["set"], r["ask"], r["family"], r["session"], r["line"], r.get("knowledge"),
                        r.get("ap_use"), " ".join((r.get("quote") or "").split())])
    for i, r in enumerate(K, 1):
        print(f"{i:3} {r['ask']} {r['session']} [{r['batch']}] ({r.get('knowledge')}, ap_use={r.get('ap_use')}) l.{r['line']}\n     {' '.join((r.get('quote') or '').split())}")


if __name__ == "__main__":
    main()
