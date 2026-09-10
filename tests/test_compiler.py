from doc_engine.compiler import compile_pdf


def test_formatted_title_keeps_custom_template_contract(tmp_path):
    template = tmp_path / "custom.typ"
    template.write_text(
        '#let setup_doc(title: "", subtitle: "", author: "", '
        'bibliography_file: none, accent: none, branding: true, version: "", '
        'paper: "a4", body) = { title; body }',
        encoding="utf-8",
    )
    output = tmp_path / "custom.pdf"
    compile_pdf(
        "Body",
        "Bold Title",
        "Author",
        str(output),
        template=str(template),
        title_markup="*Bold* Title",
    )
    assert output.read_bytes().startswith(b"%PDF-")
