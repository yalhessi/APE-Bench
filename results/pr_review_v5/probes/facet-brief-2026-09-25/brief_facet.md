# Reviewer brief (condition Y)

Act as a Mathlib maintainer reviewing this PR. Predict the concrete changes a maintainer would
request. There is no quota: a finding needs a present problem and a concrete change. Do not report
checks that passed.

**Skip what CI already settles.** The kernel checks every proof, and the build must pass. CI's
linters settle the following, so do not ask about them:
- whitespace;
- line length;
- `cdot`, `$` and `fun` syntax;
- long files;
- `set_option` misuse;
- docstrings on definitions (`docBlame`);
- simp normal form of `@[simp]` lemmas (`simpNF`);
- unused arguments;
- impossible instances;
- `deprecated` without `since`.

Your job is what no machine checks.

## How to review: object by object, then cell by cell

The **dossier** lists every changed object with its kind and what changed. Work through it object
by object; for the PR as a whole, once. For each object, ask the questions in its row of the table
below. Each question is a *cell*: a thing looked at (the object) compared against something (the
reference). Each cell has its own **warrant**, the evidence that would settle a finding there.

**A finding is admitted only if you meet its cell's warrant:**

| warrant | what you must supply |
|---|---|
| exhibit | the existing declaration or file, found with `mlfind`, `mlgrep` or `mlshow`, with its path |
| count | how the library does it: a count from `mlcount`, or two or more same-shape examples with paths |
| compile | the concrete edit, and why it should still compile (the step the proof no longer needs, the lemma that closes it). You cannot build; say "to verify by compiling". |
| judgment | the consequence for users or for later development, argued in two or three sentences; advisory unless the consequence is severe |

A finding whose warrant you cannot meet is dropped.

### The cells, by object

**A theorem or lemma's statement:**

| reference | question | warrant |
|---|---|---|
| a better version | Can a hypothesis or typeclass be weakened or dropped, or the result stated more generally, for a case users need? Does the proof use every hypothesis? | compile |
| the library | Does it already exist, or follow from an existing lemma in one step? Is it stated with the library's existing predicate or function rather than an unfolded form? | exhibit |
| the norms | Does the name follow the convention for its conclusion? Are the statement's form (canonical predicate, coercion not projection, iff vs one direction) and its binders conventional? | count |
| its siblings | Is it consistent with its siblings in this PR and in its file? Is a dual, symmetric, iff or `_left`/`_right` variant that users will need missing? | exhibit |
| automation | Should it carry `@[simp]`, `gcongr`, `fun_prop`, `norm_cast` or `ext`? Is a `simp` lemma's direction right? | judgment |

**A proof:**

| reference | question | warrant |
|---|---|---|
| a better version | Can it be shorter, more direct, or closed by a standard tactic? Is a step redundant? | compile |
| the library, as a tool | Does an existing lemma close a step the proof does by hand? | compile |
| robustness | Does it abuse definitional unfolding (`rfl`, `show`, `erw` through a definition) or depend on a fragile non-terminal step? | judgment |

**A definition, structure, class or abbreviation.** A definition has no proof that certifies its
generality, so its design questions are judgment, not compile.

| reference | question | warrant |
|---|---|---|
| a better version | Is it encoded well for later proofs: structure or type synonym, bundled or unbundled, `extends` or a field, data or `Prop`? Is it at the useful generality, and would the intended theory still hold there? | judgment |
| the library | Does the library already have this construction or concept, or one it should be built from, or an instance of? | exhibit |
| the typeclass layer | If it supplies instances, should it be `@[reducible]`/`abbrev`? Could its instances create a non-defeq diamond with existing ones? | judgment |
| its API | What basic lemmas does a new notion owe its users, judging by an analogous existing definition: simp lemmas, `ext`, `coe`, `mem` and `apply` lemmas, constructors? | exhibit (the analogous API) |
| the norms | Is it named conventionally (`lowerCamelCase` for data, `UpperCamelCase` for types and props)? | count |
| intent | Does it compute what its name and docstring claim in every case, including junk values? | judgment |

**An instance:**

| reference | question | warrant |
|---|---|---|
| the typeclass layer | Does inference already find it (a redundant shortcut)? Could it create a diamond? Is its priority or scope right? | judgment, or `exhibit` for the existing instance path |
| a better version | Does it hold under weaker hypotheses? | compile |

**The declarations as a group:**

| reference | question | warrant |
|---|---|---|
| its siblings | Do two declarations in the PR say the same thing? Was one fix or one convention applied to some siblings but not all? Should a repeated argument become a lemma? | exhibit |
| the library | Should a dual or additive version be generated (`to_additive`, `to_dual`, `simps`) rather than written out? | exhibit |

**Location:**

| reference | question | warrant |
|---|---|---|
| the module graph | Is each declaration in the file where its subject lives? Are new imports needed, and not heavy? Would a new file be better placed or merged into an existing one? | exhibit (where related material lives) |

**Prose:**

| reference | question | warrant |
|---|---|---|
| intent | Is each docstring, comment and module doc accurate for the code? | judgment |
| the norms | Does it follow documentation conventions: backticks, references, headings? | count |

**The PR as a whole:**

| reference | question | warrant |
|---|---|---|
| process | Is the change wanted and worth having? Is it one thing, or should it be split? Does the description explain the motivation and design, disclose AI use, and link related work? Is new meta code tested? | judgment |

**Removed or renamed declarations:** does each old public name keep a deprecated alias?

## Order of work

1. Read `pr.md`, then `dossier.md`, then `diff.patch`.
2. For each object, go through its rows and use the tools to meet a warrant before you write a
   finding.
3. Prefer the cells no quick reading reaches: the library, siblings, the typeclass layer, API
   and location. They are where maintainers ask most often and reviewers most often stay silent.
