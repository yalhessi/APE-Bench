"""Record what a reviewer and a matcher are shown for PR 42184, so two code versions can be compared.

Run from the repository root:

    ape/bin/python results/pr_review_v5/probes/named-episode-review-2026-11-25/capture.py <out>

Nothing here calls a model. For `solo-v1` and `pr-search-v1` it previews the named command
(`review.cli plan`) twice: on the profile's release, and on a copy that holds only
`input/episodes.jsonl`. It writes each first message, tool schema set and generation record. It
then renders the final matcher message for both saved 42184 samples
(`scope_solo_opus55_42184_{ordinary,comparison}_20261124`). Each sample is rendered under each
question policy, once through the historical solo loader and once through the named review
projection of the same accepted findings.
"""

import contextlib
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

from src.mathlib_review.analysis import matching, probes, submissions
from src.mathlib_review.io import pretty_json_bytes
from src.mathlib_review.judge.ask_matching import render_matcher_prompt
from src.mathlib_review.review import cli, runner

CASE = "42184@c5474cb4"
SAMPLES = {"ordinary": "scope_solo_opus55_42184_ordinary_20261124",
           "guided": "scope_solo_opus55_42184_comparison_20261124"}
POLICIES = ("request_only", "questions")


def preview(reviewer, release=None):
    """The named `plan` output: the first message and the printed generation record."""
    original = runner.load_run

    def load(*args):
        dataset, scaffold, overrides = original(*args)
        if release is not None:
            dataset.release = release
        return dataset, scaffold, overrides

    runner.load_run = load
    try:
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            assert cli.main(["plan", "--reviewer", reviewer, "--case", CASE]) == 0
    finally:
        runner.load_run = original
    text = printed.getvalue()
    cut = text.rindex("\n{\n")
    message, generation = text[:cut], json.loads(text[cut + 1:])
    for run in generation["runs"].values():
        run.pop("tasks_dir")
        for record in run["episodes"].values():
            record.pop("message")
    (record,) = generation["runs"][reviewer]["episodes"].values()
    return message, record.pop("mcp_schemas"), generation


def accepted_findings(run):
    """The saved accepted findings, as a named archive projects them (`submissions.capture`)."""
    (result,) = (Path(".ape/runs") / run / "tasks").glob("*/task_result.json")
    raw = submissions.read(result)
    assert raw["success"] and raw["pr_number"] == 42184
    return [{"target": probes._solo_target(f.get("anchor")), "claim": f["claim"],
             "requested_change": f["suggested_fix"]} for f in raw["findings"]]


def matcher_message(source, policy, work):
    reference = probes.load_probe_set(submissions.REFERENCE)
    seal = {"42184": {"R1": "review"}}
    seal_path = work / f"seal-{policy}.json"
    seal_path.write_text(json.dumps(seal))
    plan = matching.plan_matching(reference, name="capture", seal=seal, seal_path=seal_path,
                                  sources={"review": probes.Source.model_validate(source)},
                                  out_dir=work / policy, question_policy=policy, harness_blind=True)
    return render_matcher_prompt(plan.packets, policy)


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory() as scratch:
        scratch = Path(scratch)
        release = scratch / "episodes-only"
        (release / "input").mkdir(parents=True)
        shutil.copy("inputs/probes/probe-2026-07-08-v1/input/episodes.jsonl", release / "input")
        for reviewer in ("solo-v1", "pr-search-v1"):
            for label, where in (("profile-release", None), ("episodes-only", release)):
                message, tools, generation = preview(reviewer, where)
                if where is not None:
                    generation["release"] = "<episodes-only copy>"
                stem = out / f"plan-{reviewer}-{label}"
                stem.with_suffix(".message.txt").write_text(message)
                stem.with_suffix(".tools.json").write_bytes(pretty_json_bytes(tools))
                stem.with_suffix(".generation.json").write_bytes(pretty_json_bytes(generation))
        for sample, run in SAMPLES.items():
            findings = scratch / f"{sample}-findings.json"
            findings.write_bytes(pretty_json_bytes({"42184": accepted_findings(run)}))
            routes = {"historical": {"kind": "solo", "run": run},
                      "named": {"kind": "findings_file", "path": str(findings)}}
            for route, source in routes.items():
                for policy in POLICIES:
                    work = scratch / f"{sample}-{route}"
                    work.mkdir(exist_ok=True)
                    text = matcher_message(source, policy, work)
                    (out / f"matcher-{sample}-{route}-{policy}.txt").write_text(text)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
