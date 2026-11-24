import unittest
import xml.etree.ElementTree as ET

from sitemap import ROBOTS_TXT, render_sitemap

SM = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
XHTML = "{http://www.w3.org/1999/xhtml}"


class SitemapTest(unittest.TestCase):
    def test_sitemap(self):
        root = ET.fromstring(render_sitemap())
        urls = root.findall(f"{SM}url")
        self.assertEqual(len(urls), 6)
        for url in urls:
            self.assertEqual(len(url.findall(f"{XHTML}link")), 7)
        self.assertEqual(urls[0].find(f"{SM}loc").text, "https://forio-dk.github.io/artwidget/")

    def test_robots(self):
        self.assertTrue(ROBOTS_TXT.endswith("Sitemap: https://forio-dk.github.io/sitemap.xml\n"))
