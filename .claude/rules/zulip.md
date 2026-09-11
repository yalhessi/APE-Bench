---
paths:
  - "src/datasets/zulip/**"
---
# Zulip discussion store

- `store.gate(as_of=, exclude_pr=)` is the correctness mechanism, not the time window: it drops
  messages at or after the instant AND messages about the PR under review. Every read path calls it;
  it mirrors `retrieval/precedents.py::validate_precedents`.
- Generation-neutral by design: imports no pipeline generation; `citations.py` is the one module with
  a v2 data edge and nothing imports it.
- The one-year build answers "is this discussed" but cannot measure a trend; `emerging` maturity in
  the norm design needs a rebuild with `since: 2018-01-01`. Semantic tags have a reserved schema slot
  and are deliberately unbuilt — mechanical tags first.
- `zulip_search` returns empty 80% of the time in recorded runs. That is an open question about the
  queries, not the store: 10/10 eval PRs with a linked thread resolve under the gate.
