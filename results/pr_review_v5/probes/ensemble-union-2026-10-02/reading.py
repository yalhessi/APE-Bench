"""The ensemble's union, read from the four Opus passes already on disk (2026-10-02).

Reads the derived run `union_dev_opus_4pass_v1` (`cli report union`), its judge audit, and the
four passes' own audits, and prints, under the rule `docs/todo/ensemble-union-reading.md` stated
before the judge ran:

1. the rule: the union's judged issue recall against 10 of 23, its control emission against 2.0
   findings per control PR;
2. the per-obligation spine: each pass's verdict beside the union's, the passes' own union (the
   spine's 11) and which obligations moved under the judge's fresh verdicts;
3. the K=2 and K=3 subsets (H-claude reps 1+2; those plus hygiene rep 1), read off the same audit
   through the union's `members` map, flagged as chosen after the fact;
4. agreement as a label: hit rate by `passes_agreeing` (1..4) over judge-paired union findings,
   with and without 33149, and the within-PR AUC, with no cut proposed;
5. the judge's self-agreement on identical text: a union finding with one member is the source
   finding verbatim, so its verdict against the same obligation in the source audit is the
   judge's own repeatability.

Run from the repository root:
`ape/bin/python results/pr_review_v5/probes/ensemble-union-2026-10-02/reading.py`.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RUNS = ROOT / "results/pr_review_v5/runs"
AUDITS = ROOT / "results/pr_review_v5/audits"

UNION = "union_dev_opus_4pass_v1"
UNION_AUDIT = "union-dev-opus-4pass-v1"
#: label -> (generation run, judge audit), in the todo's order.
PASSES = {
    "H55r1": ("probe_dev_opus55_contract2_claude_sub_rep1", "probe-dev-opus55-contract2-claude-sub-rep1"),
    "H55r2": ("probe_dev_opus55_contract2_claude_sub_rep2", "probe-dev-opus55-contract2-claude-sub-rep2"),
    "M5": ("probe_dev_opus5_contract2_claude_sub_rep1", "probe-dev-opus5-contract2-claude-sub-rep1"),
    "Hyg1": ("probe_dev_opus55_contract2_hygiene_claude_sub_rep1", "probe-dev-opus55-contract2-hygiene-claude-sub-rep1"),
}
SUBSETS = {
    "K=2, H-claude reps 1+2": ["H55r1", "H55r2"],
    "K=3, + hygiene rep 1": ["H55r1", "H55r2", "Hyg1"],
    "K=4, all four": ["H55r1", "H55r2", "M5", "Hyg1"],
}
CONTROLS = [33304, 33315]
RULE_RECALL = 10
RULE_EMISSION = 2.0


def rows(path: Path) -> list:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]


def hits_of(report: dict) -> set:
    return {o["obligation_id"] for o in report["per_obligation"] if o["issue_status"] == "hit"}


def status_of(report: dict) -> dict:
    return {o["obligation_id"]: ("HIT" if o["issue_status"] == "hit" else "loc" if o["location_hit"] else ".")
            for o in report["per_obligation"]}


def within_pr_auc(scored: list) -> tuple:
    """`scored` is [(pr, score, hit)]. Pooled over PRs holding both a hit and a non-hit; a tie
    counts one half, as `centrality_probe.within_pr_auc` and the survey's table did."""
    by_pr = defaultdict(list)
    for pr, score, hit in scored:
        by_pr[pr].append((score, hit))
    wins = total = 0.0
    prs = 0
    for items in by_pr.values():
        on = [s for s, h in items if h]
        off = [s for s, h in items if not h]
        if not on or not off:
            continue
        prs += 1
        for a in on:
            for b in off:
                total += 1
                wins += 1 if a > b else 0.5 if a == b else 0
    return (round(wins / total, 3) if total else None), prs, int(total)


