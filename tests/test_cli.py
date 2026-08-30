from pathlib import Path

from click.testing import CliRunner

from doc_engine import __version__
from doc_engine.cli import _unique_path, cli
from doc_engine.compiler import _build_main, available_templates


class TestTemplates:
    def test_ships_expected_templates(self) -> None:
        names = available_templates()
        for expected in ("academic", "article", "book", "minimal", "modern", "report", "technical"):
            assert expected in names

    def test_every_template_accepts_the_documented_options(self) -> None:
        """A template that drops an option would fail only at compile time."""
        from doc_engine.compiler import template_path

        for name in available_templates():
            source = template_path(name).read_text(encoding="utf-8")
            for option in ("title:", "subtitle:", "author:", "paper:", "accent:", "branding:"):
                assert option in source, f"{name} is missing {option}"
            assert "..options" in source, f"{name} has no options sink"

    def test_build_main_injects_options(self) -> None:
        main = _build_main("body", "Title", "Me", "none", 'rgb("#ff0000")', False, "1.0.0")
        assert 'accent: rgb("#ff0000")' in main
        assert "branding: false" in main
        assert 'version: "1.0.0"' in main

    def test_build_main_injects_subtitle_and_date(self) -> None:
        main = _build_main(
            "body", "T", "Me", "none", "none", True, "1.0.0", "A subtitle", "2026-07-28"
        )
        assert 'subtitle: "A subtitle"' in main
        assert 'date: "2026-07-28"' in main

    def test_build_main_omits_absent_date(self) -> None:
        assert "date:" not in _build_main("body", "T", "Me", "none", "none", True, "1.0.0")

    def test_custom_template_path_is_rejected_when_missing(self, tmp_path) -> None:
        doc = tmp_path / "doc.md"
        doc.write_text("# T\n\nText.\n")
        result = CliRunner().invoke(
            cli, ["build", str(doc), "--template", "missing.typ", "--dry-run"]
        )
        assert result.exit_code == 2


class TestPaper:
    def test_build_main_injects_paper(self) -> None:
        main = _build_main("body", "T", "Me", "none", "none", True, "2.0.0", "", None, "a5")
        assert 'paper: "a5"' in main

    def test_invalid_paper_flag_is_rejected(self, tmp_path) -> None:
        doc = tmp_path / "doc.md"
        doc.write_text("# T\n\nText.\n")
        result = CliRunner().invoke(cli, ["build", str(doc), "--paper", "banana", "--dry-run"])
        assert result.exit_code == 2


class TestUniquePath:
    def test_returns_same_when_absent(self, tmp_path) -> None:
        target = tmp_path / "out.pdf"
        assert _unique_path(target) == target

    def test_increments_when_present(self, tmp_path) -> None:
        (tmp_path / "out.pdf").write_text("x")
        assert _unique_path(tmp_path / "out.pdf").name == "out (1).pdf"

    def test_skips_taken_indexes(self, tmp_path) -> None:
        (tmp_path / "out.pdf").write_text("x")
        (tmp_path / "out (1).pdf").write_text("x")
        assert _unique_path(tmp_path / "out.pdf").name == "out (2).pdf"


class TestInfo:
    def test_info_shows_version_and_repo(self) -> None:
        result = CliRunner().invoke(cli, ["info"])
        assert result.exit_code == 0
        assert __version__ in result.output
        assert "github.com/leonardosalasd/doc-engine-cli" in result.output


class TestVersion:
    def test_version_flag(self) -> None:
        result = CliRunner().invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output


class TestDryRun:
    def test_dry_run_reports_errors(self, tmp_path) -> None:
        bad = tmp_path / "doc.md"
        bad.write_text("# T\n\nA [broken]() link.\n")
        result = CliRunner().invoke(cli, ["build", str(bad), "--dry-run"])
        assert result.exit_code == 1
        assert "link URL must not be empty" in " ".join(result.output.split())

    def test_dry_run_clean_file(self, tmp_path) -> None:
        good = tmp_path / "doc.md"
        good.write_text("# T\n\nAll good here.\n")
        result = CliRunner().invoke(cli, ["build", str(good), "--dry-run"])
        assert result.exit_code == 0
        assert "No issues found" in result.output


