import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

import fetch_vendor
from config import LOCAL_VENDOR, VENDOR, VENDOR_DIR

MAGIC = {".woff2": b"wOF2", ".png": b"\x89PNG", ".jpg": b"\xff\xd8\xff", ".ttf": b"\x00\x01\x00\x00"}


class VendorTest(unittest.TestCase):
    def test_manifest_size(self):
        self.assertEqual(len(VENDOR), 28)  # 12 web fonts + the logo's TTF, 4 font CSS, 3 licences, 6 badges, 2 artworks

    def test_files_present_and_typed(self):
        for name in VENDOR:
            path = VENDOR_DIR / name
            with self.subTest(name=name):
                self.assertTrue(path.is_file(), f"{name} missing")
                data = path.read_bytes()
                suffix = path.suffix
                if suffix in MAGIC:
                    self.assertTrue(data.startswith(MAGIC[suffix]), f"{name} is not {suffix}")
                elif suffix == ".css":
                    self.assertIn("@font-face", data.decode("utf-8"))
                elif suffix == ".txt":
                    self.assertIn("OPEN FONT LICENSE", data.decode("utf-8").upper())
                else:
                    self.fail(f"unexpected type {suffix}")

    def test_artwork_resolution(self):
        for name in ("art/starry-night.jpg", "art/pearl-earring.jpg"):
            with self.subTest(name=name), Image.open(VENDOR_DIR / name) as image:
                self.assertGreaterEqual(image.width, 1000)

    def test_sources_listed(self):
        sources = (VENDOR_DIR / "SOURCES.md").read_text(encoding="utf-8")
        for url in VENDOR.values():
            self.assertIn(url, sources)

    def test_local_copies(self):
        sources = (VENDOR_DIR / "SOURCES.md").read_text(encoding="utf-8")
        for name, source in LOCAL_VENDOR.items():
            with self.subTest(name=name):
                self.assertTrue((VENDOR_DIR / name).read_bytes().startswith(MAGIC[".png"]))
                self.assertIn(f"`{name}`: ../{source}", sources)


class FetchVendorTest(unittest.TestCase):
    def test_missing_sibling_repository(self):
        with (tempfile.TemporaryDirectory() as tmp,
              mock.patch.object(fetch_vendor, "VENDOR", {}),
              mock.patch.object(fetch_vendor, "LOCAL_VENDOR", {"icons/x.png": "no_such_repo/icon.png"}),
              mock.patch.object(fetch_vendor, "VENDOR_DIR", Path(tmp)),
              contextlib.redirect_stderr(io.StringIO()) as err):
            self.assertEqual(fetch_vendor.main([]), 2)
        self.assertIn("no_such_repo", err.getvalue())
        self.assertIn("icon.png", err.getvalue())
