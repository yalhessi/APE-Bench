# Which census conventions are behind each ask? (assign-only reader rubric, fixed 2026-10-04 before any label)

**Why.** A census of Mathlib review conventions exists: `codebook.json`, 438 entries, each one
general sentence naming a situation and the form preferred in it. It was written from asks on other
pull requests. This reading asks, for 46 round-1 maintainer asks on 14 pull requests the census never
read, which entries are behind each ask. The count of asks with no entry is itself a measurement.

**You are one of two readers.** You never see the other reader's output. Read ONLY the three files
in your working directory: this rubric, `codebook.json` and `batch.md`. Do not open anything else,
and do not look anything up.

## Unit

One round-1 reviewer comment already judged to be an **ask** (it requests, proposes, or pointedly
questions a change). You do not decide whether it is an ask. `batch.md` lists the asks in a fixed
order with: `cid`, the PR and its title, `path:line`, kind and author, the review-work family (`F1`
proof, `F2` interface, `F3` registration, `F4` derive-don't-restate, `F5` redundancy, `F6` statement
and API design, `F7` generality, `F8` naming, `F9` formatting, `F10` documentation, `F11` meta-code
correctness, `F12` PR level), the parent comment when the ask is a reply, the ask's body, and the
diff hunk it is attached to, ending at the commented line.

## What an entry is, and when it is behind an ask

An entry is a **principle**: one general sentence, with no name, lemma, file or PR-specific detail,
such that a reviewer holding that sentence and reading this PR would make this ask.

An entry is **behind an ask** when its sentence covers the ask **as written**: the entry's situation
is the situation the ask is about, and the entry's preferred form is what the ask requests. The
test: *would a reviewer who held this sentence, and read this hunk, make this ask?*

- An entry that is only in the same family, or about a neighbouring situation, is not behind the
  ask. Do not stretch an entry to avoid `none`.
- You may not create, broaden, edit, merge or split an entry. The codebook is read-only.

## For every ask, in batch order

1. **Assign** `principle_id`: the entry behind the ask. When several cover it, the most specific.
2. `second_principle_id`: an entry id when the ask plainly makes a second, separable request that a
   different entry is behind, or when a second entry covers the same request equally well;
   otherwise `""`.
3. When no entry is behind it, `principle_id` is `"none"` and `none_reason` is one of:
   - `out_of_census`: the ask has a principle (you could write the general sentence), and no entry
     covers it as written. Put the nearest entry's id in `note` when one is near.
   - `specific`: the ask has no principle. Its content is a fact about this PR alone: a typo, a
     false statement, a broken build, a mistake that is not a design choice, a question about what
     the author meant, a reference to an external discussion.
   - `unreadable`: the ask cannot be read from the body, parent and hunk.

## Output

Write `labels.jsonl` in your working directory: one JSON object per ask, in batch order, with
exactly these keys:

- `cid`
- `principle_id`: an entry id (`P001`..`P438`), or `"none"`.
- `second_principle_id`: an entry id, or `""`. Always `""` when `principle_id` is `"none"`.
- `none_reason`: `"out_of_census"` | `"specific"` | `"unreadable"` when `principle_id` is `"none"`;
  otherwise `""`.
- `confidence`: `"sure"` | `"unsure"`.
- `note`: at most 25 words; required when `unsure` or `none`.

Validate with one short Python check that reads only `batch.md`, `codebook.json` and your
`labels.jsonl`: every cid of the batch present exactly once and in order; every id an entry of the
codebook, or as specified above; `none_reason` set exactly when `principle_id` is `"none"`. Fix any
error and re-check.

Then reply only with: the number of asks labelled, the number assigned an entry, the number with a
second entry, and the number labelled `none` by reason.

## Reading rules, fixed before reading

- Read the ask, its parent and the hunk only; never the PR's later history.
- A reply is labelled on its own content; a reply that restates its parent's request has its
  parent's entry.
- When an ask states its principle explicitly ("we prefer X because Y"), assign the entry that
  states that principle, at that generality.
- Counts are reported per reader and as the union, never averaged.
