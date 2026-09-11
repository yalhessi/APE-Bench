"""What proofs in Mathlib actually look like, at one commit, so a norm can be measured.

**Why this is not a frequency lookup.** Rung 3a established that `proof_idiom`, forced to
sweep its own tactic list, produced 53 `simpa` variants and never once wrote `grind` -- not in
a tool call, not in a result, not in its own text. An arm cannot ask about a tactic that is not
in its repertoire. So the primary question this answers is *generative* -- "what closes proofs
like this one" -- and not *confirmatory* -- "how often does X appear", which requires already
suspecting X.

**Why a level is never returned alone.** Measured at PR 33098's base commit, every framing of
code frequency argues against the maintainer who asked for `grind`:

    all proofs                                        1.1 %
    conditioned on conclusion shape                   0.7 - 1.4 %
    conditioned on the reviewed file's own directory  0.46 %   <- worse than global
    the same measure across the commit's own history  0.00 % -> 9.21 % in 14 months

The level lives in the code and buries the norm; the derivative reveals it. `agenda/review_map`
already records this trap for naming -- `coe_` outnumbers the requested `toLinearMap_` 4707 to
50 -- and it holds for tactics too. So `profile()` carries a trajectory, and a caller that wants
only a count has to ask for it explicitly and gets the population with it.

**Where it reads.** The prebuilt snapshot for the base commit, via `snapshot_workspace`, never
a task's own workspace: run workspaces materialize the directory tree but only the files a task
touches, and a scan of ~2% of Mathlib still clears any support threshold. `evidence.py` learned
this and abstains; so does this, through `is_representative`.
"""

from __future__ import annotations

import argparse
import collections
import json
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from ape.toolkits.code.lean.lean_parser import mask_noncode_regions, parse_major_declarations

from src.mathlib_review.evidence.operators.naming_contrast import declaration_conclusion
from src.mathlib_review.io import canonical_json_bytes, sha256_bytes
from src.mathlib_review.tactics import (
    TACTIC_VOCABULARY, TACTIC_VOCABULARY_VERSION, WIDE_TACTIC_VOCABULARY, tactics_used,
)

TABLE_VERSION = "v5-declaration-table/2"   # /2: binder-aware conclusion_head (a big operator's ∈ is not a membership goal)

#: The answer shape `proof_profile` returns. Bumped when the tool starts saying something new,
#: so a run can be told apart from one made against an earlier answer: `/1` returned rank and
#: trend only, and rung 3b ran against it. `/2` adds worked exemplars, because rank and trend
#: told the arm how common a tactic is and nothing about what it is for.
PROOF_PROFILE_VERSION = "v5-proof-profile/2"

#: The classifier that turns a conclusion into a reference class. Versioned separately from the
#: table because a change here re-partitions every population without changing a single row.
CONCLUSION_CLASSIFIER_VERSION = "v5-conclusion-head/2"   # /2: binder-aware; ⋃₀ is not a binder

#: Below this the scan is a sample, not a census. `naming_norm` uses the same floor for the
#: same reason, and the number is the point: a 2% scan still clears any support threshold.
MIN_CORPUS_FILES = 1000

#: Where built tables live, one directory per base commit.
TABLE_ROOT = Path("data/pr_review_v5/declaration_tables")

#: Relation symbols that make a conclusion's shape, in the order they are tested. Order matters
#: only for a conclusion carrying two of them at the same depth, which is rare and arbitrary
#: either way; it is fixed here so the partition is reproducible.
_HEADS: Tuple[Tuple[str, str], ...] = (
    ("⊆", "subset"), ("⊂", "ssubset"), ("≤", "le"), ("≥", "ge"),
    ("↔", "iff"), ("∈", "mem"), ("=", "eq"),
)


#: Symbols that open a binder `… x ∈ s, body` at depth 0: big operators, integrals, quantifiers.
_BINDER_OPENERS = "∑∏⋃⋂⨆⨅⨁∫∮⨍∀∃"


