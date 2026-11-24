import unittest

from config import ART_WIDGET, LANGS, ROOT
from strings import load_strings, shape_errors


class ShapeTest(unittest.TestCase):
    def test_same_shape(self):
        self.assertEqual(shape_errors({"a": 1, "b": [{"x": "s"}]}, {"a": 2, "b": [{"x": "t"}]}), [])

    def test_missing(self):
        self.assertEqual(shape_errors({"a": "", "b": ""}, {"a": ""}), ["b: missing"])

    def test_unexpected(self):
        self.assertEqual(shape_errors({"a": ""}, {"a": "", "c": ""}), ["c: unexpected"])

    def test_list_length(self):
        self.assertEqual(shape_errors({"b": ["", "", ""]}, {"b": ["", ""]}), ["b: 2 items, expected 3"])

    def test_type(self):
        self.assertEqual(shape_errors({"a": ""}, {"a": []}), ["a: list, expected str"])

    def test_nested_path(self):
        self.assertEqual(shape_errors({"m": {"t": ""}}, {"m": {}}), ["m.t: missing"])

    def test_english_loads(self):
        en = load_strings(["en"], ART_WIDGET.strings)["en"]
        self.assertEqual(en["meta"]["title"], "Art Widget: Artwork of the Day")
        self.assertEqual(len(en["how"]["steps"]), 3)
        self.assertEqual(len(en["features"]["items"]), 6)


SIBLING = ROOT.parent / "art_widget"
CODES = [lang.code for lang in LANGS]
COUNTS = {"en": "9,000", "da": "1.000", "it": "7.000", "ro": "1000", "ru": "4500", "uk": "1600"}
ART = {  # code: (starry.title, pearl.year), from the app's library and its year_circa format
    "en": ("The Starry Night", "c. 1665"),
    "da": ("Stjernenatten", "ca. 1665"),
    "it": ("Notte stellata", "1665 circa"),
    "ro": ("Noapte înstelată", "cca 1665"),
    "ru": ("Звёздная ночь", "ок. 1665"),
    "uk": ("Зоряна ніч", "бл. 1665"),
}
MARKER = '# Strings ending in "# new"'


def listing_block(md: str, heading: str) -> str:
    """The first ```text block after the line starting with "## <heading>"."""
    after = md.split(f"\n## {heading}", 1)[1]
    return after.split("```text\n", 1)[1].split("\n```", 1)[0]


class TranslationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strings = load_strings(CODES, ART_WIDGET.strings)

    def test_all_languages_match_english(self):
        for code in CODES[1:]:
            with self.subTest(code=code):
                self.assertEqual(shape_errors(self.strings["en"], self.strings[code]), [])

    @unittest.skipUnless(SIBLING.is_dir(), "needs ../art_widget")
    def test_title_and_lead_from_listing(self):
        for lang in LANGS:
            md = (SIBLING / "docs" / "listings" / lang.listing / "listing.md").read_text(encoding="utf-8")
            with self.subTest(code=lang.code):
                self.assertEqual(self.strings[lang.code]["meta"]["title"], listing_block(md, "App name"))
                self.assertEqual(self.strings[lang.code]["hero"]["lead"], listing_block(md, "Short description"))

    def test_collection_count(self):
        for code in CODES:
            with self.subTest(code=code):
                self.assertIn(COUNTS[code], self.strings[code]["features"]["items"][0]["heading"])

    def test_art_names(self):
        for code in CODES:
            with self.subTest(code=code):
                art = self.strings[code]["art"]
                self.assertEqual((art["starry"]["title"], art["pearl"]["year"]), ART[code])

    def test_review_markers(self):
        for code in CODES[1:]:
            with self.subTest(code=code):
                self.assertTrue((ART_WIDGET.strings / f"{code}.toml").read_text(encoding="utf-8").startswith(MARKER))


class EnglishClaimsTest(unittest.TestCase):
    """English copy must not claim more than the privacy policy and the store listing say."""

    @classmethod
    def setUpClass(cls):
        cls.en = load_strings(["en"], ART_WIDGET.strings)["en"]

    def test_privacy_names_only_what_the_policy_names(self):
        # Policy: "stores only the current artwork, its image and introduction and your language choice"
        text = self.en["privacy"]["text"]
        self.assertIn("your language choice", text)
        self.assertNotIn("your choices", text)

    def test_choosing_types_mentions_the_full_version(self):
        # Listing: sculptures, drawings, tapestries and the rest come only with the full version
        self.assertIn("full version", self.en["how"]["steps"][2]["text"])
