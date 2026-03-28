# Pull Request Title And Description Conventions For Reviewers

Use this file when a review depends on PR metadata rather than Lean code.

Derived from the official Mathlib pull request title and description guide.

## Required title shape

- Titles should use `type(optional-scope): subject`.
- Allowed `type` values are `feat`, `fix`, `doc`, `style`, `refactor`, `test`, `chore`,
  `perf`, and `ci`.
- The scope is optional, but when present it should usually be the changed module or directory and
  omit the `Mathlib` prefix.
- The subject should use imperative present tense, start lowercase, and not end with a period.

## Required description shape

- The description body should also use imperative present tense.
- It should explain what changed, why it changed, and how the new behavior differs from before.
- Optional footer material includes breaking-change notes and `Closes #...` lines for resolved
  issues.
- If the PR depends on other PRs, list them after a blank line as checkbox items like
  `- [ ] depends on: #NNNN`.

## Review use

- A vague title or discussion-only description is worth flagging because the merged PR metadata
  becomes part of project history.
- If a question or brainstorming note belongs in the PR discussion, it should usually move below
  the `---` separator rather than replacing the actual description of the change.
- Metadata issues are usually advisory, but they are important enough to mention when the title or
  description would make the final history hard to search or understand.
