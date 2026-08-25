# R0 verdict (round 1): INCONCLUSIVE — the two arms were not the same judge

*Run 2026-08-05. 18 pairs (3 reps × 6) from the 0.9.0 stable smoke, `gpt_5_mini`.
Task-arm cost ≈ $0.22 total. Reports: `report-rep{1,2,3}.json`.*

## Headline

| metric | value |
|---|---|
| pooled issue agreement | **14/18 = 77.8%** (gate: ≥95%) |
| pooled resolution agreement | 16/18 = 88.9% |
| split-vote pairs (task arm, n=3) | **1/18** |
| decision | `judge_migration_not_equivalent` on all three reps |

**But the comparison is confounded and the number should not be quoted as the migration's
disagreement rate.**

## The confound

The script arm pins its sampling parameters:

```python
LLMConfig(model_name=model, max_tokens=1200, thinking_budget_tokens=512)
```

The task arm's config left them unset, so it inherited the framework defaults
(`max_tokens=32000`, `thinking_budget_tokens=30000`). Measured from the run artifacts, the
task arm actually used **832–2752 reasoning tokens, median 1728** — three to five times
the script arm's 512-token budget.

Same prompt, same rubric, same parsing, same model — but materially more deliberation.
That is a different judge, not a different harness, so R0 as run measured *deliberation
depth*, not the migration.

The offline gates missed this because they checked prompt parity and identity parity but
never inference-parameter parity. `test_judge_config_pins_the_same_inference_parameters_as_the_script_arm`
now closes that hole, and the config pins 1200/512.

## Why the confound is the likely explanation

The disagreements are directional and internally stable, which is what a
more-deliberation effect looks like and *not* what sampling noise looks like:

| direction | count |
|---|---|
| script `True` → task `False` (task stricter) | 1 |
| script `False` → task `True` (task looser) | 3 |

**All four disagreeing pairs were unanimous 3/3 in the task arm.** If these were coin-flip
pairs, the task arm's three samples should have split on some of them; instead it split on
only 1 of 18 pairs overall. So the task arm is internally stable and confidently lands
elsewhere than the script's single cached draw.

Two obligations account for 3 of the 4 disagreements, and one of them
(`…0898b0478443`) disagrees in 2 of 3 reps — i.e. the disagreement tracks specific
borderline *content*, not random draws.

## The borderline content, for the record

The most repeated disagreement is `coveringNumber_two_mul_le_externalCoveringNumber`:

- **Gold**: replace `rcases … with (h_empty | h_nonempty)` by `(rfl | h_nonempty)` and
  discharge the empty case with `simp`.
- **Candidate**: claims the split is *dead code* because `h_nonempty` is unused, and
  proposes removing it.
- **Script** (1 sample): `issue=True` — same unnecessary split, different fix.
- **Task** (3/3 unanimous): `issue=False` — the candidate's stated problem is not the
  maintainer's problem.

Both readings are defensible under the rubric ("a different fix may still issue-match"
favours the script; "sharing a declaration is not enough" favours the task arm). This pair
is genuinely near the boundary and would be a good addition to the standing judge audit
regardless of how R0 resolves.

## An asymmetry that limits any rerun

The script arm has **one** cached sample per pair; the task arm has three. So a
disagreement cannot be attributed between "the script's single draw was its own minority
outcome" and "the arms genuinely differ" — the script's per-pair distribution was never
measured, because the script form has no `sample_count`. That asymmetry is itself part of
the argument for the migration.

## What to do next

1. **Rerun the task arm with parameters pinned** (config now does this), under fresh run
   names — `global_index` hashes the task *data*, which is unchanged, so reusing the old
   `run_name` would resume and skip execution rather than re-judge.
2. If agreement then clears 95%, the migration is equivalent and the round-1 numbers here
   are explained by deliberation depth.
3. If it does not clear, the residual disagreement is a real judge-boundary effect. In
   that case do **not** treat either arm as ground truth: sample the *script* arm three
   times on the disagreeing pairs to measure its own per-pair distribution, and report the
   flip rate as the R0 finding — it is the number every n≈8-denominator comparison must be
   read against.

## Standing lesson

"Same judge" means prompt **and** decode parameters **and** model. Two of the three were
verified offline before spending; the third was not, and it was the one that moved the
result.
