"""Read a v5 run: what the lead did, then how well it matched the experts — in that order.

The order is the point. If routing was degenerate — the lead pruned nothing, or ran nothing,
or never touched a context tool — then the delegation mechanism did not engage, and a recall
number is measuring the arms rather than the thing the run was built to test. So `routing`
prints first and `score` refuses to be read as a verdict on delegation without it.

    python -m src.mathlib_review.analysis.report routing   --run <run_name>
    python -m src.mathlib_review.analysis.report score     --audit <audit_dir> --run <run_name>
    python -m src.mathlib_review.analysis.report overlay --run <run_name> [--audit <audit_dir>]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.mathlib_review.io import jsonl_rows
from src.mathlib_review.paths import RESULTS, run_dir
from src.mathlib_review.review.trace import routing_report




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

    rows = jsonl_rows(run_dir(run_name) / "context_trace.jsonl")
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
        # The other half of the same question. `by_arm` says what an arm looked at; this says
        # what it concluded when it reported nothing, which on the held-out run was 81% of
        # specialist invocations. Before `abstention` existed the only way to answer this was
        # to reconstruct each session's last tool result from the transcripts, and three
        # successive attempts at that were wrong before one was right.
        "abstentions": _abstentions(run_name),
    }


def _abstentions(run_name: str) -> Dict[str, Any]:
    """Per arm, why it submitted nothing.

    `unstated` counts rows written before the reason was required, or by a routing mode that
    does not produce one. It is reported rather than dropped: an arm whose silence is
    unexplained is exactly the thing this field exists to make visible, so hiding it in a
    denominator would reproduce the problem in the report that is supposed to expose it.
    """

    by_arm: Dict[str, Dict[str, int]] = {}
    for row in jsonl_rows(run_dir(run_name) / "arm_responses.jsonl"):
        if row.get("candidates"):
            continue
        arm = row.get("arm_id") or str(row.get("invocation_id") or "?").rsplit("#", 1)[-1]
        reason = (row.get("abstention") or {}).get("reason") or "unstated"
        entry = by_arm.setdefault(arm, {})
        entry[reason] = entry.get(reason, 0) + 1
    return dict(sorted(by_arm.items()))


def routing(run_name: str) -> Dict[str, Any]:
    directory = run_dir(run_name)
    delegations = jsonl_rows(directory / "delegations.jsonl")
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


def scoped_obligations(run_name: str,
                       eligible_obligation_ids: Optional[Iterable[str]] = None,
                       ) -> Optional[Dict[str, Any]]:
    """How many gold obligations this run could possibly have hit, by which PRs it reviewed.

    **Not the same "reachable" as `analysis/reachability.py`**, which asks whether the
    publication mechanism can express an obligation at all. Both were called `reachable` and
    both appeared in this report: 17 here and 2 there, for the same run. A reader comparing
    them is comparing "in the PRs we looked at" with "a compile could settle it".

    The judge counts obligations across the whole release — 40 for dev-medium — regardless
    of which PRs the run actually reviewed. For a 4-PR run that denominator includes nine
    PRs the agent never saw, so the printed recall understates it by more than a factor of
    two. Scoping it is an evaluation-time question, so reading gold here is legitimate; the
    generation side never touches it.
    """

    from src.mathlib_review.run_state import MissingArtifact, StageInput

    try:
        stage = StageInput.at(run_dir(run_name), run_name=run_name, allow_partial=True)
        agenda = json.loads(stage.path("agenda").read_text())
    except (MissingArtifact, FileNotFoundError):
        return None
    reviewed = {item["pr_number"] for item in agenda.get("proposals", [])}
    if stage.release is None:
        return None
    judgments = stage.release / "gold/judgments.jsonl"
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
    from src.mathlib_review.analysis.obligation_exclusions import excluded_ids, exclusion_report

    excluded = excluded_ids()
    audited: Dict[int, int] = {}
    for row in jsonl_rows(judgments):
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
        # In scope because the run reviewed the PR, which is a different question from
        # whether the mechanism can publish it. See `analysis/reachability.py`.
        "in_scope": sum(by_pr.values()),
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

    from src.mathlib_review.release.contracts import prompt_leaks
    from src.mathlib_review.agenda.render_focused import (
        SUBMISSION_CONTRACT, focused_system_prompt,
    )
    from src.mathlib_review.agenda.arms import specs_by_arm_id

    gold: List[str] = []
    path = release / "gold/judgments.jsonl"
    if path.is_file():
        for row in jsonl_rows(path):
            for obligation in (row.get("obligations") or []):
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

    audit_dir = Path(audit_dir)
    if not (audit_dir / "semantic_report.json").is_file():
        raise SystemExit(
            f"no judge output at {audit_dir}. `report score` reads what the judge wrote; "
            "if the directory is missing, the judge has not run.\n"
            "  python -m src.mathlib_review.review.cli judge --config <judge config> "
            f"--of <run_name> --execute\n"
            "Note `--execute`: without it the judge resolves its paths and stops."
        )

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
    scope = scoped_obligations(run_name, eligible_ids) if run_name else None

    def rescope(block):
        """Recall against what the run could actually reach, alongside the judge's own."""

        if not block or not block.get("obligations") or not scope:
            return block
        reachable = scope["in_scope"]
        block["judge_denominator"] = block.pop("obligations")
        block["scoped_denominator"] = reachable
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
            if scope and scope.get("in_scope"):
                reachable = scope["in_scope"]
                row["scoped_denominator"] = reachable
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

    * The judge writes `semantic_matches.jsonl` and v4 audits hold `matches.jsonl`; the
      renderer reads whichever it finds, in that order. It used to be given an alias planted
      inside the audit directory -- a read-only report writing into another stage's output,
      which is the one thing an immutable artifact tree must not allow.
    * Output must not land inside a frozen root, or every render fails the FROZEN.lock gate.
      v5 overlays go to `results/overlays/pr_review_v5/`.

    Note the release's *treatment* and *executor* are picked up from the overlay's own
    defaults, so the page shows the deterministic arm's sites and investigations as context.
    Those were not part of a v5 model-arm run and contribute no findings to it.
    """

    from src.mathlib_review.analysis.review_overlay import build_overlay, write_overlay
    from src.mathlib_review.analysis.review_overlay import paths as v4_paths

    from src.mathlib_review.run_state import StageInput

    # Read forensically: an overlay of a partial run is exactly what someone wants to look at
    # when a run went wrong, and the page is not a measurement.
    stage = StageInput.at(run_dir(run_name), run_name=run_name, allow_partial=True)
    directory = stage.run_dir
    agenda = json.loads(stage.path("agenda").read_text())
    release = stage.release
    pr_numbers = sorted({item["pr_number"] for item in agenda.get("proposals", [])})

    judge = audit_dir if audit_dir and audit_dir.is_dir() else None

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


def conditions(runs: Dict[str, Any], release: Optional[Path] = None) -> Dict[str, Any]:
    """Two or more judged runs on one denominator: the funnel, the union, the exclusive sets.

    The first production caller of `analysis.reports.compare_conditions`, which has implemented
    the mean / union / stable protocol since Phase 9 and been called only by its tests. Phase
    9's central finding was that two arms tied on mean recall while recovering nearly disjoint
    obligations, so this reports the sets and not just the rates -- and at one repetition the
    sets are the only honest output: `stable` is undefined and a rate delta at these
    denominators is inside the judge's own disagreement with itself.

    `runs` is `{label: run_name}` or `{label: [run_name, ...]}` -- several runs under one label
    are repetitions of one condition, and are what turns the funnel into mean / union / stable
    and makes `hit_frequency` say how many of N repetitions found each obligation. Audits are
    derived from run names the way `judge --of` derives them, so a condition cannot be paired
    with an audit that scored a different run.

    Refuses to compare across judges: `judge_identity` hashes the rubric, model, sampling and
    decode budgets, and R0 found two judge arms disagreeing on 4 of 18 pairs from decode
    budgets alone. Refuses a denominator mismatch: every condition must have been scored over
    the same obligations, or the comparison is between two questions.

    With `release`, adds the two gold-light exhibits that motivate the design rather than
    score it: each condition's *attention* -- the concern-family distribution of what it raised
    -- against the maintainers', and its redundancy, the number of times it wrote up one change
    target. Neither needs a repetition to be a fact about a run.
    """

    from src.mathlib_review.analysis.reports import compare_conditions, rep_summary
    from src.mathlib_review.judge.runner import derive_from_run

    reps: Dict[str, List[str]] = {
        label: ([names] if isinstance(names, str) else list(names))
        for label, names in runs.items()}
    loaded: Dict[str, List[Dict[str, Any]]] = {}
    for label, names in reps.items():
        loaded[label] = []
        for run_name in names:
            # Derived the way `judge --of` derives it, so a condition cannot be paired with an
            # audit that scored a different run.
            audit = derive_from_run(run_name)["out_dir"] / "semantic_report.json"
            if not audit.is_file():
                raise SystemExit(
                    f"{label}: no judge output at {audit}. Judge the run first:\n"
                    f"  python -m src.mathlib_review.review.cli judge --config <judge config> "
                    f"--of {run_name} --execute")
            payload = json.loads(audit.read_text())
            if not payload.get("scored", True):
                raise SystemExit(
                    f"{label}: {run_name} is not scored "
                    f"({payload.get('coverage', {}).get('error')}); nothing to compare")
            loaded[label].append(payload)

    identities = {f"{label}[{i}]": p.get("judge_identity")
                  for label, ps in loaded.items() for i, p in enumerate(ps)}
    if len(set(identities.values())) > 1:
        raise SystemExit(
            f"conditions were judged by different instruments: {identities}. "
            "judge_identity covers the rubric, model, sampling and decode budgets; a verdict "
            "under one is not comparable to a verdict under another.")

    denominators = {
        f"{label}[{i}]": sorted(row["obligation_id"] for row in p.get("per_obligation") or [])
        for label, ps in loaded.items() for i, p in enumerate(ps)}
    reference = next(iter(denominators.values()))
    for label, ids in denominators.items():
        if ids != reference:
            diff = sorted(set(ids) ^ set(reference))
            raise SystemExit(
                f"{label} was scored over a different denominator ({len(ids)} vs "
                f"{len(reference)} obligations; symmetric difference {len(diff)}). The judge "
                "scopes obligations to the PRs a run reviewed, so this means the runs did not "
                "review the same PRs, and a recall from one is not a recall from the other.")

    def hits(payload, level):
        rows = payload.get("per_obligation") or []
        if level == "location":
            return [r["obligation_id"] for r in rows if r.get("location_hit")]
        return [r["obligation_id"] for r in rows if r.get(f"{level}_status") == "hit"]

    levels: Dict[str, Any] = {}
    for level in ("location", "issue", "resolution"):
        summaries = {label: rep_summary([hits(p, level) for p in ps], reference)
                     for label, ps in loaded.items()}
        levels[level] = compare_conditions(summaries)

    n = len(reference)
    # With one repetition per label the three coincide and `hit` is the run's count. With
    # several, `hit` is the per-repetition mean and the union / stable figures sit beside it
    # -- a condition that finds an obligation in 1 of 10 runs and one that finds it in 10 of
    # 10 have the same union and very different means, and the talk needs to know which.
    funnel = {
        label: {
            level: {
                "hit": round(sum(c["per_repetition_hits"]) / c["repetitions"], 2)
                if c["repetitions"] else None,
                "recall": round(c["mean_recall"], 3) if c["mean_recall"] is not None else None,
                "union_recall": round(c["union_recall"], 3)
                if c["union_recall"] is not None else None,
                "stable_recall": round(c["stable_recall"], 3)
                if c["stable_recall"] is not None else None,
                "per_repetition_hits": c["per_repetition_hits"],
            }
            for level in ("location", "issue", "resolution")
            for c in [levels[level]["conditions"][label]]
        }
        for label in loaded}

    out: Dict[str, Any] = {
        "denominator": n,
        # A single flipped verdict moves the headline by this much; printed so a rate is never
        # read at a precision it cannot bear.
        "one_flip_pp": round(100.0 / n, 1) if n else None,
        "judge_identity": next(iter(identities.values())),
        "repetitions": {label: len(ps) for label, ps in loaded.items()},
        "runs": reps,
        "funnel": funnel,
        "by_level": levels,
        # The only precision signal there is. NOT a false-finding rate: a control PR is one
        # where maintainers asked for nothing, and emission there is counted, not judged.
        # One entry per repetition, never pooled: the reader can see the spread.
        "control_emission": {label: [p.get("silent_pr_emission") for p in ps]
                             for label, ps in loaded.items()},
    }

    manifests: Dict[str, List[Dict[str, Any]]] = {}
    for label, names in reps.items():
        for run_name in names:
            path = run_dir(run_name) / "run_manifest.json"
            if path.is_file():
                m = json.loads(path.read_text())
                manifests.setdefault(label, []).append({
                    "run": run_name,
                    "billed": (m.get("usage") or {}).get("billed"),
                    "nominal": (m.get("usage") or {}).get("nominal"),
                    "completion_status": m.get("completion_status"),
                    "routing_mode": m.get("routing_mode")})
    if manifests:
        out["cost"] = manifests

    if release is not None:
        # The per-run exhibits are computed on the first repetition of each label. They are
        # facts about a run, and the first is as representative as any; a per-rep spread of
        # attention or examination is a separate question from the one this block answers.
        first = {label: names[0] for label, names in reps.items()}
        out["attention"] = _attention_vs_maintainers(first, Path(release), reference)
        out["redundancy"] = {label: _redundancy(run_name) for label, run_name in first.items()}
        out["examination"] = {label: _examination(run_name, Path(release))
                              for label, run_name in first.items()}
    return out


def _attention_vs_maintainers(runs: Dict[str, str], release: Path,
                              scoped_obligation_ids: Iterable[str]) -> Dict[str, Any]:
    """What each condition raised, by concern family, against what maintainers raised.

    Gold-light: uses the judgments' concern labels weighted by eligible obligations, not
    per-obligation matching, so it is a fact about a single run. `documentation` and `docs`
    are bridged through `CONCERN_ALIASES`, the one-word mismatch that made the docs arm
    unmeasurable for its whole life.
    """

    from collections import Counter

    from src.mathlib_review.analysis.benches import CONCERN_ALIASES

    def canon(name: str) -> str:
        return CONCERN_ALIASES.get(name, name)

    scoped = set(scoped_obligation_ids)
    gold: Counter = Counter()
    for node in jsonl_rows(release / "gold/judgments.jsonl"):
        weight = sum(1 for ob in node.get("obligations") or []
                     if ob.get("obligation_id") in scoped)
        if not weight:
            continue
        for label in node.get("concern_labels") or ["(none)"]:
            gold[canon(label)] += weight

    def share(counter: Counter) -> Dict[str, float]:
        total = sum(counter.values())
        return {k: round(v / total, 3) for k, v in counter.most_common()} if total else {}

    out: Dict[str, Any] = {"maintainers": {"n": sum(gold.values()), "share": share(gold)}}
    gold_share = share(gold)
    for label, run_name in runs.items():
        path = run_dir(run_name) / "findings.jsonl"
        if not path.is_file():
            continue
        raised: Counter = Counter(canon(r["concern_family"]) for r in jsonl_rows(path))
        raised_share = share(raised)
        keys = set(gold_share) | set(raised_share)
        # Half the L1 distance between the two distributions: 0 is identical attention, 1 is
        # disjoint. One number for "does it look at what maintainers look at".
        distance = round(sum(abs(gold_share.get(k, 0.0) - raised_share.get(k, 0.0))
                             for k in keys) / 2, 3)
        out[label] = {"n": sum(raised.values()), "share": raised_share,
                      "distance_from_maintainers": distance}
    return out


def _redundancy(run_name: str) -> Optional[Dict[str, Any]]:
    """How many times a run wrote up one change target.

    On the control PR the lead emitted 8 findings for 3 distinct observations across 2
    targets, restating one complaint under three concern vocabularies; the digest did not
    collapse them. That is a cost of decomposition, and it has to be measured beside recall or
    a condition that says the same thing four times reads as four times as thorough.
    """

    from collections import Counter

    path = run_dir(run_name) / "findings.jsonl"
    if not path.is_file():
        return None
    rows = list(jsonl_rows(path))
    per_target = Counter((r["pr_number"], r["primary_change_id"]) for r in rows)
    families = Counter(
        len({r["concern_family"] for r in rows
             if (r["pr_number"], r["primary_change_id"]) == target})
        for target in per_target)
    return {
        "findings": len(rows),
        "targets": len(per_target),
        "findings_per_target": round(len(rows) / len(per_target), 2) if per_target else None,
        "targets_written_up_more_than_once": sum(1 for v in per_target.values() if v > 1),
        "families_per_target": {str(k): v for k, v in sorted(families.items())},
    }


def _examination(run_name: str, release: Path) -> Optional[Dict[str, Any]]:
    """What a condition actually looked at, per PR: the depth exhibit.

    The design's motivating claim is that one model call does not examine a PR deeply -- it
    reads a few things that are easy to examine and stops. That is a claim about *attention*,
    and it is checkable from the transcript without gold: which files were read and over which
    lines, which declarations were searched for, and how much of the PR's change surface that
    touched. A change target counts as examined if a `file_read` span on its path overlaps its
    span, or its name appears in a search. Emitting a finding on it is not required -- the
    question is what was looked at, not what was said.

    Measured the same way for every condition, from transcripts, so the scheduled design's
    coverage is observed rather than asserted from its floor. Reported beside the PR's diff
    size and file count, because the claim only bites on large PRs: on a 912-character,
    single-file PR every condition reads everything, and 33294 is 46k characters over 11 files.
    """

    from collections import defaultdict

    from ape.tasks.lean_tasks.formal_math.review.candidates import normalize_proposed_edit_path
    from src.mathlib_review.analysis.trajectory import extract
    from src.mathlib_review.schema import ChangeGraph

    extracted = extract(run_name)
    if not extracted.get("present"):
        return None

    reads: Dict[int, List[tuple]] = defaultdict(list)       # pr -> (path, start, end)
    searched: Dict[int, set] = defaultdict(set)              # pr -> identifiers / patterns
    tools: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for pr_key, turns in (extracted.get("turns_by_pr") or {}).items():
        try:
            pr = int(pr_key)
        except (TypeError, ValueError):
            continue
        for turn in turns:
            for item in turn.items:
                if item.get("t") != "use":
                    continue
                name = item.get("name")
                tools[pr][name] += 1
                try:
                    payload = json.loads(item.get("v") or "{}")
                except json.JSONDecodeError:
                    payload = {}
                if not isinstance(payload, dict):
                    continue
                if name == "file_read":
                    path = normalize_proposed_edit_path(
                        payload.get("file_path") or payload.get("path") or "")
                    span = payload.get("line_range") or [None, None]
                    start = span[0] if isinstance(span, list) and span else None
                    end = span[1] if isinstance(span, list) and len(span) > 1 else None
                    reads[pr].append((path, start, end))
                elif name in ("declaration_search", "content_search", "precedent_search"):
                    for key in ("identifier", "content_pattern", "query", "declaration"):
                        if payload.get(key):
                            searched[pr].add(str(payload[key]))

    episodes = {row["pr_number"]: row for row in jsonl_rows(release / "input/episodes.jsonl")}
    out: Dict[str, Any] = {}
    for row in jsonl_rows(release / "derived/change_graphs.jsonl"):
        graph = ChangeGraph.model_validate(row)
        pr = graph.pr_number
        if pr not in tools and pr not in reads:
            continue
        entities = {e.entity_id: e for e in graph.entities}
        ranges = {r.range_id: r for r in graph.changed_ranges}
        examined = 0
        for target in graph.targets:
            spans = [(entities[e].span.line_start, entities[e].span.line_end)
                     for e in target.reviewed_entity_ids
                     if e in entities and entities[e].span]
            if not spans:
                spans = [(ranges[r].reviewed_span.line_start, ranges[r].reviewed_span.line_end)
                         for r in target.changed_range_ids
                         if r in ranges and ranges[r].reviewed_span]
            by_read = any(
                path == target.path and (
                    start is None or end is None
                    or any(s <= end and start <= t for s, t in spans))
                for path, start, end in reads.get(pr, []))
            short = (target.declaration_name or "").rsplit(".", 1)[-1]
            by_search = bool(short) and any(short in q for q in searched.get(pr, ()))
            examined += bool(by_read or by_search)
        episode = episodes.get(pr) or {}
        out[str(pr)] = {
            "targets_total": len(graph.targets),
            "targets_examined": examined,
            "examined_share": round(examined / len(graph.targets), 3) if graph.targets else None,
            "file_reads": len(reads.get(pr, [])),
            "distinct_files_read": len({path for path, _s, _e in reads.get(pr, [])}),
            "searches": len(searched.get(pr, ())),
            "tool_calls": dict(sorted(tools.get(pr, {}).items())),
            "diff_chars": len(episode.get("diff") or ""),
            "changed_files": len(episode.get("changed_files") or []),
        }
    return out


def stages(run_name: str) -> Dict[str, Any]:
    """What has happened to this run, and what the artifacts say happened.

    Two halves, and the second is the point. The ledger says what each stage recorded; the
    reconciliation says whether the run directory agrees with it. They can disagree in exactly
    the ways a crash produces -- a manifest with no row means a run closed and died before
    recording itself, an audit on disk with no row means it was judged before rows existed (or
    by hand) -- and naming those is more useful than a ledger that pretends to be complete.

    Read-only, and free.
    """

    from src.mathlib_review.judge.runner import derive_from_run
    from src.mathlib_review.paths import AUDITS
    from src.mathlib_review.run_state import RUN_ARTIFACTS, ledger, state_of

    directory = run_dir(run_name)
    rows = ledger(directory)
    manifest_path = directory / RUN_ARTIFACTS["run_manifest"].filename
    manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else None

    audits_on_disk = sorted(
        str(path) for path in AUDITS.glob(f"{derive_from_run(run_name)['out_dir'].name}*")
        if (path / "semantic_report.json").is_file())
    audits_in_ledger = {row.get("produced", {}).get("out_dir")
                        for row in rows if row.get("stage") == "judge"}

    return {
        "run": run_name,
        "state": state_of(directory).value,
        "completion_status": (manifest or {}).get("completion_status"),
        "stages": [
            {key: row.get(key) for key in
             ("stage", "node", "pipeline", "transition", "forensic", "written_at",
              "git_commit", "git_tree_state", "identity")}
            for row in rows
        ],
        "forensic_rows": [row.get("stage") for row in rows if row.get("forensic")],
        "reconciliation": {
            # A run that closed and died before recording itself. The artifacts are intact and
            # the row is not; that is worth saying rather than papering over.
            "ledger_missing_run_row": bool(
                manifest and not any(row.get("stage") == "run" for row in rows)),
            "audits_without_a_row": [
                item for item in audits_on_disk if item not in audits_in_ledger],
            "rows_without_an_audit": sorted(
                item for item in audits_in_ledger
                if item and not (Path(item) / "semantic_report.json").is_file()),
        },
    }


#: The coarse split, and it is miss-decomposition's, unchanged since June 2026.
#:
#: `UNTOUCHED` is pure geometry and judge-independent: nothing the system emitted anchors at
#: this obligation's sites, so no verdict can make it a hit. That is the number the 2026-06
#: analysis called the robust one, and it is computable before any judge runs.
#:
#: `LOCATED_MISS` is the selection gap the whole project turns on -- something *was* emitted
#: there and it was about something else. Splitting it from `COVERED` needs the judge, which is
#: why a bucket report without an audit reports `LOCATED_UNJUDGED` rather than guessing.
COARSE = ("UNTOUCHED", "LOCATED_MISS", "LOCATED_UNJUDGED", "COVERED")

#: Why an obligation sits where it does, one rung finer, in the overlay's own vocabulary.
#: Deliberately not a new taxonomy: `review_overlay.STATES` already names these states for the
#: per-target page, and a second vocabulary for the same facts is how `documentation` and
#: `docs` made an arm unmeasurable for its whole life.
FINE = ("unscheduled", "pruned", "unavailable", "silent", "candidate", "finding")


def _context_quality(calls) -> str:
    """What retrieval this job actually got back: `none`, `empty`, `partial` or `ok`.

    An ANNOTATION, never a bucket. It answers "did the arm have anything to work from", which
    is a different question from "what did the arm do", and folding it into the ladder would
    make a tooling failure and a judgement call the same row.

    It is also incomplete by construction and says so: three tools write no trace row at all
    (`proof_profile` on every path, `naming_norm` on three failure returns), so `none` means
    "no row", not "no call". Tool refusals are not recorded anywhere, so they are not offered
    as a value -- `docs/todo/evidence-tiers-and-traces.md` §4.
    """

    calls = list(calls or [])
    if not calls:
        return "none"
    empty = sum(1 for call in calls if not call.get("result_count"))
    if empty == len(calls):
        return "empty"
    return "partial" if empty else "ok"


def _cell_state(job, anchored_findings) -> str:
    """What one scheduled (arm, site) pair did, on the overlay's ladder."""

    if job.disposition == "pruned":
        return "pruned"
    if job.status != "success":
        # Ran and did not come back: a coverage gap, not a silence. A failed mandatory job
        # counted as coverage once, and the run was scored as complete over work nobody did.
        return "unavailable"
    if not anchored_findings:
        return "silent"
    if any(item.get("admission") == "published" and item.get("channels")
           for item in anchored_findings):
        return "finding"
    return "candidate"


