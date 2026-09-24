# What in the v5 pipeline is fitted to the dev set, read against the validation set (2026-09-24)

The audit asked for in `docs/todo/pipeline-overfit-review.md`. Every design since August was tuned
on 16 dev PRs (the held-out 12 plus smoke4). The validation set `val-2025-06-2026-03-v1` (60 PRs:
50 natural-rate PRs from 2025-06 to 2026-03, plus 10 AI-generated) is now development material, so
the pipeline can be checked against review work it was not shaped by. Nothing was run and nothing
was spent. The test set `eval-2025-06-2026-03-v1` was not read: every query below filters to the
validation release's `pr_numbers` and asserts it shares none with the test release.

Three parts, as the todo specifies: (1) whether the arm division covers the review work, (2)
dev-specific text in what the model sees, (3) dev-tuned knobs. Then a proposal.

## Conclusion first

**The arm division was shaped by one reviewer's asks on four PRs, and the validation set's review
work is mostly elsewhere.**

- **One reviewer.** On dev, one reviewer wrote **30 of the 52** round-1 reviewer comments (58%), on
  33066, 33098, 33145 and 33337. Those are the PRs the naming, idiom and family designs were built
  around. On validation, 26 reviewers wrote the 144 comments, and the busiest wrote 17%.
- **Naming, the most-engineered arm.** Naming is **14 of 48** dev asks (29%) and **3 of 107**
  validation asks (3%). Only one of the three is a declaration rename.
- **Asks no arm owns.** On validation, **32 to 36 of 107** asks belong to no arm's remit as
  written (32 on both readers' labels, 36 on either's). Only **40** fit an arm explicitly, and 29
  of those are the proof arms or the style prompt's binder bullet. Everything else in the ten
  remits, style's formatting bullets included, names **11** validation asks.
- **Three families no remit reaches.** They make up most of the unowned asks:
  - **registration:** should this lemma carry `simp`, `gcongr`, `grind` or `aesop`, at what
    priority, and is a `nolint` justified? 10 asks on 6 PRs, none owned.
  - **PR level:** is the change wanted, split right, explained in its description, tested and
    coordinated with other work? 15 asks on 11 PRs, none owned, and no work unit exists at PR grain.
  - **statement and API design:** the canonical form, an ext-shaped lemma, extracting a definition,
    missing basic API. 8 asks on 8 PRs, none explicit.

  The dev set has 0, 4 and 4 of these.

Parts 2 and 3, and the proposal, follow the coverage section.

## 1. Coverage of the review work by the arm division

### Method

- **The work.** Every round-1 reviewer event on the validation PRs: the events each PR's episode
  boundary lists as `feedback_event_ids` (the funnel's substantive reviewer events between review
  start and the next push). They were read from the PR store through `events_from_bundle`, the same
  path the episode builder takes, for **144 events on 49 of the 60 PRs**. The other 11 PRs have no
  round-1 feedback; they are the structural controls. `reviewer_view.jsonl` could not be used,
  because it excludes scored PRs, and the validation PRs are now scored.
- **Two readers, blind to each other and to this audit's hypothesis.** Both are model readers
  (Claude, one model family). Each got the rubric, all 144 comments with their diff hunks, and each
  arm's registry remit and system prompt verbatim, and nothing else. One read front to back and one
  back to front.
- **Per comment, they labelled:** ask or not; every arm whose *written* remit covers the ask
  (non-exclusive); a primary owner or `none`; whether the fit is `explicit` (the remit names this
  kind of ask) or a `stretch`; which prompts explicitly exclude it; one generic question; the grain;
  and the kind of code.
- **What was not shown.** The readers were not shown the generic 8-item checklist that every arm's
  user prompt ends with (`render_prompts.py::FACET_CHECKLIST_ONCE`). It is the same for every arm and
  contradicts each arm's "that is your only job". See the sensitivity note below.
- **Adjudication and the dev baseline.** The auditor adjudicated the asks into question families
  from both readers' generic questions. The dev baseline is the same extraction on
  `dev-medium-0.5.0`: 52 events on 13 of 16 PRs, labelled by the auditor alone.
