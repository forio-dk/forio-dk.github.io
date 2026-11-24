"""Paths, URLs and the list of downloaded inputs for the Art Widget home page generator."""
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "_build" / "artwidget"
VENDOR_DIR = BUILD / "vendor"
STRINGS = BUILD / "strings"
SITE = ROOT / "artwidget"
ASSETS = SITE / "assets"
ASSETS_URL = "/artwidget/assets"

PLAYFAIR = "https://cdn.jsdelivr.net/npm/@fontsource/playfair-display@5.3.0"
SOURCE_SANS = "https://cdn.jsdelivr.net/npm/@fontsource/source-sans-3@5.3.1"
SUBSETS = ("latin", "latin-ext", "cyrillic")
BADGE = "https://play.google.com/intl/en_us/badges/static/images/badges/{}_badge_web_generic.png"
COMMONS = "https://commons.wikimedia.org/wiki/Special:FilePath/{}?width=1200"
# Page language code -> Google's badge code; Google names the Ukrainian badge "ua" ("uk" is a 404).
BADGE_CODES = {"en": "en", "da": "da", "it": "it", "ro": "ro", "ru": "ru", "uk": "ua"}

# Each file in vendor/, relative to VENDOR_DIR, and where it was downloaded from.
VENDOR: dict[str, str] = {
    **{f"fonts/playfair-display-{s}-600-normal.woff2": f"{PLAYFAIR}/files/playfair-display-{s}-600-normal.woff2"
       for s in SUBSETS},
    **{f"fonts/source-sans-3-{s}-{w}-normal.woff2": f"{SOURCE_SANS}/files/source-sans-3-{s}-{w}-normal.woff2"
       for s in SUBSETS for w in (400, 600)},
    "fonts/playfair-display-600.css": f"{PLAYFAIR}/600.css",
    "fonts/source-sans-3-400.css": f"{SOURCE_SANS}/400.css",
    "fonts/source-sans-3-600.css": f"{SOURCE_SANS}/600.css",
    "fonts/OFL-playfair-display.txt": f"{PLAYFAIR}/LICENSE",
    "fonts/OFL-source-sans-3.txt": f"{SOURCE_SANS}/LICENSE",
    **{f"badges/{code}.png": BADGE.format(badge) for code, badge in BADGE_CODES.items()},
    "art/starry-night.jpg": COMMONS.format("Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg"),
    "art/pearl-earring.jpg": COMMONS.format("1665_Girl_with_a_Pearl_Earring.jpg"),
}

# Files copied once from the sibling app repositories (paths relative to ROOT.parent), for the home page's app cards.
LOCAL_VENDOR: dict[str, str] = {
    "icons/atlas-hunt.png": "atlas_hunt/docs/listings/en-US/graphics/icon-512.png",
    "icons/syllabee.png": "learn_to_read/docs/store/en/icon-512.png",
}


@dataclass(frozen=True)
class Lang:
    code: str  # html lang, hreflang, Play's hl and the page's folder (English, the default, has none)
    listing: str  # folder in ../art_widget/docs/listings
    name: str  # the language's own name, for the switcher
    og_locale: str
    font_subset: str  # "latin" or "cyrillic": the heading font file to preload


LANGS = (
    Lang("en", "en-US", "English", "en_US", "latin"),
    Lang("da", "da-DK", "Dansk", "da_DK", "latin"),
    Lang("it", "it-IT", "Italiano", "it_IT", "latin"),
    Lang("ro", "ro", "Română", "ro_RO", "latin"),
    Lang("ru", "ru-RU", "Русский", "ru_RU", "cyrillic"),
    Lang("uk", "uk", "Українська", "uk_UA", "cyrillic"),
)

SITE_URL = "https://forio-dk.github.io"
PACKAGE = "dk.forio.artwidget"
REFERRER = "utm_source%3Dforio-dk.github.io%26utm_medium%3Dwebsite%26utm_campaign%3Dartwidget-home"
VIDEO_URL = ASSETS_URL + "/video/preview.mp4"
POSTER_URL = ASSETS_URL + "/video/preview-poster.webp"
COMMONS_PAGES = {
    "starry": "https://commons.wikimedia.org/wiki/File:Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
    "pearl": "https://commons.wikimedia.org/wiki/File:1665_Girl_with_a_Pearl_Earring.jpg",
}


def is_default(lang: Lang) -> bool:
    return lang.code == LANGS[0].code


def page_path(lang: Lang) -> str:
    return "/artwidget/" if is_default(lang) else f"/artwidget/{lang.code}/"


def page_url(lang: Lang) -> str:
    return SITE_URL + page_path(lang)


def page_file(lang: Lang) -> Path:
    return SITE / "index.html" if is_default(lang) else SITE / lang.code / "index.html"


def play_url(lang: Lang) -> str:
    return f"https://play.google.com/store/apps/details?id={PACKAGE}&hl={lang.code}&referrer={REFERRER}"
