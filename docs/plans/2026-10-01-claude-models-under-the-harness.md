# Claude models under the project's harness, and the harness apart from the model (plan, 2026-10-01)

For a fresh session in a new worktree off `develop`, **after** `claude-code-harness` and
`post-carryover-replan` are both merged. The user's direction, 2026-10-01:
- separate the harness from the model and its configs, now that the Claude Code harness fix is
  being merged;
- learn whether Opus 5 and Opus 4.8 replicate Opus 5.5's review performance;
- Claude models run through the **Claude Code CLI directly, on the subscription** (no relay, no
  Anthropic provider);
- read on **both** sets: the dev held-out 12 (judge) and the post-cutoff set (blind matchers).

## What is already known (do not re-run)

| question | answer so far | where |
|---|---|---|
| Does the prompt or contract explain gpt's gap? | No. Claude given gpt's contract-v2 messages verbatim reaches 10 of 23 (brief X: 11). gpt_5.2 and gpt-5.5 under the same prompt reach 2 and 3. | `results/pr_review_v5/probes/contract-2026-10-01/` |
| Does investigation (compiles, lookups) explain it? | No. Under that prompt Claude made 35 calls, 6 compiles and 2.5 lookups; gpt-5.5 made 41, 9.5 and 6, and filed a third as much. Recall tracks how much the reviewer decides to ask for. | same |
| Does the APE-Agent harness limit gpt? | Not with gpt_5.2, reasoning off, brief G, on the six post-cutoff PRs. Under Claude Code (relay) it reaches what it does under APE-Agent (d = -0.04, -0.02). A reasoning-carried version is pre-registered there (`b7a7ca44`). | `claude-code-harness`, `a23892dc` |
| Is Claude's in-window reach memory? | Partly unknown. The post-cutoff probe (2026-09-29) found 79-107% of the in-window rate, at probe altitude. The swap reached its level with a third of its usual lookups, which memory would also produce. | `docs/todo/reviewer-model-gap.md` |

## What has to be built first (the subscription route)

`docs/todo/framework-defects-2026-09.md` on `claude-code-harness`, "Claude on a subscription",
lists what breaks when `llm_config.model_name: null` skips the relay. Each item becomes a fix
with a test:
1. **Credentials.** `HOME` is set to the attempt's `workspaces/`, so `~/.claude/.credentials.json`
   is not found. Pass `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`). The SDK passes the
   parent environment through.
2. **The model, pinned and recorded.** A scaffold field naming the Claude model (full name, never
   an alias, since an alias moves) goes into the scaffold config, so into the run plan's digest and
   the run name. `model=None`, the CLI default, is refused for a review run.
3. **Usage and limits.** Read token usage from the SDK's own result messages. Bind the
   `ExecutionLimits` token half: the subscription is zero-priced, and `cli plan` already refuses a
   zero-priced run without a token cap.
4. **Session id and transcript**, from the SDK's messages rather than the relay.
5. **A spent usage limit is a failed attempt**, never an empty review.
6. **Containment and the leak audit:** `contain_to_workspace`, `setting_sources: []` (so the
   repo's CLAUDE.md and rules never load) and the transcript audit, on every Claude config.

Before any spend, check by hand that the model names the CLI accepts exist on the subscription
(`claude --model <full name>`). Record each model's training cutoff against the PR windows: dev
PRs were created 2025-12-18..31, the post-cutoff set 2026-07-08 onwards. Do not assume either.

## The runs

One condition throughout: **contract v2** (`user_prompt: v2`, `notes_form: per_object_family`,
`filing_bar: request`, brief G2, the five context tools, `file_search`). That is the prompt the
swap and both gpt v2 runs used. Under Claude Code the task's system prompt is delivered by
`4816cd2`.

| cell | harness | model | answers |
|---|---|---|---|
| H-gpt | Claude Code (relay) | gpt-5.5, then gpt_5.2 | the harness for gpt under the v2 prompt and reasoning carried. Against the ape_agent v2 runs (0.130 / 0.087 on dev). |
| H-claude | Claude Code (subscription) | `claude-opus-5-5` | the project harness against the probe harness for the same model and prompt. Against the swap (0.435 on dev). |
| M-5 | Claude Code (subscription) | Opus 5 | whether the model generation matters |
| M-4.8 | Claude Code (subscription) | Opus 4.8 | the same, one generation further back |

Each on the dev 15 PRs (judge, held-out 12) and the post-cutoff set (blind matchers, two per
seal, audited, against the existing post-cutoff reviewers).

## Reading rules (stated here, before any run)

On the dev held-out 12 gold (23 obligations; one is 0.043, inside the judge's noise):
- **H-claude**: within 3 obligations of the swap's 10 means the project harness and the probe
  harness are interchangeable for Claude. More than 3 below means the project harness costs
  Claude something, and the gpt comparison must then be read inside one harness.
- **H-gpt**: within 2 obligations of the ape_agent run of the same model means the harness is not
  gpt's limit under this prompt either.
- **M-5, M-4.8**: "replicates Opus 5.5" means ≥ 8 obligations (the swap's bar); ≤ 5 means it does
  not; 6-7 is partial. Read beside each: findings filed, targets, hits per finding, notes coverage
  (`focus.py`), compiles and lookups.

On the post-cutoff set, by matcher reach against X1/X2 and the gpt reviewers on the same seal:
the same three readings, as q = reach / X's. A model whose dev number holds and whose post-cutoff
q falls by more than half is read as in-window memory, not review.

One run per cell is provisional. A cell whose reading decides a design gets two more repetitions
before anything is built on it.

## Merge note

`claude-code-harness` and `post-carryover-replan` both change six files:
- `src/ape/scaffolds/prompts.py`;
- `src/ape/scaffolds/ape_agent/conversation.py`;
- `src/ape/toolkits/execute/lean/tools.py`;
- `src/mathlib_review/analysis/probes.py`;
- `tests/datasets/test_pr_review_v5_prompt_delivery.py`;
- `docs/todo/framework-defects-2026-09.md`.

The first two carry this branch's `batch_preamble` and `workspace_environment` switches and that
branch's system-prompt delivery for every scaffold. Resolve them by keeping both, then run the full
suite and `verify_frozen verify` before the merge commit.
