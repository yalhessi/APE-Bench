# Where the arms come from: a structure for Mathlib review work (2026-09-25)

The user, after the 1,000-PR replication:

> *"The arms division seems a bit ad hoc. Is there a greater structure to how the arms are decided?
> How can we know we aren't missing an arm or there is duplication in the work? Ultimately this
> should consider the Lean code and the life cycle of a proof development repo such as Mathlib."*

The reading is right.
- **The ten arms** grew from whatever the development PRs contained
  (`pr-review-v5-principled-design.md` §1 says so of the method registry).
- **The family division** (`registry.FAMILY_DIVISION`) was cut from the 60-PR ask counts, one
  family at a time.
- **The twelve families** are themselves the auditor's codebook, fitted on those 60 PRs.

Nothing in that chain says what the review work *is*, so nothing can say an arm is missing.

This document derives the work from three things that the sample does not choose:
- what Lean and Mathlib's CI already check;
- what each part of a declaration is for, given how Lean treats it;
- what happens to a declaration after it merges.

The 1,000 PRs are then used only to weight the structure and to test it. The earlier structural
axis on record, the kind of knowledge an ask needs (convention, repository, local judgment;
`pr-review-v5-principled-design.md` D1), is one of its dimensions.

**Revised the same day (§7), and tested (§7.8).** Grouping by object is not enough, because the same question
("the right generality?", "already present?") recurs across objects. §7 separates five kinds of
similarity between questions and finds that an arm must follow how a question is *answered*, its
reference and warrant, rather than what it looks at. The division in §4 is superseded by §7.6;
the map in §2 stays, as the layer for scheduling and context.

A pre-registered two-reader relabel of 755 asks found that:
- the facets are reliable (κ 0.86-0.95);
- the family division's arms mix how their asks are settled, as `design`'s gate failure did;
- the warrant depends on the reference and the object *together* (85%).

So a submission contract must be chosen per (reference, object) cell. Generality on a theorem is
settled by compiling; on a definition, by judgment.

## 1. Three facts that generate review work

### 1.1 Review is the complement of what the machine checks, and the boundary moves

**What a Mathlib PR has already passed** before any human reads it:
- **The kernel:** every proof proves its statement.
- **The build:** everything compiles.
- **23 syntax linters.** These are the catalogue's "binding 23", covering layout, `cdot`,
  `refine`, long lines and files, and non-terminal `simp` (`flexible`).
- **The environment linters**, run by `lake exe runLinter Mathlib` (Mathlib
  `.github/workflows/build_template.yml`). The ones on by default in Batteries are:
  - `docBlame`: docstrings on definitions;
  - `simpNF`: a simp lemma's left side is in simp normal form;
  - `simpComm`: no commutativity simp lemmas;
  - `unusedArguments`;
  - `impossibleInstance` and `nonClassInstance`;
  - `synTaut`, `checkType` and `unusedHavesSuffices`.

  Mathlib adds `structureInType`, `deprecatedNoSince` and `tacticDocs`.
- **Other checks:** a PR-title check, and the benchmark bot when asked.

**Correction to the convention catalogue.** H6 there says the simp-normal-form linter "is not in
the standard set". That is true of the *syntax* standard set, but `simpNF` runs in CI as an
environment linter. For lemmas tagged `@[simp]`, simp normal form is machine-checked. The
catalogue scanned syntax-linter options only.

So review work is whatever remains. The catalogue's reframing ("the conventions worth
discovering are the complement of what is encodable as a linter") applies to the whole task, not
only to conventions.

**The complement is not fixed.** A convention is born in review, where one maintainer asks. It
matures as the ask repeats, gets written down in a library note or the style guide, gets a linter,
and leaves review. `flexible` took non-terminal `simp` out of review; `deprecatedNoSince` took the
`since` date of a deprecation. So the review task at any moment has two parts:
- **judgment no linter can take:** design, generality, encoding;
- **conventions not yet mechanised:** the `emerging` tier of the norm store (principled design, D2).

A division has to be re-derived when the machine frontier moves. Deriving it from the frontier
makes that re-derivation a mechanical step, not a new audit.

### 1.2 Proof irrelevance ranks a declaration's parts by what depends on them

In Lean, the proof of a theorem is irrelevant: no later declaration can observe it. It can be
rewritten at any time without touching anything downstream. What its review protects is:
- the reader (is it clear and idiomatic);
- the maintainer (is it robust when what it uses is refactored);
- the build (is it fast).

Everything else about a theorem is interface, and every use site depends on it:
- its name;
- its binders (what a user must supply);
- its statement (whether it applies, and in what form);
- its attributes (whether automation uses it).

