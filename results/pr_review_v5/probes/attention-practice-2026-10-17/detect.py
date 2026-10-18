"""Exact detectors for six rules a script can check, and a linter-enforced control, on a Lean file's text.

Each detector takes the file's lines (0-based list) and the set of 1-based line numbers to look at (the lines a
PR added, or every line), and returns (opportunities, departures): an opportunity is a construct the rule speaks
about; a departure is one that breaks the rule's literal check (stage G's `rules.json`). Each departure is a dict
with the rule, its 1-based line span, the enclosing declaration's written name (or None) and a `key` that
locates the same construct again in another version of the file.

Rules (texts in `conventions-ceiling-2026-10-04/rules.json`):
- P084J  a two-line signature (header, one continuation ending `:=` or `:= by`) whose join fits in 100 characters;
- P097   tactics joined by `;` at bracket depth 0 (not `<;>`), in a theorem or lemma body;
- P341   a new `theorem` with no `/-- ... -/` docstring above it and its attributes;
- P012   a `namespace`, `section`, `end` or `variable` command with a non-blank line directly above or below;
- P240   a theorem or lemma whose statement spans several lines and whose term proof follows `:=` on the last;
- P392   a named binder `(h : C ...)` or `{h : C ...}` whose whole type is `C args`, `C` written unqualified and a
         class no definition or structure shares a name with (`classes_unambiguous.txt`), plus `Nonempty`,
         `Finite`, `Countable`, `Subsingleton`, whose namesakes are written with a dot (`s.Nonempty`);
- LONG   a line over 100 characters with no URL (Mathlib's long-line linter: the control).
"""
import re

KW = r"(?:theorem|lemma|def|abbrev|instance|structure|class|inductive)"
MODS = r"(?:(?:protected|private|noncomputable|nonrec|scoped|unsafe|partial)\s+)*"
HEADER = re.compile(r"^(?:@\[[^\]]*\]\s*)?" + MODS + r"(" + KW + r")\s+([^\s:({\[]+)")
TOP = re.compile(r"^(?:@\[|/--|/-|--|" + MODS + KW + r"\b|end\b|section\b|namespace\b|variable\b|open\b|universe\b|#|"
                 r"noncomputable\s+section\b|attribute\b|set_option\b|alias\b|export\b|initialize\b|macro\b|syntax\b|"
                 r"elab\b|notation\b|infix|prefix|postfix|scoped\b|local\b|deriving\b|example\b|termination_by\b)")
COMMAND = re.compile(r"^(?:namespace|section|end|variable|noncomputable\s+section)\b")
CLASS_DECL = re.compile(r"^(?:@\[[^\]]*\]\s*)?" + MODS + r"class\s+(?:inductive\s+)?([^\s:({\[]+)")
RULES = ("P084J", "P097", "P341", "P012", "P240", "P392", "LONG")
#: P097's rate is read per touched proof, not per line: `opp["P097_proofs"]` counts theorem/lemma bodies with an
#: added code line, `opp["P097_proofs_departing"]` those with at least one departure.


def declarations(lines):
    """[(kind, written name, header index, end index exclusive)] for every header at column 0."""
    out = []
    for i, line in enumerate(lines):
        m = HEADER.match(line)
        if not m:
            continue
        j = i + 1
        while j < len(lines) and not (lines[j][:1] not in (" ", "\t", "") and TOP.match(lines[j])):
            j += 1
        out.append((m.group(1), m.group(2), i, j))
    return out


def enclosing(decls, i):
    for kind, name, a, b in decls:
        if a <= i < b:
            return kind, name, a, b
    return None


def strip_code(line):
    """The line without its `--` comment and string literals (block comments are handled by the caller)."""
    out, k, in_str = [], 0, False
    while k < len(line):
        c = line[k]
        if in_str:
            if c == "\\":
                k += 2
                continue
            if c == '"':
                in_str = False
            k += 1
            continue
        if c == '"':
            in_str = True
        elif line.startswith("--", k):
            break
        else:
            out.append(c)
        k += 1
    return "".join(out)


def comment_mask(lines):
    """True for lines wholly inside a `/- ... -/` block comment or docstring."""
    mask, depth = [], 0
    for line in lines:
        start_depth = depth
        k = 0
        while k < len(line):
            if line.startswith("/-", k):
                depth += 1
                k += 2
            elif line.startswith("-/", k) and depth:
                depth -= 1
                k += 2
            else:
                k += 1
        mask.append(start_depth > 0 and depth > 0 or (start_depth > 0 and line.strip().endswith("-/")
                                                        and "/-" not in line))
    return mask


def depth0_assign(code, depth):
    """(column of the first `:=` at bracket depth 0 or None, depth after the line)."""
    hit = None
    for q, ch in enumerate(code):
        if ch in "([{⟨":
            depth += 1
        elif ch in ")]}⟩":
            depth -= 1
        elif ch == ":" and code[q + 1:q + 2] == "=" and depth <= 0 and hit is None:
            hit = q
    return hit, depth


def signature_end(lines, a, b):
    """Index of the line where the signature ends: the first `:=` at bracket depth 0 (named arguments such as
    `(E := ...)` do not count), a trailing `where`, or a match arm; else None."""
    depth = 0
    for k in range(a, b):
        code = strip_code(lines[k])
        hit, depth_after = depth0_assign(code, depth)
        if hit is not None or (depth <= 0 and re.search(r"\bwhere\s*$", code)) or (k > a and depth <= 0 and code.lstrip().startswith("|")):
            return k
        depth = depth_after
    return None


def after_assign(code):
    """The text after the first depth-0 `:=` on a signature's last line ('' if none)."""
    hit, _ = depth0_assign(code, 0)
    return code[hit + 2:] if hit is not None else ""


