# The verdict contract, one matched pair (2026-09-23) — provisional

The contract ceiling of `docs/plans/2026-09-23-work-enumeration.md` ("contract first"): the current
specialist briefs, every specialist at every slot, no lead and no generalist, on the four PRs of
the fanout pair (33145, 33315 control, 33337, 33421; ten counted obligations). **One rep per
condition** — the user skipped reps 2–3 to limit spend — so every difference below is inside what
one rep can show (one obligation is 10 pp). The Phase 4 outcome bands were defined over three reps
and are not applied.

| | treatment | control |
|---|---|---|
| run | `pr5_V2_verdicts_fanout4_rep1` | `pr5_V2_verdicts_fanout4_control_rep1` |
| contract | `target_verdicts` + `verify_edits_if_present` | default (abstention, sealed verification policy) |
| issue recall, majority / unanimous | **3/10** / 2/10 | **2/10** / 1/10 |
| jobs filing | 49 of 139 (35%) | 38 of 140 (27%) |
| candidates | 87 | 57 |
| candidates on the control PR 33315 | **0** | 1 |
| resolution recall | 0.10 | 0.10 |
| `gold_alignment_rate` | 0.069 | 0.035 |
| billed | $5.82 | $4.74 |

The two runs share all 140 prompts, arms, caps, model and release, checked on the sealed plans
before any job ran; they differ in the submission contract alone. (The treatment ran on the old
search tools, the control on the grep-prefiltered ones; the tools return identical results, 60 of
60 on the treatment's own queries, so that is a difference in speed, not in what the arms saw.)

Judged v9 / `gpt_5_mini`, three votes, scoped to the four PRs the runs reviewed.

## What each hit was

| obligation | ask | treatment | control |
|---|---|---|---|
| 64e1164f | 33337: rename `coe_…` to `toLinearMap_…` | `naming` | `naming` |
| bd8a8d8c | 33145: derive the inf lemma from the sup one via `OrderDual` | `correctness`, `api_reuse`, `duplication`, `proof_golf` | `proof_golf` |
| e83e6544 | 33145: rename `continuous_upperBounds` → `upperBounds_image` | `naming` | — |

## Reading

- **The contract's measured effect in this pair is one obligation (e83e6544), a filing rate of
  27% → 35%, and 30 more candidates, with no control-PR cost** (1 → 0). That is the direction the
  forcing result predicted without forcing's cost — forced fanout put 36 findings on the same
  control PR — but at n = 1 per condition it is not distinguishable from rep-to-rep variation.
- **The control is itself better than the old fanout it replaces.** With no generalist at all,
  the current specialists reached 2 of 10, what the 2026-09-14 fanout reached *with* a generalist
  on every unit; and `naming` filed the 33337 rename unforced, which in that fanout only the
  generalist ever did. The prompt and tool revisions since `focused-prompt/2` — `naming_norm`'s
  split empty verdict (`b9acfe3`) among them — already moved that silence, so that hit is not the
  contract's.
- **Specialists alone, no generalist, no lead, reach what the generalist-anchored designs
  reached on these PRs.** That is the observation this thread started from turned around, on
  four PRs and one rep each.

## What the pilot read added (before these reps)

`cannot_determine` is never chosen, even where `naming_norm` returned `subject_unresolved`; the arm
answers `no_issue`. It does not move recall, but it is the belief state a scheduler would read, and
the evidence-gap layer of the plan's miss decomposition depends on it. Advisory micro-nits rise
under the contract (`.mpr` → `.2`, `(K := K)`, blank lines between aliases); they are part of the
30 extra candidates and are unadjudicated.

## Open

- **Reps 2–3 of both conditions** (~$5–6 each), the only thing that would make the difference a
  rate. Skipped, not dropped.
- The corpus-derived question list (Phase 1) and its ceiling — the out-of-sample condition —
  untouched.
- A miss decomposition by stage for the seven obligations neither run hit, from the per-target
  verdicts `report buckets` now shows.

**Unified, 2026-09-23.** This treatment ran the verdict tool under unchanged `focused-prompt/4` prompts:
the tool-only condition. The unified code (`docs/plans/2026-09-23-unify-the-contract-branches.md`) also
renders contract text under the same knobs and moves the naming prompt, so a run of it is a new
condition, not rep 2 of this one; reps 2-3 of this treatment are retired as superseded. Two readings
the artifacts support and this write-up omitted: e83e6544 is a judge-vote flip -- the control's naming
arm filed nearly the same rename and drew 1 of 3 votes against 2 of 3 -- so by what the arms filed the
contract gained no obligation; and one treatment job (docs, 33421) paused at $0.18 on its $0.17 cap and
lost its answer while the manifest read `paused: 0`, a counter defect now fixed (`e163523`).
