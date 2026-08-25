# Precedent retrieval for merge-readiness review — design

*2026-07-02, v0.1. Motivating diagnosis: every selection design so far (selectors, centrality,
NL-distillation, guidelines, focused checkers) drew on the artifact, the model's prior, or abstract
rules — and all plateaued at the same wall. Maintainer judgment is case law, not statute: the
guidelines (statute) were a null; concrete precedent (case law) is the untested source. The observed
recognition–generation asymmetry — agents recognize expert judgment as more correct when shown it,
but cannot generate it — says the evaluative capacity exists and the missing piece is *which
principle is active here*, which is exactly what a retrieved precedent supplies.*

## 1. The unit of retrieval — not PRs, review situations

"How do we tell two PRs are similar?" is the wrong question, deliberately: PR-level similarity is
too coarse (a measure-theory PR can contain the naming precedent that applies to an algebra PR) and
too sparse (few PRs are similar as wholes). The retrieval unit is the **review situation**:

> one maintainer comment + the code it was anchored to (the declaration/hunk, its path, namespace),
> + thread metadata (author, date, whether the thread resolved / led to a change).

The query is likewise not a PR but a **site**: one changed declaration (statement + proof) with
light context (namespace, file, imports), or — in selection mode — a candidate finding on that site.

## 2. What "similar" means — a hypothesis to test, not assume

The real question a precedent must answer: *would the principle behind comment P fire on site Q?*
Candidate similarity axes, with hypotheses about which concerns they serve:

| axis | signal | likely serves |
|---|---|---|
| proof/code shape | tactic patterns (calc-of-≤ chains, `simpa using`, match arms, induction), proof length, decl kind (iff-lemma, simp-lemma, instance) | golf / idiom (V2) |
| library domain | namespace root, typeclass heads, imports | naming, which-lemma-exists, domain idiom |
| statement semantics | NL distillation of what the declaration says (infra exists: `PRDistillation`) | generality, duplication |
| comment semantics | embedding of the comment text itself | selection mode (B): "is this *kind* of comment made?" |

Working hypothesis: **similarity is concern-conditional** — golf precedents transfer by proof
*shape*, naming precedents by *namespace + declaration kind*, generality by *statement semantics* —
so a single generic embedder is the baseline to beat, not the design. We do not settle this by
intuition; Stage 1 settles it by benchmark.

## 3. The lucky asset: our gold doubles as a retrieval benchmark

We hold 115 anchored, actionable maintainer findings. Each is a ready-made retrieval test case:
**query with the gold finding's site (code only, comment hidden), and ask whether the retrieved
precedents "predict" the hidden comment.** This lets us choose the similarity design *offline*, for
a few tens of dollars, before wiring anything into an agent — and it directly measures the
**precedent-coverage ceiling**: for what fraction of real maintainer findings does a transferable
precedent even exist in the corpus? If that number is low, the case-law hypothesis is wrong and we
learn it before the build, not after.

## 4. Two usage modes (build A first)

