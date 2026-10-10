# Beating the solo reviewer with conventions: the picture on 2026-10-09

**The question** (the user, 2026-10-09): *"I want to have a clearer picture of how to improve on the
solo reviewer to get a better deployable reviewer. I still believe sticking to the conventions is a
good direction."*

*Revised 2026-10-10: the benchmark stated once, and every reviewer in one table, because the
tables below it had mixed subsets and seals.*

**Scope.** All of it is in-sample, and it is a direction, not a claim. "Deployable" means the
reviewer never sees the maintainers' asks.

## The benchmark, and why the numbers differ between tables

**One benchmark throughout: the conventions probe sets** (`results/pr_review_v5/probes/conventions-ceiling-2026-10-04/`).
- **The set:** 14 Mathlib PRs (validation small12 and the post-cutoff probe), with 46 real
  maintainer first-round asks. For 39 of them a census convention covers what the maintainer asked
  for: the **in-census asks**, the measure's denominator.
- **The measure:** per-session reach, the share of the in-census asks one review session's findings
  reach, judged by two blind matchers. A condition ran one to three sessions; the table gives the
  count.
- **The ten PRs:** stage C ran only the ten PRs that hold an in-census ask neither unbriefed Claude
  session reached. Of the other four, three hold 6 in-census asks that both Claude sessions reach,
  and one holds none. Stages C, F, G and AP ran only these ten (AP because stage F's picks exist
  only for them); L, M and D ran all 14. So the one comparison every condition shares is the **ten
  PRs, 33 in-census asks**. They are the harder PRs, so every reviewer scores
  lower there than on all 14.

**Why the same reviewer shows different numbers:**
- **The subset:** 14 PRs or 10. For example, solo DeepSeek reaches 0.22 on all 14 and 0.16 on the ten.
- **The seal:** each round is matched afresh, by new matchers, with the two Claude solo sessions (X)
  in every round as an anchor. The same two sessions read 0.27-0.39 on the ten PRs across seven
  seals (0.36-0.49 on all 14). That ±0.06 is matching noise, so compare conditions within a seal
  when one exists.
- **Unions:** a union of reps is not a single session. Unions appear only in the AP table below,
  marked "∪".

## Every reviewer on the same ten PRs (33 in-census asks)

Per-session reach, matcher 1 (matcher 2 where it differs). `read_common.py` in the probe folder
prints every cell from the committed match tables.

| reviewer | sees the asks? | ten PRs | all 14 PRs, where run | round, sessions |
|---|---|---|---|---|
| **solo** | | | | |
| Qwen3.5-397B | no | 0.02 | 0.03 | L, 3 |
| gpt-5.5 | no | 0.16 | 0.19 | M, 1 on validation and 2 on post-cutoff |
| DeepSeek-V4.1-Flash | no | 0.16 (0.14-0.16) | 0.22 | AP and D, 3 |
| Claude Opus 5.5 | no | **0.36** on AP's seal (0.27-0.39 over seven seals) | 0.38-0.49 | every round, 2 |
| **conventions chosen from the diff alone (deployable)** | | | | |
| Claude + 25 picks, as sentences (A) | no | 0.39 / 0.36 (X on the same seal: 0.36 / 0.33) | not run | F, 1 |
| **DeepSeek + the same 25 picks, with examples and precedence (AP)** | **no** | **0.34** | not run | AP, 3 |
| **the PR's own conventions (ceiling, not deployable)** | | | | |
| Qwen + exact (LE) | yes | 0.04 | 0.09 | L, 3 |
| gpt-5.5 + exact (GE) | yes | 0.30 | 0.41 | M, 1 |
| gpt-5.5 + exact + disposition paragraph (GD) | yes | 0.55 on 31 of the 33 (GE on the same seal: 0.32) | 0.62 (13 PRs) | W (branch `generation-suppression`), 1 |
| DeepSeek + exact (DE) | yes | 0.37 | 0.44 | D, 3 |
| DeepSeek + exact + examples + precedence (DP) | yes | 0.62 / 0.61 | 0.64 | D, 3 |
| Claude + exact (E) | yes | 0.70 | not run | C and F, 1 |

