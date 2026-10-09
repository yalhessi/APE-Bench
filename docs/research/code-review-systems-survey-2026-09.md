# Code-review systems: what their designs offer this one

*2026-09-15. Primary sources read for every system below (papers, engineering posts, released
prompts); vendor-reported numbers are marked as such. Companion to
`open-code-review-comparison-2026-09.md`, which covers OCR and AACR-Bench in depth. Each borrowable
item was checked against `dead-ends.md` and, where it could be done for nothing, against our own
committed runs.*

## The systems

| System | Kind | Pipeline shape | Measured result (source) |
|---|---|---|---|
| **BitsAI-CR** (ByteDance, FSE'25) | deployed, 12k WAU | 219-rule taxonomy → fine-tuned RuleChecker → ReviewFilter (binary) → embedding dedup | precision 57.0% → 65.6% with the filter; **no taxonomy 16.8%**; conclusion-first filter 77.1% vs reasoning-first 65.8%; Outdated Rate 26.7% vs human 35–46% ([arXiv 2501.15134](https://arxiv.org/abs/2501.15134)) |
| **AutoCommenter** (Google, AIware'24) | deployed, tens of thousands daily | T5 trained on ~800k human comments that cite a best-practice URL; predicts location + URL + confidence | per-URL thresholds (80% of predictions under the global 0.98 were correct); suppressing 17+5 URLs raised useful 54% → 66% (devs), 60% → 74% (raters); ~40% resolved ([arXiv 2405.13565](https://arxiv.org/abs/2405.13565)) |
| **RovoDev Code Reviewer** (Atlassian, ICSE'26) | deployed, 4k engineers, 54k comments | guideline-conditioned generation → LLM factual judge → ModernBERT actionability gate trained on 50k comments labelled by resolution | factual judge **minimal impact**; actionability gate **+15–20pp**; guidelines +5%; resolution 38.7% vs human 44.5%; **only 4% of comments match a human comment in place and intent** ([arXiv 2601.01129](https://arxiv.org/abs/2601.01129)) |
| **HalluJudge** (Atlassian) | method | reference-free grounding check of each claim against the diff | F1 0.85 (ToT); 67% agreement with developer thumbs ([arXiv 2601.19072](https://arxiv.org/abs/2601.19072)) |
| **uReview** (Uber) | deployed, 90% of 65k diffs/week | 3 assistants (bugs, best practices, security) → per-assistant grader with confidence → semantic dedup → category classifier that suppresses low-value categories | 75% rated useful; 65% addressed vs 51% for human comments; best: Sonnet generator + o4-mini grader; addressed-ness decided by **re-running the reviewer 5× on the final commit** ([Uber blog](https://www.uber.com/us/en/blog/ureview/)) |
| **Bugbot** (Cursor) | deployed, 2M PRs/month | v1: 8 parallel passes, randomized diff order → bucket → majority vote → validator → dedup against prior runs; later fully agentic | resolution rate 52% → 70%, resolved bugs/PR 0.2 → 0.5 over 40 experiments; biggest gain the agentic switch, which needed **"aggressive" prompts after restraint made it too cautious** ([Cursor blog](https://cursor.com/blog/building-bugbot)) |
| **Codex reviewer** (OpenAI) | deployed, 100k PRs/day | trained reviewer, repo access + execution | precision-first by an explicit expected-utility rule; "the reward model you train on is not the reviewer you should ship"; 52.7% of comments lead to changes ([OpenAI alignment blog](https://alignment.openai.com/scaling-code-verification/)) |
| **Code Review** (Anthropic) | product | parallel bug-finding agents → verification → severity ranking | <1% of findings marked incorrect; substantive comments on 54% of PRs vs 16% (vendor, [claude.com](https://claude.com/blog/code-review)) |
| **code-review plugin** (Anthropic, open prompt) | open | 5 Sonnet reviewers (conventions file, bugs, git history, prior PR comments, code comments) → per-issue Haiku scorer on an anchored 0/25/50/75/100 rubric → keep ≥80 | explicit false-positive list: pre-existing, nitpicks, linter-catchable, unmodified lines ([prompt](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/code-review/commands/code-review.md)) |
| **Qodo 2.0** | product | specialist agents → judge agent merges, dedups, filters; a recommendation agent reads past PRs so deliberately accepted patterns are not re-flagged | F1 60.1% on a vendor comparison ([Qodo](https://www.qodo.ai/blog/introducing-qodo-2-0-agentic-code-review/)) |
| **CodeRabbit** | product | review agent → verification agents built with *different* context from the generator | 31k feedback pairs in the wild: 36.4% accepted, 56.3% rejected ([arXiv 2607.03316](https://arxiv.org/abs/2607.03316)) |
| **Greptile v4** | product | learns team preferences from reactions and replies | addressed 30% → 43% (vendor, [Greptile](https://www.greptile.com/blog/greptile-v4)) |
| **Semgrep Assistant** | product (SAST triage) | triage decisions with reasons become scoped "memories" that suppress future false positives | 60% of triage automated, 96% user agreement (vendor, [Semgrep](https://semgrep.dev/blog/2025/announcing-ai-noise-filtering-and-triage-memories/)) |
| **Tricorder** (Google, ICSE'15) / **Infer** (Meta, CACM'19) | static analysis at scale | analyzers in the review tool; "Not useful" button | effective false positive = *anything the user did not want to see*; analyzers above ~10% disabled; Infer's fix rate **>70% at diff time vs near zero** as an assigned-issue list |
| **Code Review Bench** (Martian) | benchmark | offline gold set + online "acted on" tracking | "**The gold set is wrong, and it matters**": comments scored false positive were real issues gold lacked ([post](https://withmartian.com/post/code-review-bench-v0)) |
| **SWR-Bench** | benchmark | 1,000 verified PRs; LLM coverage judge ~90% agreement | multi-review aggregation raises F1 by up to 43.7% ([arXiv 2509.01494](https://arxiv.org/abs/2509.01494)) |
| **CRScore** (NAACL'25) | metric | pseudo-references (claims, smells) from LLMs + static tools; reference-free | 0.54 Spearman with humans ([arXiv 2409.19801](https://arxiv.org/abs/2409.19801)) |
| **ProofJudge** (Caldwell, Aug 2026) | Mathlib | judge with library state scores initial vs maintainer-accepted revision of 218 declarations on 5 dimensions | recovers reviewer preference on 63.5–80.8% of pairs; harness, data and traces released ([arXiv 2608.20432](https://arxiv.org/abs/2608.20432)) |
| **MathlibPR** (May 2026) | Mathlib | PR-level merge-readiness | models and agents cannot separate merge-ready from build-passing PRs ([arXiv 2605.07147](https://arxiv.org/abs/2605.07147)) |

## The convergent design

Nearly every deployed system independently arrived at the same five parts: **specialised
generators → a separate grader/verifier with its own context or model → suppression at the level
of a rule or category, tuned on feedback → dedup → an online "was it acted on" metric.** Ours has
the first, a verifier (the evidence gate), and dedup (merge/digest). It has neither of the last two
parts, and those are the ones the industrial write-ups credit with trust and precision: category-level
calibration from feedback, and an acted-on signal that does not depend on gold.

Where the evidence disagrees, it is informative. A **factual-grounding judge** did little at
Atlassian (minimal impact) while a **value/actionability gate** trained on resolution moved 15–20pp;
uReview likewise gained most from suppressing whole low-value categories. The filters that helped
judge whether a comment is *worth making*, not only whether it is *true*.

## Borrowable, checked against our record

### 1. Cross-run agreement as a selection signal — measured here, provisional

*Precedent:* Bugbot's 8-pass majority vote; SWR-Bench's multi-review aggregation.
*Why it matters here:* `selection-signal.md` records every signal tried as near chance within a PR
(`model_confidence` AUC 0.486–0.516 over 907 candidates; `severity` 0.601 best). This one is
gold-free and costs nothing on runs that already have three reps.
*Measured on the committed held-out runs*, key `(pr, primary_change_id, issue_kind)`, judge-paired
findings only (so a finding's anchor at a gold change is held fixed), agreement counted over the
*other two* reps, hit = judge majority `issue_match`:

| condition | 0 of 2 other reps | 1 of 2 | 2 of 2 | within-PR AUC |
|---|---|---|---|---|
| 0.5.0 (`rel050_rep1-3`) | 7/32 = 0.22 | 7/16 = 0.44 | 50/56 = **0.89** | 0.892 |
| 0.5.0 without 33149 | 4/22 = 0.18 | 1/6 = 0.17 | 14/20 = **0.70** | 0.706 |
| 0.3.0 (`v2_rep1-3`) | 9/26 = 0.35 | 10/19 = 0.53 | 50/84 = **0.60** | 0.783 |
| 0.3.0 without 33149 | 1/14 = 0.07 | 0/7 = 0.00 | 14/48 = **0.29** | 0.631 |

Monotone in all four slices. **Why it is provisional:** outside 33149 the 2-of-2 bucket is 6 and 13
distinct keys covering 3 and 4 distinct obligations; the same obligation contributes correlated
hits; it is in-sample on the twelve PRs whose failure analysis already consumed them; and in
production it costs repeated generation (Bugbot pays 8×). **What would close it:** the same table on
a run set not used to find it — the fresh held-out window — plus the control PR's emission under a
"keep only 2-of-3" rule. Written into `docs/todo/selection-signal.md`.

### 2. "Was it acted on" as a triage signal for off-gold findings — **Δ-framing dead end applies**

*Precedent:* BitsAI's Outdated Rate (flagged lines modified later), RovoDev's resolution rate,
Cursor's LLM-judged resolution at merge, uReview's 5× re-run on the final commit, Martian's online
track. RovoDev's 4%-aligned / 38.7%-resolved gap is external evidence that alignment with human
comments understates usefulness by an order of magnitude — our `gold_alignment_rate` rule, found
independently.
*Constraint:* `dead-ends.md` retired the Δ revealed-preference framing — "authors make the changes,
not maintainers" — **reopens: never as ground truth.** So a resolution signal may only *order the
adjudication queue* (`open-code-review-comparison-2026-09.md` §1), never score. One difference in
our favour: our candidates were never shown to the author, so a site that changed the way a finding
asks was changed independently of it, which industrial resolution rates cannot claim.

### 3. Rule- or category-level calibration and suppression, with a decision rule — after adjudication

*Precedent:* AutoCommenter per-URL thresholds and URL suppression; uReview thresholds per
assistant × language × category; BitsAI decommissions rules that hold precision but whose comments
are not acted on.
*Ours:* `specialist-arm-contents.md` already has the table (`style` 348 candidates, 0 hits). What is
missing is labels: deciding on gold hits alone would suppress categories that are valid and off-gold,
exactly the error Martian and RovoDev warn about. Sequenced after adjudication.

### 4. Verdict order is contested, not settled

BitsAI measured **conclusion-first 77.1% vs reasoning-first 65.8%** filter precision — the opposite of
OCR's replay finding (reasoning must precede the ids). BitsAI's model is fine-tuned and scored on its
first token; OCR's is a frontier model emitting tool arguments. The field-order todo now carries both,
and the decision-turn replay should test both orders rather than assume one.

### 5. A separate scorer on an anchored rubric — **on the dead-end list**

The plugin's 0/25/50/75/100 scorer and uReview's grader are pointwise LLM selectors over the
finding and the code. `dead-ends.md` ("Selection from artifact-only signals") measured pointwise,
listwise and tool-using selectors at chance on V2 and says not to run another on artifact-only
information. An anchored rubric changes the elicitation, not the information, so it does not reopen
the entry. RovoDev's result points the same way: the gate that worked was trained on outcomes.

## Checked and not borrowable

- **Supervision from comments that cite a norm (AutoCommenter).** In the PR-store corpus
  (2024-03 → 2026-08), **709 of 104,093 reviewer comments (0.68%) link a norm source** — style guide
  106, naming 100, docs 45, Zulip 239, library notes 40, linter docs 187 — on 568 PRs. AutoCommenter
  trained on ~800k. Three orders of magnitude short as training data; at most an evaluation slice.
- **Rule taxonomy (BitsAI 16.8% → 57.0%).** The gain is inside a fine-tuned classifier; prompt-side
  guideline injection is null here at N=115 (`dead-ends.md`, "statute") and +5% at Atlassian.
- **Past-PR context to avoid re-flagging accepted patterns (Qodo, Semgrep memories).** This is the
  anti-precedent corpus that `dead-ends.md` names as the reopen condition for flag-rate priors;
  nothing new beyond that entry.
- **The agentic switch with "aggressive" prompts (Bugbot).** Corroborates `forbid_abstention` (arms
  withhold; forcing raised recall 0.20 → 0.50) but adds no mechanism we lack.
- **ProofJudge as a selector.** Its task (original vs accepted revision) is easier than choosing among
  valid candidates, its preference is the Δ framing, and a tool-using selector already measured 0.56
  on V2. Its released 218-pair set and five dimensions (library leverage, automation fit, structural
  clarity, statement quality, conventions) are worth reading as related work and as a vocabulary check
  on our concern families, not as a signal.

## One framing note

Tricorder's definition — a false positive is anything the user did not want to see — is this
project's thesis in static-analysis language: a verified-correct finding a maintainer would not ask
for is, to the maintainer, a false positive. It argues for keeping "valid but not an ask" as its own
label in adjudication rather than folding it into "correct".

## Revisited 2026-10-09: what the systems say about the conventions designs

This survey predates the conventions work: the census, the ceiling probe, the ladder, and the two
adversarial rounds (`docs/research/conventions-dossiers-review-2026-10.md`,
`decompose-and-shrink-review-2026-10.md`, `ceiling-residual-2026-10.md`). Read against them, one
verdict above is out of date, and four lessons bear directly on the designs now under test.

**The rule-taxonomy verdict is out of date.** Above, BitsAI's taxonomy (219 rules, precision
16.8% → 57.0%) was "not borrowable", because guideline injection was null here ("statute", N=115).
That was the right reading of a guide appended to one prompt. Since then, the census gives about 400
rules at the same order of magnitude as BitsAI's 219. Given at the right place, they move strong
reviewers +0.22 to +0.28; dumped as a list, they move nothing (stage F +0.03).

**BitsAI's shape is the per-place engine now under test.** Its shape is taxonomy → a per-rule checker
at a place → a filter. AutoCommenter predicts the place and the rule together. Tricorder runs one
narrow analyzer per rule. The per-place engine is architecture B, tested by
`results/pr_review_v5/probes/conventions-places-2026-10-09/`. The deployed versions differ from ours
in two ways that matter:
- their checkers are trained (BitsAI fine-tuned; AutoCommenter's T5 on ~800k norm-citing comments);
- their precision comes from outcome data at scale.

We prompt, and our outcome data is 1,833 census asks.

**Lesson 1: precision is managed per rule, not by a global filter or a demand predictor.**
- AutoCommenter keeps a confidence threshold per URL: 80% of the predictions under the global
  threshold were correct. Suppressing 22 URLs raised usefulness from 54% to 66%.
- Tricorder disables an analyzer whose "not useful" rate passes about 10%.
- BitsAI decommissions rules that hold precision but whose comments are not acted on.
- Applied here:
  - Stage H's failure (no model predicts which places maintainers raise, AUC 0.56-0.64) does not
    close the volume problem. The deployed answer is coarser: calibrate or switch off each rule by its
    measured record.
  - The places test produces exactly that record: departs rates and confidences per entry, at asked,
    unasked and decoy places.
  - A per-rule policy (threshold, or suppress the noisiest rules) can be simulated on its outputs
    before any end-to-end run.

**Lesson 2: aggregation is the industrial answer to instability, our largest gap component.**
- Bugbot ran 8 passes over a randomised diff order, then a majority vote.
- SWR-Bench's multi-review aggregation raised F1 by up to 43.7%.
- uReview re-runs the reviewer 5× to decide addressed-ness.
- Applied here:
  - A DP session reaches about 25 of 39 in-census asks, its three-rep union 29, and the union over
    models 34 (`ceiling-residual-2026-10.md`).
  - Union over passes buys recall, and agreement across passes ranks for precision. Cross-run
    agreement already measured 0.89 hit rate at 2 of 2 here, in sample (§1 above).
  - For the per-place engine, agreement across samples of one (rule, place) is a gold-free confidence.
    The places test's two samples per exact pair measure it at no extra cost.

**Lesson 3: value gates beat truth gates, and value is learned from outcomes.**
- RovoDev's factual judge did little, while its actionability gate trained on 50k resolutions moved
  15-20pp.
- uReview gained most by suppressing whole low-value categories.
- Applied here:
  - Validity checks (a quoted line, a compile, a lookup) keep filings true but will not make them
    wanted.
  - Our only outcome data is the census: asked situations, and unasked ones that can be mined as stage
    H did.
  - So the nearer-term value gate is per rule (lesson 1), and maybe per area. A learned per-place gate
    needs data we do not have (0.68% of 104,093 reviewer comments cite a norm source; above).

**Lesson 4: decompose by evidence source, not only by code part or convention.**
- Anthropic's open code-review plugin runs reviewers by the source they read: the conventions file,
  bugs, git history, prior PR comments on the touched files, code comments.
- Qodo's recommendation agent reads past PRs so accepted patterns are not re-flagged.
- Applied here: two of the six asks no ceiling session ever reached need exactly that kind of source.
  - v0053 needs the history of PRs #24163 and #21065.
  - p0010 needs the library's `_left`/`_right` orientation (`inf_sup_left`).
- This axis is orthogonal to the decompose-and-shrink lenses, and no design here has tried it.
  A history reviewer differs from precedent priming (Mode A, `dead-ends.md`): it reads one PR's own
  history for facts, not other PRs' comments as examples.

**Two lessons that confirm what the record found:**
- **OCR's grouping cut recall 20.0% → 12.7%** because secondary files starved, silent 68% of the time.
  Their fix gated completion on a pass per file. That is our "at the right place, asked something
  else", and it argues for small units with a verdict per (place, rule).
- **Bugbot needed "aggressive" prompts once restraint made the agent too cautious.** That is DP's
  precedence paragraph, and `forbid_abstention` (0.20 → 0.50).

**Does this re-orient the exploration?** It reinforces the current direction rather than turning it.
- **The convergent industrial design is per-rule checkers, per-rule calibration and aggregation.**
  The places test is the right first measurement for that design.
- **The survey changes what follows the places test**, in three ways:
  - volume control by per-rule calibration and suppression, simulated on the places outputs, before
    any demand predictor;
  - agreement across samples as the confidence signal;
  - an evidence-source axis (history, library analogues) for the residual that no packet carries.
- **Their caution applies too.** The deployed checkers that reach high precision are trained on
  outcome data we lack. A prompted engine may top out lower, and only a run will tell.