def buckets(runs, audit=False, replay: Optional[str] = None) -> Dict[str, Any]:
    """Why each gold obligation ended where it did, and what became of every finding.

    The join that has been done by hand in a scratchpad every time someone asked "why did we
    miss this". It reads the agenda (was anything scheduled here), the delegation ledger (did
    the lead decline it, did the job run), the arm responses (did the arm abstain, and saying
    what), the context trace (did its retrieval return anything), `findings.jsonl` (was a claim
    emitted, and did the gate publish it) and, when there is one, the judge's own report.

    Two levels, and the coarse one is miss-decomposition's: `UNTOUCHED` is judge-independent
    geometry, and the `COVERED` / `LOCATED_MISS` split needs a verdict. Without an audit the
    located set is reported as `LOCATED_UNJUDGED` rather than guessed at.

    The fine level is `review_overlay.STATES`, not a new vocabulary -- a second set of words
    for the same facts is how `documentation` and `docs` made an arm unmeasurable for its whole
    life. Everything else is an annotation beside the bucket: the abstention's own reason, the
    retrieval it got, the gate's verdict, the judge's pairing, and whether a replay found the
    decision stable. Those answer different questions and must not be folded into one ladder.

    Several runs make the per-finding half say `reps_with_key`: how many of them reproduced a
    claim. It is reported and not ranked on -- cross-rep agreement separates hits in-sample and
    is recorded as provisional (`docs/todo/selection-signal.md`).

    Costs nothing and calls no model.
    """

    from src.mathlib_review.agenda.registry import expected_concerns
    from src.mathlib_review.analysis.benches import gold_labels_for
    from src.mathlib_review.analysis.delegation_view import load_lead_views
    from src.mathlib_review.analysis.obligation_exclusions import excluded_ids
    from src.mathlib_review.analysis.review_overlay import deepest
    from src.mathlib_review.judge.runner import derive_from_run
    from src.mathlib_review.review.merge import finding_key
    from src.mathlib_review.run_state import StageInput

    # An arm's remit as gold spells it. Computed once: `gold_labels_for` bridges the two
    # concern vocabularies, and asking it per cell would call it a few thousand times.
    remit = {arm: gold_labels_for(sorted(families))
             for arm, families in expected_concerns().items()}

    run_names = [runs] if isinstance(runs, str) else list(runs)
    per_run: Dict[str, Any] = {}
    key_runs: Dict[str, set] = {}

    for run_name in run_names:
        stage = StageInput.of(
            run_name, audit=audit,
            require=("agenda", "delegations", "arm_responses", "findings"),
            allow_partial=True)
        agenda = json.loads(stage.path("agenda").read_text())
        reviewed = sorted({item["pr_number"] for item in agenda.get("proposals", [])})
        findings = jsonl_rows(stage.path("findings"))
        responses = {row["invocation_id"]: row
                     for row in jsonl_rows(stage.path("arm_responses"))}
        views = load_lead_views(stage.run_dir)
        jobs = [job for view in views.values() for job in view.delegations]

        # Findings by the change target they anchor to, which is the join anchor-tier pairing
        # makes and therefore the only one an obligation can be reached through.
        by_change: Dict[str, List[Dict[str, Any]]] = {}
        for finding in findings:
            for change_id in finding.get("change_ids") or []:
                by_change.setdefault(change_id, []).append(finding)

        verdict_by_obligation: Dict[str, str] = {}
        paired_candidates: set = set()
        matched_candidates: set = set()
        if audit:
            report = json.loads(stage.audit_path("semantic_report").read_text())
            verdict_by_obligation = {
                row["obligation_id"]: row.get("issue_status")
                for row in report.get("per_obligation") or []}
            for pair in jsonl_rows(stage.audit_path("semantic_pairs")):
                if pair.get("role") == "observed":
                    paired_candidates.add(pair["candidate_id"])
            for match in jsonl_rows(stage.audit_path("semantic_matches")):
                if match.get("role") == "observed" and match.get("issue_match"):
                    matched_candidates.add(match["candidate_id"])

        replay_by_invocation: Dict[str, Dict[str, Any]] = {}
        if replay:
            replay_by_invocation = _replay_annotations(replay)

        excluded = excluded_ids()
        obligations = []
        # Why this report's denominator differs from the judge's, counted rather than left to
        # be discovered. Two kinds of row are dropped here that a judge report still scores as
        # misses, and neither is a fact about the reviewer: one whose gold has no `change_ids`
        # at all, which anchor-tier pairing can never reach, and one `obligation_exclusions`
        # names as contradicted by the release's own artifacts. On `heldout12_v2_rep1` the
        # difference is exactly one audit-excluded row -- 23 in the judge's report, 22 here.
        skipped = {"not_proposed_atomic": 0, "audit_excluded": 0, "anchorless": 0}
        for row in jsonl_rows(stage.release / "gold/judgments.jsonl"):
            if row.get("pr_number") not in reviewed:
                continue
            for obligation in row.get("obligations") or []:
                if obligation.get("status") != "proposed_atomic":
                    skipped["not_proposed_atomic"] += 1
                    continue
                if obligation["obligation_id"] in excluded:
                    skipped["audit_excluded"] += 1
                    continue
                if not (obligation.get("change_ids") or []):
                    skipped["anchorless"] += 1
                    continue
                # The judgment, not just the obligation: `concern_labels` says whose ask this
                # was and `blocking_force` says how hard. Without them a silence cannot be
                # told from a correct silence -- 32 of 43 gold-site silences on
                # `heldout12_v2_rep1` are an arm quiet about somebody else's concern.
                obligations.append((row["pr_number"], obligation, row))

        rows = []
        for pr_number, obligation, judgment in obligations:
            gold_labels = {str(label) for label in judgment.get("concern_labels") or []}
            sites = set(obligation["change_ids"])
            cells = [job for job in jobs if sites & set(job.site_change_ids or [])]
            anchored = [finding for change_id in sites for finding in by_change.get(change_id, [])]
            anchored_ids = {item["finding_id"] for item in anchored}

            states = []
            annotations = []
            for job in cells:
                job_findings = [
                    item for item in anchored
                    if item.get("origin_arm_id") == job.arm_id
                    or (job.arm_id == "generalist" and not item.get("origin_arm_id"))]
                state = _cell_state(job, job_findings)
                states.append(state)
                response = responses.get(job.invocation_id) or {}
                abstention = (response.get("abstention") or {}) if state == "silent" else {}
                replayed = replay_by_invocation.get(job.invocation_id) or {}
                annotations.append({
                    "invocation_id": job.invocation_id,
                    "arm_id": job.arm_id,
                    "state": state,
                    "abstention_reason": abstention.get("reason") or None,
                    # The sentence the arm wrote, which is the only thing a silence can be
                    # diagnosed from: the reason *enum* swapped under replay on 17 of 45
                    # sessions with the outcome unchanged, so it labels nothing on its own.
                    "abstention_detail": abstention.get("detail") or None,
                    # Whether the ask was this arm's business at all. `None` for the
                    # generalist and anything else outside the registry, which has no remit
                    # to be outside of.
                    "on_concern": (bool(gold_labels & remit[job.arm_id])
                                   if job.arm_id in remit else None),
                    "context": _context_quality(job.context_calls),
                    "filed_elsewhere_in_unit": bool(
                        state == "silent" and (job.claims or [])),
                    "replay_stable": replayed.get("stable"),
                    "replay_reasons": replayed.get("reasons"),
                    "replay_details": replayed.get("details"),
                    "replay_filed": replayed.get("filed"),
                })

            state = deepest(*states) if states else "unscheduled"
            located = state in {"candidate", "finding"}
            if not located:
                coarse = "UNTOUCHED"
            elif not audit:
                coarse = "LOCATED_UNJUDGED"
            else:
                coarse = ("COVERED"
                          if verdict_by_obligation.get(obligation["obligation_id"]) == "hit"
                          else "LOCATED_MISS")
            rows.append({
                "obligation_id": obligation["obligation_id"],
                "pr_number": pr_number,
                "coarse": coarse,
                # What the maintainer actually asked for, beside what happened to it. Reading
                # a silence means reading the ask, and this report is where the join lives so
                # that nobody does it in a scratchpad again.
                "claim": obligation.get("claim"),
                "required": obligation.get("required"),
                "concern_labels": sorted(gold_labels),
                "blocking_force": judgment.get("blocking_force"),
                "speech_act": judgment.get("speech_act"),
                # Was an arm whose remit covers this ask scheduled here at all? Gold-free
                # apart from the ask's own label, and it separates "the right arm declined"
                # from "the right arm never ran", which are different repairs.
                "on_concern_arm_scheduled": any(
                    cell["on_concern"] for cell in annotations),
                "state": state,
                "gate": sorted({item.get("admission") for item in anchored}) or None,
                "judge": verdict_by_obligation.get(obligation["obligation_id"]) if audit else None,
                "findings_at_site": sorted(anchored_ids),
                "cells": annotations,
            })

        finding_rows = []
        for finding in findings:
            key = finding_key(_asobj(finding))
            key_runs.setdefault(key, set()).add(run_name)
            if not audit:
                judged = None
            elif finding["finding_id"] in matched_candidates:
                judged = "matched"
            elif finding["finding_id"] in paired_candidates:
                judged = "paired_unmatched"
            else:
                judged = "unpaired"
            finding_rows.append({
                "finding_id": finding["finding_id"], "key": key,
                "pr_number": finding["pr_number"],
                "admission": finding.get("admission"),
                "judge": judged,
            })

        per_run[run_name] = {
            "state": stage.state.value,
            "forensic": stage.forensic,
            "prs_reviewed": reviewed,
            "requires": stage.consumed,
            "obligations_counted": len(obligations),
            "obligations_not_counted": skipped,
            "coarse": {name: sum(1 for row in rows if row["coarse"] == name)
                       for name in COARSE},
            "fine": {name: sum(1 for row in rows if row["state"] == name) for name in FINE},
            "obligations": rows,
            "obligation_ids_by_bucket": {
                name: sorted(row["obligation_id"] for row in rows if row["coarse"] == name)
                for name in COARSE},
            "findings": finding_rows,
            "findings_by_judge": {
                name: sum(1 for row in finding_rows if row["judge"] == name)
                for name in ("matched", "paired_unmatched", "unpaired")},
        }

    if len(run_names) > 1:
        for run_name, payload in per_run.items():
            for row in payload["findings"]:
                row["reps_with_key"] = len(key_runs.get(row["key"], ()))

    return {
        "runs": run_names,
        "judged": bool(audit),
        "per_run": per_run,
        "coarse_vocabulary": list(COARSE),
        "fine_vocabulary": list(FINE),
        "note": (
            "UNTOUCHED is judge-independent: nothing the system emitted anchors at the "
            "obligation's sites, so no verdict could make it a hit. COVERED and LOCATED_MISS "
            "split the rest by the judge's own per-obligation verdict, and without an audit "
            "that split is not made. The annotations beside each cell -- abstention reason, "
            "retrieval, gate, replay stability -- answer different questions and are not "
            "buckets. `reps_with_key` is reported, never ranked on: cross-rep agreement "
            "separates hits in-sample and is provisional."),
    }


