# Beyond the solo baseline: a general harness that beats one pass (plan, 2026-10-01)

**Status** — draft, written on `develop` at `f1a95aed` for the next planning session. No run has
been made for it. The user's direction (2026-10-01): changing models and harnesses has been the
one lever that moved the wall; the additions tried before it (agenda, specialist arms, lead) did
not; even the strong model-harness pairs are inconsistent between runs; the solo reviewer is a
solid but inconsistent baseline to build on; this is a harness-engineering project, so learn from
the open-source review harnesses and this year's literature; name what is still going wrong, and
draft how to beat the solo baseline inside a general harness.

The diagnosis in §2 is reproduced by
`results/pr_review_v5/probes/claude-models-2026-10-01/consistency.py` on committed audits and runs.
Everything else cited is in the record (`docs/todo/reviewer-model-gap.md` is the ledger).

## 1. Where the solo baseline stands

One reviewer, the whole PR, contract v2 (brief G2, the PR model before the diff, the request
filing bar, a per-declaration ledger in the submission, `file_search`), the five context tools and
`lean_verify_edit`, on a reviewed workspace.

| set | gold | best single pass | per-run spread | gpt (best condition) |
|---|---|---|---|---|
| dev held-out 12 | 23 obligations, judge v9 | Opus 5.5 brief X, probe harness: 11 / 11; swap 10; **project harness: 7, 7**; Opus 5: 8 | 7-11 of 23 | gpt-5.5 carried 3, gpt_5.2 carried 2-3 |
| validation small12 | 30 asks, blind matchers | Claude 0.48-0.50 | | gpt_5.2 carried 0.27 (q 0.57) |
| post-cutoff (6 PRs) | 16 asks, blind matchers | Claude 0.47 | Codex gpt_5.2 carried 0.19-0.31 | APE-Agent 0.21, Claude Code 0.25, Codex 0.29 |

What the record has settled, and this plan does not re-test:
- **The harness is not what limits gpt.** Three harnesses with the model held reach about the
  same (`harness-postcutoff-2026-10-01`, three runs a cell).
- **The prompt text is not what limits gpt.** Claude given gpt's contract-v2 messages verbatim
  reaches 10 of 23; gpt-5.5 under the same text 3 (`contract-2026-10-01`).
- **Opus 5 replicates Opus 5.5 (8 against 7, 7); Opus 4.8 sits where gpt-5.5 sits (3).**
- **Every reviewer aims alike.** Obligations hit per finding is 0.09-0.12 for Claude and gpt,
  under every harness and prompt. Recall follows how many changes the reviewer decides to ask for:
  Opus 5.x files 73-130 held-out findings, Opus 4.8 and gpt 29-44.
- **Coverage and withholding are not the residual.** Of 67 asks no reviewer or only Claude
  reaches, the object was attended in 63 and a verified edit withheld in 2; the misses are
  judgement on attended objects, explained by convention or mechanism knowledge (25) and compiles
  nobody ran (19) (`phase1-residual-mechanisms-2026-09-30`).

## 2. What is still going wrong

### 2.1 Each run reaches about two thirds of what the family of runs reaches

| cells on the dev held-out 12 | hit per cell | union | stable |
|---|---|---|---|
| the same configuration twice (Opus 5.5, project harness, reps 1 and 2) | 7, 7 | 8 (0.35) | 6 |
| the six Opus 5.x cells (X1, X2, swap, H55 r1, r2, M5) | 11, 11, 10, 7, 7, 8 | **13 (0.57)** | 6 |

The same shape on the other sets: Codex's three carried runs reach 7 distinct post-cutoff asks
against 4.7 each; Phase 0's three carried APE-Agent runs reach q 0.93 in union against 0.71 in
mean; the June solo condition reached 8 of 23 in union against 4, 4, 1 per rep. A single pass is a
draw from a distribution whose support is half again as wide as its mean.

The reps do not differ much in *where* they look. Two reps of one configuration share 56 of their
86 change targets (Jaccard 0.65); Opus 5 against Opus 5.5 shares 0.53-0.59; Claude against gpt
0.24-0.29. They differ in *what they ask* at the same target.

