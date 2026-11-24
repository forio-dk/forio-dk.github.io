import shutil
import tempfile
import unittest
from pathlib import Path

from build import problems
from config import ART_WIDGET, LANGS


class ProblemsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name) / "art_widget"
        (self.repo / "docs" / "listings").mkdir(parents=True)
        self.apps = Path(tmp.name) / "apps"
        self.strings = self.apps / "artwidget" / "strings"
        self.strings.mkdir(parents=True)
        for lang in LANGS:
            shutil.copy(ART_WIDGET.strings / f"{lang.code}.toml", self.strings)

    def check(self, repo: Path | None = None) -> list[str]:
        return problems({ART_WIDGET: repo or self.repo}, self.apps)

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
        error = self.check(self.repo.parent / "elsewhere")[0]
        self.assertIn("is not the Art Widget repository (no docs/listings); pass --art-widget", error)
