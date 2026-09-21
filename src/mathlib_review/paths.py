"""Where a review run reads from and writes to.

Moved out of `pr_review_v5` because it is not v5's: `judge_runner` in v4 imports `run_dir`
from here so a judge run's paths come from the generation run's name instead of three
free-form strings that must agree by hand. That was a backward v4 -> v5 edge for a path
convention neither generation owns.

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

# --- The PR store --------------------------------------------------------------------
#
# One raw directory per PR, from which every PR dataset is a projection. Payloads are gitignored
# (1-2 GB, a day of quota to rebuild); provenance is tracked, the Zulip store's pattern. See
# `src/datasets/pull_requests/__init__.py`.

#: The raw store: `pr/<n>/` payloads, `index.sqlite3`, `projections/`. Gitignored.
PULL_REQUESTS_STORE = Path("data/pull_requests")

#: Tracked provenance for the store: manifest, per-PR endpoint hashes, collection report,
#: acceptance baseline, dated rosters.
PULL_REQUESTS_TRACKED = Path("inputs/pull_requests")

#: Dated roster snapshots (spec §3.1 "snapshotted into a versioned file"). The v2 roster below
#: stays where nine frozen manifests pin it; new snapshots go here.
PULL_REQUESTS_ROSTERS = PULL_REQUESTS_TRACKED / "rosters"

#: Tracked provenance for the convention catalogue: the rows a snapshot scan produced, and the
#: manifest naming the snapshot they were read from. Small, derived and regenerable, so it is
#: tracked rather than gitignored -- the point of the catalogue is to be cited in an argument, and
#: an artifact that lives only in a scratchpad cannot be.
CONVENTIONS_TRACKED = Path("inputs/conventions")

# --- v5's own roots -----------------------------------------------------------------

RESULTS = Path("results/pr_review_v5")
RUNS = RESULTS / "runs"

#: Where a judged run's audit goes. Written here once because it was written twice -- as
#: `judge.runner.JUDGE_AUDIT_ROOT` and as `analysis.denominators._AUDIT_ROOT` -- and a run's
#: identity spelled in two places is the class of mistake `judge --of` exists to remove.
AUDITS = RESULTS / "audits"

#: The cross-run adjudication label store. One file, append-only, keyed by finding rather than
#: by run: a label is about a claim the system makes, and the same claim recurs across
#: repetitions. Outside `RUNS` and outside `AUDITS` for that reason -- it belongs to no single
#: run and must survive every one of them.
ADJUDICATIONS = RESULTS / "adjudications"


def run_dir(run_name: str) -> Path:
    """Every v5 artifact for a run hangs off its `run_name`, and only off its `run_name`.

    v4 spells a run's identity three times — `dataset.run_name` (which names the
    orchestrator scratch dir), the parent of `dataset.output_file`, and the release name
    repeated in up to eight downstream `--path` flags — with nothing enforcing that they
    agree. Deriving every path from one name is what makes a v5 run reproducible from its
    config alone.
    """

    return RUNS / run_name


LEGACY_INTERVENTIONS_V5 = Path("inputs/pr_review_v3/interventions_v5.jsonl")

#: v2 annotated first-round review records — the source of v4's episode allowlist.
LEGACY_V2_ANNOTATED = Path("inputs/pr_review_v2/mathlib_pr_review_v2_annotated_20260612.jsonl")

#: The scored set. A precedent drawn from one of these PRs is the answer rather
#: than a precedent, so the corpus builder excludes them outright.
V2_EVAL_SET = Path("inputs/pr_review_v2/mathlib_pr_review_v2_actionable_20260618.jsonl")

# --- artifact roots inherited from the v4 pipeline ------------------------------------
#
# Folded in from `pr_review_v4/paths.py`, which is where they were written and which is not a
# place they belong now that there is one pipeline. The v4 names are prefixed: both packages
# called their own outputs `RESULTS` and `RUNS`, and merging them silently would have made one
# of the two mean the other's directory.

#: Immutable cached GitHub collection bundles; v4's raw event ledger is built from these.
LEGACY_V2_BUNDLES = Path("data/pr_review_v2/cache/bundles")

#: Immutable cached Git compare responses; v4's review-time diffs are derived from these.
LEGACY_V2_COMPARES = Path("data/pr_review_v2/cache/compares")

#: Mathlib maintainer roster, used to scope temporally safe precedent retrieval.
#:
#: **It cannot move, and this is load-bearing.** It is an input living inside a code
#: package, which is the wrong place for data -- and nine frozen release manifests under
#: `inputs/pr_review_v4/` declare it at exactly this path with a hash. That root is frozen,
#: so the manifests cannot be rewritten, so the file cannot be relocated without failing
#: `verify_frozen`. Tried on 2026-09-08; nine manifests reported it missing.
#:
#: The consequence is bigger than the file: **deleting `src/datasets/pr_review_v2/` would
#: break the frozen-artifact gate for every v4 release.** Whatever happens to v2's code, this
#: path has to keep existing.
LEGACY_V2_ROSTER = Path("src/datasets/pr_review_v2/data/mathlib_roster.txt")

# --- v4's own roots ------------------------------------------------------------------

V4_RESULTS = Path("results/pr_review_v4")
V4_AUDITS = V4_RESULTS / "audits"
V4_RUNS = V4_RESULTS / "runs"


#: Root markers below.
#: Directories that exist iff the process is at the repository root.
#:
#: Deliberately not the review packages. This check existed twice -- once here naming
#: `pr_review_v5`/`pr_review_v4`, once in `pr_review_v4/paths.py` naming
#: `pr_review_v4`/`inputs/pr_review_v4` -- and both would start failing during the collapse,
#: when a marker they name stops existing. A root marker should outlive what it is guarding.
ROOT_MARKERS = ("src/ape", "src/datasets", "inputs")


def assert_repo_root() -> None:
    """Fail loudly if the process was not launched from the repository root.

    Manifest paths are stored relative to the working directory, so running a builder from
    elsewhere silently writes unreproducible provenance into an otherwise immutable artifact.
    """

    missing = [marker for marker in ROOT_MARKERS if not Path(marker).is_dir()]
    if missing:
        raise RuntimeError(
            "review tooling must run from the repository root; missing "
            f"{missing}. Manifest paths are stored relative to the working directory, so "
            "running from elsewhere writes unreproducible provenance."
        )

    # A worktree shares the main checkout's venv, and that venv's editable install pins
    # `ape` to the main checkout's src/. Everything under `src.` would then come from this
    # tree while the framework came from another -- refuse the mixed state.
    import ape

    origin = getattr(ape, "__file__", None)
    if origin is not None:
        framework = Path(origin).resolve().parent
        expected = (Path.cwd() / "src" / "ape").resolve()
        if framework != expected:
            raise RuntimeError(
                f"`ape` is imported from {framework}, not from this tree's {expected}. In a "
                "worktree the shared venv's editable install points at the main checkout; run "
                "with PYTHONPATH=src (pytest.ini and the Claude Code settings already do) so the "
                "framework and the pipeline come from the same tree."
            )