class TestAccentValidation:
    def test_named_accent_is_accepted(self, tmp_path) -> None:
        good = tmp_path / "doc.md"
        good.write_text("# T\n\nText.\n")
        result = CliRunner().invoke(cli, ["build", str(good), "--accent", "teal", "--dry-run"])
        assert result.exit_code == 0

    def test_invalid_accent_is_rejected(self, tmp_path) -> None:
        good = tmp_path / "doc.md"
        good.write_text("# T\n\nText.\n")
        result = CliRunner().invoke(cli, ["build", str(good), "--accent", "banana", "--dry-run"])
        assert result.exit_code == 2

    def test_invalid_template_is_rejected(self, tmp_path) -> None:
        good = tmp_path / "doc.md"
        good.write_text("# T\n\nText.\n")
        result = CliRunner().invoke(cli, ["build", str(good), "--template", "nope", "--dry-run"])
        assert result.exit_code == 2


class TestHelp:
    def test_top_level_help_lists_build_options(self) -> None:
        result = CliRunner().invoke(cli, ["--help"])
        assert result.exit_code == 0
        for expected in ("--template", "--accent", "--paper", "--watch"):
            assert expected in result.output

    def test_top_level_help_groups_options(self) -> None:
        result = CliRunner().invoke(cli, ["--help"])
        for heading in ("Input and output", "Document details", "Appearance"):
            assert heading in result.output

    def test_top_level_help_shows_examples_and_commands(self) -> None:
        result = CliRunner().invoke(cli, ["--help"])
        assert "Examples" in result.output
        assert "doc-engine info" in result.output

    def test_build_help_still_works(self) -> None:
        result = CliRunner().invoke(cli, ["build", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output

    def test_bare_invocation_shows_help(self) -> None:
        result = CliRunner().invoke(cli, [])
        assert result.exit_code == 0
        assert "Usage" in result.output

    def test_info_lists_capabilities(self) -> None:
        result = CliRunner().invoke(cli, ["info"])
        flat = " ".join(result.output.split())
        assert "mermaid" in flat
        assert "math" in flat.lower()


class TestCodeThemes:
    def test_ships_expected_themes(self) -> None:
        from doc_engine.compiler import available_themes

        for expected in ("github", "monochrome", "solarized"):
            assert expected in available_themes()

    def test_bundled_name_resolves_to_a_file(self) -> None:
        from doc_engine.compiler import available_themes, theme_path

        for name in available_themes():
            assert theme_path(name).is_file()

    def test_a_path_is_taken_as_given(self) -> None:
        from doc_engine.compiler import theme_path

        assert theme_path("/tmp/mine.tmTheme") == Path("/tmp/mine.tmTheme")

    def test_theme_is_injected_when_asked(self) -> None:
        main = _build_main(
            "body", "T", "Me", "none", "none", True, "2.0.0", "", None, "a4", '"github.tmTheme"'
        )
        assert 'set raw(theme: "github.tmTheme")' in main

    def test_no_theme_leaves_highlighting_alone(self) -> None:
        assert "set raw" not in _build_main("body", "T", "Me", "none", "none", True, "2.0.0")


class TestOpening:
    """--open hands the file to the platform's viewer."""

    def test_uses_the_right_command_per_platform(self, monkeypatch) -> None:
        from doc_engine import cli as cli_module

        calls: list[list[str]] = []
        monkeypatch.setattr(cli_module.subprocess, "run", lambda cmd, **kw: calls.append(cmd))

        for platform, expected in (("darwin", "open"), ("linux", "xdg-open")):
            calls.clear()
            monkeypatch.setattr(cli_module.sys, "platform", platform)
            cli_module._open_file("out.pdf")
            assert calls == [[expected, "out.pdf"]]

    def test_windows_uses_startfile(self, monkeypatch) -> None:
        from doc_engine import cli as cli_module

        opened: list[str] = []
        monkeypatch.setattr(cli_module.sys, "platform", "win32")
        monkeypatch.setattr(cli_module.os, "startfile", opened.append, raising=False)
        cli_module._open_file("out.pdf")
        assert opened == ["out.pdf"]
