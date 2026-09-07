"""How a lead composes its children — named, bounded, and sealed into the plan.

Coordination is the part of this design that has never been varied, and it is where the next
piece of research goes. Today every one of these decisions is a constant somewhere in
`lead.py` or `delegation.py`:

* two waves, because the prompt says "two waves beat one";
* a pair may run **at most once** (`lead.py`: `if invocation_id in state["requested"]`), so a
  specialist that exhausted its budget mid-verification is permanently lost and cannot be
  re-run at a higher tier even deliberately;
* the parent sees `JobOutcome.summary()` — counts, cost, and each claim truncated to 800
  characters — and nothing else: not the tool calls, not the retrieval, not the artifacts;
* a child sees its brief and nothing about its siblings;
* one merge at the end.

None of that is written down as a choice, so none of it can be changed as an experiment. This
module makes each one a field with a default equal to today's behaviour, so the first run after
it is unchanged and the second can differ in exactly one respect.

**Scheduling and synthesis are separate on purpose.** A `CoordinationPolicy` decides who runs,
how often, and what they see. A `SynthesisPolicy` decides what survives. Folding them together
would mean a coordination experiment silently changed what got published, and neither result
would be readable.

**Every strategy is bounded.** `max_rounds`, `max_jobs` and `max_redispatches_per_pair` are
required rather than optional, because a policy whose cost cannot be computed before it runs
cannot be preflighted — and the one lesson this pipeline keeps relearning is that an unbounded
budget is discovered on the invoice.
"""

from __future__ import annotations

from typing import Any, Dict, Literal

from pydantic import ConfigDict, Field

from src.mathlib_review.schema.review import StrictModel

#: Bumped when a field changes meaning, so two runs' policies can be told apart by more than
#: their hash.
COORDINATION_VERSION = "v5-coordination/1"


class CoordinationPolicy(StrictModel):
    """Who runs, how many times, and what each side sees."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["v5-coordination1"] = "v5-coordination1"

    #: How many times the lead may call `delegate`. Two is what every run so far did, and what
    #: the lead's prompt asks for.
    max_rounds: int = 2

    #: A ceiling on specialist jobs across all rounds, independent of cost. Mirrors
    #: `max_delegations`, which is where it is enforced today.
    max_jobs: int = 25

    #: How many times one (arm, work unit) pair may be re-dispatched.
    #:
    #: Zero today, and hardcoded: `delegate` rejects a pair already in `state["requested"]`
    #: with "already delegated". That rule was written to stop a confused lead from looping,
    #: and it also makes a budget-starved arm unrecoverable — the lead is not even told that
    #: budget was the cause, so it could not act on it if it were allowed to.
    max_redispatches_per_pair: int = 0

    #: What the parent is shown about each finished job.
    #:
    #: `summary` is today's behaviour: status, counts, cost, and each claim truncated. The
    #: alternatives exist to be tried, not because either is known better — `counts` tests
    #: whether the lead routes as well without reading claims at all, and `full` whether it
    #: routes better with the untruncated text.
    parent_view: Literal["counts", "summary", "full"] = "summary"

    #: What a child is shown about its siblings.
    #:
    #: `none` is today's behaviour and the only one implemented. `blackboard` would be an
    #: append-only artifact the coordinator owns, with children receiving read-only snapshots
    #: through their next brief — never a shared mutable directory and never sibling
    #: transcripts, both of which would break the isolation contract.
    sibling_view: Literal["none", "blackboard"] = "none"

    def bounds(self) -> Dict[str, int]:
        """The numbers preflight needs to price this policy before it runs."""

        return {
            "max_rounds": self.max_rounds,
            "max_jobs": self.max_jobs,
            "max_redispatches_per_pair": self.max_redispatches_per_pair,
        }

    def worst_case_jobs(self) -> int:
        """The most jobs this policy can dispatch, including re-dispatches."""

        return self.max_jobs * (1 + self.max_redispatches_per_pair)


class SynthesisPolicy(StrictModel):
    """What the lead's assessments are allowed to do to what came back."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["v5-synthesis-policy1"] = "v5-synthesis-policy1"

    #: How much authority the lead's assessments carry.
    #:
    #: * `router_only` — assessments are recorded and applied to nothing. The strictest
    #:   reading of "the lead routes, it does not adjudicate", and the cleanest baseline for
    #:   asking whether its judgment adds anything.
    #: * `subtractive` — **today's behaviour**. `synthesis.apply_assessments` drops and folds
    #:   candidates the lead marks, and the removed ones are projected into `findings.jsonl`
    #:   as `diagnostic` so the decision stays auditable. No rewrite path exists.
    #: * `final_arbiter` — the lead may also rewrite a finding's text. Not implemented, and
    #:   deliberately not defaulted into: a rewritten finding is a new revision, and
    #:   claim-scoped evidence gathered for the previous wording does not transfer to it. That
    #:   evidence would have to be rebound or re-run before the rewrite could be published.
    authority: Literal["router_only", "subtractive", "final_arbiter"] = "subtractive"

    def applies_removals(self) -> bool:
        return self.authority in {"subtractive", "final_arbiter"}

    def allows_rewrites(self) -> bool:
        return self.authority == "final_arbiter"


class CoordinationConfig(StrictModel):
    """The pair, sealed together so a run records how it coordinated."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["v5-coordination-config1"] = "v5-coordination-config1"
    coordination_version: Literal["v5-coordination/1"] = COORDINATION_VERSION
    coordination: CoordinationPolicy = Field(default_factory=CoordinationPolicy)
    synthesis: SynthesisPolicy = Field(default_factory=SynthesisPolicy)

    def report(self) -> Dict[str, Any]:
        """What to record in the plan and read back beside a result."""

        return {
            "coordination_version": self.coordination_version,
            "coordination": self.coordination.model_dump(mode="json"),
            "synthesis": self.synthesis.model_dump(mode="json"),
            "bounds": self.coordination.bounds(),
            "worst_case_jobs": self.coordination.worst_case_jobs(),
        }


def assert_implemented(config: CoordinationConfig) -> None:
    """Refuse a policy the code cannot honour, before anything is spent.

    A config field that is read but not implemented is worse than no field: the run records a
    policy it did not follow, and the result is attributed to a mechanism that never ran.
    """

    unimplemented = []
    if config.coordination.sibling_view != "none":
        unimplemented.append(
            "coordination.sibling_view='blackboard' — children currently see only their own "
            "brief; the coordinator-owned append-only artifact does not exist yet")
    if config.coordination.parent_view != "summary":
        unimplemented.append(
            f"coordination.parent_view={config.coordination.parent_view!r} — the lead is "
            "shown JobOutcome.summary() and there is no other projection yet")
    if config.coordination.max_redispatches_per_pair:
        unimplemented.append(
            "coordination.max_redispatches_per_pair > 0 — `delegate` rejects a pair already "
            "requested, and lifting that needs the re-dispatch path built")
    if config.synthesis.authority == "final_arbiter":
        unimplemented.append(
            "synthesis.authority='final_arbiter' — no rewrite path exists, and a rewritten "
            "finding cannot inherit the evidence gathered for its previous wording")
    if unimplemented:
        raise ValueError(
            "coordination policy asks for behaviour that is not implemented:\n  - "
            + "\n  - ".join(unimplemented)
            + "\nThe defaults describe what the code actually does."
        )