- **Where the data is.** Labels, families and event ids (no comment bodies) are in
  `results/pr_review_v5/adjudications/arm-coverage-val-2025-06-2026-03-v1/`.

**Agreement:**

- Ask or not: 142 of 144. The two splits were c026 (a premise objection between reviewers, counted
  as an ask) and c057 (a remark about churn, counted as not an ask).
- The primary owner of the 106 comments both readers call asks: agreement 101 of 106, κ = 0.94.
- Owned versus unowned: κ = 0.91.

Two instances of one model family agreeing is an upper bound on inter-annotator agreement, not a
human figure. A human pass outranks all of it and has not happened.

### Result: the families of review work, validation against dev

One family per ask. "Owned" means both readers name a primary arm; "explicit" means both readers
name the same arm and call the fit explicit.

| family | the question | val asks | val PRs | owned | explicit | dev asks |
|---|---|---|---|---|---|---|
| F1 proof | can this proof be shorter, more direct, closed by a standard tactic; does the old proof still work? | **22** | 11 | 22 | 20 | 9 |
| F2 interface | are binders, implicitness, instance arguments and section `variable`s right? | **12** | 7 | 12 | 9 | 1 |
| F3 registration | should it carry `simp`/`gcongr`/`grind`/`aesop` or be an instance, at what scope and priority; is a `nolint` justified? | **10** | 6 | **0** | 0 | 0 |
| F4 derive, don't restate | should it be generated (`simps`, `to_dual`, `to_fun`, a structure's projections) or derived from its counterpart? | 5 | 4 | 4 | 3 | 4 |
| F5 redundancy | does it restate something existing or in the PR; is anything dead; is a deprecated alias left? | 5 | 5 | 3 | 1 | 2 |
| F6 statement and API design | is this the right statement and lemma set (canonical form, ext form, extract a definition, missing basic API, an upstream helper)? | **8** | 8 | 4 | **0** | 4 |
| F7 generality | stated at the right level, hypotheses no stronger than needed? | 3 | 3 | 3 | 1 | 1 |
| F8 naming | are declaration, variable and hypothesis names conventional? | **3** | 2 | 1 | 1 | **14** |
| F9 formatting | whitespace, indentation, parentheses, line length, imports | 8 | 6 | 7 | 2 | 3 |
| F10 documentation | docstrings, module docs, comments: complete, correct, conventional; references; TODOs | **13** | 9 | 11 | 3 | 4 |
| F11 meta-code correctness | does tactic or linter code handle every input form, robustly? | 3 | 1 | 3 | 0 | 0 |
| F12 PR level | wanted, scoped and split right, described, tested, coordinated with other work? | **15** | 11 | **0** | 0 | 4 |
| mathematical correctness | build errors, axioms, false statements | 0 | 0 | – | – | 2 |
| **total** | | **107** | | 69 | 40 | 48 |

These are counts, not rates. Sixty PRs carry too few asks per family for a rate, and F11's three
asks are all on one PR (29339, an AI-generated linter).

### What the division owns, arm by arm

Primary owner, where both readers agree:

| arm | validation asks it owns | explicitly | where |
|---|---|---|---|
| `proof_golf` | 21 | 18 | F1 |
| `style` | 19 | 11 | F2 binders and variables (9 explicit); F9 formatting |
| `docs` | 11 | 3 | F10; mostly stretches (prose edits, code comments, references) |
| `generality` | 5 | 1 | F6 and F7; all but one need a new statement *and* proof, which its "keep the proof" rule forbids |
| `family_design` | 4 | 3 | F4: two `simps` asks and one `to_dual` |
| `duplication` | 3 | 1 | F5 |
| `correctness` | 3 | 0 | F11, all on one linter PR, as stretches: its prompt is about axioms, simp loops and instances |
| `proof_idiom` | 2 | 2 | F1; in `owners` on 9 asks, 7 of them beside `proof_golf` |
| `naming` | 1 | 1 | F8 |
| `api_reuse` | **0** | 0 | named as a secondary owner on 4 asks |

