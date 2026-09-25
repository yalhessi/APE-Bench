# Does the facet framing make a reviewer ask what maintainers ask? An ad hoc probe (2026-09-25)

The user, before any pipeline change:

> *"We have run into the problem of committing to ideas here only to find out several days later
> we weren't able to move the needle. Before we commit to a major change in our pipeline, we need
> to see ad hoc evidence that this framing would indeed result in better reviewing."*

**Answer.** Not as a replacement brief. On five validation PRs, the facet brief did not reach more
maintainer asks overall, by the rule stated before it ran. It moved *which* asks are reached.
- **It gained** exactly the asks the current division cannot reach: definition design and
  PR-level asks. One of them is the most consequential ask on its PR.
- **It lost** local asks the current brief catches: whitespace, binders, proof golf.
- **Some of the losses trace to one instruction in the brief.**

The evidence points to a complement design, not a replacement. That design is untested, and the
next probe below tests it.

## Setup

Everything is in `results/pr_review_v5/probes/facet-brief-2026-09-25/`. The reading rule is in its
`README.md`, written before any reviewer ran.

**Two conditions, one run each, on the same five val1000 PRs:**
- **X, the current generalist brief:** `SYSTEM_PROMPT_V12` plus its 8-item checklist.
- **Y, the facet brief:** the cells and warrants of `review-work-structure-2026-09.md` §7, plus a
  deterministic dossier per PR: each changed object, its kind, what changed, and its siblings.

**What both got:**
- the PR description and the diff at the reviewed head;
- four search tools pinned to the PR's base commit: `mlgrep`, `mlfind`, `mlshow`, `mlcount`.

The local Mathlib clone post-dates the merges, so a leak audit of every transcript checked that
nothing reached it except through the tools. None did.

**The reviewers** were Claude agents, so the model is held fixed but is not the pipeline's
`gpt_5.2`.

**The PRs:**

| PR | what it is | why it is in the sample |
|---|---|---|
| 31984 | `ConvexSpace` | an AI PR; definition design |
| 27099 | the language of Presburger arithmetic | definitions and registration |
| 36275 | a norm on the finite adele ring | 17 asks, mostly API |
| 26308 | normalized vectors | the proof-heavy control |
| 29464 | doc corrections made with an LLM | PR-level asks |

**The reference set** is the 53 round-1 asks that both val1000 readers agree are asks. No reviewer
saw them.

**Matching.** Two independent blind matchers matched findings to asks at issue level. X and Y were
shuffled per PR and stripped of any field that reveals the condition.

## Result

| | matcher 1 | matcher 2 |
|---|---|---|
| asks reached, X / Y | 26 / **32** | 27 / 28 |
| partial, X / Y | 13 / 6 | 9 / 10 |
| gains: Y reached, X did not | 13, 12 of them in F3/F4/F6/F7/F12 | 8, all in F3/F4/F6/F7/F12 |
| losses: X reached, Y did not | **7** | **7** |
| findings, X / Y | 65 / 52 | same |
| **moves the needle** (≥ +4, ≥ 2 gains in unowned families, ≤ 1 loss) | **no** (the losses) | **no** (the difference and the losses) |

**Per PR, asks reached, X → Y:**

| PR | matcher 1 | matcher 2 |
|---|---|---|
| 31984 | 1 → 5 | 1 → 5 |
| 27099 | 5 → 4 | 5 → 4 |
| 36275 | 15 → 11 | 16 → 12 |
| 26308 | 5 → 3 | 5 → 3 |
| 29464 | 0 → 9 | 0 → 4 |

The matchers agree on the direction everywhere. They differ in size on 29464, where one PR-wide
finding ("drop the stylistic churn") is read as reaching many passage-level asks, or only some.

## What was gained

**The central design ask on `ConvexSpace` (31984).** Two maintainers asked the same thing:
- "I don't like quantifying over `Type v` here", with a suggestion to define the operation on
  `FiniteProbability R M` instead;
- "for the definition I think it's easier to use `FiniteProbability X -> X` (more
  monadic-flavoured)";
- and, with the index set gone, `ext` becomes a theorem.

The facet reviewer reached the same design by working through the class's "a better version" cell
(judgment, since a definition carries no certificate of its generality). Its finding:
> "The axiomatisation indexes convex combinations by an arbitrary `ι : Type v` tied to the universe
> of `M` … [propose] the monad-algebra form (convexCombination on `FiniteProbability R M`, with
> map/join assoc)."

The baseline found local issues on the same class, such as `IsStrictOrderedRing` being too strong,
and not the design. Both matchers agree on all four of these gains. This is the kind of blocking
design ask the audit found no arm owns: statement and API design on a definition.

**PR-level asks on the LLM-edited documentation (29464).** The maintainers' asks were that the
changes are "purely stylistic … should be up to the authors" and "we don't have a rule that LaTeX
is preferred".
- **The facet reviewer**, from its process cell, asked to drop the stylistic churn.
- **The baseline** reviewed the edits one by one and asked for the description to separate them.

## What was lost, and why

