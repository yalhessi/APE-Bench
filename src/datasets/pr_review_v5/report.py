"""Read a v5 run: what the lead did, then how well it matched the experts — in that order.

The order is the point. If routing was degenerate — the lead pruned nothing, or ran nothing,
or never touched a context tool — then the delegation mechanism did not engage, and a recall
number is measuring the arms rather than the thing the run was built to test. So `routing`
prints first and `score` refuses to be read as a verdict on delegation without it.

    python -m src.datasets.pr_review_v5.report routing   --run <run_name>
    python -m src.datasets.pr_review_v5.report score     --audit <audit_dir> --run <run_name>
    python -m src.datasets.pr_review_v5.report blueprint --run <run_name> [--audit <audit_dir>]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .paths import RESULTS, run_dir
from .trace import routing_report


def _load_jsonl(path: Path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def routing(run_name: str) -> Dict[str, Any]:
    directory = run_dir(run_name)
    delegations = _load_jsonl(directory / "delegations.jsonl")
    report = routing_report(delegations)
    manifest_path = directory / "run_manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        report["cost"] = manifest.get("total_cost")
        report["wall_seconds"] = manifest.get("wall_seconds")
        report["completion_status"] = manifest.get("completion_status")
        report["candidates_total"] = manifest.get("candidates_total")
        report["issues_total"] = manifest.get("issues_total")
    return report


def reachable_obligations(run_name: str,
                          eligible_obligation_ids: Optional[Iterable[str]] = None,
                          ) -> Optional[Dict[str, Any]]:
    """How many gold obligations this run could possibly have hit.

    The judge counts obligations across the whole release — 40 for dev-medium — regardless
    of which PRs the run actually reviewed. For a 4-PR run that denominator includes nine
    PRs the agent never saw, so the printed recall understates it by more than a factor of
    two. Scoping it is an evaluation-time question, so reading gold here is legitimate; the
    generation side never touches it.
    """

    agenda_path = run_dir(run_name) / "agenda.json"
    if not agenda_path.is_file():
        return None
    agenda = json.loads(agenda_path.read_text())
    reviewed = {item["pr_number"] for item in agenda.get("proposals", [])}
    judgments = Path(agenda["release"]) / "gold/judgments.jsonl"
    if not judgments.is_file():
        return None
    # Count *eligible* obligations, not raw ones. The judge scores a filtered set — 40 of
    # the release's obligations, not all of them — and an obligation outside it can never be
    # paired, matched, or hit. Counting raw obligations inflated the denominator with
    # unscoreable rows: PR 33057's single obligation is ineligible, so a finding that
    # correctly identified its build break had nowhere to land and read as a miss.
    eligible: Optional[set] = None
    if eligible_obligation_ids is not None:
        eligible = set(eligible_obligation_ids)
    by_pr: Dict[int, int] = {}
    ineligible: Dict[int, int] = {}
    for row in _load_jsonl(judgments):
        pr = row.get("pr_number")
        if pr not in reviewed:
            continue
        for obligation in row.get("obligations") or []:
            oid = obligation.get("obligation_id")
            if eligible is not None and oid not in eligible:
                ineligible[pr] = ineligible.get(pr, 0) + 1
                continue
            by_pr[pr] = by_pr.get(pr, 0) + 1
    return {
        "unscoreable_obligations_by_pr": dict(sorted(ineligible.items())),
        "reviewed_prs": sorted(reviewed),
        "obligations_by_pr": dict(sorted(by_pr.items())),
        "reachable": sum(by_pr.values()),
        # A control is a PR where maintainers asked for *nothing at all* — anything emitted
        # there is a false positive. A PR whose obligations exist but are all unscoreable is
        # a different thing entirely, and calling it a control would turn a measurement gap
        # into an apparent precision failure.
        "control_prs": sorted(
            pr for pr in reviewed
            if by_pr.get(pr, 0) == 0 and ineligible.get(pr, 0) == 0
        ),
    }


def score(audit_dir: Path, run_name: Optional[str] = None) -> Dict[str, Any]:
    """The two signals, over all findings and over published ones.

    `all_findings` answers "what did the agent raise" — the calibration question.
    `published` answers "what would the system have said to a maintainer" — narrower, and
    bounded by the evidence gate rather than by the agent.
    """

    def two_level(path: Path, label: str):
        if not path.is_file():
            return None
        payload = json.loads(path.read_text())
        if not payload.get("scored"):
            return {"scored": False, "reason": payload.get("coverage", {}).get("error")}
        counts = payload["obligation_status_counts"]
        obligations = payload["counts"]["obligations"]
        out = {"obligations": obligations}
        for level in ("issue", "resolution"):
            hit = counts[level]["hit"]
            out[level] = {
                "hit": hit,
                "ambiguous": counts[level]["ambiguous"],
                "miss": counts[level]["miss"],
                "recall": round(hit / obligations, 3) if obligations else None,
            }
        # At these denominators a single flipped verdict moves the headline visibly, and a
        # figure printed without that increment invites an effect-size reading it cannot bear.
        out["one_flip_pp"] = round(100.0 / obligations, 1) if obligations else None
        out["label"] = label
        return out

    # The judge's own eligible set, so the denominator counts only obligations that could
    # actually have been scored.
    eligible_ids = None
    report_path = audit_dir / "semantic_report.json"
    if report_path.is_file():
        payload = json.loads(report_path.read_text())
        eligible_ids = [row["obligation_id"] for row in (payload.get("per_obligation") or [])]
    scope = reachable_obligations(run_name, eligible_ids) if run_name else None

    def rescope(block):
        """Recall against what the run could actually reach, alongside the judge's own."""

        if not block or not block.get("obligations") or not scope:
            return block
        reachable = scope["reachable"]
        block["judge_denominator"] = block.pop("obligations")
        block["reachable_denominator"] = reachable
        for level in ("issue", "resolution"):
            hits = block[level]["hit"]
            block[level]["recall_vs_judge_denominator"] = block[level].pop("recall")
            block[level]["recall"] = round(hits / reachable, 3) if reachable else None
        block["one_flip_pp"] = round(100.0 / reachable, 1) if reachable else None
        return block

    # The publication report has its own schema: it carries `pre_publication` (every merged
    # finding in its final wording) and `post_publication` (the admission=published subset of
    # those same findings and verdicts) rather than the semantic report's shape. Reading it
    # with the wrong keys reported it as unscored, which looked like a missing measurement
    # when the number was sitting there.
    def publication(path: Path):
        if not path.is_file():
            return None
        payload = json.loads(path.read_text())
        obligations = payload.get("obligations")
        out = {"definition": payload.get("definition"),
               "findings": payload.get("findings")}
        for stage in ("pre_publication", "post_publication"):
            block = payload.get(stage) or {}
            row = {"issue_hits": block.get("issue_hits"),
                   "resolution_hits": block.get("resolution_hits"),
                   "judge_denominator": obligations}
            if scope and scope.get("reachable"):
                reachable = scope["reachable"]
                row["reachable_denominator"] = reachable
                for level in ("issue", "resolution"):
                    hits = block.get(f"{level}_hits")
                    row[f"{level}_recall"] = (
                        round(hits / reachable, 3) if hits is not None else None)
            out[stage] = row
        return out

    return {
        "scope": scope,
        "all_findings": rescope(
            two_level(audit_dir / "semantic_report.json", "all findings")),
        "publication": publication(audit_dir / "publication_report.json"),
        # The judge names this `silent_pr_emission`: how much the system said on PRs where
        # maintainers asked for nothing. It is the precision axis the deterministic arm wins
        # on, and it is judge-free — so it is readable even when recall is not.
        "silent_pr_emission": json.loads(
            (audit_dir / "semantic_report.json").read_text()
        ).get("silent_pr_emission") if (audit_dir / "semantic_report.json").is_file() else None,
    }