Five of the ten arms own three or fewer validation asks each. Seven asks are split between
`proof_golf` and `proof_idiom` on both readers' labels. That is the overlap already recorded
(`docs/todo/specialist-arm-contents.md`: the two arms share every routing field, and the golf
prompt claims idiom's remit in its first sentence).

### Where no remit reaches

- **F3 registration (10 asks, 6 PRs, none owned).**
  - What the asks are:
    - tag a monotonicity lemma `@[gcongr]` (27124, twice);
    - tag with `grind` (32875, twice);
    - restore a dropped `simp` (36822, twice);
    - an `aesop` rule strength (36784);
    - a global instance that should be local (29069);
    - `nolint simpNF` should be a last resort (33185, twice).
  - The nearest remit is `style`'s "attribute placement", which is about where an attribute sits,
    not whether a lemma should carry one.
  - On dev the one registration request, "add `attribute [grind .] finite_empty`" on 33098, rode
    inside a golf ask.
- **F12 PR level (15 asks, 11 PRs, none owned).**
  - What the asks are:
    - is the change wanted at all (28036 twice, 35571, 36648);
    - explain the design in the description, or link the discussion (29413, 29842 twice, 36969);
    - split the PR (29204);
    - add a test (32668);
    - test-file placement (29339);
    - coordinate with an external project (35571);
    - a typeclass use the community should agree on (29413);
    - a tool config scope (31079);
    - extend the change to the rest of the file (26755).
  - Both readers mark 15 asks PR-grain (17 on either's labels). Work units are file-confined
    (`schema/identity.py`), so no arm is ever shown the PR as a whole. The four "ignore scope"
    prompts (golf, idiom, duplication, generality) exclude it explicitly.
  - Five of the 15 are on AI-generated PRs. The project's eventual target is AI-generated PRs, and
    "is this wanted, and is it of library quality" is the maintainers' first question about them:
    35571 was rejected as "entirely AI generated … dubious definitions and trivial API", and 36637
    was closed for being in the wrong generality.
- **F6 statement and API design (8 asks, 8 PRs, 0 explicit).**
  - What the asks are:
    - state it in the canonical form, with bridges as separate lemmas (28098);
    - the ext-shaped lemma is the right one to have (31295);
    - extract the linear map first (29511);
    - add `homEquiv_apply` lemmas (36493);
    - one general version across structures (31554);
    - an upstream helper lemma that makes the proof a rewrite (36071);
    - a different construction that drops a hypothesis (31079);
    - `Option` versus a neutral default in meta code (32668).
  - This is the design-scale shape that four of seven misses took in the unified-contract run on
    dev (`docs/research/unified-contract-fanout4-2026-09.md`). The validation set says it is common,
    not a dev quirk.
- **Smaller gaps.** A deprecated alias for a renamed lemma (28922), dead code (29339), and a docstring
  on a new *definition* (29511). The last is excluded by the `docs` prompt's rule that a missing
  docstring is not a finding, a rule justified in the same prompt by "67% of definitions" carrying
  one, which is the convention the maintainer was enforcing.

**Sensitivity to the shared checklist.** Every arm's user prompt ends with the same 8 items, and
two of them name these families loosely: "6. style: … attribute …" and "7. scope: move, split,
expose, privatize, or remove code". Counting the checklist would move F3 and some of F12 from
"unowned" to "every arm, generically". It would not give any arm a question about them, and every
arm's system prompt says the checklist's other seven items are not its job. The same reading was
taken in Phase 0 (`docs/research/the-question-is-already-asked-2026-09.md`, caveats).

### Against the dev set, and against the work-enumeration taxonomy

- **The dev set is not a sample of review work; it is one reviewer's review of four PRs.** That
  reviewer's asks are renames, golfs and order-dual derivations, which is why:
  - naming is 29% of dev asks;
  - F4 is 8% (the 33145 and 33117 derivations);
  - F2 and F3 barely appear (1 and 0).
- **The dev gold concentrates it further.** 14 of its 43 obligations are 33098's (seven `grind`
  rewrites, three `encard_` renames), and 33098 is where `proof_idiom`'s remit and the whole rung-3
  prompt ladder come from.
- **Against Phase 0 of `docs/plans/2026-09-23-work-enumeration.md`.** Phase 0 read 23 held-out
  obligations and found the current briefs asked 17. On validation's raw asks the explicit share is
  40 of 107, and the difference is in F2, F3, F6 and F12, which the held-out gold barely contains.
  Its conclusion ("the question text is not where the specialists lose") was right about dev
  and does not carry over. The question text reaches much less of the validation work.
- **The plan's open grain question has an answer.** "Decide this when the list shows how many
  PR-grain questions there are": on validation, 15 of 107 asks (14%), by both readers. A PR-level
  unit is needed, not file grain with the limitation recorded.
- **The families were fitted on validation, and dev is their out-of-sample check.** All 48 dev asks
  fall in F1-F12, apart from the two mathematical-correctness asks (the axioms and the build error on
  33149 and 33057). That is a check that the families are not validation-specific, at n = 48 from
  one reviewer. The plan's Phase 1 corpus sample (about 56k top-level reviewer comments outside
  scored PRs) is the real one.

