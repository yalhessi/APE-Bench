"""Deterministic evidence-gated publication of review findings."""

import argparse
import json
from pathlib import Path
from typing import Iterable, List

from .io import canonical_json_bytes, jsonl_bytes, sha256_bytes, write_once
from .schema import CandidateClaim, EvidenceAssertion, EvidencePacket, SelectedFinding


def select_findings(candidates: Iterable[CandidateClaim], packets: Iterable[EvidencePacket],
                    assertions: Iterable[EvidenceAssertion]) -> List[SelectedFinding]:
    packet_by_candidate = {item.candidate_id: item for item in packets}
    assertion_by_id = {item.assertion_id: item for item in assertions}
    selected = []
    ordered = sorted(candidates, key=lambda item: (
        0 if item.severity == "blocking" else 1,
        -(item.model_confidence if item.model_confidence is not None else 0), item.candidate_id,
    ))
    for rank, candidate in enumerate(ordered):
        packet = packet_by_candidate.get(candidate.candidate_id)
        if packet is None or packet.status != "supported":
            continue
        packet_assertions = [assertion_by_id[item] for item in packet.assertion_ids
                             if item in assertion_by_id]
        supporting = [item for item in packet_assertions
                      if item.assertion_scope == "claim" and item.polarity == "supports"]
        if not supporting:
            continue
        edit_contradicted = any(item.assertion_scope == "proposed_edit" and
                                item.polarity == "contradicts" for item in packet_assertions)
        edit_supported = any(item.assertion_scope == "proposed_edit" and
                             item.polarity == "supports" for item in packet_assertions)
        compile_failure_supported = (
            candidate.concern_family == "correctness" and
            any("target-local diagnostic=True" in item.claim and
                ("compiles=False" in item.claim or "Baseline compiles=False" in item.claim)
                for item in supporting)
        )
        if compile_failure_supported:
            subject = candidate.primary_subject or candidate.concern_label
            published_claim = (
                f"`{subject}` does not compile in the reviewed state; Lean reports an error "
                "within the changed target."
            )
            published_severity = "blocking"
            published_fix = candidate.requested_change if edit_supported else None
        else:
            published_claim = candidate.claim
            published_severity = candidate.severity
            published_fix = (candidate.suggested_fix or candidate.requested_change
                             if edit_supported else candidate.suggested_fix)
        if edit_contradicted:
            published_fix = None
        rank_key = f"{rank:08d}:{candidate.candidate_id}"
        payload = {"candidate_id": candidate.candidate_id, "packet_id": packet.packet_id,
                   "pr_number": candidate.pr_number, "change_ids": candidate.change_ids,
                   "concern_label": candidate.concern_label, "severity": published_severity,
                   "claim": published_claim, "suggested_fix": published_fix,
                   "evidence_assertion_ids": [item.assertion_id for item in supporting],
                   "rank_key": rank_key}
        digest = sha256_bytes(canonical_json_bytes(payload))
        selected.append(SelectedFinding(finding_id=f"finding:{digest[:24]}",
                                        source_sha256=digest, **payload))
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--packets", type=Path, required=True)
    parser.add_argument("--assertions", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    candidates = [CandidateClaim.model_validate_json(x) for x in args.candidates.read_text().splitlines() if x]
    packets = [EvidencePacket.model_validate_json(x) for x in args.packets.read_text().splitlines() if x]
    assertions = [EvidenceAssertion.model_validate_json(x) for x in args.assertions.read_text().splitlines() if x]
    selected = select_findings(candidates, packets, assertions)
    write_once(args.out, jsonl_bytes(selected))
    print(json.dumps({"candidates": len(candidates), "selected": len(selected)}, indent=2))


if __name__ == "__main__":
    main()
