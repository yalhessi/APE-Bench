# The harness, with the model held: G under APE-Agent against G under Claude Code (2026-10-01)

Written before the seal and before any matcher runs.

## Question

Does the APE-Agent harness limit the reviewer, compared with Claude Code? The model is held fixed
(`gpt_5.2`, reasoning off, through each harness's relay to APE's client). So are the brief
(`brief_G.md`), the packet, APE's tools, the cutoff gate and the $1.50 session cap. Only the
scaffold differs. This is the paper's scaffold comparison, applied to the review task.

## Sessions

The six post-cutoff PRs with round-1 asks (41930, 42184, 42814, 43024, 43167, 43192), and their 16
agreed asks (`postcutoff-2026-09-29/asks.json`).

| label | source | harness |
|---|---|---|
| A1, A2, A3 | `probe_postcutoff_gpt52_G_lvfix_rep{1,2,3}` | `ape_agent` |
| C1, C2, C3 | `probe_postcutoff_gpt52_G_claude_lvfix_rep{1,2,3}` | `claude_code` (`configs/pr_review_v5_probe_2026_07_08_v1_gpt52_G_claude.yaml`) |
| X1, X2 | Claude's post-cutoff sessions (`postcutoff-2026-09-29/pr*/X*`) | Claude, the reference |

All six runs are at `c9c5d91`, after the relay fixes (`196d948`, `5037f57`, `04484fa`) and the
`lean_verify` path fix. All 18 Claude Code attempts audited clean and usable. Committed in `2e35347`.

## Matching

As in `gpt52-postcutoff-2026-09-29`: `cli probe match-inputs` gives each finding as target, claim,
requested change and severity, with condition cues redacted. Per PR the eight reviewer sets are
shuffled as `R1` to `R8` under `blinding_SEALED.json`. Two blind matchers (Claude subagents) use the
same rubric, generalised to eight reviewers. Both transcripts are audited before anything is
unblinded.

## Reading rule

On each matcher, a session's reach is the asks it `reached` over 16. A condition's reach is the
mean over its sessions. The primary reading is `d = reach(C) - reach(A)`:

| on both matchers | reading |
|---|---|
| `|d| <= 0.05` | comparable: on this set the APE-Agent harness is not what limits `gpt_5.2` |
| `d >= 0.10` | Claude Code reaches more with the same model |
| `d <= -0.10` | APE-Agent reaches more with the same model |
| otherwise, or the matchers disagree | inconclusive at this size |

Also reported: `q = reach / reach(X)` for A and C; each condition's stable and union asks; findings
per session; asks reached per finding.

## Stated limits

- One model, reasoning off, and 16 asks: one ask is 0.0625 of one session's reach, and the matcher
  self-agreement is about 90%. The thresholds are coarse on purpose.
- The harnesses differ in their own tools as well as their loop. Claude Code has Read, Grep and Glob
  beside APE's MCP tools; APE-Agent has APE's `file_read` and `content_search`. Under Claude Code,
  `lean_verify` still refuses 19 of 23 calls, because the reviewer passes bare `Mathlib/...` paths
  (the tool asks for `target/`). That belongs to the harness as it stands, and is not separated here.
- Earlier references on this set are not re-read here: G before the `lean_verify` fix reached 0.12
  a session, X 0.47 (test (b)).
