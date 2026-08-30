import pytest

from doc_engine import manifest


def build_project(root):
    (root / "doc").mkdir()
    (root / "img").mkdir()
    (root / "doc-engine.md").write_text(
        "---\ntitle: Handbook\ntemplate: modern\n---\n\n"
        "- [Overview](doc/overview.md)\n"
        "- [Model](doc/model.md)\n"
        "- [Picture](img/pic.svg)\n"
        "- [Refs](refs.bib)\n"
    )
    (root / "doc" / "overview.md").write_text("# Overview\n\nFirst part.\n")
    (root / "doc" / "model.md").write_text("# Model\n\nSecond part.\n")
    (root / "img" / "pic.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
    (root / "refs.bib").write_text("@article{a, title={T}, author={A}, year={2020}}\n")
    return root / "doc-engine.md"


class TestDiscovery:
    def test_finds_the_manifest(self, tmp_path) -> None:
        (tmp_path / "doc-engine.md").write_text("- [x](a.md)\n")
        assert manifest.find(tmp_path) == tmp_path / "doc-engine.md"

    def test_returns_none_without_one(self, tmp_path) -> None:
        assert manifest.find(tmp_path) is None

    def test_recognizes_known_names(self, tmp_path) -> None:
        assert manifest.is_manifest(tmp_path / "SUMMARY.md")
        assert not manifest.is_manifest(tmp_path / "README.md")


class TestLoading:
    def test_reads_metadata_and_entries(self, tmp_path) -> None:
        path = build_project(tmp_path)
        loaded = manifest.load(path)
        assert loaded.metadata["title"] == "Handbook"
        assert [entry.kind for entry in loaded.entries] == ["markdown", "markdown", "image"]

    def test_bibliography_is_separated_from_entries(self, tmp_path) -> None:
        loaded = manifest.load(build_project(tmp_path))
        assert loaded.bibliography is not None
        assert loaded.bibliography.name == "refs.bib"

    def test_entry_order_follows_the_file(self, tmp_path) -> None:
        loaded = manifest.load(build_project(tmp_path))
        assert [entry.label for entry in loaded.entries] == ["Overview", "Model", "Picture"]

    def test_paths_resolve_against_the_manifest(self, tmp_path) -> None:
        loaded = manifest.load(build_project(tmp_path))
        assert loaded.entries[0].path == tmp_path / "doc" / "overview.md"

    def test_remote_links_are_ignored(self, tmp_path) -> None:
        (tmp_path / "a.md").write_text("# A\n")
        (tmp_path / "doc-engine.md").write_text("- [Site](https://example.com)\n- [Local](a.md)\n")
        loaded = manifest.load(tmp_path / "doc-engine.md")
        assert len(loaded.entries) == 1

    def test_missing_file_is_reported(self, tmp_path) -> None:
        (tmp_path / "doc-engine.md").write_text("- [Gone](nope.md)\n")
        with pytest.raises(manifest.ManifestError, match="do not exist"):
            manifest.load(tmp_path / "doc-engine.md")

    def test_manifest_without_documents_is_reported(self, tmp_path) -> None:
        (tmp_path / "doc-engine.md").write_text("Just prose, no links.\n")
        with pytest.raises(manifest.ManifestError, match="no documents"):
            manifest.load(tmp_path / "doc-engine.md")


class TestAssembly:
    def test_documents_are_joined_in_order(self, tmp_path) -> None:
        conversion = manifest.assemble(manifest.load(build_project(tmp_path)))
        assert conversion.body.index("Overview") < conversion.body.index("Model")

    def test_headings_keep_their_level(self, tmp_path) -> None:
        conversion = manifest.assemble(manifest.load(build_project(tmp_path)))
        assert "= Overview" in conversion.body

    def test_image_entry_becomes_a_figure(self, tmp_path) -> None:
        conversion = manifest.assemble(manifest.load(build_project(tmp_path)))
        assert "#figure(fit-image(" in conversion.body
        assert any(name.endswith("pic.svg") for name in conversion.assets)

    def test_diagram_entry_is_rendered(self, tmp_path) -> None:
        (tmp_path / "flow.mmd").write_text("flowchart TD\n A-->B\n")
        (tmp_path / "doc-engine.md").write_text("- [Flow](flow.mmd)\n")
        conversion = manifest.assemble(manifest.load(tmp_path / "doc-engine.md"))
        name = next(iter(conversion.generated))
        assert "<svg" in conversion.generated[name]

    def test_assets_from_different_files_do_not_collide(self, tmp_path) -> None:
        for name in ("one", "two"):
            folder = tmp_path / name
            folder.mkdir()
            (folder / "logo.png").write_bytes(b"\x89PNG\r\n")
            (folder / "page.md").write_text(f"# {name}\n\n![logo](logo.png)\n")
        (tmp_path / "doc-engine.md").write_text("- [One](one/page.md)\n- [Two](two/page.md)\n")
        conversion = manifest.assemble(manifest.load(tmp_path / "doc-engine.md"))
        assert len(conversion.assets) == 2


class TestIncludedFileQuirks:
    def test_front_matter_in_an_included_file_is_not_rendered(self, tmp_path) -> None:
        (tmp_path / "a.md").write_text("---\ntitle: Internal\n---\n\n# Real Heading\n\nBody.\n")
        (tmp_path / "doc-engine.md").write_text("- [A](a.md)\n")
        body = manifest.assemble(manifest.load(tmp_path / "doc-engine.md")).body
        assert "title: Internal" not in body
        assert "Real Heading" in body

    def test_caption_is_escaped_for_typst(self, tmp_path) -> None:
        (tmp_path / "p.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        (tmp_path / "d.md").write_text("# D\n")
        (tmp_path / "doc-engine.md").write_text("- [Cost $5 and #1](p.svg)\n- [D](d.md)\n")
        body = manifest.assemble(manifest.load(tmp_path / "doc-engine.md")).body
        assert "\\$5" in body
        assert "\\#1" in body

    def test_empty_label_produces_a_plain_picture(self, tmp_path) -> None:
        (tmp_path / "p.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        (tmp_path / "d.md").write_text("# D\n")
        (tmp_path / "doc-engine.md").write_text("- [](p.svg)\n- [D](d.md)\n")
        body = manifest.assemble(manifest.load(tmp_path / "doc-engine.md")).body
        assert "caption" not in body


class TestCrossReferences:
    """A link between two included files should jump inside the PDF."""

    def make(self, root):
        (root / "doc-engine.md").write_text("- [A](a.md)\n- [B](b.md)\n")
        (root / "a.md").write_text("# A\n\nGo to [B](b.md) or [out](https://x.test).\n")
        (root / "b.md").write_text("# B\n\nBack to [A](a.md).\n")
        return manifest.assemble(manifest.load(root / "doc-engine.md")).body

    def test_link_to_another_entry_becomes_internal(self, tmp_path) -> None:
        body = self.make(tmp_path)
        assert "#link(<entry-1>)" in body
        assert "#link(<entry-0>)" in body

    def test_every_entry_gets_an_anchor(self, tmp_path) -> None:
        assert self.make(tmp_path).count("#metadata(none)") == 2

    def test_external_links_are_untouched(self, tmp_path) -> None:
        assert '#link("https://x.test")' in self.make(tmp_path)

    def test_links_outside_a_manifest_stay_plain(self, tmp_path) -> None:
        from doc_engine.converter import convert_document

        (tmp_path / "b.md").write_text("# B\n")
        body = convert_document("[B](b.md)", base_dir=tmp_path).body
        assert '#link("b.md")' in body
