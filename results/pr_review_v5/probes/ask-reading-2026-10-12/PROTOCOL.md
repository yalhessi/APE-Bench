# Reading every ask of P14 and D12 against the DeepSeek sessions: the protocol (fixed 2026-10-12, before any reader ran)

**Why.** The user (2026-10-12): *"We need to review every ask in P14 and D12 with the DeepSeek and
DeepSeek + AP runs to try and understand better what goes wrong. We are hypothesizing here about many
directions, and some of them are clearly an improvement over the solo reviewer but the difference they
will deliver on actual PRs is minimal (say 1-2 asks). This is partially because we keep coming up with
designs that are far far too narrow in their nature … We need … a clear general design that encapsulates
as much as possible … a design that clearly navigates knowledge and judgement."*

**The units.** 93 maintainer asks on 26 PRs: D12 (the dev held-out 12, 47 asks), P14 (post-cutoff 6 PRs,
16 asks; validation small12's 8 PRs, 30 asks). Two conditions of the free self-hosted reviewer,
DeepSeek-V4.1-Flash with its thinking kept, three sessions each: **DX** (solo: the standard packet) and
**AP** (the same packet plus a section of about 25 conventions picked from the diff by a blind selector,
each with up to two maintainer comments from other PRs, and a paragraph saying they outrank the reviewer's
own judgement). Outcomes per session come from the one reviewer table's two blind matchers (`reached`,
`partial`, `no`, with a note). The other rows (Opus X/T/OP, Opus + AP = TA, gpt-5.5) are given for
context only; they are not read here.

**What is already known, so the reading does not re-derive it.** Over every ask-free session on disk
a third of the asks is reached by nobody (17 of 46 on P14, 15 of 47 on D12), spread thin across kinds.
Prior readings of residual misses found, repeatedly: the reviewer attends the place and concludes it is
fine, or asks something else there; "knowledge" misses are mostly conventions; a rule plus a check at
the right place was verified and overridden; the conventions that move a reviewer are the ones asserted
as what maintainers ask. The reading below is finer than those: per session, at the place, with the
reviewer's own words, and with a separate column for what knowledge the miss would have needed and where
that knowledge lives. It is read on the DeepSeek sessions because that is the reviewer we can run freely.

## Inputs (all under this directory; `ROOT` is the worktree root)

- `packets/<set>/<pr>.json`: the PR's asks (maintainer text, path:line, family, census entries with their
  principle sentences), per session the matched outcome from both matchers, the finding index and text
  as the matcher saw it, and the matchers' notes; `sessions` with each DeepSeek session's run and
  transcript path and every session's findings as matched; `ap_section` for the delivered conventions.
