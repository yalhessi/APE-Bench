# Does the conventions ceiling hold for gpt-5.5? (stage M, pre-registered 2026-10-05, before any run)

The user (2026-10-05), after Result 3: replicate the exact-conventions experiment on other model
families, *"with GPT 5.5 with reasoning"*. The local model already has it (stage L, README Result 2:
+0.051, against Claude's +0.28 in Result 3), so this stage is gpt-5.5 alone.

## Conditions

gpt-5.5 (`elm_gpt_5.5`, snapshot gpt-5.5-2026-04-23) through the ELM gateway's Responses route, effort
high, reasoning carried, reasoning summaries on: the record's gpt-5.5 probe condition on these sets
(`configs/pr_review_v5_probe_2026_07_08_v1_elm_gpt55_Grc.yaml`, Eb1 in `../elm-parity-2026-10-05/`;
`configs/pr_review_v5_val_small12_elm_gpt55_Grc.yaml`, its validation twin). Brief G (brief X's text),
`user_prompt: v1`, APE-Agent, the arms' tools, 160 turns. One thing differs between the two conditions,
the context file (`run_elm.sh <val|post> <base|exact> <rep>`):

| label | the user message ends with | PRs | reps |
|---|---|---|---|
| GB | the PR model (`context_<set>_base.jsonl`, the bytes Eb1 and the val baseline read) | the 8 and the 6 with asks | 3 |
| GE | the PR model, then the exact section (`context_<set>_exact.jsonl`, stage L's file) | the same | 3 |

- The exact section is stage L's and stage C's: the entries the two assign-only readers put behind the
  PR's asks, under the fixed lead. 43024's is empty, so GE reads there what GB reads.
- Delivery: at the end of the user message, after the model (stage L: the same; stage C: the end of
  `brief.md`).

## Matching and reading rule, fixed now

One seal a set over X1, X2 (Claude, the anchor), GB1-3 and GE1-3, eight reviewers a PR as in stage L;
two blind matchers a set, the harness's rubric. `read_stage.py M GE GB`.

Per-session reach on the 39 in-census asks, pooled over the two sets, on each matcher:

| GE − GB, on both matchers | reading |
|---|---|
| **≥ +0.15** | **the ceiling holds for gpt-5.5**: knowing the right conventions moves it as it moves Claude |
| **≤ +0.05** | **it does not hold**: like the local model, gpt-5.5 does not turn a stated convention into the ask |
| between | inconclusive at this size; read the per-ask table and the reasoning summaries before saying more |

Asks reached per finding must be no lower under GE than under GB.

**Also read:** out-of-census asks (the within-session control); findings a PR; GE − GB beside Claude's
E − X (+0.256 / +0.282) and stage L's LE − LB (+0.051); and, for in-census asks GE still misses, what
its reasoning summaries say at that place: the first gpt runs whose reasoning can be read.

## Cost, expected

Billed at list price, from the record: about $5.7 a post-cutoff run (Eb1, 6 PRs, 7 min) and about $8 a
validation run (8 of the 11 PRs of `probe_val_small12_gpt55_Grc_rep1`, 19 min for 11), so twelve runs
are about $80 billed, $300-330 before cache discounts. ELM's own figure is in pounds against the key's
£500 (`ape/bin/python -m ape.llm_clients.elm_budget`; £491.80 left at 2026-10-05 00:00, synced daily),
and which of the two it tracks is not known. Matchers: Claude subagents on token B, four runs.

## As run: one briefed run a set, against the unbriefed runs on disk (revised 2026-10-05, before any briefed session)

The user, as the first runs started: *"We already have no conventions … We just need one run with
exact conventions."* So the stage is one GE run a set, and GB is the unbriefed gpt-5.5 runs already
on disk, all at the same snapshot, effort high, reasoning carried, brief G, `user_prompt: v1`:

| label | run | route | PRs |
|---|---|---|---|
| GB1, validation | `probe_val_small12_gpt55_Grc_rep1` | OpenAI directly | 11, of which the 8 with asks are matched |
| GB1, post-cutoff | `probe_postcutoff_elm_gpt55_Grc_rep1` (Eb1) | ELM, summaries on: GE's own config | 6 |
| GB2, post-cutoff | `probe_postcutoff_gpt55_Grc_rep1` (Hb1) | OpenAI directly | 6 |
| GE1, each set | `probe_conv_<set>_elmgpt55_exact_rep1` | ELM, summaries on | 8 and 6 |

- The seal per set holds X1, X2, GB and GE1: five reviewers a PR on post-cutoff, four on validation.
- The rule above is unchanged: GE − GB on the 39 in-census asks, pooled, both matchers. With one
  briefed run it is provisional, as stage C's was.
- **What differs between GB and GE besides the brief, stated:** on validation the endpoint (OpenAI
  directly against ELM), the reasoning summary, and the harness's code date; on post-cutoff, for GB1,
  only the date. `../elm-parity-2026-10-05/` read Eb1 − Hb1 = −0.0625 (parity) on these PRs.
- **Stopped and not used:** the driver's first two runs, `probe_conv_{val,post}_elmgpt55_base_rep1`,
  were stopped about five minutes in, three sessions each completed. Their run directories stay out of
  the commit; their spend is in the ELM total.
- **Matchers moved to this session's own login.** Token B now refuses every call ("Your organization
  has disabled Claude subscription access for Claude Code"), and token C was spent until 14:50. The
  four matchers run as subagents of the orchestrating session, the route of stage L and of stage C's
  post-cutoff round. Decided before any cell was judged.

## Result (2026-10-05): the ceiling holds for gpt-5.5 -- +0.222 on both matchers, in-census reach 0.19 to 0.41

Two briefed runs (GE1), matched blind beside the unbriefed gpt-5.5 runs on disk (GB) and Claude's
X1, X2 under one seal a set. Agreement 116 of 120 cells (validation) and 80 of 80 (post-cutoff); all
four matcher transcripts audit clean. `read_stage.py M GE GB` prints the tables.

| per-session reach (issue recall), matcher 1 / 2 | GB, unbriefed | GE, exact | GE − GB | Claude X, same seal |
|---|---|---|---|---|
| **in-census asks, pooled (39), the rule's measure** | 0.19 / 0.19 | **0.41 / 0.41** | **+0.222 / +0.222** | 0.46 |
| validation (25) | 0.16 | 0.36 | +0.20 | 0.48 |
| post-cutoff (14) | 0.21 | 0.50 | +0.29 | 0.43 |
| all asks (46) | 0.26 / 0.24 | 0.43 / 0.41 | +0.18 / +0.17 | 0.49 / 0.47 |
| out-of-census (7) | 0.67 / 0.56 | 0.57 / 0.43 | −0.10 / −0.13 | |

**By the rule (`≥ +0.15` on both matchers): the ceiling holds for gpt-5.5.** Provisional: one briefed
run a set, and on validation one unbriefed run, through OpenAI directly at an earlier date.

- **Nine in-census asks gained, none lost**, all on both matchers: three instance-implicit binders
  (34091), two auto-params and a name (43192), two `simpa` closes (32875) and a shared `variable`
  (42814). Every one is an ask no unbriefed gpt-5.5 session reached.
- **The out-of-census drop is one ask:** 43024's `_anti` naming ask, reached by one of the two
  unbriefed sessions and not by GE. 43024's brief is empty, so GE read there what GB read: this is
  session noise, not the brief.
- **It is not volume:** 31 findings against 30, asks reached per finding 0.53 / 0.50 to 0.65 / 0.61.
- **Beside the other models** (in-census, unbriefed to exact): Claude 0.46-0.49 to 0.74 (+0.26 / +0.28,
  stage C), gpt-5.5 0.19 to 0.41 (+0.22), the local Qwen3.5-397B 0.03 to 0.09 (+0.05, stage L).
  Briefed gpt-5.5 reaches about what unbriefed Claude does. The local model is the exception: it is
  at the floor and does not turn a stated convention into the ask.

**Cost.** The two briefed runs record $47.18 before cache discounts ($18.90 validation, 10.6 min;
$28.28 post-cutoff, 8.2 min); this morning's parity run billed a quarter of its recorded figure. The
two stopped unbriefed runs add six sessions. The ELM key's own figure syncs daily. Matchers: about
400k subagent tokens on the orchestrating session's login.

## Also read (2026-10-06): what GE's reasoning summaries say at the 23 in-census asks it still misses

Pre-registered above and not reported with the result. Read by hand after the fact, not blind: first
by the session that drafted `docs/plans/2026-10-06-generation-without-suppression.md`, then every miss
by an adversarial reviewer against the raw logs (`reasoning_content` in each task's last
conversation file).

| how GE missed the ask | asks |
|---|---|
| considered, then dropped on a guess about maintainers | 2: v0030 (t2, the census's full-words convention against `MGFs`: "I doubt that maintainers would request changes for commonly used acronyms"; `findings: []`); v0093 (a `simpa only ... using` close compiled early, then "not entirely confident about that choice", not filed) |
| considered, rejected on the merits | 1: v0067 |
| considered, untested, or the check failed | 7: v0068, v0092 (checks failed; a compiled `rw` alternative at v0092 left unfiled with no reason), p0005 (found the general lemma at t12, dropped with no reason), p0010, p0012, v0053, v0056 |
| a different change filed (matcher `partial`) | 2: v0060, v0061 |
| never considered | 11: v0029, v0055, v0062, v0063, v0064, v0090, v0105, p0000, p0003, p0004 at its place, p0006 |

So the briefed gpt-5.5 mostly misses by never considering the asked change, as the unbriefed runs do
(`../elm-parity-2026-10-05/`); withholding is real and small. GE also left a compiled `positivity`
extension on 42184 unfiled (not an ask). One run a set, and the classification is not blind.
