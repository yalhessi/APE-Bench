# The convention census: the principle behind each ask (reader rubric, pre-registered 2026-09-29)

**Why.** `docs/todo/conventions-nature.md`, study 1. We keep assuming Mathlib's conventions can be
written down, and nothing measures how many there are. This reading writes the principle behind
every round-1 ask that maintainers made on 973 validation PRs, in a fixed random order, keeping a
running codebook, so that the accumulation curve says whether review is a hundred conventions or a
thousand, and how much of it is one-off. Two further samples (300 fresh PRs in the same window,
129 PRs from 2024-05..2025-05 and 2026-04..2026-08) are read afterwards against the finished
codebook as the held-out saturation test.

**You are one of two readers.** You keep your own codebook and never see the other reader's. Read
ONLY this rubric, your own `codebook.json`, and the batch file you are given. Do not open anything
else in the directory or the repository, and do not look anything up.

## Unit

One round-1 reviewer comment already judged to be an **ask** (it requests, proposes, or pointedly
questions a change). You do not decide whether it is an ask. Each batch file lists asks in a fixed
order with: `cid`, PR title, `path:line`, kind and author, the agreed review-work family (`F1`
proof, `F2` interface, `F3` registration, `F4` derive-don't-restate, `F5` redundancy, `F6`
statement and API design, `F7` generality, `F8` naming, `F9` formatting, `F10` documentation,
`F11` meta-code correctness, `F12` PR level, `CORR` correctness; `A|B` when the two family readers
split; `-` for the held-out sets, which have no family label), the parent comment when the ask is
a reply, the ask's body, and the diff hunk it is attached to, ending at the commented line.

## What a principle is

A **principle** is one general sentence, with no name, lemma, file or PR-specific detail in it,
such that a reviewer holding that sentence and reading this PR would make this ask. It names a
**situation** and the **form preferred** in it:

- *A lemma whose main hypothesis is a predicate `P x` is named in `P`'s namespace so that it can
  be applied with dot notation.*
- *A goal that a standard finishing tactic closes is closed by that tactic, not by a hand-written
  rewrite chain.*
- *A relation that only serves as the `≤` instance is inlined into the instance, not given its own
  structure.*
- *A definition made with `choose` comes with lemmas exposing its specification.*
- *State a result as an iff when the converse holds.*
- *A structure that extends another is defined directly, not in two stages.*

**The grain.** The family is too coarse ("the proof can be shorter" is `F1`, not a principle).
The instance is too fine ("use `Finset.sum_comm` here" names this PR's fix). The test: **would the
same sentence, applied to a different PR, produce an ask of the same content?** Two asks share a
principle when one such sentence generates both. Tactic and lemma *names* may appear in a
principle only as the name of a general mechanism (`simp`, `omega`, `to_additive`, `@[simp]`,
`Type*`), never as the fix for this PR.

**Not every ask has a principle.** An ask whose content is a fact about this PR alone gets no
principle: a typo, a false statement, a broken build, a wrong or missing hypothesis that is a
mistake rather than a design choice, a question about what the author meant, a reference to an
external discussion. Label these `none` with `none_reason = specific`. An ask you cannot read from
the body, parent and hunk is `none` with `unreadable`. Do not invent a principle to avoid `none`;
a principle that is not a regularity of the library is a wish, and the count is the point.

## The codebook

`codebook.json` is a JSON list of entries you own. Start from what is there (empty on your first
batch). For every ask, in order:

1. If an existing entry's sentence covers the ask **as written**, assign it. Prefer the existing
   entry when it covers the ask without change.
2. If no entry covers it, but an entry you created is one word too narrow (it names `simp` where
   the ask is about `omega`, and the situation and preferred form are otherwise the same), you may
   **broaden that entry's sentence** so it covers both, set `"revised": true` on it, and assign it.
   Never narrow, merge, split or delete an entry, and never change its `id`.
3. Otherwise **create** a new entry with the next id and assign it.

An entry:

```
{"id": "P001", "principle": "<one general sentence: situation, then the preferred form>",
 "rationale": ["<one or two from the list>"], "form": "rule" | "standard", "revised": false}
```

`rationale`, one or two values, the reason the library holds this principle:

| value | the library gains |
|---|---|
| `readability` | a human reads the code more easily |
| `compactness` | less code: shorter proofs, no repetition, nothing unused |
| `maintainability` | the library is easier to change later: deprecation, no reliance on implementation details or accidental defeq |
| `generality` | weakest hypotheses, strongest conclusions, the right level of abstraction |
| `automation` | `simp`, typeclass inference, tactics and generators (`to_additive`, `simps`) work as intended |
| `discoverability` | users find and apply it: names, placement, API shape, docstrings |
| `consistency` | it matches how the library, or the PR's own siblings, do the same thing, whatever the reason |
| `correctness` | the code says what is meant and handles every case |
| `performance` | elaboration or compile time |
| `process` | the PR as a change: description, scope, tests, disclosure, coordination |
| `mathematics` | the mathematically right notion, generality or presentation |

`form`: `rule` when, given the situation, whether code conforms can be checked without judgment
(no `>` in statements; a `Prop`-valued declaration is a `theorem`; every new definition has a
docstring); `standard` when applying it takes judgment (a long proof is split; the statement is at
the right generality; a definition deserves its own name).

## Output

Append to `labels.jsonl` one JSON object per ask, in batch order, with exactly these keys:

- `cid`
- `principle_id`: an entry id, or `"none"`.
- `second_principle_id`: an entry id when the ask plainly makes a second, separable request that a
  different principle generates; otherwise `""`. Create the entry if needed.
- `none_reason`: `"specific"` | `"unreadable"` when `principle_id` is `none`; otherwise `""`.
- `new`: `true` when this ask created the entry in `principle_id`; otherwise `false`.
- `confidence`: `"sure"` | `"unsure"`.
- `note`: at most 20 words; required when `unsure` or `none`, and when you broadened an entry
  (say which).

Write `codebook.json` back with every entry, old and new. Validate: every cid in the batch
present exactly once, every `principle_id` and `second_principle_id` an existing entry id or as
specified, ids consecutive. Then reply only with: the number of asks, the number labelled `none`
(by reason), the number of new entries, the codebook size, and each new entry's id and sentence.

## Reading rules, fixed before reading

- Read the ask, its parent and the hunk only; never the PR's later history, and never the other
  reader's files.
- A reply is labelled on its own content; a reply that restates its parent's request shares its
  principle.
- When an ask states its principle explicitly ("we prefer X because Y"), use that statement's
  generality, not more.
- Counts are reported per reader and as agreed, never averaged. The two codebooks are matched
  afterwards by a third blind reader; agreement is reported as the share of asks whose two ids are
  matched entries, beside the two codebook sizes.

## What is reported, decided before any label

1. **The accumulation curve**: codebook size after each batch of 125 asks, per reader, and per
   family.
2. **Saturation on val1000**: entries created in the last three batches (333 asks) as a share of
   the final codebook; **saturated** if under 5%. Beside it the Good-Turing estimate: entries with
   exactly one ask, divided by asks with a principle, is the probability that the next ask needs a
   new entry.
3. **The held-out test**: entries created over the 1,070 outside asks as a share of the val1000
   codebook. **Saturated** at 10% or under; **not saturated** at 25% or over; in between, the
   curve decides and the verdict is reported as ambiguous.
4. **Concentration**: the share of asks covered by the 10, 25 and 50 most-assigned entries, and the
   share of asks with no principle (`specific`), per family.
5. **Rationale and form**: entries by rationale and by `rule` / `standard`, weighted by asks.

No threshold moves after the labels exist.
