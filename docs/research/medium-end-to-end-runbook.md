# Medium end-to-end evaluation: what the number means and how to produce it

*Rewritten 2026-08-06 for the v9 judge and the merged-ensemble architecture. The previous
version of this document gave a judge command that ran the rubric with an empty
`## REVIEWED CODE` section — see §7. Read §1 before quoting any number produced here.*

---

## 1. This is a developmental measurement, not a confirmatory one

The architecture below was designed **after** inspecting medium's targets, control
behaviour, executor output and adjudication split. Pre-registration does not undo that.
Everything medium produces is labelled **developmental**, and generalisation claims are
reserved for an untouched slice or the temporal holdout.

Two further limits that travel with every number:

- **Gold provenance is weak.** 31 of 33 medium judgments are `migration_proposal` —
  machine-migrated, not human-confirmed; 28 are `presumed_atomic`. Reviewer generation is
  gold-free and may proceed while gold is confirmed, but **pair construction, judge spending
  and every headline report wait for confirmed gold.**
- **n = 40.** One flipped obligation is 2.5pp. Medium can support a set-disjointness claim
  between the arms; it cannot support a recall difference below ~5pp.

---

## 2. The set and the two output tiers

16 PRs (13 intervention, 3 control), 225 work units, 40 included obligations.

Every finding carries an **admission tier**:

| tier | deterministic arm | holistic arm | used for |
|---|---|---|---|
| `published` | adjudicated `request` | passes the evidence gate | **the system's output** — headline recall, silent-PR emission |
| `diagnostic` | everything else | everything else | detection ceiling, arm complementarity |

Only `published` is ever called system output. Expect and report honestly: the holistic
published tier is structurally near-empty for naming, documentation and scope, because
`evidence.py` has no collector that can support those claims — 53% of the corpus. That
asymmetry is a result, not a gate to loosen.

## 3. Metrics, named for what they measure

| metric | definition |
|---|---|
| **issue recall** | obligations with ≥1 final finding the judge calls the same issue |
| **resolution recall** | obligations where a finding also satisfies the resolution criteria |
| **gold-alignment rate** | issue-matching findings / all findings on evaluated PRs. **Not precision** — gold is a lower bound (the holistic arm found a real `extenal` typo in 3/3 runs that is not in gold), so an unaligned finding is not wrong. Precision requires human adjudication. |
| **silent-PR emission rate** | findings emitted on the 3 control PRs. **Not a false-finding rate** — zero maintainer interventions is a ledger fact, but calling an emission *invented* is a judgement only human review can make. |
| **candidate-negative match rate** | judge match rate on same-PR near negatives. **Not a false-positive rate** until those pairs carry human labels — a near pair may be a genuine match, which is why widening exists. |

**Anchor pairing is the headline. Widened pairing is exploratory**, reported separately.
Measured on the pilot, widening takes obligations reached from 6 to 14 — but it can only
raise recall, so it is not quotable until its candidate-negative rate is characterised.

Three repetitions, reported as mean / union / stable-at-≥2-of-3. Repetitions are **separate
deployed systems**; union is a capability diagnostic, never merged before scoring.

## 4. Conditions

Run independently, then select: `checker_only`, `holistic_only`, `merged_ensemble`.
Selection uses only what exists at selection time — gold alignment, silent-PR emission,
merge losses, cost, failure rate. Human validity applies to the *selected* condition.

**`checker_only` is already done, free, and needs no model calls:**

```bash
./ape/bin/python -m src.datasets.pr_review_v4.conditions \
  --condition checker_only \
  --execution-release inputs/pr_review_v4/releases/dev-medium-0.2.1-systematic \
  --exclude-methods naming_contrast.v1 \
  --out results/pr_review_v4/conditions/medium-checker-only-v2
```

Result: **37 published findings across 10 PRs, 0 on any control**, 39 inputs, 0 conflicts.
By concern: correctness 31, naming 5, style 1. By evidence: 14 verified-compile, 5
repository-measurement, 20 lexical-rule.

`--exclude-methods naming_contrast.v1` is required and load-bearing. Without it the two
naming implementations request the same renames in different words (`Metric.card_x` versus
`card_x`); the merge refuses to collapse them — canonical equality is case and whitespace
only, deliberately — and reports 3 conflicts, demoting 6 genuine renames to diagnostic.
Both stay in the registry because Phase 9's lineage was produced with the narrow one; a
*condition* declares which methods it runs.

## 5. The reviewer arm (the only significant spend)

Cost anchor: **$0.079 per work unit** on the 0.9.0 pilot, same model and tool set. 225 units
≈ **$18–35 per repetition**, so **~$55–105 for three**.

```bash
for REP in 1 2 3; do
  ./ape/bin/python -m src.datasets.pr_review_v4.runner \
    --config configs/pr_review_v4_medium.yaml \
    --dataset.dry_run false \
    --dataset.run_name pr_review_v4_medium_010_rep${REP} \
    --dataset.output_file results/pr_review_v4/runs/dev-medium-0.1.0-rep${REP}/candidate_responses.jsonl
done
```

Then candidates (free), then the condition:

```bash
./ape/bin/python -m src.datasets.pr_review_v4.candidates \
  --work-units inputs/pr_review_v4/releases/dev-medium-0.1.0/derived/work_units.jsonl \
  --responses results/pr_review_v4/runs/dev-medium-0.1.0-rep${REP}/candidate_responses.jsonl \
  --out results/pr_review_v4/runs/dev-medium-0.1.0-rep${REP}/candidates.jsonl
```

## 6. Judging — after gold is confirmed

**`judge_runner --config` is the only path that spends money on a judge.** The old
`semantic_judge` CLI no longer judges; it reports over a supplied `matches.jsonl`.

```bash
./ape/bin/python -m src.datasets.pr_review_v4.judge_runner \
  --config configs/pr_review_v4_judge.yaml \
  --dataset.dry_run true       # renders every prompt; hard-fails if any lacks its code
```

Judge budget is no longer "a few dollars": pairs are over final findings (fewer than
candidates) but widened and null pairs multiply them. Set the pair cap and cost ceiling
before spending.

## 7. What changed, and why the previous version was unsafe

- **The old §5c command ran the v8 rubric with no reviewed code.** `judge_pairs` never
  passed the change graph, so `## REVIEWED CODE` rendered as
  `(reviewed code unavailable for this target)` — v7.1 behaviour under a v8 label — and the
  code was not in the cache key, so code-less and code-bearing verdicts collided. That path
  is deleted, not fixed.
- **Rubric v9** adds an `abstain` verdict; ablations change judge *identity* rather than
  minting rubric versions; verdicts are typed tool parameters (`bool("false")` was `True`).
- **Coverage is checkable.** Planned pairs are sealed with their prompt hash and reconciled
  exactly against returned verdicts; an incomplete set withholds every recall instead of
  silently scoring a failed pair as a miss.
- **Contracts are split.** `GenerationPlanV2` is gold-free and structurally enforced;
  `EvaluationProtocol` carries gold, judge config and the metric list, fixed before judging.

---

## 8. Order of work

1. Confirm medium gold (human time; parallelises with everything below).
2. `checker_only` — **done**, free.
3. Reviewer ×3 — the spend.
4. `holistic_only` and `merged_ensemble` conditions — free.
5. Judge, after gold is confirmed; then report mean / union / stable with §1 and §3 attached.
