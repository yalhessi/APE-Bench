"""External evidence collection and packet assembly for c1 candidates."""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .io import COMPILED_TARGET, canonical_json_bytes, jsonl_bytes, sha256_bytes, write_once
from .verifiers import VERIFIER_VERSION, verify
from .schema import (
    CandidateClaim, ChangeGraph, EvidenceArtifact, EvidenceAssertion, EvidencePacket,
    ReviewEpisodeBoundary, SourceEvent,
)
from src.mathlib_review.workspace import run, tool_env

from .retrieval import retrieve_payloads


#: Both moved to `mathlib_review.workspace`, which is where a primitive four modules in two
#: packages already import belongs. Kept as names here because this module's own call sites
#: use them; nothing outside should.
_tool_env = tool_env
_run = run


#: What a claim actually asserts, as opposed to the topic its arm declares.
#:
#: Every collector used to gate on `concern_family`, which is the arm's own label for its
#: subject area. That silently refused checkable claims: on heldout11 rep2 an agent wrote
#: "`Meromorphic.add` is duplicated by `Meromorphic.fun_add`" — a duplication assertion
#: `repository_search` could settle — and filed it under `style`, so the search ran, found
#: the declarations, and returned `inconclusive` because the *label* was wrong. Meanwhile
#: `policy` refused to run the repository's own linter on anything not called `style`, so
#: an over-long line in a docstring came back "no machine-checkable local policy is
#: registered for 'documentation'".
#:
#: `issue_kind` is the field that says what is being claimed, and it already routes the
#: issue-kind verifiers. Collectors now route on it too, falling back to `concern_family`
#: for candidates old enough to predate it.

#: Claims the repository's own style checker can adjudicate: anything that is a property of
#: the changed file's text. A docstring line that is too long is a lint violation whoever
#: files it.
POLICY_CHECKABLE_KINDS = frozenset({"style_norm_violation", "documentation_gap"})

#: Claims that are settled by whether something already exists in the library.
SEARCH_CHECKABLE_KINDS = frozenset({
    "duplicate_implementation", "missed_canonical_api", "generalization_available",
})


def _asserts(candidate, kinds, families) -> bool:
    """Whether this claim makes a proposition the collector can decide.

    Reads `issue_kind` first and `concern_family` only as a fallback, so a claim filed under
    the wrong topic is still checked for what it actually says.
    """

    if getattr(candidate, "issue_kind", None):
        return candidate.issue_kind in kinds
    return candidate.concern_family in families


def candidate_spans(candidate: CandidateClaim, graph: ChangeGraph) -> Dict[str, List[Tuple[int, int]]]:
    entities = {item.entity_id: item for item in graph.entities}
    ranges = {item.range_id: item for item in graph.changed_ranges}
    targets = {item.change_id: item for item in graph.targets}
    spans: Dict[str, List[Tuple[int, int]]] = {}
    for change_id in candidate.change_ids:
        target = targets[change_id]
        target_spans = [
            (entities[entity_id].span.line_start, entities[entity_id].span.line_end)
            for entity_id in target.reviewed_entity_ids
            if entity_id in entities and entities[entity_id].side == "reviewed"
        ]
        if not target_spans:
            target_spans = [
                (ranges[range_id].reviewed_span.line_start, ranges[range_id].reviewed_span.line_end)
                for range_id in target.changed_range_ids
                if range_id in ranges and ranges[range_id].reviewed_span is not None
            ]
        spans.setdefault(target.path, []).extend(target_spans)
    return spans


def diagnostic_lines(output: str, path: str) -> List[int]:
    escaped = re.escape(path)
    patterns = [rf"(?:^|\s|/){escaped}:(\d+):", rf"file=(?:[^,]*/)?{escaped},line=(\d+)"]
    return [int(match) for pattern in patterns for match in re.findall(pattern, output, re.MULTILINE)]


def _has_target_diagnostic(output: str, path: str, spans: Dict[str, List[Tuple[int, int]]]) -> bool:
    return any(start <= line <= end for line in diagnostic_lines(output, path)
               for start, end in spans.get(path, []))


