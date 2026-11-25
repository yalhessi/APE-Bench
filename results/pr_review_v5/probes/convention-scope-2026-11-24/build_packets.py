"""Reconstruct the six whole-PR packets from local submission-time inputs.

Run from the repository root with ape/bin/python build_packets.py OUTPUT.
The sibling OUTPUT.manifest.json identifies cases and arms for the organizer.
"""

import argparse
import difflib
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from src.datasets.pull_requests.definitions import clean_description, clean_title
from src.mathlib_review.diffs import assemble_unified_diff
from src.mathlib_review.io import jsonl_rows, pretty_json_bytes, sha256_bytes, write_once
from src.mathlib_review.release.change_graph import apply_file_patch, parse_unified_diff

STORE = ROOT / "data/pull_requests"
# Pinned first-review comparison hashes, recorded before packet assembly.
HEADS = {
    42184: ("c5474cb4a68a515228b49225b38a2507264f91f7",
            "75ebc25bc5f5ec39926f4c600e054def8c1688e54825e6a9a9f4113ecbd2e18d"),
    29857: ("43fd03f7e657c6395612509dfa2d3372275bb9ef",
            "778f7bb87c7d0f8ab73f2dbe31d11fa4b9d961139edf4f54351d1e7453ddf722"),
}
# The controlled addition from replay_api_clients.py. Preserve the submitted caller.
COMPANION = """lemma HasProd.nonneg [CommMonoidWithZero α] [TopologicalSpace α] [Preorder α] [ZeroLEOneClass α]
    [PosMulMono α] [ClosedIciTopology α] [L.NeBot] {f : ι → α} {a : α}
    (hf : ∀ i, 0 ≤ f i) (ha : HasProd f a L) : 0 ≤ a :=
  le_hasProd_of_le_prod ha fun _ ↦ prod_nonneg fun i _ ↦ hf i

"""
# These identifiers are the only case labels the packet-session task receives.
PACKETS = {
    "p04": (29857, "submitted", "comparison"),
    "p19": (42184, "companion", "ordinary"),
    "p37": (42184, "submitted", "ordinary"),
    "p52": (42184, "companion", "comparison"),
    "p68": (29857, "submitted", "ordinary"),
    "p83": (42184, "submitted", "comparison"),
}
ORDINARY = "Use your ordinary judgment when deciding what to request on this pull request.\n"


def contents(number):
    head, patch_hash = HEADS[number]
    folder = STORE / "pr" / str(number)
    compare = json.loads((folder / "compares" / f"{head}.json").read_text())
    diff = assemble_unified_diff(compare)
    if sha256_bytes(diff.encode()) != patch_hash:
        raise ValueError(f"First-review patch changed for PR {number}")
    file, = parse_unified_diff(diff)
    base_sha = compare["merge_base_sha"]
    base = (STORE / "base_files" / base_sha / file.path).read_text()
    source = apply_file_patch(base, file)
    pr = json.loads((folder / "pr.json").read_text())
    edits = json.loads((folder / "fetch.json").read_text())["endpoints"]["body_edits"]
    if not edits["present"] or edits["rows"] or (folder / "body_edits.jsonl").read_bytes():
        raise ValueError(f"Cannot verify the submission-time description for PR {number}")
    # Each submitted commit has the exact original title, including capitalization.
    commit, = (r for r in jsonl_rows(folder / "commits.jsonl")
               if r["sha"] == head)
    title = commit["commit"]["message"].splitlines()[0]
    if title != clean_title(pr["title"]):
        raise ValueError(f"Submitted title and cleaned PR title disagree on {number}")
    pr_text = f"# {title}\n\n{clean_description(pr['body'])}\n"
    return file.path, base, source, diff, pr_text, base_sha


def with_companion(path, base, source):
    marker = "theorem tprod_nonneg [CommMonoidWithZero α]"
    if source.count(marker) != 1 or "lemma HasProd.nonneg " in source:
        raise ValueError("The original fixture no longer has the expected public API")
    revised = source.replace(marker, COMPANION + marker)
    patch = f"diff --git a/{path} b/{path}\n" + "".join(difflib.unified_diff(
        base.splitlines(keepends=True), revised.splitlines(keepends=True), f"a/{path}", f"b/{path}"))
    file, = parse_unified_diff(patch)
    if apply_file_patch(base, file) != revised:
        raise ValueError("The controlled patch does not reproduce its complete changed file")
    return revised, patch


def build(output, intervention):
    cases = {n: contents(n) for n in HEADS}
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(f"Choose a fresh packet root: {output}")
    manifest = {}
    with TemporaryDirectory(dir=output.parent) as temp:
        staging = Path(temp) / "packets"
        for label, (number, variant, arm) in PACKETS.items():
            path, base, source, diff, pr_text, base_sha = cases[number]
            if variant == "companion":
                source, diff = with_companion(path, base, source)
            files = {"pr.md": pr_text, "changes.diff": diff, path: source,
                     "operation.md": intervention if arm == "comparison" else ORDINARY}
            for filename, content in files.items():
                dest = staging / label / filename
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(content.encode())
            manifest[label] = {
                "pr": number, "variant": variant, "arm": arm, "base": base_sha,
                "historical_head": HEADS[number][0],
                "sha256": {name: sha256_bytes(content.encode()) for name, content in files.items()},
            }
        write_once(output.with_name(output.name + ".manifest.json"), pretty_json_bytes(manifest))
        staging.rename(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--intervention", type=Path, default=Path(__file__).with_name("intervention.md"))
    args = parser.parse_args()
    build(args.output, args.intervention.read_text())
