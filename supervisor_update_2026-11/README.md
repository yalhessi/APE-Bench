# Supervisor update for 4 November 2026

**Current presentation: [HTML](original-led.html), [PDF](original-led.pdf),
[Markdown and speaker notes](original-led.md).**

This copy develops the [October deck](../supervisor_update_2026-10/slides.md). The
first section keeps its task formulation, with explicit distinctions between a
solution, a preferred alternative and an acceptable contribution. Conventions now
enter that account. Its boxed closing sentences are removed.

The experimental argument starts with the goal of building a reviewer, the solo
baseline and its misses, then asks about specialization, judgment and convention
supply. Relevant references appear at those questions. The former design-space
section is retained as backup tables. There are 31 main slides and 11 backups,
with no duration target.

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

These commands render local documents without generation, matching or judging.
HTML and PDF are generated local exports; source documents are versioned.

Validation: the PDF has 42 pages. Chrome found no slide overflow or footer overlap;
the revised framing and experimental opening were visually inspected. All 75 local
links across the current deck, notes, README and evidence register resolve. Earlier
presentation sources remain unchanged.
