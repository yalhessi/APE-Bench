# Open todos — the hypotheses worth spending on next

The register of work this project has decided is worth doing and has not done. It sits beside the
other three records and answers a question none of them answers:

| Record | Answers |
|---|---|
| `docs/PROJECT-STATUS.md` | what exists |
| `docs/plans/STATUS.md` | what a plan asked for, and whether it got built |
| `docs/dead-ends.md` | what was tried and stopped, and what would reopen it |
| **`docs/todo/`** | **what is open, why we believe it is worth doing, and what would close it** |

## The rule that makes this file worth keeping

**Every todo carries the motivating example that made us interested in it** — a measured result, a
named PR, a run path, a line of code. A todo with no motivating example is a wish, and wishes are
how this project has previously spent money on the wrong thing. If you cannot name the observation
that made the item interesting, it does not go in.

A todo is *not* a plan. Plans live in `docs/plans/<date>-*.md` and are kept verbatim. A todo is the
one-screen case for doing the work at all; when a todo grows a design, it gets a plan and this entry
links to it.

## How to use it

- **Before proposing a direction:** read this index and `docs/dead-ends.md`. If the direction is
  already here, pick it up rather than restating it; if it is in `dead-ends.md`, say so and cite the
  entry.
- **When a session surfaces a new hypothesis it will not pursue:** write it here before the session
  ends. Compaction drops what only exists in conversation, and this project has re-derived the same
  idea in three separate sessions.
- **When a todo is closed:** move it to `docs/dead-ends.md` if it was tried and stopped, or strike it
  here with the commit that closed it. Do not silently delete an entry — the reason it was open is
  part of the record.
- **One file per todo** in this directory, named `<area>-<slug>.md`; this file is the index and is
  the only place the list lives.

## Entry format

```markdown
# <title>

**Status** — open / in progress / blocked on <what>
**Cost** — an estimate in dollars of billed spend, or "no spend"
**Motivating example** — the measurement, PR, or line of code that made this interesting
**What would close it** — the concrete check, not a direction of travel
**Evidence** — file:line, run paths, commit hashes
**Risk** — what makes this possibly not worth doing
```

---

## The list

Written 2026-09-14 from an evidence sweep over the tree and the committed run artifacts. Every claim
below was gathered by one pass and then re-measured by an adversarial second pass; where the two
disagreed, the entry carries the corrected number and says what was refuted. Nothing here is costed
above "one rep" without a measurement behind it.

| Todo | The motivating result | Cost |
|---|---|---|
| [Work-unit batching](batching-work-units.md) | PR 33145's six-theorem family is split across 4 work units by a **sha256 sort and a double-counted 24,000-char budget** — the packer charges one 5,196-char hunk 12 times when the renderer prints it once. Repacking on real content: **203 units → 92**. 41 of 62 families span >1 unit; 22 of 32 required family-grain jobs hold part of their family. `patch_set` has never been submitted in **1,660 recorded candidates** and would raise TypeError on first use. | code + 1 rerun |
| [Specialist arm contents](specialist-arm-contents.md) | **Seven** of ten specialists match nothing, for three different reasons — `style` 126 findings / 0 published / 0 matches; `family_design` 26 invocations / 0 candidates; `api_reuse` 107 proposals / **0 mandatory rows** / 0 invocations. `naming_norm`'s `established` bar needs ratio ≥ 0.80 while 33337's gold prefix is **21 of 121**. `docs` is told a linter settles a check that is not in the toolset. | mostly re-scoring |
| [Lead prompt cost](lead-prompt-cost.md) | `### Exact changed fragments` is **43.6%** of rendered prompt characters and **61.8%** of prompt spend, and **95.5% of it is a verbatim re-send**. PR 33149 is **48% of the run's billed cost**: one 17,303-char hunk shipped to 120 jobs that each review one 163-char declaration. Target-scoping it removes 89.9% of the section and **16% of lead spend**. | code + 1 rep |
| [The judge and the denominators](judge-and-measurement.md) | The judge has only ever paired at `anchor` — **705 of 705 pairs, no other tier ever emitted** — so an ask anchored one change away is never shown to it. The active v9 rubric splits its own vote on **76 of 705** pairs, against a v8 result of 0/18 that does not carry forward. PR 33149 is **68.9%** of condition A's findings. | no spend |
| [Evidence tiers and traces](evidence-tiers-and-traces.md) | `repository_measurement` is declared in the schema and **produced by no v5 code path**, so "27 of 27 lemmas use this prefix" serialises exactly like a guess. Two collectors can only ever return `inconclusive`. `proof_profile` writes **no trace row at all** while gating condition C's leak audit. | no spend |
| [Selection signal](selection-signal.md) | **Refuted in its absolute form**, which is what the 2026-09-14 plan proposed: at 10× the data — 907 candidates, 71 hit-candidates — within-PR AUC is **0.486 / 0.485 / 0.516**. The forced-run frontier is one PR (drop 33145 → AUC 0.511). Kept because the **relative within-PR** form is recorded as working and was never tested here. | no spend |
| [Parked corpora](parked-corpora.md) | A **30,297-row** A→B ledger whose only importer is a test, with a clean `grind` curve countable in it. The Zulip benchmark's 45% unresolved rate is **exhaustively** two build parameters. The precedent gate's 49%/56% was measured on embeddings the bench builds itself, **never on the shipped index**. | no spend |
| [Record corrections](record-corrections.md) | Three `dead-ends.md` clauses assert mechanisms the artifacts contradict — including the 33145 decline, where `naming` **did** run at the gold site and filed both renames. Every conclusion survives; the causes do not. | no spend |
| [Operational floor](operational-floor.md) | An **aborted** fanout run sits untracked under a resumable name with a sealed plan — a resume would seal onto a retired design at ~$111. The acceptance report fails on **one unexplained row**. | no spend |
| [Billed as the only spend number](cost-accounting-billed-only.md) | Across 52 v5 manifests the field named `total_cost` sums to **$283.53** against a true billed **$84.23**, at a per-run ratio of **2.06×–3.38×** — so **69 of 820 run pairs (8.4%) are ordered differently by nominal than by billed**. Nominal is still what the live progress line labels `Cost:`, what `Already spent:` prints beside a billed cap, and what reaches `report["cost"]` and `score["cost"]`. | no spend |

### Reading order

The four no-spend measurement items — judge pairing tier, judge noise, the 33149 denominator, and
the evidence tiers — change what every recall number in the record *means*, and all four are cheaper
than any run. Anything scheduled before they land will be read against denominators that are known
to be wrong in a known direction.

[Billed as the only spend number](cost-accounting-billed-only.md) is the same argument on the cost
axis: until it lands, a cost figure in the record does not say which currency it is in, and the two
currencies do not even rank the same runs in the same order.
