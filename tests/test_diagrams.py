import pytest

from doc_engine import diagrams
from doc_engine.converter import convert_document


class TestDetection:
    def test_diagram_languages_are_recognized(self) -> None:
        for language in ("mermaid", "mmd", "svg", "SVG", "Mermaid"):
            assert diagrams.is_diagram(language)

    def test_other_languages_are_not(self) -> None:
        for language in ("python", "bash", "", "json"):
            assert not diagrams.is_diagram(language)


class TestSvg:
    def test_svg_passes_through(self) -> None:
        source = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
        assert diagrams.render("svg", source) == source


class TestMermaid:
    def test_renders_to_svg(self) -> None:
        svg = diagrams.render("mermaid", "flowchart TD\n A-->B\n")
        assert svg.lstrip().startswith("<svg") or "<svg" in svg[:200]

    def test_invalid_source_raises_with_a_readable_message(self) -> None:
        with pytest.raises(diagrams.DiagramError) as caught:
            diagrams.render("mermaid", "flowchart TD\n A --> ((( broken")
        assert caught.value.language == "mermaid"
        assert "Mermaid rendering failed" not in caught.value.message
        assert caught.value.message


class TestConversion:
    def test_mermaid_block_becomes_a_picture(self) -> None:
        conversion = convert_document("```mermaid\nflowchart TD\n A-->B\n```\n")
        name = next(iter(conversion.generated))
        assert f'#fit-image("{name}")' in conversion.body
        assert "<svg" in conversion.generated[name]

    def test_svg_block_becomes_a_picture(self) -> None:
        source = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'
        conversion = convert_document(f"```svg\n{source}\n```\n")
        name = next(iter(conversion.generated))
        assert conversion.generated[name].strip() == source

    def test_ordinary_code_is_left_alone(self) -> None:
        conversion = convert_document("```python\nprint('hi')\n```\n")
        assert conversion.generated == {}
        assert "```python" in conversion.body

    def test_several_diagrams_get_distinct_names(self) -> None:
        conversion = convert_document(
            "```mermaid\nflowchart TD\n A-->B\n```\n\n```mermaid\nflowchart TD\n C-->D\n```\n"
        )
        assert len(conversion.generated) == 2
