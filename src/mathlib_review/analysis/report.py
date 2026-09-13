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

from src.mathlib_review.paths import RESULTS, run_dir
from src.mathlib_review.review.trace import routing_report


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
    for row in _load_jsonl(run_dir(run_name) / "arm_responses.jsonl"):
        if row.get("candidates"):
            continue
        arm = row.get("arm_id") or str(row.get("invocation_id") or "?").rsplit("#", 1)[-1]
        reason = (row.get("abstention") or {}).get("reason") or "unstated"
        entry = by_arm.setdefault(arm, {})
        entry[reason] = entry.get(reason, 0) + 1
    return dict(sorted(by_arm.items()))


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
    from src.mathlib_review.analysis.obligation_exclusions import excluded_ids, exclusion_report

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

    * The judge writes `semantic_matches.jsonl`; the overlay reads `matches.jsonl`. An
      alias is created rather than a copy, so there is exactly one file of record.
    * Output must not land inside a frozen root, or every render fails the FROZEN.lock gate.
      v5 overlays go to `results/overlays/pr_review_v5/`.

    Note the release's *treatment* and *executor* are picked up from the overlay's own
    defaults, so the page shows the deterministic arm's sites and investigations as context.
    Those were not part of a v5 model-arm run and contribute no findings to it.
    """

    from src.mathlib_review.analysis.review_overlay import build_overlay, write_overlay
    from src.mathlib_review.analysis.review_overlay import paths as v4_paths

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
    for node in _load_jsonl(release / "gold/judgments.jsonl"):
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
        raised: Counter = Counter(canon(r["concern_family"]) for r in _load_jsonl(path))
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
    rows = list(_load_jsonl(path))
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

    episodes = {row["pr_number"]: row for row in _load_jsonl(release / "input/episodes.jsonl")}
    out: Dict[str, Any] = {}
    for row in _load_jsonl(release / "derived/change_graphs.jsonl"):
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
