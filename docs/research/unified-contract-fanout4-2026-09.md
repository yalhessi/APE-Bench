# The unified contract on the four fanout PRs, one rep (2026-09-23) — provisional

The first spend after unifying `work-enumeration` and `arms-speak`
(`docs/plans/2026-09-23-unify-the-contract-branches.md`, Step 3): the verdict contract with its text
rendered, against the control already paid for. Fanout, no generalist, no lead, PRs 33145 / 33315
(control) / 33337 / 33421, ten counted obligations, gpt_5.2; judged v9 / gpt_5_mini, three votes,
judge identity `0711a6c01265` — the same as the V2 pair, same scope. One rep per condition, so one
obligation is 10 pp and every difference below is inside what one rep can show.

| | control | verdicts, tool-only | **unified** |
|---|---|---|---|
| run | `pr5_V2_verdicts_fanout4_control_rep1` | `pr5_V2_verdicts_fanout4_rep1` | `pr5_V3_contract_fanout4_rep1` |
| prompts | `focused-prompt/4` | `focused-prompt/4` | `+ask_without_fix+target_verdicts`, naming bullet corrected |
| obligations hit, majority / unanimous | 2 / 1 | 3 / 2 | **3 / 2** |
| resolution recall | 1 / 10 | 1 / 10 | **2 / 10** |
| findings on control PR 33315 | 1 | 0 | **0** |
| findings | 57 | 87 | 77 |
| billed | $4.74 | $5.82 | $5.60 |

**Against the reading rule fixed before spending — ≥ 5 of 10 with ≤ 1 on the control PR, every new hit
something the arms filed — this is not through.**

## What each obligation came to

By the best vote any finding drew:

| obligation | ask | control | tool-only | unified |
|---|---|---|---|---|
| 64e1164f | 33337: `coe_starProjection…` → `toLinearMap_…` | 3/3 naming | 3/3 naming | 3/3 naming |
| bd8a8d8c | 33145: `Dense.ciSup`/`ciInf`, inf from sup by duality | 2/3 proof_golf | 3/3 correctness | 3/3 api_reuse |
| e83e6544 | 33145: rename both bounds lemmas **and** reprove the lower via `OrderDual` | 1/3 naming | 2/3 naming | 1/3 naming |
| **7fef913e** | 33145: `Dense.ciInf'` via the order dual | 0/3 | 0/3 | **2/3 duplication** |
| the other six | | 0 | 0 | 0 |

- **One filed hit is new**: 7fef913e, `duplication` asking to "replace the proof of
  `Dense.continuous_inf'` with a one-liner using `Dense.continuous_sup'` on `αᵒᵈ`" — an obligation only
  forcing had ever reached. On a split vote, so fragile.
- **e83e6544 is filed in all three runs and split every time**, and the judge's reasons say why: the
  obligation is compound (rename *both* lemmas and reprove one from the other), and each run's naming
  arm filed one rename *per declaration*, which the judge reads as half the ask. This run's naming
  finding was backed by an `established` 27-of-27 prefix count. It is the spans-several-declarations
  shape `docs/plans/2026-09-22-coordinated-emission.md` measured; a per-target contract, if anything,
  pulls asks further toward one declaration each.

## What the misses are

Read from the per-target verdicts at the seven obligations no run hit — every arm answered, so these
are statements, not silences:

- **Design-scale asks nobody's question reaches.** 38e72250 (factor out a `Tendsto (2 * ·)` lemma):
  `api_reuse`, `duplication` and `family_design` each checked whether an existing lemma covers it, and
  none asked whether a new one should be introduced. 55f65304 (generalize to arbitrary `k`):
  `generality` checked typeclass assumptions, not the constant; `family_design` considered it and said
  it is "a special" case. 8d887ce4 / e8e02821 (refactors of `ciSup'`): the arms at the site asked for
  local golfs, a docstring fix and a signature reformat.
- **Naming-evidence limits.** 6b02b611 (`round_eq'` → `round_eq_div`): naming answered `no_issue`
  because the name "still matches the `round_` prefix" — the prefix oracle cannot see a suffix change.
  ce7b5d2e: `naming_norm` returned `insufficient_evidence` with `coe_` still leading.
- **The naming correction changed behaviour where it was aimed.** 23 of 37 `naming_norm` calls returned
  `subject_unresolved`; at the `ciSup'` sites the arm now filed a rename proposal on local precedent
  instead of answering `no_issue`. It still chose `cannot_determine` 0 times in 416 verdicts.

## Reading

The per-target contract, tool-only or with its text, does what it was built to do — every target
answered, filing up (27% → 35%), zero control-PR cost, one more design-scale obligation reached — and
does not move recall past what a vote flip can explain. The residual is not arms withholding: it is
arms asking a smaller or different question at the right site (four of seven), evidence the naming
tool cannot produce (two), and a compound ask filed in halves (one). None of those is a contract
problem.

**Untried, and what this does not rule out:** reasoning on — every gpt-5.2 call in the record ran with
reasoning off (`docs/todo/reasoning-in-the-arms.md`), and "asks a smaller question at the right site"
is a judgement failure a reasoning setting could move; a no-pruning run on the twelve held-out PRs,
where pruning, not silence, loses most obligations (25 of 42 miss-reps); questions that ask for design
moves (introduce a lemma, generalize a constant) — `work-enumeration`'s Phase 1 question list; naming
evidence for suffix and namespace conventions; a compound-ask channel. And a second rep of any of
these three conditions, which is what would turn 3 vs 2 into a rate.

## Operational notes

139 of 140 jobs succeeded; one `correctness` job paused at $0.175 on its $0.17 cap, and the manifest now
counts it (`paused: 1`, fixed in `e163523`). 24 min wall; no API retries. The arm pool is copied into
the main checkout's run directory.
