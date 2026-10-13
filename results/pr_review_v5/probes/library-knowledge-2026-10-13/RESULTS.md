# Does the library decide the fix? The result (2026-10-13)

Four readers, 41 asks, every artifact verified at the base commit (`readings/*.jsonl`, with commands).

| | all 41 | no model reached (25) | another model reached (16) |
|---|---|---|---|
| `library`: an artifact decides the change | **7** (5 after the re-check) | 3 | 4 |
| `library_partial`: it points to the change, a choice remains | 19 | 15 | 4 |
| `judgement`: the maintainer's preference or design call | 11 | 5 | 6 |
| `history`: the PR's discussion or the author's intent | 4 | 2 | 2 |

**Verdict by the pre-registered rule: 7 of 41, at most 13, so knowledge taken from the library is not a
general lever for these misses.** Nothing is built on it.

**The re-check** (this session, 11 rows: all seven `library`, four others). Agreed on 9. Two `library`
rows would be `library_partial`: v0092 and v0093, where the simp set makes `simpa` possible but choosing
the shorter proof is style, not something an artifact decides. One check of mine disagreed with reader A
on v0068 because I searched the wrong PR's base; at 30641's own base the `@[gcongr]` lemma for `posLog`
is absent, as the reader said (it arrived later, in #30704).

**What the rows say.** The library rarely settles the maintainer's change by itself (5-7 of 41). Far more
often (19) it holds the ingredients and the maintainer's ask is a choice among them:
- `ciSup` is the library's word, and dropping `continuous_` from the name is the maintainer's call;
- `toLinearMap_` and `coe_` compete;
- `positivity` has the extensions but not the import;
- `grind` exists but the lemmas lack the tag the maintainer adds in the same comment;
- the file's pattern and the library's majority point different ways.

The rest is judgement (11) or history (4). So what decides most of these asks is maintainers' preference
among options the library offers, which the library does not record. Knowledge of that preference can
only come from what maintainers have said, the source the conventions list already uses.

One reading, in-sample asks, single readers with an 11-row re-check: provisional at a premise check's
altitude.
