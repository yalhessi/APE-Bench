"""
Read and browse the Zulip store.

  # full-text search, newest Mathlib maintainers only
  python -m src.datasets.zulip.browse --search "naming convention" --maintainers-only

  # the thread a PR description links to, as it stood when review began
  python -m src.datasets.zulip.browse --url "https://leanprover.zulipchat.com/#narrow/…" \
      --as-of 2025-12-22T21:15:39Z

  # what the community said about a declaration
  python -m src.datasets.zulip.browse --decl BddAbove.closure

  # threads referencing a PR (analysis only — see --include-self)
  python -m src.datasets.zulip.browse --pr 33145 --include-self

`--as-of` is the gate: it drops every message at or after that instant, and (with
`--pr`) every message referencing the PR itself. Without it you are reading the
present, which is fine for browsing and wrong for anything measuring a reviewer.
"""

import argparse
import sys

from .config import ZulipConfig
from .render import render_hits, render_thread
from .store import ZulipStore


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--search", metavar="QUERY", help="Full-text search (FTS5/BM25)")
    mode.add_argument("--url", help="Resolve a Zulip permalink to its thread")
    mode.add_argument("--pr", type=int, help="Threads referencing this mathlib4 PR")
    mode.add_argument("--decl", help="Threads referencing this declaration")
    mode.add_argument("--stats", action="store_true", help="Store summary")

    parser.add_argument("--as-of", dest="as_of", help="Drop messages at/after this instant")
    parser.add_argument("--since", help="Search lower bound (YYYY-MM-DD)")
    parser.add_argument("--until", help="Search upper bound (YYYY-MM-DD, exclusive)")
    parser.add_argument("--streams", nargs="*", help="Restrict search to these stream names")
    parser.add_argument("--sender", nargs="*", dest="senders", help="Restrict to these authors")
    parser.add_argument("--maintainers-only", action="store_true")
    parser.add_argument(
        "--include-bots", action="store_true", help="Keep CI/notification bot messages"
    )
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument(
        "--max-messages", type=int, default=None, help="Cap messages printed per thread"
    )
    parser.add_argument(
        "--include-self", action="store_true",
        help="With --pr: keep messages that reference the PR itself (analysis, not review)",
    )
    args = parser.parse_args(argv)

    config = ZulipConfig()
    with ZulipStore(config.sqlite_path) as store:
        if args.stats:
            messages, threads = store.counts()
            print(f"messages {messages:,}   threads {threads:,}")
            for key, value in sorted(store.meta().items()):
                print(f"{key:20s} {value}")
            return 0

        if args.search:
            hits = store.search(
                args.search,
                since=args.since,
                until=args.until,
                streams=args.streams,
                senders=args.senders,
                maintainers_only=args.maintainers_only,
                exclude_bots=not args.include_bots,
                as_of=args.as_of,
                limit=args.limit,
            )
            if not hits:
                print("no matches")
                return 1
            print(render_hits(hits))
            return 0

        if args.url:
            view = store.resolve_url(args.url, as_of=args.as_of)
            if view is None:
                print("thread not found in the store (wrong stream, or outside the build window)")
                return 1
            print(
                render_thread(
                    view.thread, view.messages,
                    truncated=view.truncated, max_messages=args.max_messages,
                )
            )
            return 0

        views = (
            store.threads_for_pr(args.pr, as_of=args.as_of, exclude_self=not args.include_self)
            if args.pr
            else store.threads_mentioning(args.decl, as_of=args.as_of)
        )
        if not views:
            print("no threads")
            return 1
        for view in views[: args.limit]:
            print(
                render_thread(
                    view.thread, view.messages,
                    truncated=view.truncated, max_messages=args.max_messages,
                )
            )
        return 0


if __name__ == "__main__":
    sys.exit(main())
