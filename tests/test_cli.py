from click.testing import CliRunner

from doc_engine import __version__
from doc_engine.cli import cli
from doc_engine.compiler import _build_main, available_templates


class TestTemplates:
    def test_ships_expected_templates(self) -> None:
        names = available_templates()
        for expected in ("academic", "modern", "minimal", "technical", "book"):
            assert expected in names

    def test_build_main_injects_options(self) -> None:
        main = _build_main("body", "Title", "Me", "none", 'rgb("#ff0000")', False, "1.0.0")
        assert 'accent: rgb("#ff0000")' in main
        assert "branding: false" in main
        assert 'version: "1.0.0"' in main


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
