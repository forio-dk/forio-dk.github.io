"""Renders the generated pages: each app's page in each language (apps/<slug>/template.html) and the home page
(home.html)."""
from functools import partial

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from jinja2.exceptions import UndefinedError

from assets import Picture
from config import BUILD, LANGS, SHARED_URL, SITE_URL, App, Lang, page_path, page_url, play_url
from plural import plural_category

ENV = Environment(loader=FileSystemLoader(BUILD), autoescape=True, undefined=StrictUndefined,
                  trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
ENV.globals["plural"] = plural_category  # plural(code, n): the form of a counted string to use, see plural.py


def og_image_url(app: App, lang: Lang) -> str:
    return f"{SITE_URL}{app.assets_url}/img/{lang.code}/og.jpg"


def string(s: dict, *keys: str) -> str:
    """One string from a language's strings, failing the way the template does when it is missing."""
    value = s
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            raise UndefinedError(f"'{'.'.join(keys)}' is undefined")
        value = value[key]
    return value


def json_ld(app: App, lang: Lang, s: dict) -> dict:
    """schema.org data for search engines: the app, free on Google Play. No ratings: the page has none of its own."""
    return {
        "@context": "https://schema.org",
        "@type": "MobileApplication",
        "name": app.name,
        "description": string(s, "hero", "lead"),
        "operatingSystem": "Android 8.0+",
        "applicationCategory": app.category,
        "inLanguage": lang.code,
        "url": page_url(app, lang),
        "image": og_image_url(app, lang),
        "installUrl": play_url(app, lang),
        "downloadUrl": play_url(app, lang),
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "author": {"@type": "Organization", "name": "Forio"},
    }


def render_page(app: App, lang: Lang, s: dict, pictures: dict[str, Picture], langs: tuple[Lang, ...] = LANGS,
                **extra) -> str:
    """One language's page of an app. extra holds what only that app's template uses (its video, for example)."""
    return ENV.get_template(app.template).render(
        app=app, lang=lang, s=s, p=pictures, langs=langs, default=langs[0], page_url=partial(page_url, app),
        page_path=partial(page_path, app), play=play_url(app, lang), og_image=og_image_url(app, lang),
        json_ld=json_ld(app, lang, s), assets=app.assets_url, shared=SHARED_URL, **extra)


def render_home(pictures: dict[str, Picture]) -> str:
    """The site's home page, English only: a card per app. pictures holds the art_widget, atlas_hunt and syllabee
    icons."""
    return ENV.get_template("home.html").render(p=pictures, site=SITE_URL + "/", shared=SHARED_URL)
