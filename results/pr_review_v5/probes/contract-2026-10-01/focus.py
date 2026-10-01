"""Is gpt proof-focused where Claude reviews broadly? Measured on the dev held-out 12, one way for all.

A. findings per concern family: share and count, multi-label, from one keyword classifier applied to
   every reviewer's claim and fix text, and to the gold asks;
B. gold asks hit, by the ask's `concern_labels`;
C. tool calls per session, parsed from the conversation (`tool_use` blocks in the last, cumulative
   turn file) for gpt and from `calls.jsonl` (the `ptool` log) for Claude;
D. share of PRs whose notes mention each family;
E. share of the PR model's changed declarations (`## Objects`, commands excluded) the notes name,
   in full or by leaf name, per PR and median.

The classifier is coarse and shared, so read A for differences between reviewers, not as labels.
Run from the repo root: `ape/bin/python results/pr_review_v5/probes/contract-2026-10-01/focus.py`.
"""

import asyncio
import collections
import glob
import json
import re
import statistics
import sys
from pathlib import Path

sys.path[:0] = [".", "src"]

HO = [33117, 33145, 33149, 33285, 33294, 33304, 33305, 33315, 33321, 33337, 33362, 33421]
FAM = {
    "naming": r"\brenam|\bname[sd]?\b|naming|prefix|suffix|dot.notation",
    "docs": r"docstring|doc comment|doc-string|module doc|documentation|typo|grammar|wording",
    "proof": r"\bproof|golf|\bsimp\b|simpa|tactic|grind|omega|one-liner|term.mode|positivity|gcongr"
             r"|linarith|norm_num|\bexact\b|\brfl\b|shorten",
    "generality": r"generali[sz]|weaken|more general|typeclass|hypothes|assumption",
    "duplication": r"duplicat|already (exists|in mathlib|available)|existing (lemma|declaration|theorem)"
                   r"|reuse|redundant",
    "api design": r"refactor|restat|signature|swap the sides|reorder|statement|derive|dual|instead of a new",
    "placement": r"\bmove\b|namespace|\bsection\b|placement|\bsplit\b|another file|this file",
    "style/attrs": r"style|format|line length|indent|binder|\bvariable\b|deprecat|attribute|@\[|\bsimp lemma"
                   r"|fun_prop|tag",
    "imports/build": r"\bimport|axiom|sorry|build|compile",
}
RUNS = {  # label -> (run, judge audit, Claude packet reviewer or None)
    "Claude X1": ("probe_dev_claude_X1", "probe-dev-claude-X1", "X1"),
    "Claude X2": ("probe_dev_claude_X2", "probe-dev-claude-X2", "X2"),
    "Claude swap": ("probe_dev_claude_swap_S1", "probe-dev-claude-swap-S1", "swap:S1"),
    "gpt Grc1": ("probe_dev_gpt52_Grc_rep1", "probe-dev-gpt52-Grc-rep1", None),
    "gpt contract": ("probe_dev_gpt52_Grc_contract_rep1", "probe-dev-gpt52-Grc-contract-rep1", None),
    "gpt contract2": ("probe_dev_gpt52_Grc_contract2_rep1", "probe-dev-gpt52-Grc-contract2-rep1", None),
    "gpt55 contract2": ("probe_dev_gpt55_Grc_contract2_rep1", "probe-dev-gpt55-Grc-contract2-rep1", None),
    "gpt-5.5 carried": ("probe_dev_gpt55_Grc_rep1", "probe-dev-gpt55-Grc-rep1", None),
    "gpt off": ("probe_dev_gpt52_G_rep1", "probe-dev-gpt52-G-rep1", None),
}
PACKET = "results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr{pr}/{who}"
#: The swap's packets: Claude under gpt's contract-v2 messages; its notes are in `submission.json`.
SWAP_PACKET = "results/pr_review_v5/probes/contract-2026-10-01/swap/pr{pr}/{who}"
TOOLS = ["file_read", "content_search", "file_search", "declaration_search", "naming_norm",
         "precedent_search", "zulip_search", "lean_verify_edit", "lean_verify"]


def families(text):
    return {name for name, pattern in FAM.items() if re.search(pattern, text.lower())}


def gpt_sessions(run):
    """pr -> (tool-call Counter, review_notes) for every successful held-out task."""

    from ape.orchestration.persistence import TaskStorage

    async def load():
        out = {}
        for task in sorted(p for p in (Path(".ape/runs") / run / "tasks").iterdir() if p.is_dir()):
            result = await TaskStorage(task, task.name).load_task_result()
            if not (result and result.get("success") and result["pr_number"] in HO):
                continue
            turns = [c for c in sorted(glob.glob(f"{task}/samples/0/attempts/*/conversations/*.jsonl"))
                     if not c.endswith("_raw.jsonl")]
            calls = collections.Counter()
            for node in (json.loads(l) for l in open(turns[-1]) if l.strip()):
                content = (node.get("message") or {}).get("content")
                if node.get("type") == "assistant" and isinstance(content, list):
                    calls.update(b.get("name") for b in content
                                 if isinstance(b, dict) and b.get("type") == "tool_use")
            out[result["pr_number"]] = (calls, result.get("review_notes", ""))
        return out

    return asyncio.run(load())


def claude_sessions(who):
    out = {}
    swap = who.startswith("swap:")
    for pr in HO:
        base = Path((SWAP_PACKET if swap else PACKET).format(pr=pr, who=who.split(":")[-1]))
        if (base / "calls.jsonl").is_file():
            calls = collections.Counter(json.loads(l).get("tool") for l in (base / "calls.jsonl").open()
                                        if l.strip())
            if swap:
                notes = json.loads((base / "submission.json").read_text()).get("notes", "")
            else:
                notes = (base / "notes.md").read_text() if (base / "notes.md").is_file() else ""
            out[pr] = (calls, notes)
    return out


