# gpt-5.5 through ELM, phase kept and reasoning summarised (pre-registered 2026-10-05, before the seal)

**Question.** The direct OpenAI key died on 2026-10-05; branch `gpt-harness-parity` moved the GPT models
to ELM's `/v1/responses` (same snapshots), kept each replayed message's `phase`, made carried reasoning
mandatory and added reasoning summaries. Did any of that change gpt-5.5's reach on the post-cutoff set,
and what do the summaries say about the asks it misses?

| label | run | harness | what differs from its baseline |
|---|---|---|---|
| Eb1 | `probe_postcutoff_elm_gpt55_Grc_rep1` | APE-Agent | endpoint (ELM), reasoning summaries. These sessions write no text between calls, so `phase` never arises |
| EKb1 | `probe_postcutoff_elm_gpt55_Grc_codex_rep1` | Codex | endpoint, summaries, and `phase` kept: 445 of 445 replayed messages phased |
| Hb1 | `probe_postcutoff_gpt55_Grc_rep1` | APE-Agent | baseline, 0.3125 on its earlier seal |
| Kb1 | `probe_postcutoff_gpt55_Grc_codex_rep1` | Codex | baseline, 0.25 on its earlier seal |
| X1, X2 | the Claude probe sessions | | anchors: 0.469 on every earlier seal |

Configs: `configs/pr_review_v5_probe_2026_07_08_v1_elm_gpt55_Grc{,_codex}.yaml`. One run each, $5.74 and
$4.72 billed at list prices. Both runs: 6 of 6 sessions submitted, every finding anchored; the Codex
containment audits all clean.

**Protocol.** As `harness-postcutoff-2026-10-01`: the 6 PRs with round-1 asks (16 asks), six reviewers a
PR shuffled to R1..R6 under `blinding_SEALED.json`, two blind matchers (Claude subagents) with the
generated rubric, both transcripts audited before anything is unblinded. Sources in `sources.json`.

**Reading rule** (stated before the runs, unchanged). One run a cell; gpt-5.5's runs move by about two
asks between repetitions.
- Parity, `Eb1 - Hb1`: `|d| < 0.25` (four asks) on both matchers is no evidence that the endpoint or the
  summaries changed anything; `d <= -0.25` is a possible regression, to be repeated before any other gpt
  run.
- The phase fix, `EKb1 - Kb1`: `d >= 0.25` is suggestive and earns two more repetitions; under it, no
  evidence either way.
- Matchers that disagree on a difference make it inconclusive.

**Then, by hand.** For every ask a gpt session misses, read its reasoning summaries and classify the
miss: never looked at the object; looked, did not consider the concern; considered it and rejected it
on the merits; considered it and withheld it (named a filing bar or false-positive risk). The summaries
cover about half of the reasoning turns (37 of 76 and 31 of 67), so "not in a summary" is not "not
considered". Classification is mine, not blind, and read as such.
