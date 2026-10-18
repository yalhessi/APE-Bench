# What maintainers say when they give a reason: the result (2026-10-16)

318 of reader A's 1,833 census asks state a ground by the pre-registered markers (17%). Two readers, blind to
the codebook, coded the primary ground; they agree on 295 of 318. `score.py`.

| primary ground | reader A | reader B | both agree (246 with a ground) |
|---|---|---|---|
| a technical fact (does not compile, `simp` cannot, it already exists, a counterexample) | 85 | 81 | 78 (32%) |
| a principle (generality 18, readability 15, then usability, maintainability, informative naming) | 68 | 77 | 67 (27%) |
| preference (first person, worth, aesthetics) | 45 | 44 | 40 (16%) |
| a scope's form (library 35, file 14, area 8, as named) | 29 | 28 | 28 (11%) |
| authority (style guide, a guideline page, Zulip, a ruling) | 20 | 20 | 19 (8%) |
| currency (deprecated, newer form, migration) | 10 | 9 | 7 (3%) |
| other (review cost, process, mathematical literature) | 10 | 9 | 7 (3%) |
| no ground actually stated (a marker false positive) | 51 | 50 | 49 |

**By the pre-registered rule: SUPPORTED, on both readers and on agreed items.** Preference plus authority is
24% (the line was a third); principle 27% (the line was a tenth); principle, scope's form, currency and fact
together 73% (the line was two thirds). It holds in every marginal: head conventions 75%, tail 71%, PRs
without AI authorship 74%, AI-authored PRs 68% (56 asks; authority is twice as common there, 15% against 6%,
the AI-disclosure and style policies being cited).

**What it says.** When a maintainer says why, the reason is mostly a checkable fact or a general value
(generality and readability lead), and taste or authority is about a quarter. The scope layer appears (11%,
mostly the library's practice, then the file's); currency is small (3%). This supports the user's picture
of review as reasoning on evidence from a short set of values, at the altitude of what maintainers state.

**Limits.** It reads the 17% of asks that state a ground; the 80% that state none cannot be read this way,
and the ones that do may differ from the rest. Two readers of one model family; the marker selection
included preference words so preference is not selected out. A defect fixed after scoring and before this
write-up: `select.py` compared a boolean AI flag to the string "True", so the first run's AI marginal was
empty; the fix leaves the selection and batches identical (checked) and only adds the 56 AI-authored asks
to their marginal.

## Corrections after the adversarial review (2026-10-16; `review2-grounds.md` beside the plan)

- **The verdict depends on counting `fact` for the picture**, a choice the protocol made in advance. A
  taste-driven maintainer cites facts too. With `fact` neutral, preference + authority is 35% (28-43%), over the
  one-third line for both readers and every marginal; a fairer rival category lands at 31%. **At the registered
  lines the honest reading is mixed, not supported.**
- **Counts in the table above were summed over both readers** for the principles and scopes named. Per ask, the
  scopes named are library 17, file 7, area 4: area-level scope is under 2% of stated grounds. 8 of 12
  readability-as-principle items are first-person; 8 of 19 generality grounds restate the ask.
- **The two readers act as one reader run twice** (the same quoted phrase in 68% of notes); a third reading of
  30 items agreed on 25, and 4 of its 5 changes moved away from the picture.
- **Selection.** Of 40 unselected asks read, 11 state a ground the markers missed (mostly "the library does it
  this way"), so about 37% of asks state one, not 17%; 2 state a preference, 14 are bare enforcement of a
  convention. Explicit "optional / nit / won't insist" is 2.2% of asks, so amendment 1's "hedging 28%" was
  mostly politeness.
- **What stands:** a stated reason is usually a checkable fact or a named value; first-person taste is about
  16% of stated grounds (about 2% of all asks). It says nothing about the scope layer or the attention rival.
