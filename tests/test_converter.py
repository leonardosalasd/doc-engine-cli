from doc_engine.converter import (
    TypstRenderer,
    convert,
    convert_document,
    extract_title,
    extract_title_markup,
    strip_first_heading,
)


class TestPythonCompatibility:
    """Guards the regression that made 1.1.0 unimportable below Python 3.14."""

    def test_class_body_annotations_are_not_evaluated(self) -> None:
        annotations = TypstRenderer.load_footnotes.__annotations__
        assert annotations["tokens"] == "list[dict]"

    def test_list_is_shadowed_inside_the_class(self) -> None:
        assert callable(TypstRenderer.list)


class TestEscaping:
    def test_hash_is_escaped(self) -> None:
        assert "\\#" in convert("Use C# for development")

    def test_dollar_is_escaped(self) -> None:
        assert "\\$" in convert("Price is $10")

    def test_at_is_escaped(self) -> None:
        assert "\\@" in convert("Email user@example.com")


class TestBrackets:
    def test_square_brackets_are_escaped(self) -> None:
        assert "\\[42\\]" in convert("See item [42] here.")

    def test_lone_closing_bracket_is_escaped(self) -> None:
        assert "\\]" in convert("Close it with ] here.")


class TestCitations:
    def test_pandoc_citation_becomes_typst_reference(self) -> None:
        assert "@smith2020" in convert("As shown in [@smith2020].")

    def test_citation_loses_its_brackets(self) -> None:
        assert "\\[" not in convert("As shown in [@smith2020].")


class TestExtractTitle:
    def test_simple_title(self) -> None:
        assert extract_title("# My Project\n\nDescription") == "My Project"

    def test_fallback_when_missing(self) -> None:
        assert extract_title("No heading here") == "Documentation"

    def test_ignores_h2(self) -> None:
        assert extract_title("## Subtitle\n\nText") == "Documentation"


class TestStripFirstHeading:
    def test_removes_h1(self) -> None:
        md = "# Title\n\nContent here"
        result = strip_first_heading(md)
        assert "# Title" not in result
        assert "Content here" in result

    def test_preserves_h2(self) -> None:
        md = "## Subtitle\n\nBody"
        assert strip_first_heading(md) == md

    def test_keeps_comments_inside_fenced_code(self) -> None:
        md = "```bash\n# install\npipx install doc-engine-cli\n```\n\n# Title\n\nBody"
        result = strip_first_heading(md)
        assert "# install" in result
        assert "# Title" not in result

    def test_removes_an_underlined_h1(self) -> None:
        md = "Title\n=====\n\nBody"
        result = strip_first_heading(md)
        assert "Title" not in result
        assert "Body" in result

    def test_removes_what_the_title_promotes(self) -> None:
        md = "```\n# fake\n```\n\nReal\n====\n\nBody"
        assert extract_title(md) == "Real"
        assert "Real" not in strip_first_heading(md)


class TestConvert:
    def test_heading_levels(self) -> None:
        assert "= Hello" in convert("# Hello")
        assert "== Sub" in convert("## Sub")
        assert "=== Deep" in convert("### Deep")

    def test_bold(self) -> None:
        result = convert("This is **bold** text")
        assert "*bold*" in result

    def test_italic(self) -> None:
        result = convert("This is *italic* text")
        assert "_italic_" in result

    def test_inline_code(self) -> None:
        result = convert("Use `pip install`")
        assert "`pip install`" in result

    def test_code_block(self) -> None:
        md = "```python\nprint('hi')\n```"
        result = convert(md)
        assert "```python" in result

    def test_link(self) -> None:
        result = convert("[click here](https://example.com)")
        assert '#link("https://example.com")' in result

    def test_unordered_list(self) -> None:
        result = convert("- item one\n- item two")
        assert "- item one" in result
        assert "- item two" in result

    def test_ordered_list(self) -> None:
        result = convert("1. first\n2. second")
        assert "+ first" in result
        assert "+ second" in result

    def test_blockquote(self) -> None:
        result = convert("> Important note")
        assert "#block(" in result

    def test_thematic_break(self) -> None:
        result = convert("---")
        assert "#line(" in result

    def test_empty_input(self) -> None:
        assert convert("") == ""


class TestTaskLists:
    def test_checked_and_unchecked_render_boxes(self) -> None:
        result = convert("- [x] done\n- [ ] todo\n")
        assert 'fill: rgb("#16a34a")' in result
        assert 'stroke: 1pt + rgb("#94a3b8")' in result
        assert "done" in result
        assert "todo" in result


