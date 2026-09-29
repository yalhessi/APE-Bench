"""The probe harness, held to what the post-cutoff probe committed (`docs/plans/2026-09-29-probe-harness.md`).

These read the PR store and the releases under `inputs/`, so they need the linked data stores.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.mathlib_review.analysis import probes

SETS = Path("configs/probe_sets")
POST = probes.load_probe_set(SETS / "postcutoff_2026_07_08_v1.yaml")
#: The digest recorded when the validation feedback was first extracted, before this harness.
VAL_FEEDBACK_SHA256 = "215c28a3da9fd9dbf045622c32dd019791a7406f5748678d063a666bc506c10d"


def test_every_set_spec_loads():
    names = {probes.load_probe_set(p).name for p in SETS.glob("*.yaml")}
    assert {"postcutoff_2026_07_08_v1", "val_small12", "dev_medium_0_3_0"} <= names


def test_a_feedback_source_is_a_draw_or_the_release_never_both():
    with pytest.raises(ValueError, match="not both"):
        probes.FeedbackSource(draw="x", prs_of_release=True)
    with pytest.raises(ValueError, match="not both"):
        probes.FeedbackSource()


def test_the_post_cutoff_feedback_re_extracts_exactly():
    assert probes.extract_feedback(POST) == json.loads(POST.feedback_file.read_text())


def test_the_validation_feedback_re_extracts_to_its_recorded_digest():
    val = probes.extract_feedback(probes.load_probe_set(SETS / "val_small12.yaml"))
    digest = hashlib.sha256(json.dumps(val, ensure_ascii=False, indent=1).encode()).hexdigest()
    assert digest == VAL_FEEDBACK_SHA256


def test_a_test_set_pr_is_refused(tmp_path):
    test_pr = sorted(json.loads(probes.TEST_MANIFEST.read_text())["pr_numbers"])[0]
    (tmp_path / "input").mkdir()
    (tmp_path / "input" / "episodes.jsonl").write_text(
        json.dumps({"pr_number": test_pr, "episode_id": "x"}) + "\n")
    spec = probes.ProbeSet(name="t", release=tmp_path, dataset_config=Path("x.yaml"),
                           pr_numbers=[test_pr], feedback={"prs_of_release": True},
                           probe_dir=tmp_path / "probe")
    with pytest.raises(ValueError, match="test-set PRs"):
        probes.extract_feedback(spec)
