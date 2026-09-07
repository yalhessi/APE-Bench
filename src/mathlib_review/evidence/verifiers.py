"""Route a holistic claim to the operator that can check it.

Evidence collection dispatched on `concern_family`, which is not a check: "naming" names a
topic, not a verifiable assertion. Measured consequence on the 4-PR smoke — **0 of 33
candidates** obtained a claim-scoped `supports`, so the holistic arm published nothing and
the merged ensemble was exactly the checker arm. Twelve of those candidates
(documentation 6, naming 4, scope 2) could not have been supported by any collector that
exists, whatever they said.

`issue_kind` is the missing routing key. The verifiers themselves are not new: the
deterministic arm already contains the machinery, and it has simply never been pointed at
the holistic arm's claims.

A verifier returns one of three things, and the third matters as much as the first:

* `supports` — the operator independently found what the claim asserts.
* `contradicts` — the operator looked and found the opposite. This is where the precision
  win lives: a refuted claim is actively suppressed rather than merely unsupported.
* `abstain` — no verifier for this kind, or it could not decide. The claim stays
  diagnostic, which is what "we do not know" should look like.

`abstain` is deliberately not a soft pass. A gate that admits on absence of evidence is a
rubber stamp, and it would worsen exactly the silent-PR axis the deterministic arm wins on.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from src.mathlib_review.evidence.operators.lint_policy import lint_target
from src.mathlib_review.evidence.operators.naming_norm import (
    conclusion_subject,
    leaf_prefix,
    propose_rename,
)
from src.mathlib_review.schema import CandidateClaim, ChangeTarget

VERIFIER_VERSION = "issue-kind-verifiers/1"


@dataclass(frozen=True)
class VerificationResult:
    verdict: str            # supports | contradicts | abstain
    verifier: str
    detail: str

    @property
    def decided(self) -> bool:
        return self.verdict in ("supports", "contradicts")


def _abstain(verifier: str, detail: str) -> VerificationResult:
    return VerificationResult("abstain", verifier, detail)


def verify_style_norm(candidate: CandidateClaim, target: ChangeTarget,
                      **_context) -> VerificationResult:
    """Mathlib's text-style linters can *support* a style claim, never refute one.

    This returned `contradicts` when the linter was silent, and a `contradicts` sets the
    evidence packet to `contradicted`, which `select_findings` skips — so linter silence
    suppressed the claim outright. The measurement says that is backwards.

    `style` is the **largest** concern family in the medium gold: 10 of 33 maintainer
    judgments, ahead of duplication (7) and naming (4). `lint_norm` produced **one**
    opportunity on all of medium. If maintainer style asks were codified in Mathlib's
    linters, the linter would have found them; it found one. So most of what maintainers
    actually ask for under "style" is not lint-codified, and the linter's silence carries no
    information about those asks.

    Suppressing on that silence meant using an instrument that detects ~10% of the family to
    veto the only arm attempting the other ~90% — measured on the 4-PR smoke as 8 style
    claims refuted out of 8. The claim stays diagnostic instead: unsupported, which is true,
    rather than refuted, which the linter is not entitled to say.
    """

    finding = lint_target(target)
    if finding is None:
        return _abstain(
            "lint_policy",
            "Mathlib's text-style linters report no violation on the reviewed lines; they "
            "encode only codified rules and cannot settle a style ask that is not one",
        )
    return VerificationResult(
        "supports", "lint_policy",
        f"text-style lint reports {', '.join(finding.codes)} on reviewed lines",
    )


def verify_naming_convention(candidate: CandidateClaim, target: ChangeTarget,
                             population_scan=None, **_context) -> VerificationResult:
    """The snapshot's own naming population decides a naming-convention claim.

    Requires the population scan, which is snapshot-keyed and expensive; without it the
    verifier abstains rather than guessing. A claim the corpus contradicts — the current
    prefix is itself well attested for this subject — is refuted, which is the check that
    keeps the deterministic naming operator silent on control PRs.
    """

    if population_scan is None:
        return _abstain("naming_norm", "no snapshot population scan supplied")
    code = target.reviewed_code or target.base_code or ""
    if not code:
        return _abstain("naming_norm", "target has no code to infer a subject from")

    from ape.toolkits.code.lean.lean_parser import parse_major_declarations

    from src.mathlib_review.evidence.operators.naming_contrast import declaration_conclusion

    declarations = parse_major_declarations(code)
    if not declarations:
        return _abstain("naming_norm", "no parsed declaration")
    declaration = declarations[0]
    fullname = declaration.fullname or declaration.name or ""
    subject = conclusion_subject(declaration_conclusion(declaration.signature or ""))
    if subject.token is None:
        return _abstain("naming_norm", f"no resolvable subject ({subject.kind})")
    population = population_scan.population(subject.token)
    if population is None and not getattr(population_scan, "available", lambda: True)():
        # "The corpus could not be read" and "the corpus shows no norm" are different facts,
        # and only the second is about the name under review. Collapsing them would report a
        # broken workspace as evidence that a naming claim is unsupported.
        return _abstain(
            "naming_norm",
            "the snapshot population scan could not be built from this workspace",
        )
    proposal = propose_rename(fullname, subject, population)
    if proposal is not None:
        return VerificationResult(
            "supports", "naming_norm",
            f"{proposal.support}/{proposal.members} declarations with subject "
            f"`{proposal.subject_token}` use the `{proposal.conventional_prefix}_` prefix",
        )
    if population is not None and population.is_strong():
        current = leaf_prefix(fullname.rsplit(".", 1)[-1])
        if current == population.dominant_prefix:
            return VerificationResult(
                "contradicts", "naming_norm",
                f"the name already follows the established `{current}_` prefix for subject "
                f"`{subject.token}`",
            )
    return _abstain(
        "naming_norm",
        f"the snapshot has no strong prefix norm for subject `{subject.token}`",
    )


def verify_documentation_gap(candidate: CandidateClaim, target: ChangeTarget,
                             **_context) -> VerificationResult:
    """Only the *presence* of a docstring is checkable; its quality is not.

    A missing-docstring rule was measured and rejected as a review norm — 8% of Mathlib
    lemmas and 67% of definitions carry one, so demanding them would fire on 92% of new
    lemmas. So this verifier refutes only the narrow, decidable case: a claim that
    documentation is absent, when it is plainly present. Everything else abstains, because
    whether a docstring is *good enough* is exactly the editorial judgement no rule settles.
    """

    code = target.reviewed_code or ""
    has_doc = "/--" in code or "/-!" in code
    claim = f"{candidate.claim} {candidate.requested_change or ''}".lower()
    asserts_absence = any(
        phrase in claim for phrase in
        ("missing doc", "no docstring", "lacks doc", "undocumented", "add a docstring")
    )
    if asserts_absence and has_doc:
        return VerificationResult(
            "contradicts", "docstring_presence",
            "the reviewed target already carries a doc comment",
        )
    if asserts_absence and not has_doc:
        return VerificationResult(
            "supports", "docstring_presence",
            "the reviewed target carries no doc comment",
        )
    return _abstain(
        "docstring_presence",
        "the claim is about documentation content, which no rule decides",
    )


def verify_scope_placement(candidate: CandidateClaim, target: ChangeTarget,
                           **_context) -> VerificationResult:
    """Not implemented, and abstaining loudly is the honest state.

    Placement claims need file-level adjacency, which the change graph does not preserve:
    targets carry hunk-level spans, and on one measured file fourteen of them share a single
    line. Returning `abstain` keeps these claims diagnostic instead of inventing a check.
    """

    return _abstain(
        "scope_placement",
        "placement needs file-level adjacency, which hunk-level change targets do not record",
    )


#: The focused specs whose findings this verifier can adjudicate, and what each claims.
#: Keyed on the SPEC, not the issue kind: golf and idiom both declare
#: `proof_simplification` while making different claims, so a kind-keyed verifier would give
#: idiom's laxer warrant to golf. And `select.py` publishes on ANY claim-scoped `supports`,
#: so a lax assertion appended alongside the strict golf rule silently repeals it.
_PROOF_SPEC_REQUIRES_SHORTER = {"proof_golf": True, "proof_idiom": False}


def verify_proof_simplification(candidate: CandidateClaim, target: ChangeTarget,
                                **_context) -> VerificationResult:
    """Adjudicate a proof-simplification claim against what its spec actually asserts.

    Both specs require the statement to be untouched — a rewrite that changes the theorem is
    not a simplification of it. They differ on length: golf claims the proof gets shorter and
    is held to it; idiom explicitly claims the proof may already be short, so requiring
    brevity would reject every finding it is designed to make.

    Note what this does *not* prove. The whole-file recompile shows the replacement
    elaborates in context; it does not show it closes the same goal. Statement equality is
    the strongest available proxy, and it is a proxy.
    """

    from src.mathlib_review.evidence.statement_gate import compare_statements

    spec = candidate.spec_id
    if spec not in _PROOF_SPEC_REQUIRES_SHORTER:
        return _abstain(
            "proof_simplification",
            f"no proof-simplification warrant is defined for spec {spec!r}",
        )
    edit = candidate.proposed_edit
    replacement = getattr(edit, "new_declaration", None) if edit else None
    if not replacement:
        return _abstain("proof_simplification", "the claim carries no structured edit")

    original = target.reviewed_code or target.base_code or ""
    comparison = compare_statements(original, replacement)
    if comparison.verdict == "changed":
        return VerificationResult(
            "contradicts", "proof_simplification",
            f"the edit changes the statement, so it does not simplify this theorem's proof; "
            f"{comparison.detail}",
        )
    if comparison.verdict == "undecidable":
        return _abstain("proof_simplification", comparison.detail)

    if _PROOF_SPEC_REQUIRES_SHORTER[spec]:
        if len(replacement.strip()) >= len(original.strip()):
            return VerificationResult(
                "contradicts", "proof_simplification",
                f"a proof_golf finding must be shorter: {len(replacement.strip())} chars "
                f"replacing {len(original.strip())}",
            )
        return VerificationResult(
            "supports", "proof_simplification",
            f"the statement is unchanged and the proof is shorter "
            f"({len(original.strip())} -> {len(replacement.strip())} chars)",
        )
    return VerificationResult(
        "supports", "proof_simplification",
        "the statement is unchanged and the replacement elaborates in context",
    )


#: Issue kind -> the operator that can check it. A kind absent from this table abstains,
#: which is a truthful "no verifier exists" rather than a silent pass.
VERIFIERS = {
    "proof_simplification": verify_proof_simplification,
    "style_norm_violation": verify_style_norm,
    "naming_convention_violation": verify_naming_convention,
    "documentation_gap": verify_documentation_gap,
    "scope_placement": verify_scope_placement,
}


def verify(candidate: CandidateClaim, target: Optional[ChangeTarget],
           **context) -> VerificationResult:
    if candidate.issue_kind is None:
        return _abstain("none", "candidate declares no issue_kind")
    verifier = VERIFIERS.get(candidate.issue_kind)
    if verifier is None:
        return _abstain("none", f"no verifier for issue kind {candidate.issue_kind}")
    if target is None:
        return _abstain(verifier.__name__, "no change target for this candidate")
    return verifier(candidate, target, **context)
