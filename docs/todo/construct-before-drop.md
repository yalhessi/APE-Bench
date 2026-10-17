# Construct and check before dropping a named concern

**Status** — open (written 2026-10-17 from manual trace inspection; nothing built, nothing run)
**Cost** — no spend: the free reviewer on `first`, one rep of the 26 ask-reading PRs (about 35 min a run); Lean
compiles of 5-10 s each inside the sessions

**Motivating example.** The free reviewer's misses are mostly concerns it named and dropped, not facts it lacked:
of 66 asks missed in some solo session, 35 lacked nothing and 14 lacked only the belief that maintainers enforce
it here (`probes/ask-reading-2026-10-12`). At the proof golfs the dropped candidate was never compiled, and it was
wrong:
- PR 33285, `Submodule.inf_comap_le_comap_add` (ask d0035): the reviewer wrote "Could be golfed further to
  `simpa only [...] using add_mem h.1 h.2`? Hmm. Not a finding." Compiled against the base workspace
  (2026-10-17, `scratchpad/ap/probe_d0035`): the reviewer's candidate fails (`h` never introduced), a natural
  second try fails (type mismatch), the maintainer's one-line term compiles in 5 s. Three solo sessions, none ran
  `lean_verify_edit` there, though each ran it about six times elsewhere (454 calls in 78 sessions).
- PR 32875, two `simp only [this]; exact ...` blocks (asks v0094, v0095): the maintainer's `simpa [this] using ...`
  compiles in 6.5 s in the reviewed workspace; the reviewer's "`rw [this]` would be more idiomatic" compiles but
  is no golf; its other compression fails. Dropped as "a real style point but minor".
Maintainers ask with the fix in hand: 39 of the 93 evaluation asks and 43 of the 56 census finishing-tactic
asks carry a suggestion block. Stage H's checkers, told to construct up to six candidates and compile each,
found a compiling shorter form at 12 open places in 2-8 tool calls each (`probes/stage-h-departures-2026-10-16`,
`checks/`), where the note-free readers had called most of them conforming.

**The hypothesis.** The reviewer's judgement at the place is calibrated like a maintainer who has not worked the
fix out: it half-constructs an alternative and drops it on worth. A harness rule that makes it finish the
construction before it may drop (compile the candidate; for a name, run the norm and precedent search; for a
binder or attribute, the edit) changes what it knows at exactly the places design G reached only partially
(`dead-ends.md`, "reopens if a design changes what the reviewer knows at the partial-only places"). It files
only what verifies and is shorter or consistent, so it is generator-side, not selection, and its volume is
bounded by what the reviewer already names (20-30 named-and-dropped concerns a session against 4-6 filed).

**Ceiling, stated first.** 31 of the 93 asks were named and dropped by some solo session (8 proof golfs, 9
names, 6 interface, 8 other); the proof family holds 20 asks of which solo reaches 8. A full success is about 10
asks; the record's gains have been 2-3. Not reached by this: the 24 asks no condition names (attention, PR
context, design), the questions whose answer is "no" (v0067, v0068, v0105: a verifying reviewer will not file
them and the matcher has no question form), and a newer form the reviewer argues against (the `grind` asks:
the session found the Zulip thread and still filed the opposite).

**What would close it.** Premise check first, no model: for the 8 dropped proof golfs and the 5 dropped
names, compile or search the reviewer's own quoted candidate and the maintainer's fix in the reviewed workspace
(two done above). If the maintainer's fix verifies at 10 or more of the 13 and the reviewer's own at 5 or fewer,
the construction step, not the check, is what is missing, and the rule must allow iteration (up to 6
candidates, as stage H's checkers had) or a closer battery (`review-mechanical-sweeps.md`). Then one free rep
on the 26 PRs with the rule as a harness contract: pre-registered line, full (not partial) reach on at least 8
of the 31 dropped asks on the union of three reps, at most 2.5 findings a control PR; below 5 of 31 it goes to
`dead-ends.md` beside design G.

**Start here.**
- read: `docs/dead-ends.md` (design G, and its untried list); `docs/research/filing-decision-design-2026-10-12.md`
  §10-12; `src/ape/tasks/lean_tasks/formal_math/review/filing_contract.py` (the contract mechanism to extend);
  `probes/ask-reading-2026-10-12/readings/*.jsonl` (`behaviour == "K"`, the quotes name each candidate);
  `probes/closer-battery-2026-09-26/battery.py` (how to compile a one-edit variant with `lake env lean`,
  `-Dexperimental.module=true` on Lean 4.26+ workspaces); `probes/stage-h-departures-2026-10-16/checker_prompt.md`.
- run: `ape/bin/python results/pr_review_v5/probes/ask-reading-2026-10-12/grep_session.py <transcript> <decl>`
  to see a session's reasoning at a place; the compile pattern is in the scratch probes named above.
- bounded by: design G (forced filing without construction: partials, 4.9 a control PR); the precedence
  paragraph and the filing contract (prose does not move the free model; a contract must be enforced); the
  mechanical-sweeps todo (the blind, reviewer-free form, bounded to potential only); selection is refused.

**Evidence** — `probes/ask-reading-2026-10-12/asks_all.tsv`, `readings/`; `docs/questions.md` lines on what the
free reviewer does at the place and on what grounds it drops; stage H `checks/*.jsonl` `calls` and
`compiled_candidates`; the two compile probes (scratch, 2026-10-17).

**Risk** — the reviewer's candidates may fail at most places (d0035), so a one-shot check files nothing and the
step degenerates into the mechanical battery with its volume; the free model may not follow an iteration
contract; the naming half needs a norm the record says is unreadable from the corpus alone.
