"""Facets: the features of a declaration that reviewers actually comment on.

**Why these three, and why now.** The review-join gate measured what maintainers' form
requests are *about*, on a hand-read 50 rated by two independent panels. Of 23 requests:
proof_style 11, statement_form 5, typeclass 4, naming 3, tactic 3, attribute 2, docs 2,
placement 2, api_family 2. The situation keys built before that measurement -- goal head,
predicate head, LHS subject, `of`-lemma -- are tactic- and naming-shaped, because those were the
two conventions already known. Every proof_style request came back "partial" (right declaration,
a facet describing its goal rather than its proof) and every typeclass request "no" (no facet at
all). The plurality of what reviewers ask for had no representation.

Each facet is a pure function of fields `MajorDecl` already exposes -- `signature`, `proof`,
`variables` -- so nothing here touches `lean_parser`. Values are small enums or booleans so they
can serve as join keys, and every function says what it cannot see.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence, Tuple

from ape.toolkits.code.lean.lean_parser import mask_noncode_regions

from src.mathlib_review.evidence.operators.naming_contrast import declaration_conclusion

FACETS_VERSION = "v5-facets/1"


# --- proof structure ---------------------------------------------------------------------

_TERM_MODE_HEAD = re.compile(r"^\s*(?:by\b)?")
_TACTIC_LINE = re.compile(r"^\s*(?:·\s*)?([a-z_][A-Za-z0-9_'!?]*)", re.M)
_CALC = re.compile(r"(?<![A-Za-z0-9_'])calc(?![A-Za-z0-9_'])")
_HAVE = re.compile(r"(?<![A-Za-z0-9_'])(?:have|obtain|let)(?![A-Za-z0-9_'])")
_CASES = re.compile(r"(?<![A-Za-z0-9_'])(?:by_cases!?|rcases|cases|obtain\s+⟨|induction|match)(?![A-Za-z0-9_'])")
_REFINE = re.compile(r"(?<![A-Za-z0-9_'])(?:refine|exact|apply)(?![A-Za-z0-9_'])")
_SIMP_ONLY = re.compile(r"(?<![A-Za-z0-9_'])simp\s+only\b")
_FOCUS_DOT = re.compile(r"^\s*·", re.M)


def proof_structure(proof: Optional[str]) -> Dict[str, object]:
    """How a proof is built, as the properties reviewers ask to change.

    `mode`: `term` (no leading `by`), `tactic`, or `none`. The rest are counts and flags over the
    masked body. A reviewer asking for "a one-liner", "avoid chaining tactics on one line", "use a
    `calc`", "don't case-split here" is asking about exactly these.
    """

    text = (proof or "").strip()
    if not text:
        return {"mode": "none"}
    masked = mask_noncode_regions(text)
    tactic_mode = masked.startswith("by") and (len(masked) == 2 or not masked[2].isalnum())
    lines = [ln for ln in masked.splitlines() if ln.strip()]
    steps = ([m.group(1) for m in _TACTIC_LINE.finditer(masked)] if tactic_mode else [])
    # A one-line `by grind [...]` puts `by` first on the only line; it is the mode marker, not
    # a step, and counting it made `closes_with` read `by` for every one-liner.
    if steps and steps[0] == "by":
        steps = steps[1:]
    if tactic_mode and not steps:
        # `by grind` on one line: the tactic follows `by` on the same line.
        rest = masked[2:].strip()
        first = re.match(r"([a-z_][A-Za-z0-9_'!?]*)", rest)
        steps = [first.group(1)] if first else []
    return {
        "mode": "tactic" if tactic_mode else "term",
        "lines": len(lines),
        "steps": len(steps),
        "has_calc": bool(_CALC.search(masked)),
        "case_splits": len(_CASES.findall(masked)),
        "haves": len(_HAVE.findall(masked)),
        "focus_bullets": len(_FOCUS_DOT.findall(masked)),
        "simp_only": bool(_SIMP_ONLY.search(masked)),
        "closes_with": steps[-1] if steps else None,
        "one_liner": len(lines) == 1,
    }


# --- statement shape ---------------------------------------------------------------------

_BINDER = re.compile(r"([(\[{⦃])")
_IFF = re.compile(r"↔")
_IMPLIES = re.compile(r"→")
_NUMERAL = re.compile(r"(?<![A-Za-z0-9_'.])\d+(?![A-Za-z0-9_'.])")
_EXISTS = re.compile(r"∃")
_FORALL = re.compile(r"∀")


def _split_binders(signature: str) -> List[Tuple[str, str]]:
    """`(kind, text)` for each top-level binder group before the conclusion colon.

    Depth-tracked over `()[]{}⦃⦄`. Kinds: `explicit` `(…)`, `instance` `[…]`, `implicit` `{…}`,
    `strict` `⦃…⦄`. This is the complement of `declaration_conclusion`, which finds where the
    binders END; nothing existing split what came before.
    """

    out: List[Tuple[str, str]] = []
    depth = 0; start = None; kind = None
    opens = {"(": "explicit", "[": "instance", "{": "implicit", "⦃": "strict"}
    closes = {")": "(", "]": "[", "}": "{", "⦄": "⦃"}
    stack: List[str] = []
    for index, ch in enumerate(signature or ""):
        if ch in opens:
            if depth == 0:
                start, kind = index, opens[ch]
            stack.append(ch); depth += 1
        elif ch in closes and stack:
            stack.pop(); depth -= 1
            if depth == 0 and start is not None:
                out.append((kind or "explicit", signature[start:index + 1]))
                start = kind = None
        elif ch == ":" and depth == 0 and signature[index:index + 2] != ":=":
            break  # the conclusion colon; binders are over
    return out


def statement_shape(signature: Optional[str]) -> Dict[str, object]:
    """How a statement is phrased, as the properties reviewers ask to change.

    "State it as an iff", "weaken `card = 3` to `card ≤ 3`", "generalise the numeral", "take
    the hypothesis as an instance argument" are all requests about these fields.
    """

    sig = signature or ""
    binders = _split_binders(sig)
    conclusion = declaration_conclusion(sig)
    by_kind: Dict[str, int] = {}
    for kind, _ in binders:
        by_kind[kind] = by_kind.get(kind, 0) + 1
    return {
        "binders": by_kind,
        "instance_binders": by_kind.get("instance", 0),
        "explicit_hypotheses": sum(1 for k, t in binders if k == "explicit" and ":" in t),
        "conclusion_is_iff": bool(_IFF.search(conclusion)),
        "conclusion_is_implication": bool(_IMPLIES.search(conclusion)) and not _IFF.search(conclusion),
        "conclusion_quantified": bool(_EXISTS.search(conclusion) or _FORALL.search(conclusion)),
        "numerals_in_hypotheses": len(_NUMERAL.findall(" ".join(t for k, t in binders))),
        "numerals_in_conclusion": len(_NUMERAL.findall(conclusion)),
    }


# --- typeclass usage ---------------------------------------------------------------------

_CLASS_HEAD = re.compile(r"^\[\s*(?:[a-zA-Z_][A-Za-z0-9_']*\s*:\s*)?([A-Z][A-Za-z0-9_'.]*)")


def typeclass_binders(signature: Optional[str],
                      variables: Sequence[str] = ()) -> Dict[str, object]:
    """Which typeclasses a declaration assumes, from its own binders and the section's.

    "You only need `NonAssocSemiring` here", "state at the weakest typeclass" are requests about
    the *heads* of the instance binders -- `[CommRing R]` -> `CommRing`. Section `variable`
    binders are included because that is where most Mathlib instance assumptions live.
    """

    heads: List[str] = []
    for kind, text in _split_binders(signature or ""):
        if kind == "instance":
            match = _CLASS_HEAD.match(text)
            if match:
                heads.append(match.group(1))
    for var in variables or ():
        for kind, text in _split_binders(str(var)):
            if kind == "instance":
                match = _CLASS_HEAD.match(text)
                if match:
                    heads.append(match.group(1))
    return {
        "instance_heads": sorted(set(heads)),
        "instance_count": len(heads),
    }
