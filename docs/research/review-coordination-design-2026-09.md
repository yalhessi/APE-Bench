# Coordination as a reading protocol: one PR model, perspectives that construct, passes that enrich it (2026-09-29)

**Status.** A design, checked against labelled asks. No code, no run, no spend. Written for
`docs/todo/review-coordination-design.md`; the check labels are in
`results/pr_review_v5/adjudications/coordination-design-check-2026-09-29/`.

The user (2026-09-29):

> *"Having overfocused work units isn't optimal, but the principled design is to come up with a way
> to chain context together. A per-PR pass seemed useful but didn't move the needle. It seems like
> coordination should be helpful, but we haven't reached a compelling design. We keep coming up
> with messy designs that fit the datapoint we directly consider rather than a design principled
> enough to be robust to other proof engineering datapoints and capture something the maintainers
> do."*

**The guard, applied throughout.** Every element below is justified by one of three sources: the
software-inspection literature on how readers find defects, the compiler pattern of passes over one
representation, or what a merged Mathlib declaration is *for*. The labelled asks appear only in §6,
as the check. Where an element would also have been suggested by a miss, the miss is named in the
check and not in the derivation.

---

## 1. What coordination has to share, and what it has shared so far

The pipeline has tried three kinds of coordination. What each shared is the reason it did what it did.

| design | what was shared | result | source |
|---|---|---|---|
| lead + arms (`lead` mode) | the lead sees each job's `JobOutcome.summary()` (counts, cost, claims cut to 800 chars); an arm sees its brief and nothing about its siblings (`CoordinationPolicy.sibling_view = "none"`, the only value implemented) | the lead pruned the arm holding the question in 25 of 42 held-out obligation-rep misses; fanout showed the pruned arms file nothing anyway, 7 of 7 | `review/coordination.py`; `routing-remit-and-silence.md`; `dead-ends.md` "Specialists as the coverage floor" |
| a whole-PR reader (`solo`; the facet brief Y; the hard-cells job H) | a second reader's **findings**, unioned with the first's | Y: 26→32 / 27→28 reached with 7 losses; H's gain was one PR; X′ (a second run of the same brief) gained as much as H on four of five PRs | `facet-brief-probe-2026-09.md` rounds 1–2 |
| a PR-level brief (P) | the questions about the PR as a change, asked once | the one replicated positive: 13–14 of 21 PR-level asks against 6–9, stable at 0.85 across runs | round 3 |

And two facts about what the pipeline computes and then does not share:

- **The change graph, relations, families and units are built and never reach a reviewer.**
  `agenda/components.py` computes `site / introduction / family / file / migration / pr_intent`
  components from `PRRelation` edges (`name_family`, `changed_siblings`, `declaration_dependency`,
  `direct_use_of_changed_declaration`, `repeated_implementation_shape`,
  `possible_wrapper_or_replacement`). A component reaches the lead as a `routing_reason` and a
  `component_grain` on a proposal (`agenda.py:432`), and nothing else: `render_focused.py` has no
  family context, so an arm reviewing one member of a six-lemma family is not told the other five
  exist. The unit it holds is a hash-ordered 24,000-character pack (`work_units.py:21`).
- **The lead already holds the right discipline for sharing, and applies it to the wrong thing.**
  `InvestigationBrief` (`lead.py`) frames everything as a question with `because`, `look_at`,
  `already_checked` and `abstain_if`, on the stated ground that "a specialist handed a conclusion
  will confirm it". That is the rule for sharing hypotheses. It is applied to routing rationales;
  it has never been applied to a model of the PR.

So the failure of the whole-PR pass is specific: it added a reader and unioned findings. Findings
are the one thing readers should not share, because a shared finding is confirmed rather than
established. What readers can share is **facts about the PR** (what it contains, how its parts
relate, what exists in the library near it, how the area writes such things) and **constructions**
(an artifact built from the PR that either compiles or does not). This document is the design of
that shared object and of the readers that fill and use it.

## 2. Sources

### 2.1 Perspective-based and scenario-based reading

Basili, Green, Laitenberger, Lanubile, Shull, Sørumgård and Zelkowitz, "The empirical investigation
of perspective-based reading", *Empirical Software Engineering* 1(2), 1996, and Porter, Votta and
Basili, "Comparing detection methods for software requirements inspections: a replicated
experiment", *IEEE TSE* 21(6), 1995. In both, a reviewer is not given a checklist but a
**perspective and a procedure**: the tester writes test cases from the document, the user writes
the use scenarios, the designer writes the design abstractions. Defects show up as **obstacles to
the construction**: a requirement one cannot write a test for is ambiguous; one cannot write the
user's scenario if a case is missing. Measured against ad hoc and checklist reading, the
scenario/perspective readers found more defects as a team, each perspective found more of the
defects its construction was aimed at, and no fewer of the others. Laitenberger later replicated
the effect on **code** documents against checklists.

