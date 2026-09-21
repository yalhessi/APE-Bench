"""Label the findings gold cannot judge, once, and carry the labels across runs.

Roughly 90% of what this system emits is not a maintainer obligation. `gold_alignment_rate` is
not precision -- gold is a lower bound, so a finding absent from it is *unaligned*, not wrong --
and nothing in the evaluation says whether any of that output is useful. The batching
comparison moved alignment 0.069-0.091 to 0.181-0.202 and control emission 2/3/4 to 0/0/1, and
neither could be read as better output. That is the largest gap in the evaluation.

What closes it is not another metric but a *record*: a judgement about one claim, kept where
the next run can find it. `finding_key` is what makes that affordable -- the site-and-kind key
recurs 127 times across three repetitions where the full key recurs 0 -- so labelling a claim
once pays for every repetition that reproduces it.

Three things this is deliberately not.

**Not gold.** Gold is what maintainers actually asked for, derived from what they wrote, and
its value is that it is model-independent revealed preference. These are judgements about what
they did *not* ask for. Merging the two would destroy the property the benchmark rests on, so
the store lives outside every release and outside every run.

**Not the recruited-annotator study**, which is deferred by choice until the agent is worth a
Mathlib maintainer's time. This is the project's own reading of its own output.

**Not a model, yet.** The store takes a `labelled_by` of `human:<name>` or `task:<identity>`
and a human row outranks a model row on the same key, so an LLM adjudicator plugs in without
moving anything here. Its rubric is research and needs its own evidence
(`docs/todo/adjudication-rubric.md`); building the socket is not the same as filling it, and
this repository has an entry about declaring evidence tiers nothing could produce.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.mathlib_review.io import (
    append_jsonl, appended_rows, jsonl_rows, pretty_json_bytes, write_once,
)
from src.mathlib_review.paths import ADJUDICATIONS
from src.mathlib_review.run_state import StageInput, append_stage, digests_of, stage_record
from src.mathlib_review.review.merge import finding_key
from src.mathlib_review.schema import AdjudicationLabel

#: Bumped when what a label MEANS changes -- the vocabulary, or what a labeller is shown.
#: Separate from `schema_version`, which says the row parses.
ADJUDICATION_VERSION = "v5-adjudication/1"

#: The store. One file for every run and every repetition, append-only, outside `RUNS` and
#: outside `AUDITS`: a label is about a claim, not about a run, and it has to outlive every run
#: that reproduces the claim.
LABELS = ADJUDICATIONS / "labels.jsonl"


def load_labels(path: Path = LABELS) -> List[AdjudicationLabel]:
    """Every label ever written, in order."""

    return [AdjudicationLabel.model_validate(row) for row in appended_rows(path)]


def append_label(label: AdjudicationLabel, path: Path = LABELS) -> Path:
    """Add one label. Never edits: a correction is a later row, and the disagreement is data."""

    return append_jsonl(path, label)


def resolve(labels: Iterable[AdjudicationLabel]) -> Dict[str, Dict[str, Any]]:
    """The current verdict per key, and whether the rows on that key disagree.

    A human row outranks a model row, and a later row of the same kind outranks an earlier one.
    Disagreement is *reported*, never averaged: two people reading one claim differently is the
    most interesting row in the file, and a majority over n=2 would bury it.
    """

    by_key: Dict[str, List[AdjudicationLabel]] = {}
    for label in labels:
        by_key.setdefault(label.key, []).append(label)

    resolved: Dict[str, Dict[str, Any]] = {}
    for key, rows in by_key.items():
        human = [row for row in rows if row.labelled_by.startswith("human:")]
        chosen = (human or rows)[-1]
        resolved[key] = {
            "label": chosen.label,
            "labelled_by": chosen.labelled_by,
            "adjudication_version": chosen.adjudication_version,
            "exemplar_finding_id": chosen.exemplar_finding_id,
            "from_run": chosen.from_run,
            "contested": len({row.label for row in rows}) > 1,
            "rows": len(rows),
        }
    return resolved


def ingest(path: Path, *, store: Path = LABELS) -> Dict[str, int]:
    """Read a file of human labels into the store.

    Validated as `AdjudicationLabel`, and a row that does not say a human wrote it is refused:
    the whole point of the prefix is that a human verdict outranks a model's, and a file that
    could claim either would make that ordering meaningless.
    """

    rows = [AdjudicationLabel.model_validate(row) for row in jsonl_rows(path)]
    impostors = [row.key for row in rows if not row.labelled_by.startswith("human:")]
    if impostors:
        raise ValueError(
            f"{path} carries {len(impostors)} row(s) whose `labelled_by` is not `human:<name>` "
            f"(e.g. {impostors[0]}). A human label outranks a model's, so a file that can claim "
            f"to be either makes that ordering meaningless. Write model labels through the "
            f"adjudicator that produced them.")
    for row in rows:
        append_label(row, store)
    return {"ingested": len(rows), "keys": len({row.key for row in rows})}


def population(findings: List[Dict[str, Any]], pairs, matches) -> List[Dict[str, Any]]:
    """The findings gold said nothing about: never paired, or paired and not matched.

    A matched finding is already adjudicated -- by the maintainer, which is the only authority
    that settles what they wanted -- so it is excluded rather than re-judged.
    """

    paired = {row["candidate_id"] for row in pairs if row.get("role") == "observed"}
    matched = {row["candidate_id"] for row in matches
               if row.get("role") == "observed" and row.get("issue_match")}
    return [item for item in findings if item["finding_id"] not in matched]


def adjudicate_run(run_name: str, *, labels: Optional[Path] = None,
                   store: Path = LABELS, logger=None) -> Path:
    """Report which of a run's off-gold findings carry a label, and which are waiting.

    Reads the run and its audit, keys the population, joins the store, and writes
    `adjudication_report.json` beside the judge's own output. No model runs: a label is either
    in the store already or it is not, and the report says how much of the run is still
    unadjudicated rather than filling the gap with something.
    """

    stage = StageInput.of(run_name, audit=True, require=("findings",), allow_partial=True)
    ingested = ingest(labels, store=store) if labels else {"ingested": 0, "keys": 0}
    resolved = resolve(load_labels(store))

    findings = jsonl_rows(stage.path("findings"))
    unjudged = population(
        findings,
        jsonl_rows(stage.audit_path("semantic_pairs")),
        jsonl_rows(stage.audit_path("semantic_matches")))

    from types import SimpleNamespace

    rows, labelled = [], 0
    keys = Counter()
    for finding in unjudged:
        key = finding_key(SimpleNamespace(**finding))
        keys[key] += 1
        verdict = resolved.get(key)
        labelled += bool(verdict)
        rows.append({
            "finding_id": finding["finding_id"], "key": key,
            "pr_number": finding["pr_number"],
            "admission": finding.get("admission"),
            "action_key": finding.get("action_key"),
            "label": (verdict or {}).get("label"),
            "labelled_by": (verdict or {}).get("labelled_by"),
            "contested": (verdict or {}).get("contested", False),
            # Whether the label was made by reading THIS finding or a sibling that shares its
            # site and kind. A reader has to be able to tell.
            "label_basis": (
                None if not verdict else
                "exact" if verdict["exemplar_finding_id"] == finding["finding_id"]
                else "site_kind"),
        })

    distinct = len(keys)
    collisions = sum(count - 1 for count in keys.values())
    payload = {
        "schema_version": "v5-adjudication-report1",
        "adjudication_version": ADJUDICATION_VERSION,
        "run": run_name,
        "findings_total": len(findings),
        "unadjudicated_population": len(unjudged),
        "distinct_keys": distinct,
        # The cost of a key that identifies a site and a kind rather than a sentence: within
        # one run, several findings can share one. Printed beside the coverage so a label is
        # never read as standing for exactly one ask when it stands for two.
        "findings_sharing_a_key": collisions,
        "labelled": labelled,
        "labelled_share": round(labelled / len(unjudged), 4) if unjudged else None,
        "by_label": dict(Counter(row["label"] for row in rows if row["label"])),
        "by_basis": dict(Counter(row["label_basis"] for row in rows if row["label_basis"])),
        "contested_keys": sorted({row["key"] for row in rows if row["contested"]}),
        "ingested": ingested,
        "findings": rows,
        "note": (
            "Not precision. This says how much of what gold could not judge has been read by "
            "somebody, and what they said -- and until `labelled_share` is high, a rate over "
            "the labelled part is a rate over whatever was labelled first. `valid_not_an_ask` "
            "is its own verdict on purpose: a finding can be true and not something a "
            "maintainer would raise, and a correct/wrong split forces those together."),
    }
    out = stage.audit_dir / "adjudication_report.json"
    write_once(out, pretty_json_bytes(payload))
    if logger:
        logger.info("adjudication: %d of %d off-gold findings labelled (%d distinct keys)",
                    labelled, len(unjudged), distinct)

    try:
        append_stage(stage.run_dir, stage_record(
            "adjudicate", run_name=stage.run_name, consumed=stage.consumed,
            consumed_audit=stage.consumed_audit,
            produced=digests_of([out]),
            identity={"adjudication_version": ADJUDICATION_VERSION,
                      "adjudicator": "human",
                      "labels_sha256": _store_digest(store)},
            state_before=stage.state, state_after=stage.state, transition=None,
            forensic=stage.forensic))
    except Exception:  # noqa: BLE001 - the report is written; its row must not fail it
        if logger:
            logger.warning("could not record the adjudication's stage row", exc_info=True)
    return out


def _store_digest(store: Path) -> Optional[str]:
    from src.mathlib_review.io import sha256_file

    return sha256_file(store) if Path(store).is_file() else None
