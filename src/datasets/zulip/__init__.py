"""
Mathlib Zulip discussion store: reading/browsing infrastructure.

Zulip is where Mathlib's conventions are argued about and decided, typically well
before they show up as in-tree prevalence. That makes it the only evidence source
available to us that *precedes* in-repo adoption (docs/research/
pr-review-v5-principled-design.md §D2).

This package is deliberately a peer of the pipeline generations rather than part of
any of them: nothing here imports `pr_review_v2`/`v3`/`v4`, so a future consumer in
any generation inherits no forbidden code edge. The single module with a data edge to
an earlier generation is `citations.py`, and nothing in the core store imports it.

Stages:
    sync      clone/pin the leanprover-community/archive repo   (data/zulip/archive)
    build     normalize + tag + index                           (data/zulip/corpus)
    browse    read/search the result                            (CLI)

Correctness note: the build window is an operational/size choice. The mechanism that
keeps a read leak-free is `store.as_of`, which every read path goes through.
"""