### What this measures, and what it does not

- **It measures the remits as written, not what the arms do.** An arm can file outside its remit.
  The generalist does, and it holds 64 of 71 held-out hits. The question here is what the division
  asks for, which is what a re-division would change.
- **Raw comments, not gold.** No gold exists for validation yet (`eval-set-selection.md`, next
  steps). The gold chain may drop some F12 asks, such as "link the Zulip thread in the description".
  Whether PR-level asks are scored is a decision for the gold, and it should be made knowing they are
  14% of round-1 asks.
- **Model labels.** Two readers from one model family, and single-reader dev labels. The family
  adjudication is the auditor's, and the families are the audit's construction, not a found
  taxonomy.

## 2. Dev-specific text in what the model sees

The full inventory, with every line, provenance and rewrite, is
[`pipeline-overfit-2026-09/part2-model-visible.md`](pipeline-overfit-2026-09/part2-model-visible.md).

**How it was collected.** A read-only sweep. Every prompt constant, contract text, tool description
and output template on the default v5 path. The served tool schemas were collected by registering
each tool on an in-process `FastMCP` and calling `list_tools()`, with no model, because that is what
the scaffold forwards.

**Re-verified by the auditor:** the lead's arm list, the census row shape, the three tool-description
examples, and the shipped developer docstrings.

**What reaches a model in a default (lead) run.**

- **Reached:**
  - the arm system prompts, with the submission contract;
  - every arm's user prompt, which ends with the 8-item checklist;
  - the generalist prompt;
  - the lead prompt and its tool schemas;
  - every tool description.
- **Not reached:**
  - the v2 user templates;
  - the rung-3 supplements (bench only);
  - the registry `rationale` strings. `read_agenda` returns census rows with arm ids and signals and
    no rationale (`census.py:229-239`); the rationale reaches a model only through a no-census
    fallback that default runs never take.

So the remit re-cuts in `registry.py` around 33305, 33362 and 33321 act only through
`extra_subject_kinds` and `expected_concerns` (Part 3), not as text. The one place the style remit
mentions namespace placement is text no model reads.

**Dev content that does reach a model.** No dev PR number appears in any model-visible string.
Dev-derived content does:

| what ships | dev origin | who reads it |
|---|---|---|
| "of 121 declarations … 21 use `toLinearMap_` and 7 use `coe_`" | 33337's counts | naming arm (system prompt) |
| `Submodule.coe_starProjection_eq_x` | 33337's gold rename subject, tail altered | naming arm and **generalist** (`naming_norm` argument description, `context_tools.py:617`) |
| "e.g. `toLinearMap`" | 33337 | every `zulip_search` holder, generalist included (`context_tools.py:180`) |
| `Subgroup.closure_pow_le` | 33401's gold target (46-PR window) | every arm, generalist and lead (`lean_verify_edit`, `base.py:481`) |
| "a tactic ranked second at 3% … from nothing" | 33098's `grind` curve | **generalist** in every run (`proof_profile` description) |
| `(α := αᵒᵈ)`, `OrderDual` | 33145's maintainer suggestion, verbatim | idiom and family_design prompts; all ten arms through the contract's under-reach example |
| five `family_design` bullets | one dev obligation each (33145 twice, 33117, 33421 twice) | family_design |
| "an auxiliary ordering … an 'Implementation details' note" | 33321's obligation | docs |
| `encard_le_encard` | 33098's `encard_` prefix | naming |
| "A name mentions a coercion … `coe_…`, or the name of the map it produces?" | 33337, and it leans toward that answer | every arm's context slice |
| developer anecdotes in pydantic docstrings ("exactly what happened on the first smoke run") | smoke and held-out runs | lead, through the served `delegate` schema |

