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

---

## Result (2026-09-29): the model gap holds; the structure reading splits across matchers

Four blind matchers, two per seal. All six judges, the readers included, read only their own folders
(`audit_judges.json`). Agreement: seal A 168 of 186 cells (90%), seal B 63 of 64.

| per-session reach | matcher 1 | matcher 2 |
|---|---|---|
| **Claude (X)**, pooled over 47 asks | **0.67** | **0.61** |
| `gpt_5.2` solo (G), pooled | 0.13 | 0.18 |
| `q = G/X` | 0.19 | 0.30 |
| seal A (31 asks): X / G / L | 0.69 / 0.15 / 0.29 | 0.60 / 0.21 / 0.29 |
| `L - G` on seal A | +0.15 | +0.08 |
| L, published findings only | 0.00 | 0.00 |
| without 33149 (42 asks pooled; 26 in A): `q`, `L - G` | 0.13, +0.13 | 0.17, +0.10 |

1. **The model gap:** `q = 0.19` and `0.30`, so **markedly less** by test (b)'s rule on both matchers.
2. **The structure:** `+0.15` and `+0.08`, so **partial**: one matcher over the 0.10 line, one under.
   Without 33149 it is `+0.13` and `+0.10`, adds reach on both. 33149 is an AI-generated PR with
   axioms and bundled asks, which every reviewer reached through its axiom part. The lead runs are the
   record's, on older code and in-sample.

**By family** (matcher 1; reached / session-ask cells):

| family | asks | X | G | L |
|---|---|---|---|---|
| naming (F8) | 14 | 21/28 | 1/28 | 6/20 |
| proof (F1) | 9 | 13/18 | 2/18 | 0/8 |
| F9 | 5 | 7/10 | 0/10 | 1/4 |
| derive (F4) | 4 | 6/8 | 0/8 | 0/8 |
| F6 | 4 | 2/8 | 0/8 | 0/6 |
| documentation (F10) | 4 | 6/8 | 3/8 | 4/4 |
| correctness (CORR) | 2 | 4/4 | 2/4 | 4/4 |
| F5, F12, F7 | 5 | 4/10 | 4/10 | 3/8 |

**What it means, at probe altitude** (12 ask PRs, 47 asks, two runs a condition):
- Claude reaches about two thirds of the dev asks, and `gpt_5.2` whole-PR about a sixth. The gap is
  the widest of the three sets, but Claude's reach here is in its training window and on the set the
  record knows best.
- The lead runs' gain over `gpt_5.2` is naming (6 of 20 cells) and documentation. The naming arm was
  tuned on these PRs, so that gain is in-sample. The gate published none of the lead's hits.

---

## Reasoning on (pre-registered 2026-09-30, before its run)

**The run.** Condition G with `reasoning_effort: high`, one run, `probe_dev_gpt52_Gr_rep1` (`configs/pr_review_v5_dev_medium_gpt52_Gr.yaml`).
The caps are $6.00 and 80 turns a session, so they cannot bind. The calibration session on 43192
billed $3.74 over 43 turns.

**Matching.** A new seal over X1, X2, G1, G2 and Gr1 on the ask PRs (`blinding_reasoning_SEALED.json`,
`sources_reasoning.json`), two new blind matchers, the harness's rubric. X and G are re-judged in the
same pass, so the ratio is computed within one matcher.

**Reading rule**, on both matchers: `q_r = reach(Gr1) / reach(X)`.

| on both matchers | reading |
|---|---|
| `q_r ≥ 0.8` | reasoning closes the model gap on this set |
| `q_r ≤ 0.5` | the gap remains with reasoning on |
| otherwise | partial |

Also read: `reach(Gr1) - reach(G)`, per-family reach, findings per PR, cost per session, and any
capped session (a cap that binds is reported, not hidden). One run, so provisional.
