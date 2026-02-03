import re
import aiofiles
import asyncio
from typing import List, Optional, Tuple, Dict, Any, Sequence, Set
from pydantic import BaseModel, Field
from bisect import bisect_left, bisect_right
from pathlib import Path

# -----------------------------
# Data models
# -----------------------------
class ProofBlock(BaseModel):
    """Proof block from a declaration body."""
    type: str  # "rhs" | "where" | "termination_by" | "decreasing_by" | "equations"
    span: Tuple[int, int]
    text: str

class Decl(BaseModel):
    kind: str  # def | lemma | theorem | example | instance | abbrev
    name: Optional[str]
    fullname: Optional[str] = None
    name_span: Optional[Tuple[int, int]] = None  # absolute span of name in source
    variables: List[str] = Field(default_factory=list)
    header_span: Tuple[int, int]
    body_span: Tuple[int, int]
    blocks: List[ProofBlock]

# -----------------------------
# Masking and scanning
# -----------------------------

# double-quoted strings with escapes (multiline allowed)
_STR_RE = re.compile(r'"(?:\\.|[^"\\])*"', re.S)
# char literal with escapes
_CHAR_RE = re.compile(r"'(?:\\.|[^'\\])'", re.S)
# line comments
_LINECMT_RE = re.compile(r"--[^\n]*")
# guillemet identifiers « … »
_GUILLEMETS_RE = re.compile(r"«[^»]*»", re.S)

def mask_noncode_regions(src: str) -> str:
    s = src
    for patt in (_STR_RE, _CHAR_RE, _GUILLEMETS_RE):
        s = patt.sub(lambda m: " " * (m.end() - m.start()), s)

    s = _mask_nested_block_comments(s)

    s = _LINECMT_RE.sub(lambda m: " " * (m.end() - m.start()), s)

    return s

def _mask_nested_block_comments(s: str) -> str:
    """Properly handle nested block comments /- ... -/ using balanced matching."""
    result = []
    i = 0
    while i < len(s):
        if i + 1 < len(s) and s[i:i+2] == '/-':
            comment_start = i
            depth = 1
            j = i + 2
            while j < len(s) - 1 and depth > 0:
                if s[j:j+2] == '/-':
                    depth += 1
                    j += 2
                elif s[j:j+2] == '-/':
                    depth -= 1
                    j += 2
                else:
                    j += 1
            
            if depth == 0:
                comment_text = s[comment_start:j]
                masked_comment = ''.join(' ' if c != '\n' else '\n' for c in comment_text)
                result.append(masked_comment)
                i = j
            else:
                result.append(s[i])
                i += 1
        else:
            result.append(s[i])
            i += 1
    
    return ''.join(result)

# -----------------------------
# Top-level index
# -----------------------------
_LINE_START = r"^[ \t]*"
_ATTRS = r"(?:\@\[[^\]]*\]\s*)*"
_MODIFIERS = (
    r"(?:(?:private|public|noncomputable|unsafe|protected|local|meta|partial|nonrec|"
    r"scoped(?:\[[^\]]*\])?)\s+)*"
)
_PRIORITY = r"(?:\(priority\s*:=\s*[^)]+\)\s+)*"

_DECL_KEYWORDS = (
    "def|theorem|lemma|example|instance|abbrev|axiom|structure|class|inductive"
)
_CMD_KEYWORDS = (
    "def|theorem|lemma|example|instance|abbrev"
    "|structure|class|inductive|mutual"
    "|namespace|section|end"
    "|attribute|notation|macro"
    "|syntax|macro_rules|elab_rules|elab|declare_syntax_cat"
    "|infix|prefix|postfix"
    "|axiom|constant|opaque|theory|variable|variables"
    "|initialize|run_cmd"
    "|open|export|set_option|universe"
    "|alias|deriving|library_note"
)
_DERIVING_ATTACH_KINDS = {"def", "abbrev", "axiom", "structure", "class", "inductive"}

_CMD_PREFIX = rf"{_LINE_START}{_ATTRS}{_MODIFIERS}{_PRIORITY}"

DECL_START_RE = re.compile(
    rf"(?mx){_CMD_PREFIX}(?P<kw>{_DECL_KEYWORDS})\b"
)

CMD_START_RE = re.compile(
    rf"(?mx)(?:{_CMD_PREFIX}(?:{_CMD_KEYWORDS})\b|{_LINE_START}(?:/--|/-!|/-|\#))"
)
_CMD_START_INLINE_RE = re.compile(
    rf"(?x)^{_ATTRS}{_MODIFIERS}{_PRIORITY}(?P<kw>{_CMD_KEYWORDS})\b"
)

# keywords that can appear after a primary RHS and are still part of the same decl
TRAILING_BLOCKS = ("termination_by", "decreasing_by")

_CMD_PREFIX_RE = re.compile(rf"(?x){_CMD_PREFIX}")
_DOCSTRING_START_RE = re.compile(r"(?m)^/--|^/-!")
_OPEN_IN_RE = re.compile(r"^\s*open(?:\s+scoped)?\b")
_IN_WORD_RE = re.compile(r"\bin\b")
_NAMESPACE_OPEN_RE = re.compile(r"^namespace\s+([A-Za-z0-9_'.]+)")
_SECTION_OPEN_RE = re.compile(r"^section(?:\s+([A-Za-z0-9_'.]+))?")
_END_RE = re.compile(r"^end(?:\s+([A-Za-z0-9_'.]+))?")

OPEN_TO_CLOSE = {
    '(': ')', '[': ']', '{': '}', '⟨': '⟩'
}
CLOSE_TO_OPEN = {v: k for k, v in OPEN_TO_CLOSE.items()}

def is_word_boundary(ch: str) -> bool:
    return not (ch.isalnum() or ch == '_' or ch == '\'')

def word_at(mask: str, i: int, word: str) -> bool:
    n = len(word)
    if i < 0 or i + n > len(mask):
        return False
    if mask[i:i + n] != word:
        return False
    prev = mask[i - 1] if i > 0 else ' '
    nxt = mask[i + n] if i + n < len(mask) else ' '
    return is_word_boundary(prev) and is_word_boundary(nxt)

def _starts_with_command(segment: str) -> bool:
    return bool(_CMD_START_INLINE_RE.match(segment))