**The naming example is wrong as well as dev-specific.** The live `naming-from-statement` branch
read 33337's figure from elaborated statements: when `ContinuousLinearMap.toLinearMap` heads a
left-hand side, the corpus names it `coe` 37 times against `toLinearMap` 3. So the one worked
example of "a finding" in the naming prompt cites corpus support that does not exist.

**Does the dev content recur on validation?** A lexical count over the validation PRs' reviewer
comments, all rounds: `OrderDual`/`ᵒᵈ`, `to_fun`, `fun_prop`, `grw` and "Implementation details"
each appear **0** times. `grind` appears in 5 PRs, and namespace asks in 4 or 5. These are mentions,
not asks. The classes of these prompts recur; the dev instances do not.

**The contamination gate cannot see any of this.**

- **What it sweeps:** the arm system prompts, the contract and `LEAD_SYSTEM`.
- **What it does not sweep:** tool descriptions, served schemas, `LEAD_USER`, the generalist prompt,
  the checklist, and context slices.
- **How it matches:** gold verbatim, on identifiers of 8 or more characters containing `_` or `.`,
  or on 7-word runs.
- **What that misses:** a namespaced form such as `Subgroup.closure_pow_le`, an altered name, a
  statistic, and camelCase words like `minimalCover`. `to_fun` is on its allow-list.

Run over all 96 collected surfaces, the gate returns nothing, and about a dozen dev-derived strings
ship.

**Contradictions inside one model's context.** Twelve are listed in the appendix, §c. The ones
that touch every call:

1. **Every specialist's instructions contradict each other.** The system prompt says "That is your
   only job — ignore …". The user prompt ends with the checklist: "Apply every item [8 concern
   families] to every review target".
2. **The lead's prompt describes 4 of the 10 arms it chooses among** (`prompts.py:117-126`: golf,
   idiom, duplication, generality). The census hands it ten arm ids, and six of them (naming,
   docs, style, api_reuse, correctness, family_design) are described nowhere the lead can read.
   `api_reuse`'s 0 invocations fit this; the causal link is inferred.
3. **Speak or withhold.**
   - The default abstention paragraph says "a wrong finding costs this review far more than a
     silence does". Its own code comment calls that "a price on speech that no measurement here
     supports".
   - The `severity` schema says an advisory claim "is filed as advisory, not withheld".
4. **Frequency claims that contradict each other.**
   - Golf says it is "the single most common substantive comment".
   - Duplication says it is "the single most common reason maintainers send Mathlib PRs back".
   - Docs says completeness is "the one maintainers ask for most".

   On validation's 107 asks: proof asks 22, redundancy 5, documentation completeness about 3.
5. **Unbacked tool claims.**
   - Docs and the generalist are told a linter settles line length, and no linter is granted.
   - Duplication is told to use semantic search "when available", and no such tool exists.
   - The lead is told that specialists search discussion and return compile-checked claims, which is
     false for six and for four of them respectively.

## 3. Dev-tuned knobs

The full inventory is
[`pipeline-overfit-2026-09/part3-knobs.md`](pipeline-overfit-2026-09/part3-knobs.md): about 70
knobs, each with its value, file and line, what it was tuned on, and what validation's gold-free
features say.

**How it was computed.** With the tree's own functions: `enumerate_invocations`,
`build_components` and `plan_coverage`. The required counts match `cli plan` exactly (399 required
specialist rows, 824 floor jobs, $41.20 floor).

**Re-derived by the auditor:** the whitespace-only units (85, with 714 eligible pairs and 15
required rows) and the three packer-cliff hunks (24,874, 24,200 and 25,169 chars).

**The size shape is new on validation.**

