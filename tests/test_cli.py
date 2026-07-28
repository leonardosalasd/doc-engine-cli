from click.testing import CliRunner

from doc_engine import __version__
from doc_engine.cli import _unique_path, cli
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

    def test_build_main_injects_subtitle_and_date(self) -> None:
        main = _build_main("body", "T", "Me", "none", "none", True, "1.0.0", "A subtitle", "2026-07-28")
        assert 'subtitle: "A subtitle"' in main
        assert 'date: "2026-07-28"' in main

    def test_build_main_omits_absent_date(self) -> None:
        assert "date:" not in _build_main("body", "T", "Me", "none", "none", True, "1.0.0")

    def test_custom_template_path_is_rejected_when_missing(self, tmp_path) -> None:
        doc = tmp_path / "doc.md"
        doc.write_text("# T\n\nText.\n")
        result = CliRunner().invoke(cli, ["build", str(doc), "--template", "missing.typ", "--dry-run"])
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