def _is_open_in_expr_line(
    src: str,
    mask: str,
    line_start: int,
    line_end: int,
    line_starts: List[int],
    line_ends: List[int],
) -> bool:
    line = src[line_start:line_end]
    if not _OPEN_IN_RE.match(line):
        return False
    if not _IN_WORD_RE.search(line):
        return False

    in_match = _IN_WORD_RE.search(line)
    after_in = line[in_match.end():] if in_match else ""
    if after_in.strip():
        return not _starts_with_command(after_in)

    line_idx = bisect_right(line_starts, line_start) - 1
    for j in range(line_idx + 1, len(line_starts)):
        nxt_ls = line_starts[j]
        nxt_mask = mask[nxt_ls:line_ends[j]]
        if not nxt_mask.strip():
            continue
        nxt_line = src[nxt_ls:line_ends[j]]
        return not _starts_with_command(nxt_line)
    return False

class _TopLevelIndex:
    """Holds precomputed top-level positions for fast queries."""

    def __init__(self,
                 mask: str,
                 src: str,
                 line_starts: List[int],
                 line_ends: List[int],
                 depth_at_line_start: List[int],
                 cmd_positions: List[int],
                 decl_matches: List[re.Match],
                 token_positions: Dict[str, List[int]],
                 pattern_line_starts: List[int]):
        self.mask = mask
        self.src = src
        self.line_starts = line_starts
        self.line_ends = line_ends
        self.depth_at_line_start = depth_at_line_start
        self.cmd_positions = cmd_positions
        self.decl_matches = decl_matches
        self.token_positions = token_positions
        self.pattern_line_starts = pattern_line_starts

    def find_next_cmd_after(self, pos: int) -> int:
        i = bisect_left(self.cmd_positions, pos + 1)
        return self.cmd_positions[i] if i < len(self.cmd_positions) else len(self.src)

    def first_token_in_range(
        self,
        start: int,
        end: int,
        tokens_in_priority: Sequence[str],
    ) -> Optional[Tuple[str, int]]:
        best_token = None
        best_pos = None
        for t in tokens_in_priority:
            arr = self.token_positions.get(t)
            if not arr:
                continue
            j = bisect_left(arr, start)
            if j < len(arr):
                p = arr[j]
                if p < end:
                    if best_pos is None or p < best_pos:
                        best_pos = p
                        best_token = t
        if best_token is None:
            return None
        return (best_token, best_pos)  # type: ignore

    def next_token_after(self, start: int, end: int, tokens: Sequence[str]) -> Optional[Tuple[str, int]]:
        best_token = None
        best_pos = None
        for t in tokens:
            arr = self.token_positions.get(t)
            if not arr:
                continue
            j = bisect_left(arr, start)
            if j < len(arr):
                p = arr[j]
                if p < end:
                    if best_pos is None or p < best_pos:
                        best_pos = p
                        best_token = t
        if best_token is None:
            return None
        return (best_token, best_pos)  # type: ignore

def _build_top_level_index(src: str) -> _TopLevelIndex:
    """Precompute a fast index for parsing at bracket-depth 0.

    - Computes comment/string-masked text
    - Tracks bracket depth at each line start
    - Collects all command starts and declaration starts at depth 0
    - Collects top-level tokens positions for ":=", "where", trailing blocks
    - Collects candidate pattern-matching line starts ("| ... => ...")
    """
    mask = mask_noncode_regions(src)

    line_starts: List[int] = [0]
    depth_at_line_start: List[int] = [0]
    depth = 0
    for i, ch in enumerate(mask):
        if ch in OPEN_TO_CLOSE:
            depth += 1
        elif ch in CLOSE_TO_OPEN:
            if depth > 0:
                depth -= 1
        if ch == '\n':
            line_starts.append(i + 1)
            depth_at_line_start.append(depth)
    line_ends: List[int] = []
    for idx, ls in enumerate(line_starts):
        if idx + 1 < len(line_starts):
            line_ends.append(line_starts[idx + 1] - 1)
        else:
            line_ends.append(len(mask))

    line_start_to_depth: Dict[int, int] = {ls: d for ls, d in zip(line_starts, depth_at_line_start)}

    cmd_positions_set: set[int] = set()
    for m in CMD_START_RE.finditer(mask):
        ls = m.start()
        if line_start_to_depth.get(ls, 999) == 0:
            line_end = src.find("\n", ls)
            if line_end == -1:
                line_end = len(src)
            if not _is_open_in_expr_line(src, mask, ls, line_end, line_starts, line_ends):
                cmd_positions_set.add(ls)
    for m in _DOCSTRING_START_RE.finditer(src):
        ls = m.start()
        if line_start_to_depth.get(ls, 999) == 0:
            cmd_positions_set.add(ls)
    cmd_positions = sorted(cmd_positions_set)

    decl_matches: List[re.Match] = []
    for m in DECL_START_RE.finditer(mask):
        ls = m.start()
        if line_start_to_depth.get(ls, 999) == 0:
            decl_matches.append(m)

    token_positions: Dict[str, List[int]] = {":=": [], "where": [], "termination_by": [], "decreasing_by": []}
    depth = 0
    i = 0
    L = len(mask)
    while i < L:
        ch = mask[i]
        if ch in OPEN_TO_CLOSE:
            depth += 1
            i += 1
            continue
        if ch in CLOSE_TO_OPEN:
            if depth > 0:
                depth -= 1
            i += 1
            continue

        if depth == 0:
            if i + 1 < L and ch == ':' and mask[i + 1] == '=':
                token_positions[":="].append(i)
                i += 2
                continue
            if ch == 'w' and i + 5 <= L and word_at(mask, i, "where"):
                token_positions["where"].append(i)
                i += 5
                continue
            if ch == 't' and i + 13 <= L and word_at(mask, i, "termination_by"):
                token_positions["termination_by"].append(i)
                i += 13
                continue
            if ch == 'd' and i + 12 <= L and word_at(mask, i, "decreasing_by"):
                token_positions["decreasing_by"].append(i)
                i += 12
                continue
        i += 1

    pattern_line_starts: List[int] = []
    for ls, le in zip(line_starts, line_ends):
        segment = mask[ls:le]
        stripped = segment.lstrip(' \t')
        if stripped.startswith('|') and '=>' in segment:
            pattern_line_starts.append(ls)

    return _TopLevelIndex(
        mask=mask,
        src=src,
        line_starts=line_starts,
        line_ends=line_ends,
        depth_at_line_start=depth_at_line_start,
        cmd_positions=cmd_positions,
        decl_matches=decl_matches,
        token_positions=token_positions,
        pattern_line_starts=pattern_line_starts,
    )

