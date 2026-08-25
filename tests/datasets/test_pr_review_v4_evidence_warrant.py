"""Opportunity prose must carry checkable evidence, not just assert a conclusion.

`observed_pattern` and `transformation.description` are rendered into the adjudication
prompt. When the generic executor first generalized phase3/4/5 it kept the discovery
logic but dropped the quantitative warrant — "a high-confidence unused retrieval" in
place of "the top retrieval (score 28)", and "a conflicting `card_` prefix" in place of
"87/91 direct-subject declarations ... and no `card_` examples". Phase 9's precision and
stability were measured against the specific prose, so losing it silently would move the
flagship result onto weaker evidence.

These tests pin the requirement at the source, on synthetic inputs, so it holds without
needing a Lean workspace. The end-to-end check against the frozen releases lives in
`results/pr_review_v4/audits/phase10-executor-equivalence-verdict.md`.
"""

import inspect
import re

from src.datasets.pr_review_v4 import opportunity_executor


def _runner_source(name: str) -> str:
    return inspect.getsource(getattr(opportunity_executor, name))


def test_executor_version_records_evidence_changes():
    """Any change to what the executor stores must move the version.

    /1 predates the quantitative-warrant fix these tests pin. /2 stored raw Lean
    diagnostics, which named the random temporary file Lean compiled, so its artifacts were
    not byte-reproducible; /3 substitutes `io.COMPILED_TARGET`. /4 reports a failing file
    once rather than once per declaration in it, so opportunity *counts* differ too.
    Artifacts stay comparable by content across versions, but not by hash or by count —
    which is exactly why the version has to move with them.
    """

    assert opportunity_executor.EXECUTOR_VERSION == "generic-opportunity-executor/4"


def test_naming_opportunity_cites_the_population_it_measured():
    source = _runner_source("_naming_runner")
    # The population counts must reach the prose, not just the evidence artifact.
    assert "counts['subject_prefix']" in source or 'counts["subject_prefix"]' in source
    assert "len(scan.members)" in source
    pattern_arg = source.split("_opportunity(", 1)[1]
    assert "subject_prefix" in pattern_arg, (
        "the naming observed_pattern must quote the population ratio it measured"
    )


def test_canonical_opportunity_cites_the_retrieval_score():
    source = _runner_source("_canonical_runner")
    pattern_arg = source.split("_opportunity(", 1)[1]
    assert "top.score" in pattern_arg, (
        "the canonical observed_pattern must quote the retrieval score that justified it"
    )


def test_wrapper_opportunity_names_the_witness_roles_it_composed():
    source = _runner_source("_wrapper_runner")
    assert "witness_roles" in source and "roles_phrase" in source, (
        "the wrapper opportunity must name the witness roles rather than saying "
        "'wrapper and witnesses'"
    )


def test_wrapper_transformation_kind_uses_the_frozen_contract_vocabulary():
    from src.datasets.pr_review_v4.implementation_registry import TRANSFORMATION_CLASSES

    source = _runner_source("_wrapper_runner")
    kind = re.search(r'kind="([a-z_]+)"', source).group(1)
    assert kind in TRANSFORMATION_CLASSES, (
        f"{kind} is not a frozen transformation class; synthesis.py consumes this as a "
        "finding's action kind, so ad-hoc labels leak into results"
    )
