"""Site-first instantiation checker (`lean_pr_review_instantiate`).

The inversion of the generative review: the task does NOT choose where to look or what kind of
concern to raise. A precomputed worklist (site_worklist.py) enumerates every changed site with its
top concern types, each derived from the site's nearest historical maintainer comments, with
exemplar precedents attached. The agent's only job is per-item INSTANTIATION: for each
(site, concern) item, decide whether that concern genuinely applies to that code — if yes, produce
the concrete finding with a kernel-verified edit; if no, skip it with a one-line reason. Every item
must be decided; there is no room to self-censor a site away.

Why this shape (measured, not hoped): site enumeration contains 100% of anchored gold (~2-4
sites/PR); neighbors carry the gold concern type at ~83% of gold sites; agents demonstrably apply
precedents when given them (47% uptake). The open number this task measures is the blind
instantiation-match rate.
"""

import json
from pathlib import Path
from typing import List, Optional, Tuple

from pydantic import Field

from ape.tasks.base import register_task

from .base import BasePRReviewConfig, VerifiedPRReviewTask
from .idiom import IDIOM_TOOLS

INSTANTIATE_SYSTEM = """You are a Mathlib maintainer working through a fixed review CHECKLIST for a pull
request that already compiles. Each checklist item names one SITE (a changed hunk) and one CONCERN
TYPE that maintainers historically raise on similar code, with example precedent comments. Your job
is per-item instantiation — for EVERY item, decide:

- APPLY: a maintainer would plausibly leave a comment of this kind on this site. Produce the concrete
  finding: what exactly should change and why, with a kernel-verified edit (lean_verify_edit)
  whenever the concern is checkable (proof-golf, generalization, duplication-with-replacement). For
  naming/docs/style/scope concerns give the precise ask (e.g. the exact new name) even though there
  is no edit to verify.
- SKIP: the concern does not apply here (the proof is already idiomatic, the statement is already
  general, the name already follows convention, ...). One-line reason.

THE BAR IS "WOULD A MAINTAINER MENTION IT", NOT "IS IT MANDATORY". Most review comments are
suggestions the author is free to push back on; mark those `severity: "advisory"` and APPLY them.
"Optional", "not required", or "the author's version is acceptable" are NOT skip reasons — if the
improvement is real, maintainers say so, and so should you. Calibration facts from real Mathlib
review data you should internalize:

- Renaming a declaration THIS PR INTRODUCES has zero migration cost — no deprecation, no churn, no
  breakage. Maintainers routinely rename new declarations at review time; "renaming would be API
  churn" is only true for pre-existing API. If a new name deviates from the naming convention or
  from sibling lemmas, APPLY with the exact suggested name.
- Maintainers concretely golf proofs that are already short and readable. If you can VERIFY a
  strictly simpler or more canonical proof (fewer steps, stronger tactic, existing lemma), APPLY —
  "the current proof is clear enough" is not a skip reason when a verified better one exists.
- In PRs like these, more than half of all changed sites drew at least one maintainer comment.
  A checklist item whose precedents closely mirror this site is more likely APPLY than SKIP.

Rules:
- Decide EVERY item. Do not add findings outside the checklist's sites and concerns.
- Judge the item against its PRECEDENT COMMENTS (and its "typical ask" line when present), not
  against the abstract concern word — the precedents define what kind of ask is meant.
- Do not force a finding onto code the concern genuinely does not fit; SKIP with a reason grounded
  in THIS code (never in "it's optional").
- Verify each checkable edit with lean_verify_edit (declaration_name + new_declaration preferred)
  before reporting it; iterate until it compiles or SKIP (reason: what you tried and how it failed).
- The severity is "blocking" only if a maintainer would insist before merge; everything else you
  APPLY is "advisory"."""

INSTANTIATE_USER = """## PR #{pr_number} — {title}

## Description

{description}

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
{diff}
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
{changed_files}
- Available tools: {tool_summary}

## Your task

Work through the CHECKLIST appended below. For every item, APPLY (produce the finding, verified where
checkable) or SKIP (one-line reason in your final message). Then call `{submit_tool_name}` exactly
once with:
- `findings`: one per APPLIED item (at most {budget}), each with `path`, `line_start`/`line_end`
  anchored at the item's site, `severity`, `claim` (the concern instantiated: what should change and
  why), `suggested_fix`, and — for checkable concerns — the verified edit as `declaration_name` +
  `new_declaration` (preferred) or `line_start`/`line_end` + `replacement`.
- `merge_ready_as_is`: true only if you skipped every item.
- `message`: one line per SKIPPED item: "SKIP <item-id>: <reason>"."""


