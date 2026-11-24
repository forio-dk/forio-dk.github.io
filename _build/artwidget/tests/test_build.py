import shutil
import tempfile
import unittest
from pathlib import Path

from build import problems
from config import LANGS, STRINGS


class ProblemsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name) / "art_widget"
        (self.repo / "docs" / "listings").mkdir(parents=True)
        self.strings = Path(tmp.name) / "strings"
        self.strings.mkdir()
        for lang in LANGS:
            shutil.copy(STRINGS / f"{lang.code}.toml", self.strings)

    def test_all_fine(self):
        self.assertEqual(problems(self.repo, self.strings), [])

    def test_broken_strings_file(self):
        (self.strings / "da.toml").write_text("[meta" + chr(10), encoding="utf-8")
        errors = problems(self.repo, self.strings)
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("strings/da.toml: "), errors)

    def test_missing_strings_file(self):
        (self.strings / "it.toml").unlink()
        errors = problems(self.repo, self.strings)
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("strings/it.toml: "), errors)

    def test_missing_repository(self):
        self.assertIn("no docs/listings", problems(self.repo.parent / "elsewhere", self.strings)[0])
