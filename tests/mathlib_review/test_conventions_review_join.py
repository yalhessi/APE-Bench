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


def test_a_hunk_with_a_declaration_is_resolved_from_the_head_enclosing_its_tail():
    resolved = situate_hunk(HEAD_HUNK)
    assert resolved["resolved_via"] == "line"
    assert resolved["declaration"] == "smul"
    assert resolved["situation"].predicate_head == "PosSemidef"
    # The same hunk, cut from the front by the index: the tail is not trusted, the first head
    # is taken, and the record says so.
    coarse = situate_hunk(HEAD_HUNK, tail_is_comment=False)
    assert coarse["resolved_via"] == "head"
    assert coarse["declaration"] == "smul"


def test_a_proof_interior_hunk_is_resolved_from_gits_function_context():
    """git puts the enclosing declaration's header after the `@@`; 7 % of the corpus resolves
    only this way."""

    resolved = situate_hunk(CONTEXT_ONLY_HUNK)
    assert resolved["resolved_via"] == "context"
    assert resolved["declaration"] == "isFundamentalSequence_of_isNormal"
    assert resolved["situation"].keys()["of_lemma_of_predicate"] == "of:IsFundamentalSequence"
    assert resolved["situation"].named_inside_predicate is False


def test_a_structure_field_hunk_is_joined_to_its_class_with_no_proposition_facets():
    """A comment on a class field is about the class. `class` is a head now (it was not, and
    this hunk was 'unresolved'); the class's situation carries statement and typeclass facets
    but no goal or proof facets, since it proves nothing."""

    resolved = situate_hunk(FIELD_HUNK)
    assert resolved["resolved_via"] == "line"
    assert resolved["declaration"] == "CanonicallyOrderedAdd" and resolved["kind"] == "class"
    keys = resolved["situation"].keys()
    assert "goal" not in keys and "proof_style" not in keys
    assert keys["typeclass"] == "class:Add"


def test_join_carries_provenance_and_keys():
    joined = join_comment({"comment_id": "c1", "pr_number": 33294, "created_at": "2025-12-01T00:00:00Z",
                           "path": "Mathlib/X.lean", "commenter": "m", "body": "please use dot notation",
                           "diff_hunk": CONTEXT_ONLY_HUNK})
    assert joined.resolved_via == "context"
    assert joined.situation_keys["predicate"] == "pred:IsFundamentalSequence"
    assert joined.created_at.startswith("2025-12-01")


def test_the_real_corpus_resolves_line_level_for_about_seven_in_ten():
    """Pinned so a regression in either resolver shows up as a share change. Over the whole-hunk
    corpus, resolver v2: 71.5 % resolve to the declaration enclosing the commented line; 24 %
    are `between` -- the tail sits after a blank line with no head in between (a docstring,
    `variable`, attribute or `end` for something the hunk does not contain), which v1 had joined
    to the lemma above; 2 % context, 3 % unresolved. (The original 61/7/33 was measured on the
    index's front-truncated hunks with the first-head resolver; and the first-head resolver
    disagreed with the tail 74 % of the time -- the number behind the gate's 27/50.)"""

    report = Path("data/pr_review_v5/review_join/report.json")
    if not report.is_file():
        pytest.skip("run `python -m src.mathlib_review.conventions.review_join --write`")
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["schema_version"] == REVIEW_JOIN_VERSION
    # Not a fixed count: the corpus grows with every collected month, and this assertion was
    # pinned at 34,640 until December's collection made it false. What must hold is that the
    # report describes the rows the join reads *now* -- a stale report is the defect, and one
    # was on disk for a day after 7,184 September-November rows landed without a rerun.
    from src.mathlib_review.conventions.review_join import load_rows
    current = len(load_rows())
    assert payload["comments"] == current, (
        f"review_join report covers {payload['comments']} comments but its source has {current}; "
        "rerun `python -m src.mathlib_review.conventions.review_join --write`")
    assert payload["source"].startswith("corpus")
    assert 0.70 <= payload["line_level_share"] <= 0.74
    assert 0.22 <= payload["resolved_via"]["between"] / payload["comments"] <= 0.26
    assert 0.72 <= payload["resolved_share"] <= 0.76
    assert payload["situation_key_kinds"]["of_lemma_of_predicate"] >= 600