Two things in that literature matter for this design, and one caveat.

- **The mechanism is construction, not attention.** A checklist says "check for missing API";
  the perspective says "write a client of this API" and the missing lemma is the line the client
  cannot write. This is what "generate alternatives and compare" is in principled form, and it is
  why the remaining misses (`remaining-misses-kind.md`) are described there as "deltas between the
  PR and an alternative the reviewer constructs".
- **Perspectives are consumers.** PBR's three are the people who will consume the document. For a
  library, the consumers of a merged declaration are known (§4).
- **Caveat.** Regnell, Runeson and Thelin ("Are the perspectives really different?", *ESE* 5, 2000)
  found in a replication that the perspectives overlapped heavily in what they found. The benefit
  depends on the perspectives constructing **different** things. That is a measurable property
  (which pass produced each ask), and §10 pre-registers it as a test of the design, exactly as the
  proof-trio overlap was measured for the arms (`review-work-structure-2026-09.md` §3).

### 2.2 Passes over one intermediate representation

A compiler does not hand each optimisation a fragment of source and union their outputs. It builds
one representation, and each pass **reads what earlier passes annotated and writes annotations of
its own**; ordering is by dependency (types before optimisation), and a later pass asks a question
of the representation ("is this value ever read?") rather than of the text. Three properties carry
over:

- one model, many passes, each enriching it;
- annotations are facts (this compiled, this is used here); a pass never records another pass's
  opinion as a fact;
- the order is fixed by what each pass needs, not by which is easiest.

### 2.3 How maintainers read

Mathlib's own review guide lists its categories "approximately from easiest to hardest: style,
documentation, location, improvements and library integration", and says new reviewers can do the
first two or three while library integration "generally requires several months". That is an order
of **difficulty for the reviewer**, and the guide's own library-integration checks (attributes
applied, rewrite lemmas provided, constructors for new types, generality for known future needs,
`FunLike` and `SetLike` design) are the ones that decide whether the rest of the review stands.

The order this design uses is by **dependency and cost of change**, from
`review-work-structure-2026-09.md` §1.2: a definition's body fixes definitional equality for every
downstream proof and is the most expensive part to change after merge; then binders, statements and
attributes, which every use site depends on; then names; then proofs, which nothing downstream
observes. A review that settles the proofs first and the definition last has reviewed proofs that
will be rewritten. The user's account of skilled maintainers (intent, then definitions, then
statements and API, then proofs, then the file as a whole) is the same order; the design does not
rest on that account, but agrees with it.

### 2.4 Other proof libraries, as the robustness test

Used in §7. The Archive of Formal Proofs' submission criteria are build, no `sorry`/`back`/
`sledgehammer`/`smt_oracle`, `expect` on counterexample calls, indentation by subgoal, no
auto-generated names, attributes only on named lemmas, a ROOT file and a PDF; "most violations" are
caught by the Isabelle linter and design review is not mandated. Mathematical Components'
`CONTRIBUTING.md` gives a naming grammar (`(condition_)?mainSymbol_suffixes`, `A` associativity,
`C` commutativity, `inj` injective), variable-name conventions by type, an 80-column layout, and a
deprecation window of at least one release for any rename or removal.

## 3. The PR model

The model is the object every pass reads and writes. Its contents are derived from the
**reference facet** of a review question (`review-work-structure-2026-09.md` §7.1, reliability
κ 0.86): each reference is something a reviewer compares the PR against, so each is something the
model must hold or be able to construct. The objects are the **object facet** (κ 0.95).

Every entry carries a **provenance tag**, and the tag decides how a later pass may use it:

| tag | meaning | a later pass may |
|---|---|---|
| `fact` | deterministic from the diff, the workspace or the store; or a construction that compiled or failed to | rely on it |
| `construction` | Lean text a pass built, with its compile result and workspace | rely on the compile result; read the text as evidence |
| `hypothesis` | a pass's reading, written in the `InvestigationBrief` form: question, because, look_at, already_checked | treat as a question to answer, never as a premise |

This is the distinction `components.py` already draws between `evidence = "exact"` and
`"hypothesis"` on a family, and the one the lead prompt insists on. It is made uniform here.

### 3.1 Schema

