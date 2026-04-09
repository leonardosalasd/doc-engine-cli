from doc_engine.converter import convert, extract_title, strip_first_heading


class TestEscaping:
    def test_hash_is_escaped(self) -> None:
        assert "\\#" in convert("Use C# for development")

    def test_dollar_is_escaped(self) -> None:
        assert "\\$" in convert("Price is $10")

    def test_at_is_escaped(self) -> None:
        assert "\\@" in convert("Email user@example.com")


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
