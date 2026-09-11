"""The curated reviewer roster (spec §3.1): fetched from leanprover-community, written to a dated file.

Two modules fetched the same two files with the same three team names -- `pr_review_v2/roster.py`
for the reviewer roster and `zulip/identity.py` for display-name identities. The fetch and the
team set live here now; each keeps what it builds from them.

**Never written over the pinned roster.** `src/datasets/pr_review_v2/data/mathlib_roster.txt` is
declared with a hash by nine frozen release manifests, and `pr_review_v2/roster.py` used to write
there by default when run without arguments -- one invocation would have failed `verify_frozen` for
every v4 release. New snapshots go to `inputs/pull_reviews/rosters/mathlib_roster_<date>.txt`.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Set, Tuple

import httpx
import yaml

from src.mathlib_review.paths import LEGACY_V2_ROSTER, PULL_REVIEWS_ROSTERS

DATA_URL = (
    "https://api.github.com/repos/leanprover-community/leanprover-community.github.io"
    "/contents/data/{name}"
)

#: Teams whose members set or enforce Mathlib norms. GitHub's `author_association` reports
#: MEMBER only for *public* org membership, so association alone misses active maintainers.
ROSTER_TEAMS = frozenset({"Admin team", "Mathlib maintainers", "Mathlib reviewers"})

#: Known logins for roster members missing from people.yaml; checked against GitHub/Zulip
#: profiles when added. Keep sorted, comment with the display name.
MANUAL_LOGINS: Dict[str, str] = {}


def fetch_yaml(client: httpx.Client, name: str):
    response = client.get(
        DATA_URL.format(name=name), headers={"Accept": "application/vnd.github.raw+json"})
    response.raise_for_status()
    return yaml.safe_load(response.text)


def fetch_team_data() -> Tuple[list, list]:
    """(teams.yaml, people.yaml) as parsed YAML."""
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        return fetch_yaml(client, "teams.yaml"), fetch_yaml(client, "people.yaml")


def build_roster() -> Tuple[Set[str], List[str]]:
    """Returns (github logins, lower-cased; roster-team members with no GitHub mapping)."""
    teams, people = fetch_team_data()
    login_by_name = {
        str(p.get("name", "")).strip(): str(p.get("github", "")).strip()
        for p in people or [] if p and p.get("github")
    }
    members: Set[str] = set()
    for team in teams or []:
        if str(team.get("name", "")).strip() in ROSTER_TEAMS:
            members.update(str(m).strip() for m in team.get("members") or [])
    logins: Set[str] = set()
    unmapped: List[str] = []
    for name in sorted(members):
        login = login_by_name.get(name) or MANUAL_LOGINS.get(name)
        if login:
            logins.add(login.lower())
        else:
            unmapped.append(name)
    return logins, unmapped


def dated_roster_path(on: date | None = None) -> Path:
    return PULL_REVIEWS_ROSTERS / f"mathlib_roster_{(on or date.today()).isoformat()}.txt"


def write_roster(output: Path) -> Path:
    if Path(output).resolve() == LEGACY_V2_ROSTER.resolve():
        raise PermissionError(
            f"refusing to write {LEGACY_V2_ROSTER}: nine frozen release manifests hash it, so "
            "rewriting it fails verify_frozen for every v4 release. Write a dated snapshot "
            f"under {PULL_REVIEWS_ROSTERS} instead.")
    logins, unmapped = build_roster()
    lines = [
        "# Mathlib reviewer roster (spec §3.1): admin + maintainers + reviewers teams,",
        "# built by src/datasets/pull_reviews/roster.py from leanprover-community.github.io data.",
        f"# {len(logins)} logins; {len(unmapped)} team members had no GitHub mapping (listed below).",
        *sorted(logins),
        *(f"# UNMAPPED: {name}" for name in unmapped),
    ]
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    print(write_roster(Path(sys.argv[1]) if len(sys.argv) > 1 else dated_roster_path()))
