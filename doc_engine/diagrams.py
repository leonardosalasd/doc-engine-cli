"""Fenced blocks that become pictures instead of code.

A ```mermaid block is rendered to SVG through mermaidx, which runs Mermaid on an
embedded JavaScript engine — no Node install, no headless browser. A ```svg block
is passed straight through, since Typst renders SVG natively.
"""

from __future__ import annotations

MERMAID_LANGUAGES = ("mermaid", "mmd")
SVG_LANGUAGES = ("svg",)

# Rendering the first Mermaid diagram boots a JavaScript engine and loads
# Mermaid into it, which takes several seconds. Every diagram after that is
# roughly a hundred times faster, so the cost is paid once per process.
_warm = False


class DiagramError(Exception):
    """A diagram source that could not be rendered."""

    def __init__(self, language: str, message: str) -> None:
        super().__init__(message)
        self.language = language
        self.message = message


def is_diagram(language: str) -> bool:
    lang = language.strip().lower()
    return lang in MERMAID_LANGUAGES or lang in SVG_LANGUAGES


def is_warm() -> bool:
    """Whether the Mermaid engine has already started in this process."""
    return _warm


def warmup() -> None:
    """Start the Mermaid engine, so the caller can say why it is waiting."""
    _render_mermaid("flowchart LR\n  A-->B\n")


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

    global _warm
    try:
        svg = mermaidx.render(source).svg()
    except DiagramError:
        raise
    except Exception as exc:
        _warm = True
        raise DiagramError("mermaid", _clean(str(exc))) from exc
    _warm = True
    return svg


def _clean(message: str) -> str:
    """Trim mermaidx's wrapper so the user sees Mermaid's own complaint."""
    text = message.strip()
    for prefix in ("Mermaid rendering failed:", "Error:"):
        if text.startswith(prefix):
            text = text[len(prefix) :].strip()
    return " ".join(text.split())
