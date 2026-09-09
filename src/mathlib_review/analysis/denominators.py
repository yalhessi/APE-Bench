"""Recompute what an archived audit's recall would have been over an honest denominator.

Every audit before `pr5-smoke4-rep9` was scored against the same 40-obligation pool. The pool
spans twelve PRs, and it was used whatever PRs the run reviewed: `lead-smoke4-rep7` (4 PRs) and
`heldout11-rep2` (11 PRs) have byte-identical obligation sets, so both divided their hits by
other runs' work. `semantic_report` now takes a `scoped_pr_numbers`, and `judged_pr_scope`
derives it from the generation run rather than trusting a config to remember.

That fixes future runs and does nothing for the archive, which is what every comparison we have
made so far was reading. Rather than rewrite those reports -- the same argument as
`corrections.py`: editing a run's artifacts after the fact destroys the evidence that the defect
existed -- the correction lands beside each one as `denominator_correction.json`.

**Hits are recoverable, rates are not.** An obligation belonging to a PR the run never reviewed
cannot be hit by it, so the hit *counts* in an archived report are already correct; only the
divisor was wrong. Recomputing is therefore exact, not an estimate.

This is a derived artifact and not a score. The runs it describes were produced under the
configuration they were produced under, and several of them remain forensic for other reasons.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.mathlib_review.io import canonical_json_bytes, sha256_bytes
from src.mathlib_review.paths import run_dir

#: Bumped whenever the recomputation changes what it reads or how it divides.
DENOMINATOR_CORRECTION_VERSION = "v5-denominator-correction/1"

#: Where the judge writes its audits. Imported lazily in `audit_dir_for` to avoid a cycle
#: through the judge package, which imports this module's siblings.
_AUDIT_ROOT = Path("results/pr_review_v5/audits")


@dataclass
class Correction:
    """One audit's recall, as printed and as it should have been."""

    audit: str
    run_name: Optional[str]
    printed_obligations: int
    scoped_obligations: int
    pr_scope: Optional[List[int]]
    issue_hits: int
    resolution_hits: int
    location_hits: int

    def rates(self) -> Dict[str, Optional[float]]:
        n = self.scoped_obligations
        if not n:
            return {"issue_recall": None, "resolution_recall": None, "location_recall": None}
        return {
            "issue_recall": round(self.issue_hits / n, 4),
            "resolution_recall": round(self.resolution_hits / n, 4),
            "location_recall": round(self.location_hits / n, 4),
        }


def audit_dir_for(run_name: str) -> Path:
    """The audit directory a generation run's judge writes into.

    Reuses the judge's own derivation instead of restating the slug rule, which is exactly the
    duplication `derive_from_run` exists to remove.
    """

    from src.mathlib_review.judge.runner import derive_from_run

    return Path(derive_from_run(run_name)["out_dir"])


def resolve_run_for_audit(audit_name: str, run_names: Iterable[str]) -> Optional[str]:
    """Which generation run an archived audit scored.

    `derive_from_run` is the rule now, but the older audit directories were named by hand
    before it existed and do not match it: `pr_review_v5_lead_heldout11_rep2` derives
    `lead-heldout11-rep2` while its audit sits in `heldout11-rep2`. The derived name is tried
    first, so a run that followed the rule is matched by the rule; the `lead-` elision is a
    second pass for the archive only, and anything still unmatched returns `None` rather than
    being guessed at.
    """

    derived = {}
    for name in run_names:
        try:
            derived[audit_dir_for(name).name] = name
        except Exception:
            continue
    if audit_name in derived:
        return derived[audit_name]
    relaxed = {key[len("lead-"):]: value for key, value in derived.items()
               if key.startswith("lead-")}
    return relaxed.get(audit_name)


def pr_scope_for(run_name: str) -> Optional[List[int]]:
    """The PRs a generation run enumerated work for, from its own agenda report.

    Neither `run_manifest.json` nor `run_plan.json` records them; `agenda_report.json` does.
    """

    path = run_dir(run_name) / "agenda_report.json"
    if not path.is_file():
        return None
    numbers = json.loads(path.read_text(encoding="utf-8")).get("pr_numbers")
    return sorted(numbers) if numbers else None


def obligations_by_pr(context_path: Path) -> Dict[str, int]:
    """How many obligations each PR carries, keyed by obligation id -> pr number.

    Read from the curation context rather than a release's gold, because the archived audits
    were scored against the curated pool and this has to speak about the same population.
    """

    rows = json.loads(context_path.read_text(encoding="utf-8"))["rows"]
    return {row["obligation_id"]: row["pr_number"] for row in rows}


