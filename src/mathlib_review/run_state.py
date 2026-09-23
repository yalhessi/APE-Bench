"""What states a review run can be in, and which moves between them are legal.

Every transition below is already enforced somewhere -- `TaskExecutionStatus` in the
orchestrator, `completion_status` on the run manifest, the judge's refusal to score a run that
did not cover what it promised. What did not exist is a place that states the machine, so the
guarantee had to be assembled by reading three files and hoping they agreed. They did; the
reason to write it down is that the next change has somewhere to be checked against.

    planned ──▶ running ◀──▶ paused
                   │
                   ├──▶ generated ──▶ finalized ──▶ judged
                   └──▶ partial
                   └──▶ failed

**`paused` is not `partial`.** `paused` is a run state: work stopped on a budget or turn limit
and can resume. `partial` is a *closed* run that cannot satisfy required coverage -- a mandatory
job ran and failed, so a work unit was never reviewed. The distinction is the one that voided
two September runs: they closed `failed`, were scored anyway, and their recall was reported
against a denominator that included units nobody looked at.

**A partial run never enters the successful chain.** Forensic processing is allowed and
labelled: `judge --allow-partial` scores it and marks the output forensic. What is refused is
the silent path where a partial run is judged as though it were complete.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Sequence

from src.mathlib_review.io import sha256_file


class RunState(str, Enum):
    """The state of a whole review run, as opposed to one task's execution."""

    #: Sealed, priced, nothing spent. What `plan` produces and stops at.
    PLANNED = "planned"
    #: Model calls in flight.
    RUNNING = "running"
    #: Stopped on a limit, resumable. Spend is booked; nothing is concluded.
    PAUSED = "paused"
    #: Closed, and every mandatory job that was supposed to run did.
    GENERATED = "generated"
    #: Closed, and a mandatory job did not succeed. Numbers from here measure coverage loss.
    PARTIAL = "partial"
    #: Closed on an error that is not a coverage gap.
    FAILED = "failed"
    #: Findings assembled, channels assigned, `findings.jsonl` written.
    FINALIZED = "finalized"
    #: Scored against gold.
    JUDGED = "judged"


#: The only moves that are legal. A state absent as a key is terminal.
TRANSITIONS: Dict[RunState, FrozenSet[RunState]] = {
    RunState.PLANNED: frozenset({RunState.RUNNING}),
    RunState.RUNNING: frozenset({
        RunState.PAUSED, RunState.GENERATED, RunState.PARTIAL, RunState.FAILED}),
    # A resume goes back to running; it does not jump straight to a closed state, because the
    # thing that closes a run is reconciliation and that only happens after work stops.
    RunState.PAUSED: frozenset({RunState.RUNNING}),
    RunState.GENERATED: frozenset({RunState.FINALIZED}),
    RunState.FINALIZED: frozenset({RunState.JUDGED}),
    # `partial` and `failed` are terminal for the successful chain. Forensic reading of either
    # is allowed and is not a transition -- it produces a separately labelled artifact rather
    # than moving the run forward.
    RunState.PARTIAL: frozenset(),
    RunState.FAILED: frozenset(),
    RunState.JUDGED: frozenset(),
}

#: States a run may be scored from without `--allow-partial`.
SCOREABLE: FrozenSet[RunState] = frozenset({RunState.GENERATED, RunState.FINALIZED})


class IllegalTransition(RuntimeError):
    """A move the machine does not allow."""


def assert_transition(current: RunState, target: RunState) -> None:
    allowed = TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise IllegalTransition(
            f"a run cannot go {current.value} -> {target.value}. From {current.value} the "
            f"legal moves are {sorted(s.value for s in allowed) or 'none, it is terminal'}."
        )


def from_manifest(completion_status: str) -> RunState:
    """The manifest's vocabulary, mapped onto this one.

    `run_manifest.json` writes `complete` / `partial` / `failed`, which predate this module.
    They are not renamed: the string is in every manifest in the tree and renaming it would
    make old runs unreadable to say the same thing in different words.
    """

    return {
        "complete": RunState.GENERATED,
        "partial": RunState.PARTIAL,
        "failed": RunState.FAILED,
        "incomplete": RunState.PARTIAL,
    }.get(completion_status, RunState.FAILED)


