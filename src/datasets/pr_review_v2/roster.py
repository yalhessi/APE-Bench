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

DATA_URL = (
    "https://api.github.com/repos/leanprover-community/leanprover-community.github.io"
    "/contents/data/{name}"
)
ROSTER_TEAMS = {"Admin team", "Mathlib maintainers", "Mathlib reviewers"}
# Kept inside the package (not data/, which is gitignored): the roster is a
# versioned snapshot per spec §3.1, and roster drift is an audited threat (§7.7).
DEFAULT_OUTPUT = Path(__file__).parent / "data" / "mathlib_roster.txt"

# Known logins for roster members missing from people.yaml; checked against
# GitHub/Zulip profiles when added. Keep sorted, comment with the display name.
MANUAL_LOGINS: Dict[str, str] = {}


def _fetch_yaml(client: httpx.Client, name: str):
    response = client.get(
        DATA_URL.format(name=name), headers={"Accept": "application/vnd.github.raw+json"}
    )
    response.raise_for_status()
    return yaml.safe_load(response.text)


def build_roster() -> Tuple[Set[str], List[str]]:
    """Returns (github logins, unmapped display names)."""
    with httpx.Client(timeout=30.0) as client:
        teams = _fetch_yaml(client, "teams.yaml")
        people = _fetch_yaml(client, "people.yaml")

    login_by_name = {
        str(p.get("name", "")).strip(): str(p.get("github", "")).strip()
        for p in people or []
        if p and p.get("github")
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


def write_roster(output: Path) -> Path:
    logins, unmapped = build_roster()
    lines = [
        "# Mathlib reviewer roster (spec §3.1): admin + maintainers + reviewers teams,",
        "# built by src/datasets/pr_review_v2/roster.py from leanprover-community.github.io data.",
        f"# {len(logins)} logins; {len(unmapped)} team members had no GitHub mapping (listed below).",
        *sorted(logins),
        *(f"# UNMAPPED: {name}" for name in unmapped),
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")
    return output


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    path = write_roster(target)
    print(path)
