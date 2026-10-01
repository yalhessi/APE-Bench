# Claude models under the project's harness (2026-10-01)

The readings of `docs/plans/2026-10-01-claude-models-under-the-harness.md`. That plan states the
rules, before any run. Every cell runs contract v2, unchanged, under Claude Code. The
per-invocation prompts are identical to the ape_agent contract-v2 run's: 1605 of 1605 hashes
(`a075e26`). What varies is the harness (Claude Code's own system prompt and tools, APE's preamble
in the first user message) and then the model.

Route: Claude Code on the subscription (`claude-subscription`: `75d85bd`, `ea47258`), CLI 2.1.285,
effort xhigh. Caps are contract v2's (160 replies, 16.08M tokens a session).

**The swap ran at the same effort, on the same CLI, as the same model.** The probe harness wrote
no effort into its packets, but Claude Code 2.1.285 writes `effort` into every transcript entry.
The swap's 13 subagent transcripts (session `029323d7`, `~/.claude/projects/`) read `xhigh`,
`2.1.285` and `claude-opus-5-5` on every assistant entry. The one `<synthetic>` entry is the 33294
attempt the safety classifier stopped. H-claude's own transcripts read `xhigh` / `2.1.285`. So
H-claude against the swap varies the harness alone: the probe harness's subagent against the
project's Claude Code session, with its preamble, MCP tools and containment.

## H-claude, dev: 7 of 23, at the rule's boundary (one run, provisional)

`probe_dev_opus55_contract2_claude_sub_rep1`. 15 of 15 sessions ran, every audit was clean and
usable, and nothing was billed. Judged with `configs/pr_review_v5_medium_heldout_judge.yaml`
(judge v9, $0.21), audit `probe-dev-opus55-contract2-claude-sub-rep1`.

| reviewer (dev held-out 12) | issue recall | reachable (12) | findings | per PR | targets (of 432) | hits / finding | notes bullets per PR |
|---|---|---|---|---|---|---|---|
| Claude swap (probe harness) | 0.435 | - | 99 | 8.2 | 84 | 0.101 | 11.0 |
| **H-claude (project harness)** | **0.304** | 0.500 | 77 | 6.4 | 71 | 0.091 | 11.0 |
| gpt-5.5 contract v2 (ape_agent) | 0.130 | - | 30 | 2.5 | 29 | 0.100 | 10.5 |
| gpt_5.2 contract v2 (ape_agent) | 0.087 | 0.167 | 34 | 2.8 | 34 | 0.059 | 9.5 |

Columns from `results/pr_review_v5/probes/contract-2026-10-01/breadth.py`. Its run table carries
this run, so the table regenerates.

**By the rule:** within 3 of the swap's 10 means the project harness and the probe harness are
interchangeable for Claude. 7 is exactly 3 below, so this sits on the boundary, and the judge's
noise at 23 obligations is about one to two. The cell decides how the gpt comparison is read, so the
plan's rule asks for two more repetitions before anything is built on it.

**Beside it:** the difference is volume, not aim. The project harness filed 22% fewer findings
than the swap (77 against 99) on 15% fewer targets, at nearly the same hits per finding (0.091
against 0.101), and with the same notes length. It still filed 2.3-2.6 times what gpt filed under
the same prompt.

**What the M cells' rule needs.** The plan reads M-5 and M-4.8 as replicating Opus 5.5 at 8 or
more obligations, the swap's bar. Under this harness, Opus 5.5 itself reached 7, which that rule
calls "partial". So M-5 and M-4.8 are read twice: by the rule as written, and against
H-claude's repetitions under the same harness. The second is the like-for-like comparison. This
is said here before either M run.

Per session: 9-66 tool calls, 7-55 replies, up to 6.13M processed tokens (23.2M over the run).
Two sessions passed the gpt-era 1.8M cap, one of them three times over.

## M-5, dev: 8 of 23, the same as Opus 5.5 under this harness (one run, provisional)

`probe_dev_opus5_contract2_claude_sub_rep1`: H-claude with `claude_model: claude-opus-5` and
nothing else changed. 15 of 15 sessions ran, every audit was clean and usable, every init named
claude-opus-5, and nothing was billed. Judge v9, $0.18, audit
`probe-dev-opus5-contract2-claude-sub-rep1`.

