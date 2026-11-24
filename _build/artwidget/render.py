"""Renders one language's Art Widget home page from template.html."""
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from jinja2.exceptions import UndefinedError

from assets import Picture
from config import (ASSETS_URL, BUILD, COMMONS_PAGES, LANGS, POSTER_URL, SITE_URL, VIDEO_URL, Lang, page_path,
                    page_url, play_url)

ENV = Environment(loader=FileSystemLoader(BUILD), autoescape=True, undefined=StrictUndefined,
                  trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)


def og_image_url(lang: Lang) -> str:
    return f"{SITE_URL}{ASSETS_URL}/img/{lang.code}/og.jpg"


def string(s: dict, *keys: str) -> str:
    """One string from a language's strings, failing the way the template does when it is missing."""
    value = s
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            raise UndefinedError(f"'{'.'.join(keys)}' is undefined")
        value = value[key]
    return value


def json_ld(lang: Lang, s: dict) -> dict:
    """schema.org data for search engines: the app, free on Google Play. No ratings: the page has none of its own."""
    return {
        "@context": "https://schema.org",
        "@type": "MobileApplication",
        "name": "Art Widget",
        "description": string(s, "hero", "lead"),
        "operatingSystem": "Android 8.0+",
        "applicationCategory": "DesktopEnhancementApplication",
        "inLanguage": lang.code,
        "url": page_url(lang),
        "image": og_image_url(lang),
        "installUrl": play_url(lang),
        "downloadUrl": play_url(lang),
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "author": {"@type": "Organization", "name": "Forio"},
    }


def render_page(lang: Lang, s: dict, pictures: dict[str, Picture], langs: tuple[Lang, ...] = LANGS) -> str:
    return ENV.get_template("template.html").render(
        lang=lang, s=s, p=pictures, langs=langs, default=langs[0], page_url=page_url, page_path=page_path,
        play=play_url(lang), og_image=og_image_url(lang), json_ld=json_ld(lang, s), assets=ASSETS_URL,
        video=VIDEO_URL, poster=POSTER_URL, commons=COMMONS_PAGES)


def render_home(pictures: dict[str, Picture]) -> str:
    """The site's home page, English only: a card per app. pictures holds the art_widget, atlas_hunt and syllabee
    icons."""
    return ENV.get_template("home.html").render(p=pictures, site=SITE_URL + "/", assets=ASSETS_URL)