def correct(report: Dict[str, Any], *, audit: str, run_name: Optional[str],
            pr_scope: Optional[List[int]],
            pr_of_obligation: Dict[str, int]) -> Correction:
    """Recompute one report's rates over the obligations of the PRs actually reviewed."""

    rows = report.get("per_obligation") or []
    if pr_scope is None:
        kept = rows
    else:
        wanted = set(pr_scope)
        kept = [row for row in rows
                if pr_of_obligation.get(row["obligation_id"]) in wanted]
    return Correction(
        audit=audit,
        run_name=run_name,
        printed_obligations=int((report.get("counts") or {}).get("obligations") or len(rows)),
        scoped_obligations=len(kept),
        pr_scope=pr_scope,
        issue_hits=sum(1 for row in kept if row.get("issue_status") == "hit"),
        resolution_hits=sum(1 for row in kept if row.get("resolution_status") == "hit"),
        location_hits=sum(1 for row in kept if row.get("location_hit")),
    )


def sidecar_payload(correction: Correction, report_sha256: str) -> Dict[str, Any]:
    return {
        "schema_version": DENOMINATOR_CORRECTION_VERSION,
        "audit": correction.audit,
        "run_name": correction.run_name,
        "source_report_sha256": report_sha256,
        "note": (
            "Derived. The audit's own semantic_report.json is unchanged and remains the "
            "record of what was run. Hit counts are copied, not recomputed: an obligation "
            "from a PR the run never reviewed cannot be hit, so only the divisor was wrong."
        ),
        "printed": {
            "obligations": correction.printed_obligations,
            "issue_recall": _rate(correction.issue_hits, correction.printed_obligations),
            "resolution_recall": _rate(
                correction.resolution_hits, correction.printed_obligations),
            "location_recall": _rate(correction.location_hits, correction.printed_obligations),
        },
        "corrected": {
            "obligations": correction.scoped_obligations,
            "pr_scope": correction.pr_scope,
            **correction.rates(),
        },
        "hits": {
            "issue": correction.issue_hits,
            "resolution": correction.resolution_hits,
            "location": correction.location_hits,
        },
    }


def _rate(hits: int, total: int) -> Optional[float]:
    return round(hits / total, 4) if total else None


def write_sidecar(audit_dir: Path, payload: Dict[str, Any]) -> Path:
    path = audit_dir / "denominator_correction.json"
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def correct_archive(audits_root: Path = _AUDIT_ROOT,
                    runs_root: Path = Path("results/pr_review_v5/runs"),
                    context: Path = Path(
                        "inputs/pr_review_v4/curation/obligation_context_v1.json"),
                    write: bool = False) -> List[Dict[str, Any]]:
    """Recompute every archived audit, optionally leaving a sidecar beside each."""

    pr_of_obligation = obligations_by_pr(context)
    run_names = sorted(path.name for path in runs_root.glob("*") if path.is_dir())
    rows: List[Dict[str, Any]] = []
    for report_path in sorted(audits_root.glob("*/semantic_report.json")):
        raw = report_path.read_bytes()
        report = json.loads(raw)
        if not report.get("per_obligation"):
            # An unscored report has no obligation rows to re-divide.
            continue
        audit = report_path.parent.name
        run_name = resolve_run_for_audit(audit, run_names)
        correction = correct(
            report, audit=audit, run_name=run_name,
            pr_scope=pr_scope_for(run_name) if run_name else None,
            pr_of_obligation=pr_of_obligation,
        )
        payload = sidecar_payload(correction, sha256_bytes(raw))
        if run_name is None:
            payload["note"] += (
                " No generation run could be matched to this audit, so the PR scope is "
                "unknown and the printed denominator is carried through uncorrected."
            )
        if write:
            write_sidecar(report_path.parent, payload)
        rows.append(payload)
    return rows


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true",
                        help="leave denominator_correction.json beside each audit")
    args = parser.parse_args()
    for payload in correct_archive(write=args.write):
        printed, corrected = payload["printed"], payload["corrected"]
        print("%-22s %-38s %3s -> %-3s  issue %.3f -> %.3f" % (
            payload["audit"], payload["run_name"] or "UNRESOLVED",
            printed["obligations"], corrected["obligations"],
            printed["issue_recall"] or 0.0, corrected["issue_recall"] or 0.0,
        ))


if __name__ == "__main__":
    main()
