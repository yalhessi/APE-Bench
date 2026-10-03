# A same-model critic confirmed every filing it was shown; does a critic on another model, or with the evidence, do more?

**Status** — open (2026-10-03, `review-designs`). D2 `structured_critic/2`, one rep, read as not a
lever as built. Nothing built toward the variants below.
**Cost** — a variant is a config or a few lines in `structured_critic.py`, plus one subscription
window per dev rep (the critic stage cost about as much as D1: 30.7M processed tokens).

**Motivating example.** D2 on Claude Opus 5.5, reading D1 `structured/3` rep 1 (also Opus 5.5),
on the dev held-out 12 (`probe_dev_structured3_critic_hygiene_claude_sub_rep1`, read in
`results/pr_review_v5/probes/review-designs-2026-10-02/README.md`): 11 of 23 against D1's 10, so
+1 against plan §5's +2. Over 1,950 cells the critic conceded 1,784, overturned 28 (25 verified)
and **refuted 0 of D1's 138 filings**. The +1 is a recovery (33285's golf, which `structured/3`
lost and the hygiene reps and `structured/2` reached), not a new reach. Two D1 passes of two
contract versions reach 12 together for about the same tokens.

0 refutes in 138 is either a first stage whose filings are right, or a critic that defers to a
ledger written in its own voice. One rep cannot tell these apart. The overturns lean to
`statement` (14 of 28), while the residual misses are mostly convention and mechanism knowledge.

**What would close it.** One dev rep of each variant, read by plan §5's D2 rule (+2 at control
emission at most 2.0) against the same first stage:
- the critic on a different model from the first stage (gpt-5.5, or Sonnet against an Opus
  ledger);
- the critic shown the first stage's evidence (its compiles and lookups), not only the ledger's
  reasons;
- the critic's overturn effort aimed at the concerns where the misses sit, rather than spread
  evenly over every `no_issue` cell.

Beside them, the cost-matched rival: K independent D1 passes unioned (plan of 2026-10-01, §5). If
no variant beats the union per token, the critic is the wrong use of a second window.

**Start here.**
- read: `src/ape/tasks/lean_tasks/formal_math/review/structured_critic.py` (positions,
  `_submit_critique`), the README section above, `read_critic.py` beside it.
- run: `ape/bin/python -m src.mathlib_review.review.cli plan --config configs/designs/structured_critic_dev_claude_sub.yaml --run-name <name> --of probe_dev_structured3_hygiene_claude_sub_rep1`
- bounded by: the selection ruling (`.claude/rules/mathlib-review.md`). A critic that only
  refutes is a filter on D1's output, so it would be selection. These variants change what gets
  generated.
