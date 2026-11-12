"""Working out what a build should actually do.

Three places can set the same option: a command-line flag, the document's front
matter, and the project's `.doc-engine.toml`. Deciding between them was tangled
into the CLI callback, where the only way to test it was to run the whole
program. It lives here instead, as a plain function over plain dictionaries.

Flags win over front matter, which wins over the project file, which falls back
to the built-in default.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from doc_engine.compiler import DEFAULT_PAPER, DEFAULT_TEMPLATE, PAPER_SIZES

# Words for the usual amounts of white space, so a document can ask for roomier
# or tighter pages without anyone measuring anything.
MARGINS = {"tight": "0.6in", "normal": "1in", "wide": "1.5in"}
ALIGNMENTS = ("justify", "left", "right", "center")

_MEASUREMENT = re.compile(r"^\d+(?:\.\d+)?\s*(?:pt|mm|cm|in|em)$", re.IGNORECASE)


def margin_length(value: str) -> str | None:
    """A Typst length for a margin written as a word or as a measurement."""
    cleaned = value.strip().lower()
    if cleaned in MARGINS:
        return MARGINS[cleaned]
    return cleaned.replace(" ", "") if _MEASUREMENT.match(cleaned) else None


class SettingsError(Exception):
    """An option whose value is not one this build understands."""


@dataclass(frozen=True)
class Resolved:
    template: str
    paper: str
    accent: str | None
    author: str | None
    bib: str | None
    pdf_standard: str | None
    code_theme: str | None
    branding: bool
    fetch_images: bool
    split_tall_images: bool
    toc: bool
    margin: str | None
    text_align: str | None
    warnings: tuple[str, ...] = ()


def _text(value: object) -> str | None:
    return str(value) if value else None


def resolve(
    flags: dict[str, object],
    front_matter: dict[str, str],
    project: dict[str, str],
    accent_lookup,
    template_lookup,
) -> Resolved:
    """Combine the three sources into the values a build runs with.

    *accent_lookup* and *template_lookup* turn a written value into a usable one
    and return None when it is not recognized, which keeps colour names and the
    template search out of this module.
    """
    warnings: list[str] = []

    def setting(name: str) -> str | None:
        return front_matter.get(name) or project.get(name)

    def flag(name: str):
        return flags.get(name)

    wanted_template = setting("template") or DEFAULT_TEMPLATE
    template = flag("template") or template_lookup(wanted_template)
    if template is None:
        raise SettingsError(f"Unknown template — {wanted_template}")

    paper = flag("paper")
    if paper:
        paper = str(paper).lower()
    elif setting("paper"):
        paper = str(setting("paper")).strip().lower()
        if paper not in PAPER_SIZES:
            raise SettingsError(f"Unknown paper size — {setting('paper')}")
    else:
        paper = DEFAULT_PAPER

    accent = flag("accent")
    if accent is None and setting("accent"):
        accent = accent_lookup(setting("accent"))
        if accent is None:
            warnings.append(f"Ignoring unknown accent — {setting('accent')}")

    standard = flag("pdf_standard") or setting("pdf_standard")

    margin = flag("margin") or setting("margin")
    if margin:
        measurement = margin_length(str(margin))
        if measurement is None:
            raise SettingsError(
                f"Unknown margin — {margin}. Use {', '.join(MARGINS)}, or a measurement "
                "such as 2cm."
            )
        margin = measurement

    alignment = flag("text_align") or setting("align")
    if alignment:
        alignment = str(alignment).strip().lower()
        if alignment not in ALIGNMENTS:
            raise SettingsError(f"Unknown alignment — {alignment}. Use {', '.join(ALIGNMENTS)}.")

    return Resolved(
        template=str(template),
        paper=paper,
        accent=accent if accent is None else str(accent),
        author=flag("author") or setting("author"),
        bib=flag("bib") or setting("bib"),
        pdf_standard=str(standard) if standard else None,
        code_theme=_text(flag("code_theme") or setting("code_theme")),
        branding=not flag("no_branding") and setting("branding") != "false",
        fetch_images=bool(flag("fetch_images")) or setting("fetch_images") == "true",
        split_tall_images=(
            str(flag("tall_images") or setting("tall_images") or "fit").lower() == "split"
        ),
        toc=not flag("no_toc") and setting("toc") != "false",
        margin=str(margin) if margin else None,
        text_align=str(alignment) if alignment else None,
        warnings=tuple(warnings),
    )