A definition's body is not irrelevant. It fixes definitional equality, meaning what unfolds, what
computes, and which instance paths agree. Every downstream proof that unfolds it, rewrites with
it or relies on `rfl` depends on it. It is the most expensive thing to change later.

This gives a ranking by the cost of changing a part after merge:

| part | who depends on it | cost of changing later |
|---|---|---|
| theorem proof | nobody downstream | lowest: one declaration |
| prose, layout | readers | low |
| name | every use site and search | a rename, plus a deprecated alias |
| binders, statement, attributes | every use site, human and automated | every use site |
| definition body, instances, class hierarchy | every proof that unfolds or synthesises through it | highest; diamonds can block unrelated work |

**The 1,000 PRs show that reviewers treat these differently.** Of 1,610 inline round-1 asks,
1,472 were joined to the changed declaration they comment on. The join uses the last line of the
comment's diff hunk, matched against the reviewed code
(`results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/provenance/situate.py`; its output is `situated_asks.json` in the directory above).

| | theorems | definitions | instances |
|---|---|---|---|
| changed declarations | 6,983 | 1,641 | 1,090 |
| asks per 100 changed | 12.6 | 13.3 | 11.3 |
| proof asks (F1) | **33%** | **16%** | 28% |
| statement and API design (F6) | **16%** | **28%** | 20% |
| documentation (F10) | 3% | 10% | 6% |
| redundancy (F5) | 4% | 4% | 9% |

Definitions draw as many asks as theorems, but of a different kind. What reviewers ask of a
definition (§2, row 6) is encoding and its place in the typeclass hierarchy, not its proof.

### 1.3 A declaration's life after merge gives each part its consumers

Mathlib is a monorepo that refactors itself continuously. A merged declaration will be:
1. **found**, through its name, docstring, file and namespace;
2. **used by people**, who supply its binders, check its hypotheses and match its form;
3. **used by automation**, through its attributes, the simp normal form of its statement, its
   instance arguments and its reducibility;
4. **maintained** while what it depends on is refactored, so it needs a robust proof, sensible
   imports and a build cost it deserves, and it must be the one place the fact lives;
5. **extended** by the next developers of its theory, who need its API to be complete and its
   encoding to be workable;
6. **retired**: renamed, generalised, deprecated or removed, with downstream users migrated.

Above the declarations, the PR is also a change the maintainers must accept: wanted, scoped,
described and tested. Meta code (tactics, linters, scripts) is a program, not a proof. Its body
is the product, like a definition's, and its review asks what any program review asks: every
input form handled, tests present, errors clear, speed acceptable.

Each review question is a part, asked about on behalf of one of these consumers. Mathlib's own
guide lists its categories "approximately from easiest to hardest": style, documentation,
location, improvements, then library integration, which it says "generally requires months of
mathlib familiarity" (<https://leanprover-community.github.io/contribute/pr-review.html>). That
order is the knowledge axis: an ask answerable from the diff, one needing the library's
conventions, one needing what exists and where, and one needing where the library is going.

## 2. The map: what is reviewed, for whom, from what evidence

One row per object a PR can change, taken from the anatomy of Lean code, not from the asks.

**Column key.**
- **For whom:** the consumers of §1.3.
- **Machine:** what CI already settles.
- **Evidence:** local (the diff), convention (how the library writes it), repository (what exists
  and where), vision (where the theory is going), execution (build time).
- **Families:** the codebook families whose asks land in the row.