### 2.2 At an attended declaration the reviewer files one ask, and which one varies

- 33321 `IsMulIndecomposable.baseOf` carries two obligations (the docstring fix, the set
  comprehension) and one more at the module doc. Rep 1 filed the typo and hit `c9739efc`; rep 2
  filed the set comprehension and hit `5ffba48e`; Opus 5 filed the binders and hit neither. Each
  session filed exactly one thing there.
- 33149's Parseval axiom (`61f68eed`): rep 1 found `UnitAddTorus.hasSum_sq_mFourierCoeff` by
  search and filed the replacement; rep 2 and Opus 5 removed the axiom and did not find the
  lemma. The closer-battery probe found it with `grep -i parseval` on the base
  (`closer-battery-2026-09-26`). Whether the library search happens is the draw.
- 33362's namespace move (`695ae9fd`): Opus 5 and X2 reached it, neither Opus 5.5 project rep
  did. 33285's one-`simp` golf (`585e5e0b`): X1, X2, the swap and gpt-5.5 reached it, the project
  harness never put a finding at the site, while `simp [L, Subtype.ext_iff]` compiles.

### 2.3 The ten obligations no Opus cell reaches are knowledge, not attention

| obligation | what every Claude cell did at the site |
|---|---|
| `64e1164f`, `ce7b5d2e` (33337, rename `coe_…` to `toLinearMap_…`) | all three project cells asked for a *different* rename at the site (`isComplProjection` to `isCompl_projection`); Opus 5 wrote "keep the `coe_` fronting", which is `naming_norm`'s global count (`coe_` 48 to 9) speaking. X1 reached it under brief X. |
| `57bcc9fd` (33117, `@[to_fun]` in place of hand-written `fun_*` lemmas) | 3-6 findings at the site in every cell (`fun_prop` lemmas, explicit `n`, `protected deriv`); none names the attribute. |
| `7f098f6a`, `8e276803` (33294, dot notation in a name and in a `rw`) | no finding at either site in any cell. |
| `8d887ce4`, `7fef913e`, `e8e02821` (33145, `ciSup'`/`ciInf'` by duality, the `by_cases` restructure) | the exact `by_cases h : BddAbove (range f)` restructure and the exact `(α := αᵒᵈ)` dual proof were filed in both reps and scored `loc`; Opus 5's wording of the same restructure scored a hit. |
| `0bb42bd2` (33321, module doc on ordered coefficients) | every cell rewrote the sentence the ask is about; the ask also wants a section, and the judge scored `loc`. |
| `38e72250`, `55f65304`, `6b02b611` (33421) | section placement was asked at the site where the maintainer asked for a `Tendsto` lemma, a generalised statement and a rename. |

This is Phase 1's table on the dev set: a convention or a generating mechanism the reviewer does
not know, or a compile it did not run. More passes of the same reviewer do not reach these (the
six-cell union is where they stop). Two of the rows are also a measurement note: the judge's
"same place and same concern" is strict on compound asks, and that is one to two obligations of
noise on 23, in both directions.

### 2.4 The project harness costs Claude volume, and has four defects

The project harness files 22% fewer held-out findings than the probe harness for the same model,
prompt, CLI and effort (77 against 99; 7 against 10 obligations), at the same hits per finding.
Read from the sessions (`.ape/runs/probe_dev_opus55_contract2_claude_sub_rep*`):

1. **The first message contradicts the grant.** It opens with a `<WORKSPACE_PATHS>` block that
   names a read-write scratch workspace, "your primary workspace for creating and editing files",
   and the session has `Write`, `Edit` and `Bash` disallowed. The probe harness's Claude had a
   shell and wrote `findings.json` and `notes.md` as files it reread and rewrote; the project
   harness's Claude writes 1-13 visible text blocks a session (84-1,738 characters) and its
   account exists only inside the final `submit_findings` call.
2. **The finding budget truncates silently.** `finding_budget: 20` dropped 2 findings in rep 1 and
   4 in rep 2 on 33149, the AI-generated PR with 4 obligations (`_normalize_findings` warns in the
   log and nowhere else).
