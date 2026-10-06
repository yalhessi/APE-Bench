# What each arm did, unit by unit — the family division on the four fanout PRs (2026-09-24)

The user, after `pr5_FD_family_fanout4_rep1` scored 1 of 10 against the ten arms' 3
(`9d36a1e`): *"dig deeper into what each arm did in every unit and decide whether it was on the
right track or not, what went wrong, and how we could have mitigated the issues."*

**Scope.**
- **The run.** 124 jobs, 9 arms, on 4 PRs: 33145, 33337, 33421, and the control 33315.
- **How it was reviewed.** Five read-only reviewers, one or two arms each, labelled every job
  against the code: on track, partly, off track, or correct silence. Each finding was judged
  correct, wrong or trivial, with non-exclusive failure modes, a mitigation and a comparison
  with the ten-arm run (`pr5_V3_contract_fanout4_rep1`) on the same unit.
- **What each reviewer saw.** A per-job dossier: targets, gold obligations and the maintainers'
  round-1 comments, verdicts and reasons, filings with judge votes, V3's arms on the same unit,
  and the tool transcript from `cli trajectory`. They also had the exact rendered prompts, and
  read the base and reviewed code.
- **Checked by the auditor.** Every framework defect below was re-checked in the code.
- **Where the data is.** Labels and summaries are in
  `results/pr_review_v5/adjudications/family-division-fanout4-rep1-review/`.
- **Caveats.** One run, four dev PRs, and one model reviewer per arm, so every count is
  provisional.

## Conclusion first

**The division is not what failed most on this run; shared machinery did.**
- **Two framework defects account for most wrong output, and both affect the ten arms too.**
  A leaf-only name match turns unrelated declarations into "this already exists". An artifact join
  publishes edit-less claims as compile-verified.
- **One gate is miscut for the new `design` arm.** The generalization gate demands a changed
  statement. It refused `design` in 7 of 11 jobs and killed the one gold answer it had compiled.
- **The prompts that remain fail in the same two ways.** They invent "the siblings do X"
  conventions, and they file micro-edits where the maintainer asked for a structural change.
- **Silence was the most reliable behaviour in the run:** 67 of 124 jobs were correctly silent,
  including every job on the control PR except one.

| arm | jobs | on track | partly | off track | correct silence | findings: correct / wrong / trivial |
|---|---|---|---|---|---|---|
| proof | 11 | 0 | 1 | 8 | 2 | 0 / 3 / 11 |
| library_fit | 11 | 1 | 1 | 5 | 4 | 3 / 2 / 1 |
| design | 11 | 0 | 2 | 5 | 4 | 0 / 5 / 0 |
| interface | 13 | 1 | 0 | 5 | 7 | 1 / 6 / 1 |
| formatting | 33 | 0 | 1 | 5 | 27 | 2 / 7 / 1 |
| doc_quality | 19 | 2 | 2 | 5 | 10 | 5 / 2 / 14 |
| naming | 11 | 1 | 2 | 4 | 4 | 3 / 3 / 0 |
| correctness | 11 | 0 | 0 | 3 | 8 | 0 / 4 / 0 |
| pr_level | 4 | 0 | 1 | 2 | 1 | 0 / 0 / 0 |
| **total** | **124** | **5** | **10** | **42** | **67** | **14 / 32 / 28** of 74 |

Most common failure modes, non-exclusive, over the 124 jobs:

| failure mode | jobs |
|---|---|
| false claim | 25 |
| shallow investigation | 23 |
| evidence gap | 21 |
| trivial nit | 16 |
| wrong question | 15 |
| tool misread | 14 |
| unaskable unit | 12 |
| target-grain trap | 9 |
| over-filing | 9 |
| duplicate of another arm | 8 |
| concern-gate mismatch | 7 |
| under-reach | 6 |

## 1. Framework defects, each confirmed in the code

These are not about how the arms are divided. Each reaches every v5 run in the record.

