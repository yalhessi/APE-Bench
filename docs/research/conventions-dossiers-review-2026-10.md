# Convention dossiers and exams: what an adversarial round left of the idea (2026-10-08)

The idea is `docs/todo/conventions-dossiers-exams.md` (committed `19bd1fd8`):
- an evidence-built dossier per convention;
- an exam on held-out census cases;
- exam-calibrated authority in review;
- the consequences of strict adherence;
- a map of conventions × representations.

The todo asked for an adversarial review and a steelman before any run. This is that round's record:
- the four briefs as sent: `conventions-dossiers-review-2026-10/briefs.md`;
- the four reports as returned: `R1_mechanism.md`, `R2_measurement.md`, `R3_ceiling_record.md`, `S_steelman.md`;
- the fact sheet they shared: `factsheet.py`, `factsheet.txt`.

Nothing was run except counting.

## 0. The answer

**Narrow, by all four.** The three attackers say narrow, none drop, and the steelman's strongest form is narrower than the idea.

**What survives:**
- Understanding is a real failure mode and separable from the others, but small in the record: a quarter to a half of DP1's residual. In the regime where the asks are given, a perfect fix is worth at most about +0.08 to +0.15 of in-census asks.
- The exam, as specified, would measure itself, and its first slice points at the wrong conventions.
- The question the idea needs answered first is not whether a dossier teaches better than a sentence. It is **whether anything with no asks given carries DP's gain**. Every exact-brief gain on record also told the reviewer *that* these conventions are in play here, and every delivery that did not say so moved nothing (F +0.03, G +0.000).

**The thread that remains:**
- a CPU-only check, $0, now: can nearest-neighbour retrieval over the census pick a PR's conventions?
- one ask-free review test on DeepSeek, $0 in money, with matchers on the subscription after Friday's reset.
- dossiers only if that test moves, aimed at ranks 11-50 and not the head.

## 1. The round

- **Who.** Four `general-purpose` subagents, Opus 5.5 on the primary subscription, launched together, read-only, none seeing another's brief or report.
- **Lenses.**
  - R1, mechanism: is understanding separate from the decision to file?
  - R2, measurement: does the exam measure anything, at these sizes?
  - R3, ceiling, cost and the record.
  - S, the steelman.
- **The four questions** went to all of them: separability, prediction, the tail, the cheapest falsifier.
- **Cost.** 563k subagent tokens (126k-156k each, 8-9 minutes each). The primary token's week went from 93% to 94%, and its five-hour window from 1% to 6% (read 08:48 and 09:04 EDT).

## 2. Where the four agree

**2.1 As specified, the exam measures itself.**
- **It hands over what review lacks.** It gives the convention and the place. Stages F and G show those two things are where review fails: picked from the diff, +0.03; at the place with a check, +0.000 (R1 O3, R2 O1, R3 O4).
- **Separate group scores mix up understanding and willingness to file** (R2 O2). Asked items are all positives and conforming items all negatives, so a representation that only raises the readiness to file raises the asked score. Pair ordering or AUC is needed instead, with that readiness reported on its own line.
- **Nothing can tie an exam score to recall across conventions** (R2 O3). The entries with 12 or more census PRs hold 14 of the 39 in-census probe asks, on 7 entries. By R2's simulation, even a perfect exam reaches an observed Spearman of about 0.55 against reach, with power 0.36 on 7 entries.
- **The one validation available is ask-level:** the exam on the 39 probe asks, cross-tabulated against DX/DE/DP reach.

**2.2 The first slice, the head conventions with the most asks, is where examples did nothing.**

Reach on the 39 in-census probe asks, stage D rep 1, matcher 1, by the census rank of the ask's entry (computed by R3 and S, checked here against `factsheet.txt`):

| entry rank | asks | DX1 | DE1 | DP1 |
|---|---|---|---|---|
| 1-10 | 8 | 1 | 3 | 3 |
| 11-50 | 10 | 3 | 3 | 7 |
| 51-100 | 5 | 3 | 3 | 2 |
| > 100 | 16 | 1 | 7 | 11 |

- **The head-10 misses are not about understanding.** All eight top-10 asks sit under `standard` entries (P005, P011, P018, P063). DP1's misses there are:
  - checks that failed (v0092, v0093: a `simpa`/merge form that did not elaborate);
  - merits calls (v0105, p0005);
  - a convention swept but never applied at the ask's place (v0067).

  That is the try-it mechanism: 19 of the 67 residual asks (`docs/todo/reviewer-model-gap.md`, Phase 1). It belongs to the static-analysis and closer-battery thread, where 8 of 15 try-it asks came out verbatim from exhaustive procedures.
