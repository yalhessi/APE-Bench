"""The adjudication policy may gain branches; it may not change the ones Phase 9 rests on.

Policy `/2` added branches for `naming_norm`, `lint_norm` and `repository_policy` — methods
registered after `/1` was frozen, which reached the `unresolved` fallback and therefore
deferred by construction. 25 of 42 medium opportunities (60%) fell through it, leaving the
deterministic arm with no published finding outside the development PR.

`/2` also taught the `baseline_failure` branch the generic executor's vocabulary for a failed
compile. That branch gated on evidence text matching `{"compiled=false", "fails to compile",
"compile failure"}` while the executor writes `exit_code=1\\n<compiled-target>:…: error: …`.
The phrase does appear in the opportunity's `observed_pattern`, which is not an evidence
artifact — so 12 genuine file-level build failures could never reach `request`.

Phase 9's flagship numbers were produced from the four frozen `dev-pilot-0.9.*` releases, so
those outcomes are pinned byte-for-byte here.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import get_args

import pytest

from src.datasets.pr_review_v4 import phase7_adjudication
from src.datasets.pr_review_v4.phase7_adjudication import (
    EvidenceView,
    OpportunityView,
    _classify,
    _nonzero_exit_ids,
    production_cases,
)
from src.datasets.pr_review_v4.schema import NormRecord, WorthinessDecision

LINEAGE = Path(__file__).parent / "fixtures/phase9_policy_lineage.json"


def test_phase9_lineage_outcomes_are_unchanged():
    """Every opportunity Phase 9 adjudicated must still adjudicate identically."""

    expected = json.loads(LINEAGE.read_text())
    actual = {}
    for release in sorted({key.split("|")[0] for key in expected}):
        for case in production_cases(Path("inputs/pr_review_v4/releases") / release):
            outcome = _classify(case)
            actual[f"{release}|{case.opportunity_id}"] = [
                case.method, outcome.policy_id.split(":")[-1], outcome.worthiness,
                outcome.technical_status, outcome.norm_status, outcome.request_force,
            ]
    assert actual == expected


def _case(method: str, kind: str, content: str, alternative: str | None = "do the thing"):
    return OpportunityView(
        opportunity_id="opportunity:test",
        method=method,
        pr_number=1,
        primary_change_id="change:test",
        proposed_alternative=alternative,
        evidence=(EvidenceView("opportunity-evidence:test", kind, content, "a" * 40),),
        provenance="production",
    )


@pytest.mark.parametrize(
    "method, kind, content, worthiness, force",
    [
        # The three methods that previously fell through to `unresolved`.
        ("repository_policy.v1", "policy_report",
         "construct=axiom; declaration=foo", "request", "blocking"),
        ("lint_norm.v1", "lint_report",
         '{"codes": ["ERR_LIN"]}', "request", "advisory"),
        ("naming_norm.v1", "naming_population",
         '{"is_strong": true, "members": 27}', "request", "advisory"),
        # The executor's compile vocabulary now reaches the baseline branch.
        ("baseline_failure.v1", "applicability_check",
         "exit_code=1\n<compiled-target>:35:78: error: unsolved goals", "request", "blocking"),
    ],
)
def test_new_branches_produce_requests(method, kind, content, worthiness, force):
    outcome = _classify(_case(method, kind, content))
    assert outcome.worthiness == worthiness
    assert outcome.request_force == force
    assert outcome.policy_id.startswith(phase7_adjudication.POLICY_VERSION)


def test_a_successful_compile_is_not_a_failure():
    """`exit_code=0` must never be read as a build failure."""

    assert _nonzero_exit_ids(_case("baseline_failure.v1", "applicability_check",
                                   "exit_code=0\nall good")) == ()


def test_exit_code_matching_is_parsed_not_substring():
    """`"exit_code=1" in content` would miss code 2 and match code 10."""

    assert _nonzero_exit_ids(_case("x", "applicability_check", "exit_code=2\nboom"))
    assert _nonzero_exit_ids(_case("x", "applicability_check", "exit_code=10\nboom"))
    assert _nonzero_exit_ids(_case("x", "applicability_check", "exit_code=0\nfine")) == ()


@pytest.mark.parametrize(
    "callee, arg_index, model, field",
    [
        # `_Outcome(policy_id, technical_status, compiled, norm_status, norm_kind, ...)`
        ("_Outcome", 4, NormRecord, "norm_kind"),
        ("_Outcome", 6, WorthinessDecision, "review_worthiness"),
    ],
)
def test_policy_literals_are_declared_in_the_schema(callee, arg_index, model, field):
    """Static check that every literal the policy emits is one the schema accepts.

    Writing a new branch is exactly when an invented literal slips in: `norm_kind` accepts
    `policy`, and `explicit_policy` — the *norm source* name from the method registry — was
    used by mistake, which only raised once a record was constructed.
    """

    source = Path(phase7_adjudication.__file__).read_text(encoding="utf-8")
    allowed = set(get_args(model.model_fields[field].annotation)) | {None}
    used = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == callee:
            if len(node.args) > arg_index:
                argument = node.args[arg_index]
                if isinstance(argument, ast.Constant):
                    used.add(argument.value)
    assert used, f"no positional {callee} calls found — has the signature changed?"
    assert used <= allowed, f"{callee} emits {field} values absent from {model.__name__}: {sorted(used - allowed)}"