| reviewer (dev held-out 12) | issue recall | reachable (12) | findings | targets | hits / finding | tool calls | edits compiled (+ snippets) | declaration lookups | notes name the PR's declarations |
|---|---|---|---|---|---|---|---|---|---|
| Claude swap (probe harness) | 0.435 | - | 99 | 84 | 0.101 | 35 | 6.0 (+0) | 2.0 | 82% |
| H-claude, Opus 5.5 | 0.304 | 0.500 | 77 | 71 | 0.091 | 29 | 3.5 (+0) | 2.5 | 92% |
| **M-5, Opus 5** | **0.348** | 0.417 | 73 | 72 | 0.110 | 34 | 7.0 (+2.5) | 5.0 | 92% |
| gpt-5.5 contract v2 (ape_agent) | 0.130 | - | 30 | 29 | 0.100 | 41 | 9.5 (+3.5) | 3.5 | 82% |

Tool calls, compiles and lookups are per-session medians from `focus.py`; the rest is from
`breadth.py`. Both scripts carry these runs. `focus.py` reads a subscription run's Claude Code
transcript, with Read, Grep and Glob counted as file_read, content_search and file_search. The
"notes bullets" column of `breadth.py` reads 0.0 for M-5 because Opus 5 wrote its notes (3-9K
characters a PR) as paragraphs and code-led lines rather than bullets. Declaration coverage is
the measure that does not depend on the format.

**By the rule as written** (8 or more obligations replicates Opus 5.5), Opus 5 replicates.
**Against H-claude under the same harness**, it reaches one more obligation, inside the judge's
noise. It files about the same (73 against 77 findings, 72 against 71 targets) and aims slightly
better (0.110 against 0.091 hits per finding). It also compiles and looks up about twice as
much, and its notes cover the PR's declarations as completely. One run each. H-claude's two
further repetitions come next in the queue.

## M-4.8, dev: 3 of 23, where gpt-5.5 is under the same prompt (one run, provisional)

`probe_dev_opus48_contract2_claude_sub_rep1`: H-claude with `claude_model: claude-opus-4-8`.
15 of 15 sessions ran, every audit was clean and usable, every init named claude-opus-4-8, and
nothing was billed. Judge v9, $0.09, audit `probe-dev-opus48-contract2-claude-sub-rep1`.

| reviewer (dev held-out 12) | issue recall | findings | targets | hits / finding | tool calls | edits compiled (+ snippets) | declaration lookups | notes name the PR's declarations |
|---|---|---|---|---|---|---|---|---|
| H-claude, Opus 5.5 | 0.304 (7) | 77 | 71 | 0.091 | 29 | 3.5 (+0) | 2.5 | 92% |
| M-5, Opus 5 | 0.348 (8) | 73 | 72 | 0.110 | 34 | 7.0 (+2.5) | 5.0 | 92% |
| **M-4.8, Opus 4.8** | **0.130 (3)** | 29 | 28 | 0.103 | 16 | 1.0 (+0) | 2.0 | 82% |
| gpt-5.5 contract v2 (ape_agent) | 0.130 (3) | 30 | 29 | 0.100 | 41 | 9.5 (+3.5) | 3.5 | 82% |

**By the rule** (5 or fewer does not replicate), Opus 4.8 does not replicate Opus 5.5. Against
H-claude under the same harness it is 4 obligations below.

**Beside it:** the gap is again volume, not aim. Opus 4.8 filed 29 held-out findings against
73-77 for the two Opus 5 models, at the same hits per finding (0.103). Its sessions were short:
16 tool calls and 1 compiled edit at the median, 3-26 replies, 9.9M tokens over the run against
23-24M. Its notes still name 82% of the PR's declarations, so it looked at the objects and filed
less about them. In volume and recall it sits where gpt-5.5 did under the same prompt, though
gpt-5.5 compiled and looked up far more on its way there.

**What this dev reading cannot separate.** Opus 4.8's training cutoff (Jan 2026) is at the edge of
the dev PRs' review window: they were created 2025-12-18..31, and their reviews and merges ran
later. Opus 5 (May 2026) and Opus 5.5 (Jun 2026) trained past all of it. So on dev, the
4.8-against-5.x gap could be memory of these PRs as well as the model generation. The
post-cutoff set, after all three cutoffs, is the test that separates them. That is the plan's
second half, still to run.

## Across the three models so far

