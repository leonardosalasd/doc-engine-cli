import tempfile
from pathlib import Path

import typst

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "report.typ"


def compile_pdf(
    typst_body: str,
    title: str,
    author: str,
    output_path: str,
) -> None:
    template_src = _TEMPLATE_PATH.read_text(encoding="utf-8")
    main_src = _build_main(typst_body, title, author)
    resolved_output = str(Path(output_path).resolve())

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "report.typ").write_text(template_src, encoding="utf-8")
        main_file = tmp / "main.typ"
        main_file.write_text(main_src, encoding="utf-8")

        typst.compile(str(main_file), output=resolved_output)


def _build_main(body: str, title: str, author: str) -> str:
    safe_title = title.replace('"', '\\"')
    safe_author = author.replace('"', '\\"')
    return (
        '#import "report.typ": setup_doc\n\n'
        "#show: setup_doc.with(\n"
        f'  title: "{safe_title}",\n'
        f'  author: "{safe_author}",\n'
        ")\n\n"
        f"{body}"
    )