def test_the_commented_line_is_the_hunks_last_line_and_the_declaration_is_the_one_enclosing_it():
    """GitHub builds a review comment's `diff_hunk` to end at the commented line -- 328/328 of
    the positioned comments in the cached bundles, checked by recomputing the last line's number
    from the `@@` header. So the declaration is the nearest head at or above the tail, and no
    position field is needed. The gate had found only 27/50 comments were about the declaration
    they were joined to, because the resolver took the *first* head in the hunk."""

    on_second = ("@@ -10,6 +10,9 @@ section\n"
                 " lemma first_thing : A := by\n"
                 "   simp\n"
                 "+lemma second_thing : B := by\n"
                 "+  by_cases h : x\n"
                 "+  · simpa using foo")            # <- the commented line
    resolved = situate_hunk(on_second)
    assert resolved["resolved_via"] == "line"
    assert resolved["declaration"] == "second_thing"
    on_first = ("@@ -10,6 +10,9 @@ section\n"
                " lemma first_thing : A := by\n"
                "   simp")                           # <- the commented line
    assert situate_hunk(on_first)["declaration"] == "first_thing"
    # A truncated hunk (the index cuts hunks from the front at DISPLAY_HUNK_CHARS) has no
    # trustworthy tail; the resolver falls back to the coarse first-head behaviour and says so.
    coarse = situate_hunk(on_second, tail_is_comment=False)
    assert coarse["resolved_via"] == "head"
    assert coarse["declaration"] == "first_thing"


def test_a_recut_header_does_not_matter():
    """When GitHub re-cuts a long hunk, the `@@` header starts a few lines above the comment and
    `original_position` (149 here, in the raw bundle) no longer indexes the hunk's lines. The
    tail is still the commented line."""

    hunk = ("@@ -170,7 +170,9 @@ theorem far_above : True := by\n"
            "   have h := foo\n"
            "+  simp only [bar] at h\n"
            "+  exact h")
    resolved = situate_hunk(hunk)
    assert resolved["resolved_via"] == "context"     # no head in the hunk; git's context names it
    assert resolved["declaration"] == "far_above"


def test_the_real_33098_comments_resolve_to_the_lemmas_the_maintainer_named():
    bundle = Path("data/pr_review_v2/cache/bundles/pr_33098.json")
    if not bundle.is_file():
        pytest.skip("no 33098 bundle in this checkout")
    comments = json.loads(bundle.read_text(encoding="utf-8"))["review_comments"]
    resolved = {}
    for comment in comments:
        joined = join_comment({"comment_id": comment["id"], "pr_number": 33098,
                               "created_at": comment["created_at"], "path": comment["path"],
                               "commenter": None, "body": comment["body"],
                               "diff_hunk": comment["diff_hunk"]})
        resolved[joined.declaration] = joined.resolved_via
    assert all(via == "line" for via in resolved.values())
    for lemma in ("minimalCover_subset", "maximalSeparatedSet_subset", "card_minimalCover",
                  "card_maximalSeparatedSet", "card_le_of_isSeparated",
                  "coveringNumber_le_packingNumber"):
        assert lemma in resolved, lemma


def test_a_comment_inside_an_anonymous_instance_is_not_joined_to_the_lemma_above():
    hunk = ("@@ -1,3 +1,8 @@\n"
            " lemma coeFn_star (f : α →ₘ[μ] β) : ⇑(star f) =ᵐ[μ] star ⇑f := by\n"
            "   simp\n"
            "+instance : StarAddMonoid (α →ₘ[μ] β) where\n"
            "+  star_involutive f := by\n"
            "+    ext\n"
            "+    simp only [hx, Pi.star_apply, hy, star_star]")
    resolved = situate_hunk(hunk)
    assert resolved["resolved_via"] == "line"
    assert resolved["kind"] == "instance"
    assert resolved["declaration"] == "<anonymous instance>"


def test_a_structural_line_after_a_blank_is_between_declarations_not_inside_the_one_above():
    """`omit`, `export`, `end`, an `@[to_additive]` or a docstring for the *next* declaration:
    the hunk does not contain what the comment is about, and saying so beats joining it to the
    lemma above -- which the first tail resolver did for seven of nine mis-joins in the August
    sample."""

    for tail in ("+omit [CompleteSpace V]", "+@[to_additive]", "+end CWComplex.Subcomplex",
                 "+/-- The next declaration's docstring", "+export Foo (bar baz)"):
        hunk = ("@@ -1,3 +1,6 @@\n"
                " lemma isSelfAdjoint_rankOne_add : IsSelfAdjoint (rankOne 𝕜 x y) :=\n"
                "+  (adjoint_rankOne y x) ▸ IsSelfAdjoint.star_add_self _\n"
                "+\n" + tail)
        resolved = situate_hunk(hunk)
        assert resolved["resolved_via"] == "between", tail
        assert resolved["declaration"] is None


def test_an_inductive_is_a_head():
    hunk = ("@@ -1,3 +1,6 @@\n"
            " theorem uncurry_bind : True := trivial\n"
            "+\n"
            "+/-- This presieve generates `functorPushforward`. -/\n"
            "+inductive map : Presieve (F.obj X) where\n"
            "+  | of {Y : C} {u : Y ⟶ X} (h : s u) : map (F.map u)")
    resolved = situate_hunk(hunk)
    assert resolved["resolved_via"] == "line"
    assert resolved["declaration"] == "map" and resolved["kind"] == "inductive"