# -----------------------------
# Namespace and section scopes
# -----------------------------
def _line_end_for_pos(idx: _TopLevelIndex, pos: int) -> int:
    line_idx = bisect_right(idx.line_starts, pos) - 1
    if line_idx < 0:
        return pos
    return idx.line_ends[line_idx]

def _strip_cmd_prefix(segment: str) -> Tuple[str, int]:
    match = _CMD_PREFIX_RE.match(segment)
    offset = match.end() if match else 0
    stripped = segment[offset:]
    lstrip_len = len(stripped) - len(stripped.lstrip())
    offset += lstrip_len
    return stripped.lstrip(), offset

def _parse_block_command(idx: _TopLevelIndex, pos: int) -> Optional[Tuple[str, Optional[str]]]:
    line_end = _line_end_for_pos(idx, pos)
    segment = idx.mask[pos:line_end]
    segment, _ = _strip_cmd_prefix(segment)
    if m := _NAMESPACE_OPEN_RE.match(segment):
        return ("namespace", m.group(1))
    if m := _SECTION_OPEN_RE.match(segment):
        return ("section", m.group(1))
    if m := _END_RE.match(segment):
        return ("end", m.group(1))
    return None

def _deriving_command_kind(idx: _TopLevelIndex, pos: int) -> Optional[str]:
    line_end = _line_end_for_pos(idx, pos)
    segment = idx.mask[pos:line_end]
    segment, _ = _strip_cmd_prefix(segment)
    if not segment.startswith("deriving"):
        return None
    tail = segment[len("deriving"):].lstrip()
    if tail.startswith("instance"):
        return "instance"
    return "plain"

def _find_decl_end(idx: _TopLevelIndex, start: int, kind: str) -> int:
    end = idx.find_next_cmd_after(start)
    if kind not in _DERIVING_ATTACH_KINDS:
        return end
    while end < len(idx.src) and _deriving_command_kind(idx, end) == "plain":
        end = idx.find_next_cmd_after(end)
    return end

def _build_fullname(namespace_components: List[str], name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    if name.startswith("_root_."):
        return name[len("_root_."):]
    if not namespace_components:
        return name
    ns_prefix = ".".join(namespace_components)
    if name.startswith(ns_prefix + "."):
        return name
    return f"{ns_prefix}.{name}"

def _compute_namespace_map(idx: _TopLevelIndex) -> Dict[int, List[str]]:
    decl_positions = {m.start() for m in idx.decl_matches}
    namespace_components: List[str] = []
    block_stack: List[Dict[str, Any]] = []
    decl_namespaces: Dict[int, List[str]] = {}

    def _pop_namespace(count: int) -> None:
        for _ in range(count):
            if namespace_components:
                namespace_components.pop()

    def _pop_block() -> None:
        if not block_stack:
            return
        blk = block_stack.pop()
        if blk["kind"] == "namespace":
            _pop_namespace(len(blk["components"]))

    def _pop_until_name(name: str) -> None:
        while block_stack:
            blk = block_stack.pop()
            if blk["kind"] == "namespace":
                _pop_namespace(len(blk["components"]))
            if blk["name"] == name:
                break

    def _pop_by_components(components: List[str]) -> None:
        remaining = len(components)
        while block_stack and remaining > 0:
            blk = block_stack.pop()
            if blk["kind"] == "namespace":
                _pop_namespace(len(blk["components"]))
                remaining -= len(blk["components"])

    for pos in idx.cmd_positions:
        if pos in decl_positions:
            decl_namespaces[pos] = list(namespace_components)

        cmd = _parse_block_command(idx, pos)
        if not cmd:
            continue
        cmd_type, cmd_name = cmd
        if cmd_type == "namespace" and cmd_name:
            components = cmd_name.split(".")
            for comp in components:
                namespace_components.append(comp)
                block_stack.append({
                    "kind": "namespace",
                    "name": comp,
                    "components": [comp]
                })
        elif cmd_type == "section":
            block_stack.append({
                "kind": "section",
                "name": cmd_name or "",
                "components": []
            })
        elif cmd_type == "end":
            if not block_stack:
                continue
            if cmd_name:
                components = cmd_name.split(".")
                if len(components) > 1 and namespace_components[-len(components):] == components:
                    _pop_by_components(components)
                else:
                    _pop_until_name(components[-1])
            else:
                _pop_block()

    return decl_namespaces

# -----------------------------
# Variable scopes
# -----------------------------
def _normalize_variable_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())

def _extract_variable_binders(src: str, mask: str, start: int, end: int) -> List[str]:
    """Extract binder groups like (x : T) [Group T] {y : T} from a variable command."""
    binders: List[str] = []
    i = start
    open_to_close = {k: v for k, v in OPEN_TO_CLOSE.items() if k in "([{⟨"}

    while i < end:
        ch = mask[i]
        if ch.isspace():
            i += 1
            continue

        if ch in open_to_close:
            stack = [open_to_close[ch]]
            j = i + 1
            while j < end and stack:
                c = mask[j]
                if c in open_to_close:
                    stack.append(open_to_close[c])
                elif stack and c == stack[-1]:
                    stack.pop()
                j += 1

            if stack:
                break

            text = _normalize_variable_text(src[i:j])
            if text:
                binders.append(text)
            i = j
            continue

        j = i + 1
        while j < end and not mask[j].isspace():
            if mask[j] in open_to_close:
                break
            j += 1
        text = _normalize_variable_text(src[i:j])
        if text:
            binders.append(text)
        i = j

    return binders

def _parse_variable_command(idx: _TopLevelIndex, pos: int) -> Optional[Tuple[List[str], bool]]:
    line_end = _line_end_for_pos(idx, pos)
    segment = idx.mask[pos:line_end]
    segment, offset = _strip_cmd_prefix(segment)
    m = re.match(r"(variables|variable)\b", segment)
    if not m:
        return None

    kw_end = pos + offset + m.end(1)
    cmd_end = idx.find_next_cmd_after(pos)
    cmd_tail = idx.mask[kw_end:cmd_end]
    has_in = bool(re.search(r"\bin\s*$", cmd_tail.strip()))
    binders = _extract_variable_binders(idx.src, idx.mask, kw_end, cmd_end)
    if binders:
        binders = [b for b in binders if b.lower() != "in"]
    if binders:
        return (binders, has_in)

    tail = _normalize_variable_text(idx.src[kw_end:cmd_end])
    if tail.lower().endswith(" in"):
        tail = tail[:-3].rstrip()
    if tail:
        return ([tail], True)
    return None

