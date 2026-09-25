# Probe 2: does a hard-cells job complement the current brief? (2026-09-25)

Written before any reviewer ran. This is the next probe of
`docs/research/facet-brief-probe-2026-09.md`, stated there before round 1's result was written up.

**Conditions:** Claude reviewers, one run each, on the same five val1000 PRs as round 1.
- **X′:** a second run of the current generalist brief (`SYSTEM_PROMPT_V12` plus the 8-item
  checklist), unchanged from round 1's X.
- **H:** a hard-cells-only job, covering only the cells round 1 showed the current brief missing:
  - the library;
  - definition design;
  - the typeclass layer;
  - a new notion's API;
  - siblings;
  - location;
  - the PR as a whole;
  - retirement.

  It has no whitespace instruction, and a finding a compile can settle must be verified before it
  is filed.

**Tools.** Both X′ and H hold the pipeline's own review tools through `cli tool` (`07b4dfc`,
`e30be07`), gated at each PR's retrieval cutoff:
- `declaration_search`, `content_search`, `file_read` and `file_search`;
- `naming_norm`, `precedent_search`, `zulip_search` and `proof_profile`;
- `lean_verify_edit`, compiling against the PR's base, which is built.

Round 1's X held only base-pinned `git grep` wrappers.

**Matching.** Two blind matchers, as in round 1. Each PR's three reviewers (X from round 1, X′ and
H) are shuffled to R1-R3 and stripped of any field that reveals the condition. So all three are
matched in one pass, by the same matcher.

**Reading rule.** The complement design is supported if, on both matchers:
- `X ∪ H` reaches at least 4 more of the 53 asks than `X ∪ X′`;
- at least 2 of those are in F3, F4, F6, F7 or F12;
- H files no more findings than X′.

Anything less is "this hard-cells job did not complement the current brief", with the untried
designs listed, not a negative about the cells.

**Also read, not pre-registered:**
- X′ against X: does the same brief with the pipeline's tools reach different asks? This is one run
  each, so it is anecdote.
- H's verified compiles: how many were attempted, and how many passed.