def silences(run: str, replay: Optional[str] = None, audit: bool = True,
             labels: Optional[Path] = None) -> Dict[str, Any]:
    """Every gold-site silence beside the ask it is silent about, and its label.

    The step-0 instrument. `buckets` already computes the join; this flattens it to the unit a
    reader can actually work through -- one row per (obligation, silent cell) -- and adds the
    two things a reader needs and an aggregate cannot supply: the arm's own sentence, and
    whether the ask was that arm's business at all.

    The second one reorders everything. On `heldout12_v2_rep1` only a minority of gold-site
    silences are an arm declining inside its own remit; the rest are the wrong arm, correctly
    quiet, and counting them as silences to be fixed is how an intervention aimed at a
    contract ends up aimed at nothing. `on_concern` is that split, computed through
    `benches.gold_labels_for` so the two concern vocabularies stay bridged.

    A silence is not a miss and this is not a score. An obligation is missed once, however
    many arms were quiet at it, and `by_label` below counts *cells*: several belong to one
    obligation, most of them off-concern. Read `buckets` for the obligation-level number.

    Costs nothing and calls no model.
    """

    from src.mathlib_review.judge.adjudicate import (
        SILENCE_LABELS, load_silence_labels, resolve_silences,
    )
    from src.mathlib_review.schema import silence_key

    payload = buckets([run], audit=audit, replay=replay)["per_run"][run]
    store = Path(labels) if labels else SILENCE_LABELS
    resolved = resolve_silences(load_silence_labels(store)) if store.is_file() else {}

    rows = []
    for obligation in payload["obligations"]:
        for cell in obligation["cells"]:
            if cell["state"] != "silent":
                continue
            key = silence_key(cell["invocation_id"], obligation["obligation_id"])
            verdict = resolved.get(key) or {}
            rows.append({
                "key": key,
                "pr_number": obligation["pr_number"],
                "obligation_id": obligation["obligation_id"],
                "claim": obligation["claim"],
                "concern_labels": obligation["concern_labels"],
                "blocking_force": obligation["blocking_force"],
                "coarse": obligation["coarse"],
                "invocation_id": cell["invocation_id"],
                "arm_id": cell["arm_id"],
                "on_concern": cell["on_concern"],
                "abstention_reason": cell["abstention_reason"],
                "abstention_detail": cell["abstention_detail"],
                "context": cell["context"],
                "filed_elsewhere_in_unit": cell["filed_elsewhere_in_unit"],
                "replay_stable": cell["replay_stable"],
                "replay_reasons": cell["replay_reasons"],
                "replay_details": cell["replay_details"],
                "replay_filed": cell["replay_filed"],
                "label": verdict.get("label"),
                "evidence_gap_tool": verdict.get("evidence_gap_tool"),
                "labelled_by": verdict.get("labelled_by"),
                "label_note": verdict.get("note"),
                "contested": verdict.get("contested", False),
            })

    from collections import Counter

    on_concern = [row for row in rows if row["on_concern"]]
    labelled = [row for row in rows if row["label"]]
    return {
        "run": run,
        "replay": replay,
        "labels_store": str(store),
        "silent_cells": len(rows),
        "obligations_with_a_silence": len({row["obligation_id"] for row in rows}),
        "on_concern_cells": len(on_concern),
        "off_concern_cells": sum(1 for row in rows if row["on_concern"] is False),
        "remitless_cells": sum(1 for row in rows if row["on_concern"] is None),
        # Whether an arm whose remit covers the ask was scheduled at all, per obligation.
        # `False` is a routing failure and no contract change reaches it.
        "obligations_without_an_on_concern_arm": sorted(
            item["obligation_id"] for item in payload["obligations"]
            if not item["on_concern_arm_scheduled"]),
        "labelled": len(labelled),
        "labelled_share": round(len(labelled) / len(rows), 4) if rows else None,
        "by_label": dict(Counter(row["label"] for row in labelled)),
        "by_label_on_concern": dict(
            Counter(row["label"] for row in labelled if row["on_concern"])),
        "by_arm": {
            arm: {
                "cells": sum(1 for row in rows if row["arm_id"] == arm),
                "on_concern": sum(1 for row in rows
                                  if row["arm_id"] == arm and row["on_concern"]),
            }
            for arm in sorted({row["arm_id"] for row in rows})},
        "contested_keys": sorted({row["key"] for row in rows if row["contested"]}),
        "rows": rows,
        "note": (
            "One row per (obligation, silent arm), not per obligation: an obligation with "
            "five quiet arms contributes five. `on_concern` says whether gold's own concern "
            "label for the ask falls in that arm's `expected_concerns`; where it is false the "
            "silence is correct and the question is routing, not the contract. A label is a "
            "reader's diagnosis of a silence -- it orders work and explains a number, and it "
            "never enters recall."),
    }


