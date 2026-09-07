"""What each obligation demands, on two axes: how much must be *seen*, and what must be *done*.

The scope axis existed already and only ever explained half of the failures. Codex's
observation supplies the other half, and PR 33117 is the case that shows why one axis is not
enough: the lead **did** recognise the duplicated `fun_*` family — it is in the run's own
assessments — and the specialist still failed, because knowing that thirteen lemmas are
hand-written duplicates does not tell you that `@[to_fun]` generates them, and nothing in the
contract lets one candidate carry the import, the attributes and the deletions together.
Context would not have fixed that. Capability would.

So every obligation carries both:

* **scope** — how much of the change must be in view to conclude it at all;
* **capability** — what the reviewer must be able to *do* once it has concluded it.

Hand-classified, from the maintainer's own comment rather than from the migrated claim, after
`obligation_audit` reconciled the two. The reasoning is recorded per row so a reader can
disagree with a specific call instead of the whole table.

Read this as a map of what to build, never as a target: it is derived from gold and must stay
strictly on the evaluation side. Nothing here may reach a prompt or a routing artifact.
"""

from __future__ import annotations

import collections
from dataclasses import dataclass
from typing import Dict, Sequence

#: How much must be in view.
SCOPES = ("site", "family", "file", "convention")

#: What must be possible once the problem is seen.
#:
#: `recognition` — noticing it, given what is already on screen.
#: `retrieval` — knowing something not in the diff: a library API, a stated convention.
#: `transformation` — designing the specific change, not merely naming the defect.
#: `coordinated` — making and verifying an edit that spans several declarations or files.
CAPABILITIES = ("recognition", "retrieval", "transformation", "coordinated")


@dataclass(frozen=True)
class Row:
    obligation: str
    pr_number: int
    scope: str
    capability: str
    why: str


#: Keyed by the distinctive middle of the obligation id, which is stable and short.
CLASSIFICATION: Sequence[Row] = (
    Row("6b02b6118fcd", 33421, "convention", "retrieval",
        "Renaming `round_eq'` to `round_eq_div` needs the norm that primed names should be "
        "made descriptive. Not in the diff, and not recoverable from corpus frequency — "
        "primed names are 3.4% of the library. It is stated in review: PR 17669, 'we want "
        "to move away from primed names'."),
    Row("38e72250fc9d", 33421, "family", "transformation",
        "'Factor out the repeated argument in the `tendsto_round_*` proofs … same change for "
        "the next theorem' — the repetition is only visible across several proofs, and the "
        "fix is a new lemma that must be designed, not just requested."),
    Row("55f6530478b3", 33421, "site", "transformation",
        "The hardcoded `2` is visible in the one declaration; producing the generalised "
        "`k`-version with its hypothesis is design work on that site."),
    Row("695ae9fd914c", 33362, "file", "recognition",
        "Whether declarations sit inside `namespace Complex` is a fact about the file's "
        "structure. Once seen it needs no design — move the block."),
    Row("ce7b5d2e038d", 33337, "convention", "retrieval",
        "`toLinearMap_` for coercion equalities: 50 uses against `coe_`'s 4,707, and absent "
        "from the local files. Unreachable from the code corpus; the review corpus is the "
        "only place it could come from."),
    Row("64e1164fcb58", 33337, "family", "coordinated",
        "'Rename X (and similarly Y)' — two declarations in two work units, so a unit-scoped "
        "candidate cannot carry both renames or verify them together."),
    Row("c9739efcd0a6", 33321, "site", "recognition",
        "A typo and an unfinished sentence, both visible in the docstring under review. This "
        "is the one the system already matches at resolution level."),
    Row("5ffba48eb1e1", 33321, "site", "transformation",
        "That the definition abuses the predicate/set defeq is visible at the site; the fix "
        "is the specific set-comprehension spelling."),
    Row("cc44bb996114", 33305, "site", "recognition",
        "An over-long doc line. Mechanically checkable, and the repository's own linter "
        "settles it."),
    Row("7f098f6a7437", 33294, "convention", "retrieval",
        "Dot-notation `IsFundamentalSequence.of_isNormal` over flat `*_of_*`. Corpus "
        "frequency argues the other way, 2,359 against 22,345; the convention appears in 224 "
        "review comments."),
    Row("8e276803d0f4", 33294, "site", "recognition",
        "`rw [Order.IsNormal.map_iSup h …]` should be `rw [h.map_iSup …]`. Visible in the "
        "line, and the fix is the line."),
    Row("073625ede35e", 33285, "site", "transformation",
        "Golfing to a direct lambda: the proof is on screen, the shorter proof has to be "
        "written and compiled."),
    Row("585e5e0b5b8b", 33285, "site", "transformation",
        "Replacing the manual injectivity/`ext`/`rfl` tail with a single `simp` call. The "
        "verbose tail is visible in the proof under review; the work is finding the simp set "
        "that closes the same goal and confirming it compiles."),
    Row("e83e6544d51c", 33145, "family", "coordinated",
        "Rename both lemmas *and* reprove the lower one by dualising the upper. Two renames "
        "and a proof rewrite across a family spanning four work units."),
    Row("bd8a8d8cf88c", 33145, "family", "coordinated",
        "Refactor into `Dense.ciSup`/`ciInf` and obtain the infimum by duality. The "
        "maintainer supplied the signatures and the dual proof in suggestion blocks; "
        "delivering them is still a multi-declaration edit."),
    Row("8d887ce4bdd9", 33145, "site", "transformation",
        "Generalising the supremum result into a typeclass-polymorphic `ciSup'`. The "
        "over-specialisation is visible in the one statement."),
    Row("7fef913e9651", 33145, "family", "coordinated",
        "Adding `ciInf'` and proving it from `ciSup'` in the order dual — the counterpart "
        "does not exist yet, so this is a claim about a pair."),
    Row("e8e028215fa3", 33145, "site", "transformation",
        "Restructuring the proof around a `by_cases` on `BddAbove`. Deep, but local: the "
        "system already matches this one at issue level."),
    Row("57bcc9fd3846", 33117, "family", "coordinated",
        "Import `Mathlib.Tactic.ToFun` and replace thirteen hand-written `fun_*` lemmas with "
        "`@[to_fun]`. The lead recognised the family and the specialist still failed: the "
        "mechanism is retrieval, and the fix is one import plus attributes plus deletions "
        "that must compile together."),
)


def by_scope() -> Dict[str, int]:
    return dict(sorted(collections.Counter(r.scope for r in CLASSIFICATION).items()))


def by_capability() -> Dict[str, int]:
    return dict(sorted(collections.Counter(r.capability for r in CLASSIFICATION).items()))


def cross_tab() -> Dict[str, Dict[str, int]]:
    """Scope against capability — the table that says what to build next."""

    table: Dict[str, Dict[str, int]] = {s: {c: 0 for c in CAPABILITIES} for s in SCOPES}
    for row in CLASSIFICATION:
        table[row.scope][row.capability] += 1
    return table


def report() -> Dict[str, object]:
    return {
        "obligations": len(CLASSIFICATION),
        "by_scope": by_scope(),
        "by_capability": by_capability(),
        "cross_tab": cross_tab(),
        # What no amount of context can fix: an obligation needing a coordinated edit cannot
        # be *resolved* by a reviewer confined to one work unit with one edit, however well
        # it is briefed.
        "needs_coordinated_edit": sum(
            1 for r in CLASSIFICATION if r.capability == "coordinated"),
    }