# ============================================================================
# What a stage reads: the run's artifacts, their digests, and its state
# ============================================================================
#
# A v5 experiment is several processes chained by one run name typed correctly each time.
# `judge --of X` exists BECAUSE the three paths it derives were once three free-form strings
# and disagreed -- a judge scored rep1's findings under rep2's name and nothing errored. That
# fix was made for one stage and never generalised: `replay` re-implemented "find the previous
# stage's artifacts and check they belong together", and choosing the sessions for one
# diagnostic took an ad-hoc join across four files, written in a scratchpad and thrown away.
#
# `StageInput` is that hand-off, named once. It is deliberately NOT a scheduler: it computes no
# work and hides nothing. It resolves the artifacts a stage asks for, hashes exactly those, and
# says what state the run is in -- so what a stage read is recorded rather than reconstructed.


#: Every artifact a run directory can hold: name -> (filename, the stage that writes it,
#: whether it is appended to rather than written once, and what to say when it is missing).
#:
#: Append-only files are a real category here, not an implementation detail. `write_once`
#: refuses a second write with different bytes, which is the guarantee that makes a run
#: reproducible; the journal, the context trace, the execution index and the stage ledger are
#: written *while* work happens, so a crash must leave what already ran still findable.
RUN_ARTIFACTS: Dict[str, "ArtifactSpec"] = {}


@dataclass(frozen=True)
class ArtifactSpec:
    filename: str
    writer: str
    append_only: bool = False
    hint: str = ""


def _declare(name: str, filename: str, writer: str, append_only: bool = False,
             hint: str = "") -> None:
    """Register one artifact. Named `_declare` and not `_artifact`: the duplicate-helper guard
    reserves that name for `ArtifactRef` builders, and a third one appearing is exactly what it
    watches for."""

    RUN_ARTIFACTS[name] = ArtifactSpec(filename, writer, append_only, hint)


_declare("agenda", "agenda.json", "run")
_declare("agenda_report", "agenda_report.json", "run",
          hint="the only artifact recording which PRs a run enumerated work for, and therefore "
               "the only honest source for a recall denominator")
_declare("run_plan", "run_plan.json", "run")
_declare("run_manifest", "run_manifest.json", "run")
_declare("census", "census.json", "run")
_declare("arm_pool", "arm_pool.jsonl", "run",
          hint="gitignored, so a worktree has it only if linked from the main checkout; the "
               "rel050 reps lost theirs with a deleted worktree "
               "(docs/todo/operational-floor.md)")
_declare("arm_responses", "arm_responses.jsonl", "run")
_declare("delegations", "delegations.jsonl", "run")
_declare("candidate_assessments", "candidate_assessments.jsonl", "run")
_declare("comprehension", "comprehension.jsonl", "run")
_declare("context_trace", "context_trace.jsonl", "run", append_only=True)
_declare("execution_index", "execution_index.jsonl", "run", append_only=True)
_declare("candidates_discovered", "candidates_discovered.jsonl", "run")
_declare("findings", "findings.jsonl", "run")
_declare("issues", "issues.jsonl", "run")
_declare("conflicts", "conflicts.jsonl", "run")
_declare("finalization_report", "finalization_report.json", "run")
_declare("reviewed_workspaces", "reviewed_workspaces.json", "run")
_declare("replay_outcomes", "replay_outcomes.jsonl", "replay")
_declare("replay_report", "replay_report.json", "replay")
_declare("stages", "stages.jsonl", "*", append_only=True)

#: What a judge run writes, under the audit directory rather than the run directory.
AUDIT_ARTIFACTS: Dict[str, str] = {
    "semantic_pairs": "semantic_pairs.jsonl",
    "semantic_matches": "semantic_matches.jsonl",
    "semantic_report": "semantic_report.json",
    "publication_report": "publication_report.json",
    "sample_votes": "sample_votes.jsonl",
    "adjudication_report": "adjudication_report.json",
}


class MissingArtifact(FileNotFoundError):
    """A stage asked for something the run it reads did not write."""


def state_of(directory: Path) -> RunState:
    """What state the run in this directory is in, from its own artifacts.

    Derived, never stored. The manifest is the authority on how generation ended -- its
    `complete`/`partial`/`failed` vocabulary predates this module and is deliberately not
    renamed -- and the rest is read off what exists:

    * `findings.jsonl` beside a complete manifest means finalization ran. It is not a separate
      manifest field because `finalize` runs BEFORE `reconcile` writes the manifest, so a
      partial run has findings too; `FINALIZED` is reserved for a run that also covered what it
      promised.
    * a non-forensic `judge` row in the stage ledger means it was scored. Not the presence of
      an audit directory: an audit can be written by hand, and `--allow-partial` writes one
      deliberately marked forensic.
    """

    manifest_path = directory / RUN_ARTIFACTS["run_manifest"].filename
    if manifest_path.is_file():
        state = from_manifest(json.loads(
            manifest_path.read_text(encoding="utf-8")).get("completion_status"))
        if state is RunState.GENERATED:
            if any(row.get("stage") == "judge" and not row.get("forensic")
                   for row in ledger(directory)):
                return RunState.JUDGED
            if (directory / RUN_ARTIFACTS["findings"].filename).is_file():
                return RunState.FINALIZED
        return state
    if (directory / RUN_ARTIFACTS["run_plan"].filename).is_file():
        # Sealed and spent, with no manifest: the run started and did not close. Not `PAUSED`,
        # which is a claim about resumability that only the samples can support.
        return RunState.RUNNING
    return RunState.PLANNED


