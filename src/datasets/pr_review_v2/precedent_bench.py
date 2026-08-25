"""Stage 1 — precedent-retrieval similarity benchmark (docs/research/precedent-retrieval-design.md §7).

The design-chooser and go/no-go gate, run OFFLINE against our own gold before any agent wiring.

Idea: our gold findings double as a retrieval benchmark. For each gold finding we have the SITE
(the anchored diff hunk, code only) and the HIDDEN maintainer comment (the answer key). We query the
historical maintainer-comment corpus (corpus.py) with the site's code, retrieve top-k precedents, and
ask an LLM judge whether a retrieved precedent "predicts" the hidden comment (precedent-hit@k). If a
transferable precedent exists and is findable for a large-enough fraction of real findings, the
case-law hypothesis holds and we build Mode A; if not, we learn it here for ~$20, not after a build.

Pipeline (each step writes an artifact so the expensive LLM-judge step is separable + cacheable):

  # 1. queries  (API-free) — turn gold findings into retrieval queries (site code + hidden comment)
  python -m src.datasets.pr_review_v2.precedent_bench queries

  # 2. retrieve (API-free for lexical/feature; local model for dense) — top-k precedents per query
  python -m src.datasets.pr_review_v2.precedent_bench retrieve --design lexical
  python -m src.datasets.pr_review_v2.precedent_bench retrieve --design dense_code
  python -m src.datasets.pr_review_v2.precedent_bench retrieve --design lexical+feature

  # 3. judge    (LLM) — see precedent_judge.py; consumes the retrieved.jsonl artifacts

  # 4. report   (API-free) — precedent-hit@k per stratum/design + the go/no-go gate
  python -m src.datasets.pr_review_v2.precedent_bench report
"""

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from ape.utils.logging import create_logger
from ape.utils.project import PROJECT_ROOT

BENCH_DIR = PROJECT_ROOT / "inputs" / "pr_review_v2" / "precedent_bench"
DEFAULT_GOLD = PROJECT_ROOT / "inputs" / "pr_review_v2" / "mathlib_pr_review_v2_actionable_20260618.jsonl"
DEFAULT_CORPUS = PROJECT_ROOT / "inputs" / "pr_review_v2" / "corpus" / "mathlib_review_comments.jsonl"
QUERIES_PATH = BENCH_DIR / "queries.jsonl"

# ---------------------------------------------------------------------------
# text prep — a hunk (query site OR corpus precedent) reduced to its code tokens
# ---------------------------------------------------------------------------

_HUNK_HEADER_RE = re.compile(r"^@@.*?@@", re.M)
_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_'.]*|[^\sA-Za-z0-9]")
_DECL_KIND_RE = re.compile(r"\b(theorem|lemma|def|instance|structure|class|abbrev|inductive|example)\b")


def hunk_code(hunk_text: str) -> str:
    """Strip @@ headers and diff +/- markers → just the (added/context) code the comment is about."""
    lines = []
    for line in (hunk_text or "").splitlines():
        if line.startswith("@@") or line.startswith("diff ") or line.startswith("+++") or line.startswith("---"):
            continue
        if line[:1] == "-":  # removed lines: not the reviewed state
            continue
        lines.append(line[1:] if line[:1] == "+" else line)
    return "\n".join(lines).strip()


def tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text or "")


def decl_kinds(hunk_text: str) -> List[str]:
    return sorted(set(_DECL_KIND_RE.findall(hunk_code(hunk_text))))


def namespace_root(path: Optional[str]) -> str:
    """Top-level Mathlib area, e.g. Mathlib/Algebra/Order/Round.lean -> 'Algebra'."""
    parts = [p for p in str(path or "").split("/") if p]
    if len(parts) >= 2 and parts[0] == "Mathlib":
        return parts[1]
    return parts[0] if parts else ""


def path_dirs(path: Optional[str]) -> List[str]:
    """Directory components (for feature overlap), e.g. ['Mathlib','Algebra','Order']."""
    return [p for p in str(path or "").split("/")[:-1] if p]


