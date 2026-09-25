# Probe 3: does a PR-level job reach PR-level asks across PRs, or only on one? (2026-09-25)

Written before any reviewer ran.

**The question.** Rounds 1-2 replicated one effect: on 29464 the current brief reached 0 of 10
PR-level asks in two runs, and briefs that ask about the PR as a whole reached 4-10
(`docs/research/facet-brief-probe-2026-09.md`). That is one PR. This probe asks whether it holds
across PRs, especially AI-generated ones.

**The sample.** val1000 PRs with at least 2 round-1 asks that both readers label F12 (PR level),
excluding the five earlier probe PRs, with diffs under 40,000 characters. Drawn with seed 20250926:
- **AI:** all 5 eligible: 34773, 36641, 36856, 36912, 36914.
- **Main:** 5 of 9 eligible: 27841, 28728, 29513, 30650, 32315.

The reference set is those PRs' 23 agreed round-1 asks, 21 of them F12. No reviewer sees them.

**Conditions:** Claude reviewers, holding the same base-pinned search tools as round 1 (`mlgrep`,
`mlfind`, `mlshow`, `mlcount`). No compile: PR-level questions need none.
- **C:** the current generalist brief, one run.
- **P:** a PR-level-only brief, two runs (P1, P2), to measure stability.

**Matching.** Two blind matchers. C, P1 and P2 are shuffled per PR and stripped of any field that
reveals the condition.

**Reading rule.** The PR-level job is supported if all of these hold on both matchers:
- **reach:** P, counting an ask reached in either run, reaches at least 30% of the 21 F12 asks, and
  at least 3× as many F12 asks as C;
- **stability:** of the F12 asks either P run reaches, at least 50% are reached by both;
- **noise:** P files at most 4 findings per PR on average, per run.

Anything less is "this PR-level job did not generalise", with the untried designs listed.

**Also read, not pre-registered:**
- AI against main;
- C ∪ P against C on all 23 asks;
- P's findings on each PR, read for what they claim.
