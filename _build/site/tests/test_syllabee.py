import re
import unittest
from pathlib import Path
from unittest import mock

import config
import syllabee
from config import ROOT, SYLLABEE
from syllabee import (COLOURING, FULL_THEMES, NEEDS_ATTRIBUTION, STORE_FILES, THEMES, Tile, store_problems, store_tools,
                      tiles, write_drawings)
from tests.test_assets import temporary_folder

SIBLING = ROOT.parent / SYLLABEE.repo
CODES = ("en", "da", "ru", "uk")
FAKE_TOOLS = '''WORDS = {code: ("Name", "tagline", ("BA", "NA")) for code in %r}
CARDS = {code: ("ic_word_banana", "ic_word_daisy", "ic_word_apple", "ic_word_rocket") for code in %r}


def colour(name):
    return "#123456"


def convert(path, prefix=None):
    return '<svg xmlns="http://www.w3.org/2000/svg"/>'
''' % (CODES, CODES)


def fake_repo(root: Path) -> Path:
    """A stand-in for ../learn_to_read with every file the Syllabee pages need: empty store files in the four
    languages' folders, empty drawables, and a tools/store_assets.py with the real one's names."""
    repo = root / "learn_to_read"
    for lang in SYLLABEE.langs:
        folder = SYLLABEE.listing(repo, lang)
        folder.mkdir(parents=True, exist_ok=True)
        for name in STORE_FILES:
            (folder / name).write_bytes(b"")
    (repo / "tools").mkdir(parents=True)
    (repo / "tools" / "store_assets.py").write_text(FAKE_TOOLS, encoding="utf-8")
    drawable_dir = repo / "app" / "src" / "main" / "res" / "drawable"
    drawable_dir.mkdir(parents=True)
    for name in {*THEMES.values(), *COLOURING.values(), "ic_word_banana", "ic_word_daisy", "ic_word_apple",
                 "ic_word_rocket"}:
        (drawable_dir / f"{name}.xml").write_text("<vector/>", encoding="utf-8")
    return repo


class StoreProblemsTest(unittest.TestCase):
    def setUp(self):
        self.repo = fake_repo(temporary_folder(self.addCleanup))

    def test_clean(self):
        self.assertEqual(store_problems(self.repo, {}), [])

    def test_missing_shot(self):
        (self.repo / "docs" / "store" / "da" / "phone-3-memo.png").unlink()
        self.assertEqual(store_problems(self.repo, {}), ["docs/store/da/phone-3-memo.png: missing"])

    def test_missing_drawable(self):
        (self.repo / "app" / "src" / "main" / "res" / "drawable" / "ic_word_cat.xml").unlink()
        self.assertEqual(store_problems(self.repo, {}), ["app/src/main/res/drawable/ic_word_cat.xml: missing"])

    def test_missing_tools(self):
        (self.repo / "tools" / "store_assets.py").unlink()
        self.assertEqual(store_problems(self.repo, {}), ["tools/store_assets.py: missing"])

    def test_tools_fail_to_load(self):
        (self.repo / "tools" / "store_assets.py").write_text("import no_such_module_here\n", encoding="utf-8")
        errors = store_problems(self.repo, {})
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("tools/store_assets.py: ModuleNotFoundError: "), errors)
        self.assertIn("no_such_module_here", errors[0])

    def test_words_and_cards_cover_every_language(self):
        tools = self.repo / "tools" / "store_assets.py"
        tools.write_text(tools.read_text(encoding="utf-8") + 'del WORDS["da"]\ndel CARDS["uk"]\n', encoding="utf-8")
        self.assertEqual(store_problems(self.repo, {}),
                         ["tools/store_assets.py: no WORDS for da", "tools/store_assets.py: no CARDS for uk"])

    def test_missing_colour(self):
        tools = self.repo / "tools" / "store_assets.py"
        tools.write_text(tools.read_text(encoding="utf-8") + (
            "\n\ndef colour(name):\n"
            "    if name == \"cat_birds\":\n"
            "        raise KeyError(name)\n"
            "    return \"#123456\"\n"), encoding="utf-8")
        self.assertEqual(store_problems(self.repo, {}), ["app/src/main/res/values/colors.xml: no cat_birds"])

    def test_colours_unreadable(self):
        tools = self.repo / "tools" / "store_assets.py"
        tools.write_text(tools.read_text(encoding="utf-8") + (
            "\n\ndef colour(name):\n"
            "    import pathlib\n"
            "    path = pathlib.Path(__file__).parents[1] / 'app' / 'src' / 'main' / 'res' / 'values' / 'colors.xml'\n"
            "    return path.read_text()\n"), encoding="utf-8")
        self.assertEqual(store_problems(self.repo, {}), ["app/src/main/res/values/colors.xml: missing"])

    def test_attribution(self):
        (self.repo / "app" / "src" / "main" / "res" / "drawable" / "ic_word_pigeon.xml").write_text("<vector/>")
        with mock.patch.dict(syllabee.THEMES, {"birds": "ic_word_pigeon"}):
            self.assertEqual(store_problems(self.repo, {}),
                             ["ic_word_pigeon: its licence needs an attribution the page doesn't give"])


