"""Builds the Art Widget pages, artwidget/index.html and artwidget/<code>/index.html, with their images and video
under artwidget/assets/, from the Art Widget repository's store graphics and preview video."""
from pathlib import Path

from assets import transcode_video
from config import ART_WIDGET, LANGS, VENDOR_DIR
from output import app_webp, badge
from pages import app_icon, listing_graphics, phone_shots, write_page

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
    default_graphics = listing_graphics(repo, LANGS[0])
    shared = {
        "icon": app_icon(ART_WIDGET, default_graphics),
        "starry": app_webp(ART_WIDGET, VENDOR_DIR / "art" / "starry-night.jpg", "img", "starry-night",
                           (480, 720, 960)),
        "pearl": app_webp(ART_WIDGET, VENDOR_DIR / "art" / "pearl-earring.jpg", "img", "pearl-earring", (240, 480)),
    }
    transcode_video(default_graphics.parent / "video.mp4", ASSETS / "video" / "preview.mp4",
                    ASSETS / "video" / "preview-poster.webp")

    for lang in LANGS:
        graphics = listing_graphics(repo, lang)
        pictures = shared | phone_shots(ART_WIDGET, graphics, lang, SHOTS) | {"badge": badge(lang)}
        write_page(ART_WIDGET, lang, graphics, strings[lang.code], pictures, video=VIDEO_URL, poster=POSTER_URL,
                   commons=COMMONS_PAGES)
