from doc_engine import frontmatter


class TestParse:
    def test_reads_key_values(self) -> None:
        meta, body = frontmatter.parse("---\ntitle: Hello\nauthor: Ada\n---\n\nBody\n")
        assert meta == {"title": "Hello", "author": "Ada"}
        assert body == "Body"

    def test_no_front_matter_is_untouched(self) -> None:
        text = "# Title\n\nBody\n"
        meta, body = frontmatter.parse(text)
        assert meta == {}
        assert body == text

    def test_quotes_are_stripped(self) -> None:
        meta, _ = frontmatter.parse('---\ntitle: "Quoted: value"\n---\nx')
        assert meta["title"] == "Quoted: value"

    def test_keys_are_lowercased(self) -> None:
        meta, _ = frontmatter.parse("---\nTitle: X\n---\ny")
        assert meta["title"] == "X"

    def test_unterminated_block_is_ignored(self) -> None:
        text = "---\ntitle: X\n\nno closing fence\n"
        meta, body = frontmatter.parse(text)
        assert meta == {}
        assert body == text
