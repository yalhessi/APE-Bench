# What reviewing a removed declaration asks, before any arm is built for it

**Status:** open, 2026-09-25, **for a fresh session**. It is its own thread and worktree: a study of
the task, not a build.

**Cost:** free. It reads validation reviews and the structure build; no model calls, beyond
optional readers on validation asks.

**Inputs.** Neither is committed, so rebuild both, from the repo root with
`PYTHONPATH=$PWD:$PWD/src`. The scripts are kept in
`results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/provenance/`:
- `build_structure.py <out_dir>` builds val1000's change graphs, work units and inventory per PR.
  Since `e0c22f9` it should also build the three PRs that reorder imports;
- `extract_draw_feedback.py val1000-2025-06-2026-03-v1 <out.json>` gives the round-1 comments with
  their bodies, and refuses any test-set PR.

The committed `events.jsonl` there has no bodies; its `cid`s match `reader_A` and `reader_B`.

**Motivating example.** No arm can be scheduled on a removed declaration. `_BOTH_LIFECYCLES`
(`agenda/arms.py:89`) admits `added` and `modified` only. Yet removals are common, and reviewers ask
about them:

- **On val1000's structure** (`docs/research/pipeline-overfit-2026-09-replication.md`, §3):
  - 912 removed declarations on 205 of 970 PRs (21%);
  - 44 round-1 asks on 26 PRs mention deprecation, and reader A gives 26 of them no owner;
  - of reader A's 34 unowned redundancy (F5) asks, 28 mention deprecation, renaming or removal.
    That is a keyword match, not a reading.
- **`library_fit`'s remit already asks** "does a rename or removal leave a deprecated alias
  behind?" (`registry.FAMILY_DIVISION`). It can never be scheduled where that question arises.
- **The inventory never emits `renamed`.** A rename arrives as a removal plus an addition. In the
  60-PR audit, 23 of 92 removed declarations were re-added under the same short name, and 36 left
  no trace on any `+` line.
- **The norm is recorded:** convention H10 in `docs/research/mathlib-convention-catalogue.md`,
  "deprecate with `@[deprecated (since := …)]` + `alias`, never a bare delete", over 4,335
  invertible deprecation pairs, 87.5% of them machine-generated.

**The user's framing (2026-09-25).** Reviewing a removal looks much like reviewing an addition. A
declaration cannot be freely deleted from Mathlib: only when it is superseded, or for a good reason.
So understand the task before building an arm that tries to mechanise it.

**What to find out first**, gold-free except where marked:

1. **What removals are.** Classify the 912 from structure alone:
   - a rename (re-added under another name);
   - a move (the same name, another file);
   - superseded (a more general or merged declaration added in the same PR);
   - a true deletion;
   - private or auxiliary code.

   Counts per class, main against AI.
2. **What reviewers ask about each class.** Read val1000's round-1 asks anchored on removal sites,
   meaning `-` lines or the enclosing declaration of a removed one, not only the 44 keyword hits.
   Candidate ask kinds:
   - a missing or wrong deprecated alias, or its `since` date;
   - "why delete this?";
   - "this has downstream users";
   - "keep it as a `simp` lemma";
   - "the replacement is not as general".

   Never read the test set's reviews.
3. **Which part is mechanical.** "A removed public name has no `@[deprecated]` alias in the reviewed
   tree" is close to a deterministic check, like a linter. Private declarations and PR-internal churn
   are exceptions. "Is the removal justified, and does the replacement cover it?" is judgment, and it
   is the added-declaration question pointed backwards: a statement at least as general, reachable
   under a findable name.
4. **Which arm, if any.** The choices:
   - a deterministic check;
   - removals admitted to an existing arm's remit (`library_fit` or `design`), with the removed
     statement shown beside its replacement;
   - `pr_level`, for "should this PR delete this at all";
   - some combination of these.

   Decide from 1-3, not before.

**What would close it:** a class-by-ask table with counts, and a written choice among the options
in 4, with the measurement a built version would have to move. No arm is built before that table
exists.

**Risk:** mechanising the wrong half. A deprecation check is cheap and precise on its own ground,
but it would fire on private and auxiliary lemmas. It also answers none of the "should this go"
asks, which may be the ones that block a merge.
