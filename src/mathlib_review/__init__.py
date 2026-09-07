"""Reviewing a Mathlib pull request: one package.

This was `pr_review_v4` and `pr_review_v5`, two generations built beside each other rather
than out of each other. The cost was measurable: 97 names imported from v4 into v5, backward
edges where v4 imported v5 so that "v4 is frozen and imported as a library" was stated and
untrue, and one experiment touching thirteen source files across six packages.

    paths, io, diffs,       primitives with no home in either generation: where artifacts
    workspace, corpus,      live, running a tool in a workspace, reading a model's JSON,
    model_output,           the temporal gate every retrieval source defers to, the
    retrieval_gate,         config-loading convention, coordinated multi-file edits
    run_config, patchset

    schema/                 the types, split by lifecycle rather than by concern
    release/                building the gold-free release the whole system reads
    agenda/                 what to ask: the arm registry, specs, prompts, routing, census
    review/                 running it: the CLI, the runner, candidates, merge, finalize
    evidence/               warrants: the chain, the verifiers, the statement gate, operators
    retrieval/              precedent ranking over the review corpus
    judge/                  the semantic judge that scores a run against gold
    opportunities/          v4's pre-declared-condition design, still what gold is built from
    analysis/               reading a finished run: reports, overlays, benches, scope
    legacy_pipeline/        spent one-shot builders whose artifacts are still load-bearing

An intermediate state of this package held only the shared primitives while every piece of
review logic stayed in v4 and v5, which made three places to look under a name that promised
to be the destination. That was worse than the two it replaced. The lesson is worth keeping:
the reason to merge was never that code was duplicated -- a scan found almost none -- it was
that one concept lived in several places, which is true whether or not any function appears
twice.
"""
