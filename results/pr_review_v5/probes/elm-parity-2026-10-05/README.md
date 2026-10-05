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

## Result (matched 2026-10-05)

Two blind matchers on seal `907bbc6`, agreeing on 96 of 96 cells. Audits: 9 calls each; matcher 1's one
flag is the venv's python running its own `tmp/build.py`, the benign pattern adjudicated before. The
anchors reproduce their earlier seals, so this pair reads like the earlier ones.

| reach over 16 asks | X (Claude) | Hb1 | Kb1 | Eb1 | EKb1 | Eb1 - Hb1 | EKb1 - Kb1 |
|---|---|---|---|---|---|---|---|
| both matchers | 0.469 | 0.3125 | 0.25 | 0.25 | 0.375 | -0.0625 | +0.125 |

**By the rule.** `Eb1 - Hb1 = -0.0625`: parity; the endpoint and the summaries changed nothing measurable.
`EKb1 - Kb1 = +0.125` (two asks: the `cat_disch` default on `mk`, p0014, and the `_anti` rename, p0008,
reached where Kb1 was partial): under 0.25, no evidence either way for the phase fix. Eight asks are
reached by no reviewer (p0000, p0003-p0007, p0010, p0012); every gpt session reaches p0002, p0009, p0011
and p0013, as Claude does.

## The misses, read from the reasoning summaries (by hand, not blind)

Every ask Eb1 or EKb1 missed, against what its summaries and calls show. Summaries cover about half the
reasoning turns, so "not raised" means not in a summary, a preamble or a call argument.

| ask | X | Hb1 / Kb1 | Eb1 | EKb1 |
|---|---|---|---|---|
| p0000 explain why the old names are bad (a question) | no | no / no | not raised; merge-ready in 4 turns | not raised; merge-ready in 8 turns |
| p0003 add a `HasProd` version | no | no / no | `HasProd` appears only as a proof tool (`le_hasProd_of_le_prod`) | same |
| p0004 alias for the reverse implication | no | no / no | not raised | not raised |
| p0005 state it for any UFD / normalization monoid | no | no / no | **raised and dropped untested** (t12: "not sure that's feasible", then moves to the docstring) | raises a different generalisation (t17), compares, does not file |
| p0006 `mk_iff` | no | no / no | not raised | not raised |
| p0007 a section `variable {D}` | no | no / no | not raised | not raised |
| p0008 `_mono` -> `_anti` | reached / partial | reached / partial | **considered and withheld** (t17: "If I suggest a name change and the maintainers disagree, I could be creating a false positive") | reached |
| p0010 `left`/`right` swapped against `inf_sup_left` | no | no / no | not raised | **ran the precedent search** (t13, `theorem .*_sup_left.*=.*⊔`) and drew no conclusion |
| p0012 `_of_normal` rather than a prime | no | no / no | not raised | not raised |
| p0014 `by cat_disch` defaults on `mk` | reached | no / no | not raised | reached, after weighing "blocking" against "advisory" (t11) |
| p0015 the same on the later definitions | reached | no / no | not raised | filed for `mk` only |
| p0016 `mkHom` -> `homMk` | reached | no / no | looked `homMk` up (t3, t6), no stated conclusion | asks whether `PresheafOfModules.Hom.mk` could serve (t11), does not reach the name |

What the reasoning shows, by kind:

1. **Withholding is explicit, and it uses the contract's own terms.** 23 summary passages in the 12 sessions
   sort a candidate into `blocking` or `advisory` (13 and 10), and several ask whether a maintainer "would
   object", "would merge it without a request", or whether a second finding "could seem overly critical"
   (EKb1 42184 t11). The brief says "submit none when no request is warranted" and "emit a finding only for
   a concrete change you would actually request"; the tool asks for a severity and `merge_ready_as_is`.
   The 43024 withholding is the clearest case. This is the mechanism `filing_bar: request` targets
   (`filing-bar-2026-09-30`: +0.125 here for gpt-5.5, 0.00 on validation, not adopted); until now it was
   inferred from compiled-but-unfiled edits, and the summaries now show it directly.
2. **Raised and dropped without a test.** The UFD generalisation (Eb1), the `homMk` name (both) and the
   `_sup_left` convention (EKb1) each appear in the reasoning and are never tested or concluded. These are
   the asks closest to being reached: the candidate exists and the tools were at hand.
3. **Never raised.** `mk_iff`, the alias, the section `variable`, the primed helper and, for Eb1, the
   `cat_disch` defaults. Claude misses all but the last too, so these are convention knowledge, not a gpt
   gap. They are the `conventions-nature` thread's subject (guarded rules, pinpointed), not this one's.
4. **Questions are excluded by the brief.** p0000 asks the author a question; brief G says "not ...
   questions". No reviewer reaches it.
5. gpt-5.5 reasons about being scored: "The grader probably expects any actionable requests" (EKb1 43192
   t11). Once in 12 sessions.

One run a condition, and the classification is mine. What it supports: the gpt-specific losses here
(p0008 for Eb1; p0014-p0016 against Claude) are a withheld finding and candidates raised but not carried
through, not a failure to look.
