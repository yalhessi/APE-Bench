*Appendix to [`../pipeline-overfit-2026-09.md`](../pipeline-overfit-2026-09.md), written by a read-only sweep agent in that session and kept as it reported. Re-verified by the auditor: the lead's four-arm list (`prompts.py:117-126`), the census row shape (`census.py:229-239`), the tool-description examples at `base.py:481` and `context_tools.py:180, 617`, and the shipped docstrings at `lead.py:57, 118, 187`. Line numbers are for `01ceae7`. The in-process `list_tools()` collection and the gate probes ran from that session's scratch and are not kept.*

# Part 2: dev-specific content in model-visible text (v5 pipeline)

Audited on the worktree `pipeline-overfit-review` at `01ceae7` (develop `2098546` plus one todo
commit). Read-only. Nothing was edited or run that spends money. Line numbers are for this tree.

## How this was done

- I read every prompt constant, contract text, tool description and tool-output template on the
  default v5 path.
- I collected the **served** tool schemas by registering every tool on a real `fastmcp.FastMCP`
  and calling `list_tools()` in memory, with no model involved. The scaffold forwards
  `tool.inputSchema` verbatim (`src/ape/scaffolds/ape_agent/conversation.py:1460-1463`), so what
  `list_tools` returns is what the model reads. That includes nested `$defs`, which carry pydantic
  class docstrings.
- I ran `contracts.prompt_leaks` over all 96 collected surfaces against the 1,128 gold strings in
  the dev releases. It found **nothing on any surface**, including the ones the gate never sweeps;
  §b explains why.
- Provenance comes from `git log -S … -- src`, commit bodies, the comment beside each text, and
  dev gold (`dev-medium-0.5.0/gold/judgments.jsonl`). Much of the text arrived in two squashes,
  `70b1961` (v2 import, 2026-08-25) and `3828243` (v5 checkpoint, 2026-09-07). Where a commit says
  nothing, the provenance is marked **inferred** and the evidence for the inference is given.
- For a weak test of whether an idiom generalises, I counted lexical mentions in the
  **validation** PRs' reviewer comments (`reviewer_view.jsonl`, non-author, the 60 val PR numbers
  only). That gives 276 comments across 41 PRs, all rounds. These are mentions, not asks. The test
  set was not touched.

### What is actually reachable in a default run

The validation configs extend `bases/v5_generation.yaml`, which uses `routing_mode: lead`, the
`baseline` procedure variant and both contract knobs off. The generalist prompt is
`candidate-prompt/14` (425 of 425 val prompts).

| Surface | Reached by default? |
|---|---|
| Arm system prompts (`focused_prompts.py` via `render_focused.focused_system_prompt`) plus SUBMISSION_CONTRACT, LEGACY_ABSTENTION_PARAGRAPH, and PATCH_SET_CLAUSE for 7 arms | yes |
| Arm **user** prompt: targets + `FACET_CHECKLIST_ONCE` + context slice (`render_focused.py:281-292`) | yes |
| v2 user templates `GOLF_USER` … `GEN_USER`, and v5 `NAMING_USER` … `FAMILY_DESIGN_USER` | **no**. v5 builds its own user prompt. The v2 four are used only by the frozen `pr_review_v2` tasks. |
| Rung supplements 3a/3b/3c/3d (`focused_prompts.py:593-736`) | **no**. Reachable only through `analysis/bench_cli.py --procedure-variant`. No run config or `review.cli` path sets a variant. |
| ASK_WITHOUT_FIX_CLAUSE, TARGET_SECTIONS, VERDICTS_ABSTENTION_PARAGRAPH, verdict-tool schema | only under `target_verdicts` / `verify_edits_if_present` (fanout4 configs) |
| Generalist: `SYSTEM_PROMPT_V12` (system, **and again in the user message** at /14) + checklist + context slice | yes |
| Lead: LEAD_SYSTEM / LEAD_USER, the tools `read_agenda` / `submit_comprehension` / `delegate` / `submit_routing` / `lean_verify_edit`, and their schemas | yes |
| **Registry `rationale` strings** | **not model-visible in a default lead run.** `read_agenda` returns census rows (`census.py:229-239`): arm ids, proposal ids, signals. No rationale, no `eligible`, no `routing_priority`. The rationale reaches a model only through `read_agenda`'s no-census fallback (`lead.py:423-427`), which default runs never take. So the rationale re-cuts are inert as text; they act through `extra_subject_kinds` and `expected_concerns`, which are Part 3 knobs. |
| Context tools: the generalist holds **all five** (`zulip, precedent, declaration, proof_profile, naming_norm`). Specialists hold their registry grant. | yes. Checked on `pr5_F_fanout_heldout12_v2_rep1/arm_pool.jsonl`: generalist ×203 with all five. So `proof_profile`'s and `naming_norm`'s descriptions reach the generalist in every run, although its prompt never mentions them. |
| Solo (`solo.py`) | solo configs only |

---

## (a) Items, by surface

The Kind column uses these codes:

| Code | Meaning |
|---|---|
| **W** | worked example quoting dev data |
| **L** | named tactic / lemma / idiom list drawn from dev (or v2-window) gold |
| **R** | remit re-cut around one dev obligation |
| **S** | statistic measured on dev |
| **F** | instruction written to fix one dev failure |
| **U** | unclear / contradictory / unbacked (not dev-specific) |

### a1. Arm system prompts (`src/ape/tasks/lean_tasks/formal_math/review/focused_prompts.py`)