class TestFootnotes:
    def test_reference_becomes_inline_footnote(self) -> None:
        result = convert("A claim[^1].\n\n[^1]: The evidence.\n")
        assert "#footnote[The evidence.]" in result

    def test_definition_block_is_dropped(self) -> None:
        result = convert("A claim[^1].\n\n[^1]: The evidence.\n")
        assert result.count("The evidence.") == 1


class TestHtmlImages:
    def test_block_image_is_embedded(self, tmp_path) -> None:
        (tmp_path / "logo.png").write_bytes(b"image")
        result = convert_document('<img src="logo.png">', base_dir=tmp_path)
        assert len(result.assets) == 1
        assert f'#fit-image("{next(iter(result.assets))}")' in result.body

    def test_inline_image_preserves_surrounding_text(self, tmp_path) -> None:
        (tmp_path / "logo.png").write_bytes(b"image")
        result = convert_document('Before <img src="logo.png" /> after.', base_dir=tmp_path)
        assert len(result.assets) == 1
        assert result.body.startswith("Before #fit-image(")
        assert " after." in result.body

    def test_wrapped_images_share_markdown_assets(self, tmp_path) -> None:
        for name in ("one.png", "two.png"):
            (tmp_path / name).write_bytes(b"image")
        result = convert_document(
            '<div>\n<img src="one.png"><img src="two.png">\n</div>\n\n![again](one.png)',
            base_dir=tmp_path,
        )
        assert len(result.assets) == 2
        first, second = result.assets
        assert result.body.index(first) < result.body.index(second)
        assert result.body.count(first) == 2

    def test_attribute_case_quotes_and_entities(self, tmp_path) -> None:
        (tmp_path / "a&b.png").write_bytes(b"image")
        result = convert_document("<IMG SRC='a&amp;b.png' ALT='logo' />", base_dir=tmp_path)
        assert len(result.assets) == 1
        assert next(iter(result.assets.values())).endswith("a&b.png")

    def test_missing_image_uses_escaped_alt(self, tmp_path) -> None:
        result = convert_document('<img src="missing.png" alt="A &amp; *B*">', base_dir=tmp_path)
        assert not result.assets
        assert r"[A & \*B\*]" in result.body

    def test_remote_images_require_opt_in(self, tmp_path, monkeypatch) -> None:
        def unexpected_fetch(*args):
            raise AssertionError("remote fetch was not enabled")

        monkeypatch.setattr("doc_engine.converter.remote.fetch", unexpected_fetch)
        result = convert_document(
            '<img src="https://example.test/a.png" alt="remote">', base_dir=tmp_path
        )
        assert not result.assets
        assert "[remote]" in result.body

    def test_remote_image_reuses_enabled_fetch(self, tmp_path, monkeypatch) -> None:
        image = tmp_path / "download.png"
        image.write_bytes(b"image")
        calls = []

        def fetch(url, destination):
            calls.append((url, destination))
            return image

        monkeypatch.setattr("doc_engine.converter.remote.fetch", fetch)
        result = convert_document(
            '<img src="https://example.test/a.png">',
            base_dir=tmp_path,
            work_dir=tmp_path,
            fetch_remote=True,
        )
        assert len(result.assets) == 1
        assert calls == [("https://example.test/a.png", tmp_path)]

    def test_comments_and_script_content_are_not_images(self, tmp_path) -> None:
        (tmp_path / "logo.png").write_bytes(b"image")
        result = convert_document(
            '<!-- <img src="logo.png"> -->\n\n<script>"<img src=logo.png>"</script>',
            base_dir=tmp_path,
        )
        assert not result.assets
        assert "#fit-image" not in result.body

    def test_missing_src_and_existing_linebreak_behavior(self) -> None:
        assert "[missing]" in convert('<img alt="missing">')
        assert convert("a<br>b") == "a\\\nb\n\n"


