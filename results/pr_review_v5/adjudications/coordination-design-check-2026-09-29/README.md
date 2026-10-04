# Pass labels for the coordination design's check (2026-09-29)

One reader (the session that wrote `docs/research/review-coordination-design-2026-09.md`), labelling
after the design was written. No second reader and no kappa: these are planning labels in the sense
of `miss-warrants-2026-09-26/finding_mechanism.jsonl`, not a measurement. The two-reader artifact
labelling with a pre-registered vocabulary is `docs/todo/remaining-misses-kind.md` and stays open.

- `pass_labels.jsonl`: one row per ask. The 38 misses of `miss-warrants-2026-09-26` (ids, set, PR
  and family carried over; `mechanism` and `battery` copied from `finding_mechanism.jsonl`) and the
  31 outside-reading asks both readers labelled `design_siblings`
  (`design-comparison-outside-v1`). `pass` is the design's pass (2 definitions and the typeclass
  layer, 3 statements and the family, 4 proofs, 5 names/prose/layout/location, 6 the change);
  `construction` is the artifact of §4 that would have exposed the ask.
- `analyse.py` prints the tallies the design quotes.

Ids and labels only; no review or gold text, as the audits keep it.