Every reviewer here aims about equally well: hits per finding 0.09-0.11, Claude or gpt, harness
or probe. Recall follows how much the reviewer files. That repeats what the contract probes found
(`../contract-2026-10-01/README.md`): the variable that moves recall is how many changes the
reviewer decides to ask for. Opus 5 and 5.5 under the project harness file about 75 held-out
findings, Opus 4.8 and gpt about 30. One run per cell, with H-claude's repetitions still to come.

## H-claude rep 2, first attempt: cut short by the subscription limit, then reopened

`probe_dev_opus55_contract2_claude_sub_rep2` ran 13 of 15 sessions before the subscription's
five_hour limit was spent at 10:00. 33321 (held out) and 33066 failed mid-session on
`ClaudeSessionError`, as designed. They failed as attempts and did not read as short reviews.
A partial run cannot be resumed (see the ledger), and missing 33321 it cannot be judged beside
rep 1, so it is redone after the reset under the same name. One of its sessions (33149's task
`bb11a540`) audited `clean=False` on a call to `zulip_search`, a tool that does not exist (the
real one is `mcp__core__zulip_search`), which the CLI refused before anything ran. Re-audited
under `e5de5f0`, it is clean (17 calls, 1 nonexistent, 0 leaked).

**Reopened, not redone (2026-10-01 10:36).** `run --resume` (`9ceba2a`) requeued exactly the two
lost sessions, ran them on a second account's token (checked first as allowed), and kept the 13
successes. Both succeeded on attempt 5, and the run closed complete (`e9f88b2`). Two
subscriptions served it, with the same model, CLI and effort. All 15 sessions audit clean and
usable under `e5de5f0`.

## H-claude rep 2, dev: 7 of 23 again (judge v9, $0.20)

Audit `probe-dev-opus55-contract2-claude-sub-rep2`: issue recall 0.304, reachable 0.417.

| H-claude, Opus 5.5 | rep 1 | rep 2 | union | stable |
|---|---|---|---|---|
| obligations of 23 | 7 | 7 | 8 | 6 |

Against the swap's 10: 7 of the swap's obligations are in H-claude's union and 3 are not, and 1
of H-claude's is not the swap's. Two repetitions agree to the obligation count and on 6 of 7
obligations, so the gap to the swap is not a low draw: it is 3, the boundary of the rule. Rep 3
is running and closes the cell (mean / union / stable).

## Where this stands (2026-10-01, handed to a planning session)

| cell (dev, contract v2, Claude Code) | runs | obligations of 23 | held-out findings | hits / finding |
|---|---|---|---|---|
| H-claude, Opus 5.5 | rep 1, rep 2 (rep 3 partial) | 7, 7 (union 8, stable 6) | 77, - | 0.091 |
| M-5, Opus 5 | rep 1 | 8 | 73 | 0.110 |
| M-4.8, Opus 4.8 | rep 1 | 3 | 29 | 0.103 |
| (swap, probe harness, Opus 5.5) | - | 10 | 99 | 0.101 |
| (gpt-5.5, ape_agent, same prompt) | - | 3 | 30 | 0.100 |

- **H-claude rep 3** (`probe_dev_opus55_contract2_claude_sub_rep3`) is partial and uncommitted. It
  ran 8 of 15 sessions (7 of the held-out 12). 33066, 33098, 33145, 33149, 33285, 33321 and 33337
  failed when a third subscription's limit was spent. `run --resume` on a token with headroom
  requeues exactly those. Reps 1 and 2 spent 12-16M tokens on these seven PRs. Its orchestrator
  state is in `.ape/runs/` (shared), and its results directory is untracked in the
  `claude-subscription` worktree.
- **Not run:** the H-gpt cells (`configs/pr_review_v5_dev_medium_gpt5{2,5}_Grc_contract2_claude.yaml`,
  paid, held by the user) and the whole post-cutoff half. The post-cutoff half is the one test of
  whether Opus 4.8's gap is generation or memory, and of whether the Opus 5 models' dev reach is
  review.
- **Quota:** each five_hour window held about one dev run (20-24M processed tokens, mostly cache
  reads). Check a token before a run (a one-line `claude -p` with `HOME` elsewhere reports the
  `rate_limit_event`), and stop at the first `allowed_warning` if the account is also in
  interactive use.
- **One run per cell except H-claude.** CLAUDE.md asks for three repetitions before a reading
  stands. M-5 and M-4.8 have one each.
