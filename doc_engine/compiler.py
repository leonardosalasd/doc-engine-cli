import shutil
import tempfile
from pathlib import Path

import typst

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_THEMES_DIR = Path(__file__).parent / "themes"
DEFAULT_TEMPLATE = "academic"
DEFAULT_PAPER = "a4"


def available_themes() -> list[str]:
    """Syntax highlighting themes that ship with the package, sorted."""
    return sorted(path.stem for path in _THEMES_DIR.glob("*.tmTheme"))


def theme_path(name: str) -> Path:
    """Resolve a theme identifier, which is a bundled name or a path."""
    candidate = Path(name)
    if candidate.suffix == ".tmTheme":
        return candidate
    return _THEMES_DIR / f"{name}.tmTheme"


# Archival profiles typst-py accepts. a-2b is the usual choice for documents
# that have to be readable decades from now; a-3b additionally allows embedded
# attachments.
PDF_STANDARDS = ("a-2b", "a-3b")

PAPER_SIZES = (
    "a3",
    "a4",
    "a5",
    "a6",
    "iso-b5",
    "jis-b5",
    "us-legal",
    "us-letter",
    "us-tabloid",
)


def available_templates() -> list[str]:
    """Names of the templates that ship with the package, sorted."""
    return sorted(path.stem for path in _TEMPLATES_DIR.glob("*.typ"))


def template_path(name: str) -> Path:
    """Resolve a template identifier to a `.typ` file.

    A bare name refers to a bundled template; anything else is treated as a
    path to a user-supplied one.
    """
    candidate = Path(name)
    if candidate.suffix == ".typ":
        return candidate
    return _TEMPLATES_DIR / f"{name}.typ"


def compile_pdf(
    typst_body: str,
    title: str,
    author: str,
    output_path: str,
    bib_file: str | None = None,
    template: str = DEFAULT_TEMPLATE,
    accent: str | None = None,
    branding: bool = True,
    version: str = "",
    subtitle: str = "",
    date: str | None = None,
    assets: dict[str, str] | None = None,
    generated: dict[str, str] | None = None,
    paper: str = DEFAULT_PAPER,
    pdf_standard: str | None = None,
    code_theme: str | None = None,
) -> None:
    source = template_path(template)
    if not source.exists():
        raise FileNotFoundError(f"Unknown template: {template}")

    resolved_output = str(Path(output_path).resolve())

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "template.typ").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

        bib_inject = "none"
        if bib_file:
            bib_path = Path(bib_file)
            if bib_path.exists():
                shutil.copy(bib_path, tmp / bib_path.name)
                bib_inject = f'"{bib_path.name}"'

        for name, origin in (assets or {}).items():
            destination = tmp / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(origin, destination)

        for name, content in (generated or {}).items():
            destination = tmp / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")

        theme_inject = "none"
        if code_theme:
            theme = theme_path(code_theme)
            if theme.exists():
                shutil.copy(theme, tmp / theme.name)
                theme_inject = f'"{theme.name}"'

        accent_inject = f'rgb("{accent}")' if accent else "none"

        main_file = tmp / "main.typ"
        main_file.write_text(
            _build_main(
                typst_body,
                title,
                author,
                bib_inject,
                accent_inject,
                branding,
                version,
                subtitle,
                date,
                paper,
                theme_inject,
            ),
            encoding="utf-8",
        )

        if pdf_standard:
            typst.compile(str(main_file), output=resolved_output, pdf_standards=[pdf_standard])
        else:
            typst.compile(str(main_file), output=resolved_output)


# Pictures keep their natural size unless they do not fit the text block, in
# which case they shrink until they do. Forcing every image to full width blows
# up small diagrams, and constraining only the width lets a tall one run past
# the bottom of the page, where Typst clips whatever does not fit.
_FIT_IMAGE = """#let fit-image(path) = context layout(area => {
  let img = image(path)
  let natural = measure(img)
  let scale = calc.min(1.0, area.width / natural.width, area.height / natural.height)
  if scale >= 1.0 { img } else { image(path, width: natural.width * scale) }
})
"""


def _build_main(
    body: str,
    title: str,
    author: str,
    bib_inject: str,
    accent_inject: str,
    branding: bool,
    version: str,
    subtitle: str = "",
    date: str | None = None,
    paper: str = DEFAULT_PAPER,
    theme_inject: str = "none",
) -> str:
    theme_line = f"#set raw(theme: {theme_inject})\n" if theme_inject != "none" else ""
    date_line = f'  date: "{_escape(date)}",\n' if date else ""
    return (
        '#import "template.typ": setup_doc\n\n'
        f"{theme_line}"
        f"{_FIT_IMAGE}\n"
        "#show: setup_doc.with(\n"
        f'  title: "{_escape(title)}",\n'
        f'  subtitle: "{_escape(subtitle)}",\n'
        f'  author: "{_escape(author)}",\n'
        f"{date_line}"
        f"  bibliography_file: {bib_inject},\n"
        f"  accent: {accent_inject},\n"
        f"  branding: {'true' if branding else 'false'},\n"
        f'  version: "{version}",\n'
        f'  paper: "{paper}",\n'
        ")\n\n"
        f"{body}"
    )


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
