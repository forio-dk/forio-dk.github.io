"""Builds the Syllabee pages, syllabee/index.html and syllabee/<code>/index.html, with their images and videos under
syllabee/assets/, from the reading app's repository (../learn_to_read): each language's store listing, screenshots and
preview video in docs/store/<code>/, and the app's own drawings, converted from its VectorDrawables to SVG by the
repository's tools/vd2svg.py through tools/store_assets.py, which also gives the hero's split word and picture cards
(the feature graphic's).

Syllabee is four Play apps, one per language (Syllabee, Stavebi, Слогарик, Складарик); each page presents its own.
"""
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from config import SYLLABEE
from output import app_webp, badge, prune, write_text
from pages import app_icon, language_video, phone_shots, write_page

# Theme: the drawing on its tile, one that every language's pack uses in that theme (tests/test_syllabee.py checks).
THEMES: dict[str, str] = {
    "animals": "ic_word_cat", "flowers": "ic_word_tulip", "fruits": "ic_word_orange", "vegetables": "ic_word_carrot",
    "transport": "ic_word_helicopter", "bugs": "ic_word_butterfly", "toys": "ic_word_robot",
    "clothes": "ic_word_jacket", "food": "ic_word_pizza", "music": "ic_word_trumpet", "school": "ic_word_backpack",
    "kitchen": "ic_pic_teapot", "tools": "ic_pic_hammer", "birds": "ic_word_rooster", "countries": "ic_word_flag_japan",
    "mixed": "ic_cat_mixed",
}
FULL_THEMES = frozenset({"food", "music", "school", "kitchen", "tools", "birds", "countries", "mixed"})
COLOURING: dict[str, str] = {"letters": "ic_cat_letters", "numbers": "ic_cat_numbers", "shapes": "ic_cat_shapes",
                             "math": "ic_math_rocket"}
# The two drawings whose licences ask for an attribution (docs/artwork/SOURCES.md); the pages give none.
NEEDS_ATTRIBUTION = frozenset({"ic_word_pigeon", "ic_word_pepper"})
# Picture key: the listing's Play screenshot it shows.
HERO = {"hero": "phone-1-themes.png"}
GAMES = {"game_syllables": "phone-2-syllables.png", "game_memo": "phone-3-memo.png", "game_build": "phone-4-build.png",
         "game_colouring": "phone-5-colouring-letters.png"}
COLOURING_SHOT = {"colouring": "phone-6-colouring-shapes.png"}
STORE_FILES = ("listing.md", "icon-512.png", "feature-graphic.png", "video.mp4", *HERO.values(), *GAMES.values(),
               *COLOURING_SHOT.values())
TOOLS = Path("tools") / "store_assets.py"
ART = "img/art"


@dataclass(frozen=True)
class Tile:
    """A theme's or a Colouring theme's tile: its drawing's URL, the app's colour for it, and whether only the full
    version has it."""
    key: str
    drawing: str
    colour: str
    locked: bool


def drawable(repo: Path, name: str) -> Path:
    return repo / "app" / "src" / "main" / "res" / "drawable" / f"{name}.xml"


def store_tools(repo: Path) -> ModuleType:
    """The repository's tools/store_assets.py: WORDS, CARDS, colour(name) and convert(path). Its folder goes on the
    path, as it imports vd2svg from beside it."""
    folder = str((repo / "tools").resolve())
    if folder not in sys.path:
        sys.path.append(folder)
    spec = importlib.util.spec_from_file_location("store_assets", repo / TOOLS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def drawables(tools: ModuleType) -> set[str]:
    """Every drawing the pages show: the themes', Colouring's and each language's hero cards."""
    return {*THEMES.values(), *COLOURING.values(), *(name for cards in tools.CARDS.values() for name in cards)}


def write_drawings(repo: Path, tools: ModuleType) -> dict[str, str]:
    """Writes each drawing as syllabee/assets/img/art/<name>.svg, deletes the ones no longer shown, and returns each
    drawing's URL by name."""
    folder = SYLLABEE.assets / ART
    urls, written = {}, set()
    for name in sorted(drawables(tools)):
        path = folder / f"{name}.svg"
        write_text(path, tools.convert(str(drawable(repo, name))) + "\n")
        written.add(path)
        urls[name] = f"{SYLLABEE.assets_url}/{ART}/{name}.svg"
    prune(folder, written)
    return urls


def tiles(keys: dict[str, str], urls: dict[str, str], tools: ModuleType) -> list[Tile]:
    """A tile per key, in order, with its drawing, the app's cat_<key> colour and whether it is locked."""
    return [Tile(key, urls[name], tools.colour(f"cat_{key}"), key in FULL_THEMES) for key, name in keys.items()]


def store_problems(repo: Path, strings: dict[str, dict]) -> list[str]:
    """What stops the build in the reading app's repository: a store file, the tools or a drawing that is missing, or a
    drawing whose licence needs an attribution. One line per problem, the path relative to the repository."""
    errors = [f"{(SYLLABEE.listing(repo, lang) / name).relative_to(repo).as_posix()}: missing"
              for lang in SYLLABEE.langs for name in STORE_FILES if not (SYLLABEE.listing(repo, lang) / name).is_file()]
    if not (repo / TOOLS).is_file():
        return errors + [f"{TOOLS.as_posix()}: missing"]
    names = drawables(store_tools(repo))
    errors += [f"{drawable(repo, name).relative_to(repo).as_posix()}: missing" for name in sorted(names)
               if not drawable(repo, name).is_file()]
    errors += [f"{name}: its licence needs an attribution the page doesn't give"
               for name in sorted(names & NEEDS_ATTRIBUTION)]
    return errors


def build_pages(repo: Path, strings: dict[str, dict]) -> None:
    tools = store_tools(repo)
    urls = write_drawings(repo, tools)
    themes, colouring = tiles(THEMES, urls, tools), tiles(COLOURING, urls, tools)
    icon = app_icon(SYLLABEE, SYLLABEE.graphics(repo, SYLLABEE.langs[0]))
    for lang in SYLLABEE.langs:
        graphics = SYLLABEE.graphics(repo, lang)
        pictures = {"icon": icon, "badge": badge(lang),
                    "hero": app_webp(SYLLABEE, graphics / HERO["hero"], f"img/{lang.code}", "hero", (240, 480)),
                    **phone_shots(SYLLABEE, graphics, lang, GAMES | COLOURING_SHOT)}
        write_page(SYLLABEE, lang, graphics, strings[lang.code], pictures, syllables=tools.WORDS[lang.code][2],
                   cards=[urls[name] for name in tools.CARDS[lang.code]], themes=themes, colouring=colouring,
                   **language_video(SYLLABEE, SYLLABEE.listing(repo, lang), lang))
