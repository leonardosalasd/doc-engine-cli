import re
from typing import Any

import mistune

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
}


def _escape(text: str) -> str:
    return "".join(_TYPST_ESCAPES.get(ch, ch) for ch in text)


def _render_children(renderer: mistune.BaseRenderer, token: dict, state: Any) -> str:
    children = token.get("children")
    if not children:
        return _escape(token.get("raw", ""))
    return renderer.render_tokens(children, state)


class TypstRenderer(mistune.BaseRenderer):
    NAME = "typst"

    def __init__(self) -> None:
        super().__init__()
        self._ordered_stack: list[bool] = []

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
        alt = token.get("attrs", {}).get("alt", "")
        return f"[{_escape(alt)}]" if alt else ""

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
        return f"\n```{lang}\n{code}```\n\n"

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

    def thematic_break(self, token: dict, state: Any) -> str:
        return '\n#line(length: 100%, stroke: 0.5pt + rgb("#d0d0d0"))\n\n'

    def block_html(self, token: dict, state: Any) -> str:
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

    def finalize(self, data: str, state: Any) -> str:
        return data


def convert(markdown: str) -> str:
    renderer = TypstRenderer()
    md = mistune.create_markdown(
        renderer=renderer,
        plugins=["table", "strikethrough"],
    )
    return md(markdown)


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