| section | contents | provenance | exists today as |
|---|---|---|---|
| **pr** | number, title, description; the changed files; **intent**: the design move in one or two sentences and the objects it is about; **one thing?**; AI-assistance disclosure; **open-PR overlap**: PRs open at review time touching the same files or declarations | description and files `fact`; intent `hypothesis`; overlap `fact` | `ReviewEpisodeInput`; the lead's `submit_comprehension` writes the intent and discards it; overlap does not exist (the PR store has the PRs, nothing computes it) |
| **objects[]** | every changed object: `change_id`, kind (`SubjectKind`), lifecycle, which components changed (`ModificationComponent`), path, header, base and reviewed text, centrality; **role** (central definition / its API / helper / incidental) | all `fact` except role (`hypothesis`) | `ChangeGraph.targets`, the modification inventory, `components.centrality` |
| **removed[]** | declarations removed or renamed, with their base text and whether a deprecated alias exists | `fact` | in the change graph; no arm can be scheduled on one (`removed-declarations.md`) |
| **families[]** | groups of objects that are one decision: members, evidence (`exact` from `name_family`/`changed_siblings`, `hypothesis` from shared stem), the **twin pattern** the area uses for this shape (sup/inf, left/right, additive, iff, top/bot, ball/closedBall, Pi/Prod, pow/zpow, Injective/Surjective/Bijective), and which twins are present | members `fact`/`hypothesis` as labelled; twin pattern `fact` from a census, presence `fact` | `components._families`; no twin pattern exists |
| **relations[]** | `PRRelation` edges, plus **generated_by** (a `to_additive`/`simps`/`to_dual` attribute that produces one object from another) | `fact` | `release/pr_relations.py`; `generated_by` is readable from attributes and not computed |
| **references, per object** | **library candidates**: the analogue *family* along the decoy axes (direction, dual, strength, bundling, carrier, continuity), from fold search, type search and name search, never one best match; **area regularities**: census rows for this directory (name forms for this conclusion shape, class-vs-hypothesis for this binder, attribute practice of the file's sibling lemmas, section-variable layout); **intent text**: the docstring, the module-doc lines and the description sentence that name it | `fact` (counts and hits), with the census scope stated | fold search is a probe (`fold-search-2026-09-26`); `naming_norm` counts leading tokens only; the area census is the output `conventions-nature.md` owes this design |
| **constructions, per object** | each: kind, Lean text, compile result, workspace, the pass that built it. Kinds: `usage`, `generalised_statement`, `twin`, `derived_proof`, `alternative_proof`, `rewrite_in_idiom`, `name_from_statement`, `docstring_from_code`, `description_from_code` | `construction` | `lean_verify_edit` compiles against a reviewed workspace; nothing records a construction as an artifact of the model |
| **verdicts, per (object, question)** | `issue` / `no_issue` / `cannot_determine`, with the evidence reference | `fact` about what was checked | `target_verdicts` (built, opt-in) |
| **asks[]** | one per decision: the ask, the union of `change_ids` it is about, an optional `patch_set` with anchors, the warrant | | `CandidateSubmission`; `patch_set` with `anchor_problems` (on `develop`) |

### 3.2 What the model is not

- **Not a store of findings.** A pass's asks are output, not input to the next pass. The next pass
  reads the *constructions* and *facts* the earlier pass left. A finding that another pass would
  merely confirm is exactly what `lead.py` warns against.
- **Not a dossier of precedent comments or rule text.** `dead-ends.md` records that precedent
  priming delivered and did not transfer, and that appended guidelines were null at N=115. The
  model carries counts about this area and hits in this library, never quoted comments.
- **Not a selector.** Nothing in it ranks, thresholds or publishes (the user's 2026-09-22 ruling).

## 4. Perspectives and their artifacts

PBR's perspectives are the document's consumers. A merged Mathlib declaration has six
(`review-work-structure-2026-09.md` §1.3, from the life of a declaration in a self-refactoring
monorepo): it is **found**, **used by people**, **used by automation**, **maintained**,
**extended**, and eventually **retired**; and above the declarations, the PR is **accepted** as a
change. Each consumer, asked to do its job on the PR, would produce an artifact. The artifact is the
perspective's construction, and the asks appear as what the construction cannot do.

| perspective (consumer) | constructs | obstacles that become asks | warrant of the construction |
|---|---|---|---|
| **the user** who calls the API by hand | a `usage`: a short downstream lemma or `example` that a client would write with the new declarations, at the generality a client needs | a lemma the client needs and the PR does not provide; binders the client must supply awkwardly; a statement in a form the client must unfold; a missing twin the client reaches for; insufficient generality | compile |
| **automation** (`simp`, `gcongr`, `fun_prop`, `norm_cast`, `ext`, instance inference) | automation's view: `example … := by simp` with and without the new lemma; `#synth` for new instances; the simp-normal form of each side | a lemma automation would use and is not registered for; an instance inference already finds or cannot find; a definition that must be `abbrev` or `@[reducible]` for instances to fire; a non-defeq diamond; a form that is not simp-normal | compile |
| **the maintainer** who will refactor around it | a `rewrite_in_idiom`: each proof re-done the way the library does it: a closer battery, the existing lemma at each step, dot notation, the pre-PR proof replayed under the new statement, the dual derived from its twin, a repeated fragment extracted | a shorter or more idiomatic proof; a step an existing lemma states; a proof duplicated across siblings; a proof that should be a derivation; a fragile step | compile |
| **the next developer** who extends the theory | the `generalised_statement` (the weakest binder telescope that compiles; class-typed hypotheses as instances; a literal made a parameter) and the **family closure** (each twin the area's pattern expects, stated and, where a generator or dual applies, derived) | a hypothesis or typeclass stronger than the proof needs; a twin missing; an inconsistency between siblings; a definition whose encoding the extended theory will fight; a definition that already exists under another concept | compile for statements and instances; **judgment for definitions**, because a definition carries no certificate of its generality (`review-work-structure-2026-09.md` §7.3, 8 of 9 measured) |
| **the finder** who searches, reads and reuses | a `name_from_statement` for each declaration (from its conclusion, subject and namespace, by the area's forms), a `docstring_from_code`, a `description_from_code`, and the place a finder would look for it (the module graph) | a name off the area's form or inconsistent across the family; a docstring or module doc that says something the code does not; a declaration in the wrong file or namespace; heavy or missing imports | count for names and layout; judgment for prose |
| **the gatekeeper** who accepts the change | the PR's story: what it does, why, whether it is one thing, whether it finishes the job at the analogous places, whether removed and renamed declarations leave aliases, whether meta code has tests, whether another open PR does the same, whether AI assistance is disclosed; and whether one decision made in passes 2–5 was applied to all of the objects it applies to | every F12 ask; retirement; consistency across siblings | judgment; exhibit for a duplicate PR or an un-updated analogue |

Two properties of this table are the ones §7.8 of the structure document asked a division to have:

- **Each perspective's construction has one warrant, or one per object kind that is fixed by proof
  irrelevance.** A checklist arm mixes warrants because it mixes questions; a construction cannot,
  because what settles it is whether it compiled. The one split, compile for theorems and judgment
  for definitions, is the same split the relabel measured (`variant` on proofs 88 compile / 8
  judgment; on definitions 1 / 8).
- **The perspectives differ in what they build**, which is Regnell's condition. Where two would
  build the same thing (the maintainer's alternative proof and the developer's generalisation are
  both variants that compile) they are separated by object: proofs to one, statements to the other.

## 5. The passes: a reading protocol

A pass is one perspective applied to one slice of the model, with the constructions and facts of the
earlier passes in view. The order is §2.3's: dependency and cost of change.

| # | pass | perspective | unit of work | reads from earlier passes | constructs | writes to the model | one LLM job per |
|---|---|---|---|---|---|---|---|
| 0 | **build** | none; deterministic | the PR | — | — | objects, removed, families (members and twin pattern), relations, library candidates, area regularities, open-PR overlap | — (no model call) |
| 1 | **intent** | gatekeeper, first half | the PR | pass 0 | the `description_from_code`: what the diff does, in the reviewer's words, before reading the author's | intent, roles, "one thing?", the questions to establish | PR |
| 2 | **definitions and the typeclass layer** | next developer; automation | each definition, structure, class or instance with the instances it supplies | roles; library candidates by concept; the area's encoding norms | the encoding alternatives; `#synth` paths; the API an analogous definition carries, as a list | the definition's verdicts; the **API owed** list for pass 3; instance facts | definition group |
| 3 | **statements and the family** | user; next developer; automation (registration) | each family, or a singleton statement | roles; API owed; twin pattern; library candidates by shape; binder and form norms for the area | the `usage`; the `generalised_statement` per member; each missing `twin` stated; registration checks (`simp` with and without) | family verdicts; twins that compiled; generalisations that compiled; form and binder facts; registration facts | family |
| 4 | **proofs** | maintainer | each proof, grouped by family | the twins and derivations pass 3 found (so "derive the inf from the sup" is a construction, not an idea); relations `repeated_implementation_shape`; library candidates as tools | the closer battery; old-proof replay; `derived_proof` via dual or generator; repeated fragment extracted; dot-notation rewrite | alternative proofs that compiled | proof group |
| 5 | **names, prose, layout, location** | finder | each file | the final statements (a generalised or re-formed statement is renamed with it); the family (a rename is one decision across it); area name forms | `name_from_statement` per declaration; `docstring_from_code`; the module graph's place for each object | naming, prose and location verdicts | file |
| 6 | **the change** | gatekeeper, second half | the PR | everything: all verdicts, constructions, removed declarations, open-PR overlap, analogues the library candidates revealed | the PR's story; the **consistency question**: for each decision in passes 2–5, the siblings it was not applied to | F12 asks; retirement asks; consistency asks | PR |

### 5.1 The three chaining rules

1. **Facts and constructions flow forward; findings do not.** Pass 4 sees that pass 3 compiled the
   dual statement. It does not see "pass 3 thinks the dual is missing". If it wants that judgment
   it re-derives it from the construction.
2. **A hypothesis is passed only as a question**, in the `InvestigationBrief` form, and the pass
   that receives it answers it with a verdict. This is the rule the lead already states for its
   briefs, made the rule for the model.
3. **Every applicable object receives every pass and returns a verdict per question.** No pruning
   between passes: the lead's pruning lost obligations and, when the pruned arms were run, they
   filed nothing (`dead-ends.md`, "Specialists as the coverage floor"), so the lever was never
   which arms ran but what each was asked to build. `no_issue` and `cannot_determine` are legal
   verdicts, as `target_verdicts` already makes them.

### 5.2 The unit of work is the maintainers' grain

On val1000, 24% of agreed asks needed more than one declaration in view (declaration group 133,
file 68, PR 162 of 1,511 with an agreed grain), and in the outside reading the PR's own siblings are
the largest class of comparison asks, 29 of 99. The pipeline's unit has never been any of those: it
is a hash-ordered pack of one file's targets up to 24,000 characters. Passes 3 and 4 take the
**family** as their unit and pass 5 the **file**; pass 2 a definition with its instances; passes 1
and 6 the PR. The family is `components.py`'s existing grain, with its `exact`/`hypothesis` label
kept.

### 5.3 What a pass emits

A pass returns per-(object, question) verdicts and asks. An ask is **one finding per decision**,
anchored on the union of `change_ids` it is about; a fix that spans declarations goes as a
`patch_set` with an anchor per edit, through the channel `coordinated-emission-2026-09.md` built.
Nothing is merged, ranked or suppressed afterwards: if two passes reach the same decision, both
asks are filed and the judge's pairing handles it, as today. That keeps the design on the generator
side of the user's ruling.

### 5.4 What the lead becomes

The lead stops routing among arms and becomes the **owner of the model and the sequencer of
passes**: it runs pass 1, hands each later pass its slice of the model with the prior passes'
facts, and may add questions (rule 2) to a later pass's brief from what it has read. It prunes
nothing. This is the `sibling_view = "blackboard"` value that `CoordinationPolicy` already names
and `assert_implemented` refuses: "an append-only artifact the coordinator owns, with children
receiving read-only snapshots through their next brief". The model is that artifact. Its bounds
are computable before the run: `max_rounds` is the number of passes, and `max_jobs` is
`1 + D + F + P + files + 1` from pass 0's counts, which is what preflight needs.

### 5.5 Cost shape

Jobs are `(pass × group)`, not `(arm × unit)`. For a PR with `D` definition groups, `F` families
(singletons included) and `P` proof groups, the count is `2 + D + F + P + files`. That is of the
same order as the lead runs' job counts on the same PRs, because units and families are both
roughly the declarations of one file; the pass jobs carry more context (the model slice) and one
construction each. `cli plan` prices it before anything is spent; the run name carries the pass
set and the model version, or resume would silently reuse the wrong run.

## 6. The check against the labelled asks

The labels are one reader's (the author's), made after the design was written and recorded with
the design; they carry no κ and are planning labels, as `finding_mechanism.jsonl` is. The two-reader
artifact labelling is `remaining-misses-kind.md`'s study and stays open.

### 6.1 The population: which pass is expected to produce which asks

From the facet relabel's reference × object cross-tab (`facet-relabel-val1000-v1/results.json`,
`exploratory_reference_by_object`; 516 asks where both readers agree on both facets):

| pass | cells | asks | share |
|---|---|---|---|
| 2 definitions and typeclass | variant/definition 10, variant/instance 5, library/definition 6, library/instance 2, norms/definition 4, mechanism/instance 4, mechanism/definition 2, siblings/instance 2, siblings/definition 1, intent/definition 2 | 38 | 7% |
| 3 statements and the family | variant/statement 14, variant/family 16, variant/binders 3, library/statement 16, library/family 5, norms/statement 5, norms/binders 6, norms/family 7, norms/attributes 1, siblings/family 23, mechanism/attributes 16, mechanism/statement 3, mechanism/family 1, process/family 1, intent/family 1 | 118 | 23% |
| 4 proofs | variant/proof 98, library/proof 19, norms/proof 9, siblings/proof 3, mechanism/proof 2 | 131 | 25% |
| 5 names, prose, layout, location | norms/name 48, norms/layout 38, norms/prose 23, norms/location 3, variant/prose 16, variant/layout 3, variant/name 3, library/prose 5, library/name 2, intent/prose 28, intent/name 2, module_graph/location 14, siblings/prose 2, siblings/layout 2, siblings/location 1, siblings/name 1, mechanism/layout 1 | 192 | 37% |
| 6 the change | process/pr 25, process/prose 1, intent/pr 2, norms/pr 1 | 29 | 6% |
| meta code (a program, reviewed as one; not a pass of its own here) | variant/meta 2, library/meta 2, mechanism/meta 2, intent/meta 2 | 8 | 2% |

Every cell lands in a pass, which a six-way partition of objects guarantees and which therefore
shows little. What the table does show is **where the constructions are**: passes 3 and 4 hold 48%
of asks and every compile-warranted construction; pass 5 holds the largest share and is the least
changed by this design (its arms exist; what changes is that names are constructed from statements
and renamed as a family).

### 6.2 The sibling asks: 31 agreed `design_siblings` asks from the outside reading

`design-comparison-outside-v1`, both readers agree on the label; findable by `pr_internal` on 59 of
62 reader labels. By the construction that would have produced each:

| construction | asks | pass |
|---|---|---|
| the family closure states a twin the pattern expects (AlgHom of RingHom, comap of map, zpow of pow, injective/bijective of surjective, eball/closedBall of ball, isClosed of isOpen, top of bot, right of left, prod of pi, Injective of Mono, refl and trans of symm, iff of one direction, `_eq_one` of `_eq_zero`) | 19 | 3 |
| a statement in the PR is subsumed by, duplicates or is generated from another of the PR's (a special case of the preceding lemma; two constructors; a `simps` twin of a hand-written lemma; an equiv subsuming two lemmas; a redundant lemma) | 5 | 3 (one, duplicate constructors, pass 2) |
| an inconsistency between siblings (`Nat.card` against the other statements' spelling; a strict-implicit binder on one ext lemma and not its twin; universe parameters fixed on one, a typeclass on its dual) | 3 | 3 |
| a proof repeated at each use site, or a left version that should be derived from the right via `OrderDual`, or a subproof duplicating the PR's own lemma; trace versions via `to_additive` | 4 | 4 (three), 3 (`to_additive` at the family) |

Twenty-seven of 31 land in pass 3 and need only the family read together with its twin pattern; none
needs the library. No current job can produce them: the family arm filed 0 candidates in 182
responses, and no arm is shown its unit's siblings.

### 6.3 The 38 misses of both sets

`miss-warrants-2026-09-26/misses.jsonl`, labelled by pass in
`coordination-design-check-2026-09-29/pass_labels.jsonl`:

| pass | misses | of which the closer battery or its siblings already produced mechanically |
|---|---|---|
| 2 | 2 (drop `noncomputable`; a predicate used as a `Set`) | 1 |
| 3 | 14 (class-typed hypotheses as instances ×3; section variables ×2; registration by the file's pattern ×4; the missing dual and the sup/inf pair ×2; two generalisations; the Parseval duplicate at the statement) | 5 |
| 4 | 11 (three closers; old-proof replay ×2; a one-liner from a lemma 40 lines up; dot-notation rewrite; a `simp` tail; a repeated fragment; two proof ideas) | 5 |
| 5 | 9 (four names; a hypothesis name; a namespace placement; a line length; a module-doc note; a hyphenation the maintainer withdrew) | 0 |
| 6 | 2 (interaction with another PR; record the agreed plan) | 0 |

Passes 3 and 4 hold 25 of 38 misses (66%) against 48% of the population's asks. That is the
direction `remaining-misses-kind.md` predicts: the misses over-index on the questions answered by
constructing an alternative. Of the 14 misses whose `battery` field carries a result, 11 were
produced: eight outright, one with the proof's own lemmas, two by name or shape rather than by
unification (`ea224ef`, `finding_mechanism.jsonl`); all 11 sit in passes 2–4. So for passes 3 and 4
the claim that the construction surfaces the ask without a reviewer noticing anything is already
partly measured.
Passes 5 and 6 hold the misses that are counts, judgments or information gaps, and this design
changes little there beyond the open-PR overlap.

### 6.4 The PR level

Pass 6 is the PR-level brief the probes measured: about twice the PR-level asks the current brief
reaches, stably (round 3). F12 is 6% of asks and 16% on AI-authored PRs, the project's target.

### 6.5 What this check cannot show

- A partition of objects into six passes covers every ask by construction. The check that matters
  is whether the **construction** produces the ask: measured for 11 of 14 in passes 2–4, unmeasured
  for the `usage`, `twin` and `name_from_statement` constructions. That measurement is
  `remaining-misses-kind.md`'s "three misses by hand" and comes before any build.
- Whether the passes are **disjoint** in what they find (§2.1's caveat) is only measurable from a
  run: which pass produced each judged hit. §10 pre-registers the threshold.
- The share of asks a pass holds is not the share of *recall* it would add. Pass 5 holds 37% of
  asks and the pipeline already reaches many of them.

## 7. Robustness: the same protocol on two other libraries

The design's claim is that the *structure* (consumers → perspectives → constructions → passes)
transfers, and only the *content* of pass 0 (an area's regularities and twin patterns) is
per-library and mined. Read against §2.4:

- **The Archive of Formal Proofs** is an archive, not a monorepo library. Its entries have few
  human callers, no automation that must use them, and no theory developers extending them; they
  are maintained against new Isabelle releases by the editors. Under this design passes 2–4 nearly
  empty, and the review is pass 5 (style, mostly linted: indentation, generated names, attributes
  on unnamed lemmas) and pass 6 (metadata, no `sorry`, `expect` parameters, a PDF). That is what the
  AFP's criteria are, and the AFP does not mandate design review.
- **Mathematical Components** has the consumers Mathlib has. Its naming grammar
  (`mainSymbol_suffixes`, `C` for commutativity, `inj` for injective) is pass 5's
  `name_from_statement` made almost mechanical, its variable conventions by type are pass 0
  regularities, and its deprecation window for renames is pass 6's retirement question.

So the protocol predicts, for a library whose review practice we have not fitted to, which passes
carry weight and which of pass 0's regularities must be mined. Neither library is a measurement
here; they are the test that no element of the design names a Mathlib PR.

## 8. What this design refuses, and the dead ends it touches

- **Another reader** (`solo`, Y, H): refused; findings are not shared (§1).
- **Sibling propagation as a post-processor** (`dead-ends.md`, superseded): refused as a
  post-processor. Consistency is a *question* in pass 6 over the model's decisions and families,
  answered with a verdict, not a copy of a finding to its siblings.
- **Precedent priming and guideline injection**: refused; the model carries counts and hits, not
  comments or rule text.
- **Facet-keyed review join**: not used; families come from the change graph's relations.
- **Selection**: nothing here ranks or publishes; §5.3.
- **The submission contract as the recall lever**: kept as the pass output form
  (`target_verdicts`, `verify_edits_if_present`), not relied on to move recall.
- **A no-pruning run on the twelve held-out PRs** (ruled out 2026-09-23): not proposed; the
  measurement is on validation small12 (§10).
- **Route by problem class (D1)** and **review-level coherence (D5)** of
  `pr-review-v5-principled-design.md`: D1's three classes are three of the eight references the
  model holds; D5's propagation pass is pass 6's consistency question. Both are absorbed, not
  re-derived.
- **`work-enumeration`'s question list**: its `q:*` arms (planned, not built) are the finest
  bundling of questions; a pass is a bundle of questions that share a construction and a grain.
  The two are compatible, and a pass job can be carried by that mechanism (§9).

## 9. What is built, what is not, and the minimal native path

**Built and reusable:** `ChangeGraph`, the modification inventory, `components.py` (families with
`exact`/`hypothesis`), `PRRelation` (six kinds including `repeated_implementation_shape`),
`centrality`, `submit_comprehension`, `InvestigationBrief`, `target_verdicts`,
`verify_edits_if_present`, `patch_set` with `anchor_problems` (on `develop`), reviewed workspaces
for compiling constructions, `context_by_invocation` on `render_focused` (a per-invocation text
slot nothing fills with family context), `CoordinationPolicy.sibling_view = "blackboard"` as a
refused value with its three-file implementation note, the `cli tool` workbench, the fold search
and closer battery as probes, `naming_norm` (prefix only), the PR-level arm with its "Everything
this PR changes" list (`arm-division`, unmerged).

**Not built:** the model as an artifact; pass sequencing (the lead runs waves of arms); family-grain
jobs; the twin pattern census; the area census (`conventions-nature.md`); open-PR overlap from the
store; `name_from_statement` (`naming-from-statement.md`); the `usage` construction; binder sweep
and old-proof replay as tools rather than probe scripts.

**The minimal native path, in the order the primitives allow:**

1. The model as a sealed artifact under the run (`.ape/runs/<run>/model/<pr>.json`), built by pass 0
   from the primitives above; `sibling_view = "blackboard"` implemented as its rendering into
   `context_by_invocation` and the brief, closing `assert_implemented`'s refusal.
2. Family-grain invocations: `enumerate_invocations` over `family` and `file` components, so a job's
   `change_ids` are the family's. `anchor_problems` already confines edits to claimed anchors.
3. Passes as arms with a construction step, scheduled in `rules` mode in the fixed order, each pass's
   jobs reading the model slice and the earlier passes' constructions; one shared prompt template
   per pass, the perspective and its construction as the text. Verdict per (object, question).
4. Pass 0's two censuses (twin patterns; the area's forms) as `naming_norm`-shaped operators.

None of this is a new runner, budget, cache or result store.

## 10. The measurement, stated before any run

**Before building (free, the probe method):** the `remaining-misses-kind.md` demonstration.
Construct the model by hand for three validation small12 PRs holding misses labelled pass 3 or 4,
run passes 3 and 4 by hand through `cli tool` against the reviewed workspaces, two runs each, two
blind matchers, the reviewer-cutoff caveat stated. **Threshold:** the constructions produce at
least 3 of those PRs' unreached validation asks in both runs, with the compiled artifact as the
evidence. Fewer, and the design is written into `dead-ends.md` with the untried constructions
listed.

**After building (paid, small):** validation small12 minus 30714, the PRs
`pr5_val_small12_minus30714_lead_rep1` reviewed (8 of 30 asks reached, $6.78) and the solo
baseline (2 of 30, $1.20). Three reps, reported as mean / union / stable, found and published
side by side, control emission beside them. **Thresholds, pre-set:** asks reached ≥ 14 of 30 on
the union of three reps; at least 4 of the gains in passes 3 and 4; findings per PR no more than
the lead run's; cost within 2× the lead run per rep. **Disjointness (Regnell):** if two passes
produce more than half of each other's judged hits, they are one pass and are merged before any
further run.

## 11. Risks

- **Designing from the datapoints anyway.** The derivation names no PR; the check does. The
  places where a miss would have suggested the same element are the `OrderDual` derivation (pass
  4, from the generator/twin structure of pass 3) and the family grain (from the maintainers'
  measured grain). Both have a source that is not the miss; a reader who finds an element with no
  such source should strike it.
- **The area census does not exist.** Pass 0's regularities are the output `conventions-nature.md`
  owes. Until it exists, pass 5 and the norm cells of pass 3 run on `naming_norm`'s prefix count
  and the model's own knowledge, which is today's state.
- **Constructions cost compiles.** A family closure that states and compiles three twins is three
  compiles against a reviewed workspace (2.4–16.6 min to build, seconds to check). The plan step
  bounds it; the per-job cap is `ExecutionLimits`, one object, as always.
- **The reviewer model may have seen the validation PRs** (`facet-brief-probe-2026-09.md`,
  caveat). Between-design comparisons on one model stand; absolute reach does not. The test set
  stays closed until the design has passed on validation.
- **Perspectives may not be different enough.** §10's disjointness threshold is the guard.

## Sources

- Basili, Green, Laitenberger, Lanubile, Shull, Sørumgård, Zelkowitz. The empirical investigation
  of Perspective-Based Reading. *Empirical Software Engineering* 1(2):133–164, 1996.
  <https://link.springer.com/article/10.1007/BF00368702>
- Porter, Votta, Basili. Comparing detection methods for software requirements inspections: a
  replicated experiment. *IEEE TSE* 21(6):563–575, 1995. <https://dl.acm.org/doi/abs/10.1109/32.391380>
- Regnell, Runeson, Thelin. Are the perspectives really different? Further experimentation on
  scenario-based reading of requirements. *Empirical Software Engineering* 5(4), 2000.
  <https://link.springer.com/article/10.1023/A:1009848320066>
- Laitenberger et al. An internally replicated quasi-experimental comparison of checklist and
  perspective-based reading of code documents. *IEEE TSE* 27(5), 2001.
- Mathlib PR review guide. <https://leanprover-community.github.io/contribute/pr-review.html>
- Archive of Formal Proofs, submission guidelines. <https://www.isa-afp.org/submission/>
- Mathematical Components, `CONTRIBUTING.md`.
  <https://github.com/math-comp/math-comp/blob/master/CONTRIBUTING.md>
- In this repository: `docs/research/review-work-structure-2026-09.md` (§1.2, §1.3, §7);
  `docs/research/facet-brief-probe-2026-09.md`; `docs/research/coordinated-emission-2026-09.md`;
  `docs/research/unified-contract-fanout4-2026-09.md`;
  `results/pr_review_v5/adjudications/{facet-relabel-val1000-v1, design-comparison-outside-v1,
  miss-warrants-2026-09-26}`; `src/mathlib_review/review/coordination.py`;
  `src/mathlib_review/agenda/components.py`; `src/ape/tasks/lean_tasks/formal_math/review/lead.py`.
