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

### Result, reasoning carried (matched 2026-10-01)

Two blind matchers on the seal `b7a7ca4`, both audited clean (7 calls each, none flagged), agreeing
on all 128 cells.

| reach over 16 asks | A1 | A2 | A3 | **A** | C1 | C2 | C3 | **C** | X | **d = C - A** |
|---|---|---|---|---|---|---|---|---|---|---|
| both matchers | .3125 | .125 | .1875 | **.208** | .25 | .25 | .25 | **.250** | **.469** | **+0.042** |

**By the rule: comparable** (`|d| <= 0.05`). With reasoning carried, too, the APE-Agent harness is
not what limits `gpt_5.2` against Claude Code. `q`: A 0.44, C 0.53.

- **Which asks.** C's three sessions each reach the same 4 asks: the unused import, the title's
  "of", dropping `[L.NeBot]`, and `@[to_additive]`. A's union is 5 asks, those 4 plus the
  `cat_disch` default on `mk` (A1 only), but only the import and the title are stable across A's
  sessions. Neither condition reaches `homMk`, the `mkHom` default, or the `_anti` rename.
- **Against reasoning off** (this folder's first comparison), carried reasoning raises reach for
  both harnesses: A 0.146-0.167 to 0.208, C 0.125 to 0.250. Findings fall from 15-19 a session to
  6-8, and asks per finding rise from 0.13-0.14 to 0.52-0.56. Read across two seals and two matcher
  pairs, not pre-registered.
- **Cost.** Billed for three repetitions: A $7.81, C $10.19.

**Grc's earlier 0.44 does not replicate here.** Test (e) amended matched one Grc run (before the
`lean_verify` fix) at 0.4375, q 0.93, and read it as closing the gap. Three runs of the same
configuration, with the fix, reach 0.31, 0.125 and 0.19, mean 0.21, q 0.44. Both sets of matchers
put X at 0.469, so the shift is in the A sessions, not the matching. A one-run reading moved by
regression toward the mean is the plainest account. The fix is the one difference in setup, and
its effect is not separated here. The record's "carry-over closes the gap" should be read as
"carry-over raises reach to about half of Claude's" until more runs settle it.

## Test (e) reinvestigated: did anything change between the 0.44 run and its repetitions? (2026-10-01)

Asked because no carried run since test (e) has repeated its reach. Checked from the request logs
(`data/llm_logs`, every payload APE sent), not from configs. `carry_check.py` repeats the scan.

The six APE-Agent runs of the same configuration (Grc: gpt_5.2 high, Responses, reasoning carried)
on these six PRs:

| run | when | `declaration_search` fix | `lean_verify` fix | reach |
|---|---|---|---|---|
| Grc1 = test (e)'s Grc (`probe_postcutoff_gpt52_Grc_rep1`) | 30 Sep 08:03 | no | no | 0.4375 |
| Grc2, Grc3 (Phase 0, `post-carryover-replan`) | 30 Sep 09:05 | yes (`5e215ff`) | no | 0.375, 0.1875 |
| A1-A3 (this folder) | 1 Oct 06:25 | no | yes | 0.3125, 0.125, 0.1875 |

- **What the model was sent is unchanged.** The first request of every session is byte-identical
  across the three groups, PR by PR: system instructions, every tool's name, description and
  schema, the task prompt, and the settings (`reasoning.effort: high`,
  `include: [reasoning.encrypted_content]`, `store: false`). The model is `gpt-5.2-2025-12-11`
  throughout, and every response completed.
- **Carry-over worked in every group.** Every later request carried encrypted reasoning: Grc1 77 of
  77, Grc2-3 213 of 213, A 313 of 313. They covered 98-99% of earlier turns (the rest had none to
  carry), and each turn's input grew by at least the previous turn's reasoning in every consecutive
  pair (75, 209, 301). Through Claude Code, after `e064ae0`, 373 of 373 did.
- **The tools behaved the same, apart from the two fixes.** For identical calls (same tool and
  arguments) in two groups, outputs match, except `declaration_search` between Grc1 and Grc2-3
  (16 of 16, the fix) and `lean_verify` between Grc1 and A (8 of 8: refused before, compiled now).
  `file_read`, `content_search`, `naming_norm`, `code_hover` and `zulip_search` agree in every pair,
  so the shared indexes did not move.
- **So nothing subtle broke.** The 0.4375 is the top of the distribution: six runs, mean 0.27,
  SD 0.12. Grc2 and Grc3 ran the same code side by side and differ by three asks. Grc1's sessions
  were shorter (13.8 turns against 18.4-18.8) and reasoned more a turn on average (1,409 tokens
  against 941-1,001, medians 599 against 468-514). That is one run of six sessions.
- **What carry-over does, read across these runs:** about 0.27, against 0.31 for the one Chat-high
  run (Gr1) and 0.13-0.17 with reasoning off. It is not distinguishable from high effort without
  carry-over, as Phase 0 concluded (`14200808`). Its process gains (sessions conclude, fewer repeated
  calls) are Phase 0's and are not re-measured here.
- **Still open.** `develop` and this branch lack the `declaration_search` fix (`eec8d3a`, ported as
  `5e215ff` only to `post-carryover-replan`), so every run here, both harnesses, used the defective
  tool. With n = 2-3 per group, whether either fix moves reach is not separable from the spread.

## Third harness: Codex (pre-registered 2026-10-01, before its runs)