| file:line | quoted text | kind | provenance | generalise or keep |
|---|---|---|---|---|
| 381-382 (naming) | "of 121 declarations whose conclusion is about `toLinearMap`, 21 use `toLinearMap_` and 7 use `coe_`" | **W** | PR 33337. Added in `4d655e8` (2026-09-13). The body says: "On 33337 … `toLinearMap_` 21 to 7". **Confirmed.** It is also an `emerging` case (17% modal share), so the one example of "a finding" is a plurality the tool calls advisory at most. | **Generalise:** "“This name could be clearer” is not a finding. “naming_norm: of N declarations whose conclusion is about `‹subject›`, K use `‹p›_`, verdict `established`” is." Use placeholders and no real subject. Coordinate with `naming-from-statement` (below). |
| 352-356 (naming) | "The convention that governs a name is the one for the subject its CONCLUSION is about … not the handful of lemmas that happen to sit beside it … a file can be the last corner using a spelling the library has moved away from" | **F** | 33337. In `4d655e8`: "silence in 13 of 13 reps … it read the local family, found `coe_`". The general rule rests on one PR. For 33337's other lemma the census preferred `coe_` 48 vs 9 (`19ef236`). | **Generalise:** keep "measure across the repository", but drop the absolute. For example: "Read siblings and the repository-wide count; where they disagree, say so and weigh both." Validation: 34906's reviewer quotes a repository-wide count ("'namespace [a-z].*' occurs 414 times") and 26210's asks for consistency with the local name. Both kinds occur. |
| 350 (naming) | "`encard_le_encard`, `isOpen_iUnion`, `Finset.sum_comm`" | **W** (mild) | `encard_` is 33098's requested prefix (3 gold renames). In `70b1961` the same list carried `Dense.upperBounds_image`, 33145's gold, which was later removed as a leak (`test_prompt_contamination.py:3-6`). **Inferred:** chosen from dev vocabulary in the same pass. | **Generalise:** replace `encard_le_encard` with a lemma from an unrelated area (e.g. `Finset.card_le_card`, `mul_le_mul_left`). Low risk, since it is a real Mathlib lemma (`Set.encard_le_encard`). |
| 368-370 (naming) | "Whatever the verdict, it is about the name's LEADING prefix only. The tool does not measure a suffix, a prime, argument order or a namespace" | F | 33421 `round_eq'` and the 33337 `coe_` plurality (`adcc7ba`) | **Keep.** It describes the tool truthfully and in general terms. |
| 371-373 (naming) | "A past rename request is the strongest evidence available about what will be asked here" | U (contradiction) | Written with `4d655e8` | **Generalise.** `precedent_search`'s own description (`context_tools.py:196-205`) says "EXPERIMENTAL … results are often about something else … including its own author". Suggested: "A past rename request on a genuinely similar declaration is strong evidence; most precedent hits are not similar, so read each one." |
| 397-398, 400 (docs) | "The first is the one maintainers ask for most and the one that is least often noticed." | **S** | Docs is "3 of 43 gold obligations release-wide" (`routing.py:58`). The COMPLETE item rests on 33321's two obligations. | **Delete the frequency claim.** Keep the order as a reading order only. |
| 401-403 (docs) | "A sentence that stops mid-thought: 'When the index set is finite this reduces to the …' … (This example is invented…)" | W (sanitised) | 33321's gold sentence was here verbatim and was caught by the gate (`test_prompt_contamination.py:3-6`). The replacement keeps the shape of that one obligation. | **Keep the check, trim it.** "A sentence that does not finish" is general. The invented example is fine. |
| 404-407 (docs) | "If a proof needs a construction a reader would not predict — an auxiliary ordering, a detour through a dual — the module or declaration doc should have an 'Implementation details' note" | **R/W** | 33321, obligation 3: "adding an 'Implementation details' discussion" about "the need for an ordered coefficient set". "An auxiliary ordering" paraphrases that gold. The "dual" is 33145. First seen in `3828243`. **Inferred from gold text.** Validation: "Implementation details/notes" appears in 0 of 276 reviewer comments. | **Generalise:** "A non-obvious design choice with no explanation where a reader would look for one (module doc or docstring)." Drop the "Implementation details" heading and both examples. |
| 411-413 (docs) | "a misspelled word inside an otherwise fluent sentence is exactly what skimming misses" | F | 33066 ("isometry"→"isometric") and 33321 ("crystallogrphic") typos | **Keep.** It is general and cheap. |
| 418-420 (docs) | "Over-long lines and malformed markup. The repository's own linter settles these, so they are cheap to be right about" | R + **U (unbacked)** | 33305 (wrap an over-long module-doc line). No lint tool is granted (`specialist-arm-contents.md:65-73`). The roadmap measured that "Mathlib runs these linters in CI, so mechanically-detectable style violations are already gone" (`pr-review-next-iteration-roadmap.md:92-101`). | **Generalise:** either grant `lint_policy.find_long_lines` as a tool, or say "You have no linter. Report a line-length or markup defect only when you can quote the line." Validation does have docstring-conformance asks the prompt never names: 29511 "don't indent subsequent lines in doc-strings" and 30641 "use filenames not import paths in docstrings". Name conformance generically, as "docstring formatting conventions (indentation, file references, markup)". |
| 422-424 (docs) | "only 8% of theorems and 67% of definitions do" | S (Mathlib-wide) | Measured on the Mathlib snapshot, not dev (`roadmap:85`, `evidence/verifiers.py:155`) | **Keep.** It is a corpus fact, but it contradicts the generalist's "documentation_gap when documentation is absent" and solo's docstring example (§c). |
| 439-446 (style) | "Blank lines around `section`, `namespace`, and `variable` boundaries … `calc` block alignment … Line length … Where `variable` declarations sit" | **L/R** | Each bullet maps to a smoke4 / medium style obligation. 33066: "Insert a blank line after `section auxiliaryDefs` and move the subsequent `variable`". 33098: calc first line. 33305: line length. The arms block comment says so (`focused_prompts.py:327-331`: "gold asked for … section formatting"). **Inferred per bullet.** Validation: calc 0 mentions; namespace 9 comments / 5 PRs. | **Generalise.** Remove "Line length" (see the CI finding above). Replace the list with "the conventions the surrounding file follows consistently (binders, layout, attribute and `variable` placement, where declarations sit relative to `namespace`/`section`)". Put **namespace placement** into this prompt: today it exists only in the invisible registry rationale, and validation has 4 PRs with namespace asks (26484 "shouldn't put everything in the root namespace", 32080 "`section` → `namespace`", 31079 "wrong namespace", 34906). |
| 28-32 (golf) | "Asking the author to golf or simplify a proof is the single most common substantive comment Mathlib maintainers make" | **S** | v2 text (`70b1961`), v2 window. The 46-PR window's gold mix has **proof-golf 1 of 58** (`eval-unseen-window.md:31-33`). Validation: "golf" appears in 1 of 276 comments. | **Delete the claim.** It also contradicts DUP line 173 (§c). |
| 34-36 (golf) | "`simp`/`simp_all`/`grind`/`omega`/`gcongr`/`grw`" | **L** | v2 window. **Inferred** by match with the v3 intervention digest (`inputs/pr_review_v3/interventions_review.md`): pr33401_i01/02 (`simp_all`, `grw [pow_succ, …]`), pr33333_i01 and pr33111_i02 (`grind`). Validation: `grind` 11 comments / 5 PRs, `gcongr` 3/2, `omega` 1/1, `grw` 0. | **Generalise, or keep as "e.g."** `grind` recurs in validation, so the list is not dev-only, but it is a list of that season's favourites. Suggested: "replace bespoke steps with a standard automation tactic or an existing lemma — use `proof_profile`/search to find what the library uses for goals of this shape". That needs `proof_profile` granted by default (a Part 3 decision). |
| 103-109 (idiom) | "`grw [...]` or `gcongr` … `omega` / `grind` / `decide` … `fun_prop` … dualizing via `OrderDual` (`α := αᵒᵈ`)" | **L** | v2 text. **Inferred** by digest match: `grw`/calc → 33401; `fun_prop` → 33117 (`@[to_fun (attr := fun_prop)]`, pr33117_i01); **`(α := αᵒᵈ)` is 33145's maintainer suggestion verbatim** (pr33145_i02, "hS.continuous_upperBounds (α := αᵒᵈ) hf"). 33145 and 33117 are dev PRs. Validation: OrderDual/ᵒᵈ 0, fun_prop 0, to_fun 0, grw 0. | **Generalise:** keep the pattern classes (monotonicity chain, rewrite chain, decision procedure, `fun_prop`-style discharge, re-derived lemma, symmetric statement proved twice) and drop the `(α := αᵒᵈ)` literal. The dual pattern already lives in family_design. |
| 172-174 (dup) | "This is the single most common reason maintainers send Mathlib PRs back" | **S** | v2 text | **Delete.** It contradicts golf line 30. |
| 181 (dup) | "when semantic search is available, use it" | U (unbacked) | v2 text. No semantic-search tool is granted in v5 (`duplication` holds `declaration_search` only). | **Delete**, or name the real tool. |
| 489-493 (correctness) | "Start by compiling … A reviewed file that does not compile is the most serious finding you can report and the easiest to miss" | **F** | 33057 ("Fix the remaining error(s) … so that it builds"). `base.py:643-644`: "33057's gold obligation is exactly that". Validation PRs are pre-gate passes with rebuilt reviewed workspaces, so `compiles: true` is expected almost always. | **Keep the compile** (it is cheap and the text already calls green "the ordinary case"). Drop "easiest to miss". |
| 533-543 (family_design) | Five bullets: "A DUAL … `OrderDual` (`α := αᵒᵈ`)"; "A MISSING COUNTERPART … a `sup` with no `inf`"; "A GENERATED FORM WRITTEN BY HAND. Repeated `fun_*`/`comp_*` variants … produced by an attribute"; "A REPEATED ARGUMENT … The same `have` in three proofs"; "A SHARED PARAMETER … every member fixed to `2` where `k` would do" | **R** (all five) | Every bullet is one dev obligation. 33145: reprove lower via `OrderDual`, and `Dense.ciInf'` as counterpart. 33117: `fun_*` lemmas → `@[to_fun (attr := fun_prop)]`. 33421: "Factor out the repeated `Tendsto (2 * ·)` argument", and `two_mul_fract…` → general `k`. First seen in `3828243`. **Inferred** by one-to-one match with gold. Validation: OrderDual 0, to_fun 0. `specialist-arm-contents.md`: 26 + 11 invocations, 0 candidates. | **Generalise, or retire the arm.** A group question without the dev shapes: "Would a maintainer ask for a change to how these declarations relate — one derived from another, one missing, several collapsed into one lemma or one mechanism, a constant that should be a parameter?" Drop `αᵒᵈ`, `fun_*`/`comp_*`, `2`/`k` and "three proofs". |
| 552-557 (family_design) | "The contract line above names one — declare whichever of these two" | U (contradiction) | The contract is rendered **below** and says "Every candidate must set concern_family to 'generalization'" (`render_focused.py:78-79`). Documented in `specialist-arm-contents.md`: "Zero off-concern tags have ever been emitted". | **Fix:** render `expected_concerns` in the contract, or delete this section. |

