"""The solo task's context files for the conventions ceiling probe (`probes.model_context`).

`base` is each PR's pass-0 model, on every PR of the set. A briefed level (`exact`, `common`, `all`)
adds the PR's conventions section after the model, on the PRs `briefs_<level>.json` names: a map
`{"prs": {"<pr>": ["P012", ...]}}` of reader A's codebook ids. Sentences are printed in codebook
order whatever order the brief lists them in.

`prec` (stage D) is `exact` with up to two maintainers' asks beneath each sentence and the section
closed by `probes.CONVENTIONS_PRECEDENCE`. The asks are the ones stage G's rule writers saw first
(`build_rule_writer_folders.py`): reader A's census asks filed under the entry, on val1000 and
outside_years PRs, in the order stage G's seed gives them. It needs the census bodies
(`conventions-census-v1/provenance/materialise_bodies.py`'s output) and writes `examples_prec.json`,
the asks by id. Bodies are never committed, so its two context files are not either; their digests
are in `context_prec.sha256`, which the stage's gate checks before any run.

usage (repo root, PYTHONPATH=$PWD/src): ape/bin/python <this file> <base|exact|common|all|prec> [bodies.json]
"""
import glob
import hashlib
import json
import sys
from pathlib import Path

from src.mathlib_review.analysis import probes

HERE = Path(__file__).parent
CENSUS = Path("results/pr_review_v5/adjudications/conventions-census-v1")
CODEBOOK = CENSUS / "reader_A/codebook.json"
SETS = {"val": "configs/probe_sets/val_small12.yaml", "post": "configs/probe_sets/postcutoff_2026_07_08_v1.yaml"}
PER_ENTRY = 2


def census_examples(bodies: Path, entries: set, probe_prs: set) -> dict:
    """Up to PER_ENTRY census asks a entry, as stage G's writers were shown them (body[:900], the
    hunk's last 800 characters), and the record of which they are."""

    seed = json.loads((HERE / "stage_g_entries.json").read_text())["seed"]
    key = lambda *parts: hashlib.sha256("\0".join((seed,) + parts).encode()).hexdigest()
    body = {r["cid"]: r for r in json.loads(bodies.read_text())["rows"] if r["set"] in ("val1000", "outside_years")}
    filed = {}
    for path in sorted(glob.glob(str(CENSUS / "reader_A/labels_*.jsonl"))):
        for row in map(json.loads, open(path, encoding="utf-8")):
            if row["principle_id"] in entries and row["cid"] in body:
                filed.setdefault(row["principle_id"], []).append(row["cid"])
    chosen = {i: sorted(filed.get(i, []), key=lambda c: key("ask", i, c))[:PER_ENTRY] for i in sorted(entries)}
    leaked = {body[c]["pr"] for cids in chosen.values() for c in cids} & probe_prs
    assert not leaked, f"an example sits on a probe PR: {sorted(leaked)}"
    record = {i: [{"cid": c, "pr": body[c]["pr"], "event_id": body[c]["event_id"], "path": body[c]["path"]}
                  for c in cids] for i, cids in chosen.items()}
    (HERE / "examples_prec.json").write_text(json.dumps(
        {"seed": seed, "per_entry": PER_ENTRY, "sets": ["val1000", "outside_years"], "entries": record}, indent=1) + "\n")
    return {i: [{"path": body[c]["path"], "comment": body[c]["body"][:900], "code": (body[c]["diff_hunk"] or "")[-800:]}
                for c in cids] for i, cids in chosen.items()}


level = sys.argv[1]
specs = {tag: probes.load_probe_set(Path(path)) for tag, path in SETS.items()}
briefs, closing = None, ""
if level != "base":
    source = HERE / f"briefs_{'exact' if level == 'prec' else level}.json"
    examples = None
    if level == "prec":
        entries = {i for ids in json.loads(source.read_text())["prs"].values() for i in ids}
        examples = census_examples(Path(sys.argv[2]), entries, {pr for s in specs.values() for pr in s.pr_numbers})
        closing = probes.CONVENTIONS_PRECEDENCE
    briefs = probes.load_conventions(source, CODEBOOK, examples)
digests = []
for tag, spec in specs.items():
    prs = [pr for pr in spec.pr_numbers if briefs is None or pr in briefs]
    conventions = None if briefs is None else {pr: briefs[pr] for pr in prs}
    out = HERE / f"context_{tag}_{level}.jsonl"
    out.write_text(probes.model_context(spec, prs, conventions, closing))
    digests.append(f"{hashlib.sha256(out.read_bytes()).hexdigest()}  {out.resolve().relative_to(Path.cwd().resolve())}\n")
    held = "" if conventions is None else f", {sum(map(len, conventions.values()))} sentences"
    print(f"{out}: {len(prs)} PRs{held}")
if level == "prec":
    (HERE / "context_prec.sha256").write_text("".join(digests))
    print("".join(digests), end="")