**How to read it:**
- Solo DeepSeek and solo gpt-5.5 are tied at 0.16, well below solo Claude at about 0.36.
- AP, the ask-free conventions, roughly doubles DeepSeek to 0.34, close to solo Claude.
- The same picks given to Claude as bare sentences moved it by only +0.03.
- The ceiling rows show what the conventions carry once chosen right: 0.55-0.70 on the three stronger
  models.

**The other benchmark, the dev held-out 12,** is separate. It has 23 obligations on 12 other PRs,
scored by the pipeline's judge v9, not by these matchers. Its solo readings:
- DeepSeek: 8, 6, 9 of 23;
- Opus 5.5: 11, 11 under brief X on the probe harness (the X sessions here), and 7, 7 under the
  project harness;
- gpt-5.5 under contract v2: 3 of 23;
- Qwen: 2, 0, 2.

No convention condition has run on dev. It counts as development material under the 2026-09-24
ruling, which is why the deciding test below is the fresh set, not dev.

## In one paragraph

Conventions are the right direction, and today was the first time an ask-free version moved a
reviewer.
- **AP (ask-free conventions in the reviewer's context) reached 0.34 of in-census asks** on the ten
  PRs, against solo DeepSeek's 0.16. That is about what unbriefed Claude Opus reaches (0.36), at fewer
  findings. AP gives the solo reviewer 25 conventions chosen from the diff alone, each with two
  real maintainer asks for it from other PRs, and tells it they outrank its own judgement.
- **The gain sits where the selector picked the right convention:** 0.50 against 0.20. So the lever
  now is choosing conventions well.
- **A finer-grained alternative, asking each convention's question at each changed place,** would
  reach more (about 0.55, simulated), but files about 25 times as much.
- **Simply unioning solo runs** adds a little, at no design cost.

## AP and its combinations, on AP's seal (the same ten PRs)

| reviewer | deployable? | in-census reach, 10 PRs (33 asks) | findings a PR | evidence |
|---|---|---|---|---|
| solo DeepSeek, one rep | yes | 0.16 | 2.7 | stage D, matched again under AP's seal |
| solo, two reps unioned | yes | 0.19 | ~5 (union) | same seal |
| **AP: 25 ask-free conventions + examples + precedence** | **yes** (picks made by Opus from the diff) | **0.34** | 4.9 | stage AP, three reps, both matchers |
| AP unioned with one solo rep | yes | 0.36 | ~7.6 | same seal |
| per-place engine ∪ one solo rep (each picked convention asked at each changed place, one turn) | yes, but heavy | ~0.55 (simulated from measured parts) | ~68 (median) | places test + ladder, in-sample estimate |
| *ceiling:* the conventions behind the PR's own asks, with examples and precedence (DP) | no | 0.62 | 3.5 | stage D |
| *reference:* unbriefed Claude Opus | yes | 0.36 | 5.3 | same seal |

## What we learned

1. **The knowledge is in the census conventions.**
   - At the right place, the convention's one sentence is enough for the model to write the
     maintainer's change for most asks. With the sentence it gets 29 of 39; told only "a maintainer
     asked here", 5 of 39 (the ladder, blind).
   - Of the 6 asks no condition ever reached, 5 are in the census (`ceiling-residual-2026-10.md`).
2. **"Understanding" is not the bottleneck; attention and licence are.**
   - DP's gains were already within the bare sentence's reach at the place.
   - Adding examples made the model more conservative at the place, not more accurate. So
     per-convention dossiers, a richer representation, are not supported as the lever.
3. **The ask-free delivery works when it has precedence and examples.**
   - Earlier ask-free tries (Claude without precedence) moved nothing: +0.03, +0.00.
   - AP on DeepSeek moved +0.18.
   - Its added findings hit asks at nearly solo's own rate (0.28 against 0.31 a finding), so it is
     not a flood. It does miss its pre-registered yield guard by 0.014.
4. **Selection is the lever now.**
   - AP's gain is all on the 22 of 33 asks whose convention the selector picked: 0.50 against solo's
     0.20.
   - It is nothing on the other 11: 0.03 against 0.09.
   - The picks came from an Opus selector reading only the diff, holding 0.67 of the right entries at
     25.
5. **The per-place engine is a high-recall, low-precision generator.**
   - It says "departs" at 70% of asked places and 28-30% of others, so about 7% of its filings are
     asks (the places test).
   - Its value depends on whether those unasked departures would be welcome, which nobody has judged.
   - Under the 2026-09-22 ruling it is measured as a generator; caps are selection.

## Since the summary was first written: DeepSeek as the selector (`results/pr_review_v5/probes/conventions-selector-2026-10-09/`)

**The test.** Can DeepSeek choose AP's conventions itself, in one turn, with stage F's rubric?

| on the 10 stage F PRs (33 asks) | DeepSeek, mean of 3 samples | the union of its 3 samples | Opus |
|---|---|---|---|
| recall@25 | **0.43** | 0.64 (at ~38 picks a PR) | **0.67** |
| recall@10 | 0.25 | | 0.45 |

**The verdict.** By the rule (≤ 0.45), one DeepSeek turn cannot replace Opus. The union of three
samples comes near Opus at half again as many picks. So for now AP's gain needs Opus's picks: one Opus
call a PR, on the subscription route.

## The recommended path

1. **Improve the selector, because that is where AP's remaining gain is.**
   - One DeepSeek turn reaches 0.43 at 25 against Opus's 0.67 (measured, above).
   - Next, cheapest first:
     - AP with the union of three DeepSeek samples (0.64 at ~38 picks);
     - a selector that reads one file at a time and unions its picks;
     - two stages: DeepSeek proposes, then ranks.
   - Opus picks are the deployable fallback.
2. **Combine AP with a solo rep.** AP_i ∪ DX_i is 0.36 against solo run twice at 0.19. That costs two
   sessions a PR.
3. **Test out of sample** on the fresh set: 40 validation-window PRs that no design has touched, 75
   agreed asks on 34 of them, and 6 no-ask PRs as controls.
   - First, build its reviewed workspaces: 39 of 40 are missing, about 6-7 hours of CPU and 110 GB.
   - Then AP against solo, three reps, by the rule in `deployable-reviewer-review-2026-10.md` §4.
4. **Keep the per-place engine as the high-recall option,** if extra volume is acceptable. Its cheaper
   forms need a fidelity test first, because as specified it costs about 1,000 calls a PR.

## Decisions for you

- **Is AP's narrow yield miss acceptable?** 0.295 against 0.309 asks a finding, for +2.2 findings a
  PR. Or should the next AP variant tighten the section, for example the top 10 picks rather than 25?
- **Building the fresh set's workspaces:** 6-7 hours of CPU and 110 GB.
- **The per-place engine:** pursue it as a high-volume generator, or set it aside until adjudication
  says whether unasked departures are welcome?

## Where it all is (branch `conventions-dossiers`)

- **Stage AP:**
  - `results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md`, "Stage AP" and
    "Result AP";
  - stage D (DP) in the same file.
- **The ladder:** `results/pr_review_v5/probes/conventions-ladder-2026-10-08/README.md`, "Result".
- **The places test and the engine simulation:**
  `results/pr_review_v5/probes/conventions-places-2026-10-09/README.md`.
- **Why the ceiling is not 100%:** `docs/research/ceiling-residual-2026-10.md`.
- **The three adversarial rounds:**
  - `docs/research/conventions-dossiers-review-2026-10.md`;
  - `docs/research/decompose-and-shrink-review-2026-10.md`;
  - `docs/research/deployable-reviewer-review-2026-10.md`.
- **The code-review systems survey,** revisited today: `docs/research/code-review-systems-survey-2026-09.md`.