### a2. Contract and focused renderer (`src/mathlib_review/agenda/render_focused.py`), all ten arms

| file:line | quoted text | kind | provenance | generalise or keep |
|---|---|---|---|---|
| 87-88 | "\"Rename `foo_aux'` to `foo_of_isUnit`\" is a request." | W (sanitised shape) | This replaced 33421's `round_eq_div`, which the gate caught (`test_prompt_contamination.py:3-6`). It keeps the shape of 33421's ask (primed → descriptive suffix). | **Keep** (the prime→word convention is general). An example of a different shape would stop echoing one gold ask, e.g. "Replace the `simp` block in `foo` with `exact bar.mono h`". |
| 92-97 | "The measured failure of this system is under-reaching … offering a docstring rewording where they asked for the lemma to be renamed and reproved through `OrderDual`, or a tidier tactic where they asked for the result to be generalised." | **F + S + W** | Dev held-out runs. `ab-heldout12-obligation-spine.md:118-120` ("'restructure this' asks answered with smaller edits", 33321). The OrderDual example is 33145's gold, and "generalised" matches 33145 `ciSup'` / 33421 `k`. First seen in `3828243`. **Inferred** for the exact examples. Validation: **146 of 276** reviewer comments are ```` ```suggestion ```` blocks, which are local edits. | **Generalise and soften:** "State the size of change a maintainer would ask for. If the right fix is structural (rename, reprove, generalise, merge), ask for that rather than a local patch." Remove "the measured failure of this system" (a claim about dev runs) and the OrderDual example. "Always ask for the structural one" may over-reach on a set where most asks are suggestion-sized; measure it on val small12. |
| 99-101 | "Say which field your claim is about. If what you have found is that something already exists in the library, that is a duplication claim whatever check you are running, and saying so in `concern_label`…" | U | — | "Say which field" is unclear: which field? It also conflicts with line 78-79 ("makes no other kind of claim") and with the brief's "drop it" (§c). |
| 118-121 (PATCH_SET_CLAUSE, 7 arms) | "deleting a generated lemma without adding the attribute that regenerates it does not compile, and neither does adding a dual before the lemma it is derived from exists" | **W** | 33117 (`to_fun` attribute) and 33145 (dual). `family_design`'s paragraph moved verbatim in `c74f509`. | **Generalise:** "Use it when the edits are individually wrong — e.g. removing a declaration and updating the declarations that use it." |
| 132-137 (LEGACY_ABSTENTION_PARAGRAPH, default) | "a wrong finding costs this review far more than a silence does" | U (contradiction) | `67c9580`'s own comment (`:141-143`): "a price on speech that no measurement here supports". It is still the default text. | **Delete the sentence.** It contradicts the `severity` schema that every arm reads ("filed as advisory, not withheld", `candidates.py:190-194`). |
| 190-198 (TARGET_SECTIONS, knob only) | "Maintainers here ask at advisory strength far more often than at blocking strength … a convention the repository is adopting but has not settled" | **S** | 19 of 24 held-out judgments advisory (`:173-175`, `af63619`), and 91 of 113 including the 46-window (`eval-unseen-window.md:52-55`). "Adopting but not settled" is 33337's `emerging` case. | **Keep with care.** It is a prior that is disclosed in `eval-unseen-window.md`. Re-measure on validation gold when it exists, and phrase it as a definition rather than a frequency. |
| 288 (every arm's user prompt) | `FACET_CHECKLIST_ONCE`: "Apply every item to every review target above" (8 families) | **U (major contradiction)** | `0e8fff9` moved the checklist to once per prompt. It was never removed from specialists. | **Fix:** drop the checklist from focused prompts, or render only the arm's own item. As it stands, every specialist's system prompt says "That is your only job — ignore …" and its user prompt says "Apply every item [all 8 families]". |

### a3. Generalist (`src/mathlib_review/agenda/render_prompts.py`), candidate-prompt/14

| file:line | quoted text | kind | provenance | generalise or keep |
|---|---|---|---|---|
| 49 | "style_norm_violation when Mathlib's style linters would flag it" | U (unbacked) | `fc53c8a` (v4). No linter tool. Mathlib CI already runs the linters (roadmap). | **Generalise:** "when it departs from a formatting convention the surrounding code follows". |
| 50 | "documentation_gap when documentation is absent" | U (contradiction) | v4 | It contradicts DOCS ("a missing docstring as a blanket rule" is not a finding; 8%/67%). Suggested: "when documentation a reader needs is missing or wrong". |
| 87 (in the user message via checklist) | "naming: rename declarations to match their meaning, type, and local sibling conventions" | U (contradiction) | v4 | In the **same generalist user message** the context slice says "not against the handful of lemmas that happen to sit beside it" (`review_map.py:130-133`). Pick one (see a1 row 352-356). |

The generalist's frozen text itself carries no dev identifier. Its dev exposure comes from tool descriptions (a5) and context slices (a4).

### a4. Context slices (`src/mathlib_review/agenda/review_map.py`), every arm and the generalist

| file:line | quoted text | kind | provenance | generalise or keep |
|---|---|---|---|---|
| 214-218 | "A name mentions a coercion. What does the repository call lemmas about this coercion — `coe_…`, or the name of the map it produces?" | **R** (leans to one answer) | 33337 (`coe_` → `toLinearMap_`). The docstring beside it (`:67-81`) discusses exactly this pair. First seen in `3828243`. **Inferred.** It fires on any leaf containing "coe". | **Generalise:** "A name mentions a coercion. What does the repository call lemmas with this conclusion subject? (`naming_norm`)" Drop the suggested alternative. |
| 200-206 | "Does the repository spell this family of names with dot notation (`Foo.of_bar`) or flat (`foo_of_bar`)…" | R | 33294 (dot-notation rename). Docstring `:68-74`. **Inferred.** | **Keep** (dot notation is a live convention; 2 val comments). Consider firing it on any rename, not only `migration`. |
| 208-212 | "Is a primed variant acceptable here, or is a descriptive suffix expected instead?" | R | 33421 `round_eq'`, plus the review-corpus quote "we want to move away from primed names" (`:77`). **Inferred.** | **Keep.** It is phrased neutrally. |
| 130-133 | "Not against taste, and not against the handful of lemmas that happen to sit beside it" | F | 33337 (same origin as naming 352-356) | See the naming row. It contradicts the checklist's "local sibling conventions" and the style arm's local-consistency rule. |

### a5. Tool descriptions and output templates (every arm, generalist, lead, as noted)

| file:line | quoted text | kind | reach | provenance | generalise or keep |
|---|---|---|---|---|---|
| `review/base.py:481` | `declaration_name` "e.g. Subgroup.closure_pow_le" | **W** | every arm, generalist, **lead** | PR 33401's gold target (46-window; v3 interventions pr33401_i01/02). In `70b1961` (v2). **Confirmed.** | **Generalise:** "e.g. `Finset.sum_comm`" or "`Namespace.lemma_name`". Change it at a run boundary. |
| `context_tools.py:617` | naming_norm `declaration` "e.g. `Submodule.coe_starProjection_eq_x`" | **W** (new) | naming, **generalist** | **33337's gold rename subject** `coe_starProjection_eq_isComplProjection` (dev gold: "Rename the lemma `coe_starProjection_eq_isComplProjection` … to use the `toLinearMap_...` prefix") with the tail replaced by `x`. Added in `19ef236`, whose body runs the tool on exactly that name. The gate cannot see the altered form (probe in §b). | **Generalise:** "e.g. `Finset.card_union_le`". |
| `context_tools.py:178-180` | zulip note "Search for identifier fragments or words, e.g. `toLinearMap` or `naming convention`." | **W** | all zulip holders (naming, docs, style, family_design, generalist) on an empty-term query | 33337. `9bf474e`: "The case that motivated this, from the 33337 naming arm". | **Generalise:** "e.g. a lemma-name fragment or `naming convention`". |
| `context_tools.py:484-488` | proof_profile: "A tactic ranked second at 3% whose use went from nothing to that in a year is a stronger signal than the 25% tactic that has been flat for three." | **W** (illustration) + F | **generalist** (every run); proof arms only under rung3b-d | 33098: `grind` second on subset-concluding lemmas and NEW (`0222433`: "`simpa` first … `grind` second, marked as absent a year ago"). The numbers are illustrative. The description instructs the model to prefer a rising tactic, which was written to get `grind` chosen. | **Generalise:** "Read rank, share and trend together; a rising tactic may be the one a maintainer asks for, a flat high-share one is how the library already reads." Drop the numeric vignette. Also `conclusion_head` lists "subset, ssubset" first (`:494`), which is harmless. |
| `context_tools.py:602-604` | naming_norm "`established` means the corpus is lopsided enough to hold a PR to (a blocking ask)" | U | naming, generalist | `19ef236` | The naming prompt says only "A rename is a fair ask". The bar (≥0.80) was set against 33337 (Part 3). Say "a rename is a fair ask" in both places, and leave severity to the schema definition. |
| `context_tools.py:196-205` | precedent_search "EXPERIMENTAL … results are often about something else" | — | naming, docs, style, family_design, generalist | — | **Keep.** It is honest. The naming prompt should match it (a1 row 371). |
| `context_tools.py:320-330, 351` | declaration_search examples `Finset.sum_comm`, `isOpen_iUnion` | — | — | generic | **Keep.** |
| `base.py:447-451` | environment note (base overlay) "…not evidence the PR fails to build. This PR compiles." | U | any arm on a base-overlay env | — | Moot under `require_reviewed_workspaces: true` (val). Otherwise it asserts a PR fact the tool cannot check and pre-empts `correctness`. |

### a6. Lead (`src/ape/tasks/lean_tasks/formal_math/review/prompts.py`, `lead.py`), default val mode

| file:line | quoted text | kind | provenance | generalise or keep |
|---|---|---|---|---|
| prompts.py:59-64 | "Measured on the last run: 7% of available specialist jobs were used, no PR came within half its cost cap, and three specialist arms were never invoked at all on any PR." | **S** (stale) | heldout11 rep2 (`routing.py:3-8`: "30 of 459 … (7%) … `proof_golf`, `api_reuse`, `generality` … zero times across eleven PRs"). Added in `3828243`. "The last run" is a dev run from before most of the current design. | **Generalise:** keep the instruction ("your budget is a target, not a ceiling") and drop the numbers and "last run". |
| prompts.py:80-81 | "Measured on this corpus, a single review pass misses far more by never looking at a site than by looking and judging wrong." | S | `43e9d88`, written "before anything paid had run"; refers to v2/v4 dev measurements. **Inferred.** | **Keep the instruction, drop "measured on this corpus".** |
| prompts.py:113-115 | "Self-reported confidence has been tested as a signal on this corpus three separate times and carries no information." | S | `43e9d88`. `pr-review-v5-principled-design.md:57`. | **Keep** ("do not route on confidence") and drop the count. |
| prompts.py:117-126 | "## The specialists" lists **four**: `proof_golf`, `proof_idiom` "(`grw`, `gcongr`, `simp`, `omega`/`grind`, `fun_prop`…)", `duplication`, `generality` | **L** + **U (major)** | `43e9d88` (v5 had four arms then) | **Fix:** describe all ten. `read_agenda` hands the lead ten arm ids (census rows, e.g. `results/pr5_…/census.json`: api_reuse, correctness, docs, … style), and six of them (naming, docs, style, api_reuse, correctness, family_design) are described **nowhere** the lead can read. `api_reuse` 107 pruned / 0 invocations per rep (`specialist-arm-contents.md`) fits this. The causal link is **inferred**. |
| prompts.py:119, 124-126 | "can a proof this PR *changed* be written shorter?" / "does a *new* declaration restate…" / "is a *new* declaration stated less generally…" | U (stale) | v4 lifecycles. v5 schedules every arm on added **and** modified (`arms.py:77-89`, itself motivated by 33066/33098). | **Fix:** "a proof this PR adds or changes"; "a declaration this PR adds". |
| prompts.py:10-12 | specialists "can search prior Mathlib discussion and past maintainer reviews, can compile candidate edits, and returns claims that a compiler has already checked" | U (unbacked) | `43e9d88` | Proof arms, duplication, generality, api_reuse and correctness hold no zulip/precedent tool. naming, docs and style are not compile-warranted. Suggested: "some can search discussion or review history; claims from proof, duplication and generality checks are compile-verified". |
| prompts.py:66-69, 128-130; LEAD_USER 158-160 | "The agenda marks a job `required` when…"; "The agenda marks each job `eligible`…"; "{eligible_count} of which the deterministic rule marked eligible. Call `read_agenda` to see them with their targets and rationale." | U (unbacked) | — | Census rows carry no `eligible`, `routing_priority`, `routing_reason` or `rationale` (`census.py:229-239`). Either add them to `CensusRow.render` or delete the claims. The `required` list also omits the `introduction` grain (duplication, correctness) and the `file` grain (style). |
| lead.py:500 vs prompts.py:74-78 | delegate: "The mandatory generalist pass has already run and is not requested here." vs system: "A generalist pass … is attached to your first `delegate` call automatically" | U (contradiction) | The code prepends the floor to the first `delegate` (`lead.py:622-649`). | **Fix the tool description**: "is attached to your first call". |
| lead.py:187 (served in `submit_routing` schema) | `CandidateAssessmentInput` docstring: "Recorded; never applied." | U (stale, contradiction) | Assessments are now applied subtractively (`review/lead_synthesis.py`). The system prompt and the tool description say `drop` / `duplicate_of` remove or fold. | **Fix the docstring**, or set `model_config` `json_schema_extra` so developer docstrings do not ship. |
| lead.py:53-68, 113-121 (served in `delegate` schema `$defs`) | "In one measured case the lead delegated a `generality` job whose reason named a *naming* concern…"; "exactly what happened on the first smoke run: all four leads reported 'delegate tool failed (schema error)'…" | **F** (dev-run anecdotes) | smoke / held-out runs | **Remove from the served schema.** They are developer docstrings becoming `description`. Move them to `#:` comments and give each model a one-line docstring. Verified with FastMCP `list_tools()`: present in `delegate`'s inputSchema. |
| lead.py:104-107 (brief render) | "You are still the {arm_id} check and may report only your own concern; if the answer turns out to belong to a different concern, drop it rather than restating it as yours." | U (contradiction) | `43e9d88` | It contradicts the contract's "that is a duplication claim whatever check you are running" and the current policy (off-concern is recorded, not refused, `arm.py:42-57`). Say "file it under your concern and say in `concern_label` what it is". |
| lead.py:451-452 | comprehension summary examples "'deprecates X for Y across the library', 'adds a dualised API'" | W (mild) | 33294 (deprecation / migration), 33145 (dual). **Inferred.** | **Keep, or vary**; low risk. |

### a7. Submission schema (`src/ape/tasks/lean_tasks/formal_math/review/candidates.py`), every arm and generalist

| file:line | quoted text | kind | provenance | generalise or keep |
|---|---|---|---|---|
| 190-194 | `severity`: "advisory: … a convention the repository is adopting but has not settled … A claim you hold at advisory strength is filed as advisory, not withheld." | S/F | `af63619`: "gold marks 19 of 24 held-out judgments advisory". The 33337 arm withheld an `emerging` rename. | **Keep** (it is a definition). Reconcile with the LEGACY paragraph (a2) and with `below_my_bar` (next row). |
| 746-757 | `abstention_reason` "`below_my_bar`: you found a candidate issue and it did not meet the evidence or **severity** bar" | U | — | "Severity bar" invites withholding an advisory claim, which the severity field forbids. Say "evidence bar". |
| 91-95 (served under `target_verdicts`) | `TargetVerdictSubmission` docstring: "OCR's session replay found … BitsAI measured the opposite for a fine-tuned classifier…" | U (developer text in schema) | `work-enumeration` | **Remove from the served schema.** Verified present in the verdict tool's inputSchema. |

### a8. Solo (`src/ape/tasks/lean_tasks/formal_math/review/solo.py`), solo configs only

| file:line | quoted text | kind | provenance | generalise or keep |
|---|---|---|---|---|
| 64-68 | "What maintainers actually raise, in rough order of frequency: a proof that could be shorter …; a declaration that duplicates …; … a missing or inadequate docstring" | S (unsourced) | — | Unsupported, and it contradicts the 46-window mix (style 25, naming 11, docs 10, duplication 5, proof-golf 1) and DOCS' 8%/67%. **Drop "in rough order of frequency".** |
| 75-76 | "\"`foo_bar` has no docstring, and the three lemmas around it do\" is [a review comment]" | U | — | Close to what DOCS calls a non-finding. **Keep** only if the sibling-consistency framing is intended. |

### a9. Registry rationales (`src/mathlib_review/agenda/registry.py`), not model-visible by default

This corrects the task premise and confirms the known examples.

| file:line | quoted text | kind | provenance |
|---|---|---|---|
| 142-144 (proof_idiom) | "`grw`/`gcongr`, `simp`, `omega`/`grind`, `fun_prop`" | L | The **text** is from v4 `fc53c8a` (`focused_specs.py:172-176` has the same string). The 33098 tie is in the **comment** at 145-150 (`grind` second on subset lemmas), which motivates the `proof_profile` grant, not this list. The same list **is** model-visible in LEAD_SYSTEM 120-121 and IDIOM 104-107. |
| 179-187 (docs) | "a module whose non-obvious approach has no `Implementation details` note. This is the most requested and the least often noticed … over-long lines … which the repository's own linter can settle" | R/S/U | 33321, 33305. The same content is model-visible in DOCS_SYSTEM (a1). |
| 191-194 (style) | "a lemma that belongs inside a `namespace` block and was left outside it is a placement defect" | R | 33362 (comment 196-204). **This is the only place the style remit mentions namespace placement, and no model reads it by default.** STYLE_SYSTEM never says it. |
| 221-223 (family_design) | "a generated form written by hand" | R | 33117. Model-visible via FAMILY_DESIGN_SYSTEM. |
| 94-95, 121, 198-202 | 33305 / 33362 / 33321 | comments | These justify `extra_subject_kinds` and `expected_concerns`, which are Part 3 knobs. |

**Rewrite for the rationales:** make each a one-line, dev-free statement of the arm's question, and render them in `CensusRow.render` (or once in LEAD_USER) so the lead can read what each arm is for. This is the same fix as the four-arm list in a6.

### a10. In flight, not on develop

- `naming-from-statement` (11 ahead) adds, at `context_tools.py:806` on that branch, a
  `naming_statement` description whose example is **"e.g. `round_eq'`"**. That is 33421's gold
  rename subject.
- The same branch adds a `STATEMENT_NAMING` supplement (`focused_prompts.py:744-766` there). Its
  comment enumerates the three dev non-prefix asks ("a token that names a hypothesis" = 33145,
  "a prime where a word would say what differs" = 33421, "a leaf that belongs in the conclusion
  head's namespace" = 33294). The supplement text itself names no declaration.
- Flag the `round_eq'` example before merge. The supplement is a remit cut to exactly the dev
  ask shapes. Coordinate before rewriting the naming prompt, as the todo requires.

---

## Dev identifiers in model-visible text (develop)

**PR numbers.** None of the 16 dev PR numbers, and not 33401, appears in any model-visible string.
Every occurrence is in a comment or a docstring that does not ship. The shipped schema docstrings
(a6/a7) carry no PR number. The PR's own number in the user prompt (`# PR #…`) is the PR's own data.

**Identifiers and dev-derived strings that do ship:**

| identifier / string | dev origin | where it is model-visible |
|---|---|---|
| `toLinearMap`, `toLinearMap_`, `coe_`, 121/21/7 | 33337 | NAMING_SYSTEM 381-382; zulip empty-query note `context_tools.py:180` |
| `Submodule.coe_starProjection_eq_x` | 33337 gold subject | naming_norm arg `context_tools.py:617` (naming, generalist) |
| `Subgroup.closure_pow_le` | 33401 gold | `base.py:481` (all arms, generalist, lead) |
| `encard_le_encard` | 33098 `encard_` prefix | NAMING_SYSTEM 350 |
| `grind` | 33098 (dev); 33333/33111 (v2 window) | GOLF 35, IDIOM 106, LEAD_SYSTEM 121, proof_profile vignette (implicit); RUNG3C 722 (bench-only oracle) |
| `OrderDual`, `(α := αᵒᵈ)` | 33145 maintainer suggestion | IDIOM 109, FAMILY_DESIGN 533-535, SUBMISSION_CONTRACT 95 (all ten arms) |
| `fun_*`/`comp_*` + "attribute" | 33117 `@[to_fun]` | FAMILY_DESIGN 538-540, PATCH_SET_CLAUSE 119-120 |
| `fun_prop` | 33117 | IDIOM 107, LEAD_SYSTEM 121 |
| `grw`, `gcongr`, `simp_all` | 33401 | GOLF 35, IDIOM 104, LEAD_SYSTEM 120 |
| "Implementation details" | 33321 | DOCS_SYSTEM 404-407 |
| `2` → `k`, "same `have` in three proofs" | 33421 | FAMILY_DESIGN 541-543 |
| `coe_…` vs "the name of the map it produces" | 33337 | context slice `review_map.py:217` |

**Comments only, never shipped:** `Complex` / `namespace Complex` (33362), `Parseval` (33149),
`round_eq'` / `round_eq_div` (33421), `Dense.ciSup` / `Dense.continuous_*` (33145),
`minimalCover` (33098), `IsNormal` (33294). One exception: the `round_eq'` example on the
`naming-from-statement` branch (a10) would ship.

---

## (b) The contamination gate

`tests/datasets/test_prompt_contamination.py` sweeps:

- `focused_system_prompt(spec)` for all ten arms, **baseline variant only**, in the default
  contract and with both knobs on;
- SUBMISSION_CONTRACT, ASK_WITHOUT_FIX_CLAUSE, VERDICTS_ABSTENTION_PARAGRAPH, TARGET_SECTIONS;
- `LEAD_SYSTEM`.

`analysis/report.py:262-290` (`report contamination`) sweeps the same set minus the lead.

**Not swept** (all model-visible by default unless noted):

- every tool description, argument description and output template (`base.py`, `context_tools.py`, `lead.py`, `candidates.py`);
- the pydantic class docstrings served in tool schemas;
- `LEAD_USER`;
- the generalist `SYSTEM_PROMPT_V12` and `FACET_CHECKLIST_ONCE`;
- context-slice text (`review_map.py`: convention questions, headers), component and census reason strings;
- `InvestigationBrief.render` boilerplate;
- solo prompts (solo configs only);
- the rung supplements (bench-only);
- registry rationales (fallback-only).

**Blind even where it sweeps.** `prompt_leaks` matches gold verbatim, in two ways: an identifier
of at least 8 characters containing `_` or `.` and not preceded by `.`, or a run of 7
informative words. Probed against the dev gold (1,128 strings):

| probe | result |
|---|---|
| `(e.g. Subgroup.closure_pow_le)` | **[]** (a namespaced form fails the look-behind) |
| `(e.g. closure_pow_le)` | caught |
| `` e.g. `Submodule.coe_starProjection_eq_x` `` | **[]** (altered name) |
| `21 use toLinearMap_ and 7 use coe_` | **[]** (statistic; `toLinearMap` has no `_`/`.`) |
| `` `grind [minimalCover]` `` | **[]** (`minimalCover` has no `_`; `grind` under 8 characters) |
| `move the declarations inside namespace Complex` | **[]** (fewer than 7 informative words shared) |
| `@[to_fun]` | **[]** (`to_fun` is whitelisted in `_GENERIC_LEAN_VOCABULARY`, `contracts.py:84-87`, though it is 33117's gold attribute) |

Run over all 96 collected surfaces (swept or not), it returns nothing. So the gate is clean and
the tree still carries a dozen dev-derived strings (the table above). The gate catches verbatim
answers. It cannot catch paraphrase, sanitised shapes, dev statistics, or short and camelCase
identifiers. That is a property of its design, not a bug in a regex.

**Gold source.** `all_gold()` globs every `inputs/pr_review_v4/releases/*/gold/judgments.jsonl`.
Today that means dev releases only (val and eval have no `judgments.jsonl`). When validation gold
is built it joins automatically, which is good. If a test-set `judgments.jsonl` ever lands under
`releases/`, the suite would read test gold. The glob should exclude `eval-*` explicitly.

**What would close the gate:**

1. Sweep the served tool schemas. Register each task's tools on a `FastMCP` and `list_tools()`
   in-process (free; I did exactly this).
2. Match namespace-suffixed forms (drop the `.` from the look-behind, or also test the leaf).
3. Add a **dev-vocabulary denylist** of identifiers taken from dev gold subjects and requested
   names (including camelCase tokens such as `toLinearMap`, `minimalCover`, `starProjection`),
   because the dev set is what prompts get written from.
4. Remove `to_fun` from the whitelist.
5. Sweep `LEAD_USER`, the generalist system and checklist, the context-slice templates and the
   brief boilerplate.

Also land `tool_schemas_sha256` (`framework-defects-2026-09.md:175-191`). Tool text is sealed in
no plan today, so any change in a1-a7 to a tool description moves no identity.

---

## (c) Contradictions and unbacked claims

**Contradictions within one model's context:**

1. **Specialist system vs user.** "That is your only job — ignore …" (every arm) against
   `FACET_CHECKLIST_ONCE`, "Apply every item to every review target above" (8 families,
   `render_focused.py:288`, `render_prompts.py:99-106`).
2. **Naming norm, local vs global.**
   - The checklist says "local sibling conventions" (`render_prompts.py:87`). The naming arm and
     generalist see it in their user message.
   - NAMING_SYSTEM 352-356 and the context slice (`review_map.py:130-133`) say "not the handful
     of lemmas that happen to sit beside it".
   - The generalist sees both in one user message; the naming arm sees both across system and
     user.
3. **family_design's concern.** "declare whichever of these two" vs the contract's "Every candidate must set concern_family to 'generalization'" (`focused_prompts.py:552-557` vs `render_focused.py:78-79`).
4. **Off-concern findings, four instructions.**
   - The contract says "makes no other kind of claim" (78-79).
   - The contract also says "that is a duplication claim whatever check you are running … say so in `concern_label`" (99-101).
   - The brief says "drop it rather than restating it as yours" (`lead.py:104-107`).
   - The abstention enum has `belongs_to_another_concern`.
   - Actual policy: record, do not refuse.
5. **Speak vs withhold (default run).**
   - The abstention paragraph says "a wrong finding costs this review far more than a silence does" (`render_focused.py:137`).
   - The `severity` schema says "filed as advisory, not withheld" (`candidates.py:190-194`).
   - `below_my_bar` names a "severity bar".
   - The contract's under-reach paragraph pushes the other way.
6. **Precedent weight.** NAMING says precedent is "the strongest evidence available"; the tool says "EXPERIMENTAL … often about something else".
7. **Frequency claims.** GOLF says golf is "the single most common substantive comment"; DUP says duplication is "the single most common reason maintainers send Mathlib PRs back"; DOCS says completeness is "the one maintainers ask for most"; SOLO gives its own order. The 46-window's gold mix has proof-golf 1 of 58.
8. **Golf vs idiom remit.** GOLF: "SHORTER or more idiomatically" (`:29-30`). The idiom rationale and LEAD: "Explicitly not about length"; "running both on one proof is normal and is not a duplicate". This is already recorded in `specialist-arm-contents.md`.
9. **Documentation gap.** The generalist says "documentation_gap when documentation is absent"; DOCS says a missing docstring is not a finding (8%/67%).
10. **Lead floor timing.** The `delegate` description says "already run"; LEAD_SYSTEM says "attached to your first `delegate` call" (the code does the latter).
11. **Lead assessments.** The `CandidateAssessmentInput` docstring says "Recorded; never applied"; LEAD_SYSTEM and `submit_routing` say `drop` / `duplicate_of` remove or fold (and they do).
12. **Lead lifecycle claims.** "a proof this PR *changed*", "a *new* declaration" vs v5 scheduling of every arm on added + modified.

**Unbacked by the toolset or tool output:**

- DOCS: "The repository's own linter settles these". The generalist: "Mathlib's style linters would flag it". No lint tool is granted, and Mathlib CI already enforces mechanical style (roadmap:92-101).
- DUP: "when semantic search is available, use it". No such tool in v5.
- LEAD: specialists "can search prior Mathlib discussion and past maintainer reviews … returns claims that a compiler has already checked". This is false for 5 of 10 arms (search) and 3 of 10 (compile).
- LEAD / LEAD_USER: "The agenda marks each job `eligible`", "see them with their targets and rationale". Census rows carry neither.
- LEAD: "The specialists" names four of ten.
- `base.py:450` (base-overlay environments only): "This PR compiles."

**Unclear:** the contract's "Say which field your claim is about." (`render_focused.py:99`).

---

## (d) What to change first, ranked

1. **Take dev identifiers and developer anecdotes out of the tool schemas, and make the gate see
   schemas.**
   - Rewrite the `closure_pow_le` example (`base.py:481`), `coe_starProjection_eq_x`
     (`context_tools.py:617`), `toLinearMap` (`:180`) and the 3%/25% `grind` vignette
     (`:484-488`).
   - Strip the dev-history class docstrings from `InvestigationBrief`, `DelegationRequest`,
     `TargetVerdictSubmission` and `CandidateAssessmentInput` (whose docstring is also wrong).
   - Extend the gate per §b.
   - *Why first:* these reach every arm, the lead and the generalist (which holds all five
     context tools and produces most hits). They are invisible to the gate and to every hash.
     The change is free and moves no behaviour except the example text. Land it at a run
     boundary with `tool_schemas_sha256`.
2. **Remove the specialist system/user contradiction.** Drop `FACET_CHECKLIST_ONCE` from focused
   prompts (or render the arm's own item only), and resolve "local sibling conventions" vs
   "not the neighbours". *Why:* it hits all ten arms on every call and is a direct contradiction
   of each arm's one instruction. It moves ten prompt hashes, so it lands at one boundary.
3. **Rewrite the lead's arm roster.**
   - Describe all ten arms, in dev-free one-liners (the natural home for the registry rationales).
   - Fix the stale lifecycles, the stale "last run" statistic, the "already run" contradiction,
     and the `eligible` / rationale claims `read_agenda` cannot back.
   - *Why:* the validation base config is lead mode. The lead decides which arms run, and it is
     choosing among six arm ids it has never been told the meaning of.
4. **De-dev the arm prompts that are cut to dev obligations.**
   - family_design's five bullets (33145 ×2, 33117, 33421 ×2), or retire the arm.
   - DOCS' "Implementation details / auxiliary ordering" (33321), its "most requested" claim and
     its linter claim.
   - STYLE's line-length bullet. Add namespace placement to STYLE_SYSTEM, since validation has
     4 PRs with namespace asks.
   - IDIOM's `(α := αᵒᵈ)` literal.
   - PATCH_SET_CLAUSE's two dev examples.
   - The contract's OrderDual under-reach example.
   - *Why:* these are the texts whose content is one dev obligation each. The validation lexical
     counts (OrderDual 0, to_fun 0, fun_prop 0, grw 0, "Implementation details" 0) suggest the
     specific shapes do not recur. `grind` (5 PRs) and namespace asks (4-5 PRs) do recur. Keep
     the classes and drop the instances.
5. **Replace the naming worked example** (33337 counts), `encard_le_encard`, and the leading
   coercion question in `review_map.py:214-218`. Coordinate with `naming-from-statement`, which
   also adds `round_eq'` as a tool example (a10). *Why:* this is the clearest W item, but the naming
   arm is being redesigned on that branch, so do it there or right after its merge.
6. **Delete the unsupported frequency claims** (GOLF, DUP, DOCS, SOLO) and pick one speak/withhold
   rule. Delete "a wrong finding costs … far more than a silence" from the default abstention
   paragraph, and change `below_my_bar`'s "severity bar" to "evidence bar". *Why:* these are
   mutually contradictory priors, and one of them is flagged in the code itself as unsupported by
   measurement. They can move emission rate, so measure them on val small12 with a threshold
   stated in advance.

Every item from 2 onward moves prompt identities. Items 2-4 and 6 change specialist or lead
behaviour, so each needs one judged val-small12 rep against a matched control before any claim
is made. That is three reps before a number is quoted, per CLAUDE.md. Item 1 is hygiene; a single
run-boundary note is enough.
