"""Checks the committed, generated site: links, languages, privacy and the files the pages depend on."""
import re
import subprocess
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image

from atlashunt import gallery_shots
from syllabee import NEEDS_ATTRIBUTION
from config import APPS, ART_WIDGET, ATLAS_HUNT, LANGS, ROOT, SITE_URL, SYLLABEE, page_file, play_url
from tests.test_render import Tags

ASSETS = ART_WIDGET.assets
CSS = ROOT / "assets" / "site.css"
ATLAS_THEME = ATLAS_HUNT.assets / "theme.css"
SYLLABEE_THEME = SYLLABEE.assets / "theme.css"
CSS_FILES = [CSS, ASSETS / "theme.css", ATLAS_THEME, SYLLABEE_THEME]
POLICY_BLOBS = {
    "artwidget/privacy-policy.md": "f918c89c82a0fb2b8b6995b715848743abb632f1",
    "atlashunt/privacy-policy.md": "712154b31602b8bcb454efe4576031d4472d8a25",
    "syllabee/privacy-policy.md": "0a694112f7a71f03e41caf4fda66205846e2742c",
}
HOME = ROOT / "index.html"
STYLE_URL = re.compile(r"""url\(\s*["']?([^"')]+)["']?\s*\)""")
ATLAS_SIBLING = ROOT.parent / "atlas_hunt"
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
    urls += [url for t, a in tags.tags if "style" in a for url in STYLE_URL.findall(a["style"])]
    urls += [a["href"] for t, a in tags.tags if t == "link" and a.get("rel") in REQUEST_RELS]
    return urls


def foreign_assets(slug: str, code: str, urls: list[str]) -> list[str]:
    """The URLs among a page's that belong to another language: an image in /<slug>/assets/img/<other code>/, or a
    video in /<slug>/assets/video/ named for another code. Shared images (the icon, the levels) are in neither."""
    codes = {lang.code for lang in LANGS}
    foreign = []
    for url in urls:
        parts = urlsplit(url).path.split("/")
        if parts[1:4] == [slug, "assets", "img"] and len(parts) > 5 and parts[4] in codes - {code}:
            foreign.append(url)
        elif parts[1:4] == [slug, "assets", "video"] and parts[4].split(".")[0].split("-")[0] in codes - {code}:
            foreign.append(url)
    return foreign


def css_urls(css: Path) -> list[str]:
    return re.findall(r"""url\(\s*["']?([^"')]+)["']?\s*\)""", css.read_text(encoding="utf-8"))


class SiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {f"{app.slug}/{lang.code}": page_file(app, lang).read_text(encoding="utf-8")
                     for app in APPS for lang in app.langs}
        cls.pages["home"] = HOME.read_text(encoding="utf-8")
        cls.tags = {code: Tags(html) for code, html in cls.pages.items()}
        cls.css = CSS.read_text(encoding="utf-8")

    def test_pages_exist(self):
        for app in APPS:
            for lang in app.langs:
                self.assertTrue(page_file(app, lang).is_file(), f"{app.slug}/{lang.code}")

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
        for app in APPS:
            sets = {code: {(a["hreflang"], a["href"]) for t, a in tags.tags
                           if t == "link" and a.get("rel") == "alternate"}
                    for code, tags in self.tags.items() if code.startswith(app.slug + "/")}
            with self.subTest(app=app.slug):
                self.assertEqual(len(sets), len(app.langs))
                self.assertEqual(len({frozenset(s) for s in sets.values()}), 1)
                alternates = sets[f"{app.slug}/en"]
                self.assertEqual(len(alternates), len(app.langs) + 1)
                self.assertTrue(all(href.startswith(f"{SITE_URL}/{app.slug}/") for _, href in alternates))

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

    def test_theme_fonts(self):
        theme = ATLAS_THEME.read_text(encoding="utf-8")
        self.assertEqual(theme.count("@font-face"), 3)
        self.assertEqual(theme.count("font-display: swap"), 3)
        faces = theme.split("@font-face")[1:]
        cyrillic = [face for face in faces if "montserrat-cyrillic-700-normal.woff2" in face]
        self.assertEqual(len(cyrillic), 1)
        self.assertIn("U+0400-045F", cyrillic[0])

    def test_syllabee_theme_rules(self):
        theme = SYLLABEE_THEME.read_text(encoding="utf-8")
        self.assertEqual(theme.count("@font-face"), 3)
        self.assertEqual(theme.count("font-display: swap"), 3)
        faces = theme.split("@font-face")[1:]
        cyrillic = [face for face in faces if "nunito-cyrillic-800-normal.woff2" in face]
        self.assertEqual(len(cyrillic), 1)
        self.assertIn("U+0400-045F", cyrillic[0])
        # The hero's tilted cards stay inside the page; long theme names wrap inside their tiles.
        self.assertRegex(theme, r"(?m)^body \{[^}]*overflow-x: clip;")
        self.assertRegex(theme, r"\.tile \.name \{[^}]*overflow-wrap: anywhere;")

    def test_shared_rules_use_tokens(self):
        # Outside :root, the shared stylesheet names no Art Widget colour, so a theme changes colours through the tokens
        # alone and never restyles a shared rule.
        rules = re.sub(r":root \{.*?\}", "", self.css, count=1, flags=re.S)
        for colour in ("rgba(233, 217, 180", "rgba(217, 164, 65", "#D9A441", "#F8DE94", "#E9D9B4"):
            self.assertNotIn(colour, rules)
        theme = ATLAS_THEME.read_text(encoding="utf-8")
        self.assertNotIn(".lang summary", theme)
        self.assertNotIn(".lang ul", theme)

    def test_atlas_page_cannot_scroll_sideways(self):
        # The hero's tilted phones stay inside the page by geometry; the body's clip is the safety net if a size changes.
        theme = ATLAS_THEME.read_text(encoding="utf-8")
        self.assertRegex(theme, r"(?m)^body \{[^}]*overflow-x: clip;")

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

    def test_atlas_video_sizes(self):
        for lang in LANGS:
            with self.subTest(code=lang.code):
                video = ATLAS_HUNT.assets / "video" / f"{lang.code}.mp4"
                self.assertLessEqual(video.stat().st_size, 6 * 1024 * 1024)
                self.assertTrue((ATLAS_HUNT.assets / "video" / f"{lang.code}-poster.webp").is_file())

    def test_syllabee_videos(self):
        for lang in SYLLABEE.langs:
            with self.subTest(code=lang.code):
                video = SYLLABEE.assets / "video" / f"{lang.code}.mp4"
                self.assertLessEqual(video.stat().st_size, 6 * 1024 * 1024)
                self.assertTrue((SYLLABEE.assets / "video" / f"{lang.code}-poster.webp").is_file())

    def test_syllabee_pages_name_their_own_app(self):
        packages = {SYLLABEE.package_in(lang) for lang in SYLLABEE.langs}
        for lang in SYLLABEE.langs:
            key = f"syllabee/{lang.code}"
            html, tags = self.pages[key], self.tags[key]
            with self.subTest(page=key):
                self.assertEqual(len(tags.find("a", href=play_url(SYLLABEE, lang))), 2)
                self.assertEqual([p for p in packages - {SYLLABEE.package_in(lang)} if p in html], [])
                self.assertEqual([a["content"] for a in tags.find("meta", property="og:image")],
                                 [f"{SITE_URL}/syllabee/assets/img/{lang.code}/og.jpg"])
                self.assertEqual(len(tags.find("source", src=f"/syllabee/assets/video/{lang.code}.mp4")), 1)

    def test_syllabee_drawings(self):
        used = {url for key, tags in self.tags.items() if key.startswith("syllabee/")
                for url in requested_urls(tags) if "/img/art/" in url}
        self.assertTrue(used)
        for url in used:
            with self.subTest(url=url):
                self.assertTrue(local_file(url).read_text(encoding="utf-8").startswith("<svg"))
                self.assertNotIn(Path(url).stem, NEEDS_ATTRIBUTION)
        folder = SYLLABEE.assets / "img" / "art"
        self.assertEqual({path.name for path in folder.iterdir()}, {Path(url).name for url in used})

    @unittest.skipUnless(ATLAS_SIBLING.is_dir(), "needs ../atlas_hunt")
    def test_gallery_matches_listings(self):
        for lang in LANGS:
            with self.subTest(code=lang.code):
                shots = gallery_shots(ATLAS_HUNT.graphics(ATLAS_SIBLING, lang))
                self.assertEqual('class="gallery"' in self.pages[f"atlashunt/{lang.code}"], bool(shots))
                # Exactly the listing's shots are published: a removed or renamed shot leaves no file behind.
                folder = ATLAS_HUNT.assets / "img" / lang.code / "gallery"
                published = {path.name for path in folder.glob("*")} if folder.is_dir() else set()
                self.assertEqual(published, {f"{screen}-{width}.webp" for screen, _ in shots
                                             for width in (160, 320, 540, 1080)})

    def test_atlas_card_links_page(self):
        self.assertEqual(len(self.tags["home"].find("a", href="/atlashunt/")), 1)

    def test_syllabee_card_links_page(self):
        self.assertEqual(len(self.tags["home"].find("a", href="/syllabee/")), 1)
        self.assertNotIn("Coming soon", self.pages["home"])

    def test_no_soon_style(self):
        self.assertNotIn(".soon", self.css)

    def test_foreign_assets(self):
        urls = ["/atlashunt/assets/img/da/hero-left-200.webp", "/atlashunt/assets/img/levels/earth-64.webp",
                "/atlashunt/assets/img/icon-64.webp", "/atlashunt/assets/img/en/gallery/dark-160.webp",
                "/atlashunt/assets/video/en.mp4", "/atlashunt/assets/video/da-poster.webp", "/assets/badges/en.png"]
        self.assertEqual(foreign_assets("atlashunt", "da", urls),
                         ["/atlashunt/assets/img/en/gallery/dark-160.webp", "/atlashunt/assets/video/en.mp4"])

    def test_each_page_shows_its_own_language(self):
        # The spec's anti-goal: a page in one language showing the app in another.
        for key, tags in self.tags.items():
            if key == "home":
                continue
            slug, code = key.split("/")
            urls = requested_urls(tags)
            urls += [a["content"] for t, a in tags.tags if t == "meta" and a.get("property") == "og:image"]
            with self.subTest(page=key):
                self.assertEqual(foreign_assets(slug, code, urls), [])
                if slug == ATLAS_HUNT.slug:
                    self.assertIn(f"/atlashunt/assets/video/{code}.mp4", urls)

    def test_no_stale_generator_path(self):
        # The generator moved to _build/site; no kept file should name its old folder.
        old = "/".join(("_build", "artwidget"))
        files = subprocess.run(["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True).stdout
        for name in files.splitlines():
            path = ROOT / name
            if path.suffix in {".py", ".html", ".css", ".md", ".toml", ".yml", ".txt", ".xml"} and path.is_file():
                self.assertFalse(old in path.read_text(encoding="utf-8"), f"{name} names {old}")

    def test_gallery_has_large_shots(self):
        # The strip's thumbnails at 160 and 320; each popover's shot at 540 and 1080, as tall as the screen allows.
        tags = self.tags["atlashunt/en"]
        shots = [a for a in tags.find("img") if "/gallery/" in a["src"]]
        self.assertEqual(len(shots), 15)
        for shot in shots:
            widths = [int(entry.split()[1].rstrip("w")) for entry in shot["srcset"].split(",")]
            self.assertEqual(widths, [160, 320])
        large = [url for url in requested_urls(tags) if "/gallery/" in url and url.endswith(("-540.webp", "-1080.webp"))]
        self.assertEqual(len(set(large)), 30)

    def test_favicon(self):
        with Image.open(ROOT / "favicon.ico") as icon:
            self.assertEqual(icon.format, "ICO")
            self.assertEqual(sorted(icon.info["sizes"]), [(16, 16), (32, 32), (48, 48)])
        with Image.open(ROOT / "apple-touch-icon.png") as touch:
            self.assertEqual((touch.format, touch.size), ("PNG", (180, 180)))

    def test_hero_painting_has_a_middle_size(self):
        starry = [a for a in self.tags["artwidget/en"].find("img") if a["src"].startswith("/artwidget/assets/img/starry")]
        widths = [int(entry.split()[1].rstrip("w")) for entry in starry[0]["srcset"].split(",")]
        self.assertEqual(widths, [480, 720, 960])

    def test_readme_served(self):
        # Every policy's Contact line links to /README.md
        self.assertTrue((ROOT / "README.md").is_file())
        excluded = [line.strip()[2:].strip() for line in (ROOT / "_config.yml").read_text(encoding="utf-8").splitlines()
                    if line.strip().startswith("- ")]
        self.assertNotIn("README.md", excluded)
