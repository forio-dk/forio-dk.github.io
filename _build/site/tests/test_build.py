import shutil
import tempfile
import unittest
from pathlib import Path

from build import problems
from config import APPS, ART_WIDGET, ATLAS_HUNT, LANGS


class ProblemsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.apps = self.root / "apps"
        self.repos = {}
        for app in APPS:
            self.repos[app] = self.root / app.repo
            for lang in LANGS:
                (self.repos[app] / "docs" / "listings" / lang.listing / "graphics").mkdir(parents=True)
            (self.apps / app.slug / "strings").mkdir(parents=True)
            for lang in LANGS:
                shutil.copy(app.strings / f"{lang.code}.toml", self.apps / app.slug / "strings")
        self.strings = self.apps / "artwidget" / "strings"

    def check(self, **repos: Path) -> list[str]:
        return problems({app: repos.get(app.slug, repo) for app, repo in self.repos.items()}, self.apps)

    def test_all_fine(self):
        self.assertEqual(self.check(), [])

    def test_broken_strings_file(self):
        (self.strings / "da.toml").write_text("[meta" + chr(10), encoding="utf-8")
        errors = self.check()
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("apps/artwidget/strings/da.toml: "), errors)

    def test_missing_strings_file(self):
        (self.strings / "it.toml").unlink()
        errors = self.check()
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("apps/artwidget/strings/it.toml: "), errors)

    def test_missing_repository(self):
        error = self.check(artwidget=self.root / "elsewhere")[0]
        self.assertIn("is not the Art Widget repository (no docs/listings); pass --art-widget", error)

    def test_missing_atlas_hunt_repository(self):
        errors = self.check(atlashunt=self.root / "elsewhere")
        self.assertEqual(len(errors), 1)
        self.assertIn("is not the Atlas Hunt repository (no docs/listings); pass --atlas-hunt", errors[0])

    def test_gallery_shot_without_caption(self):
        (self.repos[ATLAS_HUNT] / "docs" / "listings" / "da-DK" / "graphics" / "home-3-oceans.png").write_bytes(b"")
        self.assertEqual(self.check(), ["apps/atlashunt/strings/da.toml: no caption for home-3-oceans.png"])

    def test_both_apps_checked(self):
        self.assertEqual(set(self.repos), {ART_WIDGET, ATLAS_HUNT})