| lost ask | kind | why |
|---|---|---|
| a missing space after `←` (27099) | layout | the brief's instruction "skip whitespace: CI settles it" is wrong for spacing the whitespace linter does not flag, and maintainers ask anyway |
| a double space before `:=` (36275) | layout | the same |
| an extra blank line (36275) | layout | the same |
| `variable {v} in` (36275) | binders | attention |
| `have` → `let` for a `Fintype` instance (36275, matcher 2) | proof | attention |
| two proof golfs on the control PR (26308) | proof | attention |
| a partial generalisation (36275) | generality | attention |

- **Three of the seven are whitespace.** They are the cost of that one wrong instruction.
- **The rest are attention.** The brief says "prefer the cells no quick reading reaches", and a
  single reviewer with thirteen rows of cells spent its effort there.
- **The warrant discipline also filtered.** The facet reviewer recorded dropping findings it could
  not warrant: a weaker-typeclass point it judged "no case a user needs" (27099), and a rename with
  no count behind it. That took findings from 65 to 52, and some of the drops were asks.

**How the two reasoned.** The facet notes show the procedure working as intended: object by object,
cell by cell, each finding carrying its evidence, and each drop stated with its reason. The
baseline's notes are shorter and look first at local defects.

## What this does and does not show

It shows, at n = 1 run per condition on 5 PRs:
- **The cells the current division cannot reach are reachable when a reviewer is asked for them.**
  On the two PRs where the unowned families dominate, the baseline reached 1 of 8 and 0 of 10; the
  facet reviewer reached 5 of 8, and 4-9 of 10.
- **A single facet brief pays for this with local asks.**

It does not show that the facet framing, built as the pipeline would build it, is better or worse.

**Designs not yet tried:**
1. **The complement.** Keep the current brief unchanged and *add* a job for the cells no quick
   reading reaches: library, definition design, the typeclass layer, API, siblings, PR level.
   This matches §7's conclusion that arms are cells, not one brief.
2. **The same facet brief without the whitespace instruction** and without "prefer the hard
   cells".
