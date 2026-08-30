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

from doc_engine import diagrams, images, latex, remote

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

_BLOCK_MATH = r"^ {0,3}\$\$[ \t]*\n(?P<math_text>[\s\S]+?)\n\$\$[ \t]*$"

# mistune's own inline rule writes the closing guard as a lookahead where it
# needs a lookbehind, so "it costs $10 and $20" parses the middle as math and
# mangles it. Requiring no space beside either delimiter, and no digit after the
# closing one, keeps prices and shell variables out of math mode.
_INLINE_MATH = r"\$(?!\s)(?P<math_text>(?:[^$\\\n]|\\.)+?)(?<!\s)\$(?!\d)"
_REMOTE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:)?//", re.IGNORECASE)
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]")

# Pandoc-style [@key] survives escaping as \[\@key\]; restore it as a Typst @key.
_CITATION = re.compile(r"\\\[\\@([a-zA-Z0-9_\-]+)\\\]")

# GitHub renders a blockquote opening with [!NOTE] and friends as a coloured
# callout. The marker reaches this point already escaped, since it is ordinary
# text as far as the parser is concerned.
_ALERT = re.compile(r"^\\\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\\\]\s*", re.IGNORECASE)

# Label and colour for each kind, following what GitHub uses.
_ALERT_STYLES = {
    "NOTE": ("Note", "#0969da"),
    "TIP": ("Tip", "#1a7f37"),
    "IMPORTANT": ("Important", "#8250df"),
    "WARNING": ("Warning", "#9a6700"),
    "CAUTION": ("Caution", "#cf222e"),
}

_UNCHECKED = (
    "#box(width: 0.85em, height: 0.85em, radius: 2pt, "
    'stroke: 1pt + rgb("#94a3b8"), baseline: 0.15em)'
)
_CHECKED = (
    '#box(width: 0.85em, height: 0.85em, radius: 2pt, fill: rgb("#16a34a"), '
    "baseline: 0.15em)[#align(center + horizon)[#text(fill: white, size: 0.62em, weight: 700)[✓]]]"
)


def _escape(text: str) -> str:
    return "".join(_TYPST_ESCAPES.get(ch, ch) for ch in text)


def _math_plugin(md: mistune.Markdown) -> None:
    """Register math parsing with a stricter inline rule than mistune ships."""

    def parse_block(block: Any, match: Any, state: Any) -> int:
        state.append_token({"type": "block_math", "raw": match.group("math_text")})
        return match.end() + 1

    def parse_inline(inline: Any, match: Any, state: Any) -> int:
        state.append_token({"type": "inline_math", "raw": match.group("math_text")})
        return match.end()

    md.block.register("block_math", _BLOCK_MATH, parse_block, before="list")
    md.inline.register("inline_math", _INLINE_MATH, parse_inline, before="link")


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
    warnings: list[str] = field(default_factory=list)