def _compute_variables_map(idx: _TopLevelIndex) -> Dict[int, List[str]]:
    decl_positions = {m.start() for m in idx.decl_matches}
    namespace_components: List[str] = []
    block_stack: List[Dict[str, Any]] = []
    variables_stack: List[List[str]] = [[]]
    decl_variables: Dict[int, List[str]] = {}
    pending_locals: List[str] = []

    def _pop_namespace(count: int) -> None:
        for _ in range(count):
            if namespace_components:
                namespace_components.pop()

    def _pop_scopes(count: int) -> None:
        for _ in range(count):
            if len(variables_stack) > 1:
                variables_stack.pop()

    def _pop_block() -> None:
        if not block_stack:
            return
        blk = block_stack.pop()
        _pop_scopes(blk["scope_count"])
        if blk["kind"] == "namespace":
            _pop_namespace(len(blk["components"]))

    def _pop_until_name(name: str) -> None:
        while block_stack:
            blk = block_stack.pop()
            _pop_scopes(blk["scope_count"])
            if blk["kind"] == "namespace":
                _pop_namespace(len(blk["components"]))
            if blk["name"] == name:
                break

    def _pop_by_components(components: List[str]) -> None:
        remaining = len(components)
        while block_stack and remaining > 0:
            blk = block_stack.pop()
            _pop_scopes(blk["scope_count"])
            if blk["kind"] == "namespace":
                _pop_namespace(len(blk["components"]))
                remaining -= len(blk["components"])

    for pos in idx.cmd_positions:
        if pos in decl_positions:
            scoped_vars = [v for scope in variables_stack for v in scope]
            decl_variables[pos] = scoped_vars + pending_locals
            pending_locals = []
        elif pending_locals and not _DOCSTRING_START_RE.match(idx.src, pos):
            pending_locals = []

        cmd = _parse_block_command(idx, pos)
        if cmd:
            cmd_type, cmd_name = cmd
            if cmd_type == "namespace" and cmd_name:
                components = cmd_name.split(".")
                for comp in components:
                    namespace_components.append(comp)
                    block_stack.append({
                        "kind": "namespace",
                        "name": comp,
                        "components": [comp],
                        "scope_count": 1,
                    })
                    variables_stack.append([])
            elif cmd_type == "section":
                block_stack.append({
                    "kind": "section",
                    "name": cmd_name or "",
                    "components": [],
                    "scope_count": 1,
                })
                variables_stack.append([])
            elif cmd_type == "end":
                if not block_stack:
                    continue
                if cmd_name:
                    components = cmd_name.split(".")
                    if len(components) > 1 and namespace_components[-len(components):] == components:
                        _pop_by_components(components)
                    else:
                        _pop_until_name(components[-1])
                else:
                    _pop_block()

        vars_decl = _parse_variable_command(idx, pos)
        if vars_decl:
            binders, is_local = vars_decl
            if is_local:
                pending_locals = binders
            else:
                variables_stack[-1].extend(binders)

    return decl_variables

# -----------------------------
# Name extraction
# -----------------------------
def extract_name_with_span(kind: str, src: str, pos_kw: int) -> Tuple[Optional[str], Optional[Tuple[int, int]]]:
    """
    Extract declaration name and its absolute span in source.
    
    Returns:
        (name, span) where span is (start, end) absolute positions in src, or (None, None) if no name
    """
    tail = src[pos_kw:]
    
    if kind == "mutual":
        return (None, None)
    
    def _trim_universe_suffix(name: str, start: int, end: int) -> Tuple[str, Tuple[int, int]]:
        if name.endswith(".") and end < len(src) and src[end] == "{":
            return (name[:-1], (start, end - 1))
        return (name, (start, end))

    if kind == "instance":
        m = re.match(
            r"instance\s+([A-Za-z0-9_'.]+)\b(?:\s*(?:\([^)]*\)|\{[^}]*\}|\[[^\]]*\]))*\s*:",
            tail
        )
        if m:
            name = m.group(1)
            name_start = pos_kw + m.start(1)
            name_end = pos_kw + m.end(1)
            name, span = _trim_universe_suffix(name, name_start, name_end)
            return (name, span)
        return (None, None)
    else:
        m = re.match(rf"{kind}\s+([^:\s\(\{{\[]+)", tail)
        if m:
            name = m.group(1)
            if kind == "example":
                return (None, None)
            # Calculate absolute span
            name_start = pos_kw + m.start(1)
            name_end = pos_kw + m.end(1)
            name, span = _trim_universe_suffix(name, name_start, name_end)
            return (name, span)
        return (None, None)

def extract_name(kind: str, src: str, pos_kw: int) -> Optional[str]:
    """Legacy function for backward compatibility. Use extract_name_with_span for span info."""
    name, _ = extract_name_with_span(kind, src, pos_kw)
    return name

# -----------------------------
# Declaration extraction
# -----------------------------


def _trim_to_content_end(src: str, start: int, end: int) -> int:
    """Find the actual end position of content, excluding trailing whitespace."""
    actual_end = end
    while actual_end > start and src[actual_end - 1].isspace():
        actual_end -= 1
    return actual_end

def _add_block(blocks: List[ProofBlock], src: str, block_type: str, start: int, end: int) -> None:
    text = src[start:end].rstrip()
    actual_end = _trim_to_content_end(src, start, end) if text else start
    blocks.append(ProofBlock(type=block_type, span=(start, actual_end), text=text))

def _append_trailing_blocks(
    idx: _TopLevelIndex,
    start: int,
    end: int,
    blocks: List[ProofBlock],
) -> None:
    p = start
    while True:
        t = idx.next_token_after(p, end, TRAILING_BLOCKS)
        if not t:
            break
        label, i0 = t
        nxt = idx.next_token_after(i0 + len(label), end, TRAILING_BLOCKS)
        i1 = min(nxt[1], end) if nxt else end
        _add_block(blocks, idx.src, label, i0, i1)
        p = i1

