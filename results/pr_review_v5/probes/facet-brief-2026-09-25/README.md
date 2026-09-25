# Ad hoc probe: does the facet framing make a reviewer ask what maintainers ask? (2026-09-25)

Written before any reviewer ran.

**Conditions.** One run each, on the same five val1000 PRs.
- **X, the current generalist brief:** `SYSTEM_PROMPT_V12` plus the 8-item checklist, with a plain
  findings list instead of the submission tool.
- **Y, the facet brief:** the cell procedure and warrants, plus a deterministic dossier.
- **Shared:** both get `pr.md`, `diff.patch` and the same search tools, pinned to the PR's base
  commit. Claude reviewers throughout, so the model is held fixed.

**PRs:**
- 31984, `ConvexSpace` (AI);
- 27099, the language of Presburger arithmetic;
- 36275, a norm on the finite adele ring;
- 26308, normalized vectors: the proof-heavy control;
- 29464, doc corrections made with an LLM: PR-level asks.

**The reference set.** Round-1 asks that both val1000 readers agree are asks, about 53 in all.
Reviewers never see them.

**Matching.** A blind matcher agent matches findings to asks at issue level, with X and Y shuffled
and relabelled per PR.

**Reading rule.** Y "moves the needle" if all three hold:
- Y reaches at least 4 more asks than X in total;
- at least 2 of the gains are in F3, F4, F6, F7 or F12;
- Y loses at most 1 ask that X reached.

With one run per condition, a difference of 3 or fewer is noise. Findings that match no ask are
counted, not adjudicated: gold is a lower bound.
