# Supervisor update for 4 November 2026

**Current presentation: [HTML](original-led.html), [PDF](original-led.pdf),
[Markdown and speaker notes](original-led.md).** Since the 05:08 revision every result
slide in section 2 carries a comparison strip (what is compared, what is held fixed, how it
is measured, when it ran), and the ask-free delivery table states its units.

**Proposed restructure of section 2: [HTML](original-led-v2.html), [PDF](original-led-v2.pdf),
[Markdown and speaker notes](original-led-v2.md).** Preserves section 1 and the experimental
record; section 2 follows four questions (A attention, B conventions, C supplying useful
context without the maintainer's requests, D deciding to request a change). The opening
and closing slides give those questions and their answers. The comparison boxes are
removed: each result keeps a short setup and readable measurement labels, with full
comparison conditions, dates and instruments in speaker notes. The alternative-generation
experiment is summarized in section 2 and detailed in backup.
Kept as a separate file so the two can be compared slide by slide; see the
[notes](original-led-notes.md#second-pass-4-november-comparison-strips-and-the-four-question-route).

This copy develops the [October deck](../supervisor_update_2026-10/slides.md). The
first section keeps its task formulation. Automated checks help separate solutions
from non-solutions; human review identifies acceptable or preferred solutions;
automating review adds checks that exclude more unacceptable contributions from
what passes. Conventions supply candidate standards for that extension. Required
changes and optional preferences remain distinct. Boxed closing sentences are removed.

The experimental argument starts with the goal of building a reviewer, the solo
baseline and its misses, then asks about specialization, judgment and convention
supply. Relevant references appear at those questions. The former design-space
section is retained as backup tables. The proposed deck has 31 main slides and 12
backups, with no duration target.

[Framing and narrative notes](original-led-notes.md) explain the revisions and trace
the conventions motivation. The [evidence register](evidence.md) and speaker notes
carry experimental sources, denominators, qualifications and corrections.

## Preserved references

- [October update](../supervisor_update_2026-10/slides.md), unchanged.
- [Detailed November reference](slides.md), [HTML](slides.html), [PDF](slides.pdf), unchanged.
- The preceding original-led source is preserved in commit `7ff09a23`.
- [Experiment map since September](experiment-map.md): 25 experiment families.
- [Earlier proposed narrative](content-narrative.md).
- [Earlier meeting version](meeting-v2.md), [HTML](meeting-v2.html), [PDF](meeting-v2.pdf),
  and [structure/timing notes](meeting-structure.md).
- [First prototype](meeting-draft.md), [HTML](meeting-draft.html), [PDF](meeting-draft.pdf),
  and [restructuring options](presentation-options.md).
- [Living research overview](../docs/project-research-overview.md), unchanged.

The record covers experiments through 26 October and the 27 October assessment,
including branch-local results. The knowledge-bank and preparation usefulness
panels remain unfinished. Some evidence links depend on the experiment worktrees
remaining in this checkout.

## Render locally

From the repository root, with Marp and Chrome:

```bash
marp supervisor_update_2026-11/original-led.md --html \
  -o supervisor_update_2026-11/original-led.html
marp supervisor_update_2026-11/original-led.md --html --pdf --allow-local-files \
  -o supervisor_update_2026-11/original-led.pdf
```

The same two commands with `original-led-v2` render the proposed deck. Marp blocks when
its stdin is an open pipe; from a script, append `< /dev/null`.

These commands render local documents without generation, matching or judging.
HTML and PDF are generated local exports; source documents are versioned.

Validation: the current PDF has 42 pages and the proposed one 43. A headless-Chrome
check at 1280×720 reports no slide overflow or footer overlap in either; section 2 of the
proposed deck and the two altered slides of the current one were visually inspected.
Earlier presentation sources remain unchanged.