def _asobj(row: Dict[str, Any]):
    from types import SimpleNamespace

    return SimpleNamespace(**row)


def _replay_annotations(replay_run: str) -> Dict[str, Dict[str, Any]]:
    """Per invocation, what re-deciding from the recorded prefix produced.

    A decision that reproduces is the arm's reading of its contract; one that does not is
    sampling noise wearing a diagnosis. 41 of 45 gold-site specialist silences were stable.

    `stable` is that question and is what the overlay prints. The rest is for diagnosing the
    stable ones, which is the harder job: `reasons` because the abstention *label* is less
    reproducible than the abstention (17 of 45 sessions produced a reason the recording did
    not), `details` because the label is not the diagnosis and the arm's own sentence is, and
    `filed` because a silence that files in some samples is a different repair from one that
    never does. `details` is empty for a replay run written before the outcome rows carried
    the text; it is reported as absent rather than reconstructed from attempt directories,
    which belong to the worktree the replay ran in and may not exist.
    """

    from src.mathlib_review.run_state import StageInput

    stage = StageInput.of(replay_run, require=("replay_outcomes",), allow_partial=True)
    samples: Dict[str, List[Dict[str, Any]]] = {}
    for row in jsonl_rows(stage.path("replay_outcomes")):
        recorded = (row.get("recorded") or {}).get("decision") or {}
        replayed = (row.get("replay") or {}).get("decision") or {}
        if not replayed:
            continue
        first = replayed.get("first") or {}
        samples.setdefault(row["invocation_id"], []).append({
            "agreed": bool((recorded.get("first") or {}).get("filed") == first.get("filed")),
            "filed": bool(first.get("filed")),
            "reason": first.get("abstention_reason"),
            "detail": first.get("abstention_detail"),
        })

    out: Dict[str, Dict[str, Any]] = {}
    for invocation, rows in samples.items():
        out[invocation] = {
            "stable": all(row["agreed"] for row in rows),
            "samples": len(rows),
            "filed": sum(row["filed"] for row in rows),
            "reasons": sorted({row["reason"] for row in rows if row["reason"]}),
            "details": [row["detail"] for row in rows if row["detail"]] or None,
        }
    return out
