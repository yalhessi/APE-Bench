"""Classify val1000's removed declarations from structure alone: no review text, no model.

    PYTHONPATH=$PWD:$PWD/src ape/bin/python \
      results/pr_review_v5/adjudications/removed-declarations-val1000-2025-06-2026-03-v1/provenance/classify_removed.py \
      <structure_dir> <out.jsonl>

`<structure_dir>` is what `arm-coverage-val1000-2025-06-2026-03-v1/provenance/build_structure.py`
writes: change graphs, inventory and episodes for val1000's 973 PRs. The sealed draw gives the AI
flag (`ai` is the AI stratum, as the replication doc counts it; `ai_evidence` is the draw's flag,
which 28 main-stratum PRs also carry). "Removed" is the inventory's lifecycle on a declaration target (912 on 205 PRs). For each
one it records every trace the PR leaves of it, then assigns one class by the precedence in `cls`.
"""
import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

from src.datasets.pull_requests.projections.frame import seal_dir
from src.mathlib_review.release.change_graph import parse_unified_diff

DRAW = "val1000-2025-06-2026-03-v1"
DECL_SUBJECTS = {"theorem", "definition", "instance", "structure_or_class", "inductive", "abbreviation"}
META = re.compile(r"^(Mathlib/Tactic|Mathlib/Linter|Mathlib/Util|Mathlib/Lean|MathlibTest|test|scripts|Archive|Counterexamples)/")
AUX = re.compile(r"(^|[._])aux|Aux|(^|[._])(impl|Impl)$|_impl\b")
KW = r"theorem|lemma|def|abbrev|instance|structure|class|inductive|example|opaque|axiom"
IDENT_TAIL = r"[\w'!?₀-₉ₐ-ₜᵢ-ᵪ]"
GENERATORS = re.compile(r"\b(to_dual|to_additive|to_fun|reassoc|simps!?|elementwise|to_app)\b")

# Name translations the generating attributes apply, each pair read both ways. Only used to ask
# "is the removed name what an attribute added in this PR now generates from a sibling?".
DUAL = [("Bot", "Top"), ("bot", "top"), ("Inf", "Sup"), ("inf", "sup"), ("iInf", "iSup"), ("sInf", "sSup"),
        ("le", "ge"), ("lt", "gt"), ("min", "max"), ("Min", "Max"), ("lower", "upper"), ("Lower", "Upper"),
        ("Ici", "Iic"), ("Ioi", "Iio"), ("Ico", "Ioc"), ("antitone", "monotone"), ("Antitone", "Monotone"),
        ("pred", "succ"), ("Pred", "Succ"), ("isLeast", "isGreatest"), ("IsLeast", "IsGreatest"),
        ("isGLB", "isLUB"), ("IsGLB", "IsLUB"), ("bddBelow", "bddAbove"), ("BddBelow", "BddAbove"),
        ("lowerBounds", "upperBounds"), ("isMin", "isMax"), ("IsMin", "IsMax"), ("minimal", "maximal"),
        ("atBot", "atTop"), ("left", "right"), ("hom_inv", "inv_hom"), ("mono", "epi"), ("Mono", "Epi"),
        ("Coatom", "Atom"), ("coatom", "atom"), ("Initial", "Terminal"), ("initial", "terminal"), ("fst", "snd")]
ADDITIVE = [("mul", "add"), ("Mul", "Add"), ("one", "zero"), ("One", "Zero"), ("prod", "sum"), ("inv", "neg"),
            ("Inv", "Neg"), ("div", "sub"), ("Div", "Sub"), ("pow", "nsmul"), ("smul", "vadd"), ("SMul", "VAdd"),
            ("Monoid", "AddMonoid"), ("Group", "AddGroup"), ("Units", "AddUnits"), ("mulIndicator", "indicator"),
            ("finprod", "finsum"), ("Submonoid", "AddSubmonoid"), ("Subgroup", "AddSubgroup"), ("Hom", "AddHom")]
SUFFIXES = ("_assoc", "_symm_apply", "_apply", "_coe", "_toFun", "_app", "_hom", "_inv", "_obj", "_map")