| | dev (16 PRs) | validation (60) |
|---|---|---|
| units per PR, median / max | 5.5 / 15 | 3 / **66** |
| PRs over 15 units | 0 | **7** |
| targets on Tactic, Linter, MathlibTest or scripts paths | **0** | **90** |
| whitespace-only `modified` declarations | **0 of 124** | **120 of 344** |
| removed declarations | 13 | **92** |
| proposals the lead sees, max | 143 | **649** |

Ranked by the validation number, the knobs most likely fitted to dev:

1. **The packer charges text the renderer no longer prints.**
   - The 24,000-char unit budget charges each shared diff hunk once per unit. The budget was tuned
     against 33149, whose largest hunk (17,303 chars) is under it.
   - On validation, three new-file PRs (26484, 34906, 36637) each have one hunk shared by almost
     every target, at 24,200 to 25,169 chars. So every bundle opens a new unit: **138 of 425 units
     (32%)**, and $8.40 of the $41.20 floor.
   - At `/14` the renderer prints scoped diffs, not that hunk, so the prompts of those units are a
     median 6-8k chars. The charge should be for rendered text.
2. **No substantive-change filter on `modified`.**
   - A linter sweep (26718) and a spacing sweep (33716) put **85 units (20%)** on declarations
     whose only change is whitespace.
   - Those units carry 714 eligible specialist pairs, and 21 of the declarations count as
     proof-modified, so golf and idiom are scheduled on reformatted proofs.
   - Dev had none, so nothing ever needed the filter.
3. **Flat per-PR lead limits.** Validation has six PRs above the 184-proposal agenda that
   `lead_cost_cap` was sized for (the maximum is 649) and discretionary pools up to 469 pairs. The
   limits are 25 delegations, $1.50 of discretionary spend and a $1.00 lead cap. A lead that pauses
   on its cap appears to lose its PR's arm output (`runner.py:541-542`, a code reading, untested).
4. **The lifecycle rule.**
   - `_BOTH_LIFECYCLES` puts every arm on added and modified declarations. It was justified by
     smoke4's gold for the proof arms only.
   - It widens duplication and generality to 333 units against 174, although both remits say "a
     *new* declaration".
   - Meanwhile no arm is eligible on any of the **92 removed declarations**, 36 of which leave no
     trace. That is where the "keep a deprecated alias" ask (28922) lives.
5. **The required-row cap fills in hash order.**
   - `MAX_REQUIRED_SPECIALISTS_PER_PR = 10` binds on 12 of 60 PRs, against 4 of 16 on dev.
   - It fills in `(work_unit_id, arm_id)` order, so 26484 gets required specialists on 6 of its 66
     units, and 34906 on 3 of its 39.
   - `_ONCE_PER_PR` gives a 49-introduction PR one duplication job.
6. **`naming_norm`'s bars.**
   - `established` (0.80) fires on 3 of 560 validation theorems.
   - The `emerging` tier's 3× margin, set at exactly 33337's 21 to 7, carries 22 of the 25 rename
     verdicts the tool gives on validation.
   - The AI stratum gets 0 of 74.
   - Owned by the live naming branches; not touched here.
7. **Intent keywords** (`components.py:48-57`).
   - They are about 4-in-5 precise on both sets, so they are not worse on validation.
   - But "further golfs with Claude and Codex" on 34906 puts **70 uncapped required golf and idiom
     rows** on a 39-unit AI PR.
   - "I don't think it makes sense to add deprecations" matches `deprecat`.

**Fine or inert.**

- **Fine on validation's features:**
  - the per-job budget and cost hints (validation units are smaller);
  - the run caps, which are restated per set;
  - prompt sizes (nothing is omitted);
  - skeleton and family truncation;
  - the file-grain threshold.
- **Inert:** `MAX_INTENT_REQUIRED_PER_PR`, `DEFAULT_CENTRAL_RANK`, the `proof_profile` grant
  (never granted by any config) and the arm `finding_budget`.
- **small12 cannot test size.** It excludes PRs over 8 units by construction, so items 1, 3 and 5
  can only be read on the full 60.

## 4. Proposal