def main() -> int:
    union_dir, audit_dir = RUNS / UNION, AUDITS / UNION_AUDIT
    if not (audit_dir / "semantic_report.json").is_file():
        print(f"{audit_dir} holds no semantic_report.json: judge {UNION} first.")
        return 1
    union_report = json.loads((union_dir / "union_report.json").read_text(encoding="utf-8"))
    findings = {f["finding_id"]: f for f in rows(union_dir / "findings.jsonl")}
    report = json.loads((audit_dir / "semantic_report.json").read_text(encoding="utf-8"))
    matches = rows(audit_dir / "semantic_matches.jsonl")
    pairs = [p for p in rows(audit_dir / "semantic_pairs.jsonl") if p.get("role", "observed") == "observed"]
    pass_reports = {label: json.loads((AUDITS / audit / "semantic_report.json").read_text(encoding="utf-8"))
                    for label, (_run, audit) in PASSES.items()}
    run_label = {run: label for label, (run, _audit) in PASSES.items()}

    hit_obligations = defaultdict(set)       # union finding -> obligations it hit
    verdict = {}                              # (finding, obligation) -> issue_match
    for m in matches:
        verdict[(m["candidate_id"], m["obligation_id"])] = bool(m["issue_match"])
        if m["issue_match"]:
            hit_obligations[m["candidate_id"]].add(m["obligation_id"])
    paired = {p["candidate_id"] for p in pairs}
    n_obl = report["counts"]["obligations"]
    union_hits = hits_of(report)
    emission = report["silent_pr_emission"]

    # ---- 1. the rule -------------------------------------------------------------------------
    print(f"## 1. The rule, on `{UNION}` (judge {report['judge_version']}, {report['judge_model']}, identity `{report['judge_identity'][:12]}`)\n")
    print(f"- judged issue recall: **{len(union_hits)} of {n_obl}** ({report['issue_recall']:.3f}); rule: at least {RULE_RECALL} -> "
          f"{'MET' if len(union_hits) >= RULE_RECALL else 'NOT MET'}")
    print(f"- control emission: **{emission['candidates']} findings over {len(CONTROLS)} control PRs, {emission['candidates_per_control_pr']} per PR** "
          f"(union_report: {union_report['control_findings']}); rule: at most {RULE_EMISSION} -> "
          f"{'MET' if float(emission['candidates_per_control_pr']) <= RULE_EMISSION else 'NOT MET'}")
    lever = len(union_hits) >= RULE_RECALL and float(emission['candidates_per_control_pr']) <= RULE_EMISSION
    print(f"- **the union of the four is {'a lever' if lever else 'NOT a lever, as built'}** under the pre-stated rule; "
          f"{'the K=2 and K=3 subsets are read below, chosen after the fact' if float(emission['candidates_per_control_pr']) > RULE_EMISSION else 'no subset reading is needed'}")
    c = report["counts"]
    print(f"- volume: {c['candidates']} findings, {c['paired_candidates']} judge-paired at {c['observed_pairs']} anchored pairs; "
          f"coverage complete: {report['coverage']['complete']}; reachable recall {report['issue_recall_reachable']:.3f}; "
          f"resolution recall {report['resolution_recall']:.3f}; gold alignment {report['gold_alignment_rate']:.3f}")

    # ---- 2. the spine ------------------------------------------------------------------------
    statuses = {label: status_of(rep) for label, rep in pass_reports.items()}
    statuses["union"] = status_of(report)
    obligations = sorted(statuses["union"])
    pass_hits = {label: hits_of(rep) for label, rep in pass_reports.items()}
    spine_union = set().union(*pass_hits.values())
    print("\n## 2. The spine: each pass, the union of their audits, the union run's own audit\n")
    print("| obligation | PR | " + " | ".join(PASSES) + " | passes' union | union run |")
    print("|---|---|" + "---|" * (len(PASSES) + 2))
    pr_of = {p["obligation_id"]: p["pr_number"] for p in pairs}
    for ob in obligations:
        print(f"| `{ob[11:19]}` | {pr_of.get(ob, '')} | " + " | ".join(statuses[k].get(ob, "?") for k in PASSES)
              + f" | {'HIT' if ob in spine_union else '.'} | {statuses['union'][ob]} |")
    lost = sorted(spine_union - union_hits)
    gained = sorted(union_hits - spine_union)
    print(f"\n- hit per pass: {', '.join(str(len(pass_hits[k])) for k in PASSES)}; passes' union {len(spine_union)}; "
          f"stable (all four) {len(set.intersection(*pass_hits.values()))}; union run judged {len(union_hits)}")
    print(f"- moved: hit by some pass, missed in the union run's audit: {len(lost)} -- " + ", ".join(f"`{o[11:19]}`" for o in lost))
    print(f"- moved: hit in the union run's audit, by no pass: {len(gained)} -- " + (", ".join(f"`{o[11:19]}`" for o in gained) or "none"))

    # ---- 3. the subsets ----------------------------------------------------------------------
    members = union_report["members"]
    runs_of = {fid: {run_label[m["run"]] for m in mem} for fid, mem in members.items()}
    print("\n## 3. The K=2 and K=3 subsets, read off the union audit through `members` (chosen after the fact)\n")
    print("| subset | findings | judge-paired | hit obligations (union audit) | hit obligations (passes' own audits) | control findings (33304, 33315) | per control PR | rule |")
    print("|---|---|---|---|---|---|---|---|")
    for name, labels in SUBSETS.items():
        chosen = {fid for fid, labs in runs_of.items() if labs & set(labels)}
        hits = set().union(*(hit_obligations[fid] for fid in chosen)) if chosen else set()
        own = set().union(*(pass_hits[l] for l in labels))
        control = Counter(findings[fid]["pr_number"] for fid in chosen if findings[fid]["pr_number"] in CONTROLS)
        per_pr = sum(control.values()) / len(CONTROLS)
        met = len(hits) >= RULE_RECALL and per_pr <= RULE_EMISSION
        print(f"| {name} | {len(chosen)} | {len(chosen & paired)} | **{len(hits)}** of {n_obl} | {len(own)} | "
              f"{control[33304]}, {control[33315]} | {per_pr:.1f} | {'lever' if met else 'not, as built'} |")

    # ---- 4. agreement as a label ------------------------------------------------------------
    print("\n## 4. Agreement as a label: hit rate by `passes_agreeing` over judge-paired union findings (no cut)\n")
    scored = [(findings[fid]["pr_number"], findings[fid]["passes_agreeing"], bool(hit_obligations[fid])) for fid in paired]
    for title, keep in (("all scored PRs", lambda pr: True), ("without 33149", lambda pr: pr != 33149)):
        sub = [row for row in scored if keep(row[0])]
        print(f"**{title}** ({len(sub)} paired findings)\n")
        print("| k (passes agreeing on site and kind) | paired findings | hit | rate | distinct obligations hit |\n|---|---|---|---|---|")
        for k in (1, 2, 3, 4):
            bucket = [fid for fid in paired if findings[fid]["passes_agreeing"] == k and keep(findings[fid]["pr_number"])]
            hit = [fid for fid in bucket if hit_obligations[fid]]
            obls = set().union(*(hit_obligations[fid] for fid in hit)) if hit else set()
            rate = f"{len(hit) / len(bucket):.2f}" if bucket else "-"
            print(f"| {k} | {len(bucket)} | {len(hit)} | {rate} | {len(obls)} |")
        auc, prs, n_pairs = within_pr_auc(sub)
        print(f"\n- within-PR AUC of k: **{auc}** over {prs} PRs holding both a hit and a non-hit ({n_pairs} ordered pairs)\n")
    by_pr = defaultdict(lambda: [0, 0, Counter()])
    for pr, k, hit in scored:
        by_pr[pr][0] += 1
        by_pr[pr][1] += hit
        by_pr[pr][2][k] += 1
    print("| PR | paired findings | hit | k distribution of paired findings | enters the AUC |\n|---|---|---|---|---|")
    for pr in sorted(by_pr):
        n, h, ks = by_pr[pr]
        print(f"| {pr} | {n} | {h} | {dict(sorted(ks.items()))} | {'yes' if 0 < h < n else 'no'} |")
    print()
    all_k = Counter(f["passes_agreeing"] for f in findings.values())
    print(f"- over every union finding, paired or not: k distribution {dict(sorted(all_k.items()))}; "
          f"identical-ask folds {union_report['collapsed_identical_asks']} of {union_report['inputs']}")

    # ---- 5. judge self-agreement on identical text ------------------------------------------
    print("\n## 5. The judge against itself: one-member union findings are their source finding verbatim\n")
    source_verdict = {}
    for label, (_run, audit) in PASSES.items():
        for m in rows(AUDITS / audit / "semantic_matches.jsonl"):
            source_verdict[(label, m["candidate_id"], m["obligation_id"])] = bool(m["issue_match"])
    agree = Counter()
    flips = []
    for fid, mem in members.items():
        if len(mem) != 1:
            continue
        label, source_id = run_label[mem[0]["run"]], mem[0]["finding_id"]
        for (cand, ob), now in verdict.items():
            if cand != fid:
                continue
            before = source_verdict.get((label, source_id, ob))
            if before is None:
                agree["pair absent in the source audit"] += 1
                continue
            if before == now:
                agree["same verdict"] += 1
            else:
                agree["hit -> miss" if before else "miss -> hit"] += 1
                flips.append((label, ob[11:19], "hit -> miss" if before else "miss -> hit"))
    same, total = agree["same verdict"], sum(v for k, v in agree.items() if k != "pair absent in the source audit")
    print(f"- same (finding, obligation) pairs judged in both audits: {total}; same verdict {same} "
          f"({same / total:.2f}); hit -> miss {agree['hit -> miss']}, miss -> hit {agree['miss -> hit']}; "
          f"pairs the source audit did not hold {agree['pair absent in the source audit']}")
    for label, ob, kind in sorted(flips):
        print(f"  - {label} `{ob}`: {kind}")

    # ---- 5b. the control findings ------------------------------------------------------------
    print("\n## 5b. The 14 control-PR findings, as filed: the union's price, read per PR\n")
    print("| PR | k | passes (site and kind) | members | family / kind | asks |\n|---|---|---|---|---|---|")
    for fid, f in sorted(findings.items(), key=lambda kv: (kv[1]["pr_number"], -kv[1]["passes_agreeing"], kv[0])):
        if f["pr_number"] not in CONTROLS:
            continue
        mem = ", ".join(run_label[m["run"]] for m in members[fid])
        ask = f["requested_change"].replace("|", "/").replace("\n", " ")
        print(f"| {f['pr_number']} | {f['passes_agreeing']} | {', '.join(f['passes'])} | {mem} | {f['concern_family']} / {f['issue_kind']} | {ask[:110]}{'...' if len(ask) > 110 else ''} |")

    for name, labels in SUBSETS.items():
        chosen = {fid for fid, labs in runs_of.items() if labs & set(labels)}
        keys = {pr: {(findings[fid]["primary_change_id"], findings[fid]["issue_kind"])
                     for fid in chosen if findings[fid]["pr_number"] == pr} for pr in CONTROLS}
        n_find = {pr: sum(findings[fid]["pr_number"] == pr for fid in chosen) for pr in CONTROLS}
        print(f"- {name}: control findings {n_find[33304]}, {n_find[33315]} ({sum(n_find.values()) / 2:.1f} per PR) "
              f"are {len(keys[33304])}, {len(keys[33315])} distinct site-and-kind claims ({sum(len(v) for v in keys.values()) / 2:.1f} per PR)")

    # ---- 6. per PR ---------------------------------------------------------------------------
    print("\n## 6. Per PR\n")
    print("| PR | union findings | " + " | ".join(PASSES) + " | obligations | hit (union audit) |")
    print("|---|---|" + "---|" * (len(PASSES) + 2))
    obl_by_pr = Counter(pr_of[o] for o in obligations if o in pr_of)
    hit_by_pr = Counter(pr_of[o] for o in union_hits if o in pr_of)
    per_pr_per_run = union_report["per_pr_per_run"]
    for pr in sorted(int(p) for p in union_report["per_pr"]):
        counts = per_pr_per_run[str(pr)]
        tag = " (control)" if pr in CONTROLS else ""
        print(f"| {pr}{tag} | {union_report['per_pr'][str(pr)]} | " + " | ".join(str(counts[PASSES[k][0]]) for k in PASSES)
              + f" | {obl_by_pr.get(pr, '')} | {hit_by_pr.get(pr, '') if pr in obl_by_pr else ''} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