- `ap_sections/<set>_<pr>.md`: the conventions section every AP session of that PR received (ids
  stripped; the sentences are the census principles, so match an ask's `entries_text` by sentence).
- `families.json`: the family codes. `asks_all.tsv`: the overview (hits of 3 per condition).
- `grep_session.py <transcript> <regex>...`: blocks of a transcript that mention a declaration, a file, a
  word, with line numbers. `show_session.py <transcript> --from L --to L` reads turns; `--submission`
  prints the submitted findings and message.
- Transcripts are Claude-Code-style JSONL: each line a turn; `message.content` blocks of type
  `thinking` (`reasoning_content`, the model's own reasoning), `text`, `tool_use`, `tool_result`.

## The procedure, per ask

Work asks in this order: those no ask-free session on disk reaches (every column 0 in `asks_all.tsv`),
then those where DX and AP differ, then the rest. For each ask:

1. Read the ask (text, place, family, entries). State in one line what the maintainer wanted.
2. For each of the six sessions, from the packet: its outcome (m1/m2) and, if reached or partial, the
   matched finding. A reached session needs nothing more than that line.
3. For each session not reached: find the place in the transcript (`grep_session.py` with the
   declaration name, the file's basename, and one or two words of the ask), read the reasoning around
   the hits and the submission message, and record the **behaviour at the place** (one code) with a
   quote of the decisive reasoning (at most 25 words, with the transcript line number).
4. Record the **knowledge column** and the **AP column** (below), then the **verdict line**.
5. Append the ask's rows to `readings/<batch>.jsonl` and its narrative to `readings/<batch>.md`
   before moving on, so an interrupted reading keeps what was read.

## The codes

**Behaviour at the place** (per session not reached), exactly one:

| code | meaning | evidence that justifies it |
|---|---|---|
| `A` not attended | the session never read or searched the declaration or the region; no reasoning mentions it | no grep hit on the declaration/file region in tool calls or reasoning |
| `C` attended, concluded fine | it read the place and raised no concern of the ask's kind | reasoning reads the place and moves on, or says it is fine |
| `O` attended, asked something else | it filed a different change at the place | a finding at the place of another kind |
| `K` right concern, dropped | the reasoning names the ask's concern or convention and decides not to file | quote the ground (e.g. "maintainers wouldn't", "matter of taste", "the file does the same", "acceptable") |
| `V` checked, read as conforming | it ran a check (compile, search, count) and concluded the code conforms or the fix fails | name the check and what it concluded |
| `E` filed the substance, not matched | the submitted finding states the ask's change or question but the matcher said partial/no | quote the finding |
| `P` partial | the matcher said `partial` | the matcher's note |

**Knowledge column** (per ask, one for DX and one for AP if they differ): the fact the sessions lacked,
if any, and where it lives at the PR's base commit:

| code | meaning |
|---|---|
| `none` | the sessions had what they needed; the miss is judgement, attention or form |
| `mechanism` | a Mathlib tool, attribute, tactic or generator the session did not know or did not think of (name it; e.g. `to_fun`, `mk_iff`, `positivity`, `grind`) |
| `direction` | the maintainer's form is newer than what the corpus or the file mostly does (name the old → new pair) |
| `api` | an analogue, twin or API shape elsewhere in the library the ask compares against (name it) |
| `demand` | the convention or concern was known or stated; what was missing is that maintainers enforce it here |
| `pr_context` | history, intent or discussion outside the packet |
| `construction` | the ask only appears once an alternative is built and compared (a generalisation, a dual, a golf); the session did not build it |
| `unclear` | the ask itself cannot be read from its text and hunk alone |

**AP column** (per AP session): `held` if the ask's convention (by sentence) is in the delivered section,
`absent` if not, `n/a` if the ask is out of census; and when held, what the session did with it:
`used` (filed it), `considered_dropped` (reasoning cites it and drops it; quote), `ignored` (never
mentioned at the place).

**Verdict line** (per ask): one sentence in plain words saying whether this miss is knowledge (what,
where it lives), judgement (which decision, on what ground), attention, or form; and, if the ask was
reached by some session, what that session did differently.

## Output

`readings/<batch>.jsonl`, one row per (ask, session):
```
{"set","pr","ask","family","in_census","entries","session","condition":"DX|AP","m1","m2",
 "behaviour":"A|C|O|K|V|E|P|reached","quote","line","ap":"held|absent|n/a","ap_use":"used|considered_dropped|ignored|null",
 "knowledge":"none|mechanism|direction|api|demand|pr_context|construction|unclear","knowledge_detail"}
```
`readings/<batch>.md`: per ask, at most eight lines: the ask in one line; the six sessions in one line
each (code + quote); the verdict line. Then, at the end, a batch summary: counts by behaviour code and by
knowledge code for DX and AP, the asks where AP held the convention and what happened, and the three
readings the writer found most instructive for the design question (with ask ids).

## Rules

- Read, do not run reviewers: no model spend, no `--execute`, no API call. The helpers and Python over
  the files here are the tools.
- Do not change committed files; write only under `readings/`.
- Quote the session's own words; mark anything inferred as inferred. One reader per batch; the counts
  are provisional and the reader says so.
- Budget: at most about 400k tokens a batch. Work in the stated order and write after each ask; if the
  budget runs out, stop, and the summary names the asks left unread.
