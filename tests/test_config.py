import pytest

from doc_engine import config

if config.tomllib is None:  # pragma: no cover - only on 3.10 without tomli
    pytest.skip("no TOML parser available", allow_module_level=True)


class TestDedicatedFile:
    def test_reads_known_keys(self, tmp_path) -> None:
        (tmp_path / ".doc-engine.toml").write_text(
            '[doc-engine]\ntemplate = "report"\naccent = "teal"\n'
        )
        assert config.load(tmp_path) == {"template": "report", "accent": "teal"}

    def test_unknown_keys_are_ignored(self, tmp_path) -> None:
        (tmp_path / ".doc-engine.toml").write_text(
            '[doc-engine]\ntemplate = "report"\ntemplat = "typo"\nnonsense = 1\n'
        )
        assert config.load(tmp_path) == {"template": "report"}

    def test_booleans_become_strings(self, tmp_path) -> None:
        (tmp_path / ".doc-engine.toml").write_text("[doc-engine]\nbranding = false\n")
        assert config.load(tmp_path) == {"branding": "false"}

    def test_underscore_table_name_also_works(self, tmp_path) -> None:
        (tmp_path / ".doc-engine.toml").write_text('[doc_engine]\npaper = "a5"\n')
        assert config.load(tmp_path) == {"paper": "a5"}

    def test_broken_file_is_reported(self, tmp_path) -> None:
        (tmp_path / ".doc-engine.toml").write_text("[doc-engine\nbroken\n")
        with pytest.raises(config.ConfigError):
            config.load(tmp_path)


class TestPyproject:
    def test_reads_the_tool_table(self, tmp_path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "x"\n\n[tool.doc-engine]\npaper = "us-letter"\n'
        )
        assert config.load(tmp_path) == {"paper": "us-letter"}

    def test_dedicated_file_wins(self, tmp_path) -> None:
        (tmp_path / "pyproject.toml").write_text('[tool.doc-engine]\npaper = "a3"\n')
        (tmp_path / ".doc-engine.toml").write_text('[doc-engine]\npaper = "a5"\n')
        assert config.load(tmp_path) == {"paper": "a5"}

    def test_pyproject_without_the_table_is_empty(self, tmp_path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n')
        assert config.load(tmp_path) == {}


class TestAbsent:
    def test_no_files_means_no_settings(self, tmp_path) -> None:
        assert config.load(tmp_path) == {}
