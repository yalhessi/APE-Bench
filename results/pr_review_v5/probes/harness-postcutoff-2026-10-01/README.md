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

## Result (matched 2026-10-01)

Two blind matchers on the seal `60be343`. Both transcripts were audited clean (11 calls each, none
flagged). They agree on 126 of 128 cells, and on 127 of 128 when reading only reached or not.

| reach over 16 asks | A1 | A2 | A3 | **A** | C1 | C2 | C3 | **C** | X1 | X2 | **X** | **d = C - A** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| matcher 1 | .1875 | .1875 | .125 | **.167** | .0625 | .125 | .1875 | **.125** | .50 | .4375 | **.469** | **-0.042** |
| matcher 2 | .1875 | .1875 | .0625 | **.146** | .0625 | .125 | .1875 | **.125** | .50 | .4375 | **.469** | **-0.021** |

**By the rule: comparable.** `|d| <= 0.05` on both matchers. On this set, with `gpt_5.2` and
reasoning off, the APE-Agent harness is not what limits the reviewer compared with Claude Code.
`q = reach / X`: A 0.31-0.36, C 0.27.

- **Which asks.** Each condition's union is 3 asks, two of them shared: removing the unused import
  on 43167 (every session) and the missing "of" in 43192's title. A's third is the
  `commutator_sup_left_of_normal` rename on 43167, reached by all three A sessions; C's is the
  `_anti` rename on 43024, by C3 only. Neither reaches any of the six asks X reaches beyond those:
  dropping `[L.NeBot]`, `@[to_additive]`, the two `cat_disch` defaults, and `homMk`.
- **Per finding.** Asks reached per finding (matcher 1): A 0.138, C 0.130, X 0.31. Findings per
  session: A 19.3, C 15.3, X 24.5.
- **Spread.** C's sessions range from 1 to 3 asks, and its findings per run from 9 to 22; A's from
  1 to 3, and 18 to 20.
- **Cost.** Billed for three repetitions: A $0.82, C $1.22.

**Read at this altitude.** One model with reasoning off, and 16 asks, so one ask moves a condition
mean by about 0.02. The comparability holds for this harness pair as configured, including Claude
Code's own tools and its bare-path `lean_verify` refusals. Not tried: reasoning on (where `gpt_5.2`
reached 0.31-0.44 under APE-Agent), Claude as the model in both harnesses (it needs an Anthropic
provider), Codex, and the validation and dev sets. The gap to X stays the model's, as tests (b) and
(e) found.

## Second comparison: reasoning on, carried (pre-registered 2026-10-01, before its matchers)

The same question, with the model at its strongest setting on this set: `gpt_5.2` at high effort
through the Responses API, with each turn's encrypted reasoning carried to the next (Grc). Under
APE-Agent that reached 0.44 a session in test (e) amended, one run, before the `lean_verify` fix.
Through Claude Code nothing was carried until `e064ae0`: the relay rebuilt each request without
the turn's reasoning state. A one-PR check after the fix (`pr5_probe0708_gpt52_Grc_claude_smoke1`,
43024, 17 requests): every request carried every earlier turn's reasoning.

| label | source | harness |
|---|---|---|
| A1, A2, A3 | `probe_postcutoff_gpt52_Grc_lvfix_rep{1,2,3}` | `ape_agent`, `configs/pr_review_v5_probe_2026_07_08_v1_gpt52_Grc.yaml` |
| C1, C2, C3 | `probe_postcutoff_gpt52_Grc_claude_rep{1,2,3}` | `claude_code`, `configs/pr_review_v5_probe_2026_07_08_v1_gpt52_Grc_claude.yaml` |
| X1, X2 | Claude's post-cutoff sessions | the reference |

Seal `blinding_carried_SEALED.json`, sources `sources_carried.json`, matcher outputs in
`match_carried/`. Matching and the reading rule are as above: `d = reach(C) - reach(A)` on both
matchers, with `|d| <= 0.05` comparable, `d >= 0.10` Claude Code more, `d <= -0.10` APE-Agent
more, and anything else inconclusive. A session that stopped at its cap without submitting is
matched as an empty review, marked, and counted.