def extract_proof_blocks(src: str) -> List[Decl]:
    idx = _build_top_level_index(src)
    decl_namespaces = _compute_namespace_map(idx)
    decl_variables = _compute_variables_map(idx)
    decls: List[Decl] = []

    for m in idx.decl_matches:
        kind = m.group("kw")
        pos_kw = m.start("kw")

        decl_end = _find_decl_end(idx, m.end("kw"), kind)

        tok = idx.first_token_in_range(m.end("kw"), decl_end, [":=", "where"])  # earliest wins

        blocks: List[ProofBlock] = []
        name, name_span = extract_name_with_span(kind, idx.src, pos_kw)
        namespace_components = decl_namespaces.get(m.start(), [])
        fullname = _build_fullname(namespace_components, name)
        variables = decl_variables.get(m.start(), [])

        if tok and tok[0] == ":=":
            start_body = tok[1] + 2
            tail_end = decl_end if kind in _DERIVING_ATTACH_KINDS else idx.find_next_cmd_after(start_body)

            where_tok = idx.first_token_in_range(start_body, tail_end, ["where"])
            if where_tok:
                _add_block(blocks, idx.src, "rhs", start_body, where_tok[1])
                _add_block(blocks, idx.src, "where", where_tok[1], tail_end)
            else:
                earliest_trailing = idx.first_token_in_range(start_body, tail_end, TRAILING_BLOCKS)
                rhs_end = earliest_trailing[1] if earliest_trailing else tail_end
                _add_block(blocks, idx.src, "rhs", start_body, rhs_end)
                _append_trailing_blocks(idx, rhs_end, tail_end, blocks)

            header_span = (pos_kw, start_body)
            body_span = (start_body, tail_end)

        elif tok and tok[0] == "where":
            start_where = tok[1]
            end_decl = decl_end if kind in _DERIVING_ATTACH_KINDS else idx.find_next_cmd_after(start_where)
            _add_block(blocks, idx.src, "where", start_where, end_decl)
            header_span = (pos_kw, start_where)
            body_span = (start_where, end_decl)

        else:
            line_end = idx.src.find("\n", pos_kw)
            if line_end == -1:
                line_end = len(idx.src)
            start_search = line_end + 1 if line_end < len(idx.src) else line_end
            end_decl = decl_end if kind in _DERIVING_ATTACH_KINDS else idx.find_next_cmd_after(start_search)

            j = bisect_left(idx.pattern_line_starts, start_search)
            pattern_match_start = None
            if j < len(idx.pattern_line_starts) and idx.pattern_line_starts[j] < end_decl:
                pattern_match_start = idx.pattern_line_starts[j]

            if pattern_match_start is not None:
                header_span = (pos_kw, pattern_match_start)
                body_span = (pattern_match_start, end_decl)

                earliest = idx.first_token_in_range(pattern_match_start, end_decl, TRAILING_BLOCKS)
                match_end = earliest[1] if earliest else end_decl
                _add_block(blocks, idx.src, "rhs", pattern_match_start, match_end)
                _append_trailing_blocks(idx, match_end, end_decl, blocks)
            else:
                earliest = idx.first_token_in_range(start_search, end_decl, TRAILING_BLOCKS)
                eq_end = earliest[1] if earliest else end_decl
                _add_block(blocks, idx.src, "equations", start_search, eq_end)
                _append_trailing_blocks(idx, eq_end, end_decl, blocks)

                header_span = (pos_kw, start_search)
                body_span = (start_search, end_decl)

        decls.append(Decl(
            kind=kind, 
            name=name, 
            fullname=fullname,
            name_span=name_span,
            variables=variables,
            header_span=header_span, 
            body_span=body_span, 
            blocks=blocks
        ))

    return decls

# -----------------------------
# Major declarations API
# -----------------------------

class MajorDecl(BaseModel):
    """Summary of a major Lean declaration.

    Fields:
        kind: Declaration keyword, e.g. def/theorem/lemma/...
        name: Optional declaration name (None for anonymous or kinds without a name)
        name_span: Optional absolute byte-span (start, end) of the name in source
        signature: Declaration signature including keyword, name, parameters and type.
                   For definitions with ':=' this includes the trailing ':='.
                   For 'where'-style decls this stops right before 'where'.
        proof: Proof content for theorems/lemmas or implementation for definitions. May be empty.
        span: Overall byte-span [start, end) of the declaration in the source.
    """
    kind: str
    name: Optional[str]
    fullname: Optional[str] = None
    name_span: Optional[Tuple[int, int]] = None
    variables: List[str] = Field(default_factory=list)
    signature: str
    proof: str
    span: Tuple[int, int]


def _clean_trailing_comments(text: str) -> str:
    """Remove trailing comments from text using existing masking mechanism."""
    if not text.strip():
        return text
    
    # Use existing comment masking to identify comment regions
    masked = mask_noncode_regions(text)
    
    # Find the last non-whitespace, non-masked character
    last_content_pos = len(text)
    for i in range(len(text) - 1, -1, -1):
        if text[i].strip() and masked[i].strip():
            # Found last real content (not comment or whitespace)
            last_content_pos = i + 1
            break
    
    # Return text up to last real content
    return text[:last_content_pos].rstrip()

def parse_major_declarations(src: str) -> List[MajorDecl]:
    """Extract all major declarations and split them into header and body.

    Returns one entry per top-level declaration among:
    def | theorem | lemma | example | instance | abbrev | axiom | structure | class | inductive.

    The header (before) ends right before the main body token and includes ':='
    when present. The body (after) is the first main block among rhs/equations/where.
    """
    results: List[MajorDecl] = []
    for decl in extract_proof_blocks(src):
        # Determine full span of this declaration
        full_start = decl.header_span[0]
        full_end = decl.body_span[1]

        primary = None
        for b in decl.blocks:
            if b.type in ("rhs", "equations", "where"):
                primary = b
                break

        if primary is None:
            signature_text = src[decl.header_span[0]:decl.header_span[1]]
            proof_text = ""
        else:
            if primary.type == "rhs":
                signature_text = src[decl.header_span[0]:decl.header_span[1]]
                proof_text = _clean_trailing_comments(primary.text)
            else:
                if primary.type == "where":
                    where_keyword_end = primary.span[0] + 5
                    signature_text = src[decl.header_span[0]:where_keyword_end]
                    proof_text = _clean_trailing_comments(primary.text[5:])
                else:
                    signature_text = src[decl.header_span[0]:primary.span[0]]
                    proof_text = _clean_trailing_comments(primary.text)

        results.append(MajorDecl(
            kind=decl.kind,
            name=decl.name,
            fullname=decl.fullname,
            name_span=decl.name_span,
            variables=decl.variables,
            signature=signature_text,
            proof=proof_text,
            span=(full_start, full_end),
        ))
    return results

