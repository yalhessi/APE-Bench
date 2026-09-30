# Phase 3.1: the filing bar (pre-registered 2026-09-30, before its runs)

Phase 3.1 of `docs/plans/2026-09-30-post-carryover-replan.md`.

## The mechanism, already observed

In test (e)'s amended seal, gpt-5.4 and gpt-5.5 at high effort with reasoning carried compiled the
maintainers' asks and then declined to file them (`../model-inspection-2026-09-30/`): gpt-5.5 left 4
of 10 verified edits unfiled, gpt-5.4 2 of 10, gpt_5.2 0 of 7 (and 1 of 56 over Phase 0's carried
runs). Asked why, with their reasoning replayed: "not something I would expect a maintainer to
require", "only an optional ergonomic improvement", "a naming preference", "minor docstring polish".
The maintainers asked for exactly those.

Three places in the task framed a finding as a merge verdict, all shared by every gpt condition:
the brief's "would plausibly request" beside "emit a finding only for a concrete change you would
actually request"; the task message's `severity` line, "`blocking` if a maintainer would withhold
merge over it"; and the submit tool's `merge_ready_as_is`, "True if a maintainer would merge without
requesting changes".

## The change (`SoloReviewConfig.filing_bar: request`)

Generic, naming no ask:
- **Brief** `brief_G_bar.md`: `brief_G.md` plus one paragraph: the bar is "would request", not
  "would require"; maintainers comment on small polish routinely; a verified change the reviewer
  would suggest is filed, `advisory` when not insisted on.
- **Severity line**: "`blocking` if the change is needed for correctness or policy; `advisory` for
  every other change you would request. Advisory findings count in full."
- **Submit tool**: no `merge_ready_as_is`; the mandate's empty-review instruction no longer names it.

`filing_bar` defaults to `merge`, which renders every earlier run's wording byte for byte
(`tests/datasets/test_pr_review_v5_solo_task.py`). The field is in the scaffold config, so it is in
every run plan's digest.

## Runs

| label | run | model | set | bar | config |
|---|---|---|---|---|---|
| Hac | `probe_postcutoff_gpt54_Grc_rep1` | gpt-5.4 | post-cutoff | merge (done, f7bd8db) | `..._gpt54_Grc.yaml` |
| Hbc | `probe_postcutoff_gpt55_Grc_rep1` | gpt-5.5 | post-cutoff | merge (done) | `..._gpt55_Grc.yaml` |
| Hac_bar | `probe_postcutoff_gpt54_Grc_bar_rep1` | gpt-5.4 | post-cutoff | request | `..._gpt54_Grc_bar.yaml` |
| Hbc_bar | `probe_postcutoff_gpt55_Grc_bar_rep1` | gpt-5.5 | post-cutoff | request | `..._gpt55_Grc_bar.yaml` |
| Va | `probe_val_small12_gpt54_Grc_rep1` | gpt-5.4 | validation | merge | `pr_review_v5_val_small12_gpt54_Grc.yaml` |
| Vb | `probe_val_small12_gpt55_Grc_rep1` | gpt-5.5 | validation | merge | `..._gpt55_Grc.yaml` |
| Va_bar | `probe_val_small12_gpt54_Grc_bar_rep1` | gpt-5.4 | validation | request | `..._gpt54_Grc_bar.yaml` |
| Vb_bar | `probe_val_small12_gpt55_Grc_bar_rep1` | gpt-5.5 | validation | request | `..._gpt55_Grc_bar.yaml` |

All at high effort, Responses, reasoning carried, `declaration_search` fixed, caps the models'
post-cutoff carried caps (160 turns; $12 / 14.4M for 5.4, $20 / 24M for 5.5 a session). Six runs;
expected about $45 (the post-cutoff carried runs billed $3.22 and $5.14), ceilings $72.50 / $120.50
/ $132.50 / $220.50 / $132.50 / $220.50.

## Seals, committed before any matcher

| set | reviewers | anchor |
|---|---|---|
| post-cutoff | X1 X2 Gr1 Hac Hbc Hac_bar Hbc_bar | Gr1 (0.3125 in every matching) |
| validation | X1 X2 Grc1 Va Vb Va_bar Vb_bar | Grc1 (0.267 in Phase 0) |

Two blind matchers per seal, audited, then unblinded. Hac and Hbc are re-matched in the new seal so
the four post-cutoff conditions sit under one matcher pair.

## Reading rule

**Validation decides.** Post-cutoff is in-sample for this change: its six PRs are the ones whose
transcripts showed the mechanism, and the brief's four examples of polish are generic spellings of
what those PRs asked for. Post-cutoff is read as a check that the fix reaches the observed edits,
not as the result.

Per model, on validation, on both matchers:
- **The bar was the mechanism** if reach(bar) − reach(merge) ≥ 0.10 (three asks of 30), with asks
  reached per finding no lower than X's on this set, so filing more is not read as aiming better.
- **Not the mechanism** if the difference is ≤ 0.03.
- Between: partial.

Also read, per model and set: q against X; findings filed and verified edits unfiled
(`../model-inspection-2026-09-30/filing.py`); turns, cost, capped sessions; and whether the model
that moves reaches Claude's level (q ≥ 0.8), which would make it the base model for Phase 3.

One run per cell, so every reading is provisional. Two matchers, and the anchors, are the check on
the matching.
