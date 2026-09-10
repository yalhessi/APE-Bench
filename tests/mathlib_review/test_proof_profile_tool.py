"""The tool rung 3b adds, and the two ways its trend reading went wrong first.

Rung 3a held the tactic list fixed and required the arm to sweep it. It complied partially and
the outcome did not move: 29 of 30 verified attempts were `simp`-family, five of the six
families its own prompt lists were attempted zero times, and `grind` was never written. So the
missing resource is not effort inside the repertoire — it is a channel that enumerates
candidates the arm has not thought of.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from ape.tasks.lean_tasks.formal_math.review.context_tools import (
    _REGISTRARS, _register_proof_profile,
)
from ape.tasks.lean_tasks.formal_math.review.focused_prompts import (
    procedure_supplement, procedure_tool_grant,
)
from src.mathlib_review.agenda.arms import _grant_for
from src.mathlib_review.schema.review import CONTEXT_TOOLS

BASE = "af239326a46dea977a6d5444466c14aa423f4b10"


class _StubMCP:
    """Captures the registered coroutine so it can be called without an MCP runtime."""

    def __init__(self):
        self.tools = {}

    def tool(self, **_kwargs):
        def register(fn):
            self.tools[fn.__name__] = fn
            return fn
        return register


def _tool(sha=BASE):
    mcp = _StubMCP()
    _register_proof_profile(
        SimpleNamespace(data=SimpleNamespace(snapshot_base_sha=sha)), mcp)
    return mcp.tools["proof_profile"]


def _call(**kwargs):
    return asyncio.run(_tool()(**kwargs))


# --- wiring -----------------------------------------------------------------------------

def test_the_tool_is_in_the_vocabulary_and_has_a_registrar():
    assert "proof_profile" in CONTEXT_TOOLS
    assert "proof_profile" in _REGISTRARS


def test_the_grant_belongs_to_the_variant_and_not_to_the_registry():
    """A tool present in `baseline` would move the baseline.

    Rung 0 and rung 3a were measured with the proof arms holding `declaration_search` and
    nothing else. If `proof_profile` were in the standing registry grant it would be available
    in every variant, and the arm could discover and use it without the prompt mentioning it --
    so a later comparison against "baseline" would not be a comparison at all.
    """

    for arm in ("proof_idiom", "proof_golf"):
        assert "proof_profile" not in _grant_for(arm), arm
        assert procedure_tool_grant("baseline", arm) == ()
        assert procedure_tool_grant("rung3a", arm) == ()
        assert procedure_tool_grant("rung3b", arm) == ("proof_profile",)
    # And no other arm gains it in any variant.
    for arm in ("naming", "duplication", "docs", "style", "correctness"):
        for variant in ("baseline", "rung3a", "rung3b"):
            assert procedure_tool_grant(variant, arm) == (), (variant, arm)


def test_an_unknown_variant_cannot_silently_grant_nothing():
    with pytest.raises(ValueError):
        procedure_tool_grant("rung9z", "proof_idiom")


def test_the_3b_supplement_points_at_the_tool_and_names_no_tactic():
    """If it named `grind` it would be an oracle leak wearing a mechanism's name, and the rung
    would prove nothing."""

    supplement = procedure_supplement("rung3b", "proof_idiom")
    assert "proof_profile" in supplement
    for leak in ("grind", "simpa", "gcongr", "grw", "omega", "aesop",
                 "33098", "minimalCover", "encard", "684"):
        assert leak not in supplement, f"{leak} leaked into the 3b supplement"
    # 3b is 3a plus one factor, so the rungs differ by exactly the evidence channel.
    assert procedure_supplement("rung3a", "proof_idiom") in supplement


# --- behaviour --------------------------------------------------------------------------

def _skip_without_table(payload):
    if not payload.get("success"):
        pytest.skip(f"no declaration table: {payload.get('error')}")
    return payload


def test_it_ranks_the_tactic_the_arm_never_considered_second():
    """The case rung 3a failed. `minimalCover_subset` concludes in a subset relation; among
    Mathlib lemmas that do, the arm's own choice `simpa` is first and `grind` is second."""

    payload = _skip_without_table(_call(conclusion_head="subset", limit=6))
    assert payload["reference_class"]["population"] == 2302
    # Ranked entries only: exemplar lines are indented under the tactic they illustrate.
    ranked = [line for line in payload["results"].splitlines()
              if not line.lstrip().startswith("e.g.")]
    assert "`simpa`" in ranked[0]
    assert "`grind`" in ranked[1]