def conclusion_head(conclusion: Optional[str]) -> Optional[str]:
    """The outermost relation of a conclusion, or a role when it has none.

    Depth-tracked, so a relation inside a binder or an argument does not decide the class.

    This must never be re-derived by eye. The first version of this probe took the conclusion
    with `signature.rfind(':')` -- the *last* top-level colon, which in a signature with binders
    is a binder's -- and reported the `subset` population as **25** against the true **2302**,
    a 92x error in a table that read as authoritative. `declaration_conclusion` is depth-tracked
    and finds the *first* top-level colon; nothing here may reimplement it.
    """

    text = (conclusion or "").strip()
    if not text:
        return None
    if text.startswith(("∃", "∀")):
        return "quantified"
    depth = 0
    # A binder's `∈` is not a relation: in `∑ i ∈ s, f i = g` the conclusion is an equation, and
    # `∀ i ∈ t, p i` inside a larger conclusion quantifies. Big operators and quantifiers open a
    # binder that runs to the next depth-0 comma; relation symbols inside it do not decide.
    in_binder = False
    for index, character in enumerate(text):
        if character in "([{":
            depth += 1
        elif character in ")]}":
            depth = max(0, depth - 1)
        elif depth == 0:
            if character in _BINDER_OPENERS:
                # `⋃₀ S` / `⋂₀ S` are set-of-sets operators, not binders: no `x ∈ s,` follows,
                # and treating them as binders swallowed `⋃₀ S ⊆ t` into "other".
                if text[index + 1: index + 2] != "₀":
                    in_binder = True
                continue
            if in_binder:
                if character == ",":
                    in_binder = False
                continue
            for symbol, name in _HEADS:
                if character != symbol:
                    continue
                # `=>` is a lambda arrow, not an equality.
                if symbol == "=" and index + 1 < len(text) and text[index + 1] == ">":
                    continue
                return name
    return "other"


@dataclass(frozen=True)
class DeclarationRow:
    """One proved declaration, reduced to the features a norm question asks about."""

    path: str
    directory: str
    namespace: Optional[str]
    kind: str
    fullname: str
    conclusion_head: Optional[str]
    tactics: Tuple[str, ...]
    wide_tactics: Tuple[str, ...]
    proof_lines: int


@dataclass
class DeclarationTable:
    """Every proved declaration at one commit, and how much of the corpus was seen."""

    snapshot_sha: str
    rows: List[DeclarationRow] = field(default_factory=list)
    parsed_files: int = 0
    parse_failures: List[str] = field(default_factory=list)

    def is_representative(self) -> bool:
        """Whether this scan saw enough of the corpus to speak for it."""

        return self.parsed_files >= MIN_CORPUS_FILES

    def select(self, *, directory: Optional[str] = None,
               conclusion_head_: Optional[str] = None,
               namespace: Optional[str] = None) -> List[DeclarationRow]:
        """The reference class. Every filter is optional; none of them is a default."""

        rows = self.rows
        if directory is not None:
            rows = [item for item in rows if item.directory.startswith(directory)]
        if conclusion_head_ is not None:
            rows = [item for item in rows if item.conclusion_head == conclusion_head_]
        if namespace is not None:
            rows = [item for item in rows if (item.namespace or "").startswith(namespace)]
        return rows


def _namespace_of(fullname: str) -> Optional[str]:
    return fullname.rsplit(".", 1)[0] if "." in fullname else None