# ---------------------------------------------------------------------------
# 1. queries — gold findings as retrieval test cases
# ---------------------------------------------------------------------------

def _delta_index(gold: Dict[str, Any]) -> Dict[str, str]:
    """hunk_id -> patch text, from the drift-proof delta the pipeline already resolved."""
    idx: Dict[str, str] = {}
    for h in (gold.get("delta_total") or []):
        hid = h.get("hunk_id")
        if hid:
            idx[hid] = h.get("patch") or ""
    return idx


def build_queries(gold_path: Path, out: Path, logger) -> int:
    recs = [json.loads(l) for l in gold_path.read_text().splitlines() if l.strip()]
    out.parent.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = []
    no_site = 0
    for r in recs:
        gold = r.get("gold") or {}
        didx = _delta_index(gold)
        for c in (gold.get("comments") or []):
            linked = c.get("linked_hunks") or []
            patches = [didx[h] for h in linked if h in didx]
            site_code = "\n\n".join(p for p in patches if p).strip()
            anchor = c.get("anchor") or {}
            path = anchor.get("path")
            if not site_code:  # no resolvable anchored code → cannot form a code query
                no_site += 1
                continue
            rows.append({
                "query_id": c.get("id"),
                "pr_number": r.get("pr_number"),
                "path": path,
                "namespace_root": namespace_root(path),
                "decl_kinds": decl_kinds(site_code),
                "site_code": site_code,
                "hidden_body": c.get("body") or "",
                "stratum": c.get("stratum"),
                "severity": c.get("severity"),
                "kind": c.get("kind"),
                "author": c.get("author"),
                "linked_hunks": linked,
            })
    out.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n")
    by_stratum = Counter(x["stratum"] for x in rows)
    logger.info("Queries: %d gold findings with resolvable site code (%d had none) -> %s",
                len(rows), no_site, out)
    logger.info("  by stratum: %s", dict(sorted(by_stratum.items(), key=lambda kv: str(kv[0]))))
    return len(rows)


def load_queries(path: Path = QUERIES_PATH) -> List[Dict[str, Any]]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# 2. corpus + retrievers
# ---------------------------------------------------------------------------

def load_corpus(path: Path = DEFAULT_CORPUS) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Corpus not found at {path}. Run `python -m "
                                f"src.datasets.pr_review_v2.corpus` first.")
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