def detect(lines, look, classes=frozenset()):
    """Opportunities and departures for every rule, restricted to constructs on lines in `look` (1-based)."""
    decls = declarations(lines)
    mask = comment_mask(lines)
    opp = {r: 0 for r in RULES}
    opp["P097_proofs"] = opp["P097_proofs_departing"] = 0
    dep = []

    def add(rule, lo, hi, decl, key):
        dep.append({"rule": rule, "lines": [lo + 1, hi + 1], "decl": decl[1] if decl else None,
                    "decl_span": [decl[2] + 1, decl[3]] if decl else None, "key": key})

    for kind, name, a, b in decls:
        s = signature_end(lines, a, b)
        header_added = a + 1 in look
        # P084J: header line, then exactly one continuation that ends the signature with `:=` / `:= by`
        if header_added and s == a + 1 and depth0_assign(strip_code(lines[a]), 0)[0] is None and lines[a + 1].startswith("    ") \
                and re.search(r":=\s*(by)?\s*$", strip_code(lines[a + 1]).rstrip()) and (a + 2) in look:
            opp["P084J"] += 1
            if len(lines[a].rstrip()) + 1 + len(lines[a + 1].strip()) <= 100:
                add("P084J", a, a + 1, (kind, name, a, b), ("P084J", name))
        # P341: a theorem header with no docstring above it and its attribute lines
        if header_added and kind == "theorem" and re.match(r"^(?:@\[[^\]]*\]\s*)?" + MODS + r"theorem\b", lines[a]):
            opp["P341"] += 1
            k = a - 1
            while k >= 0 and (lines[k].startswith("@[") or (lines[k].startswith("  ") and k > 0 and lines[k - 1].startswith("@["))):
                k -= 1
            ok = False
            if k >= 0 and lines[k].rstrip().endswith("-/"):
                t = k
                while t >= 0 and "/-" not in lines[t]:
                    t -= 1
                ok = t >= 0 and "/--" in lines[t]
            if not ok:
                add("P341", a, a, (kind, name, a, b), ("P341", name))
        # P240: theorem/lemma, statement over several lines, a term proof after `:=` on the statement's last line
        if header_added and kind in ("theorem", "lemma") and s is not None and s > a:
            code = strip_code(lines[s])
            if depth0_assign(code, 0)[0] is not None:
                after = after_assign(code).strip()
                if after == "":
                    nxt = lines[s + 1].strip() if s + 1 < b else ""
                    if nxt and not nxt.startswith("by"):
                        opp["P240"] += 1
                elif not after.startswith("by"):
                    opp["P240"] += 1
                    add("P240", a, s, (kind, name, a, b), ("P240", name))
        # P392: named binders whose type's head is a declared class, in the signature lines
        if header_added and s is not None:
            sig = " ".join(strip_code(lines[k]) for k in range(a, s + 1))
            # a binder whose whole type is `C args`: simple arguments or parenthesised groups, nothing else
            for m in re.finditer(r"([({])\s*([^\s:(){}\[\]]+(?:\s+[^\s:(){}\[\]]+)*)\s*:\s*@?([A-Z][\w.']*)"
                                 r"((?:\s+[^\s(){}\[\]→↔≃=<>≤≥∈∉⊆×]+|\s*\([^()]*\))*)\s*[)}]", sig):
                head = m.group(3)
                leaf = head.rsplit(".", 1)[-1]
                if "." not in head and len(head) > 1 and head in classes:
                    opp["P392"] += 1
                    add("P392", a, s, (kind, name, a, b), ("P392", name, m.group(2), head))
            opp["P392"] += len(re.findall(r"\[[^\]]*\]", sig))
        # P097: `;` at bracket depth 0 in a theorem/lemma body, not `<;>`
        if kind in ("theorem", "lemma") and s is not None:
            touched = departing = False
            for k in range(s, b):
                if k + 1 not in look or mask[k]:
                    continue
                code = strip_code(lines[k])
                if k == s:
                    code = after_assign(code)
                if not code.strip():
                    continue
                opp["P097"] += 1
                touched = True
                depth, hit = 0, False
                for q, ch in enumerate(code):
                    if ch in "([{⟨":
                        depth += 1
                    elif ch in ")]}⟩":
                        depth -= 1
                    elif ch == ";" and depth <= 0 and code[q - 1:q] != "<" and code[q + 1:q + 2] != ">":
                        hit = True
                if hit:
                    departing = True
                    add("P097", k, k, (kind, name, a, b), ("P097", name, " ".join(code.split())))
            opp["P097_proofs"] += touched
            opp["P097_proofs_departing"] += departing
    for i, line in enumerate(lines):
        if i + 1 not in look:
            continue
        # LONG: the control
        opp["LONG"] += 1
        if len(line.rstrip("\n")) > 100 and "http" not in line:
            add("LONG", i, i, enclosing(decls, i), ("LONG", " ".join(line.split())))
        # P012: blank line around namespace/section/end/variable (multi-line `variable` spans its indented lines)
        if COMMAND.match(line) and not re.search(r"\bin\s*$", strip_code(line)):
            j = i
            while j + 1 < len(lines) and lines[j + 1].startswith((" ", "\t")) and lines[j + 1].strip():
                j += 1
            opp["P012"] += 1
            above = lines[i - 1].strip() if i > 0 else ""
            below = lines[j + 1].strip() if j + 1 < len(lines) else ""
            if above or below:
                add("P012", i, j, None, ("P012", " ".join(line.split()), above[:40], below[:40]))
    return opp, dep


def class_names(lines):
    return {m.group(1).rsplit(".", 1)[-1] for line in lines for m in [CLASS_DECL.match(line)] if m}