def build_table(workspace: Path, snapshot_sha: str,
                *, wide: bool = True) -> DeclarationTable:
    """One pass over a complete snapshot. ~42 s for Mathlib's 7409 files on this machine.

    Deliberately the same shape as `naming_norm.scan_population`, which already walks this tree
    for a different classifier: one pass, count what was parsed, record what failed, and leave
    the representativeness decision to the caller.
    """

    mathlib = workspace / "Mathlib"
    if not mathlib.is_dir():
        raise FileNotFoundError(f"Mathlib source tree is unavailable: {mathlib}")

    table = DeclarationTable(snapshot_sha=snapshot_sha)
    for path in sorted(mathlib.rglob("*.lean")):
        relative = path.relative_to(workspace).as_posix()
        table.parsed_files += 1
        try:
            source = path.read_text(encoding="utf-8")
            declarations = parse_major_declarations(source)
        except (OSError, UnicodeError, ValueError) as exc:
            table.parse_failures.append(f"{relative}: {exc}")
            continue
        parts = Path(relative).parts
        directory = "/".join(parts[1:-1]) or "."
        for declaration in declarations:
            if declaration.kind not in {"lemma", "theorem"}:
                continue
            proof = getattr(declaration, "proof", None) or ""
            if not proof:
                continue
            fullname = declaration.fullname or declaration.name or ""
            if not fullname:
                continue
            # Masked before matching: a tactic named in a docstring is not a tactic used.
            masked = mask_noncode_regions(proof)
            table.rows.append(DeclarationRow(
                path=relative,
                directory=directory,
                namespace=_namespace_of(fullname),
                kind=declaration.kind,
                fullname=fullname,
                conclusion_head=conclusion_head(
                    declaration_conclusion(getattr(declaration, "signature", "") or "")),
                tactics=tuple(sorted(tactics_used(masked, TACTIC_VOCABULARY))),
                wide_tactics=(tuple(sorted(tactics_used(masked, WIDE_TACTIC_VOCABULARY)))
                              if wide else ()),
                proof_lines=proof.count("\n") + 1,
            ))
    return table


def distribution(rows: Sequence[DeclarationRow], *, wide: bool = False) -> Dict[str, Any]:
    """How this reference class closes its proofs, with the population it is divided by."""

    counts: collections.Counter = collections.Counter()
    for row in rows:
        for tactic in (row.wide_tactics if wide else row.tactics):
            counts[tactic] += 1
    population = len(rows)
    return {
        "population": population,
        "vocabulary": "wide" if wide else "strict",
        "tactic_vocabulary_version": TACTIC_VOCABULARY_VERSION,
        "conclusion_classifier_version": CONCLUSION_CLASSIFIER_VERSION,
        "tactics": [
            {"tactic": tactic, "count": count,
             "share": round(count / population, 4) if population else None}
            for tactic, count in counts.most_common()
        ],
    }