class BM25:
    """Compact BM25 over tokenized documents — no external deps, the API-free lexical baseline."""

    def __init__(self, docs_tokens: Sequence[Sequence[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(t) for t in docs_tokens]
        self.lengths = [sum(c.values()) for c in self.docs]
        self.avgdl = (sum(self.lengths) / len(self.lengths)) if self.docs else 0.0
        df: Counter = Counter()
        for c in self.docs:
            df.update(c.keys())
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    def scores(self, query_tokens: Sequence[str]) -> List[float]:
        q = [t for t in set(query_tokens) if t in self.idf]
        out = [0.0] * len(self.docs)
        for i, c in enumerate(self.docs):
            dl = self.lengths[i] or 1
            s = 0.0
            for t in q:
                f = c.get(t, 0)
                if not f:
                    continue
                s += self.idf[t] * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            out[i] = s
        return out


class LexicalRetriever:
    """BM25 over corpus hunk code."""

    name = "lexical"

    def __init__(self, corpus: List[Dict[str, Any]], logger=None):
        self.corpus = corpus
        self._toks = [tokenize(hunk_code(c.get("diff_hunk") or "")) for c in corpus]
        self.bm25 = BM25(self._toks)

    def retrieve(self, query: Dict[str, Any], k: int) -> List[Tuple[int, float]]:
        scores = self.bm25.scores(tokenize(query["site_code"]))
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [(i, scores[i]) for i in ranked[:k] if scores[i] > 0]


class FeatureBoostRetriever:
    """Lexical, but boost precedents that share the query's namespace root / decl kind.

    A cheap encoding of the 'concern-conditional similarity' hypothesis (namespace+decl-kind for
    naming/idiom) layered on the lexical baseline — the baseline to beat, not the final design."""

    name = "lexical+feature"

    def __init__(self, corpus: List[Dict[str, Any]], logger=None, boost: float = 0.5):
        self.corpus = corpus
        self.boost = boost
        self._ns = [namespace_root(c.get("path")) for c in corpus]
        self._kinds = [set(decl_kinds(c.get("diff_hunk") or "")) for c in corpus]
        self._lex = LexicalRetriever(corpus, logger)

    def retrieve(self, query: Dict[str, Any], k: int) -> List[Tuple[int, float]]:
        scores = list(self._lex.bm25.scores(tokenize(query["site_code"])))
        qns, qkinds = query.get("namespace_root"), set(query.get("decl_kinds") or [])
        mx = max(scores) or 1.0
        for i in range(len(scores)):
            if scores[i] <= 0:
                continue
            bump = 0.0
            if qns and self._ns[i] == qns:
                bump += self.boost
            if qkinds and (qkinds & self._kinds[i]):
                bump += self.boost
            scores[i] += bump * mx
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [(i, scores[i]) for i in ranked[:k] if scores[i] > 0]


class DenseRetriever:
    """Dense-code retrieval via a local SentenceTransformer (no API). Embeds corpus hunk code once,
    cosine top-k. Model default matches ape/toolkits/retrieve (all-MiniLM-L6-v2)."""

    name = "dense_code"

    def __init__(self, corpus: List[Dict[str, Any]], logger=None,
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer  # local, lazy
        import numpy as np
        self.np = np
        self.corpus = corpus
        self.model = SentenceTransformer(model_name)
        texts = [hunk_code(c.get("diff_hunk") or "") for c in corpus]
        if logger:
            logger.info("Dense: embedding %d corpus hunks with %s", len(texts), model_name)
        self.emb = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=bool(logger),
                                     batch_size=256)

    def retrieve(self, query: Dict[str, Any], k: int) -> List[Tuple[int, float]]:
        q = self.model.encode([query["site_code"]], normalize_embeddings=True)[0]
        sims = self.emb @ q
        idx = self.np.argsort(-sims)[:k]
        return [(int(i), float(sims[i])) for i in idx]


RETRIEVERS = {
    "lexical": LexicalRetriever,
    "lexical+feature": FeatureBoostRetriever,
    "dense_code": DenseRetriever,
}


# ---------------------------------------------------------------------------
# 2b. retrieval runner — write top-k precedents per query for the judge
# ---------------------------------------------------------------------------

def _candidate(corpus_row: Dict[str, Any], score: float) -> Dict[str, Any]:
    return {
        "comment_id": corpus_row.get("comment_id"),
        "pr_number": corpus_row.get("pr_number"),
        "path": corpus_row.get("path"),
        "score": round(float(score), 5),
        "precedent_body": corpus_row.get("body") or "",
        "precedent_code": corpus_row.get("diff_hunk") or "",
        "commenter": corpus_row.get("commenter"),
        "created_at": corpus_row.get("created_at"),
    }


def run_retrieval(design: str, k: int, corpus_path: Path, out: Path, logger) -> Path:
    if design not in RETRIEVERS:
        raise ValueError(f"Unknown design {design!r}; choose from {sorted(RETRIEVERS)}")
    queries = load_queries()
    corpus = load_corpus(corpus_path)
    logger.info("Retrieval design=%s: %d queries over %d corpus situations, top-%d",
                design, len(queries), len(corpus), k)
    retriever = RETRIEVERS[design](corpus, logger=logger)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for q in queries:
            hits = retriever.retrieve(q, k)
            fh.write(json.dumps({
                "query_id": q["query_id"],
                "pr_number": q["pr_number"],
                "stratum": q["stratum"],
                "path": q["path"],
                "site_code": q["site_code"],
                "hidden_body": q["hidden_body"],
                "design": design,
                "candidates": [_candidate(corpus[i], s) for i, s in hits],
            }, ensure_ascii=False) + "\n")
    logger.info("Wrote retrieval -> %s", out)
    return out


# ---------------------------------------------------------------------------
# 4. report — precedent-hit@k + go/no-go gate (consumes judged artifacts)
# ---------------------------------------------------------------------------

def _hit_at_k(judged: List[Dict[str, Any]], k: int) -> Tuple[int, int]:
    """A query is a hit@k if any of its first-k candidates was judged a precedent-hit."""
    hits = total = 0
    for q in judged:
        cands = q.get("candidates", [])[:k]
        total += 1
        if any(c.get("hit") for c in cands):
            hits += 1
    return hits, total


def report(judged_paths: List[Path], ks: Sequence[int], logger) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    for jp in judged_paths:
        judged = [json.loads(l) for l in jp.read_text().splitlines() if l.strip()]
        design = judged[0].get("design", jp.stem) if judged else jp.stem
        by_stratum: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for q in judged:
            by_stratum[q.get("stratum") or "?"].append(q)
        d: Dict[str, Any] = {"overall": {}, "by_stratum": {}}
        for k in ks:
            h, t = _hit_at_k(judged, k)
            d["overall"][f"hit@{k}"] = f"{h}/{t} ({100*h/t:.0f}%)" if t else "0/0"
        for strat, qs in sorted(by_stratum.items()):
            d["by_stratum"][strat] = {}
            for k in ks:
                h, t = _hit_at_k(qs, k)
                d["by_stratum"][strat][f"hit@{k}"] = f"{h}/{t} ({100*h/t:.0f}%)" if t else "0/0"
        mix = Counter(c.get("relation", "?") for q in judged
                      for c in q.get("candidates", [])[:max(ks)])
        d["relation_mix"] = dict(mix)
        summary[design] = d
        logger.info("[%s] overall %s", design, d["overall"])
        for strat, v in d["by_stratum"].items():
            logger.info("    %s: %s", strat, v)
        logger.info("    relation mix (top-%d cands): %s", max(ks), dict(mix))
    # go/no-go gate on best hit@10
    best = 0.0
    for jp in judged_paths:
        judged = [json.loads(l) for l in jp.read_text().splitlines() if l.strip()]
        h, t = _hit_at_k(judged, max(ks))
        best = max(best, (h / t) if t else 0.0)
    gate = ("STRONG GO (case law transfers)" if best >= 0.40 else
            "GO, partial coverage" if best >= 0.20 else
            "STOP — precedent hypothesis fails or corpus too small/stale")
    logger.info("GATE: best hit@%d = %.0f%% -> %s", max(ks), 100 * best, gate)
    summary["_gate"] = {"best_hit_at_max_k": round(best, 3), "verdict": gate}
    (BENCH_DIR / "report.json").write_text(json.dumps(summary, indent=2))
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(description="Stage 1 precedent-retrieval similarity benchmark")
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("queries", help="build retrieval queries from gold findings (API-free)")
    q.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    q.add_argument("--out", type=Path, default=QUERIES_PATH)

    r = sub.add_parser("retrieve", help="retrieve top-k precedents per query")
    r.add_argument("--design", default="lexical", choices=sorted(RETRIEVERS))
    r.add_argument("--k", type=int, default=10)
    r.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    r.add_argument("--out", type=Path, default=None)

    rep = sub.add_parser("report", help="precedent-hit@k + go/no-go gate from judged artifacts")
    rep.add_argument("--judged", type=Path, nargs="*", default=None)
    rep.add_argument("--ks", type=int, nargs="*", default=[1, 3, 5, 10])

    args = p.parse_args()
    logger = create_logger()
    if args.cmd == "queries":
        build_queries(args.gold, args.out, logger)
    elif args.cmd == "retrieve":
        out = args.out or (BENCH_DIR / f"retrieved_{args.design}.jsonl")
        run_retrieval(args.design, args.k, args.corpus, out, logger)
    elif args.cmd == "report":
        judged = args.judged or sorted(BENCH_DIR.glob("judged_*.jsonl"))
        if not judged:
            logger.warning("No judged_*.jsonl found in %s; run precedent_judge.py first", BENCH_DIR)
            return
        report(judged, args.ks, logger)


if __name__ == "__main__":
    main()
