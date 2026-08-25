"""Build the optional judge-context sidecar: what the maintainer actually wrote.

The v8 audit specified injecting "the gold rationale, where the obligation carries one". It
was never implemented, and the reason is instructive: `JudgmentObligation` has no rationale
field, and it cannot gain one. `obligation_id` is a content hash over a payload that
includes the claim, so adding a field would change every obligation ID and break the gold
releases, the ambiguity registry's keys, and all cross-version comparability.

So this is a **sidecar**, keyed by `obligation_id`, and the artifact it produces is new gold
content even though no obligation hash moves. It belongs to the evaluation contract, never
the generation one — the reviewer must never see it.

**It is named for what it is.** What can be recovered deterministically is the maintainer's
source comment, not a distilled rationale. Those differ in a way that matters: a review
comment frequently contains a literal ```suggestion block, so an ablation that adds it is
partly measuring "does showing the judge the maintainer's own fix improve agreement" —
a legitimate question, but not the same one as "does explaining the motivation help".
Calling it a rationale would have overstated the result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .io import load_jsonl, pretty_json_bytes, sha256_bytes, write_once
from .paths import assert_repo_root
from .schema import InterventionView, JudgmentNode

CONTEXT_VERSION = "obligation-context/1"
DEFAULT_RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.1.0")
DEFAULT_OUT = Path("inputs/pr_review_v4/curation/obligation_context_v1.json")

#: Long enough for the ask and its justification, short enough that a quoted file does not
#: dominate the judge's prompt.
MAX_COMMENT_CHARS = 1200


def _navigate(bundle: Dict, source_key: str):
    """Resolve an event's `source_key` (e.g. `/review_comments/0`) inside its raw bundle."""

    node = bundle
    for part in source_key.strip("/").split("/"):
        if isinstance(node, list):
            try:
                node = node[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(node, dict):
            node = node.get(part)
        else:
            return None
        if node is None:
            return None
    return node


def comment_bodies(events: Iterable[Dict]) -> Dict[str, str]:
    """Map event ID -> comment body, reading through to the frozen raw bundles.

    The release's `source/events.jsonl` is an index: each event names the bundle and the
    key its payload lives at, not the text itself.
    """

    bundles: Dict[str, Dict] = {}
    bodies: Dict[str, str] = {}
    for event in events:
        source = event.get("source_object") or {}
        path, key = source.get("path"), event.get("source_key")
        if not path or not key:
            continue
        if path not in bundles:
            bundle_path = Path(path)
            if not bundle_path.is_file():
                continue
            bundles[path] = json.loads(bundle_path.read_text())
        node = _navigate(bundles[path], key)
        body = (node or {}).get("body") if isinstance(node, dict) else None
        if body:
            bodies[event["event_id"]] = body
    return bodies


def build_context(release: Path = DEFAULT_RELEASE, out: Path = DEFAULT_OUT) -> Dict:
    assert_repo_root()
    judgments = load_jsonl(release / "gold/judgments.jsonl", JudgmentNode)
    views = load_jsonl(release / "gold/intervention_views.jsonl", InterventionView)
    included = {
        obligation_id for view in views if view.evaluation_eligibility == "included"
        for obligation_id in view.obligation_ids
    }
    events = [json.loads(line) for line in
              (release / "source/events.jsonl").read_text().splitlines() if line]
    bodies = comment_bodies(events)

    rows, resolved, fell_back, unresolved = [], 0, 0, 0
    for judgment in judgments:
        for obligation in judgment.obligations:
            if obligation.obligation_id not in included:
                continue
            own = [bodies[item] for item in obligation.source_event_ids if item in bodies]
            shared = [bodies[item] for item in judgment.source_event_ids if item in bodies]
            texts = own or shared
            if own:
                resolved += 1
                provenance = "obligation_event"
            elif shared:
                fell_back += 1
                provenance = "judgment_event"
            else:
                unresolved += 1
                continue
            comment = "\n\n".join(texts).strip()
            rows.append({
                "obligation_id": obligation.obligation_id,
                "pr_number": judgment.pr_number,
                "provenance": provenance,
                "maintainer_comment": comment[:MAX_COMMENT_CHARS],
                "truncated": len(comment) > MAX_COMMENT_CHARS,
                # Sibling claims in the same judgment, for the cluster-coherence ablation.
                # Claim text only, and only siblings — never other candidates, which would
                # let the judge credit this obligation using another candidate's content.
                "sibling_claims": [
                    other.claim for other in judgment.obligations
                    if other.obligation_id != obligation.obligation_id
                    and other.obligation_id in included
                ],
            })

    payload = {
        "schema_version": "pr4-obligation-context1",
        "context_version": CONTEXT_VERSION,
        "release": str(release),
        "note": (
            "Optional judge context. Belongs to the evaluation contract only — the reviewer "
            "must never see it. `maintainer_comment` is the source review comment, not a "
            "distilled rationale; it often contains a literal suggestion block."
        ),
        "counts": {
            "included_obligations": len(included),
            "with_own_event": resolved,
            "with_judgment_event": fell_back,
            "unresolved": unresolved,
        },
        "rows": sorted(rows, key=lambda row: row["obligation_id"]),
    }
    write_once(out, pretty_json_bytes(payload))
    return {**payload["counts"], "out": str(out),
            "sha256": sha256_bytes(pretty_json_bytes(payload))}


def load_context(path: Path = DEFAULT_OUT) -> Dict[str, Dict]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text())
    return {row["obligation_id"]: row for row in payload.get("rows", [])}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the judge's obligation-context sidecar")
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(build_context(args.release, args.out), indent=2))


if __name__ == "__main__":
    main()
