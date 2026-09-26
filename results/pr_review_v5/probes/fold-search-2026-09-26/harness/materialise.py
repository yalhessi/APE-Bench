"""File-level harness for the fold search. For each labelled comparison ask (readers agreed on a
comparison kind; findable other than pr_internal), the PR's file at the commit the comment was
made on, with `import Fold` and a `#fold_decl` for EVERY declaration the PR added to that file,
so the ask site and the non-ask declarations are both measured. Writes harness/<cid>.lean and
harness/index.json. Compiles nothing."""
import json, glob, re, subprocess, sys
from pathlib import Path
from collections import Counter
from src.datasets.pull_requests.store import PullRequestStore
S = Path("/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/b9848b08-eb04-43a7-9e77-0f87417755b6/scratchpad")
R = Path("results/pr_review_v5/adjudications"); CLONE = "data/code_execute/repos/mathlib4/source"
H = S / "fold/harness2"
def readers(d, pattern):
    out = {}
    for f in sorted(glob.glob(str(d / pattern))):
        r = Path(f).name.split(".")[0].split("_")[1]
        for l in open(f):
            if l.strip(): x = json.loads(l); out.setdefault(x["cid"], {})[r] = x
    return out
asks = []
rv = readers(R / "design-comparison-val1000-v1", "reader_[AB].jsonl")
ev = {r["cid"]: r for r in json.load(open(S / "v2/val1000_feedback.json"))["rows"]}
for c, rr in rv.items():
    if rr["A"].get("group") == "B":
        asks.append(dict(cid=c, sample="val", pr=ev[c]["pr"], path=ev[c]["path"], gh_id=ev[c]["gh_id"], kind=ev[c]["kind"],
                         analogues=[rr["A"]["analogue"], rr["B"]["analogue"]], findable=sorted({rr["A"]["findable_by"], rr["B"]["findable_by"]})))
for tag, fb in (("b", S / "wide/outside_feedback.json"), ("w", S / "wide/outside_window_feedback.json")):
    ro = readers(R / "design-comparison-outside-v1", f"reader_[BC].{tag}*.jsonl")
    rows = {r["cid"]: r for r in json.load(open(fb))["rows"]}
    for c, rr in ro.items():
        if len(rr) == 2 and all(x.get("ask_kind") in ("design_library", "design_siblings") for x in rr.values()):
            asks.append(dict(cid=c, sample="outside." + tag, pr=rows[c]["pr"], path=rows[c]["path"], gh_id=rows[c]["gh_id"], kind=rows[c]["kind"],
                             analogues=[x.get("analogue", "") for x in rr.values()], findable=sorted({x.get("findable_by") for x in rr.values()} - {None})))
store = PullRequestStore()
DECL = re.compile(r"^\s*(?:@\[[^\]]*\]\s*)?(?:(?:protected|private|noncomputable|nonrec|public|scoped)\s+)*(theorem|lemma|def|abbrev|instance|structure|class|inductive)\s+([^\s(\[{⦃:]+)")
def added_decls(base, commit, path):
    diff = subprocess.run(["git", "-C", CLONE, "diff", f"{base}..{commit}", "--", path], capture_output=True, text=True).stdout
    return {m.group(2) for l in diff.splitlines() if l.startswith("+") for m in [DECL.match(l[1:])] if m}
def qualified(lines):
    """line index -> (declaration name qualified by the enclosing namespaces, line) for each declaration."""
    stack, out = [], {}
    for i, l in enumerate(lines):
        m = re.match(r"^namespace\s+(\S+)", l)
        if m: stack.append(m.group(1)); continue
        m = re.match(r"^end\s+(\S+)", l)
        if m and stack and stack[-1] == m.group(1): stack.pop(); continue
        m = DECL.match(l)
        if m:
            name = m.group(2)
            full = name[len("_root_."):] if name.startswith("_root_.") else ".".join(stack + [name]) if stack else name
            out[i] = (m.group(1), name, full)
    return out
