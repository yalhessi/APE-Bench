# What the two plans asked for, and what is built

*Checked against the tree at `dc894b1` on `september-checkpoint`, 2026-09-08. 1295 tests pass.*

Two plans are in this directory and the second is the first one's remainder, reordered:

* [`2026-09-06-ape-native-review-system.md`](2026-09-06-ape-native-review-system.md) — the
  original. Four stages, keyed to the four problems named in the request: the pipeline fits
  poorly into APE, one experiment touches too many files, the pieces were designed without
  each other in mind, and subagent management is fragile.
* [`2026-09-07-remaining-work.md`](2026-09-07-remaining-work.md) — written partway through,
  once Stage 0 and Stage 3 had largely landed. Six steps, ordered by what unblocks what.

Where they disagree the later one wins. Where it is silent the original still stands.

**Status is per numbered item, and only three values are used.** *Built* means it is in the
tree with tests. *Not built* means no part of it exists. *Partial* means some of it exists and
the entry says which part, because "partial" without that is how a plan stops being a record
of anything.

---

## Original plan, Stage 0 — the framework primitive and the accounting

| # | Item | Status |
|---|---|---|
| 1 | `TaskOutcome / SampleOutcome / AttemptOutcome` | **Built** |
| 2 | `paused` ≠ `partial` | **Built** |
| 3 | `UsageBreakdown` — self/nested/inclusive × nominal/billed/charged | **Built** |
| 4 | Cumulative billed cost across samples and attempts | **Built** |
| 5 | Per-child usage, not tier totals | **Built** |
| 6 | Atomic reservations before parallel dispatch | **Built** |
| 7 | Per-spec execution limits, replacing tier-grouped orchestrators | **Built** |
| 8 | Hierarchical budget scopes including run-total | **Built** |
| 9 | Root inclusive usage counted once via `nested_token_usage` | **Built** |
| 10 | Failure reasons propagate to rows, reports, manifests | **Built** |
| 11 | Mandatory failure ⇒ coverage gap ⇒ `partial` | **Built** |
| 12 | Run transitions written as an explicit state machine | **Partial** — every transition the plan names is enforced somewhere (`execution_status`, `completion_status`, the judge's refusal to score a non-complete run), but there is no single place that states the machine, so the guarantee is assembled from three files rather than read off one. |
| 13 | Lead state as an append-only event journal | **Built** |
| 14 | `execution_index.jsonl` mapping semantic ids to physical paths | **Built** |
| 15 | Isolation contract, stated and tested | **Built** |
| 16 | Kill the prompt redundancy | **Built** — 32% of the arm prompt |
| 17 | Two one-line bugs | **Built** |

`UsageBreakdown` found the live version of the problem it was written for: the manifest reported
`total_cost`, which is *nominal*, while every cap binds billed spend — roughly 2.5× apart.

Correction sidecars for the September runs: **built**. Those runs are forensic fixtures.

## Original plan, Stage 1 — one entrypoint, strict config

| Item | Status |
|---|---|
| One entrypoint with `plan / run / judge / bench / report / trajectory` | **Partial** — it is `python -m src.mathlib_review.review.cli`, not `ape review`, and there is no `resume` or `build-corpus` subcommand. `finalize` runs inside `run` rather than standing alone. |
| Mutating commands read-only without `--execute` | **Built**, with a structural test that every spending subcommand has the gate and no read-only one does |
| Pure preflight must not instantiate `TaskOrchestrator` | **Built** — the dry-run branch returns at `runner.py:799`, the orchestrator is constructed at `:862` |
| Overrides only via repeated `--set key=value` | **Not built** — overrides are bare `key=value` trailing arguments. The half that mattered *is* built: `parse_cli_args` raises on a token without `=` instead of discarding it, which is the bug that made a checked-in runbook command run the wrong experiment. |
| `extends:` with cycle detection | **Built** |
| `extra="forbid"` recursively | **Built** |
| Resume monotonic in execution only, `run_plan_revision_N` | **Built** — spending fields may move, a semantic change is refused and names the field |
| `judge --run` derives all paths | **Built**, spelled `--of`. The v5 judge configs now carry no paths at all, so the three cannot disagree. The live rep1/rep2 mismatch the plan cites is gone. |
| `evaluation_contract_version` | **Built**, starting at 2 |
| Comment-invariants become preflight | **Built** — coverage reachable when the floor is off, the evidence gate announcing itself, and `execution_release`/`skip_evidence_chain`/`pr_finding_limit`/`generalist_floor` sealed in the plan |
| Reusable templates; delete the configs naming spent runs | **Partial** — every v5 config extends a base and states only its deltas (18 keys → 2 for `medium_heldout`), and four spent one-offs are deleted. Four configs still name an already-spent run: `smoke4`, `smoke4_e2e`, `heldout11_rep2`, `specialist4`. Those are the reusable sets rather than one-offs, and `guard_run_name` refuses them fatally, so they are inert rather than dangerous — but the run name is still baked into the config, which is the shape of the problem. |

## Original plan, Stage 2 — the collapse, the arm split, the coordinator

| # | Item | Status |
|---|---|---|
| 1 | Split the 2,187-line schema by **lifecycle** | **Built** — 9 modules, façade deleted |
| 2 | Move the live v2 modules; delete v2, `v4/legacy/`, one-off scripts | **Partial** — the two v2 functions v5 reached for (`corpus._eval_pr_numbers`, `precedent_bench.hunk_code`) moved, and v5→v2 is zero. **v2 itself is untouched**: 34 dataset modules and 12 task modules. `v4/legacy/` and the seven `phase*` drivers were *moved*, to `legacy_pipeline/`, not deleted — their artifacts are still load-bearing. |
| 3 | Merge into `src/mathlib_review/`; `ReviewArmTask` / `ReviewLeadTask`; discovery-based registration | **Partial** — the merge is done and both old packages are deleted. The task classes keep their names (`LeanPRReviewV5ArmTask`, `LeanPRReviewV5LeadTask`) and still register through explicit `register_task(...)` calls. |
| 4 | `ArmCatalog` + `Coordinator`-driven dispatch replacing the pre-rendered pool | **Partial** — the catalog exists as `agenda/registry.py` and is the single declaration of an arm. Dispatch is unchanged: the agenda pool is still pre-rendered and written to `arm_pool.jsonl`. |
| 5 | Split the arms into `arms/<arm>/` behind `ArmRuntime` | **Not built** — deliberately. See below. |
| 6 | Separate `SynthesisPolicy` from `Coordinator`, sealed independently | **Built** |
| 7 | De-duplicate the drifted constants | **Built** |
| 8 | Boundary tests | **Built**, and they now assert zero rather than a budget |
| 9 | Delete `lead.py`'s dead `floor_summary` / `_floor_block` | **Not built** — and still live: `LEAD_USER` contains no `floor_block` placeholder, so `_floor_block()` is computed each time and passed to a `.format()` that silently ignores it. |

## Original plan, Stage 3 — admission channels, provenance, reachability

| # | Item | Status |
|---|---|---|
| 1 | Two channels, `review` and `verified`; contradiction is not a veto | **Built** |
| 2 | Provenance replaces the concern gate | **Built**, in the order the plan required: drops are retained as `diagnostic` findings *first*, then the gate came out. Removing it in the other order would have turned a loud rejection into a silent one. |
| 3 | Reachability predeclared, hashed, evaluation-only | **Built** |
| 4 | Judging consumes final serialized findings | **Built** |
| 5 | No broad new style/documentation checkers | **Held** — none added |

## Updated plan — the six steps

| Step | Status |
|---|---|
| 1 — `TaskExecutionSpec`, `spawn_subtasks`, retire budget tiers | **Built**. `judgment` and `review_gate` migrated onto it and their tests still pass, which was the plan's own test of whether it is a primitive or a fourth convention. |
| 2 — run-total scope, `UsageBreakdown`, lead journal, `execution_index.jsonl` | **Built** |
| 3 — dual admission channels | **Built** |
| 4 — provenance instead of a concern gate | **Built** |
| 5 — Stage 1 remainder | **Partial** — see the Stage 1 table. Outstanding: `--set`, `resume`/`build-corpus` subcommands, four configs naming spent runs. |
| 6 — the collapse | **Partial** — v4 and v5 are one package, both old ones deleted, backward edges zero. `ArmRuntime` and the arm split are not built; v2 is not deleted. |

---

## What is deliberately not built

**`ArmRuntime` and `arms/<arm>/`.** The seam separates what an arm decides (its question, its
tools, its search) from what the runtime enforces (anchoring, confinement, budget). Building it
now would add a hook layer with exactly one implementation, and this codebase already records
what that costs: `migration_consistency` sat in `PATCH_SET_ARMS` before it had a spec or a
prompt, and `code_references` sat in `SUPPORTED_TOOLS` with its registration commented out —
"a capability granted to nothing, readable as coverage that is not there." The seam is worth
building when there is a second arm strategy to put through it, which is the per-arm literature
work the plan itself puts outside its own scope.

**Deleting v2.** Its data pipeline built inputs still in use — the precedent corpus, the eval
set, the roster. The plan says delete it; nothing in the tree needs that yet, and doing it
carelessly would break the release chain.

**The package merge did not need to de-duplicate anything.** A scan for structurally identical
function bodies across all three generations found exactly two, and one was `load_run` (three
byte-identical copies, now one). This is worth writing down because it was the reasoning that
nearly stopped the merge halfway: the merge was never about duplicated code, it was about one
concept living in several places, which is true whether or not any function appears twice.

## What the work turned up that neither plan asked for

* **`code_references` was granted to nothing.** No registration, and yet 24 configs enabled it
  and — the part that did harm — the `api_reuse` arm's prompt named it in the sentence telling
  the arm how to search before making a claim.
* **The retrieval gate disagreed with itself.** Four sources each parsed timestamps their own
  way; `precedent_index` returned epoch 0 on a parse failure, which is before every cutoff, so
  an undated row was eligible for *every* review. Latent on today's corpus (34,640 rows, none
  undated), fixed regardless.
* **Retrieval is effectively one tool.** Across 2,024 calls in 13 runs: `declaration_search`
  83% (47% empty), `precedent_search` 12% (0% empty, because a dense top-k never abstains),
  `zulip_search` 5% (80% empty, an open question). Re-run with `report retrieval`.
* **The local-vs-design claim is not supported.** `obligation_scope` was written to test it and
  nothing could call it; wired up, design recall equals or exceeds local in every run with hits.
  Small n, and two of four runs predate the accounting repair.
* **No temporal leak in any recorded run** — all 2,024 retrieval calls carry their `as_of`.

## The next thing

Neither plan's remainder is what stands between this branch and a result. The pipeline is
verified end to end offline — all four live configs seal, finalization replays over a real
run's arm responses, the judge parses what finalization writes — and every September run is a
forensic fixture. What is missing is **one complete run to read**, which the original plan
names as the new reference baseline.
