"""The review system, collapsing out of `pr_review_v2` / `v4` / `v5`.

Three generations exist because each was built beside the last rather than out of it. The
result is one experiment touching thirteen source files across six packages, 97 names imported
from v4 into v5, and backward edges where v4 imports v5 -- so "v4 is frozen and imported as a
library" is stated and untrue.

This package is where the pieces land as they stop being generation-specific. It starts with
the retrieval gate, not with a mechanical file move, because the gate is the piece where
duplication was costing correctness rather than only effort.
"""
