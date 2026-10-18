# Does the library decide the fix? A premise check (2026-10-13, written before any ask is read)

**The premise.** For most asks the free reviewer misses, the maintainer's change is fixed by something
that already existed in Mathlib when the PR was reviewed: a declaration, a lemma tagged for a tactic, a
naming pattern, a deprecation, the file's own pattern. If that holds, knowledge taken from the library
itself is a general lever, and a cheap mechanism probe comes next. If not, it is not, and nothing is
built. This is the check `CLAUDE.md` asks for before a design: a reading of what is on disk, no run.

**The asks** (`asks.jsonl`, 41): every ask of P14 and D12 that no free-reviewer session reached,
on either matcher: DeepSeek alone (3 reps), DeepSeek with the conventions section (3 reps), and
DeepSeek under the filing contract (3 reps). 25 no reviewer of any model reached; 16 a Claude or gpt
session reached (`reached_by`). Each row carries the maintainer's comment, the code it was on, the PR,
the base commit (`base`, the merge-base the PR was reviewed against) and the reviewed head.

## What a reader records per ask

`readings/<batch>.jsonl`, one row per ask:

```
{"ask", "pr", "change": "<the maintainer's change, one line>",
 "determiner": "library|library_partial|judgement|history|unclear",
 "kind": "existing_declaration|tactic|naming_pattern|newer_form|file_pattern|attribute_or_generator|null",
 "artifact": "<declarations / lemmas / files with path:line at the base commit>",
 "commands": ["<the git commands that verified it>"],
 "findable_from_place": "yes|maybe|no", "confidence": "high|medium|low", "note": "<= 40 words"}
```

- **`library`**: an artifact at the base commit, or in the PR's own reviewed code, fixes the change.
  Given that artifact at the place, a reviewer would write the maintainer's change with no further
  choice of taste. Kinds:
  - `existing_declaration`: the PR re-proves, duplicates or should use a declaration that exists.
  - `tactic`: a tactic exists and the lemmas tagged for it cover the goal (name them).
  - `naming_pattern`: at least three declarations of the same shape at the base commit are named the
    asked way, and no competing pattern of similar size exists.
  - `newer_form`: a deprecation or a recent change at the base points to the asked form.
  - `file_pattern`: the same file or its siblings do it the asked way.
  - `attribute_or_generator`: `to_additive`, `to_fun`, `simps`, `mk_iff` and the like do it.
- **`library_partial`**: an artifact points to the change but a real choice remains (competing
  patterns, or the artifact makes the ask plausible without deciding it).
- **`judgement`**: no artifact fixes it; it is the maintainer's preference, design choice or view of
  what is worth having.
- **`history`**: it needs the PR's discussion, linked PRs or issues, or the author's intent.
- **`unclear`**: what was asked cannot be read.

**Rules.**
- An artifact must exist **at the base commit** (or in the PR's reviewed code), verified with
  `git -C data/code_execute/repos/mathlib4/source grep ... <base> -- Mathlib` or
  `git ... show <base>:<path>`. The command goes in `commands`.
- To learn what the maintainer's change finally was, a reader may read the merged commit
  (`git log --oneline --grep='(#<pr>)'`), and must never take an artifact from it or from any commit
  after the base: the merged tree contains the maintainer's change.
- `findable_from_place`: could a reviewer reach the artifact with a query made from words in the code
  at the place, without knowing the answer? Recorded, not a bar; it is the next question, not this one.
- Choose `library` only when the artifact decides the change; when unsure, `library_partial`.

## Reading rule and thresholds, fixed now

Count `library` (strict) over the 41, and separately over the 25 and the 16.
- **28 or more of 41 (two thirds):** knowledge from the library is a general lever for these misses;
  the mechanism probe follows (the free reviewer given the artifact at the place, one prompt per ask,
  read by hand).
- **13 or fewer (a third):** it is not; recorded in `docs/dead-ends.md` with the counts, nothing built.
- **Between:** reported with `library_partial` beside it, and decided with the user.

## Who reads

Four readers, one batch of PRs each, independent, each in its own `tmp/`. Then this session re-reads a
sample of at least ten rows, every low-confidence `library` among them, and reports agreement beside
the counts. One reading, in-sample asks: provisional at the altitude of a premise check.