1. **`declares_identifier` matches the leaf name, drops primes, and echoes the query**
   (`src/mathlib_review/evidence/evidence.py:172`, via `declaration_search` in `context_tools.py:333`).
   - **Leaf-only.** The pattern is `theorem [anything.]<leaf>`, and enclosing `namespace` blocks
     are ignored. So `Dense.continuous_inf` matches the root `theorem continuous_inf` in
     `Topology/Order/Lattice.lean`, and `Int.ceil_natCast_add` matches `ENat.ceil_natCast_add`
     in `Floor/Extended.lean`.
   - **Primes dropped.** `searchable_identifiers` strips a trailing `'`, so `Dense.continuous_inf'`
     is searched as `Dense.continuous_inf`.
   - **Query echoed.** The result reports `"declares": <the queried name>`, so the arm reads
     "`Dense.continuous_inf` is declared in Lattice.lean (before this PR)".
   - **Base facts:** no `Dense.continuous_inf` exists anywhere in Mathlib at base, and
     `Extended.lean` declares only `ENat.ceil_natCast_add`.
   - **Effect here:** **12 of the run's 74 findings**, 9 of them published, were false "already
     exists" or "name collision" claims built on it. They came from correctness 4, design 3, proof 2,
     and one each from library_fit, naming and interface.
   - **Effect in V3:** at least 5 more on the same units, from api_reuse, naming, proof_idiom and
     correctness.
   - **Against the arms' own evidence.** In several jobs the arm's own `content_search` and a
     compile contradicted the tool, and it filed anyway.
   - **The evidence collector uses the same function,** so these claims also draw `supports`
     packets.
   - **Correction.** `9d36a1e`'s body says both runs "read moved declarations as duplicates of
     their base copies". That is wrong: none of these declarations was moved, and the tool matched
     different constants.
2. **Verification artifacts join on `(work_unit_id, candidate_ordinal)`** (`review/conditions.py:208`).
   - In v5 several arms review one unit, and each arm's first candidate has ordinal 0. So an arm's
     edit-less candidate inherits another arm's compiled edit and is published as
     `verified_compile`, "the proposed edit recompiled the reviewed file".
   - **Counted:** 7 such findings in this run (6 of them the false claims of defect 1) and 5 in V3.
   - **Collisions:** 12 of this run's 28 join keys, and 16 of V3's 26, are shared by more than one
     artifact.
   - The artifact rows carry no arm or invocation id, so the join cannot be repaired after the fact.
   - Every published-finding count in the v5 record, including the admission-gate audit's, is
     affected.
