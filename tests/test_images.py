from pathlib import Path

import pytest

from doc_engine import images
from doc_engine.converter import convert_document

Image = pytest.importorskip("PIL.Image")


def picture(path, width: int, height: int):
    Image.new("RGB", (width, height), "white").save(path)
    return path


class TestPageRatios:
    def test_iso_sizes_share_one_ratio(self) -> None:
        assert images.page_ratio("a4") == images.page_ratio("a5")

    def test_us_letter_is_squarer_than_iso(self) -> None:
        assert images.page_ratio("us-letter") < images.page_ratio("a4")

    def test_unknown_paper_falls_back(self) -> None:
        assert images.page_ratio("nonsense") == images.page_ratio("a4")


class TestDetection:
    def test_a_wide_picture_is_left_alone(self) -> None:
        assert not images.needs_splitting(1000, 400, images.page_ratio("a4"))

    def test_an_ordinary_portrait_is_left_alone(self) -> None:
        assert not images.needs_splitting(700, 900, images.page_ratio("a4"))

    def test_a_very_tall_picture_is_split(self) -> None:
        assert images.needs_splitting(700, 3200, images.page_ratio("a4"))

    def test_zero_width_is_not_split(self) -> None:
        assert not images.needs_splitting(0, 100, images.page_ratio("a4"))


class TestSplitting:
    def test_tall_picture_becomes_several_pieces(self, tmp_path) -> None:
        source = picture(tmp_path / "tall.png", 700, 3200)
        pieces = images.split(source, tmp_path / "out", images.page_ratio("a4"), "tall")
        assert len(pieces) > 1
        assert all(piece.is_file() for piece in pieces)

    def test_pieces_cover_the_whole_height(self, tmp_path) -> None:
        source = picture(tmp_path / "tall.png", 700, 3200)
        pieces = images.split(source, tmp_path / "out", images.page_ratio("a4"), "tall")
        total = sum(Image.open(piece).size[1] for piece in pieces)
        assert total == 3200

    def test_pieces_keep_the_full_width(self, tmp_path) -> None:
        source = picture(tmp_path / "tall.png", 700, 3200)
        pieces = images.split(source, tmp_path / "out", images.page_ratio("a4"), "tall")
        assert all(Image.open(piece).size[0] == 700 for piece in pieces)

    def test_short_picture_is_returned_unchanged(self, tmp_path) -> None:
        source = picture(tmp_path / "wide.png", 800, 400)
        assert images.split(source, tmp_path / "out", images.page_ratio("a4"), "wide") == [source]

    def test_piece_count_is_capped(self, tmp_path) -> None:
        source = picture(tmp_path / "endless.png", 100, 40000)
        pieces = images.split(source, tmp_path / "out", images.page_ratio("a4"), "endless")
        assert len(pieces) <= images.MAX_PIECES

    def test_unreadable_file_is_reported(self, tmp_path) -> None:
        broken = tmp_path / "broken.png"
        broken.write_bytes(b"not an image")
        with pytest.raises(images.SplitError):
            images.split(broken, tmp_path / "out", images.page_ratio("a4"), "broken")


class TestConversion:
    def test_split_mode_emits_a_piece_per_page(self, tmp_path) -> None:
        picture(tmp_path / "tall.png", 700, 3200)
        conversion = convert_document(
            "![Flow](tall.png)",
            base_dir=tmp_path,
            work_dir=tmp_path / "work",
            split_tall=images.page_ratio("a4"),
        )
        assert conversion.body.count("fit-image") > 1
        assert "#pagebreak(weak: true)" in conversion.body
        assert len(conversion.assets) > 1

    def test_default_mode_keeps_one_picture(self, tmp_path) -> None:
        picture(tmp_path / "tall.png", 700, 3200)
        conversion = convert_document("![Flow](tall.png)", base_dir=tmp_path)
        assert conversion.body.count("fit-image") == 1
        assert len(conversion.assets) == 1


class TestRepeatedPictures:
    def test_the_same_tall_picture_twice_keeps_every_reference_valid(self, tmp_path) -> None:
        picture(tmp_path / "tall.png", 700, 3200)
        conversion = convert_document(
            "![one](tall.png)\n\n![two](tall.png)\n",
            base_dir=tmp_path,
            work_dir=tmp_path / "work",
            split_tall=images.page_ratio("a4"),
        )
        referenced = [chunk.split('"')[1] for chunk in conversion.body.split("fit-image(")[1:]]
        assert referenced
        assert all(name in conversion.assets for name in referenced)

    def test_it_is_only_cut_once(self, tmp_path) -> None:
        picture(tmp_path / "tall.png", 700, 3200)
        conversion = convert_document(
            "![one](tall.png)\n\n![two](tall.png)\n",
            base_dir=tmp_path,
            work_dir=tmp_path / "work",
            split_tall=images.page_ratio("a4"),
        )
        assert len({Path(p).name for p in conversion.assets.values()}) == len(conversion.assets)