| # | object | questions, and for whom | machine | evidence | families |
|---|---|---|---|---|---|
| 1 | theorem proof | clear and idiomatic (readers); robust, not abusing defeq, fast (maintainers, build); steps an existing lemma states (maintainers) | kernel, `flexible`, `maxHeartbeats` | local, convention, repository | F1 |
| 2 | name | conventional and predictable, right terminology (finding); namespace enables dot notation (use) | `dupNamespace` | convention | F8 |
| 3 | binders | explicit or implicit, argument order, section `variable`s (people); instance arguments `{}` or `[]` (automation) | `impossibleInstance`, `unusedArguments`, `unused{Decidable,Fintype}InType` | convention | F2 |
| 4 | statement form | canonical predicate, coercion not projection, simp normal form, iff or one direction (people and automation at use sites) | `simpNF` for `@[simp]` lemmas only | convention | part of F6 |
| 5 | registration | `simp`, `ext`, `gcongr`, `fun_prop`, `norm_cast`, priority, scope; generated twins with `to_additive`, `to_dual`, `simps` (automation) | `simpNF`, `simpComm` | convention, repository | F3, F4 |
| 6 | **definition body and typeclass layer** | encoding (structure or synonym, bundled or unbundled, `extends` or a field, data or `Prop` class), reducibility of instance-supplying definitions, instance scope and priority, non-defeq diamonds, computability, universes; the basic API a new notion owes (every downstream proof, the theory's developers) | `structureInType`, `nonClassInstance` | repository, convention (library notes), vision | parts of F6, F3, F4, F7 |
| 7 | generality and decomposition | weakest hypotheses and typeclasses; extract a reusable intermediate fact or inline a one-use one; the general result the special one follows from (people, the theory's developers) | none | repository, vision | F7, part of F6 |
| 8 | the notion's family | siblings, duals and analogues present and consistent; one decision applied across them (the theory's developers) | none | repository | parts of F6, F8, F3 |
| 9 | library relation and **location** | already exists or derivable (maintainers); the right file, directory and namespace; imports needed, not heavy, and in the right direction; split a file (finding, build) | `longFile`, header and import linters | repository (declarations, module graph) | F5, about 18% of F9 |
| 10 | prose | docstrings, module docs, comments, references (readers) | `docBlame` for definitions, `style.docString` | local, convention | F10 |
| 11 | layout | whitespace, breaks, parentheses, redundant qualification (readers) | most of the 23 syntax linters | local, convention | about 82% of F9 |
| 12 | the change | wanted, one thing, described, AI use disclosed, tested, extended to the other places it applies (maintainers); **retirement**: renames and removals leave deprecated aliases (downstream) | title check, `deprecatedNoSince` | the PR's context, vision | F12, part of F5 |
| 13 | meta code | handles every input, tested, clear errors, fast, documented (users of the tactic) | `tacticDocs` | local, execution | F11 |

**Statement fidelity** runs across rows 4, 6 and 13: does the statement or definition say what
is meant? It is `CORR`: the one question the kernel cannot settle and a reviewer must, rare and
blocking.

**Two questions cut across rows rather than living in one:**
- **Consistency across siblings:** "Have improvements requested for one declaration been applied
  to its counterpart declarations?" It appears in F1, F3, F8 and F12. It is the propagation pass
  of `pr-review-v5-principled-design.md` D5, applied after the rows, not an arm.
- **Retirement:** row 12's second half, under study in `docs/todo/removed-declarations.md`.

## 3. What the map says about the arms we have

### Duplication: one object, three arms

The readers listed *every* arm whose written remit covers an ask. Two arms on one ask is
therefore a measured remit overlap: 208 of the 1,833 asks have two or more owners on both
readers' labels.

| arm | asks owned | owned alone |
|---|---|---|
| `proof_idiom` | 146 | **18%** (115 shared with `proof_golf`) |
| `api_reuse` | 103 | 54% (54 shared with the proof arms, all proof-step asks) |
| `proof_golf` | 380 | 58% |
| every other arm | | 82-92% |

Three arms read row 1 and differ only in the flavour of the question: shorter, more idiomatic,
or through an existing lemma. A maintainer asks one question and makes one edit. The other arms
split cleanly. So the principle is:
- **one object, one arm**, unless two questions about it need different evidence;
- **orthogonal questions are never redundant** (`dead-ends.md`: "the gen checker is redundant
  with golf").

The family division's `proof` merge follows it.

### Gaps: rows no arm owns

| row | the ten | the family division | what the 1,000 PRs say |
|---|---|---|---|
| 6, definitions and the typeclass layer | none | partly: `design` names "encoding", `interface` names "registration" | 123 asks sit on a definition or instance and are design, registration, derivation or generality (F6/F3/F4/F7). That is 6.7% of all asks, more than generality (3.4%) or PR level (6.3%). Read one by one, most are encoding, typeclass or new-API questions; a handful are decomposition (row 7). The four most-cited library notes (`mathlib-convention-catalogue.md`) all sit in this row: reducible non-instances (364), lower instance priority (168), partially-applied ext lemmas (55), implicit instance arguments. So does "diamond instances and definitional equality issues" in Mathlib's guide. |
| 9, location | none | `formatting` has placement within a file, not "which file" | about 38 of 216 formatting asks by one reading, plus location asks filed under F6 and F12 |
| 4, statement form at use sites | none | inside `design`, beside generality | part of F6; its evidence is convention, like rows 2 and 3, not repository |
| 12, retirement | `duplication` names it, but no arm can be scheduled on a removal | the same, through `library_fit` | 912 removed declarations on 21% of PRs; a separate thread |
| 13, meta code | `correctness`, math only | `correctness`, math only, with meta code proposed | 5% of AI-PR asks; 14% of AI-PR targets are on meta paths |

### Mis-cuts: families that are two rows

The codebook's families were fitted to asks. Several of them hold two objects with different
evidence:
- **F9** is layout (row 11: local, mostly linted) plus location (row 9: the module graph).
- **F6** is statement form (row 4), encoding (row 6), decomposition (row 7) and API completeness
  (row 8).
- **F5** is redundancy at introduction (row 9) plus deprecation at retirement (row 12).

A coverage number computed over families therefore hides which half is owned. The 21.4%
unowned share is a statement about the codebook as much as about the arms.

## 4. Principles for dividing, and the division they give (the division is superseded by §7)

*Revised the same day.* Principle 2 and the table below group the work by **object**. The user's
follow-up showed why that is not enough: "right generality" and "already present" are the same
questions on a theorem and on a definition. §7 inspects the kinds of similarity between questions,
and a measured failure (`design`'s gate) shows that an arm's questions must share a warrant, not an
object. Principles 1 and 3-5 stand. Principle 2 and the table are kept as first written, for the
record.

1. **Cover the complement.** Every row, in every column CI does not settle, has an owner.
   Re-derive the division when a linter lands.
2. **One object, one arm, unless the evidence differs.** Two questions about one object that
   need different tools are two arms; two that need the same tools are one. That is why the
   three proof arms become one.
3. **Schedule by the object's change and by what the declaration is.** The inventory already
   records both: which component changed (`proof`, `statement_or_type`, `attributes`,
   `value_or_body`, ...) and the lifecycle event (added, modified, removed). Proof irrelevance
   adds the subject kind: a theorem's proof goes to row 1, and a definition's body goes to row 6,
   never to a golfing arm.
4. **An arm's object fixes its grain:**
   - line or declaration: rows 1-6, 10, 11;
   - family: row 8;
   - file: row 9;
   - PR: row 12.
5. **Name every consumer's question in the prompt.** An arm with one object and several
   consumers asks only the questions it is told to. Row 1's robustness question has not been
   asked by any proof prompt so far.

Applied to the map, these give ten arms. The table marks where each differs from the family
division.

| arm | rows | scheduled on | against the family division |
|---|---|---|---|
| `proof` | 1 | theorem proofs, instance proof fields | unchanged, plus robustness named |
| `naming` | 2 | declarations with an added or changed name | unchanged |
| `interface` | 3, 4, 5 | added or changed binders, statement or attributes | **gains statement form** from `design`: use sites, convention evidence |
| `definitions` | 6 | definitions, structures, classes, instances, abbreviations | **new** |
| `design` | 7, 8 | theorems, and families of them | loses statement form; keeps generality and adds decomposition |
| `library_fit` | 9 | added declarations, files and imports | **gains location** from `formatting`; this is Mathlib's own "Location" category |
| `prose` | 10 | docstrings, module docs, comments | the same as `doc_quality` |
| `layout` | 11 | changed text, except text-only edits | loses location; much of it is linted, so it may shrink to a deterministic pass |
| `correctness` | fidelity, 13 | statements, definitions, meta code | meta code named, as the audit proposed |
| `pr_level` | 12 | once per PR | unchanged; retirement waits for its own thread |

Consistency across siblings runs after the rows as a propagation pass, not as an arm.

## 5. How we know we are not missing an arm, or paying for one twice

Each check below can be re-run, and none depends on a codebook fitted to the sample.

1. **Completeness by construction.** The rows come from Lean's declaration anatomy and the
   columns from a declaration's life after merge. Every non-machine cell must have an owner. A
   new linter removes a cell; a new object kind adds a row.
2. **Triangulation against the maintainers' own guide.** Every category and extra check in
   Mathlib's review guide maps to a row:
   - style → rows 2 and 11;
   - documentation → 10;
   - location → 9;
   - improvements → 1, 6 and 7;
   - library integration → 5, 6, 7 and 8;
   - universes, instance attributes, lemmas for new definitions, diamonds → 6.

   Both divisions miss what maps to rows 6 and 9.
3. **Triangulation against the library notes.** The most-cited design notes, a citation-weighted
   list of what Mathlib wrote down about itself, each map to an owner. Today they all land in
   row 6, which has none.
4. **Measured overlap.** Co-ownership from non-exclusive owner labels, per arm pair (§3). Only
   the proof trio overlaps today.
5. **Evidence cohesion.** List the tools each arm's questions need. An arm needing two disjoint
   tool sets is two arms; two arms needing the same set on the same object are one.
6. **The empirical residual.** Relabel the asks by *facet* (§7: object, reference, mechanism,
   remedy, warrant) instead of by family, with a pre-registered rubric and two readers. The
   unowned share then measures the structure, not a codebook fitted to 60 PRs. NEW asks, meaning
   ones that fit no facet value, say where the map is incomplete.

## 6. What this does not settle

- **The map is the auditor's derivation.** It rests on Lean's semantics, Mathlib's CI and
  Mathlib's written guide, and it is checked against 150 read questions and the situated join.
  It has not yet been checked by a relabel (check 6); that is the next measurement, and it costs
  no model spend beyond readers.
- **Row sizes other than rows 1, 2, 6 and 9 are family counts**, and families straddle rows (§3).
  "About 123" for row 6 and "about 38" for row 9 come from the situated join and from one reading
  of 88 keyword hits. They are estimates, not labels.
- **The situated join covers inline asks only:** 1,472 of 1,610. PR-level and conversation
  comments have no line to join on.
- **Whether a derived division reaches more is still the audit's Track B measurement:** small12,
  fanout, three reps, the fixed reading rule. The map says what to build and how to check its
  coverage, not whether a model filling each remit will find the asks.
- **Readers of one model family** produced every label used here. A human reading of rows 6 and 9
  would outrank them.

## 7. Kinds of similarity between review questions (revision, same day)

The user, on §4:

> *"Many of the arms share different themes. Thinking about definitions and theorems is clearly
> similar. Are both formalized at the right generality, are they already present, etc. So there are
> some similarity in the concerns of these arms even if they are about different objects. But there
> are different types of similarities as well."*

§2 cut the work by object. That fixes what a question looks at, not how it is answered, and two
questions can be alike in one way and unlike in another. This section names the facets a question
has, checks them on a labelled sample, and derives the division from the facet that decides how
an arm works.

### 7.1 The facets of a review question

Each facet's values come from Lean and Mathlib, not from the sample.

- **Object:** what the question looks at, from §2's rows.
- **Reference:** what the object is compared against.

  | code | reference |
  |---|---|
  | `var` | a better variant of itself: weaker hypotheses, a shorter proof, a simpler encoding |
  | `lib` | a specific library declaration: a duplicate, a general version, an existing predicate or construction |
  | `pop` | the library's norms: naming, forms, syntax idioms, layout, spelling |
  | `sib` | its siblings in the PR or family |
  | `mec` | a Lean mechanism's behaviour |
  | `mod` | the module graph |
  | `int` | the author's intent |
  | `pro` | the maintainers' process and vision |

- **Mechanism,** when the reference is one:
  - registration automation (`simp`, `gcongr`, `fun_prop`);
  - generators (`simps`, `to_additive`, `to_dual`, `reassoc`);
  - typeclass inference;
  - definitional equality and reducibility;
  - build and performance.
- **Remedy:** the shape of the fix.
  - a local rewrite;
  - an interface change, which ripples to every use site;
  - delete, then redirect or generate;
  - add declarations;
  - re-encode a definition;
  - move;
  - a PR-level change.
- **Warrant:** what settles the ask.
  - it compiles;
  - an existing declaration is exhibited;
  - a count of the library's population;
  - judgment.

**How this relates to the record.**
- **D1** in `pr-review-v5-principled-design.md` (convention, repository, judgment) is three
  references.
- **`work-enumeration`'s `q:*` arms** are the finest grain: one question per arm. The facets say
  how such questions can be bundled without losing any.
- **Not the `dead-ends.md` "facet-keyed review join".** That joined maintainer requests to
  declarations by the *declaration's* shape, for retrieval. These facets describe the *question*.

### 7.2 A labelled pilot

**The sample.** 155 asks, 12 per family (all 11 for `CORR`), drawn at random from asks where both
readers agree on the family.

**The labelling.** One reader, the auditor, with the facet values fixed before reading. The
labels are in
`results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/facet_pilot.json`.

The sample is stratified, so the counts describe structure, not rates.

**Four findings.**

1. **Most references cross objects.**
   - `pop` spans 9 objects, `var` and `mec` 7 each, `pro` 6, `lib` 4.
   - "A better variant of itself" appears on statements (10), proofs (8), definitions (3),
     instances (2) and families (2).
   - That is the user's observation, measured.
2. **Mechanisms stay on their own objects.**
   - Typeclass inference: instances only (5 of 5).
   - Registration automation: attributes (6 of 7).
   - Generators: families, definitions and the attributes that carry them.
   - The build: the build.
3. **The reference nearly fixes the warrant.**
   - `pop` is settled by a count in 37 of 41.
   - `lib` by exhibiting the declaration in 8 of 8.
   - `int` by judgment in 13 of 13, and `pro` in 14 of 16.
   - `var` compiles in 19 of 27.

   This is partly true by construction, since a library reference is settled by showing the
   declaration. Findings 1, 2 and 4 are not.
4. **The codebook's families are cut on four different axes.**

   | axis | families | how pure |
   |---|---|---|
   | reference | generality (F7) | 12 of 12 `var` |
   | | naming (F8) | 10 of 12 `pop` |
   | | PR level (F12) | 10 of 12 `pro` |
   | mechanism | registration (F3), derivation (F4) | 11 of 12 each |
   | remedy | redundancy (F5) | mostly one remedy (deletion, 9 of 12), from five references: siblings, the library, typeclass inference, the norms, "not worth having" |
   | object | statement and API design (F6) | mixes `lib`, `var`, `sib`, `pro` |
   | | documentation (F10), meta code (F11) | each mixes `int` and `pop` |

   **This is why the division feels ad hoc.** Its categories live on different axes, so no single
   principle can say where a new question goes.

One more observation: 9 of the 11 `CORR` asks are about the build, 8 of them "does the PR build?".
That is on the machine's side of §1.1; the reviewer is reminding the author, not judging.

### 7.3 Five kinds of similarity, and what each should share

1. **Uniform:** the same operation on a structure every declaration has, settled the same way.
   - Every Lean declaration is `name : ∀ binders, type := value`, and a structure adds fields.
   - Generality weakens the binder telescope (hypotheses, typeclass arguments, fields) in the same
     way for a theorem, a definition, an instance and a structure.
   - **But the relabel (§7.8) shows that its warrant is not uniform.** Asks for a better version of
     a proof, a statement or an instance are settled by compiling. On a definition they are
     settled by judgment: 8 of 9.
   - The reason is proof irrelevance again. A theorem's proof certifies that the weaker hypothesis
     still suffices, so recompiling settles the generalisation. A definition carries no
     certificate: a more general definition compiles regardless, and whether the theory still
     holds, and whether the generality is the useful one, is judgment.
   - So the user's generality example is *analogous* (item 2) across theorems and definitions, and
     uniform only among the objects a proof certifies.
   - The measured uniform cases are the library's norms (settled by a count, 90%) and mechanisms
     (settled by compiling, 90%), across objects.

   **These share an arm across objects.**
2. **Analogous:** the same intent, but the object changes the procedure, because what counts as
   "the same" differs.
   - "Already present" for a theorem is a search by type (unification, as in `exact?` or loogle),
     settled by exhibiting the match.
   - For an instance it is inference: `inferInstance` succeeds, which a compile settles. Three of
     the pilot's four instance-redundancy asks were this.
   - For a definition, many definitions share a type, so presence is a question of concept and
     equivalence, settled by judgment.

   **These share an arm and an intent, but the contract must accept a warrant per object,** or it
   will refuse the asks of the objects it was not fitted to.
3. **Mechanistic:** questions that need one Lean subsystem's behaviour, whatever family they were
   filed under. The subsystems are registration automation, the generators, typeclass inference,
   and definitional equality with reducibility. Each binds to specific objects.

   **These share a mechanism arm**, or else that knowledge goes to every arm scheduled on the
   objects that carry it.
4. **Remedial:** different questions with the same fix. Redundancy (F5) is the example: "delete
   it and point to what exists" is reached from five references.

   **These share verification machinery, not an arm.** A redirect must compile at every use site,
   whichever question asked for it.
5. **Positional:** different questions about the same object read the same things: the
   declaration, its uses, its siblings, its nearest library neighbours.

   **These share a dossier built once, not an arm.**

### 7.4 What our runs already show about mixing warrants

- **Grouping by object.** The family division's `design` held variant, sibling and extraction
  questions under one gate, fitted to one warrant: a changed statement that compiles
  (`family-division-fanout4-review-2026-09.md` §2, on `arm-division`). The gate refused asks in 7
  of 11 jobs, turned the gold answer (a compiled order-dual derivation) into `no_issue`, and
  stopped nothing false.
- **Splitting one block by flavour.** The ten's proof trio is the converse: one reference and one
  object split three ways, so 82% of `proof_idiom`'s asks are also `proof_golf`'s (§3).

### 7.5 Principles, revised

1. **A submission contract belongs to a (reference, object) pair, not to an arm.** In the relabel
   the pair predicts the warrant on 85% of asks, against 76% for the reference alone and 74% for
   the object alone (§7.8). One gate must admit every question it is shown. The measured failure
   when it does not is `design`'s gate.
2. **An arm may ask across objects when the intent is shared,** as "the right generality?" is for
   theorems and definitions. It then admits findings with the contract of each pair: compile for a
   theorem's statement, judgment for a definition's encoding. An arm with one contract spans only
   the objects on which that contract holds.
3. **Split a reference by object when its evidence differs by object.** The norms of names (a
   naming census) are not the norms of statements, binders or syntax (the style guide, library
   notes, prevalence).
4. **Mechanism knowledge goes where the mechanism lives:** arms by subsystem, scheduled on the
   objects that carry it.
5. **Objects decide scheduling and context; remedies decide verification.** Neither decides the
   arms. §2's map stays as the scheduling and dossier layer, and §4's principles 3-5 stand.

### 7.6 The division these give (replaces §4's table)

It is derived, not measured. The test comes in §7.7.

| arm | reference | objects | warrant | built from |
|---|---|---|---|---|
| `proof` | variant | proofs | compile | `proof` |
| `generality` | variant, analogous across binders and fields | theorems, definitions, instances, structures | **per object:** compile for statements and instances, judgment for definitions and families | `design`'s generality half, and generality on definitions |
| `library` | library, analogous by object; module graph | theorems (by type), instances (by inference), definitions (by concept); files and imports | **per role:** compile when the library is a tool in a proof, exhibit or compile when it is a precedent for a statement | `library_fit`, `design`'s "existing predicate or construction", location |
| `siblings` | siblings | families, and the PR's analogues | exhibit or compile | `family_design`'s bullets, missing duals and variants, and the propagation pass |
| `naming` | norms of names | names | count | `naming` |
| `form` | norms of statements, binders and syntax | statements, binders, section variables, syntax idioms | count | `interface`'s binder half, `design`'s canonical-form asks, `formatting`'s idioms |
| `prose` | intent and norms of text | docstrings, module docs, comments | advisory, one contract | `doc_quality` |
| `layout` | norms of layout | whitespace, breaks, parentheses | count; mostly linted | `formatting`, narrowed |
| `automation` | mechanism: registration and generators | attributes, families, definitions with `simps` or `to_additive` | compile or judgment | `interface`'s registration half, `library_fit`'s derivation half |
| `typeclass` | mechanism: inference and definitional equality | instances, instance-supplying definitions, classes | compile or judgment | new |
| `correctness` | intent | statements, definitions, meta code | judgment | `correctness`, with meta code named |
| `pr_level` | process and vision | the PR | judgment | `pr_level` |

**Location sits in `library`**, where Mathlib's guide puts it: its "Location" category includes
"whether results already exist". Its evidence, the module graph, differs from the rest of the
arm, so it is the first split to try if `library`'s contract strains.

**Retirement** (`docs/todo/removed-declarations.md`) will enter as an object with its own
references: a variant (the replacement), the library (what supersedes it) and the process (the
deprecation norm). It is not an arm yet.

### 7.7 How to test it before any run

Relabel a pre-registered sample by facet, with two blind readers, and read four things:

1. **Facet reliability.** κ per facet. A facet the readers cannot agree on is no basis for arms.
2. **The pilot's structural claims:**
   - `var`, `lib` and `pop` each span at least 3 objects;
   - each mechanism puts at least 80% of its asks on at most 2 objects;
   - the reference predicts the warrant on at least 80% of asks.
3. **Contract fit per proposed arm.** The share of an arm's asks whose warrant its contract
   admits, computed from labels alone. This is `design`'s gate failure measured before a run, for
   both this division and the family division.
4. **Overlap and residual.** Co-ownership (§3) and asks that no arm owns, under each division.

Only then does Track B, the paid comparison on small12, compare divisions.

### 7.8 The relabel: what held and what did not (2026-09-25)

**How it was run.** Pre-registered in `docs/todo/pipeline-overfit-review.md` (`3492432`), with
the analysis committed before any label (`359dd3f`).
- **The sample:** 755 asks, the 155 pilot asks plus 600 at random.
- **The readers:** two blind Claude readers per batch of 151.
- **Where everything is:**
  `results/pr_review_v5/adjudications/facet-relabel-val1000-v1/`, holding the rubric, both
  readers' labels, `analyse.py` and `results.json`.

Readings are on the 600 random asks.

| | claim | result | verdict |
|---|---|---|---|
| F | the facets are reliable (κ ≥ 0.60 each) | object **0.95**, reference **0.86**, mechanism **0.91** (32 asks), remedy **0.95**, warrant **0.88** | **holds** for every facet |
| S1 | `variant`, `library` and `norms` each reach 3 objects at ≥ 10% | `library` 3 and `norms` 3. `variant` has 1: proofs hold 98 of its 170 asks, and the other nine objects hold 2-16 each. | **fails for `variant`**, by proof dominance at population rates, not by absence of crossing |
| S2 | each mechanism with ≥ 10 asks has ≥ 80% on ≤ 2 objects | registration 93% (15 asks). The other five mechanisms have 1-4 asks each. | **holds where testable.** Mechanism asks are 5% of asks, so the claim is mostly untested. |
| S3 | the reference's modal warrant covers ≥ 80%, pooled | **75.3%**. Norms → count 90%; mechanism → compile 90%; intent → judgment 78%; process → judgment 74%; siblings → judgment 71%; variant → compile 68%; library → compile **55%** | **fails** |
| C | the family division's `design` < 70% warrant purity, and ≥ 2 of its arms < 70% | `design` **48%**. `library_fit` 32%, `interface` 49%, `formatting` 55%, `doc_quality` 58%, `pr_level` 68%; above 70% only `proof` 87% and `naming` 79%. | **holds** |

**The pilot against the readers,** on the 155 pilot asks (κ):

| facet | auditor against each reader | reader against reader |
|---|---|---|
| object | 0.85 | 0.98 |
| reference | 0.72-0.73 | 0.89 |
| remedy | 0.78-0.81 | 0.93 |
| warrant | **0.61-0.62** | 0.89 |

The auditor's warrant labels were the idiosyncratic ones.

**What predicts the warrant (exploratory).** On the 476 random asks where the readers agree on
object, reference, remedy and warrant:

| predictor | modal share |
|---|---|
| reference alone | 76% |
| object alone | 74% |
| remedy alone | 55% |
| reference × object | **85%** |
| reference × remedy | 82% |
| all three | 88% |

Within a reference, the object decides:
- **`variant`:**

  | object | compile | judgment |
  |---|---|---|
  | proofs | 88 | 8 |
  | statements | 11 | 2 |
  | instances | 3 | 1 |
  | definitions | 1 | **8** |
  | families | 5 | 9 |
  | prose | 0 | 16 |

  This is proof irrelevance, measured (§7.3, item 1).
- **`library`:**
  - in a proof it is a tool: "use `X` here", settled by compiling, 18 of 19;
  - for a statement it is a precedent: 6 exhibit and 7 compile of 14;
  - in prose it is a reference: exhibit, 4 of 5.

**Second references (exploratory)** show which comparisons justify each other. Counted over both
readers' labels:
- norms + variant: 60;
- library + variant: 41;
- siblings + variant: 32;
- norms + siblings: 30;
- library + norms: 24.

A "better version" is often justified *by* another reference: the convention, the existing lemma,
the sibling. That is where its warrant comes from when it is not a compile.

**The AI stratum (exploratory, 81 agreed asks against 453 on main):**
- norms 35% against 27%, and process 9% against 5%;
- mechanism 2% against 7%;
- objects: the PR 10% against 4%, definitions 8% against 4%.

These are directions only at this size.

**What it changes.**
1. **The facets are a reliable description of review work.** Every facet agrees at κ ≥ 0.86
   between independent readers. That is as reliable as the families' codebook (κ 0.94 on family),
   and unlike the codebook they were not fitted to a sample. They can replace the families as the
   coordinate system for coverage and for designing arms.
2. **Neither what a question looks at nor what it compares against is enough to group
   questions.** How an ask is settled depends on the pair. So the unit a submission contract can
   serve is a (reference, object) cell (§7.5, principle 1, revised). This answers the user's
   question: generality on theorems and on definitions is one intent, and two contracts.
3. **The gate failure is structural and predictable from labels.** Every family-division arm
   except `proof` and `naming` mixes warrants, and `design`'s 48% is the arm whose gate failed.
   - §7.6's mapping scores 74% against 65%, weighted. But its own gated arms mix too: `library`
     51%, `generality` 63%. Under a single contract they would fail the way `design` did.
   - Purity is harmless for arms whose contract does not gate (advisory prose at 47%). It matters
     for the arms that compile or exhibit.
4. **What to build next follows from 2 and 3:** a gate chosen per cell, by the finding's object
   and reference, not per arm. It must be settled before the next division is run. Otherwise
   Track B measures contracts, not divisions.

### 7.9 What §7 does not settle

- **One reader labelled the pilot:** the auditor, who also designed the facets. The relabel
  measured the cost: the auditor agrees with the readers at κ 0.62 on warrant, against 0.89
  between the readers (§7.8). So the pilot's finding 3 overstated how far the reference fixes the
  warrant.
- **Stratified counts show structure, not how much work each arm would own.**
- **Twelve arms is more jobs per unit than nine.** Whether small arms such as `typeclass` and
  `siblings` stand alone, or become knowledge given to a larger arm, is a cost question that
  principle 1 constrains but does not answer.