class TypstRenderer(mistune.BaseRenderer):
    NAME = "typst"

    def __init__(
        self,
        base_dir: Path | None = None,
        namespace: str = "",
        work_dir: Path | None = None,
        fetch_remote: bool = False,
        split_tall: float | None = None,
        anchors: dict[Path, str] | None = None,
    ) -> None:
        super().__init__()
        self._ordered_stack: list[bool] = []
        self._base_dir = base_dir
        self._namespace = namespace
        self._work_dir = work_dir
        self._fetch_remote = fetch_remote
        self._split_tall = split_tall
        # Resolved paths of the other documents in this build, mapped to the
        # anchor each one carries, so links between them can jump internally.
        self._anchors = {Path(k).resolve(): v for k, v in (anchors or {}).items()}
        self.warnings: list[str] = []
        self._footnotes: dict[str, str] = {}
        self._asset_names: dict[str, str] = {}
        self._cut_pieces: dict[str, list[str]] = {}
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
        anchor = self._anchor_for(url)
        if anchor:
            return f"#link(<{anchor}>)[{children}]"
        return f'#link("{url}")[{children}]'

    def _anchor_for(self, url: str) -> str | None:
        """An anchor when this link points at another file in the same build.

        Linking to a sibling document is normal in a folder of Markdown, but the
        reader of the PDF has no such file, so the link jumps within the document
        instead.
        """
        if not self._anchors or self._base_dir is None or _REMOTE.match(url):
            return None
        target = url.split("#", 1)[0]
        if not target:
            return None
        try:
            resolved = (self._base_dir / target).resolve()
        except OSError:
            return None
        return self._anchors.get(resolved)

    def image(self, token: dict, state: Any) -> str:
        url = token.get("attrs", {}).get("url", "")
        alt = _render_children(self, token, state)
        asset = self._register_image(url)
        if asset is None:
            return f"[{alt}]" if alt else ""
        return self._place(asset)

    def _place(self, asset: str) -> str:
        """Emit a picture, cut across pages when it is too tall for one."""
        if self._split_tall is None:
            return f'#fit-image("{asset}")'
        pieces = self._cut(asset)
        if len(pieces) == 1:
            return f'#fit-image("{pieces[0]}")'
        return "\n#pagebreak(weak: true)\n".join(f'#fit-image("{p}")' for p in pieces)

    def _cut(self, asset: str) -> list[str]:
        # The same picture can appear more than once, and it is registered under
        # one name, so the pieces are remembered. Cutting twice would look for a
        # file whose entry the first pass already replaced.
        if asset in self._cut_pieces:
            return self._cut_pieces[asset]

        source = Path(self.assets.get(asset, ""))
        if not source.is_file() or self._work_dir is None:
            return [asset]
        try:
            written = images.split(source, self._work_dir, self._split_tall, Path(asset).stem)
        except images.SplitError as exc:
            self.warnings.append(str(exc))
            return [asset]
        if len(written) == 1:
            return [asset]

        names = []
        for index, piece in enumerate(written):
            name = f"assets/{self._namespace}{Path(asset).stem}_part{index}.png"
            self.assets[name] = str(piece)
            names.append(name)
        del self.assets[asset]
        self._cut_pieces[asset] = names
        return names

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

    def inline_math(self, token: dict, state: Any) -> str:
        return f"${latex.to_typst(token['raw'])}$"

    def block_math(self, token: dict, state: Any) -> str:
        return f"\n$ {latex.to_typst(token['raw'])} $\n\n"

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
        name = f"assets/{self._namespace}diagram_{len(self.generated)}.svg"
        self.generated[name] = svg
        return f'\n#align(center)[#fit-image("{name}")]\n\n'

    def block_quote(self, token: dict, state: Any) -> str:
        content = _render_children(self, token, state).strip()
        alert = _ALERT.match(content)
        if alert:
            return self._alert(alert.group(1).upper(), content[alert.end() :].strip())
        return (
            "#block(\n"
            "  width: 100%,\n"
            "  inset: (left: 1em, rest: 0.8em),\n"
            '  stroke: (left: 3pt + rgb("#4a90d9")),\n'
            '  fill: rgb("#f0f4f8"),\n'
            "  radius: (right: 3pt),\n"
            f")[{content}]\n\n"
        )

    def _alert(self, kind: str, body: str) -> str:
        label, color = _ALERT_STYLES[kind]
        return (
            "#block(\n"
            "  width: 100%,\n"
            "  inset: (left: 1em, rest: 0.8em),\n"
            f'  stroke: (left: 3pt + rgb("{color}")),\n'
            f'  fill: rgb("{color}").lighten(92%),\n'
            "  radius: (right: 3pt),\n"
            ")[\n"
            f'  #text(weight: 700, fill: rgb("{color}"))[{label}]\n'
            "  #v(0.35em, weak: true)\n"
            f"  {body}\n"
            "]\n\n"
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

        # A table_head holds its cells directly, without a table_row in between.
        cells = head.get("children", [])
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
        if not url or url.startswith("data:"):
            return None
        if _REMOTE.match(url):
            return self._download(url)
        if self._base_dir is None:
            return None
        source = (self._base_dir / url).expanduser()
        if not source.is_file():
            return None
        resolved = str(source.resolve())
        if resolved in self._asset_names:
            return self._asset_names[resolved]
        name = f"assets/{self._namespace}{len(self.assets)}_{_UNSAFE.sub('_', source.name)}"
        self._asset_names[resolved] = name
        self.assets[name] = resolved
        return name

    def _download(self, url: str) -> str | None:
        """Fetch a linked image, when the build asked for that."""
        if not self._fetch_remote or self._work_dir is None:
            return None
        if url in self._asset_names:
            return self._asset_names[url]
        try:
            downloaded = remote.fetch(url, self._work_dir)
        except remote.DownloadError as exc:
            self.warnings.append(f"could not fetch {url} — {exc}")
            return None
        name = f"assets/{self._namespace}{len(self.assets)}_{downloaded.name}"
        self._asset_names[url] = name
        self.assets[name] = str(downloaded)
        return name

    def finalize(self, data: str, state: Any) -> str:
        return data


def convert_document(
    markdown: str,
    base_dir: Path | None = None,
    namespace: str = "",
    work_dir: Path | None = None,
    fetch_remote: bool = False,
    split_tall: float | None = None,
    anchors: dict[Path, str] | None = None,
) -> Conversion:
    """Convert Markdown to Typst.

    *namespace* prefixes the names of assets and rendered diagrams, so several
    documents assembled into one PDF cannot overwrite each other's files.
    *work_dir* is scratch space for anything written during conversion.
    *fetch_remote* allows downloading linked images, and *split_tall* is the
    page proportion above which a picture is cut across pages.
    """
    renderer = TypstRenderer(
        base_dir=base_dir,
        namespace=namespace,
        work_dir=work_dir,
        fetch_remote=fetch_remote,
        split_tall=split_tall,
        anchors=anchors,
    )
    md = mistune.create_markdown(renderer=None, plugins=[*_PLUGINS, _math_plugin])
    tokens, state = md.parse(markdown)
    renderer.load_footnotes(tokens, state)
    body = renderer.render_tokens(tokens, state)
    body = _CITATION.sub(r"@\1", body)
    return Conversion(
        body=body,
        assets=renderer.assets,
        generated=renderer.generated,
        warnings=renderer.warnings,
    )


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
