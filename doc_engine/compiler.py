import shutil
import tempfile
from pathlib import Path

import typst

_TEMPLATES_DIR = Path(__file__).parent / "templates"
DEFAULT_TEMPLATE = "academic"


def available_templates() -> list[str]:
    """Names of the templates that ship with the package, sorted."""
    return sorted(path.stem for path in _TEMPLATES_DIR.glob("*.typ"))


def template_path(name: str) -> Path:
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

        accent_inject = f'rgb("{accent}")' if accent else "none"

        main_file = tmp / "main.typ"
        main_file.write_text(
            _build_main(typst_body, title, author, bib_inject, accent_inject, branding, version),
            encoding="utf-8",
        )

        typst.compile(str(main_file), output=resolved_output)


def _build_main(
    body: str,
    title: str,
    author: str,
    bib_inject: str,
    accent_inject: str,
    branding: bool,
    version: str,
) -> str:
    safe_title = title.replace('"', '\\"')
    safe_author = author.replace('"', '\\"')
    return (
        '#import "template.typ": setup_doc\n\n'
        "#show: setup_doc.with(\n"
        f'  title: "{safe_title}",\n'
        f'  author: "{safe_author}",\n'
        f"  bibliography_file: {bib_inject},\n"
        f"  accent: {accent_inject},\n"
        f"  branding: {'true' if branding else 'false'},\n"
        f'  version: "{version}",\n'
        ")\n\n"
        f"{body}"
    )
