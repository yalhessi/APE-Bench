# Claude models under the project's harness (2026-10-01)

The readings of `docs/plans/2026-10-01-claude-models-under-the-harness.md`. That plan states the
rules, before any run. Every cell runs contract v2, unchanged, under Claude Code. The
per-invocation prompts are identical to the ape_agent contract-v2 run's: 1605 of 1605 hashes
(`a075e26`). What varies is the harness (Claude Code's own system prompt and tools, APE's preamble
in the first user message) and then the model.

Route: Claude Code on the subscription (`claude-subscription`: `75d85bd`, `ea47258`), CLI 2.1.285,
effort xhigh. xhigh is a guess, since the probe harness recorded none. Caps are contract v2's
(160 replies, 16.08M tokens a session).

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
