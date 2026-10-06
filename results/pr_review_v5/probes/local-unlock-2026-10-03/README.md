# What unlocks the local model? A one-variable screen (pre-registered 2026-10-03, before its runs)

The user's question (2026-10-03): the self-hosted Qwen3.5-397B reads at the floor
(`../local-quality-2026-10-02/`: 2, 0, 2 of 23 with reasoning off, 0 with it high). What would move it
toward the Claude reviewers? Is it the prompt, Mathlib's conventions in the prompt, an instruction to
over-file, or the system prompt itself?

## What the record already says, and what the transcripts show

- **The prompt is not gpt's limit.** Claude given gpt's contract-v2 messages verbatim reached 10 of
  23, and gpt-5.5 under the same text 3 (`../contract-2026-10-01/`). That says nothing yet about a
  weaker model.
- **Conventions in the prompt were null on gpt.** The "statute" injection of distilled Mathlib
  guides: N=115, two models (`docs/dead-ends.md`). That entry reopens only for a *directive*
  injection with three reps, which is what condition C is.
- **Forced filing raised recall on gpt arms.** 49 -> 179 candidates and 2 -> 5 obligations. The cost
  was control emission, 1 -> 36 (`docs/dead-ends.md`, the volume-filter entry). Every reviewer hits
  0.06-0.12 obligations per finding, so recall follows volume.
- **No system prompt** is untried. The Claude Code and Codex harnesses already deliver this
  preamble in the first user message; only `ape_agent` uses the system role.
- **Where the local sessions lose**, from their transcripts:
  - They investigate as much as gpt does: ~9-10 file reads, 2-9 compiles a session.
  - But they submit **no findings on 4-7 of the 12 held-out PRs a rep**, against 1-3 for gpt (two of
    the twelve are controls).
  - The empty sessions decline after checking. On 33337 the model ran `naming_norm`, saw
    `toLinearMap_` lead 21-7, and wrote "no strong convention signal ... Nothing to ask"; that is the
    rename the maintainers asked for. On 33305: "This is a clean documentation fix PR ... There are
    no issues."
  - It reviews for correctness, and the brief's "There is no quota ... submit none when no request
    is warranted" licenses the empty review.

## The conditions: one variable each, against the base

Base: `configs/pr_review_v5_dev_medium_local397_contract2.yaml`, contract v2 under `ape_agent`,
reasoning off, temperature 1.0. Its three reps are on disk: 2, 0, 2. Each condition is one `--set`:

| label | change | `--set` |
|---|---|---|
| U | no system role: the identical system text opens the first user message | `system_prompt_role=user` (new, `ApeAgentConfig`) |
| O | over-file: G2's "no quota ... submit none" paragraph replaced by a recall instruction (`brief_G2_overfile.md`, diff in the commit) | `task_config.system_prompt_file=<dir>/brief_G2_overfile.md` |
| C | conventions as directive: G2 plus "check every changed declaration against each rule; each violation is a finding", then the naming, documentation, style and PR-review summaries from `docs/guides/` (`brief_G2_conventions.md`) | `task_config.system_prompt_file=<dir>/brief_G2_conventions.md` |
| T | Qwen's own sampling: temperature 0.6, the model's `generation_config.json` value (top_p 0.95 and top_k 20 already come from it) | `llm_config.temperature=0.6` |

Runs are named `iter_local397_unlock_<label>_rep<n>`. They are judged with
`configs/pr_review_v5_medium_heldout_judge.yaml` (judge v9, 23 obligations) and scored with
`cli report score` and `cli report conditions`.

## Reading rules (stated before any run)

- **Screen.** One rep per condition. A condition **advances** if its rep reaches **≥ 4 of 23**: two
  above the base's best rep, beyond one judge flip. Advanced conditions get two more reps.
