"""Checks the committed, generated site: links, languages, privacy and the files the pages depend on."""
import re
import subprocess
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image

from config import ART_WIDGET, LANGS, ROOT, SITE_URL, page_file
from tests.test_render import Tags

ASSETS = ART_WIDGET.assets
CSS = ROOT / "assets" / "site.css"
CSS_FILES = [CSS, ASSETS / "theme.css"]
POLICY_BLOBS = {
    "artwidget/privacy-policy.md": "f918c89c82a0fb2b8b6995b715848743abb632f1",
    "atlashunt/privacy-policy.md": "712154b31602b8bcb454efe4576031d4472d8a25",
    "syllabee/privacy-policy.md": "0a694112f7a71f03e41caf4fda66205846e2742c",
}
HOME = ROOT / "index.html"
OUTBOUND_HOSTS = {"play.google.com", "commons.wikimedia.org"}
REQUEST_RELS = {"stylesheet", "preload", "icon", "apple-touch-icon"}


def local_file(url_path: str) -> Path:
    """The repository file GitHub Pages serves at a root-relative URL path."""
    path = urlsplit(url_path).path
    target = ROOT / path.lstrip("/")
    if path.endswith("/"):
        target = target / "index.html"
    if not target.exists() and target.suffix == ".html":
        target = target.with_suffix(".md")  # Jekyll publishes privacy-policy.md as privacy-policy.html
    return target


def requested_urls(tags: Tags) -> list[str]:
    """Everything a browser loads for the page by itself: images, video, styles, fonts, icons."""
    urls = [a["src"] for t, a in tags.tags if t in ("img", "source", "script") and "src" in a]
    urls += [entry.split()[0] for t, a in tags.tags if t == "img" and a.get("srcset")
             for entry in a["srcset"].split(",")]
    urls += [a["poster"] for t, a in tags.tags if t == "video" and "poster" in a]
    urls += [a["href"] for t, a in tags.tags if t == "link" and a.get("rel") in REQUEST_RELS]
    return urls


def css_urls(css: Path) -> list[str]:
    return re.findall(r"""url\(\s*["']?([^"')]+)["']?\s*\)""", css.read_text(encoding="utf-8"))


class SiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {lang.code: page_file(ART_WIDGET, lang).read_text(encoding="utf-8") for lang in LANGS}
        cls.pages["home"] = HOME.read_text(encoding="utf-8")
        cls.tags = {code: Tags(html) for code, html in cls.pages.items()}
        cls.css = CSS.read_text(encoding="utf-8")

    def test_pages_exist(self):
        for lang in LANGS:
            self.assertTrue(page_file(ART_WIDGET, lang).is_file(), lang.code)

    def test_internal_links_resolve(self):
        for code, tags in self.tags.items():
            refs = requested_urls(tags) + [a["href"] for t, a in tags.tags if t == "a" and "href" in a]
            for ref in refs:
                if ref.startswith("/") and not ref.startswith("//"):
                    with self.subTest(page=code, ref=ref):
                        self.assertTrue(local_file(ref).is_file(), ref)
        for css in CSS_FILES:
            for ref in css_urls(css):
                with self.subTest(css=css.name, ref=ref):
                    self.assertTrue((css.parent / ref).is_file(), ref)

    def test_own_absolute_urls_resolve(self):
        for code, tags in self.tags.items():
            urls = [a["href"] for t, a in tags.tags if t == "link" and a.get("rel") in ("canonical", "alternate")]
            urls += [a["content"] for t, a in tags.tags if t == "meta" and a.get("property") in ("og:image", "og:url")]
            for url in urls:
                with self.subTest(page=code, url=url):
                    self.assertTrue(url.startswith(SITE_URL + "/"), url)
                    self.assertTrue(local_file(urlsplit(url).path).is_file(), url)

    def test_hreflang_reciprocal(self):
        sets = {code: {(a["hreflang"], a["href"]) for t, a in tags.tags if t == "link" and a.get("rel") == "alternate"}
                for code, tags in self.tags.items() if code != "home"}
        self.assertEqual(len({frozenset(s) for s in sets.values()}), 1)
        self.assertEqual(len(sets["en"]), 7)

    def test_no_third_party_requests(self):
        for code, tags in self.tags.items():
            for url in requested_urls(tags):
                with self.subTest(page=code, url=url):
                    self.assertFalse(url.startswith(("http:", "https:", "//")), url)
            for t, a in tags.tags:
                href = a.get("href", "") if t == "a" else ""
                if href.startswith(("http:", "https:", "//")):
                    with self.subTest(page=code, href=href):
                        self.assertIn(urlsplit(href).hostname, OUTBOUND_HOSTS)
                elif ":" in href:
                    self.assertTrue(href.startswith("mailto:"), href)
        for css in CSS_FILES:
            for url in css_urls(css):
                self.assertFalse(url.startswith(("http:", "https:", "//")), url)

    def test_fonts_swap(self):
        self.assertEqual(self.css.count("@font-face"), 9)
        self.assertEqual(self.css.count("font-display: swap"), 9)

    def test_old_shared_assets_gone(self):
        for path in ("fonts", "badges", "site.css", "img/apps"):
            with self.subTest(path=path):
                self.assertFalse((ASSETS / path).exists(), path)

    def test_focus_visible(self):
        self.assertIn(":focus-visible", self.css)

    def test_policies_untouched(self):
        for path, expected in POLICY_BLOBS.items():
            blob = subprocess.run(["git", "hash-object", path], cwd=ROOT, check=True,
                                  capture_output=True, text=True).stdout.strip()
            self.assertEqual(blob, expected, path)

    def test_home_page_exists(self):
        self.assertIn("<h1>Forio</h1>", self.pages["home"])

    def test_video_size(self):
        self.assertLessEqual((ASSETS / "video" / "preview.mp4").stat().st_size, 6 * 1024 * 1024)

    def test_favicon(self):
        with Image.open(ROOT / "favicon.ico") as icon:
            self.assertEqual(icon.format, "ICO")
            self.assertEqual(sorted(icon.info["sizes"]), [(16, 16), (32, 32), (48, 48)])
        with Image.open(ROOT / "apple-touch-icon.png") as touch:
            self.assertEqual((touch.format, touch.size), ("PNG", (180, 180)))

    def test_hero_painting_has_a_middle_size(self):
        starry = [a for a in self.tags["en"].find("img") if a["src"].startswith("/artwidget/assets/img/starry")]
        widths = [int(entry.split()[1].rstrip("w")) for entry in starry[0]["srcset"].split(",")]
        self.assertEqual(widths, [480, 720, 960])

    def test_readme_served(self):
        # Every policy's Contact line links to /README.md
        self.assertTrue((ROOT / "README.md").is_file())
        excluded = [line.strip()[2:].strip() for line in (ROOT / "_config.yml").read_text(encoding="utf-8").splitlines()
                    if line.strip().startswith("- ")]
        self.assertNotIn("README.md", excluded)
