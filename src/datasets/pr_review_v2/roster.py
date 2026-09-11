"""
Build the curated reviewer roster (spec §3.1) from the leanprover-community
website data: members of the "Mathlib maintainers" and "Mathlib reviewers"
teams (plus the admin team), mapped to GitHub logins via people.yaml.

This matters because GitHub's author_association only reports MEMBER for
*public* org memberships — active Mathlib maintainers routinely appear as
CONTRIBUTOR (observed on real PRs), so association alone misses reviewers.

Usage:
  python -m src.datasets.pr_review_v2.roster [output_path]

Names without a people.yaml mapping are written as comments so the gap is
visible; extend the manual section below as they get resolved.
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

import httpx
import yaml

from ape.utils.project import PROJECT_ROOT

# The fetch, the team set and the writer moved to `src/datasets/pull_requests/roster.py`, which is
# shared with `zulip/identity.py`. Re-exported so existing callers keep working.
from src.datasets.pull_requests.roster import (  # noqa: E402
    DATA_URL, MANUAL_LOGINS, ROSTER_TEAMS, build_roster, dated_roster_path, write_roster,
)

#: Deliberately beside the code rather than under `inputs/`, which is where it belongs and where it
#: cannot go: nine frozen v4 release manifests declare this exact path with a hash. It is read, never
#: written -- `write_roster` refuses it, and running this module writes a dated snapshot instead.
DEFAULT_OUTPUT = Path(__file__).parent / "data" / "mathlib_roster.txt"


if __name__ == "__main__":
    print(write_roster(Path(sys.argv[1]) if len(sys.argv) > 1 else dated_roster_path()))