def _artifact(candidate, collector, kind, polarity, content, source_ref, occurred_at=None):
    payload = {"candidate_id": candidate.candidate_id, "collector": collector, "kind": kind,
               "polarity": polarity, "content": content, "source_ref": source_ref,
               "occurred_at": occurred_at}
    digest = sha256_bytes(canonical_json_bytes(payload))
    return EvidenceArtifact(artifact_id=f"artifact:{digest[:24]}", source_sha256=digest, **payload)


def _assertion(candidate, artifacts, polarity, claim, assertion_scope="claim"):
    payload = {"candidate_id": candidate.candidate_id,
               "artifact_ids": [item.artifact_id for item in artifacts],
               "assertion_scope": assertion_scope, "polarity": polarity,
               "claim": claim, "producer": "collector"}
    digest = sha256_bytes(canonical_json_bytes(payload))
    return EvidenceAssertion(assertion_id=f"assertion:{digest[:24]}", source_sha256=digest, **payload)


#: Words that look like Lean identifiers but carry no discriminating power. Kept small and
#: explicit — a long stoplist would be doing the job the identifier shape should do.
_SEARCH_STOPWORDS = frozenset({
    "theorem", "lemma", "def", "find", "search", "primary", "requested_change",
    "replace", "existing", "declaration", "mathlib", "instead", "already", "exists",
    "generalize", "generalise", "duplicate", "duplicates", "statement", "proof", "with",
    "this", "that", "the", "and", "for", "from", "new", "use", "using", "should",
})

#: A Lean identifier worth searching for. Two accepted shapes, because Mathlib uses both:
#:   * dotted or snake_cased  — `Finset.sum_comm`, `equitableOn_empty`
#:   * CamelCase with >=2 humps — `IsSeparated`, `EquitableOn`
#:
#: The two-hump rule is what separates a type name from a capitalised English word: "Replace"
#: and "Mathlib" have one capital and are rejected, `ExistingFoo` has two and is kept.
#: Requiring a separator alone would have silently excluded every structure and class, i.e.
#: exactly the declarations a duplication claim about a new type would cite.
_SEPARATED_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_']*(?:[._][A-Za-z0-9_']+)+")
_CAMEL_RE = re.compile(r"[A-Z][A-Za-z0-9']*")


def _is_identifier_shaped(term: str) -> bool:
    if _SEPARATED_RE.fullmatch(term):
        return True
    return bool(_CAMEL_RE.fullmatch(term)) and sum(c.isupper() for c in term) >= 2


def searchable_identifiers(query: str) -> List[str]:
    """Extract identifier-shaped terms from a candidate's query.

    This used to tokenise the model's own prose on `[A-Za-z_][A-Za-z0-9_'.]{2,}` with a
    seven-word stoplist, so a duplication query yielded terms like `['Finset.sum_comm',
    'Replace', 'the', 'new', 'declaration', 'with', ...]`. Since the hit test accepted a file
    if *any* term appeared in it, and `'the'` occurs in 193 of 200 sampled Mathlib files,
    every duplication and generalization candidate obtained a `supports` verdict — on the
    evidence that its prose contained an English word.

    Requiring a dotted or snake_cased shape means only things that could actually name a
    declaration are searched for.
    """

    found = []
    for raw in re.findall(r"[A-Za-z_][A-Za-z0-9_'.]*", query or ""):
        cleaned = raw.strip(".'_")
        if not cleaned or cleaned.lower() in _SEARCH_STOPWORDS:
            continue
        if _is_identifier_shaped(cleaned):
            found.append(cleaned)
    return sorted(set(found))


def declares_identifier(text: str, identifier: str) -> bool:
    """True when `text` *declares* the identifier, not merely mentions it.

    A substring test matched a name inside a comment, an import, or another name that
    happens to contain it. A duplication claim is about an existing declaration, so the
    evidence has to be a declaration.
    """

    leaf = identifier.rsplit(".", 1)[-1]
    pattern = (
        r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+|noncomputable\s+|public\s+)*"
        r"(?:theorem|lemma|def|abbrev|instance|structure|class|inductive)\s+"
        rf"(?:[A-Za-z_][A-Za-z0-9_'.]*\.)?{re.escape(leaf)}\b"
    )
    return re.search(pattern, text, re.MULTILINE) is not None