Two tracks. The first is hygiene, whatever the division. The second is the re-division itself,
and it needs a measurement before any of it is adopted.

### Track A — free, and right whatever the division (moves text, not the design)

1. **Take the dev strings out of tool schemas and developer docstrings.** Rewrite the four examples
   (`base.py:481`, `context_tools.py:617`, `:180`, `:484-488`) and strip the run anecdotes from the
   served pydantic docstrings. Then extend the contamination gate to sweep served schemas, match
   namespaced forms, carry a dev-vocabulary denylist, and drop `to_fun` from its allow-list. Land it
   at a run boundary, with the tool-schema hash that `framework-defects-2026-09.md` already asks for.
2. **Remove the two contradictions that touch every call.** Render only the arm's own checklist
   item in a specialist's user prompt, and describe every scheduled arm to the lead in one dev-free
   line each. That second change is where the registry rationales finally become model-visible.
3. **Fix the packer charge and add a whitespace filter** (Part 3 items 1 and 2). This is scheduling
   hygiene: it removes 138 plus 85 units of text that no prompt carries or no maintainer would
   review. It moves release identities, so it is a new renderer version, not an edit.

### Track B — re-divide by the families the validation asks fall into

The arms, as they would stand, with the validation counts that justify each change:

| proposed arm | built from | validation asks it would own | justification |
|---|---|---|---|
| `proof` | `proof_golf` + `proof_idiom` merged | F1: 22 asks, 11 PRs | 7 asks split between the two on both readers' labels; idiom is the primary owner of 2. Keep the verified edit; drop the dev tactic list for "a standard tactic or an existing lemma". |
| `interface` (new) | `style`'s binder bullets, plus the registration questions no arm asks | F2 + F3: **22 asks, 13 PRs** | Binders, implicitness, instance arguments and section `variable`s (12, 9 explicit today under `style`), plus whether a declaration should carry `simp`/`gcongr`/`grind`/`simps`/`aesop`, at what scope and priority, and whether a `nolint` is justified (10, **none owned today**). One question: how does this declaration present itself to users and to automation? |
| `library_fit` | `duplication` + `api_reuse` + `family_design`'s generated-form and dual bullets | F4 + F5: 10 asks, 9 PRs | `api_reuse` owns 0 validation asks and `duplication` 3. The derive-don't-restate asks (`simps` twice, `to_dual`, a structure's projections) are the same question as "this already exists": the library can already produce it. Removed declarations (deprecated aliases) come here. |
| `design` | `generality` + `family_design`'s group questions + the API-design questions | F6 + F7: **11 asks, 10 PRs** | The canonical form, an ext-shaped lemma, extracting a definition, missing basic API, one general lemma, the right generality. Today 7 are owned, and **1** of them explicitly (a weaker typeclass), and `generality`'s "keep the proof" rule forbids most of them. It runs under `verify_edits_if_present`, since a design ask rarely comes with a compiling edit. |
| `docs` | kept, rewritten | F10: 13 asks, 9 PRs | 11 owned, 3 explicit. Drop 33321's shapes, the frequency claim and the linter claim. Name code comments, references, docstring format and a definition's missing docstring (the 67% convention). |
| `formatting` | `style`, narrowed | F9: 8 asks, 6 PRs | Whitespace, indentation, parentheses, import order and redundancy, namespace placement. Drop line length, which Mathlib CI enforces. |
| `pr_level` (new, PR grain) | nothing today | F12: **15 asks, 11 PRs** | Is the change wanted and of library quality; split it; does the description explain the design and link the discussion and related PRs; is there a test; does it coordinate with other work. It needs a PR-level unit: the work-enumeration plan's open question, answered at 14% of asks. 5 of the 15 are on AI PRs, the eventual target. |
| `naming` | kept as is | F8: 3 asks (1 declaration rename) | No new naming investment on validation's evidence. The redesign is `naming-from-statement`'s, and the worked-example fix waits for it. |
| `correctness` | kept, prompt widened to meta code | F11: 3 asks; mathematical correctness 0 on validation, 2 on dev | Compile-first stays: it is rare and blocking, and AI PRs are where axioms appear (33149). Add "does tactic or linter code handle every input form, and is it tested", for the 90 meta-path targets dev never had. |

That is ten arms becoming nine: two merges, one split, one retirement of `api_reuse` and
`family_design` into their families, and two new arms. It is not "more slots"
(`dead-ends.md`, "Specialists as the coverage floor"): the change is *what is asked*, at the grains
the asks live at, which is that entry's reopen condition. Nor is it the unified contract again
(`dead-ends.md`, "The submission contract as the recall lever"): that entry's residual was
design-scale asks no question reaches (4 of 7), which is F6 here.

**It is also work-enumeration's Phase 1, on validation.** The families are a question list derived
from maintainer comments on PRs no design was tuned on. Built as the plan's `q:*` arms (one question
per arm id, the shared template, a verdict per target), each proposed arm above is a small bundle
of those questions. The plan's ≥ 80% coverage gate holds by construction on validation, because
the families were fitted there. Its out-of-sample check is the corpus sample the plan specifies,
plus dev's 48 asks, which the families already cover.