The same question for Codex (`codex-cli` 0.144.5). The scaffold drives `codex exec` through a
Responses relay to APE's client (`61b3e08`, `cbffcb5`). Codex is told the model is `gpt-5.2`, so it
uses its own prompt for that model, with the MCP tools listed up front. It has no shell
(`shell_tool`, `unified_exec` off), a read-only sandbox, no web search, and of its own tools only
`update_plan`. So its tools are APE's: the same 6 toolkit tools as APE-Agent plus the task's own
(checked on `pr5_probe0708_gpt52_G_codex_smoke2`). Configs:
`configs/pr_review_v5_probe_2026_07_08_v1_gpt52_{G,Grc}_codex.yaml`, held equal to their APE-Agent
conditions.

| label | source |
|---|---|
| Cx1-Cx3 | `probe_postcutoff_gpt52_G_codex_rep{1,2,3}` (reasoning off) / `probe_postcutoff_gpt52_Grc_codex_rep{1,2,3}` (carried) |
| A1-A3, C1-C3, X1, X2 | as in the two comparisons above, the same runs |

**Matched three ways**, so every harness is read within one matcher pair. Seals
`blinding_codex_off_SEALED.json` (with the reasoning-off A and C) and
`blinding_codex_carried_SEALED.json` (with the carried A and C), eleven reviewers a PR, and
matchers in `match_codex_off/` and `match_codex_carried/`. Per PR the eleven sets are shuffled as
`R1` to `R11`.

**Reading rule**, on both matchers and for each seal, `d = reach(Cx) - reach(A)`: `|d| <= 0.05`
comparable, `d >= 0.10` Codex reaches more, `d <= -0.10` APE-Agent reaches more, otherwise
inconclusive. `reach(C) - reach(A)` is read again in the same matchings, as a replication of the
two comparisons above. A different reading there is reported, not reconciled.

### Result, three harnesses (matched 2026-10-01)

Four blind matchers, two per seal (`40a9274`), eleven reviewers a PR. Audits: 13, 11, 9 and 8 calls.
The three flags are a matcher running its own `tmp/build.py` with the repository's interpreter,
the benign pattern adjudicated before. Agreement: 174 of 176 cells with reasoning off, 176 of 176
carried.

| reach over 16 asks | A (APE-Agent) | C (Claude Code) | Cx (Codex) | X (Claude) | **Cx - A** | C - A |
|---|---|---|---|---|---|---|
| reasoning off, matcher 1 | 0.167 | 0.125 | 0.021 | 0.469 | **-0.146** | -0.042 |
| reasoning off, matcher 2 | 0.146 | 0.125 | 0.021 | 0.469 | **-0.125** | -0.021 |
| carried, both matchers | 0.208 | 0.250 | 0.292 | 0.469 | **+0.083** | +0.042 |

**By the rule.** Reasoning off: `Cx - A <= -0.10` on both matchers, so **APE-Agent reaches more than
Codex**. Codex's sessions reach 0, 1 and 0 asks (0.03 per finding, against A's 0.14). Carried:
`Cx - A = +0.083` on both, between the thresholds: **inconclusive**. Codex is highest in mean
(0.29), in union (7 asks, against A 5 and C 4) and per finding (0.74, against 0.52-0.56), with 3
stable asks. `C - A` repeats the two comparisons above exactly (-0.042 / -0.021 off, +0.042
carried), so the matchings agree with each other.

- **Codex at reasoning off made no comparison lookup at all**: 0.0 a session, against APE-Agent's
  3.4 and Claude Code's 0.6. It used only `content_search` (148) and `file_read` (85). Carried, it
  made 7.7, the most of the three, with 2.8 `lean_verify_edit` a session.
- **A possible cause, not tested:** Codex is told the model is `gpt-5.2`, so it sends its own prompt
  for a reasoning model run at medium effort. With reasoning off, the relay runs the model without
  reasoning under that prompt. The other two harnesses' prompts assume no reasoning setting.
- **Cost**, three repetitions: reasoning off A $0.84, C $1.22, Cx $1.06; carried A $7.81, C
  $10.19, Cx $9.40.

**Read at this altitude.** One model, 16 asks, three runs a condition. Codex's reasoning-off reading
holds by the rule. It is a statement about this configuration, not about Codex with reasoning,
where it is the strongest of the three without clearing the threshold.

## Codex with gpt-5.4 and gpt-5.5, reasoning carried (pre-registered 2026-10-01, while the runs go)

One run each, by the user's choice. Codex is told each model's own name (both are in its catalog).

| label | source | harness |
|---|---|---|
| Ka1 | `probe_postcutoff_gpt54_Grc_codex_rep1` | Codex, gpt-5.4 |
| Kb1 | `probe_postcutoff_gpt55_Grc_codex_rep1` | Codex, gpt-5.5 |
| Ha1 | `probe_postcutoff_gpt54_Grc_rep1` (test (e)'s Hac) | APE-Agent, gpt-5.4 |
| Hb1 | `probe_postcutoff_gpt55_Grc_rep1` (test (e)'s Hbc) | APE-Agent, gpt-5.5 |
| X1, X2 | Claude's sessions | the reference |

Seal `blinding_codex_gpt545_SEALED.json`, sources `sources_codex_gpt545.json`, matchers in
`match_codex_gpt545/`. Six reviewers a PR.

**Reading rule.** One run a cell, and gpt_5.2's carried runs spread at SD 0.12 a run, so a single
difference `Ka1 - Ha1` or `Kb1 - Hb1` under 0.25 (four asks) is no evidence of a harness
difference. 0.25 or more is suggestive, to be replicated before it is read. The APE-Agent runs
predate the `lean_verify` fix, so that difference is in the comparison too.