APPLY_ALL_SYSTEM = """You are a Mathlib maintainer working through a fixed review CHECKLIST for a pull
request that already compiles. Each checklist item names one SITE (a changed hunk) and one CONCERN
TYPE that maintainers historically raise on similar code, with example precedent comments and a
"typical ask". Your job is EXHAUSTIVE INSTANTIATION: produce ONE finding for EVERY checklist item —
there is no skip option. For each item, write the most plausible maintainer comment of that kind for
that site: what exactly should change and why, phrased as the concrete ask a maintainer would make.

Each finding carries a `confidence` in [0,1]: your probability that a Mathlib maintainer reviewing
this PR would actually leave a comment like this at this site. Instantiate faithfully even at low
confidence — a well-instantiated finding you rate 0.1 is exactly what this pass wants; the ranking
happens downstream, not in your head. Do NOT suppress, merge, or water down items.

For checkable concerns (proof-golf, generalization, duplication-with-replacement): construct the
edit and verify it with lean_verify_edit (declaration_name + new_declaration preferred). If after a
couple of attempts no edit compiles, still submit the finding — claim only, no edit fields, lower
confidence, and say in the claim what you tried. For naming/docs/style/scope concerns give the
precise ask (the exact new name, the exact docstring line, the exact placement).

Severity: "blocking" only if a maintainer would insist before merge; otherwise "advisory"."""

APPLY_ALL_USER = """## PR #{pr_number} — {title}

## Description

{description}

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
{diff}
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
{changed_files}
- Available tools: {tool_summary}

## Your task

Work through the CHECKLIST appended below and produce ONE finding PER ITEM — all of them, no
skipping (the checklist has at most {budget} items and your findings budget is {budget}). Then call
`{submit_tool_name}` exactly once with:
- `findings`: one per checklist item, each with `path`, `line_start`/`line_end` anchored at the
  item's site, `severity`, `claim` (the concern instantiated concretely), `suggested_fix`,
  `confidence` (0.0-1.0: probability a maintainer would leave this comment), and — where you got an
  edit to compile — `declaration_name` + `new_declaration` or `line_start`/`line_end` +
  `replacement`.
- `merge_ready_as_is`: your overall judgment.
- `message`: anything noteworthy (verification failures, checklist items whose site no longer
  matches the file)."""


APPLY_ALL_V2_SYSTEM = """You are reconstructing the review comments a Mathlib maintainer would most
plausibly leave on this pull request. The CHECKLIST enumerates every changed SITE with a fixed
battery of FACETS (naming, statement form, proof form, docs, placement, duplication, style,
correctness), some with precedent comments from similar code.

Your output is COUNTERFACTUAL, not a verdict: for each site, write the 2-4 most plausible
maintainer asks — "if a maintainer intervened at this site, the most likely comments are ...".
Each finding names the exact declaration and states a concrete transformation (rename X to Y;
generalize the fixed 2 to any k with 1 < k; move X below the namespace line; fix the docstring
capitalization). Attach `confidence` = your probability a maintainer would actually leave that
comment; express doubt ONLY through low confidence.

Hard rules:
- NEVER write a finding that says the code is fine, a concern does not apply, or an ask is already
  satisfied. There is no verdict channel; if a facet yields no plausible ask, write nothing for it.
- Every site gets at least 1 finding; at most 4. Cover different facets rather than restating one.
- Prefer asks in the style of the site's precedents when they genuinely fit; ground every ask in
  the actual code (name real identifiers).
- For checkable asks (proof/statement changes), verify the edit with lean_verify_edit when you can;
  if it fails to compile, keep the finding claim-only at lower confidence.
- Severity: "blocking" only for policy/correctness violations a maintainer would insist on."""

APPLY_ALL_V2_USER = """## PR #{pr_number} — {title}

## Description

{description}

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
{diff}
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
{changed_files}
- Available tools: {tool_summary}

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most {budget} findings total; spend them on the highest-probability asks across sites.
Then call `{submit_tool_name}` exactly once. `merge_ready_as_is`: your overall judgment."""


