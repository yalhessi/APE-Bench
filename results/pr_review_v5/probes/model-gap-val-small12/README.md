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
