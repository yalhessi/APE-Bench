"""Tests for the NL-distillation artifact + selection signal (no network)."""

from src.datasets.pr_review_v2.distillation import (
    DeclDistillation,
    PRDistillation,
    _finding_ident,
    legibility_signal,
)


def _art():
    return PRDistillation(pr_number=1, pr_summary="s", declarations=[
        DeclDistillation(name="foo_bar", legibility=20, divergence="opaque rw chain"),
        DeclDistillation(name="Baz.qux", legibility=90),
    ])


def test_artifact_round_trips():
    art = PRDistillation.model_validate_json(_art().model_dump_json())
    assert art.declarations[0].name == "foo_bar"
    assert art.declarations[0].legibility == 20


def test_finding_ident_prefers_claim_then_fix():
    assert _finding_ident({"claim": "`foo_bar` can be shortened"}) == "foo_bar"
    assert _finding_ident({"claim": "no ident", "suggested_fix": "use `Baz.qux`"}) == "Baz.qux"
    assert _finding_ident({"claim": "nothing here"}) is None


def test_legibility_signal_is_obscurity_of_the_targeted_decl():
    art = _art()
    assert legibility_signal({"claim": "`foo_bar` x"}, art) == 80.0   # 100 - 20 (obscure -> high)
    assert legibility_signal({"claim": "`Baz.qux` y"}, art) == 10.0   # 100 - 90 (clean -> low)


def test_legibility_signal_defaults_when_unmatched_or_missing():
    art = _art()
    assert legibility_signal({"claim": "`unknown` z"}, art) == 50.0   # no matching decl
    assert legibility_signal({"claim": "`foo` z"}, None) == 50.0      # no artifact
    assert legibility_signal({"claim": "no ident"}, art) == 50.0      # no identifier
    # parse-failed artifact also defaults
    bad = PRDistillation(pr_number=1, parse_ok=False)
    assert legibility_signal({"claim": "`foo_bar` x"}, bad) == 50.0


def test_legibility_signal_substring_match():
    art = _art()
    # namespaced / partial name still resolves to the decl
    assert legibility_signal({"claim": "`Baz.qux.helper` y"}, art) == 10.0
