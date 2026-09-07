# APE-Review

---

## 01 · Motivation — verifiable correctness is not enough

The compiler settles whether a proof is valid. It says nothing about whether the contribution
is any good.

Every PR in our evaluation set **already compiled** when the maintainer reviewed it. What they
asked for instead:

- rename this to match its siblings
- this dual should be derived, not re-proved
- there is an attribute that generates these
- move this out of that namespace

None of that is checkable by construction, and all of it decides whether the work is accepted.
That gap — between *verified* and *acceptable* — is the object of study.


---

## 02 · The frame — three things a review has to get right

Separate skills, separate failure modes, composing in one direction. A system can do the first
perfectly and still produce nothing useful.

**1. Ask the right questions.**
Decompose the diff into review targets, and decide what to ask about each one. Get this wrong
and the rest never runs.

**2. Identify the issue correctly.**
Standing at the right declaration, see what is actually wrong with it. Recognition plus
retrieval: much of what is wrong is only visible against the rest of the library.

**3. Identify the resolution correctly.**
Ask for the change the maintainer would ask for — the right *size* and the right mechanism.
More taste than recognition, and often several coordinated edits rather than one.

---

## 03 · Where it stands — each stage collapses into the next

Two runs over the same four PRs and the same nine obligations. Ranges span the two runs; the
drop between rows is the result.

| stage | | recall |
|---|---|---|
| **1 · Right place** | a prediction lands on the declaration the maintainer commented on | `0.78 – 0.89` |
| **2 · Right issue** | …and says what is actually wrong with it | `0.22 – 0.33` |
| **3 · Right resolution** | …and asks for the change that was actually requested | `0.00 – 0.11` |

- **Mostly** — finding the place is close to solved. Coverage is a scheduling problem, and we
  can schedule.
- **The wall** — naming the issue is where it breaks. Two thirds of the time we are standing on
  the right line with nothing correct to say.
- **Open** — resolution is barely started. One match, ever, on this set.

---

<!-- ## 04 · Part one — asking the right questions

A PR is split into **work units** — a declaration, or a group that has to be judged together.
Each unit is paired with the **questions** worth asking of it: is this named right, is this
proof idiomatic, does this already exist, is this family shaped correctly. A lead agent routes;
a coverage contract sets a floor.

> **30 / 459 specialist questions actually asked.**
> Left to its own judgment, the router asked 7% of the questions available to it. Three question
> types ran **zero times across eleven PRs** — including proof-golf, on a PR whose title is
> literally "golf" and whose maintainer asked for exactly that, twice.

The fix is not a quota. It is that **the PR itself supplies the trigger**: a stated rename puts
every changed declaration in scope for naming; a dualised family gets a family-level look; a
changed module doc gets one documentation pass, not one per docstring.

> Half of what maintainers ask for is not answerable from the changed declaration alone — it is
> about a family, a file, or a library-wide convention. The unit of review is not the line.

---

## 05 · Part two — identifying the issue

Specialised reviewers, each with one question and a retrieval budget: search the library, search
34,640 maintainer review comments, search the Zulip archive, compile a trial edit. They search
plenty — **5.8 searches per invocation**.

They search for the **wrong kind of thing**.

### PR #33117 — thirteen lemmas written by hand

```lean
-- the PR adds, one at a time:
@[fun_prop] lemma neg     (hf : Meromorphic f) : Meromorphic (-f)
@[fun_prop] lemma fun_neg (hf : Meromorphic f) : Meromorphic (fun x ↦ -f x)   -- ←
@[fun_prop] lemma add     (hf : Meromorphic f) (hg : Meromorphic g) : …
@[fun_prop] lemma fun_add (hf : Meromorphic f) (hg : Meromorphic g) : …       -- ←
-- … and eleven more `fun_*` twins

-- what the maintainer asked for:
@[to_fun (attr := fun_prop)]  -- generates `fun_neg` from `neg`
```

`Mathlib/Tactic/ToFun.lean` was sitting in the agent's own workspace, with a docstring saying
exactly this. The reviewer made 44 searches on this PR. Every one was a name lifted out of the
diff — `Meromorphic`, `MeromorphicAt`, `Meromorphic.add`. Not one asked *what mechanism should
have produced this?*

> Retrieval by identifier finds what the code is called. Nothing in the loop retrieves by
> mechanism — and mechanism is what a maintainer knows.

---

## 06 · Part three — identifying the resolution

Same PR, a later run. The reviewer got the issue right, on its own, from the code:

> *"`Meromorphic.fun_neg` restates `Meromorphic.neg` — the functions are definitionally equal.
> Keeping both is duplicated material."*

That is the maintainer's objection. Then it asked to **delete the lemma**, where the maintainer
asked to **generate it**. Right site, right issue, wrong size of change — the characteristic
failure at this stage is under-reaching.

**Taste is not in the corpus.**
On both naming asks we score, the library's own frequencies argue *against* the maintainer —
`coe_` outnumbers the requested form 4,707 to 50. The convention is stated in the review
archive, never in the code.

**One resolution, so far.**
Published and machine-checked: `Dense.continuous_inf'` is `Dense.continuous_sup'` applied to
`αᵒᵈ`. A real dual, correctly derived rather than re-proved.

> Resolutions are usually several coordinated edits — add an attribute here, delete four lemmas
> there. Naming the counterpart earns credit for the issue. It never earns credit for the fix.

--- -->

<!-- ## 07 · Reading — the funnel is the roadmap

- **Part 1** — coverage is tractable. We can decide what to ask and make sure it gets asked.
- **Part 2** — the wall, and it is a **retrieval** wall rather than a reasoning one: the answer
  was in the workspace, unasked for.
- **Part 3** — needs coordinated, verified edits and a source of taste that is not the code.

The measurement itself is young: nine obligations over four PRs, so a single flipped verdict
moves recall eleven points. Treat every number here as a direction, not a score.

---

*Runs: `smoke4-e2e-rep1`, `specialist4-rep1` · release `dev-medium-0.3.0`
9 anchored obligations · 4 PRs · anchor-tier pairing · no control PRs* -->
