"""Classify recorded lean_verify_edit calls by what they change, to size each safe shortcut.

  proof_only     one theorem/lemma's text changes; its statement, name and attributes do not, and no
                 other command changes. Nothing after it can change: cut the file after it.
  stmt_unused    one theorem/lemma changes its statement or name, carries no attributes, and no later
                 text in the file contains its old or new name's last component (a conservative
                 stand-in for "nothing later refers to it", dot notation included). Cut after it.
  header         the import header changes.
  needs_suffix   anything else: a def/instance/structure, attributes, several declarations, or a
                 non-declaration command (variable, open, section ...). Lean must redo what follows.
Also records where the edit is (first changed line / file length) and splices exactly as the tool.
Usage (cwd: the tree whose tool the runs used): classify_edits.py <run[,run]> <out.json>
"""
import collections, glob, json, re, sys
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, ".")
import ape.tasks.lean_tasks.formal_math.review.base as review_base  # noqa: E402
from ape.toolkits.code.lean.lean_parser import parse_major_declarations  # noqa: E402
from ape.toolkits.code.lean.provider import LeanCodeToolsProvider  # noqa: E402
nocomment = LeanCodeToolsProvider.remove_comments

DELETES_SPAN = "if replacement else []" in Path("src/ape/tasks/lean_tasks/formal_math/review/base.py").read_text()
IMPORT = re.compile(r"^\s*(?:public\s+|private\s+)?(?:meta\s+)?import\s+(\S+)", re.M)
ATTR = re.compile(r"@\[[^\]]*\]")
norm = lambda s: re.sub(r"\s+", " ", s).strip().removesuffix(":=").strip()  # noqa: E731


def splice(src, inp):
    if inp.get("declaration_name") and inp.get("new_declaration"):
        code, _ = review_base.splice_declaration(src, inp["declaration_name"], inp["new_declaration"], label="x")
        return code, "decl"
    ls, le, rep = inp.get("line_start"), inp.get("line_end"), inp.get("replacement")
    lines = src.split("\n")
    if not (isinstance(ls, int) and isinstance(le, int) and 1 <= ls <= le <= len(lines)):
        return None, "line"
    body = (str(rep).split("\n") if rep else []) if DELETES_SPAN else str(rep).split("\n")
    return "\n".join(lines[: ls - 1] + body + lines[le:]), "line"


def header(src):
    return IMPORT.findall(src[: (parse_major_declarations(src) or [None])[0].span[0]]
                          if parse_major_declarations(src) else src)


def attrs_before(src, d):
    # attributes written immediately before the declaration keyword
    pre = src[max(0, d.span[0] - 400): d.span[0]]
    m = re.search(r"(@\[[^\]]*\]\s*)+$", pre)
    return (m.group(0) if m else "") + " ".join(ATTR.findall(src[d.span[0]: d.span[0] + 200].split(":", 1)[0]))


def outside(src, decls):
    out, pos = [], 0
    for d in decls:
        out.append(src[pos:d.span[0]]); pos = d.span[1]
    out.append(src[pos:])
    return [norm(nocomment(x)) for x in out]


def classify(src, code, decls_old):
    decls_new = parse_major_declarations(code)
    if header(src) != header(code):
        return "header"
    if len(decls_old) != len(decls_new):
        return "needs_suffix:decl_count"
    if outside(src, decls_old) != outside(code, decls_new):
        return "needs_suffix:other_command"
    changed = [(o, n) for o, n in zip(decls_old, decls_new)
               if norm(nocomment(src[o.span[0]:o.span[1]])) != norm(nocomment(code[n.span[0]:n.span[1]]))]
    if len(changed) != 1:
        return "needs_suffix:several_decls" if changed else "comment_only"
    o, n = changed[0]
    if o.kind not in ("theorem", "lemma") or n.kind not in ("theorem", "lemma"):
        return f"needs_suffix:kind={o.kind}"
    if attrs_before(src, o) != attrs_before(code, n):
        return "needs_suffix:attributes"
    if o.name == n.name and norm(nocomment(o.signature)) == norm(nocomment(n.signature)):
        return "proof_only"
    if attrs_before(src, o).strip():
        return "needs_suffix:stmt_with_attrs"
    later = src[o.span[1]:]
    for name in {o.name, n.name}:
        last = (name or "").split(".")[-1]
        if not last or re.search(r"(?<![\w'.])" + re.escape(last) + r"(?![\w'])", later) \
                or re.search(r"\." + re.escape(last) + r"(?![\w'])", later):
            return "needs_suffix:stmt_used_later"
    return "stmt_unused"


def first_changed_line(a, b):
    for i, (x, y) in enumerate(zip(a.split("\n"), b.split("\n"))):
        if x != y:
            return i + 1
    return min(a.count("\n"), b.count("\n")) + 1


runs = sys.argv[1].split(",")
rows, cache = [], {}
for run in runs:
    for conv in glob.glob(f".ape/runs/{run}/tasks/*/samples/*/attempts/*/claude_code_conversation_*.jsonl"):
        tgt = Path(conv).parent / "workspaces/target"
        if not tgt.exists():
            continue
        ws = tgt.resolve()
        for line in open(conv, errors="replace"):
            try:
                ev = json.loads(line)
            except Exception:
                continue
            cont = (ev.get("message") or {}).get("content")
            if not isinstance(cont, list):
                continue
            for x in cont:
                if x.get("type") != "tool_use" or not x.get("name", "").endswith("lean_verify_edit"):
                    continue
                inp = x.get("input") or {}
                rel = (inp.get("path") or "").removeprefix("target/")
                fp = ws / rel
                if not rel or not fp.is_file():
                    continue
                if not (inp.get("new_declaration") or inp.get("line_start") is not None):
                    rows.append(dict(run=run, ws=ws.name, rel=rel, cls="as_is")); continue
                if str(fp) not in cache:
                    s = fp.read_text(encoding="utf-8"); cache[str(fp)] = (s, parse_major_declarations(s))
                src, decls = cache[str(fp)]
                code, mode = splice(src, inp)
                if not code or code == src:
                    rows.append(dict(run=run, ws=ws.name, rel=rel, mode=mode, cls="invalid_or_noop")); continue
                try:
                    cls = classify(src, code, decls)
                except Exception as e:  # noqa: BLE001
                    cls = f"parse_error"
                rows.append(dict(run=run, ws=ws.name, rel=rel, mode=mode, cls=cls,
                                 pos=first_changed_line(src, code) / max(1, src.count("\n") + 1),
                                 lines=src.count("\n") + 1,
                                 header_old=header(src) if cls == "header" else None,
                                 header_new=header(code) if cls == "header" else None))
json.dump(rows, open(sys.argv[2], "w"))
c = collections.Counter((r.get("mode", "-"), r["cls"]) for r in rows)
tot = sum(v for (m, k), v in c.items() if k not in ("as_is", "invalid_or_noop"))
print(f"{len(rows)} calls; {tot} classifiable edits")
for k in sorted({k for (m, k) in c}):
    d, l = c.get(("decl", k), 0), c.get(("line", k), 0) + c.get(("-", k), 0)
    print(f"  {k:16} decl {d:4d}  line {l:4d}  ({(d + l) / max(tot, 1):.0%} of edits)" if k not in ("as_is", "invalid_or_noop")
          else f"  {k:16} {d + l:4d}")
early = [r for r in rows if r.get("pos") is not None and r["pos"] < 0.5 and r["cls"].startswith("needs_suffix")]
print(f"needs_suffix in the first half of the file: {len(early)} of {tot}")
