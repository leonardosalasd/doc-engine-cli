from PIL import Image

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


def test_a_requested_image_size_compiles(tmp_path):
    assets = tmp_path / "assets"
    assets.mkdir()
    Image.new("RGB", (600, 300), "blue").save(assets / "box.png")
    output = tmp_path / "sized.pdf"
    compile_pdf(
        '#fit-image("assets/box.png", width: 150pt)\n\n'
        '#fit-image("assets/box.png", height: 25.5pt)\n\n'
        '#fit-image("assets/box.png", width: 1500pt)\n',
        "Sizes",
        "Author",
        str(output),
        assets={"assets/box.png": str(assets / "box.png")},
    )
    assert output.read_bytes().startswith(b"%PDF-")
