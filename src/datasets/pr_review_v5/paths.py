"""The one place v5 names its own roots and the earlier-generation artifacts it reads.

v5 owns no gold and no releases. It *consumes* a v4 release (work units, episodes, change
graphs) and a v4 treatment's modification inventory, and it writes only under `RESULTS`.
Nothing here writes into a v4 root: `verify_frozen.FROZEN_ROOTS` covers
`inputs/pr_review_v4` and `results/pr_review_v4`, and a v5 artifact landing in either would
fail the integrity gate that every v4 result depends on.

Paths are repo-root-relative on purpose, for the same reason they are in v4: manifests
record artifact paths through `display_path()`, which relativizes against the working
directory, so the recorded strings are only reproducible when tooling runs from the repo
root. Call `assert_repo_root()` from any entry point that writes a manifest.
"""

from pathlib import Path

# --- v4 artifacts v5 reads (never writes) -------------------------------------------

#: Releases carry the gold-free generation inputs: work units, episodes, change graphs.
V4_RELEASES = Path("inputs/pr_review_v4/releases")

#: The modification inventory is a *treatment* artifact, not part of a release, and it is
#: what specialist scheduling enumerates from.
V4_TREATMENTS = Path("inputs/pr_review_v4/treatments")

# --- Context corpora ----------------------------------------------------------------

#: The review-situation corpus precedent retrieval ranks over (~34.6k anchored comments).
PRECEDENT_CORPUS = Path("inputs/pr_review_v2/corpus/mathlib_review_comments.jsonl")

#: The persisted dense precedent index. Built once by `precedent_index.py`; without it the
#: retriever would re-embed a 105 MB corpus in every worker process.
PRECEDENT_INDEX = Path("data/pr_review_v5/precedent_index")

#: The Zulip discussion store. Read-only, and every read is gated (`as_of` + `exclude_pr`).
ZULIP_STORE = Path("data/zulip/corpus/zulip.sqlite3")

# --- v5's own roots -----------------------------------------------------------------

RESULTS = Path("results/pr_review_v5")
RUNS = RESULTS / "runs"


def run_dir(run_name: str) -> Path:
    """Every v5 artifact for a run hangs off its `run_name`, and only off its `run_name`.

    v4 spells a run's identity three times — `dataset.run_name` (which names the
    orchestrator scratch dir), the parent of `dataset.output_file`, and the release name
    repeated in up to eight downstream `--path` flags — with nothing enforcing that they
    agree. Deriving every path from one name is what makes a v5 run reproducible from its
    config alone.
    """

    return RUNS / run_name


def assert_repo_root() -> None:
    """Fail loudly if the process was not launched from the repository root."""

    missing = [
        marker for marker in ("src/datasets/pr_review_v5", "src/datasets/pr_review_v4")
        if not Path(marker).is_dir()
    ]
    if missing:
        raise RuntimeError(
            "pr_review_v5 tooling must run from the repository root; missing "
            f"{missing}. Manifest paths are stored relative to the working directory, so "
            "running from elsewhere writes unreproducible provenance."
        )
