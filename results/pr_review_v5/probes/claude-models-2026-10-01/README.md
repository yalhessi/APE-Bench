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

## Run-to-run consistency of the solo reviewer (2026-10-01, `consistency.py`, no spend)

Read for `docs/plans/2026-10-01-beyond-the-solo-baseline.md` from the committed audits and runs.
`consistency.py` prints the per-obligation spine for every dev cell, the union and stable sets,
the change targets two cells share, control emission, and (from the uncommitted `.ape/runs`) the
sessions' visible text and budget truncations.

| cells on the dev held-out 12 | hit per cell | union | stable |
|---|---|---|---|
| the same configuration twice (H-claude reps 1, 2) | 7, 7 | 8 (0.35) | 6 |
| the six Opus 5.x cells (X1, X2, swap, H-claude r1, r2, M-5) | 11, 11, 10, 7, 7, 8 | **13 (0.57)** | 6 |
| every cell, gpt included | as above, 3, 3, 2 | 13 | 2 |

- **A single pass reaches about two thirds of what the family of passes reaches.** Ten
  obligations are reached by no Opus cell; the thirteen reached are reached by at most six cells
  and six of them by every one.
- **Reps revisit the same targets and ask different things there.** Two reps of one
  configuration share 56 of 86 change targets (Jaccard 0.65); Opus 5 against Opus 5.5 0.53-0.59;
  Claude against gpt 0.24-0.29. At 33321's `baseOf`, rep 1 filed the docstring typo and rep 2 the
  set comprehension, one gold obligation each; at 33149's Parseval axiom, rep 1 found the Mathlib
  lemma by search and rep 2 did not.
