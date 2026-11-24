import unittest
import xml.etree.ElementTree as ET

from sitemap import ROBOTS_TXT, render_sitemap

SM = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
XHTML = "{http://www.w3.org/1999/xhtml}"


class SitemapTest(unittest.TestCase):
    def test_sitemap(self):
        root = ET.fromstring(render_sitemap())
        urls = root.findall(f"{SM}url")
        self.assertEqual(len(urls), 13)
        self.assertEqual(urls[0].find(f"{SM}loc").text, "https://forio-dk.github.io/")
        self.assertEqual(urls[0].findall(f"{XHTML}link"), [])
        for url in urls[1:]:
            self.assertEqual(len(url.findall(f"{XHTML}link")), 7)
        self.assertEqual(urls[1].find(f"{SM}loc").text, "https://forio-dk.github.io/artwidget/")
        self.assertEqual(urls[7].find(f"{SM}loc").text, "https://forio-dk.github.io/atlashunt/")
        for url in urls[7:]:
            hrefs = [link.get("href") for link in url.findall(f"{XHTML}link")]
            self.assertTrue(all(href.startswith("https://forio-dk.github.io/atlashunt/") for href in hrefs), hrefs)

    def test_robots(self):
        self.assertTrue(ROBOTS_TXT.endswith("Sitemap: https://forio-dk.github.io/sitemap.xml\n"))
