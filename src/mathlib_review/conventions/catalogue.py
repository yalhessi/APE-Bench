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
from typing import Dict, List, Optional, Tuple

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


# --- pre-registration ---------------------------------------------------------------------------
# Frozen 2026-09-11, BEFORE the calibration sample was drawn, and pinned by
# `tests/mathlib_review/test_conventions_catalogue.py`. This project has fitted thresholds while
# looking at the answer at least twice -- the `n>=2 with docstring` clause existed so `to_fun`
# would pass, and "every target with n>=6 is a genuine convention" was recognition of names already
# known. Changing a value below means editing a test that says it was frozen, which is the point.

#: Declarations read in the free calibration pass before any model spend is considered.
CALIBRATION_SAMPLE = 30

#: Fixed so the sample is reproducible from the manifest alone.
CALIBRATION_SEED = 20260911

#: The kill criterion. A calibration candidate is *useful* when it is both unencoded (not already
#: a linter or a library note) and checkable against the fields `DeclarationRow` exposes. Below
#: this fraction the idea's ceiling is the easy end that CI already handles, and it stops here
#: rather than proceeding to the model pass.
KILL_CRITERION_MIN_USEFUL_FRACTION = 1.0 / 3.0

#: Adherence bands, reported rather than judged. A rate is not a verdict: 95% says the library is
#: consistent, not that a maintainer would request it.
ADHERENCE_BANDS = ((0.95, "settled"), (0.60, "contested_or_in_transition"), (0.0, "not_a_convention"))


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


def _sources(workspace: Path) -> List[Tuple[Path, str]]:
    """Every Lean file with its text, read once.

    The three extractors each used to glob and read the tree for themselves, and
    `extract_library_notes` read it twice over -- four passes across 8,567 files and 96MB for
    one catalogue, 21.9s of which 16 was re-reading what was already in hand. They still
    accept a workspace and scan it when called alone; `build` reads once and passes the
    result down.
    """

    return [(path, _read(path)) for path in _lean_files(workspace)]


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


def extract_linters(workspace: Path,
                    sources: Optional[List[Tuple[Path, str]]] = None) -> List[ConventionRow]:
    sets = linter_sets(workspace)
    lakefile = lakefile_options(workspace)
    rows: List[ConventionRow] = []
    seen = set()
    for path, source in (sources if sources is not None else _sources(workspace)):
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


def extract_library_notes(workspace: Path,
                          sources: Optional[List[Tuple[Path, str]]] = None) -> List[ConventionRow]:
    files = sources if sources is not None else _sources(workspace)
    citations: collections.Counter = collections.Counter()
    for _path, source in files:
        citations.update(_CITE_RE.findall(source))

    rows: List[ConventionRow] = []
    seen = set()
    for path, source in files:
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


def unregistered_options(workspace: Path, extracted: List[ConventionRow],
                         sources: Optional[List[Tuple[Path, str]]] = None) -> List[str]:
    """Options that exist but whose docstring could not be read -- reported, never silently lost."""

    every = set()
    for _path, source in (sources if sources is not None else _sources(workspace)):
        every.update(_ANY_OPTION_RE.findall(source))
    return sorted(every - {r.key for r in extracted if r.source == "linter"})


# --- observed candidates: sample, then check ------------------------------------------------------

#: The fields the built declaration table actually holds. A candidate predicate that needs anything
#: else cannot be checked today, and saying so is the point: the *count* of such candidates is the
#: measured gap that would justify widening the table, rather than widening it speculatively.
VERIFIABLE_FIELDS = frozenset({
    "path", "directory", "namespace", "kind", "fullname",
    "conclusion_head", "tactics", "wide_tactics", "proof_lines",
})


@dataclass(frozen=True)
class Candidate:
    """A convention someone claims to have *observed*, stated so it can be refuted.

    `requires` is the honest half: the declaration-table fields the predicate reads. A candidate
    naming a field the table lacks is recorded unverifiable rather than quietly passed, which is
    how the tooling gap gets counted instead of estimated.
    """

    key: str
    statement: str
    requires: tuple
    source: str = "observed"          # observed | model_observed
    encoded_as: Optional[str] = None  # a catalogue key when this duplicates an encoded convention

    @property
    def verifiable(self) -> bool:
        return set(self.requires) <= VERIFIABLE_FIELDS

    @property
    def missing_fields(self) -> List[str]:
        return sorted(set(self.requires) - VERIFIABLE_FIELDS)


