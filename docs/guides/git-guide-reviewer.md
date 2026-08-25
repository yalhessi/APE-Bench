# Git Guide For Reviewers

Use this file for contributor-workflow questions around forks, branches, remotes, and checking out
PRs. This guide is mainly procedural; it is usually not the basis for code-quality findings.

Derived from the official Mathlib git guide.

## Recommended contributor setup

- Contributors should work from a fork of `mathlib4`, not by pushing directly to the main repo.
- The usual remote layout is:
  `origin` for the contributor's fork and `upstream` for `leanprover-community/mathlib4`.
- The local `master` branch should track `upstream/master`.
- The guide recommends setting `push.default current` and `push.autoSetupRemote true`.
- An optional pre-commit hook can block accidental commits to `master`.

## Daily workflow

- Update `master` before creating a new branch.
- Create feature branches from the up-to-date `master`.
- If work depends on another PR, switch to that PR branch, pull, and create a new branch on top.
- Push the feature branch to the fork, then open the PR from the fork.

## Working with other people's PRs

- `gh pr checkout <number>` is the preferred workflow when GitHub CLI is available.
- The manual fallback is to add the contributor's fork as a remote, fetch it, and check out the
  relevant branch.
- Giving collaborator access or building someone else's branch carries a security risk, so the guide
  explicitly tells contributors to do this only with people they trust.

## Review use

- Use this guide when a contributor needs process help, such as moving work off `master`, opening a
  PR from a fork, or basing follow-up work on top of an existing PR.
- Workflow mistakes from this guide are usually advisory unless the task being reviewed is itself
  about repository process or release engineering.