- **A lever:** over three reps, mean ≥ 3.33 (two above the base's 1.33) and union > 2.
- **Unlocks the tier:** mean ≥ 5, the level gate's bar (`../local-quality-2026-10-02/`).
- **Control emission.** Opus 5.5 is 1.0 per control PR, gpt and the base 0. A condition above
  **3 per control PR** is read as volume without discrimination, whatever its recall.
- **Combination.** Levers that pass are then combined in one condition, three reps.
- **Read beside each:** findings per PR, zero-finding held-out PRs, change targets with a finding,
  judged pairs, hits per finding, turns and compiles per session.

Caveats carried into any reading: one model; the dev PRs may sit inside its training window, as they
do for every reviewer on this scale; and a single rep at this level is noisy (base reps were 2, 0, 2).

## Addendum (2026-10-03, before their runs): ten more settings, one hypothesis each

The user asked for ten meaningfully different settings to narrow down how to steer the model.
One question is already answered on disk: **resampling alone does not widen reach.** The base's
three reps reach 2 obligations in union, so K passes at the base setting are not a lever.

Each setting below tests a different explanation of why the model sits at the floor. Every brief
is G2 with one delimited section added or replaced, in this directory, diffable against
`../contract-2026-10-01/brief_G2.md`.

| label | setting | hypothesis tested | how |
|---|---|---|---|
| E | 13 real maintainer review comments with the tail of their diff hunks, from PRs before 2025-12-01 in the precedent corpus (`examples_source.json`). Chosen by family from a filtered random draw, without reference to gold; a "rename to activate dot notation" example was excluded because dot notation is a known dev miss | it does not know what an ask looks like | `brief_G2_examples.md` |
| B | list at least ten candidate requests before any tool call, check each, submit every survivor | it starts verifying correctness before it has candidates | `brief_G2_brainstorm.md` |
| S | three passes on concern subsets: S1 naming + documentation, S2 proof-golf + style, S3 generalization + duplication + scope + correctness | eight families at once overload it | `brief_G2_S1/S2/S3.md`, three runs |
| D | no PR model in the packet; the brief no longer promises one | the 56k-token packet dilutes attention | `brief_G2_diffonly.md` + `task_config.context_file=null` |
| N | only the base grant: `lean_verify_edit` and `submit_findings`, with no read, search or context tools | the investigation loop pulls it into correctness-checking | `task_config.enabled_tools=[]`, `dataset.solo_context_tools=[]` |
| V | evidence mandate: `naming_norm` on every added or renamed declaration, `declaration_search` on every added one, one shorter-proof attempt per proof over three lines | it does not gather evidence on its own initiative | `brief_G2_evidence.md` |
| H | Claude Code through the relay, with contract v2 unchanged | the harness matters for this model (it did not for gpt) | `configs/pr_review_v5_dev_medium_local397_contract2_claude.yaml` |
| R | write the review as GitHub comments in plain text first, then submit one finding per comment | the structured submission suppresses natural reviewing | `brief_G2_comments.md` |
| Q | reasoning `high` with the best brief of the first screen | thinking helps only once the filing bar is lowered | after the screen |
| K | five passes of the best first-screen condition, read in union | sampling widens reach once the model files | after the screen |

Rules, as above:
- One rep each. ≥ 4 of 23 advances to two more reps; a lever is a three-rep mean ≥ 3.33 with
  union > 2; more than 3 control findings per control PR is volume without discrimination.
- **S** is three sessions per PR, so it is read as the union of S1-S3 against the base's union over
  three reps (2). It advances at a union ≥ 4.
- **K** is read the same way: the union of five passes against the condition's own single-pass
  mean.

## Result (2026-10-03): nothing lifts a single pass off the floor; over-file is the best direction

23 judged runs, 13 settings, every session successful and control emission 0 throughout. The table
is `screen.py`; unions are from `cli report conditions`.

| setting | obligations per rep | union | empty real PRs | hits / finding | reading by the rule |
|---|---|---|---|---|---|
| base (contract v2) | 2, 0, 2 | 2 | 2-4 | 0.00-0.08 | the floor |
| **O over-file** | **3, 3, 0, 1, 0** | **4** (five passes) | **1-2** | 0.00-0.10 | first three reps' mean 2.0 < 3.33: not a lever; **K, its five-pass union, reaches the advance bar of 4** |
| Q over-file + reasoning high | 3 | - | 2 | 0.088 | < 4 |
| U no system role | 2 | - | 3 | 0.087 | no effect |
| E examples | 2 | - | 3 | 0.074 | < 4; 31 judged pairs (base 2-11) |
| N near tool-free | 2 | - | 5 | **0.200** | < 4; best aim, least volume |
| C conventions as directive | 1 | - | 3 | 0.023 | < 4; most volume, worst aim |
| B brainstorm, then verify | 1 | - | 3 | 0.062 | < 4 |
| D diff only | 1 | - | 2 | 0.040 | < 4 |
| H Claude Code harness | 1 | - | 3 | 0.059 | < 4 |
| S specialists (S1, S2, S3) | 1, 0, 0 | 1 | 3-5 | 0.000-0.027 | union 1 < 4 |
| T temperature 0.6 | 0 | - | 3 | 0.000 | < 4 |
| V evidence mandate | 0 | - | 4 | 0.000 | < 4 |

- **No single pass leaves the floor.** The best single passes are 3 (O r1, O r2, Q), against
  Opus 5.5's 7, 7 on this denominator under the project harness.
- **Over-file is the one direction that helps.**
  - It has the highest single-pass ceiling and the fewest empty PRs, with no control emission.
  - Its five passes reach 4 in union, double the base's union.
  - But the model does not carry out the instruction: it files 2.2-3.2 a PR where the brief asks
    for at least five.
- **The model's reach is capped at 5 of 23**, the union over all 23 runs, every one also reached by
  a Claude cell (13).
  - Two obligations account for most hits (9 and 8 runs).
  - The other three appear under one or two settings each.
  - So varying the prompt widens reach where resampling one prompt does not, but no setting
    accumulates the extra asks.
- **Where the model looks is not the problem.**
  - With examples it put 31 findings at gold sites and matched 2.
  - The judge's reasons show it asking for a surface change where the maintainer asked for a
    substantive one: a typo fix where the maintainer asked for a finished docstring or a
    set-comprehension definition, docstrings where they asked for `@[to_fun]` deduplication.
  - That is the record's residual for every reviewer: judgement at attended sites that turns on
    convention and mechanism knowledge.
- **Process instructions are not followed.** Brainstorm, comments-first, specialists and the
  evidence mandate each filed less than the base (1.0-1.4 a PR) and reached 0-1.
- **Settings that do nothing:** the system role, temperature and the Claude Code harness. That
  matches the record for gpt.

**What this does and does not settle.**
- The screen is one rep per setting except over-file, and the judge's noise is one to two
  obligations, so a setting at 1-2 could be a 3 on another rep. But no setting's rep left the
  floor band, and over-file, the only one replicated, regressed to a mean of 1.4.
- Untried, and plausibly beyond prompting:
  - a stronger open model (`docs/dead-ends.md`);
  - supplying the knowledge rather than asking for it, i.e. deterministic candidate asks, such as
    `naming_norm`'s rename candidates or a mechanism catalogue, that the model only vets;
  - fine-tuning, which this project does not do.