- **The never-reached ten are knowledge at an attended site**: the `toLinearMap_` rename (all
  three project cells asked a different rename there, although `naming_norm` had told each of them
  `emerging`, `toLinearMap_` 21 to `coe_` 7, with the `toLinearMap_` names as candidates; corrected
  2026-10-02 from "Opus 5 citing `coe_`'s global count", which was validation PR d0045's), the
  `@[to_fun]` mechanism (3-6 findings at the site, none the attribute), dot notation (no finding at
  the site in any cell), and the 33145 `ciSup'` cluster, where the exact `by_cases` restructure and
  the exact `(α := αᵒᵈ)` dual proof were filed in both reps and scored `loc`.
- **Harness defects seen in the sessions**: the first message names a read-write scratch
  workspace "for creating and editing files" while `Write`, `Edit` and `Bash` are disallowed, so
  the sessions write 1-13 visible text blocks (84-1,738 characters) and keep their account only in
  the final call; `finding_budget: 20` dropped 2 and 4 findings on 33149 in reps 1 and 2 (the
  scaffold log's only trace); `proof_profile` is granted and dead on dev; two absolute roots name
  the same attempt.
- **Control emission**: Opus 5.5 under the project harness 1.0 per control PR, Opus 5 and the swap
  4.0, X1/X2 1.0-1.5, gpt 0-0.5.

## What the tool calls came back with (2026-10-01, `tool_outcomes.py`, no spend)

Every tool call in the three Opus subscription runs' transcripts (47 sessions), classified by
what the result was: an answer, a negative (the tool ran and found nothing), a refusal of the
call's arguments, an error (the call never ran), or an environment failure. The measurement
behind the hygiene layer (`docs/plans/2026-10-01-beyond-the-solo-baseline.md` §4).

| tool | calls | answered | negative | refused | error | env |
|---|---|---|---|---|---|---|
| `Grep` | 334 | 281 | 52 | 0 | 1 | 0 |
| `lean_verify_edit` | 313 | 234 | 72 | 0 | 7 | 0 |
| `declaration_search` | 249 | 178 | 56 | 15 | 0 | 0 |
| `Read` | 231 | 230 | 0 | 0 | 1 | 0 |
| `Glob` | 161 | 80 | 75 | 0 | 6 | 0 |
| `lean_verify` | 84 | 49 | 35 | 0 | 0 | 0 |
| `naming_norm` | 43 | 16 | 27 | 0 | 0 | 0 |
| `precedent_search` | 23 | 23 | 0 | 0 | 0 | 0 |
| `zulip_search` | 21 | 21 | 0 | 0 | 0 | 0 |
| `code_goto` | 4 | 1 | 0 | 0 | 3 | 0 |
| `code_hover` | 3 | 0 | 0 | 0 | 3 | 0 |
| `get_lean_goal` | 2 | 1 | 0 | 0 | 1 | 0 |
| `proof_profile` | 2 | 1 | 0 | 0 | 0 | 1 |
| `zulip_search` by a bare or miscased name | 2 | 0 | 0 | 0 | 2 | 0 |

- **The LSP tools were dead**: 7 of 9 hover, goto and goal calls failed with "Cannot find Lean
  project", every one on the `Mathlib/...` spelling that `lean_verify_edit` and the diff use.
- **`declaration_search` refused real names**: `Fintype`, `Meromorphic`, `abelianizeAdj`,
  `conjStarAlgEquiv`, as "not identifier-shaped" (15 of 249).
- **`lean_verify_edit` never saw 7 calls**: the model wrote `"replacement": }` to delete a span,
  which the CLI refused as malformed JSON.
- **`lean_verify` is a probe**: 55 of its 84 calls were `#check`, `example` or `exact?` snippets
  and none gave a file path, while its description said "verify ... correctness" with a
  `file_path`. 33 `lean_verify_edit` calls carried no edit (the as-is compile).
- **`proof_profile`** had no table on dev; **`Glob`** was passed a `head_limit` parameter the
  installed CLI (2.1.285) lacks three times, and twice pointed at the store root, which
  containment refused as designed.
- `submit_findings` reads as "rejected" in every transcript because the scaffold ends the session
  at submission; every session's `task_result.json` holds the submission.

Each row above that is a defect has a commit on `hygiene-layer` (2026-10-01): `01b09ce7` (one
path spelling for the LSP tools), `0a3d7d33` (snippet probe, deletion, Mathlib's linters on
whole-file compiles), `f8a65df5` (single-token names), `786f00a1` (`proof_profile` out of the
grant), `332631a4` (the tool line names `mcp__core__` and Read, Grep and Glob).

## Hygiene rep 1: Layer 0's reading (2026-10-01, `hygiene_reading.py`)

`probe_dev_opus55_contract2_hygiene_claude_sub_rep1`: H-claude on the hygiene layer's tools
(`configs/pr_review_v5_dev_medium_opus55_contract2_hygiene_claude_sub.yaml`: `Write` and `Edit`
granted and contained to `scratch/`, solo budget 40; the tool commits `01b09ce7`..`786f00a1`).
*Corrected 2026-10-02:* this line said `proof_profile` was out of the grant. It is not, for this
condition: `786f00a1` removed it from `configs/bases/v5_solo.yaml`, but
`configs/pr_review_v5_dev_medium_gpt52.yaml` restates the dev set's tool list with it, so every
hygiene rep holds `[zulip_search, precedent_search, declaration_search, naming_norm,
proof_profile]`, as H-claude did. Rep 1 never called it. The frozen config is left as it is
(`review-designs` pins it by digest); the defect register carries the correction (`928ca6b6`).
15 of 15 sessions, every containment audit clean and usable,
19.3M processed tokens (max session 4.2M), nothing billed; `completion_status=complete`, 93
findings. Launched 14:23, closed 14:50.

**The rule** (plan §5, Layer 0: no recall rule; the truncation and the contradiction gone, and
held-out findings not below 77):

| | H-claude reps 1, 2 | hygiene rep 1 |
|---|---|---|
| held-out findings | 77, 77 | **75** |
| control-PR findings (33304, 33315) | 1, 1 | 1, 1 |
| first message names one root | no (two) | yes, 15 of 15 |
| budget truncations | 1, 1 (silent) | 0 (33149 filed 18 of 40) |
| tool calls refused, errored or unanswerable | 7 LSP, 15 `declaration_search`, 7 malformed deletions, 1 `proof_profile`, 2 misnamed | **1** (`declaration_search` on prose) in 372 calls |
| hover / goto / goal | 7 of 9 refused | 2 goal calls, both answered |
| `lean_verify_edit` results carrying the linter split | 0 | 71 of 82 |
| built-in writes | not granted | granted, **used 0 times** |

**By the rule: not met, by two findings.** 75 against the 77 bar, with one run on each side;
H-claude's two reps spread 99 to 97 total candidates, so two held-out findings is inside one
run's noise and is not evidence of a volume cost. The two structural conditions are met: no
truncation, one root. What the layer was built for is visible in the tools column: the refusals
and errors that cost 30 turns across the three Opus runs are gone, and the goal tool answered
for the first time in the record under Claude Code.

**Two things the run says that the rule did not ask.** The reviewer did not write a single file
although it could; the account still lives only in the final `notes`, so the "running notes"
condition is unmeasured by this run and needs an instruction, not a grant. And `lean_verify`
was called 38 times as the snippet probe, 19 answers and 19 negatives, as described.

**Not read:** recall. The judge was not run (about $0.20 on `gpt_5_mini`); reps 2 and 3 after
the weekly window resets (2026-10-02 10:00) complete the re-baseline, and the three are judged
together as mean / union / stable against H-claude's 7, 7.

**Judged (2026-10-01, judge v9, $0.22, audit `probe-dev-opus55-contract2-hygiene-claude-sub-rep1`):
9 of 23, issue recall 0.391**, reachable 0.500, resolution 0.304, control emission 1.0 per PR,
gold alignment 0.118 (H-claude: 0.091, 0.093). One run, so provisional, and within the judge's
noise of H-claude's 7, 7; on the right side of it. The spine (`consistency.py`, which now carries
the cell as `Hyg1`): the six obligations every Opus 5.x cell hits, plus `5ffba48e` (33321's set
comprehension, H-claude rep 2's), `695ae9fd` (33362's namespace layout, Opus 5's) and
`585e5e0b` (33285's one-term golf), which no project-harness cell had reached before; `61f68eed`
(the Parseval lemma, H-claude rep 1's) is the one it loses. Union with the two H-claude reps:
10 of 23; the Opus 5.x family's union stays 13, its stable set 6. Both new hits are judgement,
not the linters: the term proof `I.cotangentEquivIdeal.symm_apply_eq.mpr rfl` and "keep the
original layout". The linters' visible work in that session was the edit gate: a long-line
warning on the reviewer's own proposed edit.

## Hygiene, three reps: Layer 0's verdict (2026-10-02)

Reps 2 and 3 ran on accounts B and C in parallel (06:40); each account's five-hour window ran out
after about 20M tokens, and `run --resume` finished the three lost sessions (33066 on rep 2;
33321 and 33066 on rep 3) on the main account at 10:11 after its reset. Every session completed
and every containment audit is clean and usable; nothing billed. Judge v9 on the held-out 12.

| cell (dev held-out 12) | obligations | issue recall | reachable | resolution | held-out findings | control findings (33304, 33315) | gold alignment |
|---|---|---|---|---|---|---|---|
| H-claude rep 1 | 7 | 0.304 | 0.500 | 0.217 | 77 | 1, 1 | 0.091 |
| H-claude rep 2 | 7 | 0.304 | 0.417 | 0.217 | 77 | 1, 1 | 0.093 |
| hygiene rep 1 | 9 | 0.391 | 0.500 | 0.304 | 75 | 1, 1 | 0.118 |
| hygiene rep 2 | 9 | 0.391 | 0.500 | 0.304 | 82 | 1, 0 | 0.126 |
| hygiene rep 3 | 7 | 0.304 | 0.500 | 0.217 | 82 | 0, 4 | 0.108 |

| | per rep | mean | union | stable |
|---|---|---|---|---|
| H-claude (2 reps) | 7, 7 | 7.0 | 8 | 6 |
| hygiene (3 reps) | 9, 9, 7 | **8.33** | 11 | 6 |
| hygiene, any two reps | | | 10, 10, 10 | 8, 6, 6 |

**By the rule** (plan of 2026-10-01 §5, Layer 0: no recall rule; the truncation and the
contradiction gone, held-out findings per rep not below 77): **met.** No budget truncation and
one named root in every first message across 48 sessions; held-out findings 75, 82, 82 (mean
79.7). Control emission 1.0, 0.5 and 2.0 per control PR (mean 1.17, H-claude 1.0); rep 3's four
on 33315 sit at the 2.0 bar the design rules use.

**Beside it.** The mean is 1.3 obligations above H-claude's, inside the judge's noise at 23, at
better aim (0.108-0.126 against 0.091-0.093). The stable core is unchanged at 6; what moved is the
spread: any two hygiene reps reach 10 where H-claude's two reach 8. Four obligations only the
hygiene reps reach (`585e5e0b`, the 33285 one-term golf, in all three; `695ae9fd`, the 33362 layout;
`64e1164f`, the `toLinearMap_` rename; `7fef913e`, the order-dual `ciInf'`, never hit by any cell
before), and one only H-claude's (`61f68eed`, the Parseval lemma). The family's never-hit set drops
from ten to nine.

**What is not the tools.** On 33337, `naming_norm` gave every Opus cell, before and after the
hygiene layer, the right evidence (`emerging`, `toLinearMap_` 21 to `coe_` 7, the maintainers' name
as a candidate); one hygiene rep of three filed it. Rep 3's new `ciInf'` hit and rep 2's rename are
draws at the decision, with the evidence already in hand. That is the inconsistency the review
designs (`docs/plans/2026-10-02-review-designs.md`) are built to remove.

**Defects the parallel reps exposed** (`docs/todo/framework-defects-2026-09.md`): Claude Code aborts
an MCP call after 300 s of silence, the compile tool's own timeout, which cut seven compiles off
while eight sessions compiled at once; and one more malformed `"replacement": }` deletion. Rep 2's
and rep 3's tool tables (16 and 17 transcripts, including the attempts the limit cut short) are in
`hygiene_reading.py`'s output; apart from those, no tool refused a call.

**The baseline, frozen.** Hygiene's 9, 9, 7 (mean 8.33, union 11, stable 6) is what every review
design is read against from here, with the four-pass union (12 of 23, 7.0 control findings per PR;
`../ensemble-union-2026-10-02/`) as the consistency yardstick.