def format_lean_code(
    src: str,
    display_mode: str = "full",
    proof_handling: str = "keep_all",
    line_spans: Optional[List[Tuple[int, int]]] = None,
    context_lines: int = 3,
    proof_placeholder: str = "/- ... omitted proof ... -/",
    add_line_numbers: bool = True,
    range_separator: str = "\n"
) -> str:
    """
    Format Lean source code with flexible display and proof handling options.
    
    Args:
        src: Original Lean source code
        display_mode: Display mode
            - "full": Show complete file
            - "line_spans": Show only specified line ranges with context
        proof_handling: How to handle proofs
            - "keep_all": Keep all proofs
            - "omit_all": Omit all proofs (theorem/lemma/example)
            - "omit_outside_spans": Omit proofs outside specified line spans (requires line_spans)
        line_spans: Optional list of (start_line, end_line) tuples (1-based, inclusive)
        context_lines: Number of context lines before/after each range in line_spans mode
        proof_placeholder: Text to replace omitted proofs
        add_line_numbers: Whether to add line numbers
        range_separator: Separator between non-contiguous ranges
        
    Returns:
        Formatted source code
    """
    if not src:
        return ""
    
    lines = src.splitlines()
    total_lines = len(lines)
    
    # Process line spans if provided
    span_ranges = []
    if line_spans:
        # Validate and sort line spans (with negative index support)
        for start, end in line_spans:
            # Handle negative indices (Python style)
            if start < 0:
                start = total_lines + start + 1
            if end < 0:
                end = total_lines + end + 1
            
            if start < 1 or end < start:
                raise ValueError(f"Invalid line span: ({start}, {end})")
            span_ranges.append((start, end))
        span_ranges.sort(key=lambda x: x[0])
    
    # Validate parameters
    if proof_handling == "omit_outside_spans" and not line_spans:
        raise ValueError("proof_handling='omit_outside_spans' requires line_spans")
    if display_mode == "line_spans" and not line_spans:
        raise ValueError("display_mode='line_spans' requires line_spans")
    
    # Step 1: Determine which lines to display
    display_lines = set()
    if display_mode == "full":
        display_lines = set(range(1, total_lines + 1))
    elif display_mode == "line_spans":
        # Add line spans with context
        for start, end in span_ranges:
            context_start = max(1, start - context_lines)
            context_end = min(total_lines, end + context_lines)
            display_lines.update(range(context_start, context_end + 1))
    
    # Step 2: Parse proof blocks if needed
    omit_ranges = []
    if proof_handling in ("omit_all", "omit_outside_spans"):
        OMIT_KINDS = {"theorem", "lemma", "example"}
        ALLOWED_BLOCK_TYPES = {"rhs", "where", "equations", "termination_by", "decreasing_by"}
        
        for decl in extract_proof_blocks(src):
            if decl.kind not in OMIT_KINDS:
                continue
            for block in decl.blocks:
                if not block.text.strip():
                    continue
                if block.type not in ALLOWED_BLOCK_TYPES:
                    continue
                start, end = block.span
                if block.type == "where":
                    # Preserve 'where' keyword in signature
                    start = min(start + 5, end)
                if start < end:
                    omit_ranges.append((start, end))
        omit_ranges.sort(key=lambda x: x[0])
    
    # Step 3: Determine which proofs to actually omit
    # Cache character position to line number mapping for performance
    line_cache = {}  # Cache character position to line number mapping
    
    def char_to_line(char_pos: int) -> int:
        if char_pos not in line_cache:
            line_cache[char_pos] = src[:char_pos].count('\n') + 1
        return line_cache[char_pos]
    
    def should_omit_proof(proof_start_char: int, proof_end_char: int) -> bool:
        if proof_handling == "keep_all":
            return False
        elif proof_handling == "omit_all":
            return True
        elif proof_handling == "omit_outside_spans":
            # Convert char positions to line numbers using cache
            proof_start_line = char_to_line(proof_start_char)
            proof_end_line = char_to_line(proof_end_char)
            
            # Check if proof overlaps with any line span
            for span_start, span_end in span_ranges:
                if not (proof_end_line < span_start or proof_start_line > span_end):
                    return False  # Overlaps with span, don't omit
            return True  # No overlap, omit
        return False
    
    # Step 4: Process lines and build output
    output_lines = []
    char_pos = 0
    current_proof_idx = 0
    inside_proof = False
    last_displayed_line = 0
    
    for line_num in range(1, total_lines + 1):
        line = lines[line_num - 1]
        line_start = char_pos
        line_end = char_pos + len(line)
        
        # Skip if not in display range
        if line_num not in display_lines:
            char_pos = line_end + 1
            continue
        
        # Add separator if there's a gap (only for line_spans mode)
        # Only add separator for real gaps in display ranges, not for omitted proofs
        if display_mode == "line_spans" and last_displayed_line > 0:
            # Check if there's a real gap in the display_lines (not caused by proof omission)
            real_gap_exists = False
            for check_line in range(last_displayed_line + 1, line_num):
                if check_line not in display_lines:
                    # There's a line in display range that we skipped, so it's a real gap
                    real_gap_exists = True
                    break
            
            if real_gap_exists:
                output_lines.append(range_separator.rstrip())
        
        # Process proof omission
        processed_line = line
        
        # Advance to next proof block if needed
        while current_proof_idx < len(omit_ranges) and line_start >= omit_ranges[current_proof_idx][1]:
            current_proof_idx += 1
            inside_proof = False
        
        if current_proof_idx < len(omit_ranges):
            proof_start, proof_end = omit_ranges[current_proof_idx]
            should_omit = should_omit_proof(proof_start, proof_end)
            
            if inside_proof:
                # Inside multi-line proof
                if line_end >= proof_end:
                    inside_proof = False
                    current_proof_idx += 1
                if should_omit:
                    # Skip this line entirely
                    char_pos = line_end + 1
                    continue
            
            # Check if proof starts in this line
            if proof_start <= line_end and proof_start >= line_start:
                if should_omit:
                    prefix = line[:proof_start - line_start]
                    if proof_end <= line_end:
                        # Single-line proof
                        suffix = line[proof_end - line_start:]
                        processed_line = prefix + proof_placeholder + suffix
                        current_proof_idx += 1
                    else:
                        # Multi-line proof starts
                        processed_line = prefix + proof_placeholder
                        inside_proof = True
            elif proof_start <= line_start < proof_end:
                # Entire line inside proof
                if line_end >= proof_end:
                    current_proof_idx += 1
                    inside_proof = False
                if should_omit:
                    char_pos = line_end + 1
                    continue
        
        # Add line to output
        if add_line_numbers:
            output_lines.append(f"{line_num:6d}|{processed_line}")
        else:
            output_lines.append(processed_line)
        
        last_displayed_line = line_num
        char_pos = line_end + 1
    
    return '\n'.join(output_lines)

