import pytest

from doc_engine import settings
from doc_engine.compiler import DEFAULT_PAPER, DEFAULT_TEMPLATE

ACCENTS = {"teal": "#0d9488", "rose": "#e11d48"}
TEMPLATES = ("academic", "report", "modern")


def resolve(flags=None, front_matter=None, project=None):
    return settings.resolve(
        flags=flags or {},
        front_matter=front_matter or {},
        project=project or {},
        accent_lookup=ACCENTS.get,
        template_lookup=lambda name: name if name in TEMPLATES else None,
    )


class TestDefaults:
    def test_nothing_set_uses_the_built_in_defaults(self) -> None:
        chosen = resolve()
        assert chosen.template == DEFAULT_TEMPLATE
        assert chosen.paper == DEFAULT_PAPER
        assert chosen.accent is None
        assert chosen.branding is True
        assert chosen.fetch_images is False
        assert chosen.split_tall_images is False


class TestPrecedence:
    """A flag beats front matter, which beats the project file."""

    def test_flag_wins_over_both(self) -> None:
        chosen = resolve(
            flags={"paper": "us-legal"},
            front_matter={"paper": "a5"},
            project={"paper": "a3"},
        )
        assert chosen.paper == "us-legal"

    def test_front_matter_wins_over_the_project_file(self) -> None:
        chosen = resolve(front_matter={"paper": "a5"}, project={"paper": "a3"})
        assert chosen.paper == "a5"

    def test_project_file_is_used_when_nothing_else_sets_it(self) -> None:
        assert resolve(project={"paper": "a3"}).paper == "a3"

    def test_each_option_is_decided_on_its_own(self) -> None:
        chosen = resolve(
            flags={"paper": "a5"},
            front_matter={"template": "report"},
            project={"author": "Team", "template": "modern"},
        )
        assert chosen.paper == "a5"
        assert chosen.template == "report"
        assert chosen.author == "Team"


class TestTemplate:
    def test_unknown_template_is_an_error(self) -> None:
        with pytest.raises(settings.SettingsError, match="Unknown template"):
            resolve(front_matter={"template": "nonsense"})

    def test_a_flag_is_taken_as_already_resolved(self) -> None:
        assert resolve(flags={"template": "/tmp/mine.typ"}).template == "/tmp/mine.typ"


class TestPaper:
    def test_case_is_ignored(self) -> None:
        assert resolve(front_matter={"paper": "A5"}).paper == "a5"

    def test_unknown_size_is_an_error(self) -> None:
        with pytest.raises(settings.SettingsError, match="Unknown paper size"):
            resolve(front_matter={"paper": "tabloid-xl"})

    def test_a_flag_is_not_second_guessed(self) -> None:
        assert resolve(flags={"paper": "US-LETTER"}).paper == "us-letter"


class TestAccent:
    def test_name_is_looked_up(self) -> None:
        assert resolve(front_matter={"accent": "teal"}).accent == "#0d9488"

    def test_unknown_name_warns_rather_than_failing(self) -> None:
        chosen = resolve(front_matter={"accent": "banana"})
        assert chosen.accent is None
        assert any("banana" in warning for warning in chosen.warnings)


class TestBooleans:
    def test_branding_is_switched_off_by_the_flag(self) -> None:
        assert resolve(flags={"no_branding": True}).branding is False

    def test_branding_is_switched_off_by_the_project_file(self) -> None:
        assert resolve(project={"branding": "false"}).branding is False

    def test_fetching_is_opt_in(self) -> None:
        assert resolve().fetch_images is False
        assert resolve(flags={"fetch_images": True}).fetch_images is True
        assert resolve(project={"fetch_images": "true"}).fetch_images is True

    def test_tall_images_split_only_when_asked(self) -> None:
        assert resolve(flags={"tall_images": "fit"}).split_tall_images is False
        assert resolve(flags={"tall_images": "split"}).split_tall_images is True
        assert resolve(project={"tall_images": "split"}).split_tall_images is True
