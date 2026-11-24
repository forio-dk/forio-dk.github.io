"""Generates the site: each app's pages (see artwidget.py), the home page index.html with the Forio logo, and
sitemap.xml and robots.txt.

Run from the repository root: python -X utf8 _build/site/build.py [--art-widget ../art_widget]
It reads each app's store graphics and preview video from the app's repository and the downloads in vendor/, and
writes only what changed, so a second run leaves git status clean. The stylesheets are hand-written.
"""
import argparse
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path

import artwidget
from assets import Picture, forio_mark
from config import ART_WIDGET, BUILD, LANGS, ROOT, VENDOR_DIR, App
from output import app_webp, write_text
from render import render_home
from sitemap import ROBOTS_TXT, render_sitemap
from strings import load_strings, shape_errors

BUILDERS: dict[App, Callable[[Path, dict[str, dict]], None]] = {ART_WIDGET: artwidget.build_pages}


def forio_logo() -> Picture:
    """Draws the Forio logo: favicon.ico and apple-touch-icon.png at the site root, which browsers also use for the
    pages that name no icon (README.md, the policies), and the home page's top-bar mark."""
    font = VENDOR_DIR / "fonts" / "playfair-display-latin-600-normal.ttf"
    forio_mark(font, 256).save(ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    forio_mark(font, 180, rounded=False).save(ROOT / "apple-touch-icon.png", optimize=True)
    master = ART_WIDGET.assets / "img" / "apps" / "forio-512.png"
    master.parent.mkdir(parents=True, exist_ok=True)
    forio_mark(font, 512).save(master, optimize=True)
    return app_webp(ART_WIDGET, master, "img/apps", "forio", (64, 128))


def build_home(repos: dict[App, Path]) -> None:
    def icon(src: Path, stem: str) -> Picture:
        return app_webp(ART_WIDGET, src, "img/apps", stem, (96, 192))

    apps = {
        "art_widget": icon(repos[ART_WIDGET] / "docs" / "listings" / LANGS[0].listing / "graphics" / "icon-512.png",
                           "art-widget"),
        "atlas_hunt": icon(VENDOR_DIR / "icons" / "atlas-hunt.png", "atlas-hunt"),
        "syllabee": icon(VENDOR_DIR / "icons" / "syllabee.png", "syllabee"),
        "forio": forio_logo(),
    }
    write_text(ROOT / "index.html", render_home(apps))


def build(repos: dict[App, Path], apps_dir: Path = BUILD / "apps") -> None:
    for app, repo in repos.items():
        BUILDERS[app](repo, load_strings((lang.code for lang in LANGS), apps_dir / app.slug / "strings"))
    build_home(repos)
    write_text(ROOT / "sitemap.xml", render_sitemap())
    write_text(ROOT / "robots.txt", ROBOTS_TXT)


def option(app: App) -> str:
    """The command-line option naming the app's repository: --art-widget for art_widget."""
    return "--" + app.repo.replace("_", "-")


def problems(repos: dict[App, Path], apps_dir: Path = BUILD / "apps") -> list[str]:
    """What stops a build: an app repository that is missing, a strings file that is missing or not valid TOML, or a
    language whose strings differ from English's."""
    errors = []
    for app, repo in repos.items():
        if not (repo / "docs" / "listings").is_dir():
            errors.append(f"{repo} is not the {app.name} repository (no docs/listings); pass {option(app)}")
        errors += strings_problems(app, apps_dir / app.slug / "strings")
    return errors


def strings_problems(app: App, folder: Path) -> list[str]:
    strings, errors = {}, []
    for lang in LANGS:
        try:
            strings.update(load_strings([lang.code], folder))
        except (OSError, tomllib.TOMLDecodeError) as error:
            errors.append(f"apps/{app.slug}/strings/{lang.code}.toml: {error}")
    english = strings.get(LANGS[0].code)
    if english is not None:
        errors += [f"apps/{app.slug}/strings/{code}.toml: {error}" for code, other in strings.items()
                   if code != LANGS[0].code for error in shape_errors(english, other)]
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for app in BUILDERS:
        parser.add_argument(option(app), type=Path, default=ROOT.parent / app.repo, dest=app.slug,
                            help=f"the {app.name} repository (default: ../{app.repo})")
    args = parser.parse_args(argv)
    repos = {app: getattr(args, app.slug) for app in BUILDERS}
    errors = problems(repos)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 2
    build(repos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
