"""Adapter tests: gold record -> task data, task result -> PredictionRecord."""

from src.datasets.pr_review_v2.schema import (
    DeltaHunk,
    GoldBlock,
    GoldComment,
    InputBlock,
    Outcome,
    PRReviewV2Record,
    SliceFlags,
    ValidationBlock,
)
from src.datasets.pr_review_v2.task_adapter import (
    build_task_data,
    result_to_prediction,
)


def _record() -> PRReviewV2Record:
    return PRReviewV2Record(
        repo="leanprover-community/mathlib4",
        pr_number=42,
        slices=SliceFlags(merged=True),
        input=InputBlock(
            title="feat: add lemma", description="adds Foo",
            base_sha="b0", head_sha="h0sha", h0_resolution="review_commit_id",
            diff=("diff --git a/Mathlib/A.lean b/Mathlib/A.lean\n"
                  "--- a/Mathlib/A.lean\n+++ b/Mathlib/A.lean\n"
                  "@@ -1,0 +1,1 @@\n+lemma foo := rfl"),
        ),
        gold=GoldBlock(
            verdict="CHANGES_REQUESTED",
            comments=[GoldComment(id="c1", author="m", kind="inline", submitted_at="t",
                                  body="rename", anchor={"path": "Mathlib/A.lean", "line": 5})],
            delta_near=[DeltaHunk(hunk_id="h", path="Mathlib/B.lean", op="removed_in_revision",
                                  new_start=10, new_lines=2, patch="@@")],
            outcome=Outcome(merged=True),
        ),
        validation=ValidationBlock(),
    )


def test_build_task_data_pins_merge_base_and_keeps_head():
    data = build_task_data(_record())
    assert data.pr_number == 42
    # target is the MERGE BASE; head is kept for reference; δ₀ reaches the reviewed state
    assert data.target_workspace.commit_hash == "b0"
    assert data.snapshot_head_sha == "h0sha"
    assert data.snapshot_base_sha == "b0"  # read by the legacy patch-marker writer
    assert data.target_workspace.default_target == "Mathlib"
    assert data.diff.startswith("diff --git")
    assert data.pr_diff == data.diff  # alias the legacy materialization reads
    # changed files parsed from the diff's `+++ b/` header
    assert data.changed_files == ["Mathlib/A.lean"]
    # default task_type is the holistic review
    assert data.task_type == "lean_pr_review_v2"
    assert data.task_id == "lean_pr_review_v2_42"


def test_build_task_data_task_type_selects_checker():
    data = build_task_data(_record(), task_type="lean_pr_review_dup")
    assert data.task_type == "lean_pr_review_dup"
    assert data.task_id == "lean_pr_review_dup_42"  # task_id carries the checker


def test_result_to_prediction_carries_evidence():
    result = {"pr_number": 7, "merge_ready_as_is": False, "findings": [
        {"anchor": {"path": "A.lean", "line_start": 9}, "severity": "blocking",
         "claim": "duplicates existing lemma", "evidence": "Finset.card_sdiff_add_card"},
    ]}
    pred = result_to_prediction(result, model="m", mode="workspace", pr_number=7)
    assert pred.findings[0].evidence == "Finset.card_sdiff_add_card"


def test_result_to_prediction_roundtrip():
    result = {
        "pr_number": 42,
        "merge_ready_as_is": False,
        "confidence": 0.7,
        "findings": [
            {"anchor": {"path": "Mathlib/A.lean", "line_start": 5, "line_end": 5},
             "severity": "blocking", "claim": "rename", "suggested_fix": None},
            {"anchor": None, "severity": "advisory", "claim": "PR-level note"},
        ],
    }
    pred = result_to_prediction(result, model="gpt_5.4", mode="workspace", pr_number=42)
    assert pred.pr_number == 42 and pred.mode == "workspace" and pred.model == "gpt_5.4"
    assert pred.merge_ready_as_is is False and pred.confidence == 0.7
    assert len(pred.findings) == 2
    assert pred.findings[0].anchor.path == "Mathlib/A.lean"
    assert pred.findings[1].anchor is None
    # serializes the same way diff_only predictions do (so evaluators are agnostic)
    assert pred.model_dump(mode="json")["mode"] == "workspace"


def test_result_to_prediction_failed_result_uses_pr_number_fallback():
    # A failed/aborted run returns a generic BaseTaskResult dump lacking pr_number/findings.
    failed = {"task_id": "x", "task_type": "lean_pr_review_v2", "global_index": "g",
              "success": False, "score": 0.0, "error": "setup failed"}
    pred = result_to_prediction(failed, model="gpt_5.4", mode="workspace", pr_number=99)
    assert pred.pr_number == 99 and pred.findings == [] and pred.merge_ready_as_is is None


def test_result_to_prediction_no_pr_number_anywhere_raises():
    import pytest
    with pytest.raises(ValueError):
        result_to_prediction({"success": True}, model="m")
