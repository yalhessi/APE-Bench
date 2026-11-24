# APE-Bench

This fork studies how to review a Mathlib PR that already compiles. What would a maintainer ask the author to change, and why? AI-generated PRs are an intended use case. Keep them identifiable and included by default when building datasets.

## Before proposing an experiment

Look up the closest previous result in `docs/questions.md` and stopped approaches in `docs/dead-ends.md`. Follow the relevant entry to the saved run. For implementation status, start at `docs/PROJECT-STATUS.md` or `docs/plans/STATUS.md`.

In the [filing-contract experiment](results/pr_review_v5/probes/filing-contract-2026-10-12/), a missing review comment suggested the reviewer had withheld feedback. Reading the transcripts showed that it had recognized the topic but still lacked a concrete fix. A rule requiring it to file a comment would address only the first explanation. When a proposed change depends on a diagnosis like this, identify an observation that distinguishes the explanations and check a saved case.

When a case changes a project decision, record what we observed, what we inferred, and why it changed the choice. Keep an unresolved explanation in the investigation where it can be challenged.

## Agent skills

### Issue tracker

Track new specs and tickets in GitHub Issues. See [issue tracker](docs/agents/issue-tracker.md).

### Triage labels

Use the [triage labels](docs/agents/triage-labels.md) when assigning an issue's next step.

### Domain docs

See [domain documentation](docs/agents/domain.md) when naming a concept or revisiting a design decision.

## Working in this checkout

Work on `develop` or a topic worktree based on it. Worktrees share data stores and the editable Python environment. Check the [checkout and run procedures](docs/guides/checkout-and-runs.md) before changing shared artifacts, extending the harness, running a suite, or comparing review scores.

Use small logical commits with explicit paths. Ask before pushing, rewriting published history, or deleting branches. API-backed generation, ingestion and semantic judging are user-run. Provide the complete command and run local checks here.
