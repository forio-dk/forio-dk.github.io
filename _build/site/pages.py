"""The steps every app's page builder shares: the app's icon, its phone screenshots, and writing one language's page
with its share image."""
from pathlib import Path

from assets import Picture, favicons, og_jpeg
from config import App, Lang, page_file
from output import app_webp, write_text
from render import render_page


def app_icon(app: App, graphics: Path) -> Picture:
    """The app's icon from the listing's icon-512.png: the tab and touch icons in <app>/assets/img, and the top bar's
    WebP set."""
    favicons(graphics / "icon-512.png", app.assets / "img")
    return app_webp(app, graphics / "icon-512.png", "img", "icon", (64, 128))


def phone_shots(app: App, graphics: Path, lang: Lang, shots: dict[str, str]) -> dict[str, Picture]:
    """The listing's phone screenshots by picture key (file name: shots[key]), as WebP sets 200 and 400 px wide in
    <app>/assets/img/<code>/."""
    return {key: app_webp(app, graphics / name, f"img/{lang.code}", key.replace("_", "-"), (200, 400))
            for key, name in shots.items()}


def write_page(app: App, lang: Lang, graphics: Path, s: dict, pictures: dict[str, Picture], **extra) -> None:
    """One language's page, with the listing's feature graphic as its share image (og.jpg)."""
    og_jpeg(graphics / "feature-graphic.png", app.assets / "img" / lang.code / "og.jpg")
    write_text(page_file(app, lang), render_page(app, lang, s, pictures, **extra))
