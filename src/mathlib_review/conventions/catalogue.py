"""Scan a Mathlib snapshot for the conventions it states about itself.

**Why a catalogue exists at all.** Six convention-discovery mechanisms were proposed and rejected
in one session (`docs/dead-ends.md`: "Surface proxies for convention discovery"). Each was fitted
to the same two or three conventions the author happened to know -- `grind`, dot notation,
`to_fun` -- because nothing said what a mechanism is *supposed* to reach. This module builds the
denominator: what conventions does Mathlib actually hold, so that "mechanism X reaches N of them"
becomes a measurement instead of an impression.

**What it extracts, and what that is worth.** Two sources state a convention *in the repository's
own words*, with a date and an author:

* **linters** -- an executable convention. `register_option linter.X` plus a docstring, and the
  enforcement status is the interesting part (below).
* **library notes** -- a design convention with rationale, cited from the code that follows it, so
  the citation count is an adoption weight. `reducible non-instances` is cited 364 times.

**Enforcement is not option existence.** This is the one thing the extraction must get right, and
the record already names it: read linter-set membership x `defValue` x the lakefile, *never*
whether an option is registered. A registered linter defaulting to `false` and belonging to no set
is a proposal, not a convention. The tiers this produces:

    standard     in `linter.mathlibStandardSet`, which the lakefile turns on globally -- binding
                 on every contributor
    lakefile     named directly in the lakefile's `leanOptions`
    weekly       in `linter.weeklyLintSet` -- run weekly, posted to Zulip, advisory
    nightly      in `linter.nightlyRegressionSet` -- a developer regression probe, NOT a
                 convention: it measures where `grind`/`lia` do not yet supersede an older tactic
    default_on   `defValue := true` but in no set
    available    registered, off, in no set -- a capability, not yet a convention
    disabled     commented out of a set with a stated reason; the reason is itself evidence

**The catalogue's known bias, stated here so it is not rediscovered.** Everything this module can
extract is a convention someone already encoded or wrote down. That is by construction the *easy*
end -- the end a syntactic method reaches and a chore PR can enforce in one pass. The conventions
that matter for review are disproportionately the ones with no linter and no note, and they have
to be added by reading code. Rows carry `source` so the two can never be silently pooled.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

from src.mathlib_review.io import sha256_bytes
from src.mathlib_review.paths import CONVENTIONS_TRACKED, assert_repo_root
from src.mathlib_review.retrieval.declaration_table import MATHLIB_CLONE

CATALOGUE_VERSION = "convention-catalogue/1"

#: A docstring may not span `-/`, or the match runs back to an unrelated earlier comment and
#: attributes it to this option. Measured: the naive form mislabelled `linter.style.emptyLine`
#: with the docstring of `Substring.Raw.getRange`.
_LINTER_RE = re.compile(
    r"/--(?P<doc>(?:(?!-/)[\s\S])*?)-/\s*\n\s*(?:public\s+|protected\s+|private\s+)*"
    r"register_option\s+(?P<opt>linter\.[A-Za-z0-9_.]+)\s*:\s*(?P<ty>\w+)\s*:="
    r"\s*\{(?P<body>(?:(?!\n\})[\s\S])*)",
)
_ANY_OPTION_RE = re.compile(r"register_option\s+(linter\.[A-Za-z0-9_.]+)")
_DEFVALUE_RE = re.compile(r"defValue\s*:=\s*([^\s,}\n]+)")
_NOTE_RE = re.compile(
    r"library_note2?\s+\"?«?(?P<tag>[^»\"\n]+?)»?\"?\s*\n?\s*/--(?P<body>(?:(?!-/)[\s\S])*)-/",
)
_CITE_RE = re.compile(r"See note \[([^\]]+)\]")
_SET_RE = re.compile(r"register_linter_set\s+(linter\.\w+)\s*:=\s*\n((?:[ \t]*(?:--)?[ \t]*linter\.[A-Za-z0-9_.]+.*\n|[ \t]*--.*\n)*)")

#: A linter set whose members are diagnostics rather than conventions. `nightlyRegressionSet`
#: holds `regressions.linarithToGrind` and friends, which exist to find where `grind` does *not*
#: yet supersede the older tactic. Reading membership here as "Mathlib wants grind" inverts it.
DIAGNOSTIC_SETS = frozenset({"linter.nightlyRegressionSet"})


@dataclass(frozen=True)
class ConventionRow:
    """One convention the repository states about itself."""

    key: str
    source: str                      # linter | library_note
    statement: str
    tier: str
    weight: Optional[int]            # citations for a note; None for a linter
    default: Optional[str]
    linter_set: Optional[str]
    path: str
    note: Optional[str] = None


def _lean_files(workspace: Path) -> List[Path]:
    return sorted(workspace.rglob("*.lean"))


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def linter_sets(workspace: Path) -> Dict[str, Dict[str, object]]:
    """Each `register_linter_set` and its members, keeping the commented-out ones.

    A member commented out of a set carries a reason -- "disabled, let's not impose this
    requirement downstream", or an issue link for `docPrime` -- and that reason is evidence about
    the convention's standing, so it is kept rather than dropped.
    """

    init = _read(workspace / "Mathlib" / "Init.lean")
    out: Dict[str, Dict[str, object]] = {}
    for match in _SET_RE.finditer(init):
        block = match.group(2)
        active, disabled = [], {}
        for line in block.splitlines():
            found = re.search(r"(linter\.[A-Za-z0-9_.]+)", line)
            if not found:
                continue
            if line.lstrip().startswith("--"):
                disabled[found.group(1)] = line.strip().lstrip("-").strip()
            else:
                active.append(found.group(1))
        out[match.group(1)] = {"active": active, "disabled": disabled}
    return out


def lakefile_options(workspace: Path) -> Dict[str, str]:
    """Linter options the lakefile turns on for every build -- the real enforcement switch."""

    text = _read(workspace / "lakefile.lean") or _read(workspace / "lakefile.toml")
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r"`(linter\.[A-Za-z0-9_.]+)\s*,\s*([^⟩\n]+)⟩", text)}


def _tier(option: str, default: Optional[str], sets: Dict[str, Dict[str, object]],
          lakefile: Dict[str, str]) -> tuple:
    for name, payload in sets.items():
        if option in payload["disabled"]:
            return "disabled", name
    standard = sets.get("linter.mathlibStandardSet", {}).get("active", [])
    if option in standard:
        return "standard", "linter.mathlibStandardSet"
    if option in lakefile:
        return "lakefile", None
    for name, payload in sets.items():
        if option in payload["active"]:
            return ("nightly" if name in DIAGNOSTIC_SETS else "weekly"), name
    if default == "true":
        return "default_on", None
    return "available", None


def extract_linters(workspace: Path) -> List[ConventionRow]:
    sets = linter_sets(workspace)
    lakefile = lakefile_options(workspace)
    rows: List[ConventionRow] = []
    seen = set()
    for path in _lean_files(workspace):
        source = _read(path)
        if "register_option linter." not in source:
            continue
        for match in _LINTER_RE.finditer(source):
            option = match.group("opt")
            if option in seen:
                continue
            seen.add(option)
            default_match = _DEFVALUE_RE.search(match.group("body"))
            default = default_match.group(1) if default_match else None
            tier, set_name = _tier(option, default, sets, lakefile)
            rows.append(ConventionRow(
                key=option, source="linter",
                statement=" ".join(match.group("doc").split()),
                tier=tier, weight=None, default=default, linter_set=set_name,
                path=path.relative_to(workspace).as_posix(),
            ))
    return sorted(rows, key=lambda r: r.key)


def extract_library_notes(workspace: Path) -> List[ConventionRow]:
    files = _lean_files(workspace)
    citations: collections.Counter = collections.Counter()
    for path in files:
        citations.update(_CITE_RE.findall(_read(path)))

    rows: List[ConventionRow] = []
    seen = set()
    for path in files:
        source = _read(path)
        if "library_note" not in source:
            continue
        for match in _NOTE_RE.finditer(source):
            tag = match.group("tag").strip()
            if tag in seen:
                continue
            seen.add(tag)
            rows.append(ConventionRow(
                key=tag, source="library_note",
                statement=" ".join(match.group("body").split()),
                # A note is normative by being cited, not by a flag; the count is the weight and
                # an uncited note is a note nobody follows.
                tier="cited" if citations[tag] else "uncited",
                weight=citations[tag], default=None, linter_set=None,
                path=path.relative_to(workspace).as_posix(),
            ))
    return sorted(rows, key=lambda r: (-(r.weight or 0), r.key))


def unregistered_options(workspace: Path, extracted: List[ConventionRow]) -> List[str]:
    """Options that exist but whose docstring could not be read -- reported, never silently lost."""

    every = set()
    for path in _lean_files(workspace):
        every.update(_ANY_OPTION_RE.findall(_read(path)))
    return sorted(every - {r.key for r in extracted if r.source == "linter"})


def workspace_revision(workspace: Path) -> Optional[str]:
    try:
        return subprocess.run(["git", "-C", str(workspace), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def build(workspace: Path = MATHLIB_CLONE) -> Dict[str, object]:
    if not (workspace / "Mathlib").is_dir():
        raise FileNotFoundError(f"no Mathlib tree at {workspace}")
    linters = extract_linters(workspace)
    notes = extract_library_notes(workspace)
    rows = linters + notes
    tiers = collections.Counter(r.tier for r in rows)
    return {
        "schema_version": CATALOGUE_VERSION,
        "workspace": str(workspace),
        "workspace_revision": workspace_revision(workspace),
        "counts": {"linters": len(linters), "library_notes": len(notes), "total": len(rows)},
        "by_tier": dict(sorted(tiers.items())),
        "linter_options_without_a_readable_docstring": unregistered_options(workspace, rows),
        "rows": [asdict(r) for r in rows],
    }


def write(payload: Dict[str, object], out_dir: Path = CONVENTIONS_TRACKED) -> Dict[str, str]:
    """Rows as JSONL beside a manifest, matching `inputs/pull_requests/`.

    The rows are the artifact and the manifest names the snapshot they were read from, so a number
    quoted from this catalogue can always be tied back to a revision. `rows_sha256` is over the
    JSONL bytes, so a manifest can never describe rows it did not produce.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    rows = payload["rows"]
    body = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
    (out_dir / "catalogue.jsonl").write_text(body, encoding="utf-8")
    manifest = {k: v for k, v in payload.items() if k != "rows"}
    manifest["rows_sha256"] = sha256_bytes(body.encode("utf-8"))
    manifest["rows_file"] = "catalogue.jsonl"
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return {"rows": str(out_dir / "catalogue.jsonl"), "manifest": str(out_dir / "manifest.json")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace", type=Path, default=MATHLIB_CLONE,
                        help="a Mathlib source tree; the revision is recorded in the manifest")
    parser.add_argument("--out", type=Path, default=CONVENTIONS_TRACKED,
                        help="directory for catalogue.jsonl + manifest.json")
    parser.add_argument("--write", action="store_true",
                        help="write the artifact; without it this prints the summary and stops")
    args = parser.parse_args()
    assert_repo_root()
    payload = build(args.workspace)
    summary = {k: v for k, v in payload.items() if k != "rows"}
    if args.write:
        summary["written"] = write(payload, args.out)
    print(json.dumps(summary, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