- **DP's gain sits elsewhere:** ranks 11-50 (+4) and the tail (+4). The tail is where no exam can be built, since an entry has three census asks or fewer.

**2.3 Understanding is real, separable, and a minority of the residual.**
- **The test that separates it:** does the session claim the code conforms, or agree that it departs and decline to file?
- **Claims of conformance that are wrong** (R1, read from the reasoning):
  - p0004: "directions used separately", where the maintainer's reason was usefulness;
  - 29842: "a generalization, not a new concept";
  - v0093: `exact` tried without the `simp`, rather than `simpa using h`;
  - p0010: argument position checked against local siblings, not the library's orientation.
- **Its share of DP1's 16 misses,** each reviewer's own reading of one rep, none blind: R1 3-5; R3 4-6; R2 5-7; S 7 shaped like application, of which 2 are arguably the decision. That is a quarter to a half.
- **What it could add,** with the asks given: R1 +0.08-0.13; R2 ≤ +0.11-0.15; R3 ≤ +0.10-0.15. Ask-free, multiply by the retrieval loss.

**2.4 The assertion, not the wording, carried the oracle gain.**
- **Checked here:** at the 10 in-census asks only E reached, stage G's reviewer, holding the same sentence at the same place, was `partial` at 6 on matcher 1 and 5 on matcher 2 (`match_G_*/unblinded.json`). It filed a different change where E1 filed the asked one. E's brief said these conventions apply here; G's asked the reviewer to verify each against decoys.
- DP recovered stage G's filing-bar overrides: p0007 "Mathlib does not require these", and p0006 (README Stage D, interim result).
- So the sentence often carries enough to make the right change once the reviewer is told it applies. The variable that moved the reviewer was the claim, which is the ask's own pinpointing in disguise (R1 O1, R3 §1).

**2.5 "A passed convention is applied strictly" is the disposition paragraph, and a volume lever** (all four).
- Maintainers raise a convention at 5% or less of the places its situation occurs (stage H).
- Under the disposition paragraph, gpt-5.5 filed 13 of 14 unasked detector facts (`docs/dead-ends.md`, detectors).
- The exam never measures selection, so passing it licenses volume, not recall.

**2.6 The map cannot be read cell by cell** (R2 O4, R3 O6, S §4).
- Split by PR, the top 10 conventions give 9-24 held-out items each, and below rank 30 it is 7 or fewer.
- The smallest readable paired difference is 0.34 at 20 items and 0.20 at 56. Only P005 and P019 come near 56.
- Also in the way: reader agreement is 0.809, and the judge agrees with itself about 90% of the time.
- What the map could read: perhaps three pooled contrasts. The representation effect over the head (about ±0.13), rule against standard, and a pooled tail.

## 3. Where they disagree

| question | R1 | R2 | R3 | S |
|---|---|---|---|---|
| what could replace the asks' pinpointing | upstream retrieval and localisation dominate; nothing tried | the exam cannot see it | nothing tried has: the bottleneck is the in-context-to-filed step without asks | **precedent retrieval as the selector** (V1), the one route the record leaves open (`dead-ends.md`: "precedent-based selection" untried; Mode A reopens for "recognition mode, ranking") |
| revealed preference (did Mathlib later conform?) | keep: the only gold-free read of the unasked 95% | a different measurement from Δ, but it needs control places, rename tracking and a fixed horizon; it can order adjudication, never score | reject: it follows migrations and adoption curves (grind 4% to 14.5% of files), and it bears on precision, not recall | defer: off-goal, confounded by migrations |
| self-written dossier | circular if examined on its own cases | — | genuinely untried | the strongest dossier form, if the study and exam halves are split by PR (V2) |
| coarse dossiers (family or mechanism) | — | — | they become guidelines (statute null; F +0.03) | low prior, but DeepSeek reaches 1 of 16 tail asks unbriefed where Claude reaches 9, so its gap may be knowledge a coarse text carries |

## 4. The steelman, and where it fails

**S's strongest form** has two parts:
- **(A) Retrieval chooses the conventions.** For each changed hunk, take the nearest census triples (code, ask, merged fix), and deliver their conventions with the examples under DP's precedence lead. That turns DP's "a situation like an example's" into something computed.
- **(B) Study-and-exam dossiers only for the head's judgement conventions,** examined by a paired before/after exam.
- Executable checks (V3) belong to the static-analysis thread; the dossier adds only how to read a failed check, for instance "file a failed `gcongr` as a question".

