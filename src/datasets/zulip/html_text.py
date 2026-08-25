"""
Zulip rendered-HTML -> plain text, with the structure we care about preserved.

The archive stores Zulip's *rendered* HTML, not the markdown source. Naive tag
stripping loses three things this store depends on:

1. **Code blocks.** Lean snippets are syntax-highlighted into hundreds of
   `<span class="n">` fragments inside `<div class="codehilite" data-code-language=...>`.
   Stripping tags recovers the characters but loses the language and the block
   boundary, and a maintainer quoting a compiling snippet is the single most
   informative thing in a thread.
2. **Link targets.** `docs#Foo` links carry the declaration name in the *href*
   (`mathlib4_docs/find/?pattern=Foo#doc`) and PR references carry the number in the
   href. Anchor text alone is not enough to build reference tags.
3. **Math.** KaTeX renders each formula twice — a MathML tree and an aria-hidden
   glyph pile. Stripping tags yields the formula's characters two or three times over,
   as noise. The original LaTeX is present exactly once, in
   `<annotation encoding="application/x-tex">`, so math mode emits that and suppresses
   the rest.

Deliberately stdlib-only (`html.parser`): `bs4` is not installed in this environment,
and the markup is a small closed vocabulary that Zulip generates mechanically.
"""

from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple

#: Tags whose content is dropped entirely.
_SKIP_CONTENT = {"style", "script"}


@dataclass
class ExtractedContent:
    text: str
    code_blocks: List[Tuple[str, str]] = field(default_factory=list)
    hrefs: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    has_quote: bool = False


class _ZulipHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: List[str] = []
        self.code_blocks: List[Tuple[str, str]] = []
        self.hrefs: List[str] = []
        self.mentions: List[str] = []
        self.has_quote = False

        self._skip_depth = 0
        self._quote_depth = 0

        # code block state
        self._code_depth = 0          # inside <div class="codehilite">
        self._code_lang = ""
        self._code_parts: List[str] = []

        # katex state: suppress everything except the x-tex annotation. Tracked as a
        # *span nesting count* rather than a flag: a formula is
        # `<span class="katex"><span class="katex-mathml">…</span>
        #  <span class="katex-html">…</span></span>`, so exiting on the first `</span>`
        # would leave the aria-hidden glyph pile unsuppressed and duplicate the formula.
        self._katex_spans = 0
        self._in_annotation = False
        self._mention_depth = 0

    # --- helpers ---------------------------------------------------------

    def _emit(self, text: str) -> None:
        if self._code_depth:
            self._code_parts.append(text)
        else:
            self.parts.append(text)

    def _suppressed(self) -> bool:
        return bool(self._skip_depth) or (self._katex_spans and not self._in_annotation)

    # --- HTMLParser interface -------------------------------------------

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attributes: Dict[str, str] = {k: (v or "") for k, v in attrs}
        classes = set(attributes.get("class", "").split())

        if tag in _SKIP_CONTENT:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return

        if self._katex_spans:
            if tag == "span":
                self._katex_spans += 1
            elif tag == "annotation" and attributes.get("encoding") == "application/x-tex":
                self._in_annotation = True
                self._emit("$")
            return
        if "katex" in classes:
            self._katex_spans = 1
            return

        if "codehilite" in classes:
            self._code_depth += 1
            if self._code_depth == 1:
                self._code_lang = attributes.get("data-code-language", "")
                self._code_parts = []
            return

        if tag == "a":
            href = attributes.get("href", "")
            if href:
                self.hrefs.append(href)
            return
        if tag == "code" and not self._code_depth:
            self._emit("`")
            return
        if tag == "blockquote":
            self._quote_depth += 1
            self.has_quote = True
            self._emit("\n")
            return
        if tag in {"br"}:
            self._emit("\n")
            return
        if tag in {"p", "div", "ul", "ol", "pre", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._emit("\n")
            return
        if tag == "li":
            self._emit("\n- ")
            return
        if tag == "img":
            alt = attributes.get("alt", "").strip()
            if alt:
                self._emit(f"[image: {alt}]")
            return
        if tag == "time":
            stamp = attributes.get("datetime", "").strip()
            if stamp:
                self._emit(stamp)
            return
        if "user-mention" in classes:
            self._mention_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_CONTENT:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return

        if self._katex_spans:
            if tag == "annotation" and self._in_annotation:
                self._in_annotation = False
                self._emit("$")
            elif tag == "span":
                self._katex_spans -= 1
            return

        if self._code_depth and tag == "div":
            self._code_depth -= 1
            if self._code_depth == 0:
                code = "".join(self._code_parts).strip("\n")
                self.code_blocks.append((self._code_lang, code))
                fence = f"\n```{self._code_lang}\n{code}\n```\n"
                self.parts.append(fence)
                self._code_parts = []
            return

        if tag == "code" and not self._code_depth:
            self._emit("`")
            return
        if tag == "blockquote":
            self._quote_depth = max(0, self._quote_depth - 1)
            self._emit("\n")
            return
        if tag in {"p", "div", "ul", "ol", "pre", "li", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._emit("\n")
            return
        if tag == "span" and self._mention_depth:
            self._mention_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._suppressed():
            return
        if self._mention_depth and data.strip():
            name = data.strip().lstrip("@").strip()
            if name and name not in self.mentions:
                self.mentions.append(name)
        self._emit(data)


def _reflow(raw: str, quote_prefix: bool) -> str:
    lines = [line.rstrip() for line in raw.split("\n")]
    out: List[str] = []
    for line in lines:
        if not line and out and not out[-1]:
            continue
        out.append(line)
    text = "\n".join(out).strip("\n")
    if quote_prefix:
        text = "\n".join(f"> {line}" if line else ">" for line in text.split("\n"))
    return text


def extract(content: str) -> ExtractedContent:
    """Parse one Zulip message body. Never raises on malformed markup."""
    parser = _ZulipHTMLParser()
    parser.feed(content)
    parser.close()
    return ExtractedContent(
        text=_reflow("".join(parser.parts), quote_prefix=False),
        code_blocks=list(parser.code_blocks),
        hrefs=list(parser.hrefs),
        mentions=list(parser.mentions),
        has_quote=parser.has_quote,
    )