def pack_themes(pack: Path) -> dict[str, list[str]]:
    """A language pack's themes and the drawables of their words: each Map.entry("<theme>", List.of(...))."""
    src = pack.read_text(encoding="utf-8")
    return {m[1]: re.findall(r"R\.drawable\.(\w+)", src[m.end():src.index(")))", m.end())])
            for m in re.finditer(r'Map\.entry\("([a-z]+)", List\.of\(', src)}


@unittest.skipUnless(SIBLING.is_dir(), "needs ../learn_to_read")
class AppArtTest(unittest.TestCase):
    def test_real_repository(self):
        self.assertEqual(store_problems(SIBLING, {}), [])

    def test_each_theme_drawing_is_in_every_pack(self):
        data = SIBLING / "app" / "src" / "main" / "java" / "com" / "slogarik" / "app" / "data"
        packs = {code: pack_themes(next((data / code).glob("*Pack.java"))) for code in CODES}
        for code, themes in packs.items():
            with self.subTest(code=code):
                self.assertEqual({len(words) for words in themes.values()}, {10})
        for key, drawable in THEMES.items():
            with self.subTest(theme=key):
                if key == "countries":
                    self.assertIn(f"R.drawable.{drawable}", (data / "Country.java").read_text(encoding="utf-8"))
                elif key == "mixed":
                    self.assertEqual(drawable, "ic_cat_mixed")
                else:
                    for code, themes in packs.items():
                        self.assertIn(drawable, themes[key], code)
        self.assertFalse(set(THEMES.values()) & NEEDS_ATTRIBUTION)

    def test_write_drawings(self):
        root = temporary_folder(self.addCleanup)
        with mock.patch.object(config, "ROOT", root):
            art = root / "syllabee" / "assets" / "img" / "art"
            art.mkdir(parents=True)
            (art / "old.svg").write_text("<svg/>")
            tools = store_tools(SIBLING)
            urls = write_drawings(SIBLING, tools)
            self.assertEqual(urls["ic_word_cat"], "/syllabee/assets/img/art/ic_word_cat.svg")
            self.assertEqual(set(urls), {*THEMES.values(), *COLOURING.values(),
                                         *(name for cards in tools.CARDS.values() for name in cards)})
            self.assertEqual({path.name for path in art.iterdir()}, {f"{name}.svg" for name in urls})
            for path in art.iterdir():
                self.assertTrue(path.read_text(encoding="utf-8").startswith("<svg"), path.name)
            times = {path.name: path.stat().st_mtime_ns for path in art.iterdir()}
            write_drawings(SIBLING, tools)
            self.assertEqual({path.name: path.stat().st_mtime_ns for path in art.iterdir()}, times)

    def test_tiles(self):
        tools = store_tools(SIBLING)
        urls = {name: f"/art/{name}.svg" for name in {*THEMES.values(), *COLOURING.values()}}
        themes = tiles(THEMES, urls, tools)
        self.assertEqual(themes[0], Tile("animals", "/art/ic_word_cat.svg", "#8A5024", False))
        self.assertEqual([tile.key for tile in themes], list(THEMES))
        self.assertEqual({tile.key for tile in themes if tile.locked}, FULL_THEMES)
        colouring = tiles(COLOURING, urls, tools)
        self.assertEqual([tile.key for tile in colouring], ["letters", "numbers", "shapes", "math"])
        self.assertFalse(any(tile.locked for tile in colouring))