S, OUT = Path(sys.argv[1]), Path(sys.argv[2])
graphs = {g["pr_number"]: g for g in map(json.loads, open(S / "change_graphs.jsonl"))}
inv = defaultdict(list)
for r in map(json.loads, open(S / "modification_inventory.jsonl")):
    inv[r["pr_number"]].append(r)
eps = {e["pr_number"]: e for e in map(json.loads, open(S / "episodes.jsonl"))}
draw = json.loads((seal_dir(DRAW) / "draw.json").read_text())
ai = {a["pr_number"]: a["stratum"].startswith("ai") for a in draw["accepted"]}
ai_evidence = {a["pr_number"]: bool(a.get("ai_evidence")) for a in draw["accepted"]}


def short(name):
    return name.replace("_root_.", "").split(".")[-1]


def tok(name):
    return re.compile(r"(?<![\w'])" + re.escape(name) + r"(?!" + IDENT_TAIL + ")")


def header(code):
    for line in code.split("\n"):
        if re.search(rf"(^|\s)({KW})\b", line):
            return line
    return code.split("\n")[0]


def statement(code, name):
    """Text between the declaration's name (or `instance` keyword) and its `:=` / `where` / first
    `|` arm, whitespace collapsed."""
    code = re.sub(r"/--.*?-/", "", code, flags=re.S)
    code = re.sub(r"@\[[^\]]*\]", "", code)
    m = (re.search(r"(?<![\w'.])" + re.escape(short(name)) + r"(?!" + IDENT_TAIL + ")", code) if name
         else re.search(r"\binstance\b(\s*\(priority[^)]*\))?", code))
    if not m:
        return None
    rest = code[m.end():]
    cut = [i for i in (rest.find(":="), rest.find(" where"), rest.find("\n  |"), rest.find("\n|")) if i >= 0]
    rest = rest[: min(cut)] if cut else rest
    return re.sub(r"\s+", " ", rest).strip() or None


def _swap_all(s, table):
    """Swap every pair in `table` at once, longest key first, as a generating attribute does."""
    pairs = {**{a: b for a, b in table}, **{b: a for a, b in table}}
    keys = sorted(pairs, key=len, reverse=True)
    return re.sub("|".join(map(re.escape, keys)), lambda m: pairs[m.group(0)], s)


def conclusion(stmt):
    """The text after the last ` : ` outside brackets: a statement without its binders, so a move
    that turned binders into section variables still compares equal."""
    if not stmt:
        return stmt
    depth, cut = 0, -1
    for i, ch in enumerate(stmt):
        depth += ch in "([{⦃⟨" and 1 or 0
        depth -= ch in ")]}⦄⟩" and 1 or 0
        if depth == 0 and stmt[i:i + 3] == " : ":
            cut = i + 3
    return stmt[cut:].strip() if cut >= 0 else stmt.lstrip(": ").strip()


def translations(s):
    out = set()
    for table in (DUAL, ADDITIVE):
        out.add(_swap_all(s, table))
        for a, b in table:
            for x, y in ((a, b), (b, a)):
                if x in s:
                    out.add(s.replace(x, y))
    if s.startswith("fun_"):
        out.add(s[4:])
    if "_fun_" in s:
        out.add(s.replace("_fun_", "_"))
    out.update(s[: -len(x)] for x in SUFFIXES if s.endswith(x) and len(s) > len(x))
    return out - {s}


ALIAS = re.compile(
    r"@\[(?P<attrs>[^\]]*deprecated[^\]]*)\]\s*(?:(?:protected|private|noncomputable|nonrec|theorem|lemma)\s+)*"
    r"alias\s+(?P<old>⟨[^⟩]*⟩|\S+)\s*:=\s*(?P<new>\S+)")
DEPRECATED_TO = re.compile(r"deprecated\s+(?P<new>[^\s(\]]+)")


def diff_lines(diff_file):
    return [l for h in diff_file.hunks for l in h.lines if l[:1] in "+- " and not l.startswith(("+++", "---"))]


