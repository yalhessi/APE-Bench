# Name-token search baseline (2026-09-26)

**Question.** Would a naive similarity search from the PR's own declaration names reach the
analogue the maintainer compared against (reader A's `analogue` for the 43 library- and
sibling-reference design asks)?

**Method.** Index: every declaration name in one built base (`workspaces/7ee74e7d…`, Lean
4.27.0-rc1, the newest available; the val1000 PRs have no built bases of their own, so the
library state differs from each PR's by up to a few months). 217,318 raw matches. Query: the
tokens (snake and camel split) of the last two declarations added in the hunk the comment is
attached to. Score: idf-weighted shared tokens. Result: the rank of the analogue's last name
component among the top 20 (`name_search_baseline.json`).

**Result.** Analogue present in the index for **32 of 43**; ranked in the top 10 for **0 of 43**
(one at rank 19: `QuotSMulTop`, whose token is in the PR's lemma name). The top hits are name
lookalikes that would be wrong analogues: `IsCountablyCompact` → `isCountablyGenerated` lemmas
(the maintainer's analogue is `IsCompact`'s filter form); `orbit` → `val_preimage_orbit` (analogue:
the `MulAction.orbit` API); `absDiff` → `contDiff_abs` (analogue: `edist`); `IsStarProjection.add`
→ `starProjection_add_starProjection_orthogonal` (analogue: `IsIdempotentElem.add_sub_mul_of_commute`).

**Reading.** Name similarity is not how these analogues are found, and a reviewer who trusted its
top hits would compare against the wrong sibling in nearly every case, which is the risk the user
named. The analogues are reached by role (the same kind of object in the same position) and by
API shape (the unfolded form of an existing predicate), which the next retrieval must target.