def exemplars(rows: Sequence[DeclarationRow], tactic: str, workspace: Path,
              *, limit: int = 3, max_chars: int = 260) -> List[Dict[str, str]]:
    """Real proofs from this reference class that use `tactic`, shortest first.

    **Why a count is not enough.** A share tells an arm how often a tactic appears and nothing
    about what it is for. `grind` at 2.6% conveys "uncommon"; `map_div' := by grind
    [div_eq_mul_inv]` conveys the mechanism -- name the fact the goal needs and the tactic
    assembles the rest -- which is the thing that transfers to a new goal. Rung 3b delivered
    rank and trend, the arm read them, and proposed the tactic it already knew; motivation by
    demonstration is the part that was missing.

    Read from the snapshot on demand rather than stored: the table is 4.3 MB without proof
    bodies and would be an order of magnitude larger with them, for text that is wanted a
    handful of rows at a time.

    Sampled ACROSS the length range rather than taking the k shortest. Taking the shortest
    returned three bare `by grind` proofs, which show that the tactic closes such goals and not
    how it is aimed; the bracketed form that carries the mechanism only appears in longer ones.
    Filtering *for* the bracketed spelling would be steering dressed as evidence -- a maintainer
    asked for it on this PR, and the tool must not know that -- so the rule is length diversity,
    which is spelling-blind and gets there anyway.
    """

    candidates = [row for row in rows if tactic in row.tactics]
    candidates.sort(key=lambda row: (row.proof_lines, row.fullname))
    if not candidates:
        return []

    # Round-robin over length terciles rather than sampling fixed indices: a candidate that
    # fails the `max_chars` filter or whose declaration cannot be re-found has to be replaced,
    # and index sampling silently returned two exemplars where three were asked for.
    terciles: List[List[DeclarationRow]] = [[], [], []]
    for position, row in enumerate(candidates):
        terciles[min(2, position * 3 // len(candidates))].append(row)

    ordered: List[DeclarationRow] = []
    for depth in range(len(candidates)):
        for bucket in terciles:
            if depth < len(bucket):
                ordered.append(bucket[depth])

    out: List[Dict[str, str]] = []
    for row in ordered:
        if len(out) >= limit:
            break
        try:
            source = (workspace / row.path).read_text(encoding="utf-8")
        except OSError:
            continue
        for declaration in parse_major_declarations(source):
            if (declaration.fullname or declaration.name) != row.fullname:
                continue
            proof = (getattr(declaration, "proof", "") or "").strip()
            if proof and tactic in mask_noncode_regions(proof) and len(proof) <= max_chars:
                out.append({"fullname": row.fullname, "path": row.path, "proof": proof})
            break
    return out


# --- trajectory ------------------------------------------------------------------------
#
# The same classifier, evaluated at earlier commits of the same clone. Level and trajectory
# then differ only in `as_of`, so they are directly comparable -- which a discussion corpus
# could not be. `--before` is also the temporal gate: `rev-list` walks ancestors of the base,
# so no commit after it is reachable.

MATHLIB_CLONE = Path("data/code_execute/repos/mathlib4/source")


def _git(clone: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(clone), *args],
                          capture_output=True, text=True, timeout=300).stdout


def commit_date(base_sha: str, *, clone: Path = MATHLIB_CLONE) -> Optional[str]:
    """The base commit's own date, so a curve can be anchored to it rather than to a literal.

    Hardcoded sample dates are how a trend gets missed: the first version of the tool sampled
    2025-01 and 2025-07 for a commit dated 2025-12, which straddled none of `grind`'s rise and
    reported every tactic as flat.
    """

    if not clone.is_dir():
        return None
    out = _git(clone, "log", "-1", "--format=%ad", "--date=short", base_sha).strip()
    return out or None


def curve_dates(base_sha: str, *, clone: Path = MATHLIB_CLONE) -> List[str]:
    """Points for a trend ending at the base commit: two years back, one year back, and it.

    The last point is the base's own date, so the curve's right-hand end is the state the PR was
    opened against. Earlier points are calendar-shifted from it, not fixed.
    """

    anchored = commit_date(base_sha, clone=clone)
    if not anchored:
        return []
    year = int(anchored[:4])
    return [f"{year - 2}{anchored[4:]}", f"{year - 1}{anchored[4:]}", anchored]


def trajectory(pattern: str, base_sha: str, dates: Sequence[str],
               *, clone: Path = MATHLIB_CLONE,
               subdir: str = "Mathlib") -> List[Dict[str, Any]]:
    """File-level share of `pattern` at each date, along the base commit's own ancestry.

    File-level rather than proof-level on purpose: this walks history without checking out,
    and `git grep` over a tree is seconds where a parse of every commit would be minutes. The
    absolute numbers therefore differ from `distribution()` -- 9.2% of *files* against 1.1% of
    *proofs* at the same commit -- and only the shape of the curve is being read.
    """

    if not clone.is_dir():
        raise FileNotFoundError(
            f"no Mathlib clone at {clone}; trajectory needs history, not a snapshot")
    out: List[Dict[str, Any]] = []
    for date in dates:
        commit = _git(clone, "rev-list", "-1", f"--before={date}", base_sha).strip()
        if not commit:
            continue
        files = _git(clone, "ls-tree", "-r", "--name-only", commit, "--", subdir)
        total = sum(1 for line in files.splitlines() if line.endswith(".lean"))
        hits = _git(clone, "grep", "-l", "-E",
                    rf"(^|[^A-Za-z0-9_]){pattern}([^A-Za-z0-9_]|$)",
                    commit, "--", f"{subdir}/*.lean")
        matched = len([line for line in hits.splitlines() if line.strip()])
        out.append({
            "date": date, "commit": commit[:12],
            "files": total, "matching": matched,
            "share": round(matched / total, 4) if total else None,
        })
    return out


# --- persistence -----------------------------------------------------------------------

def table_dir(snapshot_sha: str, root: Path = TABLE_ROOT) -> Path:
    return root / snapshot_sha


def write_table(table: DeclarationTable, root: Path = TABLE_ROOT) -> Path:
    out = table_dir(table.snapshot_sha, root)
    out.mkdir(parents=True, exist_ok=True)
    rows_path = out / "declarations.jsonl"
    rows_path.write_text(
        "".join(json.dumps(asdict(row), ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")) + "\n" for row in table.rows),
        encoding="utf-8")
    manifest = {
        "schema_version": TABLE_VERSION,
        "tactic_vocabulary_version": TACTIC_VOCABULARY_VERSION,
        "conclusion_classifier_version": CONCLUSION_CLASSIFIER_VERSION,
        "snapshot_sha": table.snapshot_sha,
        "parsed_files": table.parsed_files,
        "parse_failures": len(table.parse_failures),
        "rows": len(table.rows),
        "representative": table.is_representative(),
        "rows_sha256": sha256_bytes(rows_path.read_bytes()),
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def load_table(snapshot_sha: str, root: Path = TABLE_ROOT) -> DeclarationTable:
    """Read a built table, refusing one that was written from a partial checkout."""

    out = table_dir(snapshot_sha, root)
    manifest_path = out / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"no declaration table for {snapshot_sha}; build it with "
            f"`python -m src.mathlib_review.retrieval.declaration_table --commit {snapshot_sha}`")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # Versions are checked, not just recorded. A classifier change re-partitions every population
    # without changing a row count, so a stale table loads cleanly and answers wrongly: the one
    # table on disk was labelled `conclusion-head/1` for a day after the code moved to `/2`, and
    # nothing noticed because this function looked only at `representative`.
    expected = {
        "schema_version": TABLE_VERSION,
        "conclusion_classifier_version": CONCLUSION_CLASSIFIER_VERSION,
        "tactic_vocabulary_version": TACTIC_VOCABULARY_VERSION,
    }
    stale = {key: (manifest.get(key), want) for key, want in expected.items()
             if manifest.get(key) != want}
    if stale:
        detail = ", ".join(f"{key} {have!r} != {want!r}" for key, (have, want) in stale.items())
        raise ValueError(
            f"the declaration table for {snapshot_sha} is stale ({detail}); rebuild it with "
            f"`python -m src.mathlib_review.retrieval.declaration_table --commit {snapshot_sha} --write`")
    if not manifest.get("representative"):
        raise ValueError(
            f"the declaration table for {snapshot_sha} was built from "
            f"{manifest.get('parsed_files')} files, below the {MIN_CORPUS_FILES} floor. A scan "
            "of a partial checkout still clears any support threshold, so it would publish "
            "sampling artifacts as repository measurements."
        )
    table = DeclarationTable(snapshot_sha=snapshot_sha,
                             parsed_files=manifest["parsed_files"])
    for line in (out / "declarations.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = json.loads(line)
            payload["tactics"] = tuple(payload["tactics"])
            payload["wide_tactics"] = tuple(payload.get("wide_tactics") or ())
            table.rows.append(DeclarationRow(**payload))
    return table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--commit", required=True, help="base commit sha")
    parser.add_argument("--workspace", type=Path, default=None,
                        help="override the snapshot workspace (default: resolve by sha)")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    workspace = args.workspace
    if workspace is None:
        from src.mathlib_review.evidence.evidence import snapshot_workspace

        workspace = snapshot_workspace(args.commit)
    if workspace is None:
        raise SystemExit(f"no prebuilt snapshot for {args.commit}")

    started = time.time()
    table = build_table(Path(workspace), args.commit)
    report = {
        "snapshot_sha": args.commit,
        "seconds": round(time.time() - started, 1),
        "parsed_files": table.parsed_files,
        "parse_failures": len(table.parse_failures),
        "rows": len(table.rows),
        "representative": table.is_representative(),
        # `None` is a real class -- a declaration whose signature yielded no conclusion --
        # and it has to survive into the report rather than being dropped or crashing the
        # sort, because a large one means the extractor is failing.
        "by_conclusion_head": {
            (head or "unextracted"): count
            for head, count in collections.Counter(
                row.conclusion_head for row in table.rows).most_common()
        },
    }
    if args.write:
        report["written"] = str(write_table(table))
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
