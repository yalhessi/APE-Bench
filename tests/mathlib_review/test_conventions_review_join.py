"""Each review comment attached to the situation of the code it was written about.

This is the decisive component: the largest class of conventions -- enforced in review, not
followed in code -- is invisible anywhere else. Dot notation: 224 dated comments, 14 % adoption.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.conventions.review_join import (
    REVIEW_JOIN_VERSION, join_comment, situate_hunk,
)

HEAD_HUNK = """@@ -165,6 +166,12 @@ protected lemma add [AddLeftMono R] {A : Matrix m m R}
     rw [add_mulVec, dotProduct_add]
     exact add_nonneg (hA.2 x) (hB.2 x)⟩

+protected theorem smul [StarOrderedRing R'] {x : Matrix n n R'} (hx : x.PosSemidef) {a : R'}
+    (ha : 0 ≤ a) : (a • x).PosSemidef := by
+  refine ⟨IsSelfAdjoint.smul (IsSelfAdjoint.of_nonneg ha) hx.1, fun y => ?_⟩
+  simp only [smul_mulVec, dotProduct_smul, smul_eq_mul]
+  exact mul_nonneg ha (hx.2 _)
"""

CONTEXT_ONLY_HUNK = """@@ -40,6 +40,7 @@ theorem isFundamentalSequence_of_isNormal (h : IsNormal f) : IsFundamentalSequence f o g := by
   intro x hx
-  exact foo hx
+  exact bar hx
"""

FIELD_HUNK = """@@ -25,6 +25,7 @@ variable {α : Type u}
 class CanonicallyOrderedAdd (α : Type*) [Add α] [LE α] : Prop
+  protected le_add_self : ∀ a b : α, a ≤ b + a
   protected le_self_add : ∀ a b : α, a ≤ a + b
"""


def test_a_hunk_with_a_declaration_is_resolved_from_its_head():
    resolved = situate_hunk(HEAD_HUNK)
    assert resolved["resolved_via"] == "head"
    assert resolved["declaration"] == "smul"
    assert resolved["situation"].predicate_head == "PosSemidef"


def test_a_proof_interior_hunk_is_resolved_from_gits_function_context():
    """git puts the enclosing declaration's header after the `@@`; 7 % of the corpus resolves
    only this way."""

    resolved = situate_hunk(CONTEXT_ONLY_HUNK)
    assert resolved["resolved_via"] == "context"
    assert resolved["declaration"] == "isFundamentalSequence_of_isNormal"
    assert resolved["situation"].keys()["of_lemma_of_predicate"] == "of:IsFundamentalSequence"
    assert resolved["situation"].named_inside_predicate is False


def test_a_structure_field_hunk_is_reported_unresolved_not_guessed():
    resolved = situate_hunk(FIELD_HUNK)
    assert resolved["resolved_via"] == "unresolved"
    assert resolved["declaration"] is None


def test_join_carries_provenance_and_keys():
    joined = join_comment({"comment_id": "c1", "pr_number": 33294, "created_at": "2025-12-01T00:00:00Z",
                           "path": "Mathlib/X.lean", "commenter": "m", "body": "please use dot notation",
                           "diff_hunk": CONTEXT_ONLY_HUNK})
    assert joined.resolved_via == "context"
    assert joined.situation_keys["predicate"] == "pred:IsFundamentalSequence"
    assert joined.created_at.startswith("2025-12-01")


def test_the_real_corpus_resolves_about_two_thirds():
    """Pinned so a regression in either resolver shows up as a share change. 61 % from heads,
    7 % from context lines, 33 % genuinely unresolvable from the hunk alone."""

    report = Path("data/pr_review_v5/review_join/report.json")
    if not report.is_file():
        pytest.skip("run `python -m src.mathlib_review.conventions.review_join --write`")
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["schema_version"] == REVIEW_JOIN_VERSION
    assert payload["comments"] == 34640
    assert 0.66 <= payload["resolved_share"] <= 0.72
    assert payload["situation_key_kinds"]["of_lemma_of_predicate"] >= 600
