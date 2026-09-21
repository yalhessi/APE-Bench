

def test_the_overlay_never_writes_into_the_audit_it_reads(tmp_path, monkeypatch):
    """It planted a `matches.jsonl` symlink inside the audit directory to bridge a filename
    the renderer expected -- a read-only report writing into another stage's output, which is
    the one thing an immutable artifact tree must not allow. The renderer reads the judge's own
    filename now, with v4's spelling as a fallback because those audits are frozen."""

    import inspect

    from src.mathlib_review.analysis import report, review_overlay

    assert "symlink_to" not in inspect.getsource(report.overlay)
    source = inspect.getsource(review_overlay.build_overlay)
    assert '"semantic_matches.jsonl"' in source
    assert '"matches.jsonl"' in source      # still readable, for the frozen v4 audits
