# The reviewer-model probe on validation small12 (2026-09-29)

The post-cutoff probe's experiment (`../gpt52-postcutoff-2026-09-29/README.md`, tests (b) and the arms
condition) on a second set, through the harness (`src/mathlib_review/analysis/probes.py`,
`configs/probe_sets/val_small12.yaml`, `docs/plans/2026-09-29-probe-harness.md`).

**The set.** `val-2025-06-2026-03-v1` small12 less 30714, whose base does not build: 11 PRs created
2025-06..2026-03. There are 30 asks on 8 PRs, from the 60-PR audit's two readers agreeing, with the
auditor's families (`asks.json`). The controls, with no agreed ask, are 26185, 32080 and 34935.
**Inside Claude's training window**: Claude may have seen these PRs and their comments. Test (a)
found Claude's reach there is not mainly recall.

**Conditions**, one sealed matching (`blinding_SEALED.json`, `sources.json`), five reviewers a PR:

| label | what | runs |
|---|---|---|
| X1, X2 | Claude (`claude-opus-5-5`), the control brief, packet and tools. New sessions on 8 PRs; the construction demonstration's X1, X2 on 30458, 32875, 34091 | 2 |
| G1, G2 | `gpt_5.2` solo, reasoning off, the same brief and pass-0 model (`probe_val_small12_gpt52_G_rep{1,2}`) | 2 |
| L1 | the pipeline in lead mode, `gpt_5.2` (`pr5_val_small12_minus30714_lead_rep1`, all channels) | 1 |

## Reading rule, stated before any matcher runs

Per-session reach is asks `reached` over asks, on each of two blind matchers.

1. **The model gap**, test (b)'s rule: `q = reach(G) / reach(X)`.

   | on both matchers | reading |
   |---|---|
   | `q ≤ 0.5` | markedly less |
   | `q ≥ 0.8` | comparable |
   | otherwise | inconclusive at this size |

2. **The structure**, `reach(L1) - reach(G)`.

   | on both matchers | reading |
   |---|---|
   | `≥ 0.10` | the structure adds reach on this set |
   | `≤ 0.03` | it adds nothing |
   | otherwise | partial |

   One lead run only, so this reading is provisional.

**Also read:** reach on families F1-F7 (the post-cutoff set's pass-3/4 scope), the lead's
published-only reach, findings per PR, and whether the post-cutoff per-ask pattern recurs: X reaching
design and convention asks that G and L miss.

---

## Result (2026-09-29): the model gap replicates; here the structure adds reach, on proof asks

Two blind matchers, 150 cells. They read only their own folders and agree on 147 reached-or-not and
144 three-valued (`match/`, `unblinded.json`).

| per-session reach, 30 asks | matcher 1 | matcher 2 |
|---|---|---|
| **Claude (X)** | **0.48** | **0.50** |
| `gpt_5.2` solo, reasoning off (G) | 0.13 | 0.13 |
| the pipeline, lead mode (L1) | 0.27 | 0.27 |
| the pipeline, published findings only | 0.03 | 0.07 |
| on families F1-F7 (20 asks): X / G / L | 0.55 / 0.05 / 0.20 | 0.53 / 0.05 / 0.20 |

1. **The model gap:** `q = 0.28` and `0.27`, so **markedly less** by the rule. That is the post-cutoff
   set's figure (0.27) on a different set of asks, and here in Claude's training window.
2. **The structure:** `L1 - G = +0.13` on both matchers, so **it adds reach on this set** (provisional,
   one lead run). The lead run's 0.27 is the 8 of 30 the validation probe found for the same run.

**By family** (matcher 1; reached / session-ask cells):

| family | asks | X | G | L1 |
|---|---|---|---|---|
| proof (F1) | 11 | 12/22 | 0/22 | 4/11 |
| interface (F2) | 5 | 6/10 | 2/10 | 0/5 |
| registration (F3) | 4 | 4/8 | 0/8 | 0/4 |
| naming (F8) | 2 | 1/4 | 0/4 | 0/2 |
| documentation (F10) | 5 | 4/10 | 6/10 | 4/5 |
| PR level (F12) | 3 | 2/6 | 0/6 | 0/3 |

**What it means, at probe altitude** (8 PRs, 30 asks, two runs of X and G, one of L):
- Claude reaches about half of the maintainers' asks. `gpt_5.2` whole-PR reaches about an eighth,
  and the pipeline about a quarter. That is the post-cutoff ordering, with the pipeline higher here.
- The pipeline's gain over its own model run whole-PR is proof asks: 4 of 11 against none, the
  proof-golf and proof-idiom arms' remit. On the post-cutoff set the asks were mostly naming and
  design, and there the structure added nothing. So the structure's value depends on the ask mix, and
  on neither set does it touch interface, registration, naming or PR-level asks.
- `gpt_5.2` whole-PR does best on documentation asks (6 of 10); Claude's lead is everywhere else.
- The gate published almost none of the pipeline's hits (0.03-0.07 against 0.27).

**Caveats:** inside Claude's training window; one lead run; 8 PRs. Findings per session per PR:
X 5.4, G 1.9, L 5.1.
