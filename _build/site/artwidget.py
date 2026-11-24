"""Builds the Art Widget pages, artwidget/index.html and artwidget/<code>/index.html, with their images and video
under artwidget/assets/, from the Art Widget repository's store graphics and preview video."""
from pathlib import Path

from assets import favicons, og_jpeg, transcode_video
from config import ART_WIDGET, LANGS, VENDOR_DIR, page_file
from output import app_webp, badge, write_text
from render import render_page

ASSETS = ART_WIDGET.assets
SHOTS = {"shot_widget": "phone-1-widget.png", "shot_details": "phone-2-details.png",
         "shot_settings": "phone-4-settings.png"}
VIDEO_URL = ART_WIDGET.assets_url + "/video/preview.mp4"
POSTER_URL = ART_WIDGET.assets_url + "/video/preview-poster.webp"
COMMONS_PAGES = {
    "starry": "https://commons.wikimedia.org/wiki/File:Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
    "pearl": "https://commons.wikimedia.org/wiki/File:1665_Girl_with_a_Pearl_Earring.jpg",
}


def build_pages(repo: Path, strings: dict[str, dict]) -> None:
    listings = repo / "docs" / "listings"
    default_graphics = listings / LANGS[0].listing / "graphics"

    favicons(default_graphics / "icon-512.png", ASSETS / "img")
    shared = {
        "icon": app_webp(ART_WIDGET, default_graphics / "icon-512.png", "img", "icon", (64, 128)),
        "starry": app_webp(ART_WIDGET, VENDOR_DIR / "art" / "starry-night.jpg", "img", "starry-night",
                           (480, 720, 960)),
        "pearl": app_webp(ART_WIDGET, VENDOR_DIR / "art" / "pearl-earring.jpg", "img", "pearl-earring", (240, 480)),
    }
    transcode_video(listings / LANGS[0].listing / "video.mp4", ASSETS / "video" / "preview.mp4",
                    ASSETS / "video" / "preview-poster.webp")

    for lang in LANGS:
        graphics = listings / lang.listing / "graphics"
        pictures = dict(shared, badge=badge(lang))
        for key, name in SHOTS.items():
            pictures[key] = app_webp(ART_WIDGET, graphics / name, f"img/{lang.code}", key.replace("_", "-"),
                                     (200, 400))
        og_jpeg(graphics / "feature-graphic.png", ASSETS / "img" / lang.code / "og.jpg")
        html = render_page(ART_WIDGET, lang, strings[lang.code], pictures, video=VIDEO_URL, poster=POSTER_URL,
                           commons=COMMONS_PAGES)
        write_text(page_file(ART_WIDGET, lang), html)