def rename_and_set_proof(
    src: str, 
    new_name: str,
    new_proof: str = "sorry",
    verify_old_name: Optional[str] = None
) -> str:
    """
    Rename the first declaration and set its proof.
    
    For := style declarations, replace the proof with specified content.
    Mainly used for BEq proving:
    - Q (assumption): new_proof="sorry" means assumption is true
    - P (target): new_proof="by" means waiting for proof
    
    Args:
        src: Original Lean source code
        new_name: New declaration name
        new_proof: New proof content ("sorry", "by", "trivial" etc.)
        verify_old_name: Optional old name to verify
        
    Returns:
        Source code with renamed declaration and replaced proof
        
    Example:
        >>> src = "theorem foo : True := by simp"
        >>> rename_and_set_proof(src, "thm_Q", "sorry")
        "theorem thm_Q : True := sorry"
        
        >>> rename_and_set_proof(src, "thm_P", "by")
        "theorem thm_P : True := by"
    """
    decls = extract_proof_blocks(src)
    if not decls:
        raise ValueError("No declaration found in source code")
    
    decl = decls[0]
    
    # Verify if there is a name
    if not decl.name or not decl.name_span:
        raise ValueError(
            f"Cannot rename anonymous declaration of kind '{decl.kind}'"
        )
    
    # Verify original name (if provided)
    if verify_old_name is not None and decl.name != verify_old_name:
        raise ValueError(
            f"Name mismatch: expected '{verify_old_name}', found '{decl.name}'"
        )
    
    name_start, name_end = decl.name_span
    
    # Check if there is rhs block (:= style)
    has_rhs_block = any(b.type == "rhs" for b in decl.blocks)
    
    if not has_rhs_block:
        raise ValueError(
            f"Cannot set proof for non-rhs declaration (kind='{decl.kind}'). "
            f"This function only works with := style declarations."
        )
    
    # Rename + replace proof
    # body_span[0] is the position after :=
    new_code = (
        src[:name_start] +              # Before name
        new_name +                      # New name
        src[name_end:decl.body_span[0]] # Name after body before (contains :=)
        + new_proof +                   # New proof
        src[decl.body_span[1]:]         # Content after declaration
    )
    
    return new_code

def convert_to_axiom(
    src: str, 
    new_name: str,
    verify_old_name: Optional[str] = None
) -> str:
    """
    Convert the first declaration to axiom (remove proof, only keep type declaration).
    
    Mainly used for BEq proving: declare Q as axiom (assumption, no proof).
    
    How it works:
    1. Parse source code to get declaration span information
    2. For := style declarations, find := position in header region
    3. Extract the part from start to := (type declaration)
    4. Replace keyword with axiom, name with new_name
    
    Args:
        src: Original Lean source code containing a theorem/lemma
        new_name: New axiom name
        verify_old_name: Optional old name to verify
        
    Returns:
        Source code with axiom declaration (no proof)
        
    Example:
        >>> src = "theorem foo (n : Nat) : n + 0 = n := by simp"
        >>> convert_to_axiom(src, "thm_Q")
        "axiom thm_Q (n : Nat) : n + 0 = n"
        
        >>> src = "lemma bar : True := sorry"
        >>> convert_to_axiom(src, "thm_Q", verify_old_name="bar")
        "axiom thm_Q : True"
    """
    decls = extract_proof_blocks(src)
    if not decls:
        raise ValueError("No declaration found in source code")
    
    decl = decls[0]
    
    # Verify if there is a name
    if not decl.name or not decl.name_span:
        raise ValueError(
            f"Cannot convert anonymous declaration of kind '{decl.kind}' to axiom"
        )
    
    # Verify original name (if provided)
    if verify_old_name is not None and decl.name != verify_old_name:
        raise ValueError(
            f"Name mismatch: expected '{verify_old_name}', found '{decl.kind}'"
        )
    
    # Check if there is rhs block (:= style)
    has_rhs_block = any(b.type == "rhs" for b in decl.blocks)
    
    if not has_rhs_block:
        raise ValueError(
            f"Cannot convert non-rhs declaration (kind='{decl.kind}') to axiom. "
            f"This function only works with := style declarations."
        )
    
    # Find := position in header region (using mask to avoid := in comments/strings)
    header_start, header_end = decl.header_span
    header_region = src[header_start:header_end]
    header_mask = mask_noncode_regions(header_region)
    
    # Find last := from back to front (in real code)
    assign_pos = -1
    i = len(header_mask) - 2  # -2 because := has two characters
    while i >= 0:
        if header_mask[i:i+2] == ':=':
            assign_pos = i
            break
        i -= 1
    
    if assign_pos == -1:
        raise ValueError("Cannot find := token in header region")
    
    # Calculate absolute position of type declaration end (before :=, remove trailing spaces)
    type_decl_end = header_start + assign_pos
    while type_decl_end > header_start and src[type_decl_end - 1].isspace():
        type_decl_end -= 1
    
    # Extract part from start to name before (contains keyword)
    kind_start, kind_end = decl.header_span[0], decl.name_span[0]
    
    # Extract part from name after to type declaration end
    name_end_pos = decl.name_span[1]
    
    # Construct new axiom declaration
    new_code = (
        "axiom " +                      # New keyword
        new_name +                       # New name
        src[name_end_pos:type_decl_end] +  # Parameters and type (from name end to := before)
        src[decl.body_span[1]:]         # Content after declaration (next declaration etc.)
    )

    return new_code


def extract_imports(src: str) -> List[str]:
    """
    Extract all import statements from Lean source code.

    Returns a list of module paths (e.g., ['Mathlib.Data.List.Basic', 'Std.Data.HashMap'])

    This function:
    1. Masks comments and strings to avoid false matches
    2. Extracts import statements
    3. Returns normalized module paths
    """
    # Mask comments and strings
    masked = mask_noncode_regions(src)

    # Extract import statements
    # Pattern: import <module_path>
    import_pattern = re.compile(r'\bimport\s+([A-Z][A-Za-z0-9_.]*)')

    imports = []
    for match in import_pattern.finditer(masked):
        module_path = match.group(1).strip()
        if module_path:
            imports.append(module_path)

    return imports


