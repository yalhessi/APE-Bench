"""Render a curator sitting digest for every judgment of the requested PRs."""

import argparse
import json
from pathlib import Path

from src.mathlib_review.io import load_jsonl
from src.mathlib_review.schema import ChangeGraph, JudgmentNode, OutcomeObservation


DECISION_MENU = (
    "confirm_atomic (one obligation, as stated) | split (list independently satisfiable "
    "obligations) | not_judgeable (exclude with reason) | revise (correct claim/scope)"
)


def render_curation_digest(release_dir: Path, pr_numbers: list) -> str:
    wanted = set(pr_numbers)
    judgments = [item for item in load_jsonl(release_dir / "gold/judgments.jsonl", JudgmentNode)
                 if item.pr_number in wanted]
    outcomes = {item.judgment_id: item
                for item in load_jsonl(release_dir / "gold/outcome_observations.jsonl", OutcomeObservation)}
    graphs = {item.episode_id: item
              for item in load_jsonl(release_dir / "derived/change_graphs.jsonl", ChangeGraph)}
    lines = [
        "# PR Review v4 curation digest",
        "",
        f"Release: `{release_dir}`",
        f"PRs: {', '.join(str(pr) for pr in sorted(wanted))}",
        f"Judgments: {len(judgments)}",
        "",
        f"Per item choose one of: {DECISION_MENU}.",
        "Supporting proof steps normally stay inside one obligation; split only when parts are "
        "independently satisfiable.",
        "",
    ]
    for judgment in sorted(judgments, key=lambda item: (item.pr_number, item.source_intervention_id)):
        annotation = judgment.annotation
        flagged = annotation.atomicity_status not in {"presumed_atomic", "reviewed_decomposed"}
        outcome = outcomes.get(judgment.judgment_id)
        targets = {target.change_id: target for target in graphs[judgment.episode_id].targets}
        lines.extend([
            f"## {judgment.source_intervention_id} (PR #{judgment.pr_number})"
            + (" ⚠ FLAGGED" if flagged else ""),
            "",
            f"Status: `{annotation.status}` / `{annotation.atomicity_status}`"
            + (" — signals: " + ", ".join(f"`{s}`" for s in annotation.atomicity_signals)
               if annotation.atomicity_signals else ""),
            f"Concerns: {', '.join(judgment.concern_labels) or '—'} | speech act: "
            f"{judgment.speech_act} | blocking: {judgment.blocking_force}",
            f"Outcome: {outcome.outcome if outcome else 'unknown'}"
            + (f" — {outcome.evidence}" if outcome and outcome.evidence else ""),
            "",
            f"**Action:** {judgment.action}",
            "",
            "**Obligations:**",
        ])
        for obligation in judgment.obligations:
            lines.append(f"- ({obligation.status}) {obligation.claim}")
            lines.append(f"  - resolution: {obligation.resolution_criteria}")
        if not judgment.obligations:
            lines.append("- None recorded")
        lines.append("")
        lines.append("**Scope targets:**")
        scoped = [relation.change_id for relation in judgment.scope_relations]
        for change_id in scoped:
            target = targets.get(change_id)
            if target is None:
                lines.append(f"- UNRESOLVED `{change_id}`")
            else:
                label = target.declaration_name or target.kind
                lines.append(f"- `{target.path}`: `{label}`")
        if not scoped:
            lines.append("- None")
        lines.extend(["", "**Decision:** pending", ""])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render curator digest for selected PRs")
    parser.add_argument("release", type=Path)
    parser.add_argument("--prs", type=int, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rendered = render_curation_digest(args.release, args.prs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered)
    print(json.dumps({"out": str(args.out), "bytes": len(rendered.encode("utf-8"))}, indent=2))


if __name__ == "__main__":
    main()
