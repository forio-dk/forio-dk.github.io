"""Builds the Atlas Hunt pages, atlashunt/index.html and atlashunt/<code>/index.html, with their images and videos
under atlashunt/assets/, from the Atlas Hunt repository's store graphics and preview videos.

Every page shows its own listing's Play screenshots and video. The home-N-<screen>.png shots (taken for this page)
appear as a gallery on a page only when that page's listing has them, each with its caption from the strings.
"""
import re
from dataclasses import dataclass
from pathlib import Path

from assets import Picture, transcode_video
from config import ATLAS_HUNT, LANGS
from output import app_webp, badge
from pages import app_icon, listing_graphics, phone_shots, write_page

ASSETS = ATLAS_HUNT.assets
# Picture key: the listing's Play screenshot it shows.
HERO = {"hero_left": "phone-4-flags.png", "hero_centre": "phone-3-game.png", "hero_right": "phone-8-night-sky.png"}
STEPS = {"step_1": "phone-2-europe.png", "step_2": "phone-5-card.png", "step_3": "phone-6-results.png"}
# Picture key: the en-US leaderboard icon that stands for the level (the icons have no text).
LEVELS = {"level_earth": "leaderboard-world-512.png", "level_space": "leaderboard-space-512.png",
          "level_flags": "leaderboard-flags-512.png", "level_currencies": "leaderboard-currencies-512.png"}
HOME_SHOT = re.compile(r"home-(\d+)-([a-z0-9-]+)\.png")


@dataclass(frozen=True)
class Shot:
    """A gallery shot: its thumbnail in the strip, and the shot enlarged in its popover at 1x and 2x."""
    screen: str
    thumb: Picture
    large_1x: str
    large_2x: str


def gallery_shots(graphics: Path) -> list[tuple[str, Path]]:
    """The listing's home-N-<screen>.png shots as (screen, file), in N order."""
    found = [(int(match[1]), match[2], path) for path in graphics.glob("home-*.png")
             if (match := HOME_SHOT.fullmatch(path.name))]
    return [(screen, path) for _, screen, path in sorted(found)]


def gallery_problems(repo: Path, strings: dict[str, dict]) -> list[str]:
    """A shot in a listing whose screen has no caption in that language's strings stops the build."""
    return [f"apps/atlashunt/strings/{lang.code}.toml: no caption for {path.name}"
            for lang in LANGS for screen, path in gallery_shots(listing_graphics(repo, lang))
            if screen not in strings[lang.code]["gallery"]["captions"]]


def gallery_shot(screen: str, path: Path, folder: str) -> Shot:
    """The strip's thumbnail at 160 and 320 px, and the popover's shot at 540 and 1080 px wide."""
    large = app_webp(ATLAS_HUNT, path, folder, screen, (540, 1080))
    return Shot(screen, app_webp(ATLAS_HUNT, path, folder, screen, (160, 320)), large.src,
                large.srcset.split(", ")[1].split()[0])


def build_pages(repo: Path, strings: dict[str, dict]) -> None:
    default = listing_graphics(repo, LANGS[0])
    shared = {"icon": app_icon(ATLAS_HUNT, default)}
    for key, name in LEVELS.items():
        shared[key] = app_webp(ATLAS_HUNT, default / name, "img/levels", key.removeprefix("level_"), (64, 128))

    for lang in LANGS:
        graphics = listing_graphics(repo, lang)
        pictures = shared | phone_shots(ATLAS_HUNT, graphics, lang, HERO | STEPS) | {"badge": badge(lang)}
        gallery = [gallery_shot(screen, path, f"img/{lang.code}/gallery") for screen, path in gallery_shots(graphics)]
        video = ASSETS / "video" / f"{lang.code}.mp4"
        poster = ASSETS / "video" / f"{lang.code}-poster.webp"
        transcode_video(graphics.parent / "video.mp4", video, poster)
        write_page(ATLAS_HUNT, lang, graphics, strings[lang.code], pictures, gallery=gallery,
                   video=f"{ATLAS_HUNT.assets_url}/video/{video.name}",
                   poster=f"{ATLAS_HUNT.assets_url}/video/{poster.name}")