3. **Per-cell jobs for the hard cells** (`work-enumeration`'s `q:*` shape), with a gate chosen
   per cell.
4. **The pipeline's own model,** `gpt_5.2`, through `cli run`.

## The next probe, stated before it runs

This is design 1. Two more conditions on the same five PRs and the same tools:
- **X′:** a second run of the current brief.
- **H:** a hard-cells-only facet job, covering only the rows the baseline does not reach, with the
  whitespace instruction removed.

The same two blind matchers score them. The comparison is `X ∪ H` against `X ∪ X′`, the second run
of the current brief being the control: two runs of anything find more than one.

**It supports the complement design if, on both matchers:**
- `X ∪ H` reaches at least 4 more asks than `X ∪ X′`;
- at least 2 of them are in F3, F4, F6, F7 or F12;
- H files no more findings than X′.

The cost is ten reviewer runs and two matcher runs, on Claude.

## Caveats

- **One run per condition.** A difference of 3 or fewer is noise. The trade's direction is
  consistent across PRs and across both matchers; its size is not established.
- **Claude reviewers, not the pipeline's model or its submission contract.** No compile warrant
  could be checked; "to verify by compiling" findings are unverified.
- **The auditor wrote both briefs and chose the PRs.** The PRs were chosen to exercise the new
  cells, so this is a probe of mechanism, not a rate. The matching was blind to condition.
- **Two process deviations:**
  - One facet reviewer (29464) was stopped by an API safeguard error before writing its notes. Its
    findings were already complete, and a resume hit the same error.
  - Matcher 2 listed file names in the probe directory while deleting a helper script. It reports
    opening nothing outside its inputs.

---

## Round 2: a hard-cells job beside the current brief, with the pipeline's own tools (2026-09-25)

**What was run** (the next probe stated above; its rule was restated in
`results/pr_review_v5/probes/complement-2026-09-25/README.md` before any reviewer ran):

**Conditions,** on the same five PRs and 53 asks:
- **X′:** a second run of the current brief.
- **H:** a job for only the cells round 1 showed the current brief missing:
  - the library;
  - definition design;
  - the typeclass layer;
  - a new notion's API;
  - siblings;
  - location;
  - the PR as a whole;
  - retirement.

  A finding a compile can settle must be verified before it is filed.

**Tools.** Both held the pipeline's own review tools through `cli tool` (`07b4dfc`, `e30be07`).
That includes `lean_verify_edit` against each PR's base, built for the probe
(`ape.toolkits.execute.lean.build`, 78 min for five commits). Round 1's X held only `git grep`
wrappers.

**Matching.** Two blind matchers, with X, X′ and H shuffled per PR, matched in one pass each.

**Integrity:**
- **Leak audit:** clean. Every `cat` outside the brief and packet read a reviewer's own temporary
  output.
- **Safeguard failures:** X′ on 31984 failed twice on an API safeguard error with nothing written,
  and completed on the third launch of the identical prompt.

### Result

| | matcher 1 | matcher 2 |
|---|---|---|
| asks reached: X / X′ / H | 26 / 29 / 24 | 25 / 26 / 19 |
| `X ∪ H` against `X ∪ X′` | **41 vs 32** | **39 vs 31** |
| gains; in F3/F4/F6/F7/F12; losses | 11; 10; 2 | 10; 9; 2 |
| findings: H / X′ | 35 / 53 | same |
| **the rule** (≥ +4, ≥ 2 unowned, H ≤ X′ findings) | **holds** | **holds** |

**Per PR, asks reached, X / X′ / H:**

| PR | matcher 1 | matcher 2 |
|---|---|---|
| 31984 | 1 / 4 / 5 | 1 / 4 / 5 |
| 27099 | 5 / 6 / 0 | 5 / 6 / 0 |
| 36275 | 15 / 14 / 7 | 14 / 11 / 4 |
| 26308 | 5 / 5 / 2 | 5 / 5 / 1 |
| 29464 | 0 / 0 / 10 | 0 / 0 / 9 |

### What the pass does and does not mean

**The gain is one PR.**
- **On 29464:** 9-10 of the 10-11 gains are there, where H's one PR-level finding ("revert the
  purely stylistic changes") reaches most of the maintainers' passage-level asks.
- **On the other four PRs:** the complement gained 1 ask (a design ask on 31984) and lost 2 that X′
  found and H did not: a proof golf, and "is there really no way around using `@`?".

The rule was stated as a total and holds as one, but it does not show a broad complement.

**What replicates across both rounds is that single effect.** On the LLM-edited documentation PR
(29464), the current brief reached 0 of 10 asks in both of its runs, X and X′. The briefs that ask
about the PR as a whole reached 4-9 (Y) and 9-10 (H). It is one PR, and the one kind of ask no
current arm owns, `pr_level`. It is also the kind the audit found most common on AI-generated PRs:
16% of their asks.

**Correction to round 1.** Round 1 credited the facet framing with the central `ConvexSpace` design
ask, reached by Y and missed by X. In round 2 the *current* brief reached it too: X′, 4 of 8, by
reading the class's axioms, not by compiling ("Read from the diff"). H reached it as well, 5 of 8.
The same brief reached 1 of 8 in one run and 4 of 8 in another. So round 1's X/Y difference on that
PR was at least partly run-to-run variance. At one run per condition, an issue-level difference on
one PR is not evidence about a brief.

**H on its own is weak outside the PR level:**
- 0 asks on 27099;
- 4-7 of 17 on 36275, against 14-15 for X;
- it missed design asks there that X′ found.

The hard-cells questions do not reliably surface the design asks maintainers make.

### What the tools contributed

This is a regex over each finding's evidence text, so it is indicative only:

| evidence cited | X′ (53 findings) | H (35 findings) |
|---|---|---|
| a compile | 53% | 37% |
| declaration or content search | 47% | 69% |
| Zulip | 4% | 11% |
| precedent search | 4% | 0% |
| `naming_norm` | 6% | 0% |

**Compile turned judgments into checked facts.** H on 31984 used `lean_verify_edit` as a probe, not
only as a check:
- **The universe problem, verified.** A `#check @convexCombo₂` inserted into a compile showed the
  definition silently fixed to `{M : Type}`, and an `example` at `Type 1` failed. The central design
  problem became verified evidence.
- **The weaker typeclass, verified.** `IsStrictOrderedRing → IsOrderedRing` compiled.
- **Unused imports, shown by compiling without them.** Round 1's reviewers had said: "I could not
  show that any import is unused without compiling".

**Compile did not raise reach.** X reached 26/25 asks and X′ 29/26, within run variance. It made
findings verified; it did not make them more numerous.

**Precedent search, Zulip and the naming census rarely supplied a finding's evidence.**

## What the two rounds say about how to proceed

At probe altitude: 5 PRs, one run per condition, Claude reviewers.

1. **A PR-level job is the one change with a replicated effect,** on one PR in two rounds, and it
   targets the AI-generated PRs that are this project's target. The next evidence is breadth: a
   PR-level job on about 10 val1000 PRs with PR-level round-1 asks, stratified AI and main, against
   the current brief. Two runs each, since one run is not enough (point 4).
2. **The other gains claimed for a facet or hard-cells division are within single-run variance.**
   The design asks the facet framing seemed to unlock were reached by the current brief in its
   second run. No arm division should be rebuilt around them on this evidence.
3. **Compile and repository search carry the evidence; precedent search, Zulip and the naming
   census rarely do.**
   - Access to compile raised verification, not reach.
   - Where the arms already hold `lean_verify_edit`, the cheap lever is using it as a probe:
     `#check` a universe, try the weaker typeclass, drop an import. That is a brief change, not new
     machinery.
   - Improving the three retrieval tools is not where the next gain is, on this evidence.
4. **Run-to-run variance is large at the issue level.** The same brief reached 1 and 4 of 8 on one
   PR. Every future probe needs at least two runs per condition, or a comparison against a second
   run of the control, as round 2 had. The `cli tool` workbench makes that cheap: a round is about
   20 minutes of Claude time and no pipeline spend.