def main():
    gold = []
    for line in open("inputs/pr_review_v4/releases/dev-medium-0.3.0/gold/judgments.jsonl"):
        judgment = json.loads(line)
        if judgment["pr_number"] in HO and ":round1:" in judgment["episode_id"]:
            gold += [(judgment, ob) for ob in judgment.get("obligations") or []]

    print("A. findings touching each family: share (count), multi-label")
    print(f"{'':16}" + "".join(f"{k[:11]:>13}" for k in FAM) + f"{'n':>5}")
    for label, (run, _audit, _who) in RUNS.items():
        if not Path(f"results/pr_review_v5/runs/{run}/findings.jsonl").is_file():
            print(f"{label:16} (no run yet)")
            continue
        rows = [json.loads(l) for l in open(f"results/pr_review_v5/runs/{run}/findings.jsonl") if l.strip()]
        rows = [r for r in rows if r["pr_number"] in HO]
        counts = collections.Counter(f for r in rows for f in families(
            " ".join(str(r.get(k) or "") for k in ("claim", "suggested_fix"))))
        print(f"{label:16}" + "".join(f"{counts[k] / len(rows):8.0%} ({counts[k]:2})" for k in FAM)
              + f"{len(rows):5}")
    counts = collections.Counter(f for j, ob in gold for f in families(
        (ob.get("claim") or "") + " " + json.dumps(j.get("action"))))
    print(f"{'gold asks':16}" + "".join(f"{counts[k] / len(gold):8.0%} ({counts[k]:2})" for k in FAM)
          + f"{len(gold):5}")

    print("\nB. gold asks hit, by the ask's concern label")
    label_of = {ob.get("obligation_id"): (j.get("concern_labels") or ["?"])[0] for j, ob in gold}
    names = sorted(set(label_of.values()))
    print(f"{'':16}" + "".join(f"{n[:10]:>11}" for n in names))
    print(f"{'gold':16}" + "".join(f"{list(label_of.values()).count(n):11}" for n in names))
    for label, (_run, audit, _who) in RUNS.items():
        if not Path(f"results/pr_review_v5/audits/{audit}/semantic_matches.jsonl").is_file():
            print(f"{label:16} (not judged yet)")
            continue
        hit = {json.loads(l)["obligation_id"]
               for l in open(f"results/pr_review_v5/audits/{audit}/semantic_matches.jsonl")
               if json.loads(l).get("issue_match")}
        print(f"{label:16}" + "".join(f"{sum(label_of.get(o) == n for o in hit):11}" for n in names))

    sessions = {label: (claude_sessions(who) if who else gpt_sessions(run))
                for label, (run, _audit, who) in RUNS.items() if label in
                ("Claude X1", "Claude X2", "Claude swap", "gpt Grc1", "gpt contract", "gpt contract2",
                 "gpt55 contract2")
                and (who or (Path(".ape/runs") / run / "tasks").is_dir())}
    print("\nC. tool calls per session, median")
    print(f"{'':14}" + "".join(f"{t[:10]:>11}" for t in TOOLS) + f"{'all':>6}")
    for label, prs in sessions.items():
        median = lambda t: statistics.median(c.get(t, 0) for c, _ in prs.values())  # noqa: E731
        total = statistics.median(sum(v for k, v in c.items() if k not in ("submit_findings", "describe"))
                                  for c, _ in prs.values())
        print(f"{label:14}" + "".join(f"{median(t):11.1f}" for t in TOOLS) + f"{total:6.0f}")

    print("\nD. share of PRs whose notes mention each family")
    print(f"{'':14}" + "".join(f"{k[:11]:>13}" for k in FAM))
    for label, prs in sessions.items():
        notes = [n for _, n in prs.values() if n]
        if notes:
            print(f"{label:14}" + "".join(
                f"{sum(bool(re.search(p, n.lower())) for n in notes) / len(notes):13.0%}"
                for p in FAM.values()) + f"   (n={len(notes)})")
        else:
            print(f"{label:14} (no notes asked for)")

    print("\nE. the PR model's changed declarations the notes name")
    labels = [label for label, prs in sessions.items() if any(n for _, n in prs.values())]
    print(f"{'PR':6} {'decls':>5}" + "".join(f"{label[-10:]:>13}" for label in labels))
    rates = collections.defaultdict(list)
    for pr in HO:
        declarations = model_declarations(pr)
        if not declarations:
            continue
        row = []
        for label in labels:
            notes = sessions[label].get(pr, (None, ""))[1]
            rate = sum(notes_name(d, notes) for d in declarations) / len(declarations)
            rates[label].append(rate)
            row.append(rate)
        print(f"{pr:6} {len(declarations):5}" + "".join(f"{r:13.0%}" for r in row))
    print(f"{'median':12}" + "".join(f"{statistics.median(rates[label]):13.0%}" for label in labels))


def model_declarations(pr):
    """The changed declarations the PR model lists, commands excluded."""

    model = Path(PACKET.format(pr=pr, who="X1")) / "model.md"
    section = model.read_text().split("## Objects", 1)[1].split("\n## ", 1)[0]
    return [name for name, kind in re.findall(r"^### `([^`]+)` \(([^,]+), ", section, re.M)
            if kind != "command"]


def notes_name(declaration, notes):
    """Whether the notes name the declaration, in full or by a leaf name of four or more characters."""

    leaf = declaration.rsplit(".", 1)[-1]
    return declaration in notes or (len(leaf) > 3 and re.search(
        r"(?<![\w.'])" + re.escape(leaf) + r"(?![\w'])", notes) is not None)


if __name__ == "__main__":
    main()
