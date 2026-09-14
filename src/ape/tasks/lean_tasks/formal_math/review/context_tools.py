"""Live context an arm can pull for its own site, and the gates that keep it honest.

Three capabilities are added here; `lean_verify_edit` is the fourth and is inherited from
the shared review base, unchanged.

Everything in this module is subject to one rule: **a read that could see the future is not
allowed to happen at all.** Not "is filtered afterwards", not "is usually fine" — the gate
is applied inside the single helper every read path goes through, and a missing cutoff
raises instead of falling back to an ungated read. An ungated read is a silent leak, and a
silent leak invalidates the run that contains it without ever failing.

Time is only half of it. `exclude_pr` is the half time cannot do: a Zulip thread *about*
this PR can predate the reviewed commit and still hand over the answer. Both corpora already
encode this — `zulip.store.gate` takes both arguments, and
`pr_review_v4.retrieval.validate_precedents` raises on a future event rather than dropping
it — so the work here is to route through them rather than around them.

Dataset-layer readers are imported lazily inside each tool. `ape` is an installed top-level
package and `src.datasets` only resolves with the repo root on `sys.path`; the established
convention for a task that needs dataset code is a function-local import, as in
`pr_review_v4/candidates.py` and `file_scoped.py`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional

from pydantic import Field

#: Hard bounds on what one retrieval may return. A context tool that can flood the
#: conversation spends the arm's budget on reading instead of on checking, and an arm that
#: runs out of turns mid-investigation returns nothing at all.
MAX_HITS = 8
MAX_RESULT_CHARS = 6000
MAX_SNIPPET = 400


def _append_trace(task, row: Dict[str, Any]) -> None:
    """Append one `ContextCall` to the attempt's trace, best-effort.

    Append-only and written as the call happens, rather than returned with the result,
    because a job that fails or exhausts its budget returns nothing — and those are exactly
    the jobs whose retrieval behaviour explains the outcome. Tracing must never be able to
    fail a tool call, so every error here is swallowed after logging.
    """

    path = getattr(task.data, "trace_path", None)
    if not path:
        return
    try:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        with target.open("a", encoding="utf-8") as handle:
            handle.write(line)
    except Exception as exc:  # noqa: BLE001
        if getattr(task, "logger", None) is not None:
            task.logger.warning("context trace append failed (%s): %s", path, exc)


def _truncate(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_RESULT_CHARS:
        return text, False
    return text[:MAX_RESULT_CHARS] + "\n… (truncated)", True


def _require_cutoff(task) -> str:
    """The gate instant, or a hard failure. Never a default."""

    as_of = getattr(task.data, "retrieval_cutoff", None)
    if not as_of:
        raise RuntimeError(
            "no retrieval cutoff is set for this invocation, so a gated context read "
            "cannot be performed. This is a configuration error, not a transient one: "
            "running the read ungated would let the arm see discussion written after the "
            "code it is reviewing."
        )
    return as_of


# --------------------------------------------------------------------------------------
# Zulip
# --------------------------------------------------------------------------------------

def _register_zulip(task, mcp) -> None:
    @mcp.tool(
        description=(
            "Search Mathlib Zulip discussion for context on this change — whether a "
            "convention is settled or still being argued, whether a lemma name or API "
            "shape has been discussed, what maintainers have said about this area. "
            "Results are restricted to discussion that existed BEFORE the code you are "
            "reviewing was pushed, and threads about this PR are excluded, so anything "
            "returned is genuinely prior context rather than the answer. Use it when a "
            "claim depends on what the community's convention IS, not on what the code does."
        )
    )
    async def zulip_search(
        query: Annotated[str, Field(description=(
            "Free-text query, e.g. a declaration name, tactic, or convention. Terms are "
            "OR-ed and ranked by relevance, so extra words widen the search rather than "
            "narrowing it; punctuation is ignored. Not FTS5 syntax."))],
        declaration: Annotated[Optional[str], Field(
            description="Optional: find threads referencing this exact declaration name")] = None,
        maintainers_only: Annotated[bool, Field(
            description="Restrict to messages from roster maintainers")] = False,
        limit: Annotated[int, Field(description=f"Max hits (capped at {MAX_HITS})")] = MAX_HITS,
    ) -> Dict[str, Any]:
        from src.datasets.zulip.config import ZulipConfig
        from src.datasets.zulip.render import render_hits, render_thread
        from src.datasets.zulip.store import ZulipStore

        try:
            as_of = _require_cutoff(task)
        except RuntimeError as exc:
            return {"success": False, "error": str(exc)}
        exclude_pr = task.data.pr_number
        store_path = Path(ZulipConfig().sqlite_path)
        if not store_path.is_file():
            return {"success": False, "error": (
                f"the Zulip store is not built at {store_path}. Build it with "
                "`python -m src.datasets.zulip.sync` then `python -m src.datasets.zulip.build "
                "--config configs/zulip_corpus.yaml`.")}

        limit = max(1, min(int(limit or MAX_HITS), MAX_HITS))
        try:
            with ZulipStore(store_path) as store:
                # Both gate arguments on every call, always. There is no code path in this
                # tool that reaches the store without them.
                if declaration:
                    views = store.threads_mentioning(
                        declaration, as_of=as_of, exclude_pr=exclude_pr)[:limit]
                    rendered = "\n\n".join(
                        render_thread(view.thread, view.messages,
                                      truncated=view.truncated, max_messages=12)
                        for view in views
                    )
                    ids = [view.thread.thread_key for view in views]
                    count = len(views)
                else:
                    hits = store.search(
                        query, as_of=as_of, exclude_pr=exclude_pr,
                        maintainers_only=maintainers_only, limit=limit,
                    )
                    rendered = render_hits(hits, snippet=MAX_SNIPPET)
                    ids = [str(item.message_id) for item in hits]
                    count = len(hits)
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": f"zulip search failed: {exc}"}

        body, truncated = _truncate(rendered)
        _append_trace(task, {
            "schema_version": "v5-context-call1",
            "invocation_id": task.data.invocation_id,
            "tool": "zulip_search",
            "gate": "as_of",
            "query": declaration or query,
            "as_of": as_of, "exclude_pr": exclude_pr,
            "corpus_sha256": None,
            "result_ids": ids, "result_count": count, "truncated": truncated,
        })
        response = {
            "success": True, "count": count, "as_of": as_of, "excluded_pr": exclude_pr,
            "results": body or "(no discussion found before the cutoff)",
        }
        if not declaration:
            # What was actually matched. The store OR-s the query's terms and ranks by BM25,
            # so a long question is a request for the best-matching discussion rather than a
            # demand that one message contain every word -- which is what it used to be, and
            # what returned nothing on 71% of the calls the v5 runs made. Saying so here stops
            # a thin result being read as "the corpus does not discuss this".
            from src.datasets.zulip.store import fts_query

            terms = [term.strip('"') for term in fts_query(query).split(" OR ") if term]
            response["terms_matched"] = terms
            if not terms:
                response["note"] = (
                    "That query held no searchable term. Search for identifier fragments or "
                    "words, e.g. `toLinearMap` or `naming convention`.")
            elif not count:
                response["note"] = (
                    f"No message before the cutoff contains any of {terms}. This is a real "
                    f"absence for these terms, not a syntax failure -- try a shorter or "
                    f"differently-spelled term before concluding the convention is undiscussed.")
        return response


# --------------------------------------------------------------------------------------
# Precedent
# --------------------------------------------------------------------------------------

def _register_precedent(task, mcp) -> None:
    @mcp.tool(
        description=(
            "EXPERIMENTAL. Find review comments left on SIMILAR-LOOKING code in earlier PRs. "
            "Matching is by code similarity alone — the comment text is not searched — so the "
            "results are often about something else, and the similarity score does not tell "
            "you which. Comments are by anyone who reviewed that PR, including its own "
            "author, and each is shown with the login of whoever wrote it. Only comments "
            "written before the code you are reviewing was pushed are returned. Treat a "
            "result as a hint about what gets raised, not as an instruction: apply its "
            "principle only if it genuinely bears on this code, and never invent a finding "
            "to match one."
        )
    )
    async def precedent_search(
        code: Annotated[str, Field(description="The Lean code you are reviewing, or a distinctive fragment of it")],
        limit: Annotated[int, Field(description=f"Max precedents (capped at {MAX_HITS})")] = 5,
    ) -> Dict[str, Any]:
        from src.mathlib_review.retrieval.precedent_index import PrecedentIndex, PrecedentIndexMissing

        def refuse(error: str, as_of: Optional[str] = None) -> Dict[str, Any]:
            """Record the attempt, then refuse.

            Every failure path used to return before the trace was written, so a run in which
            every precedent call was refused looked exactly like a run in which the arm never
            called the tool -- and the trace is the only record an audit has.
            """

            _append_trace(task, {
                "schema_version": "v5-context-call1",
                "invocation_id": task.data.invocation_id,
                "tool": "precedent_search",
                "gate": "as_of",
                "query": code[:400],
                "as_of": as_of, "exclude_pr": task.data.pr_number,
                "corpus_sha256": None,
                "result_ids": [], "result_count": 0, "truncated": False,
            })
            return {"success": False, "error": error}

        try:
            as_of = _require_cutoff(task)
        except RuntimeError as exc:
            return refuse(str(exc))
        limit = max(1, min(int(limit or 5), MAX_HITS))
        try:
            index = PrecedentIndex.shared()
        except PrecedentIndexMissing as exc:
            return refuse(str(exc), as_of)
        try:
            # The filter runs BEFORE ranking, not after: filtering a ranked list silently
            # shortens it, so a query whose best matches are all ineligible would return a
            # handful of weak precedents and look like a thin corpus rather than a gated one.
            hits = index.search(
                code, k=limit, as_of=as_of, exclude_pr=task.data.pr_number,
            )
        except Exception as exc:  # noqa: BLE001
            return refuse(f"precedent search failed: {exc}", as_of)

        blocks = []
        for rank, hit in enumerate(hits, 1):
            body = (hit.get("body") or "").strip()[:MAX_SNIPPET]
            # The TAIL of the hunk, not the head. GitHub builds a review comment's hunk so
            # that it ENDS at the line being commented on, so taking the first N characters
            # drops exactly the line the comment is about. Measured over every precedent
            # delivered to an arm in the v5 runs: 711 of 2,825 hits (25%) had a hunk longer
            # than this budget, and every one of them was shown code the comment was not
            # about, under the words of a comment about something else.
            whole = (hit.get("diff_hunk") or "").strip()
            snippet = whole[-(MAX_SNIPPET * 2):]
            if len(snippet) < len(whole):
                snippet = "…(earlier lines of this hunk omitted)\n" + snippet
            # The commenter's own login, not "maintainer". The corpus keeps comments by
            # GitHub `author_association`, which a PR's own author carries on their own PR,
            # so 46% of delivered hits were the PR author replying to a reviewer ("Done.",
            # "My bad, thanks.") presented to the arm as a maintainer's judgement.
            who = hit.get("commenter") or "someone"
            blocks.append(
                f"{rank}. PR #{hit.get('pr_number')} · `{hit.get('path')}` · "
                f"{hit.get('created_at')} (similarity {hit.get('score'):.3f})\n"
                f"   {who} wrote: \"{body}\"\n   on this code:\n```\n{snippet}\n```"
            )
        rendered, truncated = _truncate("\n\n".join(blocks))
        _append_trace(task, {
            "schema_version": "v5-context-call1",
            "invocation_id": task.data.invocation_id,
            "tool": "precedent_search",
            "gate": "as_of",
            "query": code[:400],
            "as_of": as_of, "exclude_pr": task.data.pr_number,
            "corpus_sha256": index.corpus_sha256,
            "result_ids": [str(item.get("comment_id")) for item in hits],
            "result_count": len(hits), "truncated": truncated,
        })
        return {
            "success": True, "count": len(hits), "as_of": as_of,
            "results": rendered or "(no eligible precedent found before the cutoff)",
            # Said plainly because the scores do not say it. Measured across representative
            # queries, the top-5 similarities sit in 0.59-0.63 whether the hits are about the
            # queried code or not, so there is no cutoff that separates a real precedent from
            # the nearest thing in the corpus, and inventing one would only hide the problem.
            "note": (
                "These are the nearest comments by CODE similarity, not a judgement that any "
                "of them bears on your code. The similarity score is not calibrated: a "
                "top-ranked hit may be unrelated. Read each one and discard the ones that do "
                "not apply; finding nothing applicable here is a normal outcome."
            ),
        }


# --------------------------------------------------------------------------------------
# Declarations
# --------------------------------------------------------------------------------------

def _reviewed_overlay_root(task):
    """The attempt's `target/`: base + δ₀, with the PR's changed files materialised as real
    files. `None` when the task has no target workspace, in which case only the base corpus
    is searched and the tool says so."""

    workspace = getattr(task, "target_workspace", None)
    path = getattr(workspace, "path", None)
    return Path(path) if path else None


def _register_declaration(task, mcp) -> None:
    @mcp.tool(
        description=(
            "Find where a declaration is DEFINED in Mathlib at this PR's base commit — "
            "used to check whether something already exists before claiming it is new, or "
            "to locate the canonical spelling of an API. Matches declaration sites only, "
            "not mentions in comments or imports. Give a real identifier "
            "(e.g. `Finset.sum_comm`), not prose.\n\n"
            "Two corpora, reported separately: the tree BEFORE this PR (the base commit), and "
            "the files this PR changes, as this PR leaves them. A name found only in the "
            "second is one this PR introduces or renames -- which is what refutes a "
            "duplication or 'already exists' claim, and what lets a rename be looked up "
            "under its new name. An empty result in the base corpus is an ANSWER, not a "
            "failure. Do not re-query a name that came back empty in both."
        )
    )
    async def declaration_search(
        identifier: Annotated[str, Field(description="Declaration name, dotted or snake_cased")],
        limit: Annotated[int, Field(description=f"Max files (capped at {MAX_HITS})")] = 5,
    ) -> Dict[str, Any]:
        # `declares_identifier` lives with v4's evidence collector and is used here
        # deliberately rather than copied: it is the fix for a measured defect — a substring
        # search matched prose terms like "the" in 193 of 200 sampled files and handed a
        # `supports` verdict to every duplication claim. A second implementation would be a
        # second chance to reintroduce that. It was `_declares_identifier` until two packages
        # importing it made the underscore a claim that was not true.
        from src.mathlib_review.evidence.evidence import (
            declares_identifier, searchable_identifiers, snapshot_workspace,
        )

        terms = searchable_identifiers(identifier)
        if not terms:
            return {"success": False, "error": (
                f"{identifier!r} is not identifier-shaped. Give a declaration name such as "
                "`Finset.sum_comm` or `isOpen_iUnion`, not a description.")}

        limit = max(1, min(int(limit or 5), MAX_HITS))
        root = snapshot_workspace(task.data.snapshot_base_sha)
        if root is None:
            return {"success": False, "error": (
                f"no complete base snapshot is available for {task.data.snapshot_base_sha}; "
                "searching the partial attempt overlay would report absence that only means "
                "the file was never materialized.")}

        hits: List[Dict[str, Any]] = []
        try:
            for path in sorted(Path(root).rglob("*.lean")):
                if len(hits) >= limit:
                    break
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                for term in terms:
                    if declares_identifier(text, term):
                        hits.append({
                            "path": str(path.relative_to(root)),
                            "declares": term,
                        })
                        break
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": f"declaration search failed: {exc}"}

        # The reviewed state of the files this PR changes. Base-only search blinds a rename
        # review to the very name under review: on 33337 the naming arm looked up the PR's new
        # name, got "no declaration exists at the base commit", and had nothing to reason
        # about. Only the changed files are searched -- they are the only files whose reviewed
        # text differs from the base, and the only ones the overlay materialises as real
        # files -- so this is a few reads, not a second tree walk. Kept apart from the base
        # hits: "exists before this PR" and "exists because of this PR" answer opposite
        # questions, and folding them would turn a rename into a duplicate.
        introduced: List[Dict[str, Any]] = []
        overlay = _reviewed_overlay_root(task)
        if overlay is not None:
            for rel in getattr(task.data, "changed_files", None) or []:
                if len(introduced) >= limit:
                    break
                path = Path(overlay) / rel
                if path.is_symlink() or not path.is_file():
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                for term in terms:
                    if declares_identifier(text, term):
                        introduced.append({"path": rel, "declares": term})
                        break

        lines = [f"- `{item['declares']}` is declared in `{item['path']}` (before this PR)"
                 for item in hits]
        lines += [f"- `{item['declares']}` is declared in `{item['path']}` (IN THIS PR, as "
                  "it leaves the file)" for item in introduced]
        rendered, truncated = _truncate("\n".join(lines))
        _append_trace(task, {
            "schema_version": "v5-context-call1",
            "invocation_id": task.data.invocation_id,
            "tool": "declaration_search",
            "gate": "base_snapshot",
            # `gate` is a closed vocabulary the leak audit enumerates, and the temporal bound
            # here is still the base snapshot: the second corpus is the PR's own changed files,
            # which can see nothing later than the PR itself. Overlay hits are distinguishable
            # in `result_ids` by their `reviewed:` prefix.
            "query": identifier,
            "as_of": None, "exclude_pr": None,
            "corpus_sha256": task.data.snapshot_base_sha,
            "result_ids": [item["path"] for item in hits] + [
                f"reviewed:{item['path']}" for item in introduced],
            "result_count": len(hits) + len(introduced), "truncated": truncated,
        })
        empty = (
            f"No declaration of {identifier!r} exists at the base commit"
            + (" or in the files this PR changes." if overlay is not None else ".")
            + " This is a finding, not a failed lookup. Re-querying will return the same answer."
        )
        return {
            "success": True, "count": len(hits) + len(introduced),
            "declared_before_this_pr": len(hits), "declared_in_this_pr": len(introduced),
            "searched_terms": terms,
            "results": rendered or empty,
        }


def _register_proof_profile(task, mcp) -> None:
    @mcp.tool(
        description=(
            "Ask the repository what actually closes proofs LIKE THIS ONE, at this PR's base "
            "commit. Returns the tactics that close proofs in the same reference class, "
            "RANKED, each with how common it is and whether its use is rising or flat.\n\n"
            "Use this BEFORE deciding what to propose, not to confirm a tactic you have "
            "already chosen. It answers 'what would a maintainer reach for here', which is a "
            "question you cannot ask by searching for a tactic you have not thought of.\n\n"
            "READ THE RANK AND THE TREND, NOT ONLY THE SHARE. A tactic the library is adopting "
            "is rare in absolute terms and still the thing a maintainer will ask for — a "
            "convention is where the code is going, and a share is where it has been. A tactic "
            "ranked second at 3% whose use went from nothing to that in a year is a stronger "
            "signal than the 25% tactic that has been flat for three.\n\n"
            "The corpus is the tree BEFORE this PR, so nothing this PR adds appears in it."
        )
    )
    async def proof_profile(
        conclusion_head: Annotated[Optional[str], Field(description=(
            "Restrict to proofs whose goal concludes in this relation: subset, ssubset, le, "
            "ge, eq, iff, mem, quantified, other. Omit for no restriction."))] = None,
        directory: Annotated[Optional[str], Field(description=(
            "Restrict to a Mathlib subtree, e.g. `Topology/MetricSpace`. Omit for the whole "
            "library. Narrow is not better: a subtree can be behind the library."))] = None,
        limit: Annotated[int, Field(description="Max tactics to return")] = 8,
        examples: Annotated[int, Field(description=(
            "Real proofs to show per tactic, sampled across the length range. A count says how "
            "often a tactic is used; an example shows what it is FOR, which is the part that "
            "transfers to your goal. 0 to omit."))] = 2,
    ) -> Dict[str, Any]:
        from src.mathlib_review.retrieval.declaration_table import (
            PROOF_PROFILE_VERSION, curve_dates, distribution, exemplars, load_table,
            trajectory,
        )
        from src.mathlib_review.evidence.evidence import snapshot_workspace

        sha = task.data.snapshot_base_sha
        try:
            table = load_table(sha)
        except (FileNotFoundError, ValueError) as exc:
            # Absence is reported, never papered over: a profile computed from a partial
            # checkout would be a 2% sample that still clears any support threshold.
            return {"success": False, "error": str(exc)}

        rows = table.select(conclusion_head_=conclusion_head, directory=directory)
        if not rows:
            return {"success": True, "population": 0, "results": (
                "No proofs in the base commit match that reference class. Widen it — drop the "
                "directory, or drop the conclusion restriction — rather than reading this as "
                "'there is no convention here'.")}

        payload = distribution(rows)
        top = payload["tactics"][:max(1, min(int(limit or 8), 20))]

        # The trend is what makes the level readable, so it is computed for what is returned
        # rather than offered as a second call the arm has to think to make.
        # Anchored to the base commit's own date rather than to literals, so the right-hand
        # end of every curve is the state this PR was opened against.
        dates = curve_dates(sha)
        # Exemplars are read from the same snapshot the table was built from. `None` when the
        # snapshot is gone: the numbers still stand, the examples are simply omitted.
        workspace = snapshot_workspace(sha)
        lines = []
        ranked = 1
        for item in top:
            try:
                curve = trajectory(item["tactic"], sha, dates, subdir="Mathlib") if dates else []
            except (FileNotFoundError, OSError):
                curve = []
            # The trend is read from the curve ALONE. `item["share"]` is a share of proofs in
            # this reference class; the curve is a share of files across the library. Comparing
            # them would divide two different denominators -- the first version of this did,
            # and reported `simpa` as "declining" because 5.9% of subset proofs is less than
            # half the fraction of files that mention it anywhere.
            trend = ""
            if len(curve) >= 2:
                early = curve[0]["share"] or 0.0
                late = curve[-1]["share"] or 0.0
                if late > 0.005 and early < 0.005:
                    # Categorically different from a tactic that merely grew: this one did not
                    # meaningfully exist a year ago, which is the strongest available signal
                    # that it is a convention arriving rather than one the author has already
                    # applied.
                    trend = ("  NEW — essentially absent a year ago (%.2f%% of files), "
                             "now %.2f%%" % (100 * early, 100 * late))
                elif late > 0.005 and late > max(2 * early, early + 0.01):
                    trend = "  rising (%.2f%% -> %.2f%% of files)" % (
                        100 * early, 100 * late)
                elif early > 0.005 and late < early / 2:
                    trend = "  declining (%.2f%% -> %.2f%% of files)" % (
                        100 * early, 100 * late)
                else:
                    trend = "  flat"
            lines.append("%2d. `%s` — %.1f%% of %d proofs%s"
                         % (ranked, item["tactic"], 100 * (item["share"] or 0.0),
                            payload["population"], trend))
            ranked += 1
            if examples and workspace is not None:
                for case in exemplars(rows, item["tactic"], workspace,
                                      limit=max(0, min(int(examples), 3))):
                    body = " ".join(case["proof"].split())
                    lines.append("      e.g. `%s` := %s" % (case["fullname"], body))

        return {
            "success": True,
            "reference_class": {"conclusion_head": conclusion_head, "directory": directory,
                                "population": payload["population"]},
            "corpus_sha256": sha,
            "proof_profile_version": PROOF_PROFILE_VERSION,
            "conclusion_classifier_version": payload["conclusion_classifier_version"],
            "tactic_vocabulary_version": payload["tactic_vocabulary_version"],
            "results": "\n".join(lines),
        }


def _register_naming_norm(task, mcp) -> None:
    @mcp.tool(
        description=(
            "What this repository CALLS lemmas like this one, counted over the whole base "
            "snapshot. Give a declaration this PR adds or renames.\n\n"
            "Returns the declaration's conclusion subject (what the statement is *about*), "
            "every leaf prefix the corpus uses for that subject with its count, and -- only "
            "when the corpus has an opinion worth holding a PR to -- candidate names.\n\n"
            "This is a census, not a sample: `content_search` caps at a handful of files and "
            "says so, and a prefix count read off a capped grep is the kind of number this "
            "tool exists to replace. Counts come from the BASE commit, so the PR's own new "
            "names are not counted into the norm they are being judged against.\n\n"
            "`verdict` is the answer, not the counts: `established` means the corpus is "
            "lopsided enough to hold a PR to (a blocking ask); `emerging` means one spelling "
            "leads clearly but is not dominant (advisory at most); `insufficient_evidence` "
            "means the corpus has no opinion here and you should submit nothing on naming."
        )
    )
    async def naming_norm(
        declaration: Annotated[str, Field(
            description="Declaration this PR adds or renames, e.g. `Submodule.coe_starProjection_eq_x`")],
    ) -> Dict[str, Any]:
        from ape.toolkits.code.lean.lean_parser import parse_major_declarations
        from src.mathlib_review.evidence.evidence import snapshot_workspace
        from src.mathlib_review.evidence.operators.naming_contrast import declaration_conclusion
        from src.mathlib_review.evidence.operators.naming_norm import (
            MAX_CONFLICT_RATIO, MIN_SUPPORT, MIN_SUPPORT_RATIO, conclusion_subject, leaf_prefix,
            norm_for, norm_index, rename_candidates,
        )

        base = task.data.snapshot_base_sha
        root = snapshot_workspace(base)
        if root is None:
            return {"success": False, "error": (
                f"no complete base snapshot for {base}; a norm read from the attempt overlay "
                "would be a 2% sample reported as a repository measurement.")}
        index = norm_index(Path(root), base)
        if index is None:
            return {"success": False, "error": f"no naming norms are available for {base}."}

        # The declaration's own conclusion, from the reviewed text -- the arm is asking about a
        # name this PR introduces, which by construction is not in the base tree.
        signature = ""
        overlay = _reviewed_overlay_root(task)
        wanted = declaration.rsplit(".", 1)[-1]
        for rel in getattr(task.data, "changed_files", None) or []:
            if not str(rel).endswith(".lean") or overlay is None:
                continue
            source = overlay / str(rel)
            if not source.is_file():
                continue
            try:
                parsed = parse_major_declarations(source.read_text(encoding="utf-8", errors="ignore"))
            except Exception:  # noqa: BLE001
                continue
            for item in parsed:
                name = item.fullname or item.name or ""
                if name == declaration or name.rsplit(".", 1)[-1] == wanted:
                    signature = item.signature or ""
                    break
            if signature:
                break
        if not signature:
            return {"success": False, "error": (
                f"{declaration!r} is not among the declarations this PR changes; this tool "
                "answers for a name the PR adds or renames.")}

        subject = conclusion_subject(declaration_conclusion(signature))
        population = norm_for(index, subject.token)
        if subject.token is None or subject.confidence != "high" or population is None:
            _append_trace(task, {
                "schema_version": "v5-context-call1",
                "invocation_id": task.data.invocation_id,
                "tool": "naming_norm",
                "gate": "base_snapshot",
                "query": declaration,
                "as_of": None, "exclude_pr": None, "corpus_sha256": base,
                "result_ids": [], "result_count": 0, "truncated": False,
            })
            return {"success": True, "verdict": "insufficient_evidence", "subject": subject.token,
                    "results": (
                        "The corpus has no counted opinion about this declaration's subject, so "
                        "there is no convention here to hold the PR to. Submit nothing on naming "
                        "unless a maintainer precedent says otherwise.")}

        current = leaf_prefix(declaration.rsplit(".", 1)[-1])
        ranked = population.prefix_counts.most_common()
        dominant, support = ranked[0]
        runner_up = ranked[1][1] if len(ranked) > 1 else 0
        established = population.is_strong() and population.conflict_ratio(current) <= MAX_CONFLICT_RATIO
        emerging = (support >= MIN_SUPPORT and support >= 3 * max(runner_up, 1)
                    and population.prefix_counts.get(current, 0) < support)
        verdict = ("established" if established and dominant != current
                   else "emerging" if emerging and dominant != current
                   else "insufficient_evidence")
        candidates = (rename_candidates(declaration, dominant, subject.expression,
                                        index.get("notation"))
                      if verdict != "insufficient_evidence" else [])
        counted = ", ".join(f"`{prefix}_` {count}" for prefix, count in ranked[:6])
        lines = [
            f"Subject of the conclusion: `{subject.token}` (from {subject.kind}).",
            f"Of {population.members} declarations in the base snapshot with that subject: {counted}.",
            f"This declaration uses `{current}_` ({population.prefix_counts.get(current, 0)}).",
            f"Verdict: **{verdict}**.",
        ]
        if verdict == "established":
            lines.append(f"`{dominant}_` is the convention here ({support}/{population.members}, "
                         f"over the {MIN_SUPPORT_RATIO:.0%} bar). A rename is a fair ask.")
        elif verdict == "emerging":
            lines.append(f"`{dominant}_` leads {support} to {runner_up} but is not dominant. "
                         "Advisory at most -- say it is the emerging spelling, not the rule.")
        else:
            lines.append("The corpus does not back a rename here. Submit nothing on naming.")
        if candidates:
            lines.append("Candidate names: " + ", ".join(f"`{name}`" for name in candidates))
        rendered, truncated = _truncate("\n".join(lines))
        _append_trace(task, {
            "schema_version": "v5-context-call1",
            "invocation_id": task.data.invocation_id,
            "tool": "naming_norm",
            "gate": "base_snapshot",
            "query": declaration,
            "as_of": None, "exclude_pr": None, "corpus_sha256": base,
            "result_ids": [f"{subject.token}:{dominant}:{support}/{population.members}"],
            "result_count": population.members, "truncated": truncated,
        })
        return {"success": True, "verdict": verdict, "subject": subject.token,
                "members": population.members, "counts": dict(ranked[:8]),
                "candidates": candidates, "results": rendered}


_REGISTRARS = {
    "zulip_search": _register_zulip,
    "precedent_search": _register_precedent,
    "declaration_search": _register_declaration,
    "naming_norm": _register_naming_norm,
    "proof_profile": _register_proof_profile,
}


def register_context_tools(task, mcp) -> None:
    """Register exactly the context tools this arm was granted.

    `lean_verify_edit` is absent from the table on purpose: it is registered by the shared
    review base for every review task, and registering it twice would shadow it.
    """

    granted = list(getattr(task.data, "context_tools", None) or [])
    for name in granted:
        registrar = _REGISTRARS.get(name)
        if registrar is not None:
            registrar(task, mcp)
    return [name for name in granted if name in _REGISTRARS]