def snapshot_workspace(base_sha: Optional[str]) -> Optional[Path]:
    """The complete checkout for one commit, from the toolkit's own workspace cache.

    Run workspaces are deliberately partial: the runtime hardlinks the unmodified tree and
    materializes files on demand, so a task's `target/` holds tens of `.lean` files rather
    than Mathlib's ~7400. That is the right trade for running tasks and the wrong input for a
    corpus measurement — a naming population read from it is a 2% sample that still clears
    `MIN_SUPPORT`.

    The complete trees already exist. `RestoreManager` keeps one compiled workspace per
    commit under `<repo>/workspaces/<sha>`, shared across every run; all 16 medium episodes'
    base snapshots are present, each with ~7425 modules. Reading the population from there is
    snapshot-exact — the population question is "what does the corpus look like *before* this
    PR" — and costs nothing, because the tree is already materialized.

    Returns None when the commit is not cached, which makes the verifier abstain rather than
    fall back to the partial tree.
    """

    if not base_sha:
        return None
    try:
        from ape.toolkits.execute.lean.config import LeanVerifyToolConfig

        config = LeanVerifyToolConfig()
        repo_name, _url = config.resolve_repo(None)
        candidate = config.get_workspace_dir(repo_name) / base_sha
    except Exception:
        return None
    return candidate if (candidate / "Mathlib").is_dir() else None


class LazyPopulationScan:
    """A naming population scan built on first use and shared across candidates.

    `verify_naming_convention` abstains without a scan, and nothing passed one: the parameter
    existed on `collect_candidate` and no caller filled it, so every naming claim was
    undecidable in production regardless of its merit. Measured on the 4-PR `/12` smoke, that
    was 5 of 30 candidates — the largest recoverable block of abstains.

    Lazy and cached because the scan is a full parse of the Mathlib source tree. Building it
    eagerly per episode would pay that cost even for a run containing no naming claim at all,
    and building it per candidate would pay it repeatedly for the same snapshot.

    A scan that cannot be built — no source tree, unreadable workspace — resolves to `None`,
    which the verifier reads as "no scan supplied" and abstains on. Abstaining is the honest
    outcome; substituting a partial scan would let a missing corpus read as a naming norm.
    """

    def __init__(self, workspace: Optional[Path], cache: Dict[str, object]):
        self._workspace = workspace
        self._cache = cache

    def _scan(self):
        if self._workspace is None:
            return None
        key = str(self._workspace)
        if key not in self._cache:
            from .operators.naming_norm import scan_population
            try:
                scan = scan_population(self._workspace, key)
            except (FileNotFoundError, OSError, ValueError):
                scan = None
            # A partial checkout is not a snapshot. Review workspaces materialize the full
            # directory tree but only the files a task touches, and a scan of ~2% of Mathlib
            # still yields subjects that clear `MIN_SUPPORT` — sampling artifacts that would
            # be published as repository measurements. Treated as no scan at all.
            if scan is not None and not scan.is_representative():
                scan = None
            self._cache[key] = scan
        return self._cache[key]

    def available(self) -> bool:
        """Whether a scan could actually be built, so a failure is not read as a finding."""

        return self._scan() is not None

    def population(self, subject_token: str):
        scan = self._scan()
        return scan.population(subject_token) if scan is not None else None


