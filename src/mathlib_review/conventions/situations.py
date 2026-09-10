"""Situation extractors: the reference class a declaration belongs to, per category.

**The situation is where a convention lives.** Measured on the base commit: "dot notation" read
over every `_of_` lemma is 5.7 % adopted; read over `of`-lemmas *whose conclusion is a namespaced
predicate* -- the situation where the rule actually applies -- it is 13.7 %. Same convention, a
2.4x different number, from the situation definition alone. Every downstream measurement (what
the code does, what new code does, what reviewers asked for) is only as good as this.

Each extractor answers one question about one declaration and returns a small hashable key, so
that comments, commits and declarations can be joined on it. They reuse what exists --
`declaration_conclusion` and `conclusion_head` for the goal shape, `conclusion_subject` for the
LHS subject, `tactics_used` for the proof -- and add the one the existing operators could not
produce: the **predicate head**. `conclusion_subject` reads the left-hand side of a relation,
so a conclusion with no relation (`IsFundamentalSequence f o g`) came back `unknown`, and that
is exactly the shape the dot-notation convention is about.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple

from ape.toolkits.code.lean.lean_parser import mask_noncode_regions

from src.mathlib_review.evidence.operators.naming_contrast import declaration_conclusion
from src.mathlib_review.evidence.operators.naming_norm import conclusion_subject, leaf_prefix
from src.mathlib_review.conventions.facets import (
    proof_structure, statement_shape, typeclass_binders,
)
from src.mathlib_review.retrieval.declaration_table import conclusion_head
from src.mathlib_review.tactics import TACTIC_VOCABULARY, tactics_used

SITUATIONS_VERSION = "v5-situations/1"

#: A conclusion whose head is a capitalised, possibly namespaced identifier applied to
#: arguments -- `IsFundamentalSequence f o g`, `Continuous f`, `x.PosSemidef` -- i.e. a
#: predicate, not a relation between two sides.
_PREDICATE_HEAD = re.compile(r"^(?:\(?)([A-Z][A-Za-z0-9_']*(?:\.[A-Z][A-Za-z0-9_']*)*)\b")
#: `x.PosSemidef` or `(a • x).PosSemidef` -- the predicate applied with dot syntax to a receiver
#: that may be an identifier or a parenthesised expression; the head is after the last dot.
_DOTTED_PREDICATE = re.compile(
    r"^(?:[a-z][A-Za-z0-9_']*|\((?:[^()]|\([^()]*\))*\))\.([A-Z][A-Za-z0-9_']*)\b")


def predicate_head(conclusion: Optional[str]) -> Optional[str]:
    """The predicate a conclusion asserts, when it asserts one rather than relating two sides.

    Returns `None` for relations (`a = b`, `s ⊆ t`), for quantified conclusions, and for
    anything whose head is not a capitalised identifier. `IsFundamentalSequence f o g` ->
    `IsFundamentalSequence`; `(a • x).PosSemidef` -> `PosSemidef`; `Continuous f` ->
    `Continuous`.
    """

    text = (conclusion or "").strip()
    if not text or text.startswith(("∃", "∀", "¬")):
        return None
    if conclusion_head(text) not in ("other", None):
        return None
    match = _PREDICATE_HEAD.match(text)
    if match:
        return match.group(1)
    match = _DOTTED_PREDICATE.match(text)
    if match:
        return match.group(1)
    return None


def name_form(fullname: str) -> Dict[str, object]:
    """How a declaration is named, as the features naming conventions are stated over.

    `dotted_under_predicate` is filled by the caller once the predicate head is known: it is
    the dot-notation question itself -- is `IsFoo.of_bar` named inside `IsFoo`, or is it
    `isFoo_of_bar` beside it.
    """

    leaf = fullname.rsplit(".", 1)[-1]
    namespace = fullname.rsplit(".", 1)[0] if "." in fullname else ""
    return {
        "leaf": leaf,
        "namespace": namespace,
        "leaf_prefix": leaf_prefix(leaf),
        "is_of_lemma": "_of_" in leaf or leaf.startswith("of_"),
        "primed": leaf.endswith("'"),
        "leaf_is_lower": leaf[:1].islower(),
    }


@dataclass(frozen=True)
class Situation:
    """Everything a convention could be conditioned on, for one declaration."""

    kind: str
    conclusion_head: Optional[str]
    predicate_head: Optional[str]
    subject_token: Optional[str]
    subject_kind: str
    leaf_prefix: str
    is_of_lemma: bool
    primed: bool
    #: For an `of`-lemma concluding predicate P: is it named inside P's namespace?
    named_inside_predicate: Optional[bool]
    tactics: Tuple[str, ...]
    #: The facets the review-join gate showed reviewers actually comment on -- proof_style 11,
    #: statement_form 5, typeclass 4 of 23 form requests -- and which the first four keys did
    #: not represent at all. Stored as small dicts; `keys()` turns them into join keys.
    proof: Dict[str, object]
    statement: Dict[str, object]
    typeclasses: Tuple[str, ...]

    def keys(self) -> Dict[str, str]:
        """The join keys other sources are indexed by. Each is one reference class."""

        out: Dict[str, str] = {}
        if self.conclusion_head:
            out["goal"] = f"goal:{self.conclusion_head}"
        if self.predicate_head:
            out["predicate"] = f"pred:{self.predicate_head}"
        if self.subject_token:
            out["subject"] = f"subject:{self.subject_token}"
        if self.is_of_lemma and self.predicate_head:
            out["of_lemma_of_predicate"] = f"of:{self.predicate_head}"
        # proof_style: the shape of the proof, coarse enough to be a class.
        mode = self.proof.get("mode")
        if mode and mode != "none":
            shape = "term" if mode == "term" else (
                "tactic:one-liner" if self.proof.get("one_liner") else
                "tactic:cases" if self.proof.get("case_splits") else
                "tactic:calc" if self.proof.get("has_calc") else "tactic:multi")
            out["proof_style"] = f"proof:{shape}"
        # statement_form: iff / implication / plain, with whether numerals are hard-coded.
        if self.statement:
            form = ("iff" if self.statement.get("conclusion_is_iff") else
                    "impl" if self.statement.get("conclusion_is_implication") else "plain")
            if self.statement.get("numerals_in_hypotheses"):
                form += "+numeral-hyp"
            out["statement_form"] = f"stmt:{form}"
        # typeclass: one key per instance head, so "you only need X" can be indexed by X.
        for head in self.typeclasses:
            out.setdefault("typeclass", f"class:{head}")
        return out


def situation_of(kind: str, fullname: str, signature: str, proof: str,
                 variables: Sequence[str] = ()) -> Situation:
    """Every situation one declaration is in, from the fields `MajorDecl` already exposes."""

    conclusion = declaration_conclusion(signature or "")
    head = conclusion_head(conclusion)
    predicate = predicate_head(conclusion)
    subject = conclusion_subject(conclusion)
    form = name_form(fullname or "")
    inside: Optional[bool] = None
    if predicate and form["is_of_lemma"]:
        inside = str(form["namespace"]).endswith(predicate) or fullname.startswith(predicate + ".")
    masked = mask_noncode_regions(proof or "") if proof else ""
    return Situation(
        kind=kind,
        conclusion_head=head,
        predicate_head=predicate,
        subject_token=subject.token,
        subject_kind=subject.kind,
        leaf_prefix=str(form["leaf_prefix"]),
        is_of_lemma=bool(form["is_of_lemma"]),
        primed=bool(form["primed"]),
        named_inside_predicate=inside,
        tactics=tuple(sorted(tactics_used(masked, TACTIC_VOCABULARY))) if masked else (),
        proof=proof_structure(proof),
        statement=statement_shape(signature),
        typeclasses=tuple(typeclass_binders(signature, variables)["instance_heads"]),
    )