### How it is measured, and what blocks it

- **Validation has no gold yet**, and no reviewed workspaces. `cli plan` refuses both validation
  configs on 60 of 60 and 12 of 12 unbuilt, so no condition can run today. The order is
  `prebuild --reviewed` for small12, then the measurement.
- **Gold-free, and possible as soon as small12 is built:**
  - run control (the current ten arms) and the re-division in fanout, with no lead, so that the
    division is the only difference;
  - three reps each;
  - two blind readers match each run's findings to small12's **31 round-1 asks on 9 PRs**, with this
    audit's rubric.
- **Reading rule, fixed before running.**
  - **Through if** all of these hold:
    - the re-division reaches, on the mean over three reps, **at least 5 more of the 31 asks** than
      control;
    - at least 3 of those are in F2, F3, F6 or F12;
    - the stable set (reached in all three reps) is not smaller than control's;
    - on small12's two PRs with no round-1 feedback (26185, 34935), findings rise by no more than 1
      per rep against control.
  - **Anything less** is read as "this division did not reach more", with the untried designs
    listed, and not as a negative about division.
- **Cost:**
  - small12's lead-shape worst case is $24.05 a rep, and fanout will differ; `cli plan` prices it
    before anything runs;
  - both conditions, three reps each, are six runs;
  - the reader pass is free.

  The full validation set follows only if small12 is through, and it is where the size knobs
  (Part 3, items 1, 3 and 5) can be read.

## Caveats and what this does not settle

- **Model readers, and counts, not rates.** Two readers of one model family, κ 0.91-0.94, and 107
  asks. A family of 3 asks on one PR (F11) is an anecdote, and so is naming's 3.
- **Round-1 raw asks, not gold, and not all rounds.** Later rounds may shift the mix. The gold chain
  may score fewer PR-level asks, and whether it should is a decision the gold has to make.
- **The remits as written, not the arms' behaviour.** An arm can file outside its remit, and the
  generalist files across all of them. Coverage by remit is what a re-division changes; recall is
  what the measurement above reads.
- **The dev baseline is one reader, and it describes one reviewer.** 30 of its 52 events are one
  person's.
- **The family list is the auditor's construction.** It was checked out of sample only against
  dev's 48 asks.

## Record corrections this forces

- **The corpus projection on disk is stale.** `data/pull_requests/projections/corpus/reviewer_view.jsonl`
  was projected on 2026-09-12 with `excluded_scored_prs: 138` and still holds **198 rows on
  test-set PRs**. This was counted by PR number only; no text was read. No code reads the file, but
  two things trust it to exclude scored PRs:
  - the work-enumeration plan's Phase 1 sample, which says "scored PRs already excluded";
  - this todo's own Start-here block.

  Regenerate it on `develop` as its own step. It is a shared data store, so not from a topic branch.
- **The validation release manifest says `"split": "test"`**, the same as the test release. It
  looks carried over from the test build. Nothing gates on `split` today, but check it before
  anything does.
- **Phase 0 of work-enumeration does not carry over.** Its "the question text is not where the
  specialists lose" was measured on the held-out gold, whose asks the briefs were partly written
  from. On validation the explicit share is 40 of 107.

