"""Reader packets for Phase 1: for every residual ask (reached by nobody, or only by Claude), the
reviewers' own records, so two blind readers can label the mechanism of each miss.

Usage, from the repo root:
    python results/pr_review_v5/probes/phase1-residual-mechanisms-2026-09-30/build_packets.py OUT_DIR

Writes OUT_DIR/<split>/m{1,2}/ for splits post, val, dev_a, dev_b (dev is halved by PR so no reader
carries more than about 40 pairs). Pairs: for a "nobody" ask, X1, X2 and Grc1; for a "claude_only"
ask, Grc1 only. Reader inputs never include the matchers' notes.
"""
import glob
import importlib.util
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, ".")
from src.mathlib_review.analysis import probes  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "coh", "results/pr_review_v5/probes/carryover-coherence-2026-09-30/coherence.py")
coh = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(coh)

HERE = Path(__file__).parent
POPULATION = Path("results/pr_review_v5/probes/phase0-carried-baseline-2026-09-30/phase1_population.json")
FAMILIES = json.load(open("results/pr_review_v5/adjudications/arm-coverage-val-2025-06-2026-03-v1/families.json"))["families"]
SETS = {"post": ("configs/probe_sets/postcutoff_2026_07_08_v1.yaml", "probe_postcutoff_gpt52_Grc_rep1"),
        "val": ("configs/probe_sets/val_small12.yaml", "probe_val_small12_gpt52_Grc_rep1"),
        "dev": ("configs/probe_sets/dev_medium_0_3_0.yaml", "probe_dev_gpt52_Grc_rep1")}
CLASSES = ("nobody", "claude_only")


def short(v, n):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + f"...(+{len(s) - n} chars)"


def render_transcript(task):
    """Every tool call with a truncated result, in order, then the submission in full."""
    rows = [json.loads(l) for l in open(coh.last_conversation(task))]
    results = {}
    for r in rows:
        for b in (r.get("message") or {}).get("content") or []:
            if b.get("type") == "tool_result":
                results[b.get("tool_use_id")] = b.get("result_content") or ""
    out, turn = [], 0
    for r in rows:
        if r["type"] != "assistant":
            continue
        turn += 1
        for b in (r.get("message") or {}).get("content") or []:
            if b.get("type") != "tool_use":
                continue
            a = b.get("input") or {}
            if b["name"] == "submit_findings":
                out.append(f"\n[turn {turn}] SUBMIT merge_ready_as_is={a.get('merge_ready_as_is')} confidence={a.get('confidence')}\n  message: {a.get('message')}")
                for i, f in enumerate(a.get("findings") or []):
                    out.append(f"  finding {i}: {json.dumps(f, ensure_ascii=False)}")
                continue
            out.append(f"[turn {turn}] {b['name']} {short(a, 700 if b['name'] == 'lean_verify_edit' else 350)}\n"
                       f"      -> {short(results.get(b['id'], ''), 500)}")
    return "\n".join(out)


def build(out_dir: Path):
    pop = json.load(open(POPULATION))["sets"]
    askwhy = {}
    p = HERE / "ask_answers.json"
    if p.exists():
        for row in json.load(open(p)):
            askwhy[(row["set"], row["pr"])] = row["answer"]
    splits = {}
    for set_name, (set_cfg, run) in SETS.items():
        spec = probes.load_probe_set(Path(set_cfg))
        rows = {a: r for a, r in pop[set_name]["rows"].items() if r["class"] in CLASSES}
        prs = sorted({r["pr"] for r in rows.values()})
        halves = [prs] if set_name != "dev" else [prs[: len(prs) // 2], prs[len(prs) // 2:]]
        for i, half in enumerate(halves):
            split = set_name if len(halves) == 1 else f"dev_{'ab'[i]}"
            base = out_dir / split / "src"
            base.mkdir(parents=True, exist_ok=True)
            pairs = []
            for pr in half:
                d = base / f"pr{pr}"; d.mkdir(exist_ok=True)
                pr_asks = {a: r for a, r in rows.items() if r["pr"] == pr}
                json.dump([{"ask_id": a, "text": r["text"], "family": r["family"], "family_definition": FAMILIES.get(r["family"]),
                            "class": r["class"], "reached_by": r["reached_by_both_matchers"]} for a, r in sorted(pr_asks.items())],
                          open(d / "asks.json", "w"), indent=1, ensure_ascii=False)
                # the PR as the reviewers saw it, from a Claude packet (pr.md, diff.patch)
                x1 = spec.session_dir(pr, "X1"); packet = x1.parent
                for name in ("pr.md", "diff.patch"):
                    src = packet / name
                    if src.exists():
                        shutil.copy(src, d / name)
                for sess in ("X1", "X2"):
                    sd = spec.session_dir(pr, sess); (d / sess).mkdir(exist_ok=True)
                    for name in ("findings.json", "notes.md", "calls.jsonl"):
                        if (sd / name).exists():
                            shutil.copy(sd / name, d / sess / name)
                task = next(t for t in glob.glob(f".ape/runs/{run}/tasks/*") if coh.session(t)["pr"] == pr)
                (d / "Grc1").mkdir(exist_ok=True)
                (d / "Grc1" / "transcript.txt").write_text(render_transcript(task))
                if (set_name, pr) in askwhy:
                    (d / "Grc1" / "askwhy.txt").write_text(
                        "The reviewer's own account, asked after its review had been submitted, with its reasoning "
                        "replayed. A self-report: weigh it against transcript.txt.\n\n" + askwhy[(set_name, pr)])
                for a, r in sorted(pr_asks.items()):
                    for rev in (("X1", "X2", "Grc1") if r["class"] == "nobody" else ("Grc1",)):
                        pairs.append({"ask_id": a, "pr": pr, "reviewer": rev})
            json.dump(pairs, open(base / "pairs.json", "w"), indent=1)
            shutil.copy(HERE / "reader_rubric.md", base / "reader_rubric.md")
            for m in ("m1", "m2"):
                dst = out_dir / split / m
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(base, dst); (dst / "tmp").mkdir(exist_ok=True)
            splits[split] = {"prs": half, "pairs": len(pairs), "asks": sum(1 for r in rows.values() if r["pr"] in half)}
    json.dump(splits, open(out_dir / "splits.json", "w"), indent=1)
    return splits


if __name__ == "__main__":
    print(json.dumps(build(Path(sys.argv[1])), indent=1))
