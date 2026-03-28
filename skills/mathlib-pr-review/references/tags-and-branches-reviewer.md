# Tags, Branches, And CI For Reviewers

Use this file for branch, toolchain, and CI questions involving Lean, Batteries, and Mathlib.
This guide is mainly relevant for workflow and release-engineering reviews rather than ordinary code
review.

Derived from the official Lean/Mathlib tags and branches guide.

## Everyone should know

- Mathlib PRs should come from forks.
- Lean PRs that may break Batteries or Mathlib should be rebased onto `nightly-with-mathlib` so
  combined CI can run.

## Key branch and tag concepts

- Lean development happens on `master`, with stable tags, release candidates, and nightly tags.
- Lean PRs that build successfully receive PR toolchains of the form
  `leanprover/lean4-pr-releases:pr-release-NNNN`.
- Mathlib and Batteries both have `nightly-testing`, `lean-pr-testing-NNNN`, and `bump/v4.X.Y`
  workflows for adapting to upstream Lean changes.
- For Mathlib, these adaptation branches and tags live on
  `leanprover-community/mathlib4-nightly-testing`.

## Review-relevant distinctions

- `nightly-testing` is for ongoing adaptation work and is not guaranteed to build cleanly or be
  maintainer-reviewed.
- `bump/v4.X.Y` is the reviewed, protected branch preparing the next Lean release transition.
- Adaptation PRs typically move changes from `nightly-testing` into `bump/v4.X.Y`.
- When Lean changes also break Batteries, a Mathlib adaptation branch may need to track a matching
  Batteries `lean-pr-testing-NNNN` branch.

## Combined CI

- Combined Lean/Mathlib CI relies on `nightly-with-mathlib`.
- If a Lean PR is based on the wrong nightly, bots will comment and Mathlib CI may not run.
- Successful combined CI creates or updates the matching `lean-pr-testing-NNNN` workflow on the
  Mathlib nightly-testing fork.

## Review use

- Use this guide for comments about rebasing, branch targets, toolchain selection, or adaptation-PR
  process.
- These workflow issues are usually separate from merge readiness of an ordinary Mathlib theorem PR,
  but they matter a lot for core/toolchain and release-transition work.
