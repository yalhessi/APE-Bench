# Duplicate directory note

This directory is byte-identical to `systematic-opportunities-v1-medium-c1v2/` (verified with
`diff -rq`, 2026-07-18). The generation-side treatment did not change when the census annotation
protocol moved from `obligation-issue-class/1` to `obligation-expression-class/2` — only the
evaluation-side census layer did — but the frozen C1v2 census report records the `-c1v2`
treatment path, so that directory is the canonical go-forward reference and
`phase10_medium.py` defaults point there. This copy is retained because the superseded
v1-protocol census (`results/pr_review_v4/audits/phase10-medium-static-census/`) records this
path in its provenance.