rows = []
for pr, g in sorted(graphs.items()):
    lifecycle = {r["primary_change_id"]: r for r in inv[pr]}
    decl_targets = [t for t in g["targets"] if t["kind"] == "declaration"]
    removed = [t for t in decl_targets if lifecycle.get(t["change_id"], {}).get("lifecycle") == "removed"
               and lifecycle[t["change_id"]]["subject_kind"] in DECL_SUBJECTS]
    if not removed:
        continue
    files = parse_unified_diff(eps[pr]["diff"])
    by_old = {(f.old_path or f.path): f for f in files}
    file_status = {(f.old_path or f.path): f.status for f in files}
    plus_text = {f.path: "\n".join(l[1:] for l in diff_lines(f) if l[0] == "+") for f in files}
    all_plus = "\n".join(plus_text.values())
    minus = {(f.old_path or f.path): [l[1:] for l in diff_lines(f) if l[0] == "-"] for f in files}
    generators = sorted(set(GENERATORS.findall(all_plus)))
    aliases = []
    for path, text in plus_text.items():
        for m in ALIAS.finditer(text):
            new = m.group("new")
            d = DEPRECATED_TO.search(m.group("attrs"))
            aliases.append({"path": path, "old": [o.strip() for o in m.group("old").strip("⟨⟩").split(",")],
                            "new": new, "attr_target": d.group("new") if d else None})
    reviewed = [e for e in g["entities"] if e["side"] == "reviewed" and e["kind"] not in ("command", "module_doc")]
    reviewed_full = defaultdict(set)   # fullname -> paths
    reviewed_short = defaultdict(set)  # short -> fullnames
    reviewed_stmt = {}                 # (path, fullname) -> statement
    for e in reviewed:
        if e["fullname"]:
            reviewed_stmt[(e["path"], e["fullname"])] = statement(e["code"], e["fullname"])
    for e in reviewed:
        if e["fullname"]:
            reviewed_full[e["fullname"]].add(e["path"])
            reviewed_short[short(e["fullname"])].add(e["fullname"])
    added = [t for t in decl_targets if lifecycle.get(t["change_id"], {}).get("lifecycle") == "added"]
    added_statements = defaultdict(list)
    for t in added:
        s = statement(t["reviewed_code"] or "", t["declaration_name"])
        if s:
            added_statements[s].append(t["declaration_name"] or "(instance)")

    for t in removed:
        rec = lifecycle[t["change_id"]]
        name, path, base = t["declaration_name"], t["path"], t["base_code"] or ""
        s_name = short(name) if name else None
        hdr = header(base)
        fl = diff_lines(by_old[path]) if path in by_old else []
        header_deleted = ("-" + hdr) in fl
        attrs_head = base[: base.find(hdr)] + hdr if hdr in base else hdr
        stmt = statement(base, name)
        own = set(base.split("\n"))
        row = {
            "pr": pr, "ai": ai.get(pr, False), "ai_evidence": ai_evidence.get(pr, False), "title": eps[pr]["title"]["text"], "change_id": t["change_id"],
            "path": path, "name": name, "short": s_name, "decl_kind": t["declaration_kind"],
            "subject_kind": rec["subject_kind"], "visibility": rec["visibility"],
            "file_status": file_status.get(path), "meta_path": bool(META.match(path)),
            "aux_name": bool(s_name and AUX.search(s_name)), "header": hdr[:160],
            "header_deleted": header_deleted,
            "survives_same_file": bool(name and path in reviewed_full.get(name, set())),
            "same_file_statement_equal": bool(name) and reviewed_stmt.get((path, name)) == stmt,
            "other_file_statement_equal": bool(name) and any(conclusion(reviewed_stmt.get((p, name))) == conclusion(stmt)
                                                             for p in reviewed_full.get(name, set()) if p != path),
            "already_deprecated": "deprecated" in attrs_head,
            "same_fullname_other_file": sorted(p for p in reviewed_full.get(name, set()) if p != path) if name else [],
            # a namespace rename: the same short name on a declaration this PR *adds* elsewhere
            "same_short_other_namespace": sorted(a["declaration_name"] for a in added
                                                 if name and a["declaration_name"] and a["declaration_name"] != name
                                                 and short(a["declaration_name"]) == s_name),
            "generators_added": generators,
            "generator_names_it": bool(s_name) and any(GENERATORS.search(l) and tok(s_name).search(l)
                                                       for l in all_plus.split("\n")),
            "generated_from": sorted({x for tr in (translations(s_name) if s_name else ()) for x in reviewed_short.get(tr, ())}
                                     | {tr for tr in (translations(name) if name else ()) if tr in reviewed_full}),
            "alias": [a for a in aliases if name and any(o.replace("_root_.", "") in (name, s_name) or
                                                       name.endswith("." + o.replace("_root_.", "")) for o in a["old"])],
            # a plain (not deprecated) `alias old := new` keeps the old name alive
            "plain_alias": bool(s_name) and any(re.search(r"^\s*(?:protected\s+)?alias\s+(?:⟨[^⟩]*\b|)(?:[\w'.₀-₉]*\.)?" + re.escape(s_name) + r"(?![\w'])", l)
                                                 and "deprecated" not in l for l in all_plus.split("\n")),
            "deprecated_mention": bool(s_name) and any("deprecated" in l and tok(s_name).search(l) for l in all_plus.split("\n")),
            "name_on_plus": bool(s_name and tok(s_name).search(all_plus)),
            "statement": stmt,
            "same_statement_added": [n for n in added_statements.get(stmt, []) if n != name] if stmt else [],
            "uses_rewritten_lines": sum(1 for ls in minus.values() for l in ls if s_name and l not in own and tok(s_name).search(l)),
        }
        new_names = {a["new"] for a in row["alias"]} | {a["attr_target"] for a in row["alias"] if a["attr_target"]}
        row["alias_target_added"] = sorted(n for n in new_names if any(x == n or x.endswith("." + n) or n.endswith("." + x)
                                                                        for x in (a["declaration_name"] or "" for a in added)))
        rows.append(row)


