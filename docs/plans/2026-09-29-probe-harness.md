# Plan: one probe harness for the reviewer-model experiment, on three sets (2026-09-29)

**Status: built and run, 2026-09-29.** Steps 1-5 are in `src/mathlib_review/analysis/probes.py` and `cli probe`, each held to the post-cutoff set's committed artifacts by `tests/mathlib_review/test_probes.py`. Validation small12 and dev ran as planned; the dev set is 15 PRs (33057 has no reviewed workspace). The results are in `docs/todo/reviewer-model-gap.md`, "The experiment on three sets".

**Why.** Every reviewer-model result rests on one set, `probe-2026-07-08-v1`: 6 PRs and 16 asks.
The user asked for the same experiment on the dev set, validation small12 and that post-cutoff set.
The procedure is in `docs/todo/reviewer-model-gap.md`. Its scripts hard-code one set, its feedback
files live only in scratch, and the Claude sessions were launched by hand.

## The sets

| set | PRs | asks | Claude sessions | what the harness must add |
|---|---|---|---|---|
| `probe-2026-07-08-v1` (post-cutoff) | 10 | 16 agreed, committed ids | X1, X2 on all 10 | nothing; it is the regression target |
| validation small12 (`val-2025-06-2026-03-v1`) | 11 buildable | 30 agreed (60-PR audit readers) | X1-X4 on 3 PRs | 16 sessions on the other 8 PRs, and G runs |
| dev (`dev-medium-0.3.0`) | 16 | none yet | none | feedback by PR list, two readers, 32 sessions, G runs |

## The build, one commit each

1. **The set spec and feedback.** A spec per set in `configs/probe_sets/` names its release, dataset
   config, PRs, feedback source (a sealed draw, or a PR list for the dev set), comment-id prefix, asks
   file and probe directory. `analysis/probes.py` extracts round-1 feedback from either source; the
   code is the extractor the val1000 and post-cutoff probes used. Test: the post-cutoff re-extraction
   equals the committed copy.
2. **Readers and asks.** The reader batch, and the agreed-ask manifest from two label files. Test: it
   reproduces the committed post-cutoff manifest and families from the committed labels.
3. **Packets and the session prompt.** The brief, the PR text, the diff, the pass-0 model and the
   logging `ptool`, plus the exact reviewer prompt used so far. Test: the post-cutoff X1 packets are
   byte-identical to the committed ones, apart from `ptool`'s scratch paths.
4. **Matching.** The inputs from any mix of Claude sessions, solo runs and lead runs, under a seal.
   The generic unblinding gives per-session reach, per-condition means, stable asks and the per-ask
   table. Test: the committed test (b) and arms reach reproduce from the committed matches.
5. **`cli probe`.** One subcommand per step: `feedback`, `reader-batch`, `asks`, `packets`,
   `prompt`, `match-inputs`, `unblind`.

The historical probe scripts under `results/` are the record of what ran, and they stay as they are.

## Then the runs

- **Validation small12:** packets and 16 Claude sessions on the 8 PRs without any, and two G runs at
  about $0.6 each. Matching uses its 30 asks with X, G and the existing lead run.
- **Dev:** feedback, two readers, packets, 32 sessions, two G runs, then matching.
- **High effort** (about $20 a run) is not in this plan; the user decides on it.

**Leakage, stated.** Only the post-cutoff set is unseen by Claude. `gpt_5.2`'s training cutoff is not
recorded here, and it is stated before any comparison on 2025 PRs.

## Reasoning on, all three sets (launched 2026-09-30): the hand-off

The user approved one high-effort run per set and warned that the session may disconnect. The runs are
detached, so they survive the session ending:

| set | run | config |
|---|---|---|
| post-cutoff | `probe_postcutoff_gpt52_Gr_rep1` | `pr_review_v5_probe_2026_07_08_v1_gpt52_Gr.yaml` |
| validation small12 | `probe_val_small12_gpt52_Gr_rep1` | `pr_review_v5_val_small12_gpt52_Gr.yaml` |
| dev | `probe_dev_gpt52_Gr_rep1` | `pr_review_v5_dev_medium_gpt52_Gr.yaml` |

Logs are in `.ape/probe_scratch/reasoning/<run>.log`, which is linked and persistent. Each set's
README holds its reading rule, stated before the run.

**To finish, from the repo root with `PYTHONPATH=$PWD:$PWD/src`:**
1. **Check each run.** `grep 'Total Cost' .ape/probe_scratch/reasoning/<run>.log` should appear. A
   session that stopped at a cap shows `paused_cost_limit` or `paused_max_turns` in its `sample.json`.
   Raise that cap in the config and rerun the same command with `--resume`. A run killed before it
   wrote outputs also resumes with `--resume`.
2. **Commit** `results/pr_review_v5/runs/<run>/` before building any matcher input.
3. **For each set:**
   - write `sources_reasoning.json`: the set's `sources.json` less L, plus
     `"Gr1": {"kind": "solo", "run": "<run>"}`;
   - `cli probe seal --set configs/probe_sets/<set>.yaml --sessions X1 X2 G1 G2 Gr1 --out <probe_dir>/blinding_reasoning_SEALED.json`;
   - `cli probe match-inputs ... --seal <that> --sources <probe_dir>/sources_reasoning.json --out <scratch>/<set>-reasoning`.
     It prints each matcher's folder and prompt;
   - run two blind matchers with those prompts, and audit each (`cli probe audit`);
   - copy `matches.{1,2}.json` and `session_stats.json` into `<probe_dir>/match_reasoning/`;
   - run `cli probe unblind`, and apply the README's rule.
4. **Write the results** into each README and the three-set table in `docs/todo/reviewer-model-gap.md`.

**Hand-off completed 2026-09-30** in a resumed session: all three runs committed, matched, unblinded and written up (`docs/todo/reviewer-model-gap.md`, "Reasoning on, all three sets").
