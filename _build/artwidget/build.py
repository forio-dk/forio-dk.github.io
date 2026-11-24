"""Generates the Art Widget home pages: artwidget/index.html and artwidget/<code>/index.html, their images, fonts,
badges and video under artwidget/assets/, and the site's sitemap.xml and robots.txt.

Run from the repository root: python -X utf8 _build/artwidget/build.py [--art-widget ../art_widget]
It reads the store graphics and preview video from the Art Widget repository and the downloads in vendor/, and
writes only what changed, so a second run leaves git status clean. artwidget/assets/site.css is hand-written.
"""
import argparse
import shutil
import sys
from pathlib import Path

from PIL import Image

from assets import Picture, favicons, og_jpeg, responsive_webp, transcode_video
from config import ASSETS, ASSETS_URL, LANGS, ROOT, VENDOR_DIR, Lang, page_file
from render import render_page
from sitemap import ROBOTS_TXT, render_sitemap
from strings import load_strings, shape_errors

SHOTS = {"shot_widget": "phone-1-widget.png", "shot_details": "phone-2-details.png",
         "shot_settings": "phone-4-settings.png"}


def write_text(path: Path, text: str) -> bool:
    """Writes UTF-8 text with \\n line endings, only when the content differs. Returns whether it wrote."""
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


def copy_file(src: Path, dst: Path) -> None:
    if dst.is_file() and dst.read_bytes() == src.read_bytes():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def webp(src: Path, folder: str, stem: str, widths: tuple[int, ...]) -> Picture:
    """A WebP set under artwidget/assets/<folder>, served at the matching URL."""
    return responsive_webp(src, ASSETS / folder, f"{ASSETS_URL}/{folder}", stem, widths)


def badge(lang: Lang) -> Picture:
    dst = ASSETS / "badges" / f"{lang.code}.png"
    copy_file(VENDOR_DIR / "badges" / f"{lang.code}.png", dst)
    with Image.open(dst) as image:
        return Picture(f"{ASSETS_URL}/badges/{lang.code}.png", "", image.width, image.height)


def build(art_widget: Path) -> None:
    listings = art_widget / "docs" / "listings"
    default_graphics = listings / LANGS[0].listing / "graphics"
    strings = load_strings(lang.code for lang in LANGS)

    favicons(default_graphics / "icon-512.png", ASSETS / "img")
    shared = {
        "icon": webp(default_graphics / "icon-512.png", "img", "icon", (64, 128)),
        "starry": webp(VENDOR_DIR / "art" / "starry-night.jpg", "img", "starry-night", (480, 960)),
        "pearl": webp(VENDOR_DIR / "art" / "pearl-earring.jpg", "img", "pearl-earring", (240, 480)),
    }
    for font in sorted((VENDOR_DIR / "fonts").glob("*.woff2")) + sorted((VENDOR_DIR / "fonts").glob("OFL-*.txt")):
        copy_file(font, ASSETS / "fonts" / font.name)
    transcode_video(listings / LANGS[0].listing / "video.mp4", ASSETS / "video" / "preview.mp4",
                    ASSETS / "video" / "preview-poster.webp")

    for lang in LANGS:
        graphics = listings / lang.listing / "graphics"
        pictures = dict(shared, badge=badge(lang))
        for key, name in SHOTS.items():
            pictures[key] = webp(graphics / name, f"img/{lang.code}", key.replace("_", "-"), (200, 400))
        og_jpeg(graphics / "feature-graphic.png", ASSETS / "img" / lang.code / "og.jpg")
        write_text(page_file(lang), render_page(lang, strings[lang.code], pictures))

    write_text(ROOT / "sitemap.xml", render_sitemap())
    write_text(ROOT / "robots.txt", ROBOTS_TXT)


def problems(art_widget: Path) -> list[str]:
    """What stops a build: a missing Art Widget repository, or a language whose strings differ from English's."""
    if not (art_widget / "docs" / "listings").is_dir():
        return [f"{art_widget} is not the Art Widget repository (no docs/listings); pass --art-widget"]
    strings = load_strings(lang.code for lang in LANGS)
    english = strings[LANGS[0].code]
    return [f"strings/{lang.code}.toml: {error}" for lang in LANGS[1:]
            for error in shape_errors(english, strings[lang.code])]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--art-widget", type=Path, default=ROOT.parent / "art_widget",
                        help="the Art Widget repository (default: ../art_widget)")
    args = parser.parse_args(argv)
    errors = problems(args.art_widget)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 2
    build(args.art_widget)
    return 0


if __name__ == "__main__":
    sys.exit(main())
