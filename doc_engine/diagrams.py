"""Fenced blocks that become pictures instead of code.

A ```mermaid block is rendered to SVG through mermaidx, which runs Mermaid on an
embedded JavaScript engine — no Node install, no headless browser. A ```svg block
is passed straight through, since Typst renders SVG natively.
"""

from __future__ import annotations

MERMAID_LANGUAGES = ("mermaid", "mmd")
SVG_LANGUAGES = ("svg",)


class DiagramError(Exception):
    """A diagram source that could not be rendered."""

    def __init__(self, language: str, message: str) -> None:
        super().__init__(message)
        self.language = language
        self.message = message


def is_diagram(language: str) -> bool:
    lang = language.strip().lower()
    return lang in MERMAID_LANGUAGES or lang in SVG_LANGUAGES


def render(language: str, source: str) -> str:
    """Return the SVG for a diagram block, raising DiagramError if it is invalid."""
    lang = language.strip().lower()
    if lang in SVG_LANGUAGES:
        return source
    if lang in MERMAID_LANGUAGES:
        return _render_mermaid(source)
    raise DiagramError(language, f"unsupported diagram language: {language}")


def _render_mermaid(source: str) -> str:
    try:
        import mermaidx
    except ImportError as exc:
        raise DiagramError(
            "mermaid",
            "mermaid rendering needs the 'mermaidx' package, which ships with "
            "doc-engine-cli — reinstall with 'pip install --upgrade doc-engine-cli'",
        ) from exc

    try:
        return mermaidx.render(source).svg()
    except DiagramError:
        raise
    except Exception as exc:
        raise DiagramError("mermaid", _clean(str(exc))) from exc


def _clean(message: str) -> str:
    """Trim mermaidx's wrapper so the user sees Mermaid's own complaint."""
    text = message.strip()
    for prefix in ("Mermaid rendering failed:", "Error:"):
        if text.startswith(prefix):
            text = text[len(prefix) :].strip()
    return " ".join(text.split())