def cls(r):
    if not r["header_deleted"]:
        return "survives_in_place"        # inventory artifact: lines deleted inside a declaration that remains
    if r["survives_same_file"]:
        # the same full name is still declared in the file: cut and pasted within it, or its
        # statement edited in a way the graph split into removed + added
        return "survives_moved_in_file" if r["same_file_statement_equal"] else "survives_restated"
    if r["already_deprecated"]:
        return "expired_deprecation"
    if r["same_fullname_other_file"]:
        # the same full name declared in another file: a move if the statement is unchanged,
        # otherwise the name now belongs to a different (usually merged or more general) statement
        return "move" if r["other_file_statement_equal"] else "moved_restated"
    if r["name"] is None and r["same_statement_added"]:
        return "move"                     # an anonymous instance: the same instance type re-added
    if r["plain_alias"] and not (r["alias"] or r["deprecated_mention"]):
        return "survives_as_alias"         # a plain `alias` keeps the name
    if r["alias"] or r["deprecated_mention"]:
        if r["same_statement_added"] or r["same_short_other_namespace"]:
            return "rename_deprecated"
        if r["alias_target_added"]:
            return "superseded_by_new_deprecated"
        return "deprecated_to_existing"
    if r["generators_added"] and (r["generated_from"] or r["generator_names_it"]):
        return "attribute_generated"
    if r["subject_kind"] == "instance":
        return "instance_removed"         # instances are found by type, not name; deprecation is not the question
    if r["same_statement_added"] or r["same_short_other_namespace"]:
        return "rename_no_alias"
    if r["visibility"] == "private" or r["decl_kind"] == "example":
        return "private_or_example"
    if r["aux_name"] or r["meta_path"]:
        return "aux_or_meta"
    if r["name_on_plus"]:
        return "deleted_name_recurs"
    return "deleted_no_trace"


for r in rows:
    r["class"] = cls(r)
with open(OUT, "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

c = Counter((r["class"], r["ai"]) for r in rows)
order = [k for k, _ in Counter(r["class"] for r in rows).most_common()]
print(f"{len(rows)} removed declarations on {len({r['pr'] for r in rows})} PRs "
      f"(AI: {sum(r['ai'] for r in rows)} on {len({r['pr'] for r in rows if r['ai']})})")
print(f"{'class':30s} {'main':>5s} {'AI':>4s} {'PRs':>4s}  top PR share")
for k in order:
    prs = Counter(r["pr"] for r in rows if r["class"] == k)
    top = prs.most_common(1)[0]
    print(f"{k:30s} {c[(k, False)]:5d} {c[(k, True)]:4d} {len(prs):4d}  {top[0]}:{top[1]}")
