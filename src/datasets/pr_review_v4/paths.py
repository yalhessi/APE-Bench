"""The one place v4 names artifacts produced by earlier pipeline generations.

v4's gold descends from the v2 collector and the v3 intervention builder, and twelve v4
release manifests record these files as provenance inputs. So the *data* dependency is
correct and permanent — what was wrong was spelling these paths as literals in ten
different modules, which made the generation boundary invisible and unauditable.

These are frozen inputs, not a live dependency on v2/v3 *code*: nothing here imports
from `pr_review_v2` or `pr_review_v3`, and `test_pr_review_v4_no_prior_generation`
enforces that.

Paths are repo-root-relative on purpose. Manifests record artifact paths through
`display_path()`, which relativizes against the current working directory, so the
recorded strings are only reproducible when tooling runs from the repo root — call
`assert_repo_root()` from any entry point that writes a manifest.
"""

from pathlib import Path

# --- Frozen provenance inputs from earlier generations ------------------------------

#: v3 intervention gold (schema i5). The single most load-bearing legacy artifact:
#: v4's judgment graph, scope migration, and historical store all derive from it.
LEGACY_INTERVENTIONS_V5 = Path("inputs/pr_review_v3/interventions_v5.jsonl")

#: v2 annotated first-round review records — the source of v4's episode allowlist.
LEGACY_V2_ANNOTATED = Path("inputs/pr_review_v2/mathlib_pr_review_v2_annotated_20260612.jsonl")

#: Immutable cached GitHub collection bundles; v4's raw event ledger is built from these.
LEGACY_V2_BUNDLES = Path("data/pr_review_v2/cache/bundles")

#: Immutable cached Git compare responses; v4's review-time diffs are derived from these.
LEGACY_V2_COMPARES = Path("data/pr_review_v2/cache/compares")

#: Mathlib maintainer roster, used to scope temporally safe precedent retrieval.
LEGACY_V2_ROSTER = Path("src/datasets/pr_review_v2/data/mathlib_roster.txt")

# --- v4's own roots ------------------------------------------------------------------

RELEASES = Path("inputs/pr_review_v4/releases")
TREATMENTS = Path("inputs/pr_review_v4/treatments")
RESULTS = Path("results/pr_review_v4")
AUDITS = RESULTS / "audits"
RUNS = RESULTS / "runs"


def assert_repo_root() -> None:
    """Fail loudly if the process was not launched from the repository root.

    Manifest paths are stored relative to the working directory, so running a builder
    from elsewhere would silently write unreproducible provenance into an otherwise
    immutable artifact.
    """

    missing = [
        marker for marker in ("src/datasets/pr_review_v4", "inputs/pr_review_v4")
        if not Path(marker).is_dir()
    ]
    if missing:
        raise RuntimeError(
            "pr_review_v4 tooling must run from the repository root "
            f"(cannot see {', '.join(missing)} from {Path.cwd()})"
        )
