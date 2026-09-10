"""The tactic vocabulary, in one place, with the reason it is versioned.

Three hand-written tactic keyword lists already exist in this tree and they disagree:
`datasets/taxonomy/ape_bench_parser_taxonomy.py:_tactic_family_counts` (10 families, for
ape_bench's edit taxonomy), `agenda/census.py:_MANUAL_TACTICS` (20 names, for the agenda's
"manual tactic chain" signal, and self-described as "deliberately crude"), and the list this
module now owns. Those two classify different things for different consumers and are left
alone; what must not happen is a fourth.

**Why two vocabularies and not one.** A result about "did this arm ever ask about a tactic"
must not depend on where the line between tactic and non-tactic was drawn. `simp`, `rw` and
`exact` are tactic names, and excluding them is arguable either way -- a search for `@[simp]`
is looking for an attributed lemma, not for tactic idiom. So both are reported, and a finding
that survives the loose one is not an artifact of the strict one. Measured on
`pr5_smoke4_rep9`: widening takes the run from 2 tactic-shaped queries to 14 and `style` from
1 to 9, while `proof_idiom` and `proof_golf` stay at zero under both.

**Why word boundaries, and why the query must be normalized first.** `decide` sits inside
`decide_eq_true_eq` and `bound` inside `bounded_of_isCompact`, so a substring test scores
name lookups as tactic questions. And a *regex* query for a tactic carries its own boundary
syntax: the generalist searched the literal `\\bgrind\\b`, which a naive word-boundary test
scores as NOT asking about `grind`, because the `b` of the escape closes the boundary against
the `g`. Reading a `grind` search as a non-tactic search is the exact error this exists to
avoid.
"""

from __future__ import annotations

import re
from typing import Iterable, Optional

#: Bumped whenever either list changes, so two measurements can be told apart.
TACTIC_VOCABULARY_VERSION = "v5-tactic-vocabulary/1"

#: Tactics whose name has no innocent English or identifier reading.
TACTIC_VOCABULARY = (
    "grind", "by_cases", "gcongr", "grw", "omega", "fun_prop", "decide", "simpa",
    "simp_all", "norm_num", "positivity", "aesop", "field_simp", "ring_nf", "calc",
    "bound", "linarith", "nlinarith", "polyrith", "continuity", "measurability",
)

#: The same question with a deliberately generous boundary. A superset, always.
WIDE_TACTIC_VOCABULARY = TACTIC_VOCABULARY + (
    "simp", "rw", "erw", "norm_cast", "push_cast", "ring", "abel", "exact", "apply",
)

#: Regex syntax that appears *inside* a query string and must not be read as word characters.
_REGEX_NOISE = re.compile(r"\\[bBsSwWdDAZzG]|[\\^$.|?*+()\[\]{}]")


def normalize_query(pattern: Optional[str]) -> str:
    """Strip regex syntax so a pattern can be word-boundary matched as prose."""

    return _REGEX_NOISE.sub(" ", pattern or "")


def mentions_tactic(text: Optional[str],
                    vocabulary: Iterable[str] = TACTIC_VOCABULARY,
                    *, normalize: bool = True) -> bool:
    """Does this text name a tactic, word-boundary matched?

    `normalize=True` for a *query* written by an agent, which may contain regex syntax.
    `normalize=False` for Lean source, where `\\b` would be a real escape and stripping
    punctuation could join two tokens.
    """

    if not text:
        return False
    haystack = normalize_query(text) if normalize else text
    return any(re.search(rf"\b{re.escape(word)}\b", haystack) for word in vocabulary)


def tactics_used(proof_text: Optional[str],
                 vocabulary: Iterable[str] = TACTIC_VOCABULARY) -> frozenset:
    """Which vocabulary tactics appear in a proof body.

    The caller must pass text already run through `lean_parser.mask_noncode_regions`, or a
    tactic named in a docstring will be counted as used. Not normalized: this is Lean source.
    """

    if not proof_text:
        return frozenset()
    return frozenset(
        word for word in vocabulary
        if re.search(rf"(?<![A-Za-z0-9_']){re.escape(word)}(?![A-Za-z0-9_'])", proof_text)
    )
