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

from src.mathlib_review.release.contracts import (
    GoldLeakError, assert_prompts_gold_free, prompt_leaks,
)
from src.mathlib_review.agenda.render_focused import (
    ASK_WITHOUT_FIX_CLAUSE, SUBMISSION_CONTRACT, TARGET_SECTIONS, VERDICTS_ABSTENTION_PARAGRAPH,
    focused_system_prompt,
)
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
    # Both contracts an arm can be sent: the default, and the one both knobs render.
    offenders = {
        arm: prompt_leaks(focused_system_prompt(spec), gold)
        + prompt_leaks(focused_system_prompt(
            spec, submission_verification_policy="verify_edits_if_present",
            target_verdicts=True), gold)
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
    for text in (ASK_WITHOUT_FIX_CLAUSE, VERDICTS_ABSTENTION_PARAGRAPH, TARGET_SECTIONS):
        assert not prompt_leaks(text, gold)


def test_the_lead_instructions_quote_no_gold():
    from ape.tasks.lean_tasks.formal_math.review import prompts as v5_prompts

    gold = all_gold()
    if not gold:
        pytest.skip("no gold available in this checkout")
    assert not prompt_leaks(v5_prompts.LEAD_SYSTEM, gold)


# --- tool text, and the declarations gold is about ---------------------------------------
#
# The pipeline-overfit audit (2026-09-24) found dev text the gate above could not see: tool and
# argument descriptions are not prompts, and a gold *subject* -- the declaration a maintainer
# asked about -- is not an answer. `lean_verify_edit`'s example was `Subgroup.closure_pow_le`,
# 33401's gold target, so every arm reviewing 33401 was shown its own subject as the model
# name. Tool schemas are also sealed nowhere (`docs/todo/framework-defects-2026-09.md`), so no
# plan identity could show the change either.

#: Modules whose string literals reach a model: the review tools, the prompts, the arm
#: rationales the lead reads, and the producers' section titles, leads and fact templates
#: (2026-10-06: a producer section is placed in the reviewer's packet by `context_file`).
MODEL_TEXT_MODULES = (
    *sorted(Path("src/ape/tasks/lean_tasks/formal_math/review").glob("*.py")),
    *sorted(Path("src/mathlib_review/producers").glob("*.py")),
    Path("src/mathlib_review/agenda/registry.py"),
    Path("src/mathlib_review/agenda/render_focused.py"),
    Path("src/mathlib_review/agenda/review_map.py"),
)


def model_text(path: Path):
    """Every string literal in a module except docstrings. The review tools declare their text
    with `description=`, so a docstring there never reaches a model."""

    import ast

    tree = ast.parse(path.read_text())
    docstrings = {
        id(node.body[0].value) for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and node.body and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    }
    return "\n".join(node.value for node in ast.walk(tree)
                     if isinstance(node, ast.Constant) and isinstance(node.value, str)
                     and id(node) not in docstrings)


def gold_subjects():
    """Leaf names of the declarations every release's gold asks about, through its change graph.
    Short or unseparated leaves (`le_refl`, `comm`) are ordinary vocabulary and are left out."""

    out = {}
    for release in sorted(RELEASES.glob("*")):
        gold, graphs = release / "gold/judgments.jsonl", release / "derived/change_graphs.jsonl"
        if not (gold.is_file() and graphs.is_file()):
            continue
        asked = {change for line in gold.read_text().splitlines() if line.strip()
                 for obligation in (json.loads(line).get("obligations") or [])
                 for change in (obligation.get("change_ids") or [])}
        for line in graphs.read_text().splitlines():
            if not line.strip():
                continue
            graph = json.loads(line)
            for target in graph.get("targets") or []:
                leaf = (target.get("declaration_name") or "").split(".")[-1]
                if target.get("change_id") in asked and len(leaf) >= 8 and "_" in leaf:
                    out[leaf] = graph["pr_number"]
    return out


def test_no_model_text_names_a_gold_subject_or_quotes_gold():
    import re

    subjects, gold = gold_subjects(), all_gold()
    if not subjects:
        pytest.skip("no gold available in this checkout")
    offenders = {}
    for path in MODEL_TEXT_MODULES:
        text = model_text(path)
        found = [f"{leaf} ({pr})" for leaf, pr in sorted(subjects.items())
                 if re.search(r"(?<![\w'])" + re.escape(leaf) + r"(?![\w'])", text)]
        found += prompt_leaks(text, gold)
        if found:
            offenders[str(path)] = found
    assert not offenders, f"model-facing text names gold: {offenders}"


def test_the_subject_sweep_would_have_caught_the_tool_example():
    """`closure_pow_le` is what `lean_verify_edit` showed before this gate existed."""

    import re

    subjects = gold_subjects()
    if not subjects:
        pytest.skip("no gold available in this checkout")
    assert subjects.get("closure_pow_le") == 33401
    old = 'description="Name of the declaration to replace whole (e.g. Subgroup.closure_pow_le)"'
    assert re.search(r"(?<![\w'])closure_pow_le(?![\w'])", old)


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
