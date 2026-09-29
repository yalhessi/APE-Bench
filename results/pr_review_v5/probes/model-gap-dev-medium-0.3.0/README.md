# The reviewer-model probe on the dev set (2026-09-29)

The post-cutoff probe's experiment on the dev set, through the harness
(`configs/probe_sets/dev_medium_0_3_0.yaml`, `docs/plans/2026-09-29-probe-harness.md`).

**The set.** `dev-medium-0.3.0`: 16 PRs created 2025-12-18..31, less 33057, whose reviewed code does
not build on its base. So 15 PRs, of which 33304, 33315 and 33438 have no round-1 feedback.
- **Every v5 design was tuned on these PRs**, so the pipeline's figures here are in-sample.
- **They are inside Claude's training window.**
- The asks come from two new blind readers on the 51 round-1 comments (`feedback.json`, the
  post-cutoff rubric). Only asks both readers agree on count. The validation audit's single auditor
  labelled the same comments once (`arm-coverage-val-…/families.json`, `dev`); that labelling is a
  cross-check, not the asks.

**Conditions:**

| label | what | runs |
|---|---|---|
| X1, X2 | Claude (`claude-opus-5-5`), the control brief, packet and tools | 2 |
| G1, G2 | `gpt_5.2` solo, reasoning off, the same brief and pass-0 model (`probe_dev_gpt52_G_rep{1,2}`) | 2 |
| L1, L2 | the pipeline in lead mode, as measured on the held-out 12: `pr5_A_lead_heldout12_v2_rep{1,2}`, all channels | 2 |

The lead runs are the record's, on older review code. They cover 12 of the 15 PRs; 33066, 33098 and
33438 are outside the held-out 12.

**Matching.** Two seals, because a matcher's rubric fixes the reviewer count per PR:
- seal A: six reviewers (X, G and L) on the ask-bearing PRs inside the held-out 12;
- seal B: four reviewers (X and G) on the ask-bearing PRs outside it.

Each seal has two blind matchers.

## Reading rule, stated before the asks exist

Per-session reach is asks reached over asks, on each matcher.
1. **The model gap** is `q = reach(G) / reach(X)`, pooled over both seals. The thresholds are test
   (b)'s: `≤ 0.5` markedly less, `≥ 0.8` comparable, otherwise inconclusive.
2. **The structure** is `reach(L) - reach(G)` on seal A's PRs, with validation's thresholds:
   `≥ 0.10` adds reach, `≤ 0.03` adds nothing. It is in-sample and on older code, so it is read as
   the record's pipeline against the model it ran on, not as a test of the current one.

**Also read:** reach by family, published-only reach for L, and findings per PR.
