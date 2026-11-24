import unittest
from pathlib import Path

from config import ART_WIDGET, ATLAS_HUNT, LANGS, ROOT, SYLLABEE, page_file, page_url, play_url

EN, DA, RU, UK = (next(lang for lang in LANGS if lang.code == code) for code in ("en", "da", "ru", "uk"))


class ConfigTest(unittest.TestCase):
    def test_codes(self):
        self.assertEqual([lang.code for lang in LANGS], ["en", "da", "it", "ro", "ru", "uk"])

    def test_urls(self):
        self.assertEqual(page_url(ART_WIDGET, LANGS[0]), "https://forio-dk.github.io/artwidget/")
        self.assertEqual(page_url(ART_WIDGET, LANGS[5]), "https://forio-dk.github.io/artwidget/uk/")
        self.assertEqual(page_file(ART_WIDGET, LANGS[0]), ROOT / "artwidget" / "index.html")
        self.assertEqual(page_file(ART_WIDGET, LANGS[1]), ROOT / "artwidget" / "da" / "index.html")

    def test_play_url(self):
        self.assertEqual(
            play_url(ART_WIDGET, LANGS[0]),
            "https://play.google.com/store/apps/details?id=dk.forio.artwidget&hl=en"
            "&referrer=utm_source%3Dforio-dk.github.io%26utm_medium%3Dwebsite%26utm_campaign%3Dartwidget-home")

    def test_badge_codes(self):
        self.assertEqual([lang.badge for lang in LANGS], ["en", "da", "it", "ro", "ru", "ua"])

    def test_flavours(self):
        self.assertEqual([lang.code for lang in SYLLABEE.langs], ["en", "da", "ru", "uk"])
        self.assertEqual([SYLLABEE.name_in(lang) for lang in (EN, DA, RU, UK)],
                         ["Syllabee", "Stavebi", "Слогарик", "Складарик"])
        self.assertEqual([SYLLABEE.package_in(lang) for lang in (EN, DA, RU, UK)],
                         ["dk.forio.syllabee", "dk.forio.stavebi", "dk.forio.slogarik", "dk.forio.skladaryk"])
        self.assertEqual(ATLAS_HUNT.name_in(DA), "Atlas Hunt")
        self.assertEqual(ATLAS_HUNT.package_in(DA), "dk.forio.atlashunt")
        self.assertEqual(ATLAS_HUNT.langs, LANGS)

    def test_syllabee_play_url(self):
        self.assertEqual(
            play_url(SYLLABEE, UK),
            "https://play.google.com/store/apps/details?id=dk.forio.skladaryk&hl=uk"
            "&referrer=utm_source%3Dforio-dk.github.io%26utm_medium%3Dwebsite%26utm_campaign%3Dsyllabee-home")

    def test_listing_locations(self):
        self.assertEqual(ATLAS_HUNT.graphics(Path("r"), DA), Path("r/docs/listings/da-DK/graphics"))
        self.assertEqual(ATLAS_HUNT.listing(Path("r"), DA), Path("r/docs/listings/da-DK"))
        self.assertEqual(SYLLABEE.graphics(Path("r"), UK), Path("r/docs/store/uk"))
        self.assertEqual(SYLLABEE.listing(Path("r"), UK), Path("r/docs/store/uk"))