3. **`lean_verify_edit` with an empty `new_declaration` compiles the unedited file and reports
   success** (`review/base.py:335`: `if declaration_name and new_declaration:` falls through to "compile
   the file unedited").
   - An arm that means to delete a declaration gets a green on code it did not change: 6 calls
     (library_fit 4, design 2).
   - Deletion means three different things in three places. The submission validator refuses it;
     `splice_declaration` documents it as a deletion; this tool silently ignores it.
4. **Smaller tool defects, shared by all arms:**
   - `content_search` returns `[]` for a pattern that spans lines, and two arms read that as
     support.
   - In declaration mode, `lean_verify_edit` places a new docstring after the existing one, so the
     edit fails to parse; this forced retries in 8 `doc_quality` jobs.
   - A compiled edit carrying a linter warning counts as verified, though Mathlib's CI would reject
     it (2 jobs).
   - `declaration_search` does not index `meta def`.

## 2. Contract and gate problems

- **The generalization statement gate is miscut for `design`.**
  - `design` declares `generalization`, whose gate requires the target's statement to change. But
    its remit includes deriving a lemma from its counterpart and extracting a helper, and neither
    changes the target's statement.
  - Refused in 7 of 11 jobs (12 refused calls); the ten arms had 1 such refusal in total.
  - **It killed the gold answer.** In `28601c8d` the arm compiled the order-dual proof of
    `Dense.continuous_inf'` (gold 7fef913e). The gate refused it, and the arm flipped to `no_issue`,
    although the refusal said "resubmit the same candidate without `proposed_edit` … accepted and
    recorded as unverified".
  - **It stopped nothing false.** The gate reads only `proposed_edit`, so no-edit and patch-set asks
    skip it, and design's false no-edit claims were published.
- **One concern per arm.** The contract forces the arm's single concern: the defect already
  recorded in `docs/todo/specialist-arm-contents.md`, item 5. It pushed duplicate-shaped asks under
  the wrong label (proof 7f4540ff and 4a8d72b1 filed duplicate claims as `proof-golf`). A
  `design` finding that is really duplicated reasoning could not declare `duplication`, whose gate
  (close the new declaration with the existing one) would have admitted the dual derivation.
- **Per-target verdicts pull `pr_level` down to target grain.**
  - In 3 of 4 jobs it reviewed its targets' docstrings, placement and names, not the PR.
  - On 33421, a 15-file PR, its one job was anchored to a one-line import unit, and it judged "from
    this fragment alone".
  - The PR descriptions of 33337 and 33421 reached every arm as "(unavailable)": the release omits
    a description edited after review started.
- **The publication gate publishes the wrong half.**
  - All 11 published `doc_quality` findings are "this lemma has no docstring" asks, the kind its
    prompt says is not a finding by itself. One of them is false: `ContinuousOn.comp_fract''` has a
    docstring.
  - All 5 correct `doc_quality` wording fixes stayed `diagnostic`.
  - The one 3/3 naming finding was demoted, because an `emerging` verdict has no collector, while
    two 1/3 ones were published. Style-family findings published 0 of 18.
  - Recorded, not acted on: publication is selection, which is parked
    (`docs/todo/publication-rule.md`).

## 3. What each arm did, and how it could have been mitigated

- **`proof`: 0 correct of 14; 11 trivial.**
  - What it filed: tactic swaps (`grind` → `aesop`), `simpa` restyles, single-step inlining, the
    micro-edits its own prompt excludes.
  - What it never asked: prove the inf/lower lemma from the sup/upper one (33145); call the sibling
    in `continuous_sup'` instead of re-proving it; extract the repeated `Tendsto (2 * ·)` argument
    (33421).
  - V3's proof arms did better on all four 33145 units, with the dual prompt text the audit removed.
  - **Mitigate:**
    - refuse a proof rewrite whose claim does not say what it saves;
    - ask first whether a proof repeats a sibling's or its dual's argument, and put dual pairs in
      one unit;
    - add a whole-unit pass for repeated arguments.
- **`library_fit`: 3 correct, 2 wrong.**
  - Found `upperBounds_closure` for a hand-written step (1031e8ac), one of the three order-dual
    derivations (28601c8d), and checked deprecated aliases on a rename PR.
  - Its duplication check is mostly name search, and it trusted `declaration_search` over its own
    file reads (730afd5b).
  - It re-filed without an edit an ask the verifier had refused, and that ask was published
    (4a8d72b1).
  - **Mitigate:** defect 1; "trust the file when the tool contradicts it"; a compile-refused ask may
    not return without an edit; completing a left/right family is not duplication.
- **`design`: 0 correct, 5 wrong; 3 of them published false blocking claims (defect 1).**
  - It missed all three asks in its remit: generalize `2` to `k` with `1 < k` (55f65304), a general
    lemma for the repeated `Tendsto` step (38e72250), and turn the iSup/iInf equalities around
    (c9a216b7). The last one has empty `change_ids`, so no unit ever carries it.
  - **Mitigate:**
    - a gate that fits the remit: let the arm declare `duplication` for derivations, or gate only
      edits that claim generalization;
    - a verdict may not flip from `issue` to `no_issue` after a refusal;
    - prompt items for constants that should be parameters and for repeated `have` blocks;
    - defect 1.
- **`interface`: 1 correct, 6 wrong; silence 7 of 7.**
  - Four of its eight filings claimed sibling binder inconsistencies that do not exist: the six
    new `Dense.*` headers are identical.
  - Its one sound ask is the new kind the audit wanted: `@[fun_prop]` on `continuousAt_fract`.
  - It missed the real registration gap: the new `continuousAt_floor` has `@[fun_prop]` and its new
    twin `continuousAt_ceil` does not.
  - **Mitigate:**
    - refuse a sibling claim that does not quote the siblings' lines verbatim;
    - add a twin-attribute rule: a declaration and its dual or twin carry the same automation
      attributes;
    - keep renames and proof edits out of this arm.
- **`formatting`: 0 correct in its remit; 27 of 33 correct silences.**
  - Every filing rested on an invented convention: docstring rewraps where the siblings break the
    same way, a blank line read as after a docstring when it is before, and a private import made
    public, which is visibility, not layout.
  - It cost $0.54 on units that only change comments or follow a rename.
  - **Mitigate:**
    - quote two same-shape lines with line numbers for any "the file does X" claim;
    - an empty multi-line `content_search` is not evidence;
    - skip units that only change comments or follow a rename.
- **`doc_quality`: 5 correct, 2 wrong, 14 trivial.**
  - The correct ones are real prose fixes, all unpublished.
  - It over-filed "no docstring" (11 findings, all published), and made the control PR's one
    finding: a "broken" reference to `MonomialOrder/DegLex.lean`, a file that exists. The PR had
    just fixed the path, and the arm read an empty content search as "no file".
  - **Mitigate:**
    - restore the old docs prompt's statistic (8% of theorems, 67% of definitions carry a
      docstring) with "a rename creates no docstring obligation";
    - refuse a broken-reference claim that does not cite a failed `file_read` of the path;
    - "accurate prose is `no_issue`".