class TestImages:
    def test_local_image_is_embedded(self, tmp_path) -> None:
        (tmp_path / "logo.png").write_bytes(b"\x89PNG\r\n")
        conversion = convert_document("![logo](logo.png)", base_dir=tmp_path)
        name = next(iter(conversion.assets))
        assert f'#fit-image("{name}")' in conversion.body
        assert conversion.assets[name].endswith("logo.png")

    def test_repeated_image_is_registered_once(self, tmp_path) -> None:
        (tmp_path / "logo.png").write_bytes(b"\x89PNG\r\n")
        conversion = convert_document("![a](logo.png) ![b](logo.png)", base_dir=tmp_path)
        assert len(conversion.assets) == 1

    def test_remote_image_falls_back_to_alt(self, tmp_path) -> None:
        conversion = convert_document("![alt](https://x.test/a.png)", base_dir=tmp_path)
        assert conversion.assets == {}
        assert "[alt]" in conversion.body

    def test_missing_image_falls_back_to_alt(self, tmp_path) -> None:
        conversion = convert_document("![alt](nope.png)", base_dir=tmp_path)
        assert conversion.assets == {}
        assert "[alt]" in conversion.body


class TestTables:
    def test_all_header_columns_are_kept(self) -> None:
        result = convert("| A | B | C |\n|---|---|---|\n| 1 | 2 | 3 |\n")
        assert "columns: (1fr, 1fr, 1fr)" in result
        for header in ("[*A*]", "[*B*]", "[*C*]"):
            assert header in result

    def test_body_cells_follow_the_header(self) -> None:
        result = convert("| A | B |\n|---|---|\n| 1 | 2 |\n")
        assert "columns: (1fr, 1fr)" in result
        assert "[1]" in result and "[2]" in result

    def test_single_column_table(self) -> None:
        result = convert("| Only |\n|---|\n| one |\n")
        assert "columns: (1fr)" in result


class TestAlerts:
    """GitHub-style callouts: > [!NOTE] and friends."""

    def test_note_becomes_a_labelled_callout(self) -> None:
        result = convert("> [!NOTE]\n> Something worth knowing.\n")
        assert "Note" in result
        assert "#0969da" in result
        assert "!NOTE" not in result

    def test_every_kind_is_recognized(self) -> None:
        for kind, label in (
            ("NOTE", "Note"),
            ("TIP", "Tip"),
            ("IMPORTANT", "Important"),
            ("WARNING", "Warning"),
            ("CAUTION", "Caution"),
        ):
            result = convert(f"> [!{kind}]\n> Body.\n")
            assert f"[{label}]" in result
            assert "Body." in result

    def test_lowercase_marker_still_works(self) -> None:
        assert "Note" in convert("> [!note]\n> Body.\n")

    def test_each_kind_has_its_own_colour(self) -> None:
        colours = {
            convert(f"> [!{kind}]\n> Body.\n").split('rgb("')[1][:7]
            for kind in ("NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION")
        }
        assert len(colours) == 5

    def test_a_plain_quote_is_left_alone(self) -> None:
        result = convert("> Just a quote.\n")
        assert "Just a quote." in result
        assert "Note" not in result

    def test_a_bracket_that_is_not_an_alert_is_left_alone(self) -> None:
        result = convert("> [!MADEUP]\n> Body.\n")
        assert "MADEUP" in result

    def test_body_keeps_its_formatting(self) -> None:
        result = convert("> [!TIP]\n> Use **bold** and `code`.\n")
        assert "*bold*" in result
        assert "`code`" in result


class TestFormattedTitle:
    def test_title_uses_body_plugins_and_citations(self) -> None:
        for inline in ("~~struck~~ title", "The $x^2$ theorem", "Result [@smith2020]"):
            assert extract_title_markup(f"# {inline}") == convert(f"# {inline}").strip()[2:]

    def test_plugin_metadata_is_plain(self) -> None:
        assert extract_title("# ~~Old~~ $x^2$ result") == "Old x^2 result"

    def test_reference_links_use_document_definitions(self) -> None:
        result = extract_title_markup("# [Guide][ref]\n\n[ref]: https://example.com")
        assert result == '#link("https://example.com")[Guide]'

    def test_metadata_uses_plain_text(self) -> None:
        assert extract_title("# **Document** *Title*") == "Document Title"

    def test_display_preserves_emphasis(self) -> None:
        assert extract_title_markup("# **Document** *Title*") == "*Document* _Title_"

    def test_literal_markers_survive(self) -> None:
        assert extract_title(r"# \*literal\* and `code_name`") == "*literal* and code_name"
        assert (
            extract_title_markup(r"# \*literal\* and `code_name`") == r"\*literal\* and `code_name`"
        )

    def test_nested_formatting(self) -> None:
        assert extract_title("# **Bold and *italic***") == "Bold and italic"
        assert extract_title_markup("# **Bold and *italic***") == "*Bold and _italic_*"

    def test_missing_heading_has_no_markup(self) -> None:
        assert extract_title_markup("## Body heading") is None
