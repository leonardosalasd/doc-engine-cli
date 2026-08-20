import pytest

from doc_engine import remote
from doc_engine.converter import convert_document


class TestSchemes:
    @pytest.mark.parametrize("url", ["ftp://x.test/a.png", "file:///etc/passwd", "gopher://x/a"])
    def test_only_http_is_fetched(self, url: str, tmp_path) -> None:
        with pytest.raises(remote.DownloadError, match="http"):
            remote.fetch(url, tmp_path)


class TestSuffix:
    def test_known_image_extension_is_accepted(self) -> None:
        assert remote._suffix_from("https://x.test/a/b.png") == ".png"

    def test_query_string_does_not_confuse_it(self) -> None:
        assert remote._suffix_from("https://x.test/a.svg?v=2") == ".svg"

    def test_non_image_extension_is_rejected(self) -> None:
        assert remote._suffix_from("https://x.test/a.exe") is None


class TestGating:
    """Nothing is fetched unless the build explicitly asked for it."""

    def test_remote_image_is_skipped_without_a_download_dir(self) -> None:
        conversion = convert_document("![alt](https://x.test/a.png)")
        assert conversion.assets == {}
        assert conversion.warnings == []
        assert "[alt]" in conversion.body

    def test_failure_warns_instead_of_raising(self, tmp_path) -> None:
        conversion = convert_document(
            "![alt](ftp://x.test/a.png)", work_dir=tmp_path, fetch_remote=True
        )
        assert conversion.assets == {}
        assert len(conversion.warnings) == 1
        assert "could not fetch" in conversion.warnings[0]

    def test_data_uris_are_left_alone(self, tmp_path) -> None:
        conversion = convert_document(
            "![alt](data:image/png;base64,AAAA)", work_dir=tmp_path, fetch_remote=True
        )
        assert conversion.assets == {}
        assert conversion.warnings == []


class TestLimits:
    def test_size_ceiling_is_sane(self) -> None:
        assert 0 < remote.MAX_BYTES <= 64 * 1024 * 1024

    def test_timeout_is_set(self) -> None:
        assert 0 < remote.TIMEOUT_SECONDS <= 60
