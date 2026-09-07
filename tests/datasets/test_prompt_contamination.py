"""No arm may be handed the answer.

Three exact heldout answers reached the arms' instructions and sat there undetected: PR
33321's docstring sentence and PR 33421's requested new name `round_eq_div`, both written as
*illustrations* while editing an arm prompt and the submission contract, plus an inherited
`Dense.upperBounds_image` in the naming prompt. An illustration is exactly how this happens —
a real example is the most natural thing to reach for, and the evaluation set is the code you
have been reading.

`contracts.assert_gold_free` could not have caught any of them: it sweeps the sealed agenda,
and the agenda carries prompt **hashes** only. Prompt text was outside the gold sweep by
construction.

The distinction this file encodes: the leak is gold *answers* in *instructions*. A rendered
user prompt legitimately contains the PR's own code, and gold necessarily names declarations
in that code, so only instruction text is swept.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.datasets.pr_review_v4.contracts import (
    GoldLeakError, assert_prompts_gold_free, prompt_leaks,
)
from src.datasets.pr_review_v4.render_focused import SUBMISSION_CONTRACT, focused_system_prompt
from src.mathlib_review.agenda.arms import specs_by_arm_id

RELEASES = Path("inputs/pr_review_v4/releases")


def gold_strings(release: Path):
    """Every phrasing a maintainer asked for, from one release's gold."""

    path = release / "gold/judgments.jsonl"
    if not path.is_file():
        return []
    out = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        for obligation in (json.loads(line).get("obligations") or []):
            for field in ("claim", "requested_change", "resolution_criteria"):
                if obligation.get(field):
                    out.append(str(obligation[field]))
    return out


def all_gold():
    out = []
    for release in sorted(RELEASES.glob("*")):
        out.extend(gold_strings(release))
    return out


def test_no_arm_instruction_quotes_gold():
    """The gate. Every specialist's system prompt, against every release's gold."""

    gold = all_gold()
    if not gold:
        pytest.skip("no gold available in this checkout")
    offenders = {
        arm: prompt_leaks(focused_system_prompt(spec), gold)
        for arm, spec in specs_by_arm_id().items()
    }
    offenders = {arm: found for arm, found in offenders.items() if found}
    assert not offenders, f"arm instructions quote gold: {offenders}"


def test_the_submission_contract_quotes_no_gold():
    """Shared by every arm, so one leak here is a leak in all of them — which is what
    `round_eq_div` was."""

    gold = all_gold()
    if not gold:
        pytest.skip("no gold available in this checkout")
    assert not prompt_leaks(SUBMISSION_CONTRACT, gold)


def test_the_lead_instructions_quote_no_gold():
    from ape.tasks.lean_tasks.formal_math.pr_review_v5 import prompts as v5_prompts

    gold = all_gold()
    if not gold:
        pytest.skip("no gold available in this checkout")
    assert not prompt_leaks(v5_prompts.LEAD_SYSTEM, gold)


# --- the detector itself, which was wrong the first time --------------------------------

def test_it_catches_a_declaration_name_lifted_from_a_claim():
    """Identifiers are extracted from *within* a claim: a claim is a sentence and the leak is
    one token inside it, which is why matching whole gold strings found nothing."""

    gold = ["Rename the theorem `round_eq'` to `round_eq_div`."]
    assert "round_eq_div" in prompt_leaks('Say "rename `round_eq_div`" not "unclear".', gold)


def test_it_catches_prose_lifted_from_a_claim():
    gold = ["Complete the sentence “In the case that `v` is the set of roots of a "
            "crystallographic root system, and `S` is ordered, this is the …”"]
    leaked = "a sentence that stops mid-thought: in the case that `v` is the set of roots " \
             "of a crystallographic root system, and `S` is ordered, this is the"
    assert prompt_leaks(leaked, gold)


def test_both_sides_are_filtered_identically():
    """The bug that made the first version report a contaminated codebase clean: stop-words
    were stripped from gold and not from the prompt, so runs could never match."""

    gold = ["Rename the declaration and reprove the dual statement by dualizing the "
            "original through OrderDual instead of duplicating the argument"]
    prompt = ("guidance: rename the declaration and reprove the dual statement by "
              "dualizing the original through OrderDual instead of duplicating the argument")
    assert prompt_leaks(prompt, gold)


def test_an_ordinary_word_ending_a_sentence_is_not_an_identifier():
    """`statement.` was reported as a leaked identifier because it contains a dot."""

    assert prompt_leaks("Name the declaration in the claim, not the statement.",
                        ["copy the statement."]) == []


def test_generic_lean_vocabulary_is_not_a_leak():
    """`fun_prop` is a tactic. It appears in an idiom instruction as "built by hand instead
    of `fun_prop`" and also inside a gold claim, and those are not the same event."""

    gold = ["replace the lemmas with `@[to_fun (attr := fun_prop)]` on the main lemmas"]
    assert prompt_leaks("a continuity proof built by hand instead of `fun_prop`", gold) == []


def test_ordinary_review_language_is_not_a_leak():
    gold = ["Rename the lemma to follow the naming convention and fix the docstring typo."]
    assert prompt_leaks(
        "Check whether the docstring is accurate. Report a typo you can see.", gold) == []


def test_assert_prompts_gold_free_names_the_offending_prompt():
    with pytest.raises(GoldLeakError) as caught:
        assert_prompts_gold_free(
            ["clean text", "rename it to `round_eq_div` exactly"],
            ["Rename the theorem to `round_eq_div`."])
    assert "prompt 1" in str(caught.value)


def test_a_shared_namespace_is_not_a_leak():
    """`Finset.sum` occurs inside `Finset.sum_comm`. A prompt naming the latter has not
    quoted the former, and substring matching reported that as a leak — which would fire for
    any two declarations sharing a namespace."""

    gold = ["Use `Finset.sum` here rather than re-deriving it."]
    assert prompt_leaks("Names follow the statement, e.g. `Finset.sum_comm`.", gold) == []


def test_a_file_path_is_not_a_leaked_identifier():
    """Gold names the file it is about, and the reviewer is given that file. `Inverses.lean`
    appearing in both is the review working, not the answer leaking — and without this the
    check fires on every prompt carrying a file skeleton."""

    gold = ["Wrap the overly long doc comment line in "
            "`Mathlib/GroupTheory/Submonoid/Inverses.lean` (around line 20)."]
    assert prompt_leaks("### Structure of `Mathlib/GroupTheory/Submonoid/Inverses.lean`",
                        gold) == []
