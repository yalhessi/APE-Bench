"""What each carry-over session verified against what it filed, on the six post-cutoff PRs.

Usage, from the repo root: python results/pr_review_v5/probes/model-inspection-2026-09-30/filing.py

A verified edit is a `lean_verify_edit` call carrying an edit (`new_declaration` or `replacement`)
whose result is `verified_edit` with `success: true`, deduplicated by declaration name (or by file and
line span). It counts as filed when a submitted finding names the declaration's last component or
overlaps its line span in the same file. A heuristic: it undercounts a filing that names neither.
"""
import glob
import importlib.util
import json
from collections import Counter

spec = importlib.util.spec_from_file_location(
    "coh", "results/pr_review_v5/probes/carryover-coherence-2026-09-30/coherence.py")
coh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coh)
RUNS = {"gpt_5.2 carried (Grc)": "probe_postcutoff_gpt52_Grc_rep1",
        "gpt-5.4 carried (Hac)": "probe_postcutoff_gpt54_Grc_rep1",
        "gpt-5.5 carried (Hbc)": "probe_postcutoff_gpt55_Grc_rep1",
        "gpt_5.2 Chat (Gr1)": "probe_postcutoff_gpt52_Gr_rep1"}


def verified(calls, results):
    out = {}
    for _, cid, name, a in calls:
        if name != "lean_verify_edit" or not (a.get("new_declaration") or "replacement" in a):
            continue
        r = results.get(cid) or ""
        if r.startswith('{"success": true') and "verified_edit" in r:
            key = a.get("declaration_name") or f"{a.get('path', '').split('/')[-1]}:{a.get('line_start')}-{a.get('line_end')}"
            out.setdefault(key, (a.get("path"), a.get("line_start"), a.get("line_end")))
    return out


def filed(key, where, findings):
    path, lo, hi = where
    leaf = key.split(".")[-1]
    for f in findings:
        if ":" not in key and leaf in json.dumps(f, ensure_ascii=False):
            return True
        if lo and f.get("line_start") and f.get("path") == path and \
                f["line_start"] <= (hi or lo) and (f.get("line_end") or f["line_start"]) >= lo:
            return True
    return False


def main():
    print("| session set | PR | tool calls | edits verified | findings filed | verified, not filed |")
    print("|---|---|---|---|---|---|")
    totals = {}
    for label, run in RUNS.items():
        t = Counter()
        for task in sorted(glob.glob(f".ape/runs/{run}/tasks/*")):
            s = coh.session(task)
            calls, results, _, _ = coh.conversation(task)
            submits = [a for _, _, n, a in calls if n == "submit_findings"]
            findings = (submits[-1].get("findings") or []) if submits else []
            ed = verified(calls, results)
            held = [k for k, w in ed.items() if not filed(k, w, findings)]
            t.update(calls=len(calls), verified=len(ed), held=len(held), findings=len(findings))
            print(f"| {label} | {s['pr']} | {len(calls)} | {len(ed)} | {len(findings)} | "
                  f"{', '.join(f'`{k}`' for k in held) or '-'} |")
        totals[label] = t
    print("\n| session set | tool calls | edits verified | findings | verified, not filed |\n|---|---|---|---|---|")
    for label, t in totals.items():
        print(f"| {label} | {t['calls']} | {t['verified']} | {t['findings']} | {t['held']} ({t['held'] / max(t['verified'], 1):.0%}) |")


if __name__ == "__main__":
    main()