def blueprint(run_name: str, audit_dir: Optional[Path] = None,
              out: Optional[Path] = None) -> Dict[str, Any]:
    """Render v4's per-PR review visualization over a v5 run.

    v5 writes `findings.jsonl` in the shape the blueprint's `--condition` expects, so no new
    renderer is needed — the reviewed code, the gold, the findings and the judge's verdicts
    all line up. Two seams have to be bridged, and both are one-liners rather than reasons
    to fork a 1600-line renderer:

    * The judge writes `semantic_matches.jsonl`; the blueprint reads `matches.jsonl`. An
      alias is created rather than a copy, so there is exactly one file of record.
    * Output must not land inside a frozen root, or every render fails the FROZEN.lock gate.
      v5 blueprints go to `results/blueprints/pr_review_v5/`.

    Note the release's *treatment* and *executor* are picked up from the blueprint's own
    defaults, so the page shows the deterministic arm's sites and investigations as context.
    Those were not part of a v5 model-arm run and contribute no findings to it.
    """

    from src.datasets.pr_review_v4.blueprint import build_blueprint, write_blueprint
    from src.datasets.pr_review_v4 import paths as v4_paths

    directory = run_dir(run_name)
    agenda_path = directory / "agenda.json"
    if not agenda_path.is_file():
        raise FileNotFoundError(
            f"no agenda at {agenda_path}; the blueprint needs the run's release and PR set."
        )
    agenda = json.loads(agenda_path.read_text())
    release = Path(agenda["release"])
    pr_numbers = sorted({item["pr_number"] for item in agenda.get("proposals", [])})

    judge = None
    if audit_dir and audit_dir.is_dir():
        alias = audit_dir / "matches.jsonl"
        source = audit_dir / "semantic_matches.jsonl"
        if source.is_file() and not alias.exists():
            alias.symlink_to(source.name)
        judge = audit_dir if alias.exists() else None

    out = out or Path("results/blueprints/pr_review_v5") / run_name
    treatment = v4_paths.TREATMENTS / "systematic-opportunities-v3-medium"
    executor = v4_paths.AUDITS / "phase10-medium-executor-v5"
    built = build_blueprint(
        release,
        treatment=treatment if treatment.is_dir() else None,
        executor=executor if executor.is_dir() else None,
        runs=[],
        conditions=[directory],
        judge=judge,
        include_gold=True,
        pr_numbers=pr_numbers or None,
    )
    report = write_blueprint(built, out)
    report["out"] = str(out)
    report["index"] = str(out / "index.html")
    report["prs"] = [bundle.pr_number for bundle in built.prs]
    report["judge_verdicts_included"] = judge is not None
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    routing_parser = sub.add_parser("routing", help="what the lead did")
    routing_parser.add_argument("--run", required=True)
    score_parser = sub.add_parser("score", help="issue and resolution match against gold")
    score_parser.add_argument("--audit", type=Path, required=True)
    score_parser.add_argument("--run", help="the run, so recall is reported against the "
                                            "obligations it could actually reach")
    bp = sub.add_parser("blueprint", help="render the per-PR review as browsable HTML")
    bp.add_argument("--run", required=True)
    bp.add_argument("--audit", type=Path, help="judge output, to overlay gold verdicts")
    bp.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.command == "routing":
        print(json.dumps(routing(args.run), indent=2))
    elif args.command == "score":
        print(json.dumps(score(args.audit, args.run), indent=2))
    else:
        print(json.dumps(blueprint(args.run, args.audit, args.out), indent=2))


if __name__ == "__main__":
    main()
