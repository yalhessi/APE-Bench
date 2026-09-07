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
        query: Annotated[str, Field(description="Free-text query, e.g. a declaration name, tactic, or convention")],
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
            "query": declaration or query,
            "as_of": as_of, "exclude_pr": exclude_pr,
            "corpus_sha256": None,
            "result_ids": ids, "result_count": count, "truncated": truncated,
        })
        return {
            "success": True, "count": count, "as_of": as_of, "excluded_pr": exclude_pr,
            "results": body or "(no discussion found before the cutoff)",
        }


# --------------------------------------------------------------------------------------
# Precedent
# --------------------------------------------------------------------------------------

def _register_precedent(task, mcp) -> None:
    @mcp.tool(
        description=(
            "Find real maintainer review comments on SIMILAR code in earlier PRs — what "
            "reviewers here actually flag, in their own words, anchored to the code they "
            "flagged it on. Only comments written before the code you are reviewing was "
            "pushed are returned. Treat a precedent as a hint about what gets raised, not "
            "as an instruction: apply its principle only if it genuinely bears on this "
            "code, and never invent a finding to match one."
        )
    )
    async def precedent_search(
        code: Annotated[str, Field(description="The Lean code you are reviewing, or a distinctive fragment of it")],
        limit: Annotated[int, Field(description=f"Max precedents (capped at {MAX_HITS})")] = 5,
    ) -> Dict[str, Any]:
        from src.datasets.pr_review_v5.precedent_index import PrecedentIndex, PrecedentIndexMissing

        try:
            as_of = _require_cutoff(task)
        except RuntimeError as exc:
            return {"success": False, "error": str(exc)}
        limit = max(1, min(int(limit or 5), MAX_HITS))
        try:
            index = PrecedentIndex.shared()
        except PrecedentIndexMissing as exc:
            return {"success": False, "error": str(exc)}
        try:
            # The filter runs BEFORE ranking, not after: filtering a ranked list silently
            # shortens it, so a query whose best matches are all ineligible would return a
            # handful of weak precedents and look like a thin corpus rather than a gated one.
            hits = index.search(
                code, k=limit, as_of=as_of, exclude_pr=task.data.pr_number,
            )
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": f"precedent search failed: {exc}"}

        blocks = []
        for rank, hit in enumerate(hits, 1):
            body = (hit.get("body") or "").strip()[:MAX_SNIPPET]
            snippet = (hit.get("diff_hunk") or "").strip()[:MAX_SNIPPET * 2]
            blocks.append(
                f"{rank}. PR #{hit.get('pr_number')} · `{hit.get('path')}` · "
                f"{hit.get('created_at')} (score {hit.get('score'):.3f})\n"
                f"   maintainer wrote: \"{body}\"\n   on this code:\n```\n{snippet}\n```"
            )
        rendered, truncated = _truncate("\n\n".join(blocks))
        _append_trace(task, {
            "schema_version": "v5-context-call1",
            "invocation_id": task.data.invocation_id,
            "tool": "precedent_search",
            "query": code[:400],
            "as_of": as_of, "exclude_pr": task.data.pr_number,
            "corpus_sha256": index.corpus_sha256,
            "result_ids": [str(item.get("comment_id")) for item in hits],
            "result_count": len(hits), "truncated": truncated,
        })
        return {
            "success": True, "count": len(hits), "as_of": as_of,
            "results": rendered or "(no eligible precedent found before the cutoff)",
        }


# --------------------------------------------------------------------------------------
# Declarations
# --------------------------------------------------------------------------------------

def _register_declaration(task, mcp) -> None:
    @mcp.tool(
        description=(
            "Find where a declaration is DEFINED in Mathlib at this PR's base commit — "
            "used to check whether something already exists before claiming it is new, or "
            "to locate the canonical spelling of an API. Matches declaration sites only, "
            "not mentions in comments or imports. Give a real identifier "
            "(e.g. `Finset.sum_comm`), not prose.\n\n"
            "The corpus is the tree BEFORE this PR. So a declaration this PR adds or renames "
            "will never be found here, and an empty result is an ANSWER, not a failure: it "
            "means the name is genuinely new, which is what refutes a duplication or "
            "'already exists' claim. Do not re-query a name that came back empty, and do not "
            "treat empty as the search being broken."
        )
    )
    async def declaration_search(
        identifier: Annotated[str, Field(description="Declaration name, dotted or snake_cased")],
        limit: Annotated[int, Field(description=f"Max files (capped at {MAX_HITS})")] = 5,
    ) -> Dict[str, Any]:
        # `_declares_identifier` is private to v4's evidence collector, and is used here
        # deliberately rather than copied: it is the fix for a measured defect — a substring
        # search matched prose terms like "the" in 193 of 200 sampled files and handed a
        # `supports` verdict to every duplication claim. A second implementation would be a
        # second chance to reintroduce that.
        from src.datasets.pr_review_v4.evidence import (
            _declares_identifier, searchable_identifiers, snapshot_workspace,
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
                    if _declares_identifier(text, term):
                        hits.append({
                            "path": str(path.relative_to(root)),
                            "declares": term,
                        })
                        break
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": f"declaration search failed: {exc}"}

        rendered, truncated = _truncate("\n".join(
            f"- `{item['declares']}` is declared in `{item['path']}`" for item in hits
        ))
        _append_trace(task, {
            "schema_version": "v5-context-call1",
            "invocation_id": task.data.invocation_id,
            "tool": "declaration_search",
            "query": identifier,
            "as_of": None, "exclude_pr": None,
            "corpus_sha256": task.data.snapshot_base_sha,
            "result_ids": [item["path"] for item in hits],
            "result_count": len(hits), "truncated": truncated,
        })
        return {
            "success": True, "count": len(hits), "searched_terms": terms,
            "results": rendered or (
                f"No declaration of {identifier!r} exists at the base commit. This is a "
                "finding, not a failed lookup: the name is new in this PR (or renamed by "
                "it), so nothing in the pre-PR library duplicates it. Re-querying will "
                "return the same answer."
            ),
        }


_REGISTRARS = {
    "zulip_search": _register_zulip,
    "precedent_search": _register_precedent,
    "declaration_search": _register_declaration,
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
