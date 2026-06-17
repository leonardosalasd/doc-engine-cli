from doc_engine.linter import has_errors, lint


class TestEmptyLinks:
    def test_empty_link_url_is_error(self) -> None:
        issues = lint("See [the docs]() for details.")
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert issues[0].line == 1
        assert "URL must not be empty" in issues[0].message

    def test_column_points_at_the_link(self) -> None:
        issues = lint("ok [bad]() here")
        assert issues[0].column == 4

    def test_whitespace_only_url_is_error(self) -> None:
        assert has_errors(lint("[x](   )"))

    def test_filled_link_is_fine(self) -> None:
        assert lint("[docs](https://example.com)") == []

    def test_empty_image_is_a_warning(self) -> None:
        issues = lint("![alt]()")
        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert not has_errors(issues)


class TestFences:
    def test_unclosed_fence_is_error(self) -> None:
        issues = lint("# Title\n\n```python\nprint('hi')\n")
        assert any(i.message == "unclosed fenced code block" for i in issues)

    def test_closed_fence_is_fine(self) -> None:
        assert lint("```\ncode\n```") == []

    def test_links_inside_fences_are_ignored(self) -> None:
        assert lint("```\n[x]()\n```") == []


class TestFormatting:
    def test_format_matches_file_line_col(self) -> None:
        issue = lint("[x]()")[0]
        assert issue.format("file.md") == "file.md:1:1: error: link URL must not be empty"