3. **`naming_norm` counts a prefix globally** and told three reviewers the wrong convention on
   33337 (§2.3; Phase 1's d0045, "fix first").
4. **`proof_profile` is in the grant and dead on dev** (no declaration tables), and the first
   message names two different absolute roots for the same attempt (the worktree's `.ape/runs`
   and the main checkout's).

### 2.5 Precision is the price of volume, and nothing adjudicates it

Opus 5.5 under the project harness files 1.0 per control PR; Opus 5 and the swap 4.0; gpt 0-0.5.
Gold alignment is 0.09-0.22 for Claude and 0.02-0.05 for gpt. Nothing in the evaluation says
which of the 90% off-gold findings a maintainer would have accepted (CLAUDE.md, "Reporting
results"), so a design that raises volume cannot yet be read for precision, only for control
emission.

## 3. What the review harnesses and the 2026 literature say

The September survey (`docs/research/code-review-systems-survey-2026-09.md`) found every deployed
reviewer converging on *specialised generators → a separate verifier with its own context →
suppression tuned on feedback → dedup → an acted-on metric*. Read this year, the following add to it.

| source | design | number or claim | borrowed here |
|---|---|---|---|
| Anthropic Code Review and ultrareview (docs, 2026) | a fleet of class-specific agents in parallel; a verification step that independently reproduces each candidate against actual code behaviour; dedup; severity ranking; `REVIEW.md` tunes the *verification bar* and severity definitions, not the finder; effort trades coverage for confidence | $15-25 a review, 20 minutes; ultrareview $5-25, 5-10 minutes | parallel passes; a verifier that reproduces, not judges value; tune the bar, not the finder |
| Cursor Bugbot (survey) | 8 parallel passes with randomised diff order, bucket, majority vote, validator, dedup; "aggressive" prompts after restraint made it too cautious | resolution 52% to 70% | randomised reading order as the decorrelator |
| OpenCodeReview (Aug 2026 write-up, AACR-Bench) | rule-guided dispatch; an *independent reflection* stage that sees only the diff and may remove only what the diff contradicts, never generate or judge value | 25-38% precision / 12-20% recall at 5-15x fewer tokens, against Claude Code's high-recall-low-precision; F1 2.17x on the same model | the refutation-only critic, when it is funded |
| Adversarial Review (arXiv 2608.18167) | reviewer plus critic with structured, evidence-grounded disagreement | highest F1 on SWE-PRBench with three agents against a five-agent baseline; the naive version converges on *false consensus* until disagreement is prompted explicitly | the critic must be asked to disagree with evidence, or it agrees |
| Wisdom and Delusion of LLM Ensembles for code (arXiv 2510.21513) | ten models, three benchmarks | the oracle over a union gains up to 83% over the best single model; diversity-based selection realises 95% of it; **consensus voting is a "popularity trap" that amplifies common wrong outputs**; two-model ensembles already pay | union over decorrelated passes; agreement as a label, never a vote |
| SWR-Bench (survey) | aggregation of several reviews | F1 up to +43.7% | the same |
| Harness Engineering, eleven systems (arXiv 2609.00006) | source study | no production harness retrieves with embeddings; deterministic retrieval and hand-rolled loops throughout; skills adopted in 9 of 11, MCP in 8 | deterministic evidence before the model |
| Noise Floor Audit for agent benchmarks (arXiv 2608.22331) | reruns against prompt perturbations | rerun flips 0.7-2.7% at temperature 0; semantics-preserving prompt changes give paired SDs 11-58x larger | every prompt variant is its own distribution: three reps per variant, and instruments that hold the investigation fixed |
| Code Review Agent Benchmark, c-CRAB (arXiv 2603.23448) | tests generated from human reviews | PR-agent, Devin, Claude Code and Codex together solve about 40%; agents review different aspects from humans | the ceiling is the field's, not ours alone |

Not borrowed, and why: majority voting (the popularity trap, and the user's ruling of 2026-09-22
that selection waits for a better generator); category suppression and trained actionability gates
(they need the adjudication labels item 1 of `open-code-review-comparison-2026-09.md` describes);
a fine-tuned filter (no training data at this scale, survey "checked and not borrowable").

## 4. The design: one general harness in three layers

The harness is the solo task under `claude_code`, `ape_agent` or `codex` (`src/ape/scaffolds/`),
so every layer runs the same for any model. Nothing here adds a lead, an arm, a gate or a
selection rule. Each layer is one commit series with a test, and each has its rule in §5 before
its run.

### Layer 0 — hygiene, free, first

**Built on `hygiene-layer`, 2026-10-01** (eight commits, `01b09ce7`..`786f00a1`), after a count of
what every tool call in the three Opus subscription runs came back with
(`results/pr_review_v5/probes/claude-models-2026-10-01/tool_outcomes.py`; the table is in that
README). The user's addition to the layer: a cleaning round of the tools, since runs mixed
`lean_verify` with `lean_verify_edit`, many tools failed to run or ran to a negative, and the
interface's interaction with the file storage was not principled. What the count found, and what
each item became:

| measured | built |
|---|---|
| hover, goto and goal refused on 7 of 9 calls: they took `target/Mathlib/...` where every other tool and the diff say `Mathlib/...` | one spelling for every tool: a reviewed file is `Mathlib/.../X.lean`; the refusal names the spellings (`01b09ce7`) |
| `lean_verify` described as "verify ... correctness" with a `file_path`; used 55 times in 84 as a `#check`/`example` probe, never with a file | in a review task it is the snippet probe, takes only the snippet, and says `lean_verify_edit` is for the reviewed file (`0a3d7d33`) |
| 7 `lean_verify_edit` calls never ran: `"replacement": }` to delete a span | a span without a replacement is a deletion (`0a3d7d33`) |
| whole-file compiles reported `warnings: []` on the 101-character line maintainers asked to wrap (d0041) | edit and as-is compiles run Mathlib's standard linter set, as CI does; warnings split like errors (`0a3d7d33`) |
| `declaration_search` refused `Fintype`, `Meromorphic`, `abelianizeAdj` as "not identifier-shaped" (15 of 249) | one identifier-shaped token is searched as given; prose is still refused (`f8a65df5`) |
| `naming_norm`'s one global count misled three reviewers on 33337 | the reviewed file's directory is counted beside the library and overrules a verdict it contradicts (`scope_conflict`, `7d39d0d7`) |
| `finding_budget: 20` dropped 2 and 4 findings on 33149 with a log line as the only trace | the call is refused with the count and the budget; the reviewer chooses (`50742516`) |
| the first message promised a read-write `scratch/` "for creating and editing files" with `Write` and `Edit` disallowed; two roots named for one attempt | built-in writes may land in `scratch/` and nowhere else, so the hygiene config grants `Write` and `Edit`; one resolved root (`669c217d`) |
| `proof_profile` granted and dead on every base but one | out of the solo grant (`786f00a1`) |
| the "Tools available" line named `file_read`, `content_search`, `file_search`, none of which exist under Claude Code; `zulip_search` called by a bare name | under Claude Code the line names Read, Grep, Glob and the `mcp__core__` spelling; `lean_verify` reads as the snippet probe (`332631a4`) |

Not changed, and why: the no-edit mode of `lean_verify_edit` (the correctness arm's sealed prompt
opens with it, and 33057's gold obligation is a red reviewed state; with the linters on it now
reports what CI would); `Glob`'s `head_limit` refusals (a CLI-version mismatch in the harness,
3 calls); the `submit_findings` "rejected" wording in transcripts (the scaffold ends the session
at submission; `task_result.json` is the record).

The condition: `configs/pr_review_v5_dev_medium_opus55_contract2_hygiene_claude_sub.yaml`, which is
the H-claude config with `Write` and `Edit` granted (contained to `scratch/`) and the solo budget at
40, on the tools above. Its re-baseline (§5, Layer 0's rule) is the next run.

### Layer 1 — deterministic evidence before the model

Phase 3.2 and 3.3 of `docs/plans/2026-09-30-post-carryover-replan.md`, made harness-general by
delivering them as packet sections rather than arms, so any model under any scaffold reads them:

- **the closer and exists-already battery**, run over every changed proof and declaration before
  the session (`closer-battery-2026-09-26`: 8 of 15 asks produced outright; Parseval found by a
  name grep; the dual proof by `(α := αᵒᵈ)`), its compiled outcomes given as evidence lines
  ("`simp [L, Subtype.ext_iff]` closes `cotangentEquivIdeal_symm_apply`"; "the pre-PR proof still
  compiles"; "`AddCircleMulti.lean:237` states Parseval on `UnitAddTorus`");
- **a mechanism catalogue**: the attributes and generators that replace hand-written families
  (`to_additive`, `to_fun`, `mk_iff`, `simps`, `fun_prop`, `deprecated alias`, `variable … in`),
  each with its one-line applicability test, as a brief section;
- **scoped naming evidence** (Layer 0 item 3, plus the Zulip hits the `toLinearMap_` push has);
- **the static analysis pass** (`docs/todo/static-analysis-pass.md`, the user's direction of
  2026-10-01, next up after Layer 0's re-baseline): what Mathlib's own linters, the tacticAnalysis
  set, `#lint` and `shake` say about the reviewed state and about every edit, as a packet section
  restricted to the diff, a gate on `lean_verify_edit`, and a finder for the mechanical subset.
  The standard linter set is already on every whole-file compile (`0a3d7d33`).

The census codebook on `conventions-nature` is the source for the catalogue; its PRs must be
disjoint from every evaluation set (the PR-level leakage rule).

### Layer 2 — decorrelated passes with union (the ensemble)

K whole-PR passes per PR under one contract, decorrelated on purpose, their findings unioned.

- **Decorrelators**, in the order of measured complementarity: (i) the model, Opus 5.5 and Opus 5
  on the subscription and gpt-5.5 carried under Codex or APE-Agent (Jaccard 0.53-0.59 within the
  Opus family, 0.24-0.29 across families; gpt-5.5 reached `585e5e0b`, which the project Opus cells
  did not); (ii) the reading order: each pass reads the whole PR but is handed the PR model's
  declarations in a different permutation and told to finish its pass on them in that order
  (Bugbot's randomised diff order; OCR's per-file pass that cured starved secondary members);
  (iii) a second round inside each session: "for each declaration you attended, every change you
  would request, not only the one you filed" (OCR's rounds 2+ with confirmed findings; Bugbot's
  aggressive prompt). Round (iii) is the one prompt change in this plan, and it is tested as a
  stage with a rule, on Claude, where volume tracks recall; the filing-bar null on validation was
  gpt-5.4 and gpt-5.5 (`filing-bar-2026-09-30`), and it widened targets without a per-object pass.
- **Union** by `finding_key` (`src/mathlib_review/review/merge.py:64`) and anchor, through the
  existing merge and digest; each finding carries `passes_agreeing: k of K` as a **label**. No
  vote, no threshold: union is the output. What to show is parked, as ruled, and the price of the
  union is read as control emission.
- **Mechanics**: K runs under `TaskOrchestrator`, one run name per pass (the permutation seed and
  model in the name), and a `report union` that writes the merged findings as a derived run the
  judge and `probe match-inputs` read as any other. Nothing new under `src/datasets/`.

### Layer 3 — a refutation-only critic, gated

A separate session per finding set, with the workspace, allowed only to remove a finding that a
compile or a lookup contradicts (a lemma claimed missing exists at base; a proposed edit does not
compile; a claimed convention has the opposite population in scope), and told to disagree with
evidence (Adversarial Review's false-consensus finding; OCR's filter before its fix deleted real
defects when it judged value). Never a value judgement, never generation. Gated on either
adjudicated off-gold labels (open-code-review comparison, item 1) or a control-emission reading
alone; built only if Layer 2's union raises control emission past its rule.

## 5. Measurement, and the rules before any run

- **Sets.** Dev held-out 12 (judge v9, 23 obligations) for iteration; validation small12 (30
  asks) and post-cutoff (16 asks) by blind matchers for confirmation. Dev is inside Claude's
  training window; a dev gain confirms only on the other two. 33149 (AI-generated) is kept and
  reported beside the rest.
- **Repetitions.** Three per condition; mean / union / stable; control emission on 33304 and
  33315 (and the no-ask PRs of the other sets) beside recall; asks reached per finding reported,
  not gated. One run per cell is provisional.
- **Baseline.** Opus 5.5, contract v2, `claude_code` on the subscription: 7, 7 (rep 3 partial,
  `probe_dev_opus55_contract2_claude_sub_rep3`, resumable), control emission 1.0 per PR.

| layer | rule, on dev held-out 12 unless said |
|---|---|
| 0 | no recall rule. Passes if the truncation and the contradiction are gone and held-out findings per rep are not below 77. Then three reps re-baseline. |
| 2, union of K=3 | **a lever** if the ensemble's mean recall over three ensemble reps is ≥ 0.435 (10 of 23, the swap's level), with control emission ≤ 2.0 per control PR (twice the single pass); **not, as built** if ≤ 0.35 (8). Read beside it: the 2-of-3 agreement AUC on validation, out of sample, which is `selection-signal.md`'s close condition, reported as a label's property. |
| 2, round (iii) alone | the same rule on a single pass with the second round, against the Layer 0 baseline: ≥ 9 of 23 with control emission ≤ 2.0 is a lever. |
| 1 | on the ten never-hit dev obligations and Phase 1's 44 knowledge and try-it asks: ≥ 4 of the 10 and ≥ 10 of the 44 reached by a single pass with the evidence in its packet, control emission unchanged, is a lever. |
| confirmation | on validation small12 and post-cutoff, both matchers: reach ≥ Claude's single-session reach + 0.10, with no-ask PR emission ≤ 2.0 per PR. |

## 6. Order and cost

| step | spend | wall time |
|---|---|---|
| Layer 0, then one dev rep to re-baseline | nothing billed; one five_hour subscription window | a day |
| Layer 2 on dev: K=3 (Opus 5.5, Opus 5, gpt-5.5 Codex), three ensemble reps | 6 subscription windows plus about $60 of gpt-5.5 | two to three days of quota |
| round (iii) alone, three reps | 3 windows | a day |
| Layer 1: the battery is compute only; the catalogue is reading; one dev rep, then three | 3-4 windows | after `conventions-nature`'s codebook, or with the attributes list alone |
| confirmation on validation small12 and post-cutoff | 2-3 windows a set plus matching | after a dev lever |
| Layer 3 | about $30 | only if Layer 2's control emission fails its rule |

A dev run is 20-24M processed tokens, one window; rep 2 showed that two accounts' tokens can serve
one run through `run --resume`. The cheap instrument for any closing-instruction change is the
decision-turn replay (`cli replay`, built for the arms): resume a recorded solo session at its last
turn with the changed instruction and resample only the submission, which holds the investigation
fixed and costs one cached-prefix turn a session. Extending it to the solo task is the first thing
to build if §5's prompt rule is reached and a second wording is wanted.

## 7. Not in this plan, and the untried designs if it fails

- **No lead, arms or gate.** Phase 2 is unfunded on Phase 1's table; coverage is 6% of the residual.
- **No selection, ranking or publication rule.** Agreement is recorded as a label. The ruling of
  2026-09-22 stands until the generator is judged good enough.
- **No prompt rewriting as a thread.** The swap settles that the text is not gpt's limit; brief X
  against G2 is within judge noise for Claude; and the noise-floor result says each wording is its
  own distribution. The one change made (round (iii)) is a stage with a rule.
- **No bigger caps, no more retrieval breadth, no plain resampling of gpt** (transcript inspection,
  Phase 0).

If Layer 2 is not a lever as built, the untried decorrelators are: concern-ordered reading (a
permutation over families, not a remit, since arms with a remit were silent); brief X against G2
across passes; effort xhigh against high; a shell in one pass and none in another; a second model
family as the critic. If Layer 1 is not, the next input is the design-comparison line's analogue
retrieval (`review-design-comparison.md`), which the never-hit set's `ciSup'` and `to_fun` rows
also point at.