- **`naming`: 3 correct, 3 wrong; right exactly when `naming_norm` answered.**
  - `naming_norm` gave 3 usable verdicts in 40 calls; 25 were `subject_unresolved`, on `⨆`/`⨅`,
    `⌈⌉`, `ContinuousAt` and `Tendsto`.
  - It asked for 3 of the 9 renames maintainers wanted.
  - **Mitigate:**
    - subject resolution for those heads;
    - siblings the same PR adds are not evidence;
    - a prefix verdict never clears a prime or a suffix.

    Owned by `naming-from-statement`; coordinate.
- **`correctness`: 0 correct, 4 wrong; 8 correct silences.** All four filings are defect 1's false
  collisions, filed although its own compile had passed. **Mitigate:** defect 1; "a name clash is a
  build error: with `compiles: true`, do not claim one without quoting the error".
- **`pr_level`: nothing filed; 1 clean job (the control).**
  - Pulled down to target grain in 3 of 4 jobs.
  - On 33337 it endorsed the `coe_` names the maintainer changed.
  - **Mitigate:** one PR-level verdict instead of per-target ones; a PR-wide summary listing every
    changed declaration and group hint; the description, or an explicit "missing".

## 4. Scheduling and targets

- **Unchanged declarations become targets.** The PR wrapped a block in `section Ring`, so the
  unchanged `ContinuousOn.comp_fract''` became a target that three arms reviewed. A declaration
  whose own text did not change should be context, not a target.
- **Dual pairs are split across units.** 33145's sup/inf pairs fall in three units (730afd5b,
  7f4540ff, 28601c8d), so no job sees both halves of a pair. Per-target verdicts never pose a
  question about a pair or a group.
- **Some units have nothing to ask.** Comment-only and rename-only units draw every arm. About $1
  over the division went to units where nothing could be asked.
- **Judge.** A gold item that bundles a rename with a dual proof scores a correct proof half 1/3.
  The false claim on `Dense.continuous_sup'` scored 1/3 against 8d887ce4.

## 5. What this changes

- **The 1-versus-3 comparison was confounded.** Before any comparison between divisions is read,
  defects 1-3 should be fixed: they fall on both arms of the comparison. Beside the dev-fitted text
  the audit already named, the family division also paid for a gate miscut for its `design` arm.
  The cleanest next reading is the two divisions again, after the fixes, on the validation set.
- **Mitigations ranked by jobs they would have fixed across all arms:**
  1. **Fix `declares_identifier`.** Match the qualified name, keep primes, and report the name found
     with its `file:line` (12 findings here, 9 published; at least 5 in V3).
  2. **Key verification artifacts by invocation.** An edit-less claim is never `verified_compile`
     (7 here, 5 in V3).
  3. **Evidence rules in the prompts.** A claim that the file or the siblings do X quotes the lines;
     an empty multi-line search is not evidence (about 10 jobs across formatting and interface).
  4. **Fit the gate to the remit** for `design`, let every arm declare its registered concerns, and
     keep an ask alive through a refusal (7 design jobs).
  5. **Reject micro-rewrites, and ask the structural question first.** Is this a sibling's or its
     dual's argument? Should a constant be a parameter? Should a repeated step be a lemma? (proof 6,
     design 3).
  6. **Give `pr_level` a PR-level verdict and a PR summary** (3 jobs), and give arms the
     description, or a statement that it is missing.
  7. **Treat an empty `new_declaration` as a deletion** (6 false greens).
  8. **Skip comment-only and rename-only units** for the arms that have nothing to ask there (about
     $1 a run).
- **The re-division's premise is untouched.** This run cannot reach the validation families
  missing from dev: registration, PR level and API design. `interface`'s `@[fun_prop]` ask shows
  that the first of those gets asked once an arm's remit names it.