def ledger(directory: Path) -> List[Dict[str, Any]]:
    """Every stage row this run has, in the order written."""

    from src.mathlib_review.io import appended_rows

    return appended_rows(Path(directory) / RUN_ARTIFACTS["stages"].filename)


def append_stage(directory, record) -> Path:
    """Add one stage row to a run's ledger.

    Appended, never written once: a stage that crashes between writing its artifacts and
    writing its row must leave the artifacts findable, and `report stages` saying "a manifest
    with no run row" is more useful than a row that lies. `--redo` removes the ledger with the
    run it discards, which is right -- the rows describe that run and it no longer exists.
    """

    from src.mathlib_review.io import append_jsonl

    return append_jsonl(Path(directory) / RUN_ARTIFACTS["stages"].filename, record)


def stage_record(stage: str, *, run_name: str, produced: Optional[Dict[str, str]] = None,
                 identity: Optional[Dict[str, Any]] = None,
                 consumed: Optional[Dict[str, str]] = None,
                 consumed_audit: Optional[Dict[str, str]] = None,
                 node: Optional[str] = None, pipeline: Optional[str] = None,
                 state_before: Optional["RunState"] = None,
                 state_after: Optional["RunState"] = None,
                 transition: Optional[str] = None, forensic: bool = False,
                 evaluation_contract_version: Optional[str] = None):
    """A `StageRecord` with the provenance every row carries filled in the same way.

    Git state and the timestamp are read here rather than by each stage, because a row whose
    provenance depends on which caller remembered to add it is not provenance.
    """

    from datetime import datetime, timezone

    from src.mathlib_review.io import git_state
    from src.mathlib_review.schema.runs import StageRecord

    commit, tree_state = git_state()
    return StageRecord(
        stage=stage, node=node, pipeline=pipeline, run_name=run_name,
        consumed=dict(consumed or {}), consumed_audit=dict(consumed_audit or {}),
        produced=dict(produced or {}), identity=dict(identity or {}),
        state_before=state_before.value if state_before else None,
        state_after=state_after.value if state_after else None,
        transition=transition, forensic=forensic,
        evaluation_contract_version=evaluation_contract_version,
        git_commit=commit, git_tree_state=tree_state,
        written_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def digests_of(paths) -> Dict[str, str]:
    """`display_path -> sha256` for the artifacts a stage wrote that exist."""

    from src.mathlib_review.io import display_path, sha256_file

    return {display_path(Path(path)): sha256_file(Path(path))
            for path in paths if Path(path).is_file()}


@dataclass(frozen=True)
class StageInput:
    """One run as a stage reads it: where it is, what it holds, and whether it may be used.

    Hashes only what the stage asked for. `context_trace.jsonl` runs to tens of megabytes and
    only the bucket report reads it, so hashing everything by default would make every stage
    pay for the most expensive reader.
    """

    run_name: str
    run_dir: Path
    release: Optional[Path]
    state: RunState
    manifest: Optional[Dict[str, Any]]
    #: artifact name -> sha256, for exactly the artifacts `require` named.
    consumed: Dict[str, str]
    audit_dir: Optional[Path] = None
    consumed_audit: Dict[str, str] = field(default_factory=dict)
    ledger: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def at(cls, directory, *, run_name: Optional[str] = None, audit_dir=None,
           require: Sequence[str] = (), allow_partial: bool = False) -> "StageInput":
        """Read a run directory directly.

        `at` rather than only `of` because the judge resolves its source from
        `Path(dataset.candidates).parent`: an override that scores one run's findings into a
        second audit is legitimate, and so is a hand-assembled candidates file in a temp
        directory with no run name at all.
        """

        directory = Path(directory)
        state = state_of(directory)
        manifest_path = directory / RUN_ARTIFACTS["run_manifest"].filename
        manifest = (json.loads(manifest_path.read_text(encoding="utf-8"))
                    if manifest_path.is_file() else None)
        # Refused on the manifest's word, not on the derived state. A directory with no
        # manifest is UNCHECKED, not bad: v4 runs never wrote one and a hand-assembled
        # candidates file has no run at all, and refusing those would be a new rule wearing a
        # refactor's clothes. What is refused is a run that closed and said it did not cover
        # what it promised.
        if manifest is not None and state not in SCOREABLE | {RunState.JUDGED} \
                and not allow_partial:
            gaps = manifest.get("coverage_gaps") or []
            raise ValueError(
                f"source run {manifest.get('run_name')!r} closed as "
                f"{manifest.get('completion_status')!r}"
                + (f" with {len(gaps)} coverage gap(s): "
                   + ", ".join(sorted(g.get("invocation_id", "?") for g in gaps)[:6])
                   if gaps else "")
                + ". Recall from it is measured against work units that were never reviewed, "
                "so it is not comparable to a complete run. Set `dataset.allow_partial: true` "
                "to score it anyway -- the output is forensic and must not be reported as a "
                "headline number."
            )

        consumed = {}
        for name in require:
            consumed[name] = sha256_file(_require(directory, name))
        consumed_audit = {}
        if audit_dir is not None:
            audit_dir = Path(audit_dir)
            for name, filename in AUDIT_ARTIFACTS.items():
                path = audit_dir / filename
                if path.is_file():
                    consumed_audit[name] = sha256_file(path)

        return cls(
            run_name=run_name or directory.name, run_dir=directory,
            release=_release_of(directory), state=state, manifest=manifest,
            consumed=consumed, audit_dir=audit_dir, consumed_audit=consumed_audit,
            ledger=ledger(directory))

    @classmethod
    def of(cls, run_name: str, *, audit=False, require: Sequence[str] = (),
           allow_partial: bool = False) -> "StageInput":
        """Read the run by name, and optionally the audit its name implies.

        `audit=True` resolves the default judge node; `audit="<node>"` resolves a named one, so
        a run carrying two judgements can be read as either.
        """

        from src.mathlib_review.judge.runner import derive_from_run
        from src.mathlib_review.paths import run_dir

        audit_dir = None
        if audit:
            node = "judge" if audit is True else str(audit)
            audit_dir = derive_from_run(run_name, node)["out_dir"]
        return cls.at(run_dir(run_name), run_name=run_name, audit_dir=audit_dir,
                      require=require, allow_partial=allow_partial)

    def path(self, name: str) -> Path:
        """One artifact, refusing by name rather than by `FileNotFoundError` three frames on."""

        return _require(self.run_dir, name)

    def audit_path(self, name: str) -> Path:
        if self.audit_dir is None:
            raise MissingArtifact(
                f"{self.run_name} was read without an audit, so {name!r} cannot be resolved. "
                f"Read it with `audit=True`, and judge the run first if it has not been.")
        path = self.audit_dir / AUDIT_ARTIFACTS[name]
        if not path.is_file():
            raise MissingArtifact(
                f"{path} does not exist. It is written by `judge`; run "
                f"`cli judge --of {self.run_name} --config <judge config> --execute` first.")
        return path

    @property
    def forensic(self) -> bool:
        """Whether anything read from this run is forensic rather than a measurement.

        A run whose manifest says it did not cover what it promised. Not the same as
        `unchecked`: one is a run that reported a gap, the other is a run that reported
        nothing.
        """

        return self.manifest is not None and self.state not in SCOREABLE | {RunState.JUDGED}

    @property
    def unchecked(self) -> bool:
        """No manifest, so completeness was never established either way."""

        return self.manifest is None


def _require(directory: Path, name: str) -> Path:
    spec = RUN_ARTIFACTS.get(name)
    if spec is None:
        raise KeyError(f"unknown run artifact {name!r}; known: {sorted(RUN_ARTIFACTS)}")
    path = Path(directory) / spec.filename
    if not path.is_file():
        raise MissingArtifact(
            f"{path} does not exist. It is written by the `{spec.writer}` stage"
            + (f". {spec.hint}" if spec.hint else "."))
    return path


def _release_of(directory: Path) -> Optional[Path]:
    """The release this run was built from, taken from its own sealed agenda.

    From the agenda rather than from a config, for the reason `judge --of` exists: the config
    that produced a run is not recoverable from the run, and the agenda is.
    """

    path = Path(directory) / RUN_ARTIFACTS["agenda"].filename
    if not path.is_file():
        return None
    release = json.loads(path.read_text(encoding="utf-8")).get("release")
    return Path(release) if release else None
