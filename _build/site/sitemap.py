"""The site's sitemap.xml (the home page, then each app's pages, each naming its translations) and robots.txt."""
from xml.sax.saxutils import quoteattr

from config import APPS, LANGS, SITE_URL, App, Lang, page_url

ROBOTS_TXT = f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n"


def app_urls(app: App, langs: tuple[Lang, ...]) -> str:
    """The <url> entries of one app's pages, each listing every language's page and the x-default."""
    alternates = [(lang.code, page_url(app, lang)) for lang in langs] + [("x-default", page_url(app, langs[0]))]
    links = "".join(f"    <xhtml:link rel=\"alternate\" hreflang={quoteattr(code)} href={quoteattr(url)}/>\n"
                    for code, url in alternates)
    return "".join(f"  <url>\n    <loc>{page_url(app, lang)}</loc>\n{links}  </url>\n" for lang in langs)


def render_sitemap(apps: tuple[App, ...] = APPS, langs: tuple[Lang, ...] = LANGS) -> str:
    urls = f"  <url>\n    <loc>{SITE_URL}/</loc>\n  </url>\n"
    urls += "".join(app_urls(app, langs) for app in apps)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            f"{urls}</urlset>\n")
