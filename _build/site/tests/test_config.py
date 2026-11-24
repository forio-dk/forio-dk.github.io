import unittest

from config import ART_WIDGET, LANGS, ROOT, page_file, page_url, play_url


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