def module_path_to_file_path(module_path: str, base_dir: Path) -> Optional[Path]:
    """
    Convert a Lean module path to a relative file path.

    Args:
        module_path: e.g., 'Mathlib.Data.List.Basic'
        base_dir: Base directory (workspace root)

    Returns:
        Relative Path to the .lean file (e.g., Path('Mathlib/Data/List/Basic.lean')), or None if not found
    """
    # Convert dots to slashes
    rel_path = Path(module_path.replace('.', '/') + '.lean')
    full_path = base_dir / rel_path

    if full_path.exists():
        return rel_path
    return None


async def check_dependencies_against_blocked_paths(
    code: str,
    working_dir: Path,
    blocked_paths: List[Path]
) -> Tuple[bool, Optional[str], List[Path]]:
    """
    Efficiently check if code depends on any blocked paths.

    Strategy: Instead of recursively parsing all dependencies from the code,
    we compute which files are transitively blocked (files that import blocked files),
    then check if the code imports any of them.

    This is much more efficient because:
    1. blocked_paths is typically small (few files)
    2. We only need to scan the workspace once to build reverse dependency graph
    3. We don't need to recursively parse the user's entire dependency tree

    Args:
        code: Lean source code to verify
        working_dir: Working directory (workspace root, absolute path)
        blocked_paths: List of blocked file paths (relative to working_dir)

    Returns:
        Tuple of (is_safe, error_message, blocked_dependencies):
        - is_safe: True if no blocked dependencies found
        - error_message: Error message if blocked dependencies found, None otherwise
        - blocked_dependencies: List of blocked dependency paths that code imports (relative)
    """
    if not blocked_paths:
        return True, None, []

    # Convert blocked paths to absolute for compute_transitive_blocked_paths
    blocked_absolute = [working_dir / p for p in blocked_paths]

    # Compute all transitively blocked files (files that directly or indirectly import blocked files)
    all_blocked_absolute = await compute_transitive_blocked_paths(blocked_absolute, working_dir)

    # Convert back to relative paths for comparison
    all_blocked_relative = set()
    for abs_path in all_blocked_absolute:
        try:
            rel_path = abs_path.relative_to(working_dir)
            all_blocked_relative.add(rel_path)
        except ValueError:
            pass

    # Extract direct imports from code
    imports = extract_imports(code)

    # Check each import
    blocked_dependencies = []
    for module_name in imports:
        rel_path = module_path_to_file_path(module_name, working_dir)
        if rel_path and rel_path in all_blocked_relative:
            blocked_dependencies.append(rel_path)

    if blocked_dependencies:
        error_message = (
            f"Cannot verify code that depends on blocked paths. "
            f"Blocked dependencies: {', '.join(str(p) for p in blocked_dependencies)}"
        )
        return False, error_message, blocked_dependencies

    return True, None, []


async def compute_transitive_blocked_paths(
    directly_blocked_files: List[Path],
    workspace_dir: Path
) -> List[Path]:
    """
    Compute all files that should be blocked due to transitive dependencies.

    Uses DFS with a reverse dependency graph for better performance.
    Files are read in parallel using asyncio for maximum speed.

    Args:
        directly_blocked_files: List of directly blocked file paths (absolute)
        workspace_dir: Workspace directory to search for Lean files

    Returns:
        List of all file paths that should be blocked (including transitive dependencies)
    """

    async def read_file_imports(lean_file: Path) -> List[str]:
        """Read a single file header and extract its imports.

        Lean `import` commands are expected at the beginning of the file (after whitespace/comments).
        To avoid unnecessary I/O, we stop reading once we reach the first non-trivia, non-import line.
        """
        try:
            # Inline block comment segments that start and end on the same line.
            # Multi-line block comments are handled by a simple depth counter.
            inline_block_comment_re = re.compile(r"/-.*?-/")

            header_lines: List[str] = []
            block_comment_depth = 0

            async with aiofiles.open(lean_file, 'r', encoding='utf-8') as f:
                async for line in f:
                    header_lines.append(line)

                    # Track multi-line (possibly nested) block comments.
                    # We intentionally keep this lightweight: it is only used to avoid
                    # prematurely terminating the header scan.
                    i = 0
                    while i < len(line) - 1:
                        two = line[i:i + 2]
                        if two == "/-":
                            block_comment_depth += 1
                            i += 2
                            continue
                        if two == "-/":
                            if block_comment_depth > 0:
                                block_comment_depth -= 1
                            i += 2
                            continue
                        i += 1

                    if block_comment_depth > 0:
                        continue

                    # Remove same-line block comments and line comments to decide whether
                    # we've reached the end of the import header section.
                    effective = inline_block_comment_re.sub(" ", line)
                    effective = effective.split("--", 1)[0]
                    effective_stripped = effective.strip()
                    if not effective_stripped:
                        continue
                    if effective_stripped.startswith("import "):
                        continue

                    # First non-trivia, non-import line => imports section is over.
                    break

            return extract_imports("".join(header_lines))
        except Exception:
            # Skip files that can't be read
            return []

    # Step 1: Collect all .lean files and compute their module paths
    all_lean_files = list(workspace_dir.rglob('*.lean'))
    workspace_str = str(workspace_dir.resolve()) + '/'
    file_to_module = {
        f: str(f.resolve()).removeprefix(workspace_str).removesuffix('.lean').replace('/', '.')
        for f in all_lean_files
    }

    # Step 2: Read all files in parallel to extract imports
    imports_list = await asyncio.gather(*[read_file_imports(f) for f in all_lean_files])

    # Step 3: Build reverse dependency graph (module -> files that import it)
    reverse_deps: Dict[str, List[Path]] = {}

    for file_path, imports in zip(file_to_module.keys(), imports_list):
        # For each import, record that file_path imports it
        for imp in imports:
            if imp not in reverse_deps:
                reverse_deps[imp] = []
            reverse_deps[imp].append(file_path)

    # Step 4: DFS from directly_blocked_files to find all transitive dependencies
    blocked = set(directly_blocked_files)

    def dfs(file_path: Path):
        """DFS to find all files that depend on the given file."""
        # Get module path for this file
        module_path = file_to_module.get(file_path)
        if not module_path:
            return

        # Find all files that import this module
        importers = reverse_deps.get(module_path, [])
        for importer in importers:
            if importer not in blocked:
                blocked.add(importer)
                # Recursively process this importer
                dfs(importer)

    # Start DFS from each directly blocked file
    for blocked_file in directly_blocked_files:
        dfs(blocked_file)

    return list(blocked)
