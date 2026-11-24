"""The site's sitemap.xml (the six Art Widget pages, each naming its translations) and robots.txt."""
from xml.sax.saxutils import quoteattr

from config import LANGS, SITE_URL, Lang, page_url

ROBOTS_TXT = f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n"


def render_sitemap(langs: tuple[Lang, ...] = LANGS) -> str:
    alternates = [(lang.code, page_url(lang)) for lang in langs] + [("x-default", page_url(langs[0]))]
    links = "".join(f"    <xhtml:link rel=\"alternate\" hreflang={quoteattr(code)} href={quoteattr(url)}/>\n"
                    for code, url in alternates)
    urls = "".join(f"  <url>\n    <loc>{page_url(lang)}</loc>\n{links}  </url>\n" for lang in langs)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            f"{urls}</urlset>\n")
