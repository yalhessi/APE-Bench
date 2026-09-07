"""Read a v5 run: what the lead did, then how well it matched the experts — in that order.

The order is the point. If routing was degenerate — the lead pruned nothing, or ran nothing,
or never touched a context tool — then the delegation mechanism did not engage, and a recall
number is measuring the arms rather than the thing the run was built to test. So `routing`
prints first and `score` refuses to be read as a verdict on delegation without it.

    python -m src.datasets.pr_review_v5.report routing   --run <run_name>
    python -m src.datasets.pr_review_v5.report score     --audit <audit_dir> --run <run_name>
    python -m src.datasets.pr_review_v5.report overlay --run <run_name> [--audit <audit_dir>]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.mathlib_review.paths import RESULTS, run_dir
from .trace import routing_report


def _load_jsonl(path: Path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def retrieval(run_name: str) -> Dict[str, Any]:
    """Which retrieval tool the arms actually reached for, and what came back.

    The question a recall number cannot answer: the arms have three retrieval tools and
    measurably do not use them evenly. Across the thirteen runs in the tree at the time this
    was written, 83% of 2,024 calls went to `declaration_search` -- the one that returns
    nothing but "X is declared in file Y" -- and 47% of those came back empty.

    An empty `declaration_search` is not automatically waste: for a duplication or `api_reuse`
    claim it is the refutation, and the tool's own description says so. The concern is the
    83%. `family_design` spent 50 of its 63 discretionary calls on a name lookup that cannot
    answer a question about a group's shape, and that is what made the retrieval grant
    per-arm. The one run made after that change, `specialist4_rep1`, is the outlier at 45%
    and a 19% empty rate -- the cheapest evidence available that the grant does something.

    The other two tools are at opposite extremes and **`empty_rate` means something different
    for each**, which is why this reports the rate rather than a score:

        declaration_search   1681 calls   47% empty
        precedent_search      240 calls    0% empty
        zulip_search          103 calls   80% empty

    `precedent_search` never comes back empty because it is a dense top-k over 34.6k anchored
    comments: it returns k rows whatever the query, so 0% is "never abstains", not "always
    useful". Reading it as relevance would be reading the retrieval mode as a result.

    `zulip_search` comes back empty four times in five. The store is not the problem -- it
    holds 180k messages and resolves discussion for 10 of 10 eval PRs -- so this is a query,
    gate or coverage question and it is open. It is also only 103 calls across thirteen runs,
    so the arms granted it barely use it.
    """

    rows = _load_jsonl(run_dir(run_name) / "context_trace.jsonl")
    if not rows:
        return {"run": run_name, "calls": 0}

    by_tool: Dict[str, Dict[str, int]] = {}
    for row in rows:
        tool = by_tool.setdefault(
            row.get("tool") or "?", {"calls": 0, "empty": 0, "truncated": 0})
        tool["calls"] += 1
        tool["empty"] += int(not row.get("result_count"))
        tool["truncated"] += int(bool(row.get("truncated")))

    total = len(rows)
    for stats in by_tool.values():
        stats["share"] = round(stats["calls"] / total, 3)
        stats["empty_rate"] = round(stats["empty"] / stats["calls"], 3)

    by_arm: Dict[str, Dict[str, int]] = {}
    for row in rows:
        arm = str(row.get("invocation_id") or "?").rsplit("#", 1)[-1]
        entry = by_arm.setdefault(arm, {"calls": 0, "declaration_search": 0})
        entry["calls"] += 1
        entry["declaration_search"] += int(row.get("tool") == "declaration_search")

    return {
        "run": run_name,
        "calls": total,
        "by_tool": dict(sorted(by_tool.items())),
        # Per arm, because the grant is per arm and this is how you see whether an arm is
        # using what it was given.
        "by_arm": dict(sorted(by_arm.items())),
        # Rows written before gates were recorded have no `gate`; a modern run has one on
        # every row, and a row without one is a tool that was added without declaring how it
        # is bounded.
        "calls_without_a_recorded_gate": sum(1 for row in rows if not row.get("gate")),
    }


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
    # An obligation carrying no `change_ids` has no anchor, and anchor-tier pairing joins on
    # change_id — so no finding can ever be paired with it, however good the review. That is
    # a property of the gold row, not of the agent, and counting it in the denominator makes
    # a data gap read as a miss. Exactly one exists in dev-medium (PR 33145, "swap the sides
    # of the iSup/iInf equalities"). Reported, never edited: the release is an input.
    anchorless: Dict[int, int] = {}
    # Rows the release's own artifacts contradict — an ask its source comment does not make,
    # or an outcome its own evidence refutes. Named in `obligation_exclusions` with the
    # evidence, applied here, and reported below so they are never silently dropped.
    from .obligation_exclusions import excluded_ids, exclusion_report

    excluded = excluded_ids()
    audited: Dict[int, int] = {}
    for row in _load_jsonl(judgments):
        pr = row.get("pr_number")
        if pr not in reviewed:
            continue
        for obligation in row.get("obligations") or []:
            oid = obligation.get("obligation_id")
            if eligible is not None and oid not in eligible:
                ineligible[pr] = ineligible.get(pr, 0) + 1
                continue
            if not (obligation.get("change_ids") or []):
                anchorless[pr] = anchorless.get(pr, 0) + 1
                continue
            if oid in excluded:
                audited[pr] = audited.get(pr, 0) + 1
                continue
            by_pr[pr] = by_pr.get(pr, 0) + 1
    return {
        "unscoreable_obligations_by_pr": dict(sorted(ineligible.items())),
        "anchorless_obligations_by_pr": dict(sorted(anchorless.items())),
        "audit_excluded_by_pr": dict(sorted(audited.items())),
        "audit_exclusions": exclusion_report(),
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


def contamination(release: Path) -> Dict[str, Any]:
    """Do any arm instructions quote this release's gold?

    Lives here, on the evaluation side, and deliberately **not** in the runner: the
    generation path must never read gold — that isolation is the single structural defence
    `contracts.assert_gold_free` exists to protect, and a pre-run check that opened
    `judgments.jsonl` inside `run()` would breach it in order to enforce it. So this is a
    gate an operator runs before spending, not a step inside the pipeline.

    It catches what `assert_gold_free` structurally cannot: that check sweeps the sealed
    agenda, and the agenda carries prompt *hashes* only. Three exact heldout answers reached
    the arms' instructions through that blind spot.
    """

    from src.datasets.pr_review_v4.contracts import prompt_leaks
    from src.datasets.pr_review_v4.render_focused import (
        SUBMISSION_CONTRACT, focused_system_prompt,
    )
    from src.datasets.pr_review_v5.arms import specs_by_arm_id

    gold: List[str] = []
    path = release / "gold/judgments.jsonl"
    if path.is_file():
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            for obligation in (json.loads(line).get("obligations") or []):
                for field in ("claim", "requested_change", "resolution_criteria"):
                    if obligation.get(field):
                        gold.append(str(obligation[field]))

    instructions = {"submission_contract": SUBMISSION_CONTRACT}
    for arm, spec in specs_by_arm_id().items():
        instructions[arm] = focused_system_prompt(spec)
    leaks = {name: found for name, found in
             ((name, prompt_leaks(text, gold)) for name, text in sorted(instructions.items()))
             if found}
    return {
        "release": str(release),
        "gold_strings": len(gold),
        "instructions_checked": len(instructions),
        "clean": not leaks,
        "leaks": leaks,
    }


def admission(run_name: str) -> Dict[str, Any]:
    """Which gate ran, what it decided, and what the lead removed before it.

    Assembled from the run's own `finalization_report.json` rather than recomputed, so it
    cannot disagree with the admissions actually written.
    """

    path = run_dir(run_name) / "finalization_report.json"
    if not path.is_file():
        return {"available": False}
    payload = json.loads(path.read_text())
    synthesis = payload.get("lead_synthesis") or {}
    return {
        "available": True,
        "gate": payload.get("generalist_evidence_gate"),
        "findings": payload.get("inputs"),
        "published": payload.get("issues_published"),
        "published_by_concern": payload.get("published_by_concern"),
        "by_evidence_tier": payload.get("by_evidence_tier"),
        "conflicts": payload.get("conflicts"),
        "specialists_dropped_unverified": payload.get(
            "candidates_specialist_dropped_unverified"),
        "evidence": payload.get("evidence"),
        # Subtractive by construction, so `candidates_out <= candidates_in` always holds;
        # `unmatched` is the one that matters, because an assessment naming no candidate
        # means the lead was addressing claims it could not see.
        "lead_synthesis": {
            "assessments": synthesis.get("assessments", 0),
            "by_verdict": synthesis.get("by_verdict", {}),
            "dropped": synthesis.get("candidates_dropped", 0),
            "absorbed": synthesis.get("candidates_absorbed", 0),
            "unmatched": len(synthesis.get("unmatched") or []),
        },
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
        # Read before any recall number. A publication rate is uninterpretable without the
        # regime that produced it: under a `closed` gate nothing was ever asked to support
        # a claim, so `diagnostic` says only that no chain ran — which is how eight runs
        # reported publication rates as if they were strictness results.
        "admission": admission(run_name) if run_name else None,
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


def overlay(run_name: str, audit_dir: Optional[Path] = None,
              out: Optional[Path] = None) -> Dict[str, Any]:
    """Render v4's per-PR review visualization over a v5 run.

    v5 writes `findings.jsonl` in the shape the overlay's `--condition` expects, so no new
    renderer is needed — the reviewed code, the gold, the findings and the judge's verdicts
    all line up. Two seams have to be bridged, and both are one-liners rather than reasons
    to fork a 1600-line renderer:

    * The judge writes `semantic_matches.jsonl`; the overlay reads `matches.jsonl`. An
      alias is created rather than a copy, so there is exactly one file of record.
    * Output must not land inside a frozen root, or every render fails the FROZEN.lock gate.
      v5 overlays go to `results/overlays/pr_review_v5/`.

    Note the release's *treatment* and *executor* are picked up from the overlay's own
    defaults, so the page shows the deterministic arm's sites and investigations as context.
    Those were not part of a v5 model-arm run and contribute no findings to it.
    """

    from src.datasets.pr_review_v4.review_overlay import build_overlay, write_overlay
    from src.datasets.pr_review_v4 import paths as v4_paths

    directory = run_dir(run_name)
    agenda_path = directory / "agenda.json"
    if not agenda_path.is_file():
        raise FileNotFoundError(
            f"no agenda at {agenda_path}; the overlay needs the run's release and PR set."
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

    out = out or Path("results/overlays/pr_review_v5") / run_name
    treatment = v4_paths.TREATMENTS / "systematic-opportunities-v3-medium"
    executor = v4_paths.AUDITS / "phase10-medium-executor-v5"
    built = build_overlay(
        release,
        treatment=treatment if treatment.is_dir() else None,
        executor=executor if executor.is_dir() else None,
        runs=[],
        conditions=[directory],
        judge=judge,
        include_gold=True,
        pr_numbers=pr_numbers or None,
    )
    report = write_overlay(built, out)
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
    cp = sub.add_parser(
        "contamination", help="do any arm instructions quote gold? run before spending")
    cp.add_argument("--release", type=Path, required=True)
    bp = sub.add_parser("overlay", help="render the per-PR review as browsable HTML")
    bp.add_argument("--run", required=True)
    bp.add_argument("--audit", type=Path, help="judge output, to overlay gold verdicts")
    bp.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.command == "contamination":
        print(json.dumps(contamination(args.release), indent=2))
        raise SystemExit(0 if contamination(args.release)["clean"] else 1)
    if args.command == "routing":
        print(json.dumps(routing(args.run), indent=2))
    elif args.command == "score":
        print(json.dumps(score(args.audit, args.run), indent=2))
    else:
        print(json.dumps(overlay(args.run, args.audit, args.out), indent=2))


if __name__ == "__main__":
    main()
