"""Paths, languages, apps, URLs and the list of downloaded inputs for the site generator (the home page and each
app's page)."""
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "_build" / "site"
VENDOR_DIR = BUILD / "vendor"
SHARED = ROOT / "assets"  # what every page shares: fonts, badges, the base stylesheet, the home page's icons
SHARED_URL = "/assets"

PLAYFAIR = "https://cdn.jsdelivr.net/npm/@fontsource/playfair-display@5.3.0"
SOURCE_SANS = "https://cdn.jsdelivr.net/npm/@fontsource/source-sans-3@5.3.1"
MONTSERRAT = "https://cdn.jsdelivr.net/npm/@fontsource/montserrat@5.3.0"  # Atlas Hunt's headings, as in its store graphics
SUBSETS = ("latin", "latin-ext", "cyrillic")
BADGE = "https://play.google.com/intl/en_us/badges/static/images/badges/{}_badge_web_generic.png"
COMMONS = "https://commons.wikimedia.org/wiki/Special:FilePath/{}?width=1200"


@dataclass(frozen=True)
class Lang:
    code: str  # html lang, hreflang, Play's hl and the page's folder (English, the default, has none)
    listing: str  # folder in each app repository's docs/listings
    name: str  # the language's own name, for the switcher
    og_locale: str
    font_subset: str  # "latin" or "cyrillic": the heading font file to preload
    badge: str  # Google's code for the Get it on Google Play badge; Ukrainian's is "ua" ("uk" is a 404)


LANGS = (
    Lang("en", "en-US", "English", "en_US", "latin", "en"),
    Lang("da", "da-DK", "Dansk", "da_DK", "latin", "da"),
    Lang("it", "it-IT", "Italiano", "it_IT", "latin", "it"),
    Lang("ro", "ro", "Română", "ro_RO", "latin", "ro"),
    Lang("ru", "ru-RU", "Русский", "ru_RU", "cyrillic", "ru"),
    Lang("uk", "uk", "Українська", "uk_UA", "cyrillic", "ua"),
)


@dataclass(frozen=True)
class App:
    """An app with a page of its own: /<slug>/ in English and /<slug>/<code>/ in the other languages."""
    slug: str  # the page's folder, apps/<slug>/ here, and the Play referrer's campaign "<slug>-home"
    name: str
    package: str
    repo: str  # the app's repository, a sibling of this one
    theme_color: str
    category: str  # schema.org applicationCategory
    heading_font: str  # the heading font's file in /assets/fonts, with {subset}: the one the page preloads

    @property
    def site(self) -> Path:
        return ROOT / self.slug

    @property
    def assets(self) -> Path:
        return self.site / "assets"

    @property
    def assets_url(self) -> str:
        return f"/{self.slug}/assets"

    @property
    def folder(self) -> Path:
        return BUILD / "apps" / self.slug

    @property
    def strings(self) -> Path:
        return self.folder / "strings"

    @property
    def template(self) -> str:
        return f"apps/{self.slug}/template.html"


ART_WIDGET = App("artwidget", "Art Widget", "dk.forio.artwidget", "art_widget", "#132841",
                 "DesktopEnhancementApplication", "playfair-display-{subset}-600-normal.woff2")
ATLAS_HUNT = App("atlashunt", "Atlas Hunt", "dk.forio.atlashunt", "atlas_hunt", "#0B2A3C", "GameApplication",
                 "montserrat-{subset}-700-normal.woff2")
APPS: tuple[App, ...] = (ART_WIDGET,)

# Each file in vendor/, relative to VENDOR_DIR, and where it was downloaded from.
VENDOR: dict[str, str] = {
    **{f"fonts/playfair-display-{s}-600-normal.woff2": f"{PLAYFAIR}/files/playfair-display-{s}-600-normal.woff2"
       for s in SUBSETS},
    **{f"fonts/source-sans-3-{s}-{w}-normal.woff2": f"{SOURCE_SANS}/files/source-sans-3-{s}-{w}-normal.woff2"
       for s in SUBSETS for w in (400, 600)},
    "fonts/playfair-display-600.css": f"{PLAYFAIR}/600.css",
    # The heading font as TrueType, which Pillow needs to draw the Forio logo's F.
    "fonts/playfair-display-latin-600-normal.ttf":
        "https://cdn.jsdelivr.net/fontsource/fonts/playfair-display@5.3.0/latin-600-normal.ttf",
    "fonts/source-sans-3-400.css": f"{SOURCE_SANS}/400.css",
    "fonts/source-sans-3-600.css": f"{SOURCE_SANS}/600.css",
    "fonts/OFL-playfair-display.txt": f"{PLAYFAIR}/LICENSE",
    "fonts/OFL-source-sans-3.txt": f"{SOURCE_SANS}/LICENSE",
    **{f"fonts/montserrat-{s}-700-normal.woff2": f"{MONTSERRAT}/files/montserrat-{s}-700-normal.woff2" for s in SUBSETS},
    "fonts/montserrat-700.css": f"{MONTSERRAT}/700.css",
    "fonts/OFL-montserrat.txt": f"{MONTSERRAT}/LICENSE",
    **{f"badges/{lang.code}.png": BADGE.format(lang.badge) for lang in LANGS},
    "art/starry-night.jpg": COMMONS.format("Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg"),
    "art/pearl-earring.jpg": COMMONS.format("1665_Girl_with_a_Pearl_Earring.jpg"),
}

# Files copied once from the sibling app repositories (paths relative to ROOT.parent), for the home page's app cards.
LOCAL_VENDOR: dict[str, str] = {
    "icons/atlas-hunt.png": "atlas_hunt/docs/listings/en-US/graphics/icon-512.png",
    "icons/syllabee.png": "learn_to_read/docs/store/en/icon-512.png",
}

SITE_URL = "https://forio-dk.github.io"


def is_default(lang: Lang) -> bool:
    return lang.code == LANGS[0].code


def page_path(app: App, lang: Lang) -> str:
    return f"/{app.slug}/" if is_default(lang) else f"/{app.slug}/{lang.code}/"


def page_url(app: App, lang: Lang) -> str:
    return SITE_URL + page_path(app, lang)


def page_file(app: App, lang: Lang) -> Path:
    return app.site / "index.html" if is_default(lang) else app.site / lang.code / "index.html"


def play_url(app: App, lang: Lang) -> str:
    referrer = f"utm_source%3Dforio-dk.github.io%26utm_medium%3Dwebsite%26utm_campaign%3D{app.slug}-home"
    return f"https://play.google.com/store/apps/details?id={app.package}&hl={lang.code}&referrer={referrer}"
