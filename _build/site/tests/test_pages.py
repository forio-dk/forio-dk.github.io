import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

import config
from config import ART_WIDGET, ATLAS_HUNT, LANGS
from pages import app_icon, listing_graphics, phone_shots, write_page
from strings import load_strings
from tests.test_assets import gradient, temporary_folder
from tests.test_render import ATLAS_KEYS, fake


class PagesTest(unittest.TestCase):
    """The steps every app's builder shares, writing into a temporary site root."""

    def setUp(self):
        self.root = temporary_folder(self.addCleanup)
        patcher = mock.patch.object(config, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.graphics = self.root / "listing"
        self.graphics.mkdir()

    def test_listing_graphics(self):
        self.assertEqual(listing_graphics(Path("repo"), LANGS[1]), Path("repo/docs/listings/da-DK/graphics"))

    def test_app_icon(self):
        gradient(self.graphics / "icon-512.png", (512, 512), "RGBA")
        icon = app_icon(ART_WIDGET, self.graphics)
        self.assertEqual(icon.src, "/artwidget/assets/img/icon-64.webp")
        for name in ("favicon-32.png", "apple-touch-icon.png", "icon-64.webp", "icon-128.webp"):
            self.assertTrue((self.root / "artwidget" / "assets" / "img" / name).is_file(), name)

    def test_phone_shots(self):
        gradient(self.graphics / "phone-1-x.png", (1080, 1920))
        shots = phone_shots(ATLAS_HUNT, self.graphics, LANGS[1], {"step_1": "phone-1-x.png"})
        self.assertEqual(list(shots), ["step_1"])
        self.assertEqual(shots["step_1"].src, "/atlashunt/assets/img/da/step-1-200.webp")
        self.assertTrue((self.root / "atlashunt" / "assets" / "img" / "da" / "step-1-400.webp").is_file())

    def test_write_page(self):
        gradient(self.graphics / "feature-graphic.png", (1024, 500))
        pictures = {key: fake(f"/atlashunt/assets/img/{key}-1.webp") for key in ATLAS_KEYS}
        pictures["badge"] = fake("/assets/badges/en.png")
        strings = load_strings(["en"], ATLAS_HUNT.strings)["en"]
        write_page(ATLAS_HUNT, LANGS[0], self.graphics, strings, pictures, gallery=[],
                   video="/atlashunt/assets/video/en.mp4", poster="/atlashunt/assets/video/en-poster.webp")
        page = (self.root / "atlashunt" / "index.html").read_text(encoding="utf-8")
        self.assertIn("<title>Atlas Hunt: Map Quiz</title>", page)
        with Image.open(self.root / "atlashunt" / "assets" / "img" / "en" / "og.jpg") as og:
            self.assertEqual((og.format, og.size), ("JPEG", (1024, 500)))
