"""Pure functions from the PR store to each consumer's dataset.

Each projection is versioned, writes under `data/pull_requests/projections/<name>/<version>/`, and
records the store manifest's sha in its own manifest, so any derived number traces to the exact
raw bytes it came from.
"""
