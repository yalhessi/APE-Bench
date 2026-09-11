"""
Zulip display name -> GitHub login -> maintainer role.

Zulip messages carry only `sender_full_name`, a display name. The community website
publishes `teams.yaml` (team -> display names) and `people.yaml` (display name ->
GitHub login), and Zulip display names match `people.yaml`'s `name` field exactly for
the Mathlib regulars. That join is what lets the store weight a message by whether the
author is someone whose opinion sets repository norms.

`src/datasets/pr_review_v2/roster.py` builds the same roster for the GitHub side; this
module deliberately re-derives it from the same two files rather than importing that
package, so the Zulip store stays free of pipeline-generation code edges. The two are
kept honest by a test that compares the derived logins against that roster's snapshot.

The result is pinned in-package (`data/identity.tsv`), following roster.py's precedent:
roster drift is an audited threat, so the mapping used by a build must be a versioned
artifact rather than whatever the website said that day.

Usage:
  python -m src.datasets.zulip.identity [--refresh]
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Set, Tuple

import httpx
import yaml

#: The fetch URL and the three roster teams are shared with the reviewer roster: they used to be
#: spelled here and in `pr_review_v2/roster.py`, independently, for the same reason.
from src.datasets.pull_requests.roster import DATA_URL, ROSTER_TEAMS  # noqa: E402
from src.datasets.pull_requests.roster import fetch_yaml as _fetch_yaml  # noqa: E402

IDENTITY_VERSION = "zulip-identity/1"
DEFAULT_PATH = Path(__file__).parent / "data" / "identity.tsv"


#: Zulip display names end in a "bot" word rather than GitHub's `[bot]` suffix, so
#: `pr_review_v2.derive.is_bot`'s login rule does not transfer; this is the display-name
#: equivalent. Bots are ~12k of the corpus's messages and carry no norm signal, so
#: leaving them untagged would quietly weight any downstream frequency count.
_BOT_NAME = re.compile(r"\bbots?\b", re.IGNORECASE)


def is_bot(display_name: str) -> bool:
    return bool(_BOT_NAME.search(display_name or ""))


class Person(NamedTuple):
    display_name: str
    github: str
    is_maintainer: bool


class Identities:
    """Display-name lookup. Unknown names resolve to (None, False), never an error."""

    def __init__(self, people: Dict[str, Person]):
        self._people = people

    def __len__(self) -> int:
        return len(self._people)

    def __contains__(self, display_name: str) -> bool:
        return display_name in self._people

    def resolve(self, display_name: str) -> Tuple[Optional[str], bool]:
        person = self._people.get(display_name)
        return (person.github, person.is_maintainer) if person else (None, False)

    def maintainer_logins(self) -> Set[str]:
        return {p.github for p in self._people.values() if p.is_maintainer}

    def rows(self) -> List[Person]:
        return sorted(self._people.values())


def fetch_identities() -> Tuple[Identities, List[str]]:
    """Returns (identities, display names on a roster team with no people.yaml entry)."""
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        teams = _fetch_yaml(client, "teams.yaml")
        people = _fetch_yaml(client, "people.yaml")

    login_by_name: Dict[str, str] = {}
    for entry in people or []:
        name = str((entry or {}).get("name", "")).strip()
        # Lower-cased because GitHub logins are case-insensitive and every other
        # login-keyed artifact in this repo (pr_review_v2's roster, comment authors)
        # is lower-cased; keeping people.yaml's display casing would silently break
        # those joins.
        github = str((entry or {}).get("github", "")).strip().lower()
        if name and github:
            login_by_name[name] = github

    roster_names: Set[str] = set()
    for team in teams or []:
        if str((team or {}).get("name", "")).strip() in ROSTER_TEAMS:
            roster_names.update(str(m).strip() for m in (team.get("members") or []))

    resolved = {
        name: Person(name, login, name in roster_names)
        for name, login in login_by_name.items()
    }
    unmapped = sorted(roster_names - set(login_by_name))
    return Identities(resolved), unmapped


def write_snapshot(identities: Identities, unmapped: List[str], path: Path = DEFAULT_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Zulip display name -> GitHub login -> maintainer flag ({IDENTITY_VERSION}).",
        "# Built by src/datasets/zulip/identity.py from the leanprover-community website",
        "# data (teams.yaml + people.yaml). Pinned in-package because roster drift would",
        "# otherwise silently change what a rebuild considers a maintainer opinion.",
        f"# {len(identities)} people; "
        f"{sum(1 for p in identities.rows() if p.is_maintainer)} on a roster team.",
    ]
    if unmapped:
        lines.append(f"# Roster members with no people.yaml mapping: {', '.join(unmapped)}")
    lines.append("display_name\tgithub\tis_maintainer")
    lines += [
        f"{p.display_name}\t{p.github}\t{'1' if p.is_maintainer else '0'}"
        for p in identities.rows()
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def load_identities(path: Path = DEFAULT_PATH) -> Identities:
    """Load the pinned snapshot. Builds never hit the network."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} missing — run `python -m src.datasets.zulip.identity --refresh`"
        )
    people: Dict[str, Person] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or line.startswith("display_name\t"):
            continue
        display_name, github, flag = line.split("\t")
        people[display_name] = Person(display_name, github, flag == "1")
    return Identities(people)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Re-fetch and rewrite the snapshot")
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args(argv)

    if args.refresh or not args.path.exists():
        identities, unmapped = fetch_identities()
        write_snapshot(identities, unmapped, args.path)
        if unmapped:
            print(f"unmapped roster members ({len(unmapped)}): {', '.join(unmapped)}")
    else:
        identities = load_identities(args.path)

    maintainers = sum(1 for p in identities.rows() if p.is_maintainer)
    print(f"{args.path}: {len(identities)} people, {maintainers} maintainers/reviewers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