- **Mode A — precedent-primed generation.** Before reviewing a site, retrieve top-k precedents for
  it and put them in the checker/agent context ("maintainers have said these things on similar
  code"). Hypothesis: biases discovery toward what maintainers actually flag and suppresses the
  valid-but-never-flagged flood — attacking selection at generation time, where a post-hoc filter
  failed.
- **Mode B — precedent-based selection with base rates.** For a candidate finding, retrieve both
  precedents (similar site, similar comment) and **anti-precedents** (similar sites in reviewed,
  merged PRs that drew *no* comment), and estimate an empirical flag-rate P(flag | pattern).
  This is the statistically honest model of maintainer *selectivity* (underreporting is a policy:
  what they spend author goodwill on). Requires the corpus to include full PR diffs (uncommented
  hunks), not just commented ones — collect them in Stage 0 so B stays open. B is gated on A.

Both modes end with the model in **recognition mode** (its demonstrated strength): reranking
retrieved precedents ("which of these genuinely bear on this site?") and applying one ("does this
precedent's principle yield a finding here?"). Nothing asks it to generate judgment from nothing.

## 5. Retrieval architecture (two-stage, boring on purpose)

1. **Recall (cheap, k≈50–100):** dense embedding of the site (raw code hunk; separately, its NL
   distillation) + sparse/feature filters (namespace root, decl kind, tactic multiset from
   `lean_parser`/regex). Union of retrievers.
2. **Rerank (LLM, recognition mode):** "here is site Q and 50 precedent comments with their code —
   which genuinely bear on Q?" → top 3–5 with one-line rationales.
3. **Delivery:** top precedents (comment + its code + what changed) into the agent prompt (mode A)
   or the selection judge (mode B).

## 6. Corpus (Stage 0)

> **Status (built):** `src/datasets/pr_review_v2/corpus.py` collects the commented-situation rows
> (Mode A). It streams the repo-level `/repos/leanprover-community/mathlib4/pulls/comments` endpoint
> (each comment carries its `diff_hunk` natively), keeps substantive **maintainer** comments
> (`author_association ∈ {MEMBER, OWNER, COLLABORATOR}` — which also drops author self-comments,
> non-bot, `.lean`, non-trivial via the reused `derive` hygiene), over a created-at window that ends
> before the eval window, and excludes the 138 eval PRs outright. One paginated pass, resumable.
> Run: `python -m src.datasets.pr_review_v2.corpus --start 2024-03-01 --end 2025-08-31`.
> **Deferred (Stage 0b, gated with Mode B):** per-PR full diffs / uncommented hunks for
> anti-precedents — not needed for Mode A, which is built first.


- **Source:** mathlib4 PR review comments, **cutoff strictly before the eval window** (eval PRs are
  Sept–Dec 2025; corpus ends before the earliest eval PR; the 138 eval PRs excluded outright).
- **Recency matters more than volume:** Mathlib idiom drifts fast (`grw` barely existed before
  mid-2025 — a 2023 precedent cannot recommend it). Start with the trailing ~12–18 months
  (~10–20k PRs → est. 30–80k human review comments), recency-weight at rerank.
- **Row:** comment body, `diff_hunk` (GitHub review comments carry their anchored hunk natively —
  no repo checkout needed for v1), path, line, commenter, date, thread-resolved flag, PR number /
  title / author; plus per-PR full diff (for Mode B anti-precedents).
- **Hygiene:** bot filter, author-self-comment filter, `.lean`-only (all already in
  `src/datasets/pr_review/collector.py`); actionability classification applied lazily at rerank
  time (cheap) rather than over the whole corpus.
- **Storage:** JSONL + chroma index (embedding infra exists under `ape/toolkits/retrieve/`).

## 7. Experimental ladder with gates

> **Status (built):** `src/datasets/pr_review_v2/precedent_bench.py` (queries → retrieve → report)
> + `precedent_judge.py` (LLM hit@k). Query builder run: **109** gold findings have resolvable
> anchored site code (V2=50, V3=46, V4=4, +12 non-V), drawn drift-proof from `gold.delta_total` via
> each comment's `linked_hunks`. Retrievers: `lexical` (BM25, no API), `lexical+feature` (namespace/
> decl-kind boost), `dense_code` (local all-MiniLM-L6-v2, no API). Judge returns hit / same_concern /
> unrelated (three-way, so misses split into "no predictive precedent" vs "same-concern-but-doesn't-
> transfer"). API-free pipeline validated end-to-end on synthetic corpus; awaiting the real corpus
> (Stage 0 fetch) to run for signal. Run order once corpus lands:
> `precedent_bench queries` → `precedent_bench retrieve --design {lexical,lexical+feature,dense_code}`
> → `precedent_judge --retrieved ...` → `precedent_bench report`.

**Stage 1 — similarity benchmark (offline; the design-chooser and go/no-go).**
Queries: the 115 gold sites (comment hidden). For each retrieval design — (a) dense-code,
(b) dense-NL-distill, (c) feature/lexical, (d) hybrids — retrieve top-10 and score
**precedent-hit@k**: an LLM judge answers "does precedent P raise the same kind of concern, and
would applying its principle to Q's code lead to (roughly) the hidden comment's ask?" Report per
stratum (expect V2 and V3 to prefer different designs).
*Cost:* embedding ~50k hunks ≈ negligible; judging ≈ 115 × 10 × 4 designs mini-calls ≈ $10–30.
*Gate:* best design ≥ ~40% hit@10 → strong go (case law transfers). ~20–40% → go, expect partial
coverage. < ~15–20% → the hypothesis fails or the corpus is too small/stale; stop before agent work.
*(Also read the failures: they tell us whether misses are "no precedent exists" vs "retrieval
couldn't find it" — different fixes.)*

**Stage 2 — precedent-primed checkers (Mode A, on the first-20).**
Wire the Stage-1 winner into golf + idiom (+ holistic) prompts; rerun the first-20 and score with
the frozen v6 metric. Baselines already exist from this week's runs (golf 6/31 V2, idiom 4/31,
union 7/31). *Success:* matched recall and/or on-target rate move materially; also watch
finding-count (precedents should *focus*, not add flood).

**Stage 3 — flag-rate priors (Mode B).** Only if Stages 1–2 pass: for each candidate finding,
estimate P(flag | pattern) from precedents vs anti-precedents; use as the selection prior the
pointwise selectors lacked. This is the principled version of everything the selector line tried.

## 8. Risks, named

- **Precedent sparsity / idiosyncrasy** — the central risk; measured directly by Stage 1 before
  any build-out.
- **Thin context**: `diff_hunk` is a few lines; may under-specify the situation. Mitigation:
  two-stage — fetch full file context only for reranked candidates.
- **Temporal drift** of conventions — recency window + date-weighting (above).
- **Contamination**: the model may have memorized mathlib GitHub; retrieval neither fixes nor
  worsens this, and it applies equally to all our baselines.
- **Comment ≠ full judgment** (underreporting): precedents inherit the same bias — they model
  *what maintainers say*, which is exactly the target (match expert *comments*), so this is
  acceptable for A; Mode B's base rates partially model the underreporting policy itself.

## 9. Deliberately not doing

- PR-level similarity; fine-tuning/training a reranker (LLM rerank first); building retrieval into
  dup/gen before Stage 1 says which similarity works; collecting all 30k+ PRs up front (recency
  window first, extend if Stage 1 wants more coverage).
