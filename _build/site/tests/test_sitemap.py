import unittest
import xml.etree.ElementTree as ET

from sitemap import ROBOTS_TXT, render_sitemap

SM = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
XHTML = "{http://www.w3.org/1999/xhtml}"


class SitemapTest(unittest.TestCase):
    def test_sitemap(self):
        root = ET.fromstring(render_sitemap())
        urls = root.findall(f"{SM}url")
        self.assertEqual(len(urls), 17)
        self.assertEqual(urls[0].find(f"{SM}loc").text, "https://forio-dk.github.io/")
        self.assertEqual(urls[0].findall(f"{XHTML}link"), [])
        self.assertEqual([len(url.findall(f"{XHTML}link")) for url in urls[1:]], [7] * 12 + [5] * 4)
        self.assertEqual(urls[1].find(f"{SM}loc").text, "https://forio-dk.github.io/artwidget/")
        self.assertEqual(urls[7].find(f"{SM}loc").text, "https://forio-dk.github.io/atlashunt/")
        self.assertEqual(urls[13].find(f"{SM}loc").text, "https://forio-dk.github.io/syllabee/")
        for start, slug in ((7, "atlashunt"), (13, "syllabee")):
            for url in urls[start:start + 6]:
                hrefs = [link.get("href") for link in url.findall(f"{XHTML}link")]
                self.assertTrue(all(href.startswith(f"https://forio-dk.github.io/{slug}/") for href in hrefs), hrefs)

    def test_robots(self):
        self.assertTrue(ROBOTS_TXT.endswith("Sitemap: https://forio-dk.github.io/sitemap.xml\n"))
