import tempfile
import unittest
from pathlib import Path

from atlashunt import gallery_problems, gallery_shots
from config import ATLAS_HUNT, LANGS
from output import prune
from strings import load_strings

STRINGS = load_strings([lang.code for lang in LANGS], ATLAS_HUNT.strings)


def temporary_folder(test: unittest.TestCase) -> Path:
    folder = tempfile.TemporaryDirectory()
    test.addCleanup(folder.cleanup)
    return Path(folder.name)


def touch(folder: Path, *names: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        (folder / name).write_bytes(b"")


class GalleryShotsTest(unittest.TestCase):
    def test_gallery_order(self):
        folder = temporary_folder(self)
        touch(folder, "home-10-b.png", "home-9-a.png", "home-2-c.png", "phone-1-x.png", "notes.txt")
        self.assertEqual(gallery_shots(folder),
                         [("c", folder / "home-2-c.png"), ("a", folder / "home-9-a.png"),
                          ("b", folder / "home-10-b.png")])

    def test_no_shots(self):
        folder = temporary_folder(self)
        touch(folder, "phone-1-x.png")
        self.assertEqual(gallery_shots(folder), [])


class GalleryProblemsTest(unittest.TestCase):
    def repo(self, *names: str) -> Path:
        repo = temporary_folder(self)
        for lang in LANGS:
            touch(repo / "docs" / "listings" / lang.listing / "graphics")
        touch(repo / "docs" / "listings" / "en-US" / "graphics", *names)
        return repo

    def test_shot_without_caption(self):
        repo = self.repo("home-1-explore-names.png", "home-16-oceans.png")
        self.assertEqual(gallery_problems(repo, STRINGS),
                         ["apps/atlashunt/strings/en.toml: no caption for home-16-oceans.png"])

    def test_captioned_shots(self):
        self.assertEqual(gallery_problems(self.repo("home-1-explore-names.png", "home-15-dark.png"), STRINGS), [])

    def test_misnamed_shots(self):
        repo = self.repo("home-1-explore-names.png", "home-16-Oceans.png", "home-17_seas.png", "home-x-seas.png")
        self.assertEqual(gallery_problems(repo, STRINGS),
                         [f"docs/listings/en-US/graphics/{name}: name it home-<N>-<screen>.png, <screen> in lowercase "
                          "letters, digits and hyphens" for name in ("home-16-Oceans.png", "home-17_seas.png",
                                                                     "home-x-seas.png")])

    def test_duplicate_screens(self):
        repo = self.repo("home-1-dark.png", "home-15-dark.png")
        self.assertEqual(gallery_problems(repo, STRINGS),
                         ["docs/listings/en-US/graphics: home-1-dark.png and home-15-dark.png are the same screen, dark"])


class PruneTest(unittest.TestCase):
    def test_removes_only_what_the_build_did_not_write(self):
        folder = temporary_folder(self)
        touch(folder, "a-160.webp", "old-160.webp", "old-320.webp")
        prune(folder, {folder / "a-160.webp"})
        self.assertEqual(sorted(path.name for path in folder.iterdir()), ["a-160.webp"])

    def test_missing_folder(self):
        prune(temporary_folder(self) / "none", set())
