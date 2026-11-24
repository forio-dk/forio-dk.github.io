"""Checks the committed, generated site: links, languages, privacy and the files the pages depend on."""
import re
import subprocess
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from config import ASSETS, LANGS, ROOT, SITE_URL, page_file
from tests.test_render import Tags

CSS = ASSETS / "site.css"
POLICY_BLOB = "f918c89c82a0fb2b8b6995b715848743abb632f1"
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


def css_urls() -> list[str]:
    return re.findall(r"""url\(\s*["']?([^"')]+)["']?\s*\)""", CSS.read_text(encoding="utf-8"))


class SiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {lang.code: page_file(lang).read_text(encoding="utf-8") for lang in LANGS}
        cls.tags = {code: Tags(html) for code, html in cls.pages.items()}
        cls.css = CSS.read_text(encoding="utf-8")

    def test_pages_exist(self):
        for lang in LANGS:
            self.assertTrue(page_file(lang).is_file(), lang.code)

    def test_internal_links_resolve(self):
        for code, tags in self.tags.items():
            refs = requested_urls(tags) + [a["href"] for t, a in tags.tags if t == "a" and "href" in a]
            for ref in refs:
                if ref.startswith("/") and not ref.startswith("//"):
                    with self.subTest(page=code, ref=ref):
                        self.assertTrue(local_file(ref).is_file(), ref)
        for ref in css_urls():
            with self.subTest(css=ref):
                self.assertTrue((CSS.parent / ref).is_file(), ref)

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
                for code, tags in self.tags.items()}
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
        for url in css_urls():
            self.assertFalse(url.startswith(("http:", "https:", "//")), url)

    def test_fonts_swap(self):
        self.assertEqual(self.css.count("@font-face"), 9)
        self.assertEqual(self.css.count("font-display: swap"), 9)

    @unittest.expectedFailure  # Task 7 styles the page
    def test_focus_visible(self):
        self.assertIn(":focus-visible", self.css)

    def test_policy_untouched(self):
        blob = subprocess.run(["git", "hash-object", "artwidget/privacy-policy.md"], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()
        self.assertEqual(blob, POLICY_BLOB)

    def test_video_size(self):
        self.assertLessEqual((ASSETS / "video" / "preview.mp4").stat().st_size, 6 * 1024 * 1024)
