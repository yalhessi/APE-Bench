# R0 runbook — judge equivalence (script arm vs registered task)

*Built 2026-08-05. Everything below is validated offline; the three `judge_runner`
invocations are the only steps that spend money.*

## What R0 decides

The judge was migrated from a standalone script (own LLM client, own JSON file cache) to
a registered task run through the orchestrator. R0 answers whether that migration **moves
any numbers**, and whether `sample_count: 3` removes the known 2-of-3 verdict flip on
byte-identical inputs (~4pp at n=8 denominators).

Until R0 passes, no number may be quoted from the task arm — it blocks every downstream
comparison in the roadmap.

## Why this is cheap

The target is the 0.9.0 stable smoke, whose **18 pairs (3 reps × 6) already have cached
script verdicts** under `data/pr_review_v4/cache/semantic_judge`. Verified: 18/18
comparable. So R0 pays only for the task arm — 18 pairs × 3 samples = **54 judgments** on
`gpt_5_mini`, capped at `sample_max_cost: 0.10` each.

## Already verified offline (no calls)

- Both arms share `JUDGE_VERSION` and the **identical rubric string**.
- The task arm renders a **byte-identical prompt** to the script arm — so R0 compares
  judges, not prompts.
- The task record's identity fields are exactly what the script's cache key hashes, so
  the two arms join pair-for-pair; a different model yields a different key.
- Verdict parsing is identical across arms, including the fenced-JSON and regex-salvage
  paths and the `resolution ⇒ issue` clamp.
- Majority voting resolves a 2-of-3 split and records `issue_votes` / `unanimous`.
- 264 tests pass; frozen ledger clean.

## Run it

From the repo root. Each command flips `dry_run` off and points at one repetition's
candidates; the run name is the resume key, so re-running a command continues rather than
restarts.

```bash
# rep 1
./ape/bin/python -m src.mathlib_review.judge.runner \
  --config configs/pr_review_v4_judge.yaml dataset.dry_run=False

# rep 2
./ape/bin/python -m src.mathlib_review.judge.runner \
  --config configs/pr_review_v4_judge.yaml dataset.dry_run=False \
  dataset.candidates=results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3-rep2/candidates.jsonl \
  dataset.out_dir=results/pr_review_v4/audits/r0-judge-equivalence/task-arm-rep2 \
  dataset.run_name=pr_review_v4_judge_r0_rep2

# rep 3
./ape/bin/python -m src.mathlib_review.judge.runner \
  --config configs/pr_review_v4_judge.yaml dataset.dry_run=False \
  dataset.candidates=results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3-rep3/candidates.jsonl \
  dataset.out_dir=results/pr_review_v4/audits/r0-judge-equivalence/task-arm-rep3 \
  dataset.run_name=pr_review_v4_judge_r0_rep3
```

Then score each repetition (free, no calls):

```bash
for rep in 1 2 3; do
  suffix=""; [ $rep -gt 1 ] && suffix="-rep$rep"
  ./ape/bin/python -m src.mathlib_review.judge.r0_equivalence \
    --release inputs/pr_review_v4/releases/dev-pilot-0.9.0 \
    --candidates results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3$suffix/candidates.jsonl \
    --task-arm results/pr_review_v4/audits/r0-judge-equivalence/task-arm-rep$rep \
    --out results/pr_review_v4/audits/r0-judge-equivalence/report-rep$rep.json
done
```

(For rep 1 the candidates path has no suffix — that is what the `suffix` variable handles.)

Finally reseal the ledger, since R0 adds artifacts under a frozen root:

```bash
./ape/bin/python -m src.mathlib_review.release.verify_frozen build-lock
./ape/bin/python -m pytest tests -q
```

## Gates

The comparator prints a `decision` and per-gate pass flags:

| Gate | Requirement | Why |
|---|---|---|
| `agreement` | ≥95% of pairs get identical `issue_match` and `resolution_match` | below this the arms are different judges, and downstream deltas would measure the migration |
| `no_split_votes` | zero pairs split their 3 votes | this is the flip the migration exists to remove; a split pair is a measured disagreement, not noise to average away |
| `coverage` | every pair comparable in both arms | a missing verdict silently shrinks the denominator |

`decision: judge_migration_equivalent` means the task arm may replace the script arm.

## If a gate fails

- **Agreement below threshold** — do *not* adopt the task arm. Inspect
  `disagreements[]` in the report: each row carries both verdicts and the cache key.
  Because the prompts are byte-identical, disagreement is judge sampling variance, which
  is itself the R0 finding and should be reported as the flip rate rather than repaired.
- **Split votes present** — the flip survives voting at n=3. Report the split count; the
  fix is more samples, not a prompt change, and every downstream denominator must budget
  for it.
- **Coverage short** — a pair lacks a cached script verdict. Re-run the script arm for
  that pair first (`python -m src.mathlib_review.judge.semantic_judge …`), or the
  comparison is not apples-to-apples.

## After R0 passes

The script arm stays in place as the frozen historical producer; nothing that was
measured with it gets re-scored. New measurements use the task arm, and the hand-rolled
cache directory can stop growing. Update the roadmap's R0 row and record the observed
flip rate — it is the number every future n=8-scale comparison must be read against.
