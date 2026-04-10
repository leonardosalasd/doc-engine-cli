import shutil
import tempfile
from pathlib import Path

import typst

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "report.typ"


def compile_pdf(
    typst_body: str,
    title: str,
    author: str,
    output_path: str,
    bib_file: str | None = None,
) -> None:
    resolved_output = str(Path(output_path).resolve())

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "report.typ").write_text(_TEMPLATE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        
        main_file = tmp / "main.typ"
        bib_inject = "none"
        
        if bib_file:
            bib_path = Path(bib_file)
            if bib_path.exists():
                shutil.copy(bib_path, tmp / bib_path.name)
                bib_inject = f'"{bib_path.name}"'
                
        main_src = _build_main(typst_body, title, author, bib_inject)
        main_file.write_text(main_src, encoding="utf-8")

        typst.compile(str(main_file), output=resolved_output)


def _build_main(body: str, title: str, author: str, bib_inject: str) -> str:
    safe_title = title.replace('"', '\\"')
    safe_author = author.replace('"', '\\"')
    return (
        '#import "report.typ": setup_doc\n\n'
        "#show: setup_doc.with(\n"
        f'  title: "{safe_title}",\n'
        f'  author: "{safe_author}",\n'
        f"  bibliography_file: {bib_inject},\n"
        ")\n\n"
        f"{body}"
    )