class LeanPRReviewInstantiateConfig(BasePRReviewConfig):
    """Instantiation-checker config: worklist input + idiom-style verify/search toolset."""

    enabled_tools: List[str] = list(IDIOM_TOOLS)
    worklist_file: Optional[Path] = Field(
        default=None,
        description="Per-PR site x concern worklist JSONL (site_worklist.py). Required.",
    )
    worklist_max_items: Optional[int] = Field(
        default=None,
        description="DEPRECATED (was a silent weight-ranked site drop). Now interpreted as "
        "worklist_window_size ≈ max_items//3 for back-compat; prefer the window fields.",
    )
    worklist_window_size: Optional[int] = Field(
        default=None,
        description="Sites per work unit. Large PRs are processed in DETERMINISTIC windows "
        "(file order) — never silently dropped; run one task per window via worklist_window.",
    )
    worklist_window: int = Field(
        default=0, description="0-based window index into the PR's site list.")


class LeanPRReviewInstantiateTask(VerifiedPRReviewTask):
    """Checklist-driven instantiation: sites and concerns are given; the model only instantiates."""

    task_type = "lean_pr_review_instantiate"
    task_config_class = LeanPRReviewInstantiateConfig

    def _get_prompts(self, version: str) -> Tuple[str, str]:
        # "apply_all_v2": counterfactual-only — no assertion channel at all (defend-the-code
        # findings consumed ~30% of the identify->issue failures; assertion is instruction-immune,
        # so the output type no longer admits it). "apply_all" (v1): exhaustive with per-finding
        # confidence. Default: the decide (APPLY/SKIP) framing.
        v = str(version or "")
        if v.startswith("apply_all_v2"):
            return APPLY_ALL_V2_SYSTEM, APPLY_ALL_V2_USER
        if v.startswith("apply_all"):
            return APPLY_ALL_SYSTEM, APPLY_ALL_USER
        return INSTANTIATE_SYSTEM, INSTANTIATE_USER

    def _worklist_row(self) -> dict:
        pf = getattr(self.config.task_config, "worklist_file", None)
        if not pf:
            self.logger.warning("worklist_file not set — empty checklist")
            return {}
        pf = Path(pf)
        if not pf.exists():
            self.logger.warning("worklist_file %s missing — empty checklist", pf)
            return {}
        for line in pf.read_text().splitlines():
            if line.strip() and json.loads(line).get("pr_number") == self.data.pr_number:
                return json.loads(line)
        return {}

    def _worklist_block(self) -> str:
        row = self._worklist_row()
        sites = row.get("sites") or []
        if not sites:
            return ("\n\n---\n## CHECKLIST\n\n(no items for this PR — submit an empty review with "
                    "`merge_ready_as_is: true`)\n")
        # Deterministic windowing (file order) — sites are NEVER ranked-and-dropped. A large PR is
        # processed as ceil(n/window_size) work units; this task renders window `worklist_window`.
        cfg = self.config.task_config
        wsize = getattr(cfg, "worklist_window_size", None)
        if not wsize and getattr(cfg, "worklist_max_items", None):
            wsize = max(1, cfg.worklist_max_items // 3)  # back-compat reinterpretation
        window = getattr(cfg, "worklist_window", 0) or 0
        window_note = ""
        if wsize and len(sites) > wsize:
            total = (len(sites) + wsize - 1) // wsize
            lo, hi = window * wsize, min((window + 1) * wsize, len(sites))
            self.logger.info("worklist: PR has %d sites -> %d windows of %d; this task renders "
                             "window %d (sites %d-%d). Other windows need their own work units.",
                             len(sites), total, wsize, window, lo, hi - 1)
            window_note = f" (window {window + 1}/{total}: sites {lo + 1}-{hi} of {len(sites)})"
            sites = sites[lo:hi]
        parts, n = [], 0
        for si, s in enumerate(sites, 1):
            head = (f"### Site {si}: `{s.get('path')}` lines {s.get('line_start')}-"
                    f"{s.get('line_end')}\n```\n{(s.get('site_code') or '')[:1500]}\n```")
            facet_lines = []
            for it in (s.get("items") or []):
                n += 1
                ask = (it.get("typical_ask") or "").strip()
                w = it.get("weight") or 0.0
                wtxt = f" (neighbor weight {w})" if w else ""
                line = f"- Item {n} | **{it.get('concern')}**{wtxt}: {ask}"
                for p in (it.get("precedents") or [])[:2]:
                    line += f"\n    precedent: \"{(p.get('body') or '').strip()[:220]}\""
                facet_lines.append(line)
            parts.append(head + "\n" + "\n".join(facet_lines))
        header = (f"\n\n---\n## CHECKLIST — {len(sites)} sites, {n} facet items{window_note}\n\n")
        return header + "\n\n".join(parts) + "\n"

    async def create_user_prompt(self) -> str:
        return await super().create_user_prompt() + self._worklist_block()


register_task("lean_pr_review_instantiate", LeanPRReviewInstantiateTask)