def test_a_tactic_that_did_not_exist_a_year_ago_is_marked_new_not_merely_rising():
    """`grind` went from nothing to 9.21% of files; `aesop` roughly doubled from 4.55%. Both
    grew, and only one is a convention arriving. Collapsing them would bury the signal in the
    noise of every tactic that happens to be popular."""

    payload = _skip_without_table(_call(conclusion_head="subset", limit=6, examples=0))
    grind_line = next(l for l in payload["results"].splitlines() if "`grind`" in l)
    assert "NEW" in grind_line
    assert sum(1 for l in payload["results"].splitlines() if "NEW" in l) == 1


def test_the_trend_is_read_from_the_curve_alone():
    """The first version compared a share of *proofs in the reference class* against a share of
    *files across the library* — two different denominators — and reported `simpa` as declining
    because 5.9% of subset proofs is less than half the fraction of files mentioning it."""

    payload = _skip_without_table(_call(conclusion_head="subset", limit=6, examples=0))
    simpa_line = next(l for l in payload["results"].splitlines() if "`simpa`" in l)
    assert "flat" in simpa_line
    assert "declining" not in simpa_line


def test_every_answer_carries_its_population_and_classifier_versions():
    payload = _skip_without_table(_call(conclusion_head="subset"))
    assert payload["corpus_sha256"] == BASE
    assert payload["conclusion_classifier_version"]
    assert payload["tactic_vocabulary_version"]


def test_an_empty_reference_class_says_to_widen_rather_than_that_there_is_no_norm():
    payload = _call(conclusion_head="not-a-head")
    assert payload["success"] is True
    assert payload["population"] == 0
    assert "Widen it" in payload["results"]


def test_a_missing_table_is_reported_not_papered_over():
    """A profile computed from a partial checkout would be a 2% sample that still clears any
    support threshold, so absence has to surface as an error the arm can read."""

    payload = asyncio.run(_tool(sha="0" * 40)(conclusion_head="eq"))
    assert payload["success"] is False
    assert "declaration table" in payload["error"]


# --- rungs 3c and 3d --------------------------------------------------------------------

def test_only_the_capability_probe_is_an_oracle_and_only_it_names_a_tactic():
    """3c removes the choice on purpose; every other variant must leave it with the arm.

    A tactic named in 3b or 3d would make the rung measure transcription, and its result would
    say nothing about whether the arm can find the tactic itself.
    """

    from ape.tasks.lean_tasks.formal_math.review.focused_prompts import is_oracle_variant

    for variant in ("baseline", "rung3a", "rung3b", "rung3d"):
        assert not is_oracle_variant(variant), variant
        supplement = procedure_supplement(variant, "proof_idiom")
        for tactic in ("grind", "simpa", "gcongr", "omega", "aesop"):
            assert tactic not in supplement, f"{tactic} named in {variant}"
    assert is_oracle_variant("rung3c")
    assert "grind" in procedure_supplement("rung3c", "proof_idiom")


def test_the_oracle_names_a_tactic_but_never_where_to_apply_it():
    """Otherwise it measures transcription rather than capability: the arm still has to decide
    which declarations the tactic suits, and 'it failed everywhere' stays a valid outcome."""

    supplement = procedure_supplement("rung3c", "proof_idiom")
    for gold in ("minimalCover", "maximalSeparatedSet", "33098", "encard",
                 "isCover", "card_minimalCover"):
        assert gold not in supplement, f"{gold} leaked into the oracle"
    assert "not told which declarations" in supplement


def test_3c_and_3d_both_extend_3b_but_neither_extends_the_other():
    """They are alternatives — capability and motivation — and stacking them would confound
    the two remaining explanations for rung 3b's failure."""

    three_b = procedure_supplement("rung3b", "proof_idiom")
    three_c = procedure_supplement("rung3c", "proof_idiom")
    three_d = procedure_supplement("rung3d", "proof_idiom")
    assert three_b in three_c and three_b in three_d
    assert three_c not in three_d and three_d not in three_c


def test_the_motivation_variant_points_at_the_examples_not_the_numbers():
    supplement = procedure_supplement("rung3d", "proof_idiom")
    assert "examples" in supplement.lower()
    assert "percentage" in supplement.lower()


def test_the_profile_returns_worked_examples_and_says_which_answer_shape_it_is():
    """Rung 3b ran against `/1`, which returned counts alone. A run cannot be compared against
    one made under a different answer shape unless the shape is recorded."""

    from src.mathlib_review.retrieval.declaration_table import PROOF_PROFILE_VERSION

    payload = _skip_without_table(_call(conclusion_head="subset", limit=3, examples=2))
    assert payload["proof_profile_version"] == PROOF_PROFILE_VERSION
    assert "e.g. `" in payload["results"]
    # Examples are attributed, so a claim built on one can be checked.
    assert payload["results"].count("e.g. `") >= 2


def test_examples_can_be_switched_off():
    payload = _skip_without_table(_call(conclusion_head="subset", limit=3, examples=0))
    assert "e.g. `" not in payload["results"]
