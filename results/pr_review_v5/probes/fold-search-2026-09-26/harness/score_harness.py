"""Score the file-level harness. Per ask: did the file compile (no errors before the fold
commands), what did the SITE declaration fold to, does that include the readers' analogue, and how
many folds landed on the other added declarations (noise)."""
import json, re, sys
from pathlib import Path
from collections import Counter, defaultdict
import sys
H = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/b9848b08-eb04-43a7-9e77-0f87417755b6/scratchpad/fold/harness")
index = json.load(open(H / "index.json"))
STOP = {"the", "The", "of", "for", "in", "with", "and", "or", "as", "via", "on", "to", "from", "instead", "existing", "lemma", "lemmas", "API", "predicate", "class", "instance", "structure", "def", "definition", "notation", "scoped", "variant", "version", "form", "sibling", "siblings", "twin", "dual", "PR", "PR's", "own", "same", "file", "above", "below", "just", "directly", "should", "use", "used", "rather", "than", "its", "it", "is", "be", "an", "a", "by", "at", "not", "no", "over", "under", "into", "which", "that", "this", "these", "those", "one", "two", "where", "when", "then", "so", "but", "if", "iff", "Prop", "Type", "Sort", "fun", "let", "have", "match"}
def analogue_keys(texts):
    """Lean-looking names in the readers' analogue text: backticked spans first, else dotted or
    snake_case identifiers; plain English words are dropped."""
    keys = set()
    for t in texts:
        spans = re.findall(r"`([^`]+)`", t)
        pool = spans if spans else [t]
        for span in pool:
            for n in re.findall(r"[A-Za-z_][\w'.₀-₉!?]*", span):
                n = n.strip(".'")
                if not n or n in STOP or len(n) < 3: continue
                if "." in n or "_" in n or (n[0].isupper() and any(c.islower() for c in n)):
                    keys.add(n)
    return keys
def parse(out, own_decls=()):
    """{decl: [fold records]} and error lines. A fold record may span several lines: it starts at
    `#fold ` and ends at the `[const, via X, kind]` tag; a following `as a function of` line is its
    function-level form. Folds whose `via` is one of the file's own declarations are self-folds and dropped."""
    decls = defaultdict(list); cur = None; errors = []
    lines = out.splitlines(); i = 0
    TAG = re.compile(r"\[([^,\]]+), via ([^,\]]+), ([^\]]+)\]\s*$")
    while i < len(lines):
        l = lines[i]
        if ": error" in l: errors.append(l)
        m = re.match(r".*#fold_decl (\S+) : (type|body)", l)
        if m: cur = m.group(1); i += 1; continue
        if "#fold " in l and cur:
            rec = l[l.index("#fold ") + 6:]; j = i
            while not TAG.search(rec) and j + 1 < len(lines) and "#fold" not in lines[j + 1] and ": error" not in lines[j + 1]:
                j += 1; rec += " " + lines[j].strip()
            t = TAG.search(rec)
            if t and "⇒" in rec:
                sub, fold = rec[:t.start()].split("⇒", 1) if rec.count("⇒") >= 1 else (rec[:t.start()], "")
                fn = None
                if j + 1 < len(lines) and "as a function of" in lines[j + 1]: fn = lines[j + 1].split(":", 1)[-1].strip(); j += 1
                via = t.group(2).strip()
                kind_tier = [x.strip() for x in t.group(3).split(",")]
                kind = kind_tier[0]; tier = kind_tier[1] if len(kind_tier) > 1 else "untiered"
                if via not in own_decls:
                    decls[cur].append(dict(sub=sub.strip(), fold=fold.strip(), const=t.group(1).strip(), via=via, kind=kind, tier=tier, fn=fn))
            i = j + 1; continue
        i += 1
    return decls, errors
rows = []
for a in index:
    p = H / f"{a['cid']}.out"
    if not p.exists(): rows.append(dict(cid=a["cid"], status="not run")); continue
    out = p.read_text(); decls, errors = parse(out, set(a["added"]) | {a["site_decl"]})
    pre_fold_errors = [e for e in errors if "#fold" not in e]
    keys = analogue_keys(a["analogues"])
    site = a["site_decl"]
    site_key = next((d for d in decls if d == site or d == "HarnessProbe." + site), None)
    site_present = site_key is not None or any(re.search(r"#fold_decl (HarnessProbe\.)?" + re.escape(site) + r" : type", l) for l in out.splitlines())
    site_folds = decls.get(site_key, []) if site_key else []
    def matches(k, name):
        """A qualified key must match the constant's full name (or a suffix of it at a dot); a bare key matches the last component. Folds into the harness's own copy never count."""
        if name.startswith("HarnessProbe."): return False
        if "." in k: return name == k or name.endswith("." + k)
        return name.split(".")[-1] == k
    def hit(f): return any(matches(k, f["const"]) or matches(k, f["via"]) or (("." in k) and (k in f["fold"] or (f["fn"] and k in f["fn"]))) for k in keys)
    hits = [f for f in site_folds if hit(f)]
    other = {d: fs for d, fs in decls.items() if d != site}
    rows.append(dict(cid=a["cid"], sample=a["sample"], pr=a["pr"], findable=a["findable"], month=a["month"], site=site,
                     compiled=not pre_fold_errors, site_present=site_present, n_errors=len(errors), site_folds=len(site_folds), site_naming=len(naming), hit=bool(hits), hit_naming=bool(hits_naming),
                     hit_consts=sorted({f["const"] for f in hits}), site_consts=sorted({f["const"] for f in site_folds})[:12],
                     analogue_keys=sorted(keys), other_decls=max(0, len([d for d in decls if d != site_key])), other_folds=sum(len(v) for v in other.values()), other_naming=other_naming,
                     other_decls_with_folds=sum(1 for v in other.values() if v)))
json.dump(rows, open(H / "scores.json", "w"), indent=1, ensure_ascii=False)
run = [r for r in rows if r.get("status") != "not run"]
comp = [r for r in run if r["site_present"]]
print(f"run {len(run)} clean-compile {sum(1 for r in run if r['compiled'])} site-present {len(comp)}  site folds>0: {sum(1 for r in comp if r['site_folds'])} (naming tier: {sum(1 for r in comp if r['site_naming'])})  analogue hit: {sum(1 for r in comp if r['hit'])} (naming tier: {sum(1 for r in comp if r['hit_naming'])})")
for fb, grp in sorted(defaultdict(list, {tuple(r["findable"]): [x for x in comp if x["findable"] == r["findable"]] for r in comp}).items()):
    print(f"  {fb}: n={len(grp)} site_folds>0={sum(1 for r in grp if r['site_folds'])} hit={sum(1 for r in grp if r['hit'])}")
od = sum(r["other_decls"] for r in comp); of = sum(r["other_folds"] for r in comp); odf = sum(r["other_decls_with_folds"] for r in comp); on = sum(r["other_naming"] for r in comp)
print(f"noise: {od} other added declarations, {odf} with at least one fold ({odf/od:.2f}), {of} folds in all ({of/od:.2f} per declaration), naming tier {on} ({on/od:.2f} per declaration)" if od else "noise: n/a")
print("--- per ask ---")
for r in run: print(f"{r['cid']} {r.get('sample','')} {r.get('findable')} present={r.get('site_present')} site_folds={r.get('site_folds')}/{r.get('site_naming')} hit={r.get('hit')}/{r.get('hit_naming')} {r.get('hit_consts') or r.get('site_consts')} keys={r.get('analogue_keys')}")
