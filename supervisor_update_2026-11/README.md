# Supervisor update for 4 November 2026

**Current presentation: [original-led HTML](original-led.html), [PDF](original-led.pdf),
[Markdown and speaker notes](original-led.md).**

This fresh copy returns to the [October deck](../supervisor_update_2026-10/slides.md).
Its theoretical slides are unchanged, its prior-work comparison is retained, and
the experimental section follows the original thesis and Q1–Q4 progression. It
removes the added overview from `meeting-v2`, makes the shared-context problem with
specialist arms explicit, traces the motivation for conventions, and folds in the
later experimental results. There is no duration target.

The deck has 31 main slides and seven backups. [Revision notes](original-led-notes.md)
map it to the original and link the contemporaneous motivation for conventions.
The [evidence register](evidence.md) supports the later empirical claims. Speaker
notes carry measurement details, limitations and sources.

## Preserved references and earlier drafts

- [October update](../supervisor_update_2026-10/slides.md): the preferred starting point;
  its Markdown, local HTML and PDF remain unchanged.
- [Detailed November reference](slides.md), [HTML](slides.html), [PDF](slides.pdf):
  the 37-slide empirical update, preserved unchanged.
- [Experiment map since September](experiment-map.md): 25 experiment families with
  motivations, comparisons, answers, corrections and consequences.
- [Earlier content narrative](content-narrative.md): preserved working proposal;
  it is not the structure of the current presentation.
- [Earlier meeting version](meeting-v2.md), [HTML](meeting-v2.html), [PDF](meeting-v2.pdf),
  and [structure/timing notes](meeting-structure.md).
- [First prototype](meeting-draft.md), [HTML](meeting-draft.html), [PDF](meeting-draft.pdf),
  and [restructuring options](presentation-options.md).
- [Living research overview](../docs/project-research-overview.md), unchanged.

The experiment review covers completed work through 26 October and the 27 October
assessment, including branch-local records. The knowledge-bank and preparation
usefulness panels are unfinished. No overall usefulness improvement is claimed.
The evidence register records branch snapshots and source paths; some links depend
on the experiment worktrees remaining in this checkout.

## Render locally

From the repository root, with a local Marp CLI and Chrome:

```bash
marp supervisor_update_2026-11/original-led.md --html \
  -o supervisor_update_2026-11/original-led.html
marp supervisor_update_2026-11/original-led.md --html --pdf --allow-local-files \
  -o supervisor_update_2026-11/original-led.pdf
```

These commands render local documents; they do not run generation, matching or
judging. HTML and PDF are generated local exports, as in the October update. Source
documents are versioned. Substitute `slides.md` to rebuild the detailed reference.

Validation: the current PDF has 38 pages. Chrome found no slide overflow or footer
overlap; the updated experimental slides were visually inspected. All 35 local
Markdown links resolve. The original theoretical slides and convention formulation
were compared directly, and the earlier presentation sources remain unchanged.