import datetime as dt
WS = Path("data/code_execute/repos/mathlib4/workspaces")
bases = {}
for d in WS.iterdir():
    if re.fullmatch(r"[0-9a-f]{40}", d.name) and (d / "lean-toolchain").exists():
        r = subprocess.run(["git", "-C", CLONE, "log", "-1", "--format=%cI", d.name], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            bases[d.name] = (r.stdout.strip(), (d / "lean-toolchain").read_text().strip())
print("built bases with dates:", len(bases))
def norm(t): return dt.datetime.fromisoformat(t.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
def pick_base(created, review_at):
    """The latest built base dated at or before the review comment (the library the maintainer saw),
    and not more than 90 days before the PR was opened."""
    if not review_at: return None
    lo = norm(created) - dt.timedelta(days=90); hi = norm(review_at)
    cands = [(norm(date), sha, tc) for sha, (date, tc) in bases.items() if lo <= norm(date) <= hi]
    if not cands: return None
    d, sha, tc = max(cands); return (d.isoformat(), sha, tc)
index, skipped = [], Counter()
for a in asks:
    if a["findable"] == ["pr_internal"] or not a["path"] or a["kind"] != "review_comment":
        skipped["pr_internal or no site"] += 1; continue
    b = store.load_bundle(a["pr"])
    rc = next((c for c in b.get("review_comments") or [] if c.get("id") == a["gh_id"]), None)
    if not rc: skipped["comment not found"] += 1; continue
    commit = rc.get("original_commit_id") or rc.get("commit_id"); line = rc.get("original_line") or rc.get("line")
    if subprocess.run(["git", "-C", CLONE, "cat-file", "-e", f"{commit}^{{commit}}"], capture_output=True).returncode != 0:
        r = subprocess.run(["git", "-C", CLONE, "fetch", "--quiet", "origin", commit], capture_output=True, text=True, timeout=300)
        if r.returncode != 0: skipped["fetch failed"] += 1; continue
    text = subprocess.run(["git", "-C", CLONE, "show", f"{commit}:{a['path']}"], capture_output=True, text=True).stdout
    if not text: skipped["file not at commit"] += 1; continue
    base = subprocess.run(["git", "-C", CLONE, "merge-base", "origin/master", commit], capture_output=True, text=True).stdout.strip()
    if not base: skipped["no merge base"] += 1; continue
    pr = b["pr"]; chosen = pick_base(pr.get("created_at") or "", rc.get("created_at") or "")
    if not chosen: skipped["no built base at or before the review"] += 1; continue
    added = added_decls(base, commit, a["path"])
    lines = text.splitlines(); decls = qualified(lines)
    added_full = [(i, k, n, f) for i, (k, n, f) in decls.items() if n in added and k in ("theorem", "lemma", "def", "abbrev")]
    if not added_full: skipped["no added declaration found"] += 1; continue
    # the declaration the comment sits in: the last declaration starting at or before the comment line
    site = max((i for i in decls if line and i + 1 <= line), default=None)
    site_full = decls[site][2] if site is not None else None
    # insert the import after the header (module + public imports), append fold commands
    j = 0
    while j < len(lines) and (lines[j].startswith("import ") or lines[j].startswith("public import ") or lines[j].strip() in ("module", "") or lines[j].startswith("/-") or lines[j].startswith("-/") or lines[j].startswith("Copyright") or lines[j].startswith("Released") or lines[j].startswith("Authors") or lines[j].startswith("Author")): j += 1
    last_import = max((i for i in range(j) if lines[i].startswith("import ") or lines[i].startswith("public import ")), default=None)
    if last_import is None: skipped["no import line"] += 1; continue
    # the whole library at the chosen base, and the file's own declarations under a fresh namespace
    # so they never clash with the base's copy of this module
    ismod = any(l.strip() == "module" for l in lines[:12])
    out = lines[:last_import + 1] + [("public import Mathlib" if ismod else "import Mathlib"), "import Fold"]
    rest = lines[last_import + 1:]
    # keep a leading module docstring / `@[expose] public section` prologue outside the namespace? no: inside is fine
    out += ["", "set_option maxHeartbeats 4000000", "", "namespace HarnessProbe", ""] + rest
    out += ["", "set_option maxHeartbeats 4000000", ""]
    for i, k, n, f in sorted(added_full):
        out.append(f"#fold_decl HarnessProbe.{f}   -- line {i + 1}{'  SITE' if f == site_full else ''}")
    out += ["", "end HarnessProbe"]
    fn = H / f"{a['cid']}.lean"; fn.write_text("\n".join(out) + "\n")
    index.append(dict(a, commit=commit, base=base, line=line, site_decl=site_full, added=[f for _, _, _, f in sorted(added_full)], file=str(fn), month=(b["pr"].get("created_at") or "")[:7],
                      workspace=str(WS / chosen[1]), workspace_date=chosen[0][:10], toolchain=chosen[2], review_at=(rc.get("created_at") or "")[:10], is_module=lines[0:8].count("module") > 0 or any(l.strip() == "module" for l in lines[:12])))
json.dump(index, open(H / "index.json", "w"), indent=1, ensure_ascii=False)
print("asks", len(asks), "materialised", len(index), "skipped", dict(skipped))
print("by sample:", Counter(x["sample"] for x in index), "site decl found:", sum(1 for x in index if x["site_decl"]), "added decls total:", sum(len(x["added"]) for x in index))
print("months:", dict(sorted(Counter(x["month"] for x in index).items())))
print("toolchains:", Counter(x["toolchain"] for x in index), "module files:", sum(1 for x in index if x["is_module"]))
print("base gap (days from base to review, binned by 30):", sorted(Counter((dt.date.fromisoformat(x["review_at"]) - dt.date.fromisoformat(x["workspace_date"])).days // 30 * 30 for x in index).items()))