**Where it fails, in its own words:**
- Every positive result depends on the asks' own pinpointing.
- V2's recall ceiling on the probe set (+0.11) is below what one rep can resolve.
- Stage H's near-chance discrimination of demand may hit V1 too and turn it into a volume lever.
- The idea as stated has no route to recall without the asks; only V1 offers one, and it is unmeasured.

## 5. Found beside the round

- **Before/after pairs exist where understanding matters least.** 856 of 1,917 census asks with a reader-A entry carry a ```` ```suggestion ```` block, which is an exact before and after (`factsheet.txt`; the A→B ledger, `src/datasets/pull_requests/projections/ledger.py`).
  - Mechanical entries nearly always do: P017 30/32, P057 25/26, P059 27/30, P005 45/59.
  - Judgement entries rarely do: P004 2/43, P063 3/27, P100 2/24, P154 4/23.
  - DP1's merits and comparison misses (P063, P100, P011) sit in the second group. A paired exam there needs the merged code at the ask's place, and no reviewer verified that the PR store holds it.
- **Stage D's gate finished at 07:52** (`ds41_conv_gate.status`). All 18 runs are on disk, and reps 2-3 are unmatched. Matching them belongs to the `conventions-ds41` thread.
- **The local Mathlib clone ends 2026-05-14** (R2). A revealed-preference reading of val1000 would have a 2-11 month horizon.

## 6. The thread that remains, in order

| step | what | cost | reading, fixed before it runs | the most recall it can add |
|---|---|---|---|---|
| 0 (another thread's) | stage D reps 2-3 matched, read as `D1,D23` | four matcher runs, about 0.5-1M subscription tokens, after Friday's reset | **if DP − DE ≤ +0.03 over three reps, examples and precedence do not move DeepSeek even with the asks given, and a dossier, which is more of the same evidence, has nothing to build on: drop the line** (R3, S). Also: DP's stable misses sorted by R1's test of §2.3 | none by itself; it decides whether steps 2-4 mean anything |
| 1 (this thread, now) | **V1, retrieval as the selector, CPU only:** for each probe PR, rank census entries by the nearest census hunks to the PR's own hunks (MiniLM, the precedent index's model), and ask whether each in-census ask's entry is in the PR's top 5 | $0, minutes of CPU | pre-registered in its own README before it runs, against two baselines: the census's global top 5 for every PR, and stage F's selector's first five | 0; it decides whether step 3 uses retrieval's selections or stage F's |
| 2 | **the oracle ladder at ask level** (R1 §5 with R2 §5): DE's and DP's misses on the 39, each given the hunk and the sentence in three forms — "does it conform?", "a maintainer asked for this here", and the same with DP's examples — plus a hunk-only floor, three samples each | under an hour of DeepSeek server time; one or two blind matchers, about 100k tokens | R1's: representation-fixable misses (wrong when asserted, right with examples), stable 2 of 3: **4 of 22 or fewer, drop the understanding thread; 7 or more, in entries with ≥ 10 census asks, proceed**. R2's floor: the hunk-only arm ordering ≥ 0.6 of pairs makes the exam uninformative on this model | 0; a diagnosis of where misses come from, in-sample |
| 3 | **the recall test without asks:** AP (stage F's blind selections, each entry with DP's two examples under DP's precedence paragraph), or RP (step 1's retrieved entries) if step 1 passes; DeepSeek, the ten stage C PRs, three reps, one seal with DX1-3 and Claude X1/X2 as anchors | about 1.5 hours of the 8-GPU node on `first` (R3: about 12 GPU-hours), $0; matchers 0.4-0.9M subscription tokens, after the reset | R3's: **AP − DX ≥ +0.10 on both matchers**, with findings a PR no more than DX + 3.0 and asks reached a finding no lower than DX's: a lever exists without the asks; **≤ +0.05**, or a gain that fails the volume guard: evidence-rich delivery does not survive removing the asks, so drop dossiers as a recall lever (`docs/dead-ends.md`, listing self-study and index browsing as untried) | theoretical (18 − 4)/46 = +0.30 on the top-50 asks; R3's optimistic +0.09; on the record without asks, about +0.02 |
| 4 | **dossiers (V2), only if 3 moves and 2 finds ≥ 7:** self-written from the census asks on half the census PRs, examined by pair ordering on the other half, for the judgement conventions at ranks 11-50 | DeepSeek, a few node-hours | written then, against step 2's misses | S: +0.11 on the probe set at most, below one rep's resolution; read on the exam, then one review test |

**Order and why.**
- Step 1 is free and decides how step 3 selects.
- Step 3 is the measurement that answers the recall question. It is cheap to build: context files from selections already on disk, plus `probes.exemplified`.
- Step 2 can share step 3's server session.
- Step 0 is read the moment it lands, whoever matches it.
- None of steps 1-4 needs Opus beyond the matchers, and the matchers wait for Friday 10:00.
- On GPUs: the DeepSeek setup is the validated one (stage D ran 147 sessions), so step 3 does not fall under the speculative-test caution. It still waits for `first` to have room (`squeue -w first`, `oomctl`).

## 7. Rejected, with the evidence

| proposal | why rejected | reopens if |
|---|---|---|
| Exam-calibrated authority: a passed convention is applied strictly, a failed one as advisory | It is the disposition paragraph: 13 of 14 unasked detector facts filed under it. Maintainers raise at most 5% of situations. The exam never measures selection (R1-R3, S). | adjudication (`docs/todo/adjudication-rubric.md`) shows unasked filings are mostly welcome, or precision becomes the goal |
| Scoring the third group (unasked departures) | It is mined by a model pinpointer: 205 places on 16 PRs, 2.9% at an ask. Filing there is understanding times strictness, and silence is either misunderstanding or the maintainers' bar (R2 O6). | the adjudication rubric exists |
| Three exam groups scored separately | A push to file looks like understanding (R2 O2). Use pair ordering or AUC, with the readiness to file reported on its own line. | -- |
| The map, top 50 × four representations, read per cell | Smallest readable difference 0.34 at 20 items, and only P005 and P019 approach the 56 needed for 0.20 (R2 O4). It measures the exam, not recall (S). | only as pooled contrasts (head, rule against standard, a pooled tail), after the exam predicts reach at ask level |
| The map's tail column | 286 conventions have three asks or fewer, so there are no held-out cases; it is empty by construction (R3). | the census grows (held-out reading resumed) |
| A first slice on the head-10 conventions | DE1 = DP1 = 3 of 8 there. The misses are try-it and search, not understanding (§2.2). | -- ; those misses go to the closer battery and static pass |
| A 438-entry index the reviewer opens like skills | Stage F: 25 sentences diluted (+0.03, asks reached a finding fell to 0.18). The 438 level was never run for that reason (R1, S). | a selector, retrieval or other, brings a PR's list to about 5 with stage F's retrieval or better |
| Family-grain dossiers to cover the tail | Statute null at N=115; stage F +0.03 on Claude (R3). | DeepSeek's tail gap (DX 1 of 16 against Claude's 9) is tested directly: family dossiers against DX, a low prior (S) |
| Corpus prevalence at base as a decision rule or authority | p0016: DP1 counted `homMk` 25 against `mkHom` 7 and still wrote "NOT a clear naming violation". `coe_` 48:9 misled all three reviewers on d0045. A `standard` entry has no predicate to count (R1, R2, R3). | kept as information inside a dossier, tested as such |
| Unasked situations and base rates as dossier content | Stage H's deciders, told the base rate, set p at 0.05-0.10 everywhere. It teaches suppression, the opposite of DP's lever (S). | -- |
| Revealed preference as a score | Next to the Δ dead end ("never as ground truth"). Confounded by migrations and sweeps (grind 4% to 14.5% of files; P047's `λ` to `fun`). Off the recall goal (R2, R3, S). | as an order for the adjudication queue, with a per-convention conformance check, control places, rename tracking and a fixed horizon (R2); R1 keeps it as the only gold-free read of the unasked |
| A self-written dossier examined on the cases it was written from | Circular (R1). | split by PR, study half and exam half, revised on the study half only (S's V2, step 4) |
| "Proposes the merged fix" scored by the semantic judge alone | Fixes take several forms. Compile or equivalence first, and report `partial` (R2). | -- |

## 8. What this does not settle

- **Every figure in §2 rests on one probe set** (39 in-census asks, chosen for X's misses) and on stage D's rep 1. The miss classifications are each reviewer's own and none is blind. R1 found DP2 filing v0068's `gcongr`, which DP1's table lists as a failed check, so the single-rep table is noisy. Steps 0 and 2 replace it.
- **Retrieval's coverage is unmeasured.** The precedent index's hit@5 of 49% was on the bench's own corpus, never on census hunks (S). Step 1 measures it.
- **Leakage:** census merges predate DeepSeek-V4.1's release (2026-09-10), so any exam on them may read memory as understanding (R2 O5, R3 O5). Only differences between arms on the same items are read, and a saturation stop is part of every exam reading.
- **The volume question is the user's.** Step 3's guard (DX + 3.0 findings a PR) is stage W's, and whether the recall-only goal tolerates more volume than that has not been ruled.