def collect_candidate(
    candidate: CandidateClaim, graph: ChangeGraph, workspace: Optional[Path] = None,
    boundary: Optional[ReviewEpisodeBoundary] = None,
    events: Optional[Iterable[SourceEvent]] = None,
    baseline_compile_cache: Optional[Dict[Tuple[str, str], object]] = None,
    naming_population_scan=None,
) -> Tuple[List[EvidenceArtifact], List[EvidenceAssertion], EvidencePacket]:
    """Run deterministic collectors; unsupported tools become explicit terminal failures."""
    targets = {item.change_id: item for item in graph.targets}
    artifacts, assertions, completed, failures = [], [], set(), {}
    target_text = "\n\n".join(
        (targets[cid].reviewed_code or "") + "\n" + "".join(targets[cid].diff_fragments)
        for cid in candidate.change_ids
    )
    local = _artifact(candidate, "local_context", "target_context", "neutral", target_text,
                      ",".join(candidate.change_ids))
    artifacts.append(local)
    completed.add("local_context")

    for request in candidate.evidence_requests:
        collector = request.collector
        if collector == "local_context":
            assertions.append(_assertion(candidate, [local], "inconclusive",
                                         "Local context was preserved but is not independent support.",
                                         "context"))
        elif collector == "repository_search":
            if workspace is None:
                failures[collector] = "workspace_not_supplied"
                continue
            terms = searchable_identifiers(request.query)
            if not terms:
                # A duplication claim that names no Lean identifier cannot be checked by
                # search. Recording the failure keeps it `inconclusive` rather than letting
                # the absence of a query read as an absence of duplicates.
                failures[collector] = "query_has_no_identifier_terms"
                continue
            hits = []
            target_paths = {targets[cid].path for cid in candidate.change_ids}
            for path in sorted(workspace.rglob("*.lean")):
                rel = str(path.relative_to(workspace))
                if rel in target_paths:
                    continue
                try:
                    text = path.read_text(errors="replace")
                except OSError:
                    continue
                matched = [term for term in terms if declares_identifier(text, term)]
                if matched:
                    hits.append(f"{rel} :: {', '.join(sorted(matched))}")
                if len(hits) == 20:
                    break
            polarity = "support" if hits else "counterevidence"
            item = _artifact(candidate, collector, "search_result", polarity,
                             "\n".join(hits) if hits else "No matching repository files found.",
                             f"workspace:{workspace}")
            artifacts.append(item)
            externally_checkable = _asserts(
                candidate, SEARCH_CHECKABLE_KINDS, {"duplication", "generalization"})
            if hits and externally_checkable:
                verdict = "supports"
            elif not hits and externally_checkable:
                verdict = "contradicts"
            else:
                verdict = "inconclusive"
            assertions.append(_assertion(
                candidate, [item], verdict,
                f"Repository search for {sorted(terms)} found {len(hits)} file(s) "
                f"declaring a cited identifier."))
            completed.add(collector)
        elif collector == "lean_compile":
            edit = candidate.proposed_edit
            if workspace is None:
                failures[collector] = "workspace_not_supplied"
                continue
            candidate_paths = sorted({targets[cid].path for cid in candidate.change_ids})
            compile_path = edit.path if edit is not None else candidate_paths[0]
            matching = [targets[cid] for cid in candidate.change_ids if targets[cid].path == compile_path]
            source_path = workspace / compile_path
            if not matching or not source_path.is_file():
                failures[collector] = "compile_path_not_in_candidate_targets"
                continue
            source = source_path.read_text()
            cache_key = (str(workspace.resolve()), compile_path)
            baseline = (baseline_compile_cache or {}).get(cache_key)
            if baseline is None:
                try:
                    baseline = _run(["lake", "env", "lean", str(source_path)], workspace)
                except (OSError, subprocess.TimeoutExpired) as exc:
                    failures[collector] = f"lean_process_failed:{type(exc).__name__}"
                    continue
                if baseline_compile_cache is not None:
                    baseline_compile_cache[cache_key] = baseline
            baseline_output = (baseline.stdout + "\n" + baseline.stderr).strip()[-8000:]
            spans = candidate_spans(candidate, graph)
            relevant_failure = baseline.returncode != 0 and _has_target_diagnostic(
                baseline_output, compile_path, spans)
            baseline_item = _artifact(
                candidate, collector, "compile_result",
                "support" if relevant_failure else "neutral",
                f"state=baseline\nexit_code={baseline.returncode}\n{baseline_output}",
                f"workspace:{workspace}:{compile_path}:baseline",
            )
            artifacts.append(baseline_item)
            completed.add(collector)
            if edit is None:
                verdict = ("supports" if candidate.concern_family == "correctness" and relevant_failure
                           else "inconclusive")
                assertions.append(_assertion(
                    candidate, [baseline_item], verdict,
                    f"Reviewed file compiles={baseline.returncode == 0}; "
                    f"target-local diagnostic={relevant_failure}."))
                continue

            replacement = edit.new_declaration if edit.new_declaration is not None else edit.replacement
            if replacement is None:
                failures[collector] = "structured_edit_has_no_replacement"
                continue
            old = None
            if edit.new_declaration is not None:
                old = next((item.reviewed_code for item in matching
                            if item.reviewed_code and item.reviewed_code in source), None)
                if old is None or source.count(old) != 1:
                    failures[collector] = "complete_declaration_not_uniquely_located"
                    continue
                edited = source.replace(old, replacement, 1)
            elif edit.line_start is not None and edit.line_end is not None:
                lines = source.splitlines(keepends=True)
                if edit.line_end > len(lines) or edit.line_end < edit.line_start:
                    failures[collector] = "invalid_edit_line_span"
                    continue
                old = "".join(lines[edit.line_start - 1:edit.line_end])
                edited = ("".join(lines[:edit.line_start - 1]) + replacement.rstrip("\n") + "\n" +
                          "".join(lines[edit.line_end:]))
            else:
                failures[collector] = "structured_edit_has_no_location"
                continue
            with tempfile.NamedTemporaryFile(suffix=".lean", mode="w", delete=False) as handle:
                handle.write(edited)
                temp_path = Path(handle.name)
            try:
                edited_proc = _run(["lake", "env", "lean", str(temp_path)], workspace)
            except (OSError, subprocess.TimeoutExpired) as exc:
                failures[collector] = f"lean_edit_process_failed:{type(exc).__name__}"
                temp_path.unlink(missing_ok=True)
                continue
            temp_path.unlink(missing_ok=True)
            edited_output = (edited_proc.stdout + "\n" + edited_proc.stderr).strip().replace(
                str(temp_path), COMPILED_TARGET)[-8000:]
            edited_item = _artifact(
                candidate, collector, "compile_result",
                "support" if edited_proc.returncode == 0 else "counterevidence",
                f"state=proposed_edit\nexit_code={edited_proc.returncode}\n{edited_output}",
                f"workspace:{workspace}:{compile_path}:proposed_edit",
            )
            artifacts.append(edited_item)
            shorter = len(replacement.strip()) < len((old or "").strip())
            if candidate.concern_family == "correctness" and relevant_failure:
                claim_verdict = "supports"
            elif (candidate.concern_family == "proof-golf" and baseline.returncode == 0 and
                  edited_proc.returncode == 0 and shorter):
                claim_verdict = "supports"
            else:
                claim_verdict = "inconclusive"
            assertions.append(_assertion(
                candidate, [baseline_item, edited_item], claim_verdict,
                f"Baseline compiles={baseline.returncode == 0}; target-local diagnostic="
                f"{relevant_failure}; compiling shorter replacement="
                f"{edited_proc.returncode == 0 and shorter}."))
            edit_verdict = "supports" if edited_proc.returncode == 0 else "contradicts"
            assertions.append(_assertion(
                candidate, [edited_item], edit_verdict,
                f"Proposed edit compiles={edited_proc.returncode == 0}.", "proposed_edit"))
        elif collector == "policy":
            if workspace is None:
                failures[collector] = "workspace_not_supplied"
                continue
            if not _asserts(candidate, POLICY_CHECKABLE_KINDS, {"style"}):
                item = _artifact(
                    candidate, collector, "policy_text", "neutral",
                    f"No machine-checkable local policy is registered for {candidate.concern_family!r}.",
                    "policy-registry:pr-review-v4/1",
                )
                artifacts.append(item)
                completed.add(collector)
                assertions.append(_assertion(
                    candidate, [item], "inconclusive",
                    "The repository snapshot contains no applicable registered policy checker."))
                continue
            script = workspace / "scripts" / "lint-style.py"
            if not script.is_file():
                failures[collector] = "style_policy_checker_missing"
                continue
            spans = candidate_spans(candidate, graph)
            policy_items, relevant_violations = [], []
            try:
                for path in sorted({targets[cid].path for cid in candidate.change_ids}):
                    proc = _run([sys.executable, str(script), path], workspace, timeout=60)
                    output = (proc.stdout + "\n" + proc.stderr).strip()[-8000:]
                    relevant = proc.returncode == 1 and _has_target_diagnostic(output, path, spans)
                    relevant_violations.append(relevant)
                    policy_items.append(_artifact(
                        candidate, collector, "policy_result", "support" if relevant else "neutral",
                        f"checker=scripts/lint-style.py\nexit_code={proc.returncode}\n{output}",
                        f"workspace:{workspace}:scripts/lint-style.py:{path}",
                    ))
            except (OSError, subprocess.TimeoutExpired) as exc:
                failures[collector] = f"style_policy_process_failed:{type(exc).__name__}"
                continue
            artifacts.extend(policy_items)
            completed.add(collector)
            verdict = "supports" if any(relevant_violations) else "inconclusive"
            assertions.append(_assertion(
                candidate, policy_items, verdict,
                f"Repository-owned style checker reported a target-local violation="
                f"{any(relevant_violations)}."))
        elif collector == "precedent":
            if boundary is None or events is None:
                failures[collector] = "precedent_corpus_not_supplied"
                continue
            precedents = retrieve_payloads(boundary, events, request.query)
            if not precedents:
                failures[collector] = "no_temporally_eligible_precedent"
                continue
            items = [_artifact(candidate, collector, "precedent", "neutral", body,
                               event.event_id, occurred_at=event.occurred_at)
                     for event, body in precedents]
            artifacts.extend(items)
            completed.add(collector)
            assertions.append(_assertion(
                candidate, items, "inconclusive",
                "Historical comments are transfer hints and cannot independently support this finding.",
                "context"))

    # Issue-kind verification. `concern_family` names a topic and no collector can verify a
    # topic — measured: 0 of 33 candidates on the 4-PR smoke obtained a claim-scoped
    # `supports`, and 12 of them belonged to families no collector could ever support.
    # `issue_kind` routes the claim to the operator that can check it.
    verification = verify(
        candidate, targets.get(candidate.primary_change_id),
        population_scan=naming_population_scan,
    )
    if verification.decided:
        polarity = "supports" if verification.verdict == "supports" else "contradicts"
        verification_artifact = _artifact(
            candidate, "issue_kind_verifier", "verification",
            "support" if polarity == "supports" else "counterevidence",
            f"issue_kind={candidate.issue_kind}; verifier={verification.verifier}; "
            f"verdict={verification.verdict}; {verification.detail}",
            f"verifier:{VERIFIER_VERSION}:{candidate.issue_kind}",
        )
        artifacts.append(verification_artifact)
        assertions.append(_assertion(
            candidate, [verification_artifact], polarity,
            f"{verification.verifier} {verification.verdict}: {verification.detail}",
        ))
        completed.add("issue_kind_verifier")

    claim_assertions = [item for item in assertions if item.assertion_scope == "claim"]
    supports = any(item.polarity == "supports" for item in claim_assertions)
    contradicts = any(item.polarity == "contradicts" for item in claim_assertions)
    requested = sorted({item.collector for item in candidate.evidence_requests})
    if failures and not claim_assertions:
        status = "incomplete"
    elif contradicts:
        status = "contradicted"
    elif supports:
        status = "supported"
    else:
        status = "inconclusive"
    packet_payload = {
        "candidate_id": candidate.candidate_id,
        "artifact_ids": [item.artifact_id for item in artifacts],
        "assertion_ids": [item.assertion_id for item in assertions],
        "requested_collectors": requested, "completed_collectors": sorted(completed),
        "terminal_failures": failures, "status": status,
    }
    digest = sha256_bytes(canonical_json_bytes(packet_payload))
    packet = EvidencePacket(packet_id=f"packet:{digest[:24]}", source_sha256=digest,
                            **packet_payload)
    return artifacts, assertions, packet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--graphs", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--workspace-map", type=Path, nargs="+",
                        help="One or more JSON objects mapping episode_id to reviewed workspace roots")
    parser.add_argument("--population-workspace-map", type=Path, nargs="+",
                        help="episode -> a COMPLETE checkout, for the naming population scan. "
                             "The candidate run's workspaces are partial (measured 59-229 "
                             ".lean files against Mathlib's ~7400), so scanning them yields a "
                             "sample, not a snapshot; without this every naming claim "
                             "abstains, which is correct but recovers nothing.")
    parser.add_argument("--boundaries", type=Path)
    parser.add_argument("--events", type=Path)
    args = parser.parse_args()
    candidates = [CandidateClaim.model_validate_json(x) for x in args.candidates.read_text().splitlines() if x]
    graphs = [ChangeGraph.model_validate_json(x) for x in args.graphs.read_text().splitlines() if x]
    graph_by_episode = {item.episode_id: item for item in graphs}
    workspace_map = {}
    for path in args.workspace_map or []:
        workspace_map.update(json.loads(path.read_text()))
    # Separate from `workspace_map` on purpose: compiles must run in the episode's own
    # reviewed workspace, while the population scan needs a complete corpus. Conflating them
    # would either compile against the wrong tree or measure naming against a sample.
    population_map = {}
    for path in args.population_workspace_map or []:
        population_map.update(json.loads(path.read_text()))

    def _population_workspace(candidate, explicit_map, graphs_by_episode):
        """Explicit override, else the commit cache, else nothing.

        Deliberately never falls back to the run's own workspace: that tree is partial, and a
        naming population measured from it is a sample presented as a repository measurement.
        Abstaining is the correct outcome when no complete snapshot is available.
        """

        override = explicit_map.get(candidate.episode_id)
        if override:
            return Path(override)
        graph = graphs_by_episode.get(candidate.episode_id)
        return snapshot_workspace(getattr(graph, "base_sha", None))
    boundaries = ([ReviewEpisodeBoundary.model_validate_json(x) for x in args.boundaries.read_text().splitlines() if x]
                  if args.boundaries else [])
    event_rows = ([SourceEvent.model_validate_json(x) for x in args.events.read_text().splitlines() if x]
                  if args.events else None)
    boundary_by_episode = {item.episode_id: item for item in boundaries}
    all_artifacts, all_assertions, packets = [], [], []
    baseline_compile_cache = {}
    # Shared across every candidate and episode: keyed by workspace, so one snapshot is
    # parsed once no matter how many naming claims are checked against it.
    population_cache: Dict[str, object] = {}
    for candidate in candidates:
        workspace = Path(workspace_map[candidate.episode_id]) if candidate.episode_id in workspace_map else args.workspace
        a, s, p = collect_candidate(candidate, graph_by_episode[candidate.episode_id], workspace,
                                    boundary_by_episode.get(candidate.episode_id), event_rows,
                                    baseline_compile_cache,
                                    LazyPopulationScan(
                                        _population_workspace(
                                            candidate, population_map, graph_by_episode,
                                        ),
                                        population_cache,
                                    ))
        all_artifacts.extend(a)
        all_assertions.extend(s)
        packets.append(p)
    write_once(args.out_dir / "artifacts.jsonl", jsonl_bytes(all_artifacts))
    write_once(args.out_dir / "assertions.jsonl", jsonl_bytes(all_assertions))
    write_once(args.out_dir / "packets.jsonl", jsonl_bytes(packets))
    print(json.dumps({"candidates": len(candidates), "supported": sum(p.status == "supported" for p in packets),
                      "terminal_packets": len(packets)}, indent=2))


if __name__ == "__main__":
    main()