def sample(table, count: int = CALIBRATION_SAMPLE, *, seed: int = CALIBRATION_SEED) -> List:
    """A reproducible sample stratified over directories.

    Uniform sampling of 168,058 declarations would concentrate wherever the library is largest and
    read like a tour of one subject. Stratifying by directory spreads the read across the 970 of
    them, which is what makes "conventions I already knew" less likely to be all that comes back.
    """

    import random

    by_directory: Dict[str, List] = collections.defaultdict(list)
    for row in table.rows:
        by_directory[row.directory].append(row)
    rng = random.Random(seed)
    directories = sorted(by_directory)
    rng.shuffle(directories)
    picked = []
    for directory in directories:
        if len(picked) >= count:
            break
        picked.append(rng.choice(sorted(by_directory[directory], key=lambda r: r.fullname)))
    return picked


def band(rate: float) -> str:
    for threshold, name in ADHERENCE_BANDS:
        if rate >= threshold:
            return name
    return ADHERENCE_BANDS[-1][1]


def adherence(table, candidate: Candidate, applicable, conforming) -> Dict[str, object]:
    """How much of the class the candidate claims actually conforms to it.

    `applicable` selects the reference class the convention speaks about and `conforming` picks out
    the rows that follow it, so the denominator is declared by the candidate rather than inherited
    from whatever happened to be observed -- which is the objection that sank the edit-clustering
    design.
    """

    if not candidate.verifiable:
        return {"key": candidate.key, "verifiable": False,
                "missing_fields": candidate.missing_fields,
                "applicable": None, "conforming": None, "rate": None, "band": None}
    rows = [row for row in table.rows if applicable(row)]
    hits = [row for row in rows if conforming(row)]
    rate = (len(hits) / len(rows)) if rows else None
    return {"key": candidate.key, "verifiable": True, "missing_fields": [],
            "applicable": len(rows), "conforming": len(hits),
            "rate": round(rate, 4) if rate is not None else None,
            "band": band(rate) if rate is not None else "no_applicable_rows"}


def calibration_verdict(candidates: List[Candidate]) -> Dict[str, object]:
    """The pre-registered decision, computed from the counts rather than from an impression."""

    useful = [c for c in candidates if c.encoded_as is None and c.verifiable]
    fraction = len(useful) / len(candidates) if candidates else 0.0
    return {
        "candidates": len(candidates),
        "already_encoded": sum(1 for c in candidates if c.encoded_as is not None),
        "unencoded_and_checkable": len(useful),
        "unencoded_but_unverifiable": sum(
            1 for c in candidates if c.encoded_as is None and not c.verifiable),
        "useful_fraction": round(fraction, 4),
        "threshold": round(KILL_CRITERION_MIN_USEFUL_FRACTION, 4),
        "proceed_to_model_pass": fraction >= KILL_CRITERION_MIN_USEFUL_FRACTION,
    }


def workspace_revision(workspace: Path) -> Optional[str]:
    try:
        return subprocess.run(["git", "-C", str(workspace), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def build(workspace: Path = MATHLIB_CLONE) -> Dict[str, object]:
    if not (workspace / "Mathlib").is_dir():
        raise FileNotFoundError(f"no Mathlib tree at {workspace}")
    sources = _sources(workspace)
    linters = extract_linters(workspace, sources)
    notes = extract_library_notes(workspace, sources)
    rows = linters + notes
    tiers = collections.Counter(r.tier for r in rows)
    return {
        "schema_version": CATALOGUE_VERSION,
        "workspace": str(workspace),
        "workspace_revision": workspace_revision(workspace),
        "counts": {"linters": len(linters), "library_notes": len(notes), "total": len(rows)},
        "by_tier": dict(sorted(tiers.items())),
        "linter_options_without_a_readable_docstring": unregistered_options(
            workspace, rows, sources),
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
