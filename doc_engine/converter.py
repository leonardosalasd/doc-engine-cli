"""Markdown to Typst transpiler built on a mistune renderer.

`from __future__ import annotations` is required, not cosmetic: mistune resolves
tokens to methods by name, so this renderer must define one called `list`, which
shadows the builtin inside the class body. Any annotation written there — such as
`tokens: list[dict]` — would otherwise be evaluated against that method and raise
`TypeError: 'function' object is not subscriptable` on import. Python 3.14 defers
annotations by default and hides the problem; every earlier version does not.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import mistune

from doc_engine import diagrams

_TYPST_ESCAPES = {
    "\\": "\\\\",
    "#": "\\#",
    "$": "\\$",
    "@": "\\@",
    "*": "\\*",
    "_": "\\_",
    "`": "\\`",
    "~": "\\~",
    "<": "\\<",
    ">": "\\>",
    "[": "\\[",
    "]": "\\]",
}

_PLUGINS = ["table", "strikethrough", "task_lists", "footnotes"]
_REMOTE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:)?//", re.IGNORECASE)
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]")

# Pandoc-style [@key] survives escaping as \[\@key\]; restore it as a Typst @key.
_CITATION = re.compile(r"\\\[\\@([a-zA-Z0-9_\-]+)\\\]")

_UNCHECKED = (
    '#box(width: 0.85em, height: 0.85em, radius: 2pt, '
    'stroke: 1pt + rgb("#94a3b8"), baseline: 0.15em)'
)
_CHECKED = (
    '#box(width: 0.85em, height: 0.85em, radius: 2pt, fill: rgb("#16a34a"), '
    'baseline: 0.15em)[#align(center + horizon)[#text(fill: white, size: 0.62em, weight: 700)[✓]]]'
)


def _escape(text: str) -> str:
    return "".join(_TYPST_ESCAPES.get(ch, ch) for ch in text)


def _render_children(renderer: mistune.BaseRenderer, token: dict, state: Any) -> str:
    children = token.get("children")
    if not children:
        return _escape(token.get("raw", ""))
    return renderer.render_tokens(children, state)


@dataclass
class Conversion:
    """Typst markup plus everything the compiler must place beside it.

    `assets` maps a sandbox-relative name to a file on disk to copy. `generated`
    maps a name to content produced during conversion, such as a rendered
    diagram, which has no file of its own.
    """

    body: str
    assets: dict[str, str] = field(default_factory=dict)
    generated: dict[str, str] = field(default_factory=dict)


class TypstRenderer(mistune.BaseRenderer):
    NAME = "typst"

    def __init__(self, base_dir: Path | None = None) -> None:
        super().__init__()
        self._ordered_stack: list[bool] = []
        self._base_dir = base_dir
        self._footnotes: dict[str, str] = {}
        self._asset_names: dict[str, str] = {}
        self.assets: dict[str, str] = {}
        self.generated: dict[str, str] = {}

    def text(self, token: dict, state: Any) -> str:
        return _escape(token["raw"])

    def strong(self, token: dict, state: Any) -> str:
        return f"*{_render_children(self, token, state)}*"

    def emphasis(self, token: dict, state: Any) -> str:
        return f"_{_render_children(self, token, state)}_"

    def codespan(self, token: dict, state: Any) -> str:
        raw = token["raw"]
        return f"``{raw}``" if "`" in raw else f"`{raw}`"

    def link(self, token: dict, state: Any) -> str:
        children = _render_children(self, token, state)
        url = token["attrs"]["url"]
        return f'#link("{url}")[{children}]'

    def image(self, token: dict, state: Any) -> str:
        url = token.get("attrs", {}).get("url", "")
        alt = _render_children(self, token, state)
        asset = self._register_image(url)
        if asset is None:
            return f"[{alt}]" if alt else ""
        return f'#fit-image("{asset}")'

    def linebreak(self, token: dict, state: Any) -> str:
        return "\\\n"

    def softbreak(self, token: dict, state: Any) -> str:
        return "\n"

    def strikethrough(self, token: dict, state: Any) -> str:
        return f"#strike[{_render_children(self, token, state)}]"

    def inline_html(self, token: dict, state: Any) -> str:
        raw = token.get("raw", "").strip().lower()
        if raw in ("<br>", "<br/>", "<br />"):
            return "\\\n"
        return ""

    def footnote_ref(self, token: dict, state: Any) -> str:
        key = token["raw"]
        body = self._footnotes.get(key, "")
        return f"#footnote[{body}]"

    def blank_line(self, token: dict, state: Any) -> str:
        return ""

    def block_text(self, token: dict, state: Any) -> str:
        return _render_children(self, token, state)

    def paragraph(self, token: dict, state: Any) -> str:
        body = _render_children(self, token, state).strip()
        return f"{body}\n\n" if body else ""

    def heading(self, token: dict, state: Any) -> str:
        level = token["attrs"]["level"]
        body = _render_children(self, token, state)
        return f"\n{'=' * level} {body}\n\n"

    def block_code(self, token: dict, state: Any) -> str:
        info = token.get("attrs", {}).get("info", "") or ""
        lang = info.split()[0] if info else ""
        code = token["raw"]
        if lang and diagrams.is_diagram(lang):
            return self._render_diagram(lang, code)
        return f"\n```{lang}\n{code}```\n\n"

    def _render_diagram(self, language: str, source: str) -> str:
        svg = diagrams.render(language, source)
        name = f"assets/diagram_{len(self.generated)}.svg"
        self.generated[name] = svg
        return f'\n#align(center)[#fit-image("{name}")]\n\n'

    def block_quote(self, token: dict, state: Any) -> str:
        content = _render_children(self, token, state).strip()
        return (
            "#block(\n"
            '  inset: (left: 1.2em, y: 0.6em),\n'
            '  stroke: (left: 2.5pt + rgb("#4a90d9")),\n'
            '  fill: rgb("#f0f4f8"),\n'
            "  radius: 2pt,\n"
            f")[{content}]\n\n"
        )

    def list(self, token: dict, state: Any) -> str:
        ordered = token.get("attrs", {}).get("ordered", False)
        self._ordered_stack.append(ordered)
        body = _render_children(self, token, state)
        self._ordered_stack.pop()
        return body + "\n"

    def list_item(self, token: dict, state: Any) -> str:
        body = _render_children(self, token, state)
        marker = "+" if (self._ordered_stack and self._ordered_stack[-1]) else "-"
        lines = body.strip().split("\n")
        result = f"{marker} {lines[0]}\n"
        for extra in lines[1:]:
            if extra.strip():
                result += f"  {extra}\n"
        return result

    def task_list_item(self, token: dict, state: Any) -> str:
        checked = token.get("attrs", {}).get("checked", False)
        box = _CHECKED if checked else _UNCHECKED
        body = " ".join(_render_children(self, token, state).split())
        return f"{box} {body} \\\n"

    def thematic_break(self, token: dict, state: Any) -> str:
        return '\n#line(length: 100%, stroke: 0.5pt + rgb("#d0d0d0"))\n\n'

    def block_html(self, token: dict, state: Any) -> str:
        return ""

    def footnotes(self, token: dict, state: Any) -> str:
        return ""

    def footnote_item(self, token: dict, state: Any) -> str:
        return ""

    def table(self, token: dict, state: Any) -> str:
        head = None
        body_rows: list[dict] = []

        for child in token.get("children", []):
            if child["type"] == "table_head":
                head = child
            elif child["type"] == "table_body":
                body_rows = child.get("children", [])

        if not head:
            return ""

        head_row = head.get("children", [{}])[0]
        cells = head_row.get("children", [])
        n = len(cells)
        if n == 0:
            return ""

        cols = ", ".join(["1fr"] * n)
        out = (
            f"#table(\n  columns: ({cols}),\n"
            '  stroke: 0.5pt + rgb("#d0d0d0"),\n'
            "  inset: 8pt,\n"
            '  fill: (_, row) => if row == 0 { rgb("#f0f0f0") },\n'
        )
        for c in cells:
            txt = _render_children(self, c, state).strip()
            out += f"  [*{txt}*],\n"
        for row in body_rows:
            for c in row.get("children", []):
                txt = _render_children(self, c, state).strip()
                out += f"  [{txt}],\n"
        return out + ")\n\n"

    def table_head(self, token: dict, state: Any) -> str:
        return ""

    def table_body(self, token: dict, state: Any) -> str:
        return ""

    def table_row(self, token: dict, state: Any) -> str:
        return ""

    def table_cell(self, token: dict, state: Any) -> str:
        return _render_children(self, token, state)

    def load_footnotes(self, tokens: list[dict], state: Any) -> None:
        for token in tokens:
            if token.get("type") != "footnotes":
                continue
            for item in token.get("children", []):
                key = item.get("attrs", {}).get("key")
                if key is None:
                    continue
                rendered = _render_children(self, item, state)
                self._footnotes[str(key)] = " ".join(rendered.split())

    def _register_image(self, url: str) -> str | None:
        if not url or self._base_dir is None or _REMOTE.match(url) or url.startswith("data:"):
            return None
        source = (self._base_dir / url).expanduser()
        if not source.is_file():
            return None
        resolved = str(source.resolve())
        if resolved in self._asset_names:
            return self._asset_names[resolved]
        name = f"assets/{len(self.assets)}_{_UNSAFE.sub('_', source.name)}"
        self._asset_names[resolved] = name
        self.assets[name] = resolved
        return name

    def finalize(self, data: str, state: Any) -> str:
        return data


def convert_document(markdown: str, base_dir: Path | None = None) -> Conversion:
    renderer = TypstRenderer(base_dir=base_dir)
    md = mistune.create_markdown(renderer=None, plugins=_PLUGINS)
    tokens, state = md.parse(markdown)
    renderer.load_footnotes(tokens, state)
    body = renderer.render_tokens(tokens, state)
    body = _CITATION.sub(r"@\1", body)
    return Conversion(body=body, assets=renderer.assets, generated=renderer.generated)


def convert(markdown: str, base_dir: Path | None = None) -> str:
    return convert_document(markdown, base_dir).body


def extract_title(markdown: str) -> str:
    for line in markdown.split("\n"):
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("##"):
            return stripped[2:].strip() or "Documentation"
    return "Documentation"


def strip_first_heading(markdown: str) -> str:
    lines = markdown.split("\n")
    result: list[str] = []
    found = False
    for line in lines:
        if not found and line.strip().startswith("# ") and not line.strip().startswith("##"):
            found = True
            continue
        if found and not result and not line.strip():
            continue
        result.append(line)
    return "\n".join(result)
