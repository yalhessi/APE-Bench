"""One broken file is one finding.

When a Lean file fails to elaborate, every declaration after the first error reports "unknown
identifier" for names declared in that same file. Agents file each as a separate correctness
claim and the evidence chain supports all of them, because the file genuinely does not
compile. Measured on heldout11 rep2: PR 33294 published eight correctness findings that were
three root errors — `deriv_fp` and `mem_range_deriv` were reported "not found" while being
declared in the file under test.

The collapse is deterministic and runs after the gate, so it can only ever remove support,
never grant it.
"""

from __future__ import annotations

from types import SimpleNamespace

from src.datasets.pr_review_v5.evidence_chain import _collapse_compile_cascades

PATH = "Mathlib/A.lean"


def candidate(cid, *, episode_id="e1", change_ids=("change:1",)):
    return SimpleNamespace(candidate_id=cid, episode_id=episode_id,
                           change_ids=list(change_ids), pr_number=1)


def baseline(cid, *, path=PATH, exit_code=1, lines=(10,)):
    body = "\n".join(f"/w/{path}:{line}:0: error: boom" for line in lines)
    return SimpleNamespace(
        candidate_id=cid, collector="lean_compile", kind="compile_result",
        source_ref=f"workspace:/w:{path}:baseline",
        content=f"state=baseline\nexit_code={exit_code}\n{body}",
    )


def graph_with(spans):
    """A stand-in graph whose `_candidate_spans` result is dictated by `spans`."""

    entities = [SimpleNamespace(entity_id=f"ent:{cid}", side="reviewed",
                                span=SimpleNamespace(line_start=s, line_end=e))
                for cid, (s, e) in spans.items()]
    targets = [SimpleNamespace(change_id=f"change:{cid}", path=PATH,
                               reviewed_entity_ids=[f"ent:{cid}"], changed_range_ids=[])
               for cid in spans]
    return SimpleNamespace(entities=entities, targets=targets, changed_ranges=[])


def test_the_claim_owning_the_first_error_survives_and_the_rest_do_not():
    root = candidate("candidate:root", change_ids=["change:root"])
    tail = candidate("candidate:tail", change_ids=["change:tail"])
    graph = graph_with({"root": (5, 20), "tail": (30, 40)})
    collapsed = _collapse_compile_cascades(
        [root, tail],
        [baseline("candidate:root", lines=(10, 35)), baseline("candidate:tail", lines=(35,))],
        {"e1": graph}, {"candidate:root", "candidate:tail"},
    )
    assert collapsed == {"candidate:tail"}


def test_a_single_claim_about_a_broken_file_is_left_alone():
    """There is no cascade to collapse, and the observation stands on its own."""

    only = candidate("candidate:only", change_ids=["change:only"])
    graph = graph_with({"only": (5, 20)})
    assert _collapse_compile_cascades(
        [only], [baseline("candidate:only")], {"e1": graph}, {"candidate:only"}) == set()


def test_claims_in_different_files_are_not_siblings():
    """One finding per broken *file*: a PR that breaks three files reports three."""

    a = candidate("candidate:a", change_ids=["change:a"])
    b = candidate("candidate:b", change_ids=["change:b"])
    graph = graph_with({"a": (5, 20), "b": (5, 20)})
    collapsed = _collapse_compile_cascades(
        [a, b],
        [baseline("candidate:a", path=PATH), baseline("candidate:b", path="Mathlib/B.lean")],
        {"e1": graph}, {"candidate:a", "candidate:b"},
    )
    assert collapsed == set()


def test_a_file_that_compiles_is_never_collapsed():
    """The rule keys on failure. Two clean claims in one file are two claims."""

    a = candidate("candidate:a", change_ids=["change:a"])
    b = candidate("candidate:b", change_ids=["change:b"])
    graph = graph_with({"a": (5, 20), "b": (30, 40)})
    collapsed = _collapse_compile_cascades(
        [a, b],
        [baseline("candidate:a", exit_code=0), baseline("candidate:b", exit_code=0)],
        {"e1": graph}, {"candidate:a", "candidate:b"},
    )
    assert collapsed == set()


def test_collapse_is_deterministic_when_no_span_owns_the_first_error():
    """The break is outside every claimed target; still collapse, still reproducibly."""

    a = candidate("candidate:zzz", change_ids=["change:a"])
    b = candidate("candidate:aaa", change_ids=["change:b"])
    graph = graph_with({"a": (100, 110), "b": (120, 130)})
    arts = [baseline("candidate:zzz", lines=(10,)), baseline("candidate:aaa", lines=(10,))]
    first = _collapse_compile_cascades([a, b], arts, {"e1": graph},
                                       {"candidate:zzz", "candidate:aaa"})
    second = _collapse_compile_cascades([b, a], arts, {"e1": graph},
                                        {"candidate:aaa", "candidate:zzz"})
    assert first == second == {"candidate:zzz"}


def test_collapsing_never_grants_support():
    """It runs after the gate and can only subtract."""

    a = candidate("candidate:a", change_ids=["change:a"])
    b = candidate("candidate:b", change_ids=["change:b"])
    graph = graph_with({"a": (5, 20), "b": (30, 40)})
    collapsed = _collapse_compile_cascades(
        [a, b], [baseline("candidate:a"), baseline("candidate:b")],
        {"e1": graph}, {"candidate:a"},          # only `a` was supported
    )
    assert collapsed <= {"candidate:a", "candidate:b"}
    assert "candidate:b" not in ({"candidate:a"} - collapsed)
